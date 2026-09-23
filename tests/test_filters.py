"""Tests for src.filters — bounds parsing for the I/M image effects."""

import pytest

from src.filters import DEFAULT_INVERT_BOUNDS, DEFAULT_MATTE_BOUNDS, parse_bounds


class TestParseBounds:
    def test_plain(self) -> None:
        assert parse_bounds("32,239", "invert bounds") == (32, 239)

    def test_full_width_comma_and_spaces(self) -> None:
        assert parse_bounds(" 5，250 ", "matte bounds") == (5, 250)

    def test_zero_lo(self) -> None:
        assert parse_bounds("0,255", "invert bounds") == (0, 255)

    @pytest.mark.parametrize("bad", ["", "32", "a,b", "32,239,1", "239,32", "-1,200", "32,256"])
    def test_invalid_raises(self, bad: str) -> None:
        with pytest.raises(ValueError):
            parse_bounds(bad, "invert bounds")

    def test_defaults(self) -> None:
        assert DEFAULT_INVERT_BOUNDS == (32, 239)
        assert DEFAULT_MATTE_BOUNDS == (64, 239)
