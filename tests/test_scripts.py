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
