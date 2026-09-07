"""Tests for src.font.

Functions that require a real font file are conditionally skipped
when no test font is available.
"""

import platform
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Utility functions (no real font needed)
# ---------------------------------------------------------------------------

class TestNormalizeFontFamilyName:
    def test_basic(self) -> None:
        from src.font import _normalize_font_family_name

        assert _normalize_font_family_name("  Source  Han  Sans  ") == "source han sans"


class TestSafeAssetStem:
    def test_basic(self) -> None:
        from src.font import _safe_asset_stem

        result = _safe_asset_stem("Source Han Sans SC")
        assert result == "source-han-sans-sc"

    def test_filtered_clean(self) -> None:
        from src.font import _safe_asset_stem

        result = _safe_asset_stem("Fira Code@2.0!")
        assert result == "fira-code-2-0"


class TestUniqueKeepOrder:
    def test_orders_preserved(self) -> None:
        from src.font import _unique_keep_order

        assert _unique_keep_order(["b", "a", "b", "c"]) == ["b", "a", "c"]

    def test_skips_empty(self) -> None:
        from src.font import _unique_keep_order

        assert _unique_keep_order(["a", "", "b"]) == ["a", "b"]


# ---------------------------------------------------------------------------
# resolve_font_path
# ---------------------------------------------------------------------------

class TestResolveFontPath:
    def test_file_not_found_raises_fontconfig_error(self) -> None:
        from src.font import resolve_font_path

        # Non-existent path — on non-Linux it raises NotImplementedError
        # because it falls through to fontconfig resolution
        with pytest.raises((FileNotFoundError, NotImplementedError, ValueError)):
            resolve_font_path("/nonexistent/font.ttf")

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        from src.font import resolve_font_path

        fake_font = tmp_path / "font.txt"
        fake_font.write_text("not a font")
        with pytest.raises(ValueError, match="Unsupported font file"):
            resolve_font_path(fake_font)


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-only")
class TestResolveFontPathWindows:
    """Family-name resolution on Windows (registry + font directories)."""

    def test_resolves_family_name(self) -> None:
        from src.font import resolve_font_path

        try:
            resolved = resolve_font_path("Arial")
        except (ValueError, FileNotFoundError) as exc:
            pytest.skip(f"Arial not resolvable on this Windows: {exc}")
        assert resolved.is_file()
        assert resolved.suffix.lower() in (".ttf", ".otf")

    def test_unknown_family_raises(self) -> None:
        from src.font import resolve_font_path

        with pytest.raises(ValueError, match="Font family not found on Windows"):
            resolve_font_path("Definitely-Not-A-Real-Font-12345")

    def test_resolves_collection_family(self) -> None:
        """Family names backed by a .ttc collection (e.g. 微软雅黑 / SimSun)."""
        from src.font import resolve_font_path

        for name in ("Microsoft YaHei", "SimSun"):
            try:
                resolved = resolve_font_path(name)
            except (ValueError, FileNotFoundError) as exc:
                pytest.skip(f"{name} not resolvable on this Windows: {exc}")
            assert resolved.is_file()
            assert resolved.suffix.lower() in (".ttf", ".otf", ".ttc", ".otc")


# ---------------------------------------------------------------------------
# read_font_metadata — requires a real font
# ---------------------------------------------------------------------------

def _find_test_font() -> Path | None:
    """Search common locations for a font to use in metadata tests."""
    candidates = [
        # Windows
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/times.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        p = Path(path)
        if p.is_file():
            return p
    return None


def _find_test_collection() -> Path | None:
    """Search common locations for a .ttc/.otc collection file."""
    candidates = [
        # Windows
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        # Linux (Noto CJK etc.)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        p = Path(path)
        if p.is_file():
            return p
    return None


class TestReadFontMetadata:
    @classmethod
    @pytest.fixture(scope="class")
    def test_font_path(cls) -> Path:
        font = _find_test_font()
        if font is None:
            pytest.skip("No test font found on this system")
        return font

    def test_reads_family_name(self, test_font_path: Path) -> None:
        from src.font import read_font_metadata

        family, weight, style, fmt, aliases = read_font_metadata(test_font_path)
        assert isinstance(family, str)
        assert len(family) > 0
        assert isinstance(weight, int)
        assert 100 <= weight <= 1000
        assert style in ("normal", "italic")
        assert fmt in ("truetype", "opentype", "woff", "woff2")
        assert isinstance(aliases, list)
        assert family in aliases

    def test_nonexistent_file_raises(self) -> None:
        from src.font import read_font_metadata

        with pytest.raises(FileNotFoundError):
            read_font_metadata(Path("/nonexistent/font.ttf"))

    def test_directory_raises(self, tmp_path: Path) -> None:
        from src.font import read_font_metadata

        with pytest.raises(ValueError, match="is not a file"):
            read_font_metadata(tmp_path)

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        from src.font import read_font_metadata

        fake = tmp_path / "font.txt"
        fake.write_text("not a font")
        with pytest.raises(ValueError, match="Unsupported font file"):
            read_font_metadata(fake)


class TestReadFontMetadataMany:
    @classmethod
    @pytest.fixture(scope="class")
    def collection_path(cls) -> Path:
        collection = _find_test_collection()
        if collection is None:
            pytest.skip("No .ttc/.otc collection found on this system")
        return collection

    @classmethod
    @pytest.fixture(scope="class")
    def single_font_path(cls) -> Path:
        font = _find_test_font()
        if font is None:
            pytest.skip("No test font found on this system")
        return font

    def test_collection_yields_all_faces(self, collection_path: Path) -> None:
        from src.font import read_font_metadata_many

        entries = read_font_metadata_many(collection_path)
        assert len(entries) >= 1
        for family, weight, style, fmt, aliases in entries:
            assert isinstance(family, str) and len(family) > 0
            assert 100 <= weight <= 1000
            assert style in ("normal", "italic")
            assert fmt in ("truetype", "opentype")
            assert family in aliases

    def test_single_font_file_yields_one_entry(self, single_font_path: Path) -> None:
        from src.font import read_font_metadata_many

        entries = read_font_metadata_many(single_font_path)
        assert len(entries) == 1

    def test_read_font_metadata_matches_first_entry(
        self, collection_path: Path
    ) -> None:
        from src.font import read_font_metadata, read_font_metadata_many

        first = read_font_metadata_many(collection_path)[0]
        assert read_font_metadata(collection_path) == first


class TestReadFamilyNames:
    """_read_family_names()（按名解析的轻量筛查路径）。"""

    @pytest.fixture(scope="class")
    def single_font_path(cls) -> Path:
        font = _find_test_font()
        if font is None:
            pytest.skip("No test font found on this system")
        return font

    @pytest.fixture(scope="class")
    def collection_path(cls) -> Path | None:
        collection = _find_test_collection()
        if collection is None:
            pytest.skip("No test collection found on this system")
        return collection

    def test_single_font_matches_full_read(self, single_font_path: Path) -> None:
        from src.font import _read_family_names, read_font_metadata

        full_family = read_font_metadata(single_font_path)[0]
        names = _read_family_names(single_font_path)
        assert len(names) == 1
        assert names[0] == full_family

    def test_collection_matches_full_read(self, collection_path: Path) -> None:
        from src.font import _read_family_names, read_font_metadata_many

        full_families = [e[0] for e in read_font_metadata_many(collection_path)]
        assert _read_family_names(collection_path) == full_families

    def test_invalid_file_returns_empty(self, tmp_path: Path) -> None:
        from src.font import _read_family_names

        bad = tmp_path / "broken.ttf"
        bad.write_bytes(b"not a font")
        assert _read_family_names(bad) == []

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        from src.font import _read_family_names

        assert _read_family_names(tmp_path / "nope.ttf") == []