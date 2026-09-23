"""Luma-threshold bounds for the I/M image effects.

The effects themselves are implemented at runtime by the canvas processor in
templates/docheader/image_effects.js (dark/bright band selection on the
Rec.601 luma, KNEE-wide linear knees — see that file). This module only
parses and validates the "lo,hi" bounds given to --invert-bounds /
--matte-bounds (config.json: features.invert_bounds / features.matte_bounds),
which are injected into the processor as its defaults at build time.
"""

DEFAULT_INVERT_BOUNDS = (32, 239)
DEFAULT_MATTE_BOUNDS = (64, 239)


def parse_bounds(text: str, name: str) -> tuple[int, int]:
    """Parse a "lo,hi" bounds string (full-width comma tolerated)."""
    parts = [p.strip() for p in text.replace("，", ",").split(",")]
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        raise ValueError(
            f"Invalid {name}: {text!r}, expected two integers \"lo,hi\" (8-bit luma, 0-255)."
        )
    lo, hi = int(parts[0]), int(parts[1])
    if not (0 <= lo < hi <= 255):
        raise ValueError(
            f"Invalid {name}: {text!r}, expected 0 <= lo < hi <= 255."
        )
    return lo, hi
