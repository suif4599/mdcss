"""Tolerance comparison for rendered pages.

A rendered pixel passes when any reference pixel inside a
(2 * delta_x + 1) square around it has a per-channel difference of at most
delta_color. The page passes only when every rendered pixel passes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CompareResult:
    ok: bool
    failed: int
    mask: np.ndarray


def compare_pixels(
    actual: np.ndarray,
    expected: np.ndarray,
    delta_color: int = 12,
    delta_x: int = 2,
) -> CompareResult:
    if actual.shape != expected.shape:
        raise ValueError(
            f"page shape mismatch: rendered {actual.shape}, reference {expected.shape}"
        )
    actual_i = actual.astype(np.int16)
    expected_i = expected.astype(np.int16)
    height, width = actual.shape[:2]
    passed = np.zeros((height, width), dtype=bool)
    for dy in range(-delta_x, delta_x + 1):
        actual_rows = slice(max(0, -dy), min(height, height - dy))
        expected_rows = slice(max(0, dy), min(height, height + dy))
        for dx in range(-delta_x, delta_x + 1):
            actual_cols = slice(max(0, -dx), min(width, width - dx))
            expected_cols = slice(max(0, dx), min(width, width + dx))
            difference = np.abs(
                actual_i[actual_rows, actual_cols] - expected_i[expected_rows, expected_cols]
            ).max(axis=2)
            passed[actual_rows, actual_cols] |= difference <= delta_color
    mask = ~passed
    failed = int(mask.sum())
    return CompareResult(ok=failed == 0, failed=failed, mask=mask)
