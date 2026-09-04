<#
.SYNOPSIS
    Collect LinkedIn post metrics and push them to the repository.

.DESCRIPTION
    opencli drives the Chrome session on this machine, so collection can only
    happen here. The cloud session cannot reach linkedin.com; it reads what
    this script pushes.

    It steals the screen if you let it, and -Window background did not stop
    that on this machine. So the window is dealt with from the outside as well:
    hide_browser.ps1 runs alongside and moves whatever browser window comes up
    off the desktop, keeping focus where it was. Pass -ShowBrowser to watch it
    work; otherwise nothing appears in front of you.

    There is no version of this that runs in the cloud. opencli drives the
    Chrome session that is logged in to LinkedIn, that session is on this PC,
    and linkedin.com is blocked from the cloud session besides.

    Run it by hand, or from Task Scheduler. See docs/COLLECTING.md.

.PARAMETER RepoPath
    Working copy of speedrack-yuplee/Cluade---Linked-In.

.PARAMETER Branch
    Branch to push to. Kept separate from the content branch so the two
    sessions never collide.
#>
param(
    [string]$RepoPath = "$env:USERPROFILE\Documents\Cluade---Linked-In",
    [string]$Branch = "claude/linkedin-metrics",
    [int]$Limit = 40,
    [ValidateSet("background", "foreground")]
    [string]$Window = "background",
    [switch]$ShowBrowser
)

$ErrorActionPreference = "Stop"
chcp 65001 > $null
# chcp sets the console code page; PowerShell 5.1 decodes a piped child
# process with [Console]::OutputEncoding, which chcp leaves alone. Without
# this the UTF-8 opencli writes is read as cp949 and Korean is destroyed.
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
$OutputEncoding = New-Object System.Text.UTF8Encoding $false


$HideJob = $null
$HideStop = Join-Path $env:TEMP "homedant-collect-$PID.stop"

function Start-BrowserHiding {
    if ($ShowBrowser) { return }
    $watcher = Join-Path $PSScriptRoot "hide_browser.ps1"
    if (-not (Test-Path -LiteralPath $watcher)) {
        Write-Warning "hide_browser.ps1 이 없습니다. 창이 화면에 보일 수 있습니다."
        return
    }
    Remove-Item -LiteralPath $HideStop -ErrorAction SilentlyContinue
    $script:HideJob = Start-Job -ScriptBlock {
        param($script, $stop)
        & powershell.exe -ExecutionPolicy Bypass -NoProfile -File $script -StopFile $stop
    } -ArgumentList $watcher, $HideStop
}

function Stop-BrowserHiding {
    # The stop file, not Stop-Job: the watcher is a child process and killing
    # the job would leave it running with windows still to park.
    New-Item -ItemType File -Path $HideStop -Force | Out-Null
    if ($script:HideJob) {
        Wait-Job $script:HideJob -Timeout 5 | Out-Null
        Remove-Job $script:HideJob -Force -ErrorAction SilentlyContinue
        $script:HideJob = $null
    }
    Remove-Item -LiteralPath $HideStop -ErrorAction SilentlyContinue
}


function Invoke-OpenCli {
    <#
        One opencli call, returned as a single string.

        Two things go wrong often enough to handle here rather than at each
        call site. A tab that opencli opened and closed can leave the bridge
        holding an identity the browser no longer has ("stale page identity"),
        which the next call resolves; and an opencli build that predates
        --window background rejects the value, in which case foreground is
        better than nothing. Both are retried once, and only once: a second
        identical failure is a real one and the caller should see it.
    #>
    param([string[]]$Arguments, [int]$Attempts = 2)

    $mode = $Window
    for ($try = 1; $try -le $Attempts; $try++) {
        $output = & opencli.cmd @Arguments --window $mode --keep-tab false 2>&1 |
            Out-String -Width 100000

        if ($output.TrimStart().StartsWith("[")) { return $output }

        if ($mode -ne "foreground" -and $output -match "window|invalid|unknown|unrecognized") {
            Write-Warning "opencli 가 --window $mode 를 받지 않습니다. 화면에 띄워서 다시 시도합니다."
            $mode = "foreground"
            continue
        }
        if ($try -lt $Attempts -and $output -match "stale page identity|Page not found") {
            Start-Sleep -Seconds 3
            continue
        }
        return $output
    }
    return $output
}


function ConvertTo-ReferenceSchema {
    <#
        opencli emits its own columns, and leaves raw newlines and quotes
        inside raw_text so the document does not parse. raw_text duplicates
        body, so it is dropped by line before parsing rather than repaired.
        The result is the shape content/reference/README.md documents.
    #>
    param([string]$RawJson)

    $kept = New-Object System.Collections.Generic.List[string]
    $skipping = $false
    foreach ($line in ($RawJson -split "`r?`n")) {
        if ($skipping) {
            if ($line -match '^\s*\},?\s*$') { $skipping = $false; $kept.Add($line) }
            continue
        }
        if ($line -match '^\s*"raw_text"\s*:') {
            if ($kept.Count -gt 0) {
                $last = $kept[$kept.Count - 1].TrimEnd()
                if ($last.EndsWith(",")) { $kept[$kept.Count - 1] = $last.Substring(0, $last.Length - 1) }
            }
            $skipping = $true
            continue
        }
        $kept.Add($line)
    }

    $posts = ($kept -join "`n") | ConvertFrom-Json

    $rows = foreach ($p in $posts) {
        $body = if ($p.body) { [string]$p.body } else { "" }
        $hook = ($body -split "`n" | Where-Object { $_.Trim() } | Select-Object -First 1)
        $tags = @([regex]::Matches($body, "#(\w+)") | ForEach-Object { $_.Groups[1].Value })
        $tagged = @()
        if ($p.mentions) { $tagged = @(([string]$p.mentions) -split "\s*,\s*" | Where-Object { $_ }) }
        [ordered]@{
            posted_at   = $p.posted_at
            pillar      = $null
            topic       = $null
            url         = $p.url
            impressions = $p.impressions
            reactions   = $p.reactions
            comments    = $p.comments
            reposts     = $p.reposts
            hook        = $hook
            hashtags    = $tags
            tagged      = $tagged
            has_image   = [bool]$p.media
            body        = $body
        }
    }
    return ($rows | ConvertTo-Json -Depth 6)
}

if (-not (Test-Path $RepoPath)) {
    throw "Repository not found at $RepoPath. Clone it first, or pass -RepoPath."
}
Set-Location $RepoPath

git fetch origin --quiet
git checkout $Branch --quiet 2>$null
if ($LASTEXITCODE -ne 0) { git checkout -b $Branch --quiet }
git pull --quiet origin $Branch 2>$null

# Out-String -Width keeps PowerShell from wrapping long JSON lines, which
# silently corrupts the file; WriteAllText avoids the UTF-16 default of ">".
# $ErrorActionPreference is Stop, so any failure below unwinds the script. The
# watcher is a separate process and would keep parking windows after it, so it
# is stopped on the way out as well as at the end.
trap { Stop-BrowserHiding; break }

Start-BrowserHiding
$json = Invoke-OpenCli @("linkedin", "posts", "--limit", "$Limit", "-f", "json")

if (-not $json.TrimStart().StartsWith("[")) {
    throw "opencli did not return JSON. First 200 characters:`n$($json.Substring(0, [Math]::Min(200, $json.Length)))"
}

New-Item -ItemType Directory -Force -Path "content\reference" | Out-Null
$target = Join-Path $RepoPath "content\reference\posts.json"
[IO.File]::WriteAllText($target, (ConvertTo-ReferenceSchema $json), [Text.UTF8Encoding]::new($false))

$count = ([regex]::Matches($json, '"rank"')).Count
Write-Host "collected $count posts"

# The feed: what the people and companies this account follows are posting.
# Impressions are visible to a post's author only, so watched posts carry
# reactions and comments and nothing more.
$feed = Invoke-OpenCli @("linkedin", "timeline", "--limit", "50", "-f", "json")
if ($feed.TrimStart().StartsWith("[")) {
    [IO.File]::WriteAllText(
        (Join-Path $RepoPath "content\reference\timeline.json"), $feed, [Text.UTF8Encoding]::new($false))
    Write-Host "collected $((([regex]::Matches($feed, '"rank"')).Count)) feed posts"
} else {
    Write-Warning "timeline returned no JSON; skipping"
}

# Named profiles from the watchlist. An entry with no profile_url is named
# and skipped: a guessed handle would collect the wrong person silently.
$watchPath = Join-Path $RepoPath "src\homedant_linkedin\data\watchlist.json"
if (Test-Path $watchPath) {
    $watch = Get-Content $watchPath -Raw | ConvertFrom-Json
    $collected = @()
    $missing = @()
    foreach ($person in $watch.people) {
        if (-not $person.profile_url) { $missing += $person.name; continue }
        $one = Invoke-OpenCli @("linkedin", "posts", "--profile-url", $person.profile_url,
                                "--limit", "10", "-f", "json")
        if ($one.TrimStart().StartsWith("[")) {
            $collected += [pscustomobject]@{ name = $person.name; url = $person.profile_url; posts = ($one | ConvertFrom-Json) }
        } else {
            Write-Warning "$($person.name): no JSON returned"
        }
    }
    if ($collected.Count) {
        [IO.File]::WriteAllText(
            (Join-Path $RepoPath "content\reference\watched.json"),
            ($collected | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
        Write-Host "collected $($collected.Count) watched profiles"
    }
    if ($missing.Count) {
        Write-Host "no profile_url yet, skipped: $($missing -join ', ')"
    }
}

Stop-BrowserHiding

# Only stage what actually got written. A skipped timeline used to abort the
# whole run here, throwing away the posts that had already been collected.
$staged = 0
foreach ($file in @("content/reference/posts.json",
                    "content/reference/timeline.json",
                    "content/reference/watched.json")) {
    if (Test-Path -LiteralPath (Join-Path $RepoPath $file)) {
        git add $file
        $staged++
    }
}
if ($staged -eq 0) {
    Write-Warning "수집된 파일이 없습니다. opencli.cmd doctor 로 확인해 주세요."
    exit 1
}
if (git diff --cached --quiet) {
    Write-Host "no change since the last run"
    exit 0
}
git commit -m "Refresh LinkedIn metrics ($count own posts, $(Get-Date -Format yyyy-MM-dd))" --quiet
git push -u origin $Branch --quiet
Write-Host "pushed to $Branch"
