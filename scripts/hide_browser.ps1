<#
.SYNOPSIS
    Keep the browser opencli drives out of sight while it works.

.DESCRIPTION
    Collection has to happen on this PC. opencli drives the Chrome session that
    is logged in to LinkedIn, the cloud session cannot reach linkedin.com, and
    a server has no logged-in session to drive — so there is no version of this
    that runs somewhere else. What there is, is a version that does not take
    the screen off whoever is working at it.

    So this watches for the window opencli raises and moves it off the desktop:
    to -32000,-32000, where Windows itself parks minimised windows. Off-screen
    is deliberate and minimised is not. A minimised Chrome throttles rendering
    and eventually stops painting altogether, and a page that is not painted is
    a page opencli reads as empty. Moved off-screen it keeps rendering exactly
    as if it were visible, and is simply somewhere nobody is looking.

    Whatever window had focus keeps it, so a sentence being typed in Outlook
    when the run starts goes on being typed in Outlook.

    Run in the background by collect_linkedin.ps1. It stops when -StopFile
    appears, and after -MaxMinutes regardless, so a crash upstream cannot leave
    something moving windows around for the rest of the day.

.PARAMETER StopFile
    Path this watches for. The moment it exists, the watcher stops.

.PARAMETER Match
    Window title substrings worth hiding. Anything else is left alone.
#>
param(
    [Parameter(Mandatory = $true)][string]$StopFile,
    [string[]]$Match = @("LinkedIn", "OpenCLI", "about:blank", "새 탭", "New Tab"),
    [int]$MaxMinutes = 30
)

$ErrorActionPreference = "Stop"

Add-Type -Namespace HD -Name Win -MemberDefinition @"
[DllImport("user32.dll")]
public static extern bool SetWindowPos(IntPtr hWnd, IntPtr after,
    int x, int y, int cx, int cy, uint flags);
[DllImport("user32.dll")]
public static extern IntPtr GetForegroundWindow();
[DllImport("user32.dll")]
public static extern bool IsWindowVisible(IntPtr hWnd);
"@

# SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE: move it, change nothing else.
# Not touching size matters — a window resized to nothing renders nothing.
$MoveOnly = 0x0001 -bor 0x0004 -bor 0x0010
$Parked = -32000

$moved = @{}
$deadline = (Get-Date).AddMinutes($MaxMinutes)

while (-not (Test-Path -LiteralPath $StopFile) -and (Get-Date) -lt $deadline) {
    # Whoever the user is actually working in keeps the keyboard. Reading it
    # each pass rather than once means a window they raise mid-run is safe too.
    $focused = [HD.Win]::GetForegroundWindow()

    foreach ($process in Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne 0 -and $_.ProcessName -match "chrome|msedge" }) {

        $handle = $process.MainWindowHandle
        if ($moved.ContainsKey([int64]$handle)) { continue }
        if ($handle -eq $focused) { continue }

        $title = $process.MainWindowTitle
        if (-not $title) { continue }
        $wanted = $false
        foreach ($needle in $Match) { if ($title -like "*$needle*") { $wanted = $true; break } }
        if (-not $wanted) { continue }

        if ([HD.Win]::IsWindowVisible($handle)) {
            [void][HD.Win]::SetWindowPos($handle, [IntPtr]::Zero, $Parked, $Parked, 0, 0, $MoveOnly)
            $moved[[int64]$handle] = $true
        }
    }

    Start-Sleep -Milliseconds 250
}
