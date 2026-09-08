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
    [string]$Window = "foreground",
    [switch]$ShowBrowser,
    [switch]$Full
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

    # opencli writes progress to stderr. With $ErrorActionPreference at Stop
    # that arrives as a NativeCommandError and kills the whole run before
    # anything can look at what opencli actually said — which is how a single
    # failed call took the script down with nothing collected and nothing to
    # diagnose. Inside this function a non-zero exit is data, not an event.
    $ErrorActionPreference = "Continue"

    # This used to fall back from --window background to foreground when the
    # output mentioned --window. It always did: a PowerShell NativeCommandError
    # quotes the failing source line, and that line contains --window. So every
    # unrelated failure "proved" the flag was rejected. It is moot anyway —
    # opencli on this machine does not take background at all, which is the
    # whole reason hide_browser.ps1 exists. The window is raised and then moved
    # off the desktop; that is the mechanism, not this flag.
    for ($try = 1; $try -le $Attempts; $try++) {
        $output = & opencli.cmd @Arguments --window $Window --keep-tab false 2>&1 |
            Out-String -Width 100000

        if ($output.TrimStart().StartsWith("[")) { return $output }

        # Retried, because both of these come back clean on a second ask: a
        # tab opencli closed can leave the bridge holding an identity the
        # browser no longer has, and the home feed is sometimes still loading
        # the first time the timeline is read.
        if ($try -lt $Attempts -and
            $output -match "stale page identity|Page not found|EMPTY_RESULT") {
            Start-Sleep -Seconds 4
            continue
        }
        break
    }

    if (-not $output.TrimStart().StartsWith("[")) {
        Write-Warning "opencli ($($Arguments -join ' ')) 가 JSON 을 주지 않았습니다:"
        Write-Host ($output.Trim()) -ForegroundColor DarkYellow
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

# The working tree is left exactly where Leo had it.
#
# This used to check $Branch out here, which swapped every file under scripts/
# for whatever the metrics branch happened to hold — including the sibling
# scripts this one calls, which is why hide_browser.ps1 "did not exist" a
# second after it was pulled. It also left the checkout parked on the metrics
# branch after the run, so the next pull of the content branch merged two
# branches that both edit these scripts, and PowerShell met a conflict marker.
#
# The results go to $Branch through a worktree instead: a second checkout in
# TEMP that git manages, committed and pushed from there and then removed.
$Original = (git rev-parse --abbrev-ref HEAD).Trim()
git fetch origin --quiet 2>$null

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

# Collected files are staged outside the checkout. Writing them into it would
# leave uncommitted changes on whichever branch Leo is working on, and those
# are what turn the next pull into a conflict.
$Staging = Join-Path $env:TEMP "homedant-collect"
New-Item -ItemType Directory -Force -Path $Staging | Out-Null
$target = Join-Path $Staging "posts.json"
$rows = ConvertTo-ReferenceSchema $json
[IO.File]::WriteAllText($target, $rows, [Text.UTF8Encoding]::new($false))

$count = ([regex]::Matches($json, '"rank"')).Count
Write-Host "collected $count posts"

# posts.json is a snapshot; overwriting it each run is exactly right for "what
# does the feed look like now" and exactly wrong for "is this post gaining."
# This run's snapshot is written on its own here and appended to the
# committed log further down, once the worktree that log lives in exists —
# appending to a plain file in $Staging would not survive back to a fresh
# checkout on a machine or run that does not already have it.
$snapshotTarget = Join-Path $Staging "impressions_snapshot.jsonl"
[ordered]@{
    checked_at = (Get-Date).ToUniversalTime().ToString("o")
    posts      = @($rows | ConvertFrom-Json)
} | ConvertTo-Json -Depth 6 -Compress |
    Out-File -LiteralPath $snapshotTarget -Encoding utf8 -NoNewline

# The feed: what the people and companies this account follows are posting.
# Impressions are visible to a post's author only, so watched posts carry
# reactions and comments and nothing more.
$feed = Invoke-OpenCli @("linkedin", "timeline", "--limit", "50", "-f", "json")
if ($feed.TrimStart().StartsWith("[")) {
    [IO.File]::WriteAllText(
        (Join-Path $Staging "timeline.json"), $feed, [Text.UTF8Encoding]::new($false))
    Write-Host "collected $((([regex]::Matches($feed, '"rank"')).Count)) feed posts"
} else {
    Write-Warning "timeline returned no JSON; skipping"
}

# Named profiles from the watchlist. Only on -Full: visiting the same named
# profile every hour looks nothing like the account's ordinary use, where
# following a company and reading a feed does. Competitor *company* posts do
# not wait for this — they arrive in the timeline above every run, the moment
# the company is followed. This loop exists for the one or two people who are
# worth reading but have no company page to follow instead.
$watchPath = Join-Path $RepoPath "src\homedant_linkedin\data\watchlist.json"
if ($Full -and (Test-Path $watchPath)) {
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
            (Join-Path $Staging "watched.json"),
            ($collected | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
        Write-Host "collected $($collected.Count) watched profiles"
    }
    if ($missing.Count) {
        Write-Host "no profile_url yet, skipped: $($missing -join ', ')"
    }
}

Stop-BrowserHiding

$produced = @("posts.json", "timeline.json", "watched.json") |
    Where-Object { Test-Path -LiteralPath (Join-Path $Staging $_) }
if (-not $produced) {
    Write-Warning "수집된 파일이 없습니다. opencli.cmd doctor 로 확인해 주세요."
    exit 1
}

# From here on a non-zero exit from git is a value to test, not an event to
# throw on. Under Stop it was one: "is not a working tree", from removing a
# worktree that was never there, took the run down after the posts had been
# collected and before they were pushed.
$ErrorActionPreference = "Continue"

function Remove-Worktree {
    param([string]$Path)
    if ((git worktree list) -match [regex]::Escape($Path)) {
        git worktree remove --force $Path 2>&1 | Out-Null
    }
    git worktree prune 2>&1 | Out-Null
    Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
}

# A worktree, so the branch Leo is on is never checked out from under him and
# never left switched afterwards.
$Tree = Join-Path $env:TEMP "homedant-metrics"
Remove-Worktree $Tree

git ls-remote --exit-code --heads origin $Branch 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    git worktree add --quiet -B $Branch $Tree "origin/$Branch"
} else {
    git worktree add --quiet -b $Branch $Tree
}
if ($LASTEXITCODE -ne 0) { throw "worktree 를 만들지 못했습니다: $Tree" }

try {
    $into = Join-Path $Tree "content\reference"
    New-Item -ItemType Directory -Force -Path $into | Out-Null
    foreach ($file in $produced) {
        Copy-Item -LiteralPath (Join-Path $Staging $file) -Destination $into -Force
    }

    # Appended to whatever the worktree already has from earlier pushes, never
    # overwritten — the whole point is a trend across runs, not this run's view.
    if (Test-Path -LiteralPath $snapshotTarget) {
        $logFile = Join-Path $into "impressions_log.jsonl"
        $line = [IO.File]::ReadAllText($snapshotTarget, [Text.UTF8Encoding]::new($false))
        Add-Content -LiteralPath $logFile -Value $line -Encoding utf8
    }

    git -C $Tree add content/reference
    git -C $Tree diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "no change since the last run"
    } else {
        git -C $Tree commit -m "Refresh LinkedIn metrics ($count own posts, $(Get-Date -Format yyyy-MM-dd))" --quiet
        git -C $Tree push -u origin $Branch --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Host "pushed to $Branch" -ForegroundColor Green
        } else {
            Write-Warning "push 에 실패했습니다. 수집한 파일은 $Staging 에 남아 있습니다."
        }
    }
} finally {
    Remove-Worktree $Tree
}

$now = (git rev-parse --abbrev-ref HEAD).Trim()
if ($now -ne $Original) {
    Write-Warning "브랜치가 $Original 에서 $now 로 바뀌었습니다. 이러면 안 됩니다."
} else {
    Write-Host "작업 브랜치 그대로: $Original"
}
