"""Tests for src.print_style."""

from pathlib import Path

import pytest


class TestGeneratePrintStyle:
    """generate_print_style() output."""

    def test_basic_generation(self, sample_css: Path, codeblock_css: Path) -> None:
        from src.print_style import generate_print_style

        result = generate_print_style(sample_css, codeblock_css, print_margin="5mm")
        assert isinstance(result, str)
        assert len(result) > 0
        # Must contain the print media query
        assert "@media print" in result

    def test_css_selectors_are_converted(self, sample_css: Path, codeblock_css: Path) -> None:
        from src.print_style import generate_print_style

        result = generate_print_style(sample_css, codeblock_css, print_margin="5mm")
        # User's ".markdown-preview.markdown-preview h1" → "body h1"
        assert "body h1" in result
        # The template preserves ".markdown-preview" for PDF image & pagination rules,
        # so we only verify that user CSS selectors were converted.

    def test_print_margin_appears_in_output(self, sample_css: Path, codeblock_css: Path) -> None:
        from src.print_style import generate_print_style

        result = generate_print_style(sample_css, codeblock_css, print_margin="10mm")
        assert "10mm" in result

    def test_zebra_strategy_rules_present(self, sample_css: Path, codeblock_css: Path) -> None:
        from src.print_style import generate_print_style

        result = generate_print_style(sample_css, codeblock_css, print_margin="5mm")
        # auto 条带打印实色 + nth-child 抑制（zebra/nozebra 共用），抑制在前、条带在后靠顺序取胜
        assert "html body table.mdcss-auto tbody tr.mdcss-z td" in result
        assert "html body table.mdcss-nozebra tbody tr:nth-child(2n) td" in result
        assert result.index("html body table.mdcss-auto tbody tr:nth-child(2n) td") < result.index(
            "html body table.mdcss-auto tbody tr.mdcss-z td"
        )

    def test_missing_css_warns(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        from src.print_style import generate_print_style

        missing = tmp_path / "missing.css"
        # Should warn but not crash
        result = generate_print_style(missing, missing, print_margin="5mm")
        assert result == "/* Error: no CSS content loaded */"
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_ui_keywords_filtered(self, tmp_path: Path) -> None:
        from src.print_style import generate_print_style

        css_path = tmp_path / "test.css"
        # Sidebar is a UI keyword — should be filtered out
        css_path.write_text(
            ".markdown-preview.sidebar { color: red; }\n"
            ".markdown-preview p { color: #333; }\n"
        )
        result = generate_print_style(css_path, css_path, print_margin="5mm")
        assert "sidebar" not in result.lower()
        assert "color" in result

    def test_disallowed_props_removed(self, tmp_path: Path) -> None:
        from src.print_style import generate_print_style

        css_path = tmp_path / "test.css"
        css_path.write_text(
            ".markdown-preview.markdown-preview {\n"
            "  font-family: 'Arial';\n"      # in disallowed_print_props
            "  color: #333;\n"                # should pass through
            "}\n"
        )
        result = generate_print_style(css_path, css_path, print_margin="5mm")
        assert "font-family" not in result
        assert "color" in result

    def test_no_valid_styles_raises(self, tmp_path: Path) -> None:
        from src.print_style import generate_print_style

        css_path = tmp_path / "test.css"
        # Only UI selectors → nothing to extract
        css_path.write_text(".markdown-preview.sidebar { color: red; }")
        with pytest.raises(ValueError, match="No valid styles extracted"):
            generate_print_style(css_path, css_path, print_margin="5mm")


class TestInternalHelpers:
    """Internal helper functions in print_style."""

    def test_is_ui_selector(self) -> None:
        from src.print_style import _is_ui_selector

        assert _is_ui_selector(".sidebar a")
        assert _is_ui_selector("body .sidebar")
        assert not _is_ui_selector("p")
        assert not _is_ui_selector("h1")

    def test_convert_selector(self) -> None:
        from src.print_style import _convert_selector

        assert _convert_selector(".markdown-preview.markdown-preview h1") == "body h1"
        assert _convert_selector(".markdown-preview p") == "body p"
        assert _convert_selector("body") == "body"