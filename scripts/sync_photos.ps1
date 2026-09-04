<#
.SYNOPSIS
    Copy downscaled product photography out of the company design library.

.DESCRIPTION
    The master library under "01_사진 ~ 05_본사 관련 자료" is about 250 GB, which
    is far too much to hand over as a zip and far too large to keep in the
    repository. This script reads it and writes a working copy: images only,
    long edge 1600 px, JPEG quality 82. That is roughly 200 KB a photo instead
    of 3-8 MB, and it is already larger than a 1200 px LinkedIn image needs.

    The source library is READ ONLY. This script opens files there and never
    writes, moves, renames or deletes anything in it. Everything it produces
    goes to -Destination.

    The copies land in the repository, because that is the only place the cloud
    session can open them as files: it can look at OneDrive through the
    connector, but it cannot read bytes out of it, and a photograph has to be
    readable to be composited or cropped. Leo's own Image folder is for
    finished work coming the other way, not for copies of originals.

    It runs as a dry run by default and reports what it would copy. Pass -Apply
    to actually write. Re-running is incremental: a photo already copied and
    unchanged at the source is skipped, so a second run takes seconds.

.PARAMETER Source
    The design library root. Read only.

.PARAMETER RepoPath
    Working copy of speedrack-yuplee/Cluade---Linked-In. The photos land under
    assets/library there.

.PARAMETER Destination
    Overrides where the copies go. Normally left alone.

.PARAMETER Sets
    Which parts of the library to copy, as "destination folder = source path
    relative to Source". Defaults to the three that carry usable product and
    brand photography.

.PARAMETER Apply
    Write the files. Without it the script only reports.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\scripts\sync_photos.ps1
    powershell -ExecutionPolicy Bypass -File .\scripts\sync_photos.ps1 -Apply
#>
param(
    [string]$Source = "$env:USERPROFILE\OneDrive - 스피드랙\박 상희의 파일 - 01_사진 ~ 05_본사 관련 자료\01_사진 ~ 05_본사 관련 자료",
    [string]$RepoPath = "$env:USERPROFILE\Documents\Cluade---Linked-In",
    [string]$Destination = $null,
    [System.Collections.Specialized.OrderedDictionary]$Sets = $null,
    [int]$MaxEdge = 1600,
    [int]$Quality = 82,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
chcp 65001 > $null
# PowerShell 5.1 decodes child output with [Console]::OutputEncoding, which
# chcp leaves alone. Without this the Korean folder names come out as mojibake.
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
$OutputEncoding = New-Object System.Text.UTF8Encoding $false

Add-Type -AssemblyName System.Drawing

if (-not $Destination) { $Destination = Join-Path $RepoPath "assets\library" }

if (-not $Sets) {
    $Sets = [ordered]@{
        # Photographs of units standing in real rooms someone bought them for:
        # a university store, a testing laboratory, a back of house. Worth more
        # to a B2B post than any studio shot, and worth more than compositing a
        # unit into a stock photograph, because the question "which school?"
        # has an answer. 57 MB, so this is the one to run first.
        "installations" = "01_사진자료_IMAGE SOURCE\B05_특판 이미지\설치이미지추가"
        # Already sized and cropped for social, so the least work to reuse.
        "sns"           = "02_해외 디자인자료(아마존_월마트)\A03-01_글로벌_SNS"
        # Small, and needed on every generated image.
        "logo"          = "01_사진자료_IMAGE SOURCE\D01_브랜드로고"
    }
}

# Folders whose contents must not leave the library. The repository this
# script lives in is public, and a working copy is one careless commit away
# from it, so competitor analysis, unreleased work and customer-specific
# artwork are excluded at the source rather than sorted out later.
$ExcludedSegments = @(
    "경쟁사비교",
    "Before&After",
    "작업중",
    "Costco",
    "Test Rite",
    "테스트라이트",
    "IndexLiving",
    "인덱스리빙"
)

$ImageSuffixes = @(".jpg", ".jpeg", ".png")

# FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS. OneDrive Files On-Demand leaves cloud
# only files as placeholders; reading one downloads it. Worth counting up
# front so a first run does not silently pull tens of gigabytes.
$RecallOnDataAccess = 0x400000


function Test-Excluded {
    param([string]$Path)
    foreach ($segment in $ExcludedSegments) {
        if ($Path -like "*$segment*") { return $true }
    }
    return $false
}


function Get-JpegEncoder {
    [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() |
        Where-Object { $_.MimeType -eq "image/jpeg" } |
        Select-Object -First 1
}


function Copy-Downscaled {
    <#
        Write $SourceFile to $TargetFile with its long edge at most $MaxEdge.
        A photo already smaller than that is still re-encoded, so every file in
        the working copy is a predictable JPEG regardless of what it came from.
    #>
    param([string]$SourceFile, [string]$TargetFile)

    $image = [System.Drawing.Image]::FromFile($SourceFile)
    try {
        $scale = [Math]::Min(1.0, $MaxEdge / [Math]::Max($image.Width, $image.Height))
        $width = [int][Math]::Round($image.Width * $scale)
        $height = [int][Math]::Round($image.Height * $scale)

        $canvas = New-Object System.Drawing.Bitmap $width, $height
        try {
            $graphics = [System.Drawing.Graphics]::FromImage($canvas)
            try {
                $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
                $graphics.DrawImage($image, 0, 0, $width, $height)
            } finally { $graphics.Dispose() }

            $parameters = New-Object System.Drawing.Imaging.EncoderParameters 1
            $parameters.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter(
                [System.Drawing.Imaging.Encoder]::Quality, [long]$Quality)
            $canvas.Save($TargetFile, (Get-JpegEncoder), $parameters)
            $parameters.Dispose()
        } finally { $canvas.Dispose() }
    } finally { $image.Dispose() }
}


if (-not (Test-Path -LiteralPath $Source)) {
    throw "원본 폴더를 찾을 수 없습니다: $Source`n-Source 로 경로를 지정해 주세요."
}

Write-Host ""
Write-Host "원본 (읽기 전용) : $Source"
Write-Host "사본 저장 위치   : $Destination"
Write-Host "                   (저장소 안입니다. 이엽님 Image 폴더에는 결과물만 들어갑니다.)"
Write-Host "축소             : 긴 변 $MaxEdge px, JPEG 품질 $Quality"
if (-not $Apply) {
    Write-Host "모드             : DRY RUN — 아무것도 쓰지 않습니다. 실제로 복사하려면 -Apply" -ForegroundColor Yellow
}
Write-Host ""

$plannedCount = 0
$plannedBytes = [long]0
$cloudOnlyCount = 0
$cloudOnlyBytes = [long]0
$copied = 0
$skipped = 0
$failed = @()
$index = @()

foreach ($setName in $Sets.Keys) {
    $setRoot = Join-Path $Source $Sets[$setName]
    if (-not (Test-Path -LiteralPath $setRoot)) {
        Write-Host "[건너뜀] $setName — 경로 없음: $setRoot" -ForegroundColor Yellow
        continue
    }

    $files = Get-ChildItem -LiteralPath $setRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $ImageSuffixes -contains $_.Extension.ToLower() } |
        Where-Object { -not (Test-Excluded $_.FullName) }

    Write-Host ("[{0}] 이미지 {1}장" -f $setName, $files.Count)

    foreach ($file in $files) {
        $relative = $file.FullName.Substring($setRoot.Length).TrimStart('\')
        $targetRelative = [IO.Path]::ChangeExtension((Join-Path $setName $relative), ".jpg")
        $target = Join-Path $Destination $targetRelative

        if ((([int]$file.Attributes) -band $RecallOnDataAccess) -ne 0) {
            $cloudOnlyCount++
            $cloudOnlyBytes += $file.Length
        }

        $existing = Get-Item -LiteralPath $target -ErrorAction SilentlyContinue
        if ($existing -and $existing.LastWriteTimeUtc -ge $file.LastWriteTimeUtc) {
            $skipped++
            continue
        }

        $plannedCount++
        # 1600 px at quality 82 lands near 200 KB whatever the source was.
        $plannedBytes += 200KB

        if (-not $Apply) { continue }

        try {
            $parent = Split-Path -Parent $target
            if (-not (Test-Path -LiteralPath $parent)) {
                New-Item -ItemType Directory -Path $parent -Force | Out-Null
            }
            Copy-Downscaled -SourceFile $file.FullName -TargetFile $target
            $copied++
            $index += [pscustomobject]@{
                set    = $setName
                file   = $targetRelative -replace '\\', '/'
                source = $relative -replace '\\', '/'
                bytes  = (Get-Item -LiteralPath $target).Length
            }
            if ($copied % 50 -eq 0) { Write-Host "  ... $copied 장 복사" }
        } catch {
            $failed += "$($file.FullName) — $($_.Exception.Message)"
        }
    }
}

Write-Host ""
Write-Host "-------------------------------------------"
Write-Host ("복사 대상   : {0} 장 (약 {1:N0} MB)" -f $plannedCount, ($plannedBytes / 1MB))
Write-Host ("이미 있음   : {0} 장 — 건너뜀" -f $skipped)
if ($cloudOnlyCount -gt 0) {
    Write-Host ("클라우드 전용: {0} 장 (원본 {1:N1} GB) — 읽을 때 다운로드됩니다" -f `
        $cloudOnlyCount, ($cloudOnlyBytes / 1GB)) -ForegroundColor Yellow
}
if ($Apply) {
    Write-Host ("실제 복사   : {0} 장" -f $copied) -ForegroundColor Green
    if ($index.Count -gt 0) {
        # The cloud session reads this instead of opening every file, so it can
        # see what the working copy holds in one call.
        $indexPath = Join-Path $Destination "index.json"
        $index | ConvertTo-Json -Depth 4 |
            Set-Content -LiteralPath $indexPath -Encoding UTF8
        Write-Host "목록 파일   : $indexPath"
    }
} else {
    Write-Host "실제로 복사하려면 같은 명령에 -Apply 를 붙여 다시 실행하세요." -ForegroundColor Yellow
}
if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host ("실패 {0} 건:" -f $failed.Count) -ForegroundColor Red
    $failed | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" }
}
Write-Host "-------------------------------------------"
Write-Host ""
