"""Unit tests for the pixel comparison rule."""

from __future__ import annotations

import numpy as np
import pytest

from tests_visual.harness.compare import compare_pixels


def page(value: int = 255, size: int = 32) -> np.ndarray:
    return np.full((size, size, 3), value, dtype=np.uint8)


def test_identical_pages_pass() -> None:
    assert compare_pixels(page(), page()).ok


def test_shift_within_delta_x_passes() -> None:
    reference = page()
    reference[10:20, 10:20] = 0
    actual = page()
    actual[10:20, 12:22] = 0
    assert compare_pixels(actual, reference, delta_color=12, delta_x=2).ok


def test_shift_beyond_delta_x_fails() -> None:
    reference = page()
    reference[10:20, 10:20] = 0
    actual = page()
    actual[10:20, 13:23] = 0
    result = compare_pixels(actual, reference, delta_color=12, delta_x=2)
    assert not result.ok
    assert result.failed > 0


def test_color_within_delta_passes() -> None:
    reference = page(100)
    actual = page(112)
    assert compare_pixels(actual, reference, delta_color=12).ok


def test_color_beyond_delta_fails() -> None:
    reference = page(100)
    actual = page(113)
    result = compare_pixels(actual, reference, delta_color=12)
    assert not result.ok
    assert result.failed == actual.shape[0] * actual.shape[1]


def test_shape_mismatch_raises() -> None:
    with pytest.raises(ValueError, match="shape mismatch"):
        compare_pixels(page(size=16), page(size=32))


def test_edges_only_use_in_bounds_neighbours() -> None:
    reference = page()
    reference[0, 0] = 0
    actual = page()
    actual[2, 2] = 0
    assert compare_pixels(actual, reference, delta_color=12, delta_x=2).ok
