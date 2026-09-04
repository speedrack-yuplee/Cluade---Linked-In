<#
.SYNOPSIS
    Collect LinkedIn post metrics and push them to the repository.

.DESCRIPTION
    opencli drives the Chrome session on this machine, so collection can only
    happen here. The cloud session cannot reach linkedin.com; it reads what
    this script pushes.

    Run it by hand, or from Task Scheduler weekly. See docs/COLLECTING.md.

.PARAMETER RepoPath
    Working copy of speedrack-yuplee/Cluade---Linked-In.

.PARAMETER Branch
    Branch to push to. Kept separate from the content branch so the two
    sessions never collide.
#>
param(
    [string]$RepoPath = "$env:USERPROFILE\Documents\Cluade---Linked-In",
    [string]$Branch = "claude/linkedin-metrics",
    [int]$Limit = 40
)

$ErrorActionPreference = "Stop"
chcp 65001 > $null
# chcp sets the console code page; PowerShell 5.1 decodes a piped child
# process with [Console]::OutputEncoding, which chcp leaves alone. Without
# this the UTF-8 opencli writes is read as cp949 and Korean is destroyed.
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
$OutputEncoding = New-Object System.Text.UTF8Encoding $false


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
$json = opencli.cmd linkedin posts --limit $Limit -f json --window foreground --keep-tab false |
    Out-String -Width 100000

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
$feed = opencli.cmd linkedin timeline --limit 50 -f json --window foreground --keep-tab false |
    Out-String -Width 100000
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
        $one = opencli.cmd linkedin posts --profile-url $person.profile_url --limit 10 -f json `
            --window foreground --keep-tab false | Out-String -Width 100000
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

git add content/reference/posts.json content/reference/timeline.json content/reference/watched.json 2>$null
if (git diff --cached --quiet) {
    Write-Host "no change since the last run"
    exit 0
}
git commit -m "Refresh LinkedIn metrics ($count own posts, $(Get-Date -Format yyyy-MM-dd))" --quiet
git push -u origin $Branch --quiet
Write-Host "pushed to $Branch"
