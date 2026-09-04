"""The PowerShell scripts run on Leo's PC, where nothing here can check them."""

from pathlib import Path

import pytest

SCRIPTS = sorted((Path(__file__).resolve().parent.parent / "scripts").glob("*.ps1"))
BOM = b"\xef\xbb\xbf"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_a_script_with_korean_in_it_starts_with_a_byte_order_mark(script):
    """Windows PowerShell 5.1 reads a .ps1 as the ANSI code page unless the
    file opens with a BOM. On a Korean machine that is cp949, so UTF-8 Korean
    decodes to mojibake that swallows quotes and braces and the whole file
    stops parsing — which is how sync_photos.ps1 first ran."""
    body = script.read_bytes()
    if body.decode("utf-8").isascii():
        return
    assert body.startswith(BOM), (
        f"{script.name} has non-ASCII text but no BOM; PowerShell 5.1 will "
        "read it as cp949 and fail to parse"
    )


def test_the_collector_hides_the_browser_unless_asked_not_to():
    """Collection cannot move to the cloud — opencli drives the logged-in Chrome
    on Leo's PC — so the window has to be got out of the way instead. The
    watcher must start before the first opencli call and be stopped on every
    way out, including the failure paths, or it goes on moving windows around
    after the run is over."""
    collector = next(s for s in SCRIPTS if s.name == "collect_linkedin.ps1")
    body = collector.read_text(encoding="utf-8")

    assert "hide_browser.ps1" in body
    assert "-ShowBrowser" in body or "$ShowBrowser" in body, "no way to watch it work"

    start = body.index("Start-BrowserHiding\n")
    first_call = body.index('Invoke-OpenCli @("linkedin"')
    assert start < first_call, "the browser is raised before anything is watching for it"

    assert "trap { Stop-BrowserHiding" in body, "a failure would leave the watcher running"
    assert body.count("Stop-BrowserHiding") >= 3, "no ordinary end to the watcher"


def test_the_watcher_moves_windows_rather_than_minimising_them():
    """A minimised Chrome throttles rendering and eventually stops painting, and
    opencli reads an unpainted page as an empty one. Off-screen keeps it
    rendering; that distinction is the whole reason this file exists."""
    watcher = next(s for s in SCRIPTS if s.name == "hide_browser.ps1")
    body = watcher.read_text(encoding="utf-8")

    assert "SetWindowPos" in body
    assert "-32000" in body
    assert "ShowWindow" not in body, "minimising is what this is here to avoid"
    assert "StopFile" in body and "MaxMinutes" in body, (
        "the watcher must be able to stop on its own if the run never does"
    )


def test_the_collector_never_checks_out_another_branch():
    """It used to switch the working tree to the metrics branch mid-run, which
    replaced every file under scripts/ — including the sibling scripts this one
    calls — and left the checkout parked there afterwards, so the next pull of
    the content branch merged two branches that both edit these scripts and
    PowerShell was handed a conflict marker to parse. Results go through a
    worktree now; the checkout is not to be touched."""
    body = next(
        s for s in SCRIPTS if s.name == "collect_linkedin.ps1"
    ).read_text(encoding="utf-8")

    for line in body.splitlines():
        code = line.split("#", 1)[0]
        assert "git checkout" not in code, f"still switches branches: {line.strip()}"

    assert "git worktree add" in body
    assert body.count("git worktree remove") >= 2, (
        "a worktree left behind makes the next run refuse to add one"
    )
    assert "rev-parse --abbrev-ref HEAD" in body, "nothing checks the branch survived"


def test_a_failing_opencli_call_says_what_it_said():
    """opencli writes to stderr, and under $ErrorActionPreference = Stop that is
    a terminating NativeCommandError — the run died with nothing collected and
    nothing to diagnose. Inside the wrapper a non-zero exit has to be data."""
    body = next(
        s for s in SCRIPTS if s.name == "collect_linkedin.ps1"
    ).read_text(encoding="utf-8")

    wrapper = body[body.index("function Invoke-OpenCli") : body.index("function ConvertTo-Reference")]
    assert '$ErrorActionPreference = "Continue"' in wrapper
    assert "Write-Host" in wrapper, "a failure that prints nothing cannot be diagnosed"

    stale = wrapper.index("stale page identity")
    window = wrapper.index("--window|unknown option")
    assert stale < window, (
        "a stale page must be retried before falling back to the foreground, "
        "or an unrelated failure puts the window back on the screen"
    )
