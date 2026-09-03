"""Shared raw-byte loading for the image and audio branches -- both build
their tensor from the same source bytes (ADR-0002, ADR-0003, ADR-0018), so
the dispatch logic lives in one place rather than twice.
"""

from __future__ import annotations

from pathlib import Path

from src.data.recover import recover_bytes

IMAGE_FILE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif")


def parse_kaggle_bytes_file(path: Path) -> bytes:
    """BIG2015 `.bytes` format: '<address> <hex> <hex> ... <hex>' per line, the
    leading address label discarded. '??' marks a byte the competition scrubbed
    from the PE header (ADR-0003) and is treated as 0x00 -- there is no way to
    recover the true value on this track, and 0x00 is at least a fixed, stated
    convention rather than a guess dressed up as data."""
    out = bytearray()
    with open(path, "r", encoding="ascii", errors="replace") as f:
        for line in f:
            for tok in line.split()[1:]:
                out.append(0 if tok == "??" else int(tok, 16))
    return bytes(out)


def load_raw_bytes(binary_path: str) -> bytes:
    """Dispatches on file extension: a Malimg image recovers via Nataraj
    flattening (ADR-0002, strict -- a resize failure must surface here, not be
    masked as "malformed input"); a BIG2015 `.bytes` file is a hex-dump text
    format; anything else (a benign PE, ADR-0018, or a raw instrument-set
    binary) is read directly."""
    path = Path(binary_path)
    suffix = path.suffix.lower()
    if suffix == ".bytes":
        return parse_kaggle_bytes_file(path)
    if suffix in IMAGE_FILE_EXTENSIONS:
        return recover_bytes(path)
    return path.read_bytes()
