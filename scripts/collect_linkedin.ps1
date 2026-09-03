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
[IO.File]::WriteAllText($target, $json, [Text.UTF8Encoding]::new($false))

$count = ([regex]::Matches($json, '"rank"')).Count
Write-Host "collected $count posts"

git add content/reference/posts.json
if (git diff --cached --quiet) {
    Write-Host "no change since the last run"
    exit 0
}
git commit -m "Refresh LinkedIn post metrics ($count posts, $(Get-Date -Format yyyy-MM-dd))" --quiet
git push -u origin $Branch --quiet
Write-Host "pushed to $Branch"
