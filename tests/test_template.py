"""Tests for src.template."""

from pathlib import Path

import pytest


class TestLoadTemplate:
    """load_template() basic behavior."""

    def test_load_css_template(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template("css", "style.css")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_load_parser_template(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template("parser", "preparser_column.js")
        assert isinstance(result, str)
        assert "mergeColumnSpec" in result

    def test_load_docheader_template(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template("docheader", "image_effects.js")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_missing_template_raises(self, template_dir: Path) -> None:
        from src.template import load_template

        with pytest.raises(FileNotFoundError):
            load_template("css", "non_existent.css")

    def test_unknown_directory_raises(self, template_dir: Path) -> None:
        from src.template import load_template

        with pytest.raises(FileNotFoundError):
            load_template("unknown", "style.css")

    def test_output_ends_with_newline(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template("css", "style.css")
        assert result.endswith("\n")


class TestTemplateSubstitution:
    """load_template() placeholder replacement."""

    def test_substitution_works(self, template_dir: Path, tmp_path: Path) -> None:
        """Test <variable>...<variable/> substitution in a custom template."""
        from src.template import load_template

        result = load_template("css", "printstyle.css",
                               new_rules="body { color: red; }",
                               print_margin="10mm",
                               fallback_print_resets="")
        assert "body { color: red; }" in result
        assert "10mm" in result or "10mm" in result.lower() or "10 mm" in result

    def test_missing_placeholder_raises(self, tmp_path: Path) -> None:
        """Substituting a key that has no placeholder in the template."""
        from src.template import load_template, TEMPLATE_DIR

        # Use a template that definitely doesn't have a custom placeholder
        with pytest.raises(ValueError, match="Placeholder"):
            load_template("css", "style.css", non_existent_key="hello")


class TestImageTemplates:
    """Image postparser templates contain the pipe-grammar machinery."""

    def test_postparser_image_content(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template("parser", "postparser_image.js")
        assert "MDCSS_CONTROL_RE" in result
        assert "data-mdcss-cap" in result
        assert "mdcss-inv" in result

    def test_postparser_imagetitle_content(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template("parser", "postparser_imagetitle.js")
        assert "mdcss-fig-row" in result
        assert "mdcss-fig-group" in result
        assert "mdcss-fig-float-" in result

    def test_style_css_has_no_alt_selectors(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template("css", "style.css")
        assert "mdcss-" in result
        assert "alt*=" not in result
        assert "alt$=" not in result

    def test_printstyle_fallback_resets_placeholder(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template(
            "css", "printstyle.css",
            new_rules="body { color: red; }",
            print_margin="10mm",
            fallback_print_resets='img[alt^="40%i"] { filter: none; }',
        )
        assert 'img[alt^="40%i"] { filter: none; }' in result


class TestColumnTemplates:
    """Multi-column templates contain the main-column machinery."""

    def test_preparser_column_content(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template("parser", "preparser_column.js")
        assert "mergeColumnSpec" in result
        assert "data-mdcss-cols" in result
        assert "data-mdcss-col=" in result

    def test_lineshift_content(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template("parser", "preparser_lineshift.js")
        assert "__MDCSS_LINE_SHIFTS__" in result
        assert "__mdcssOrigLine" in result
        assert "__mdcssRecordLineDiff" in result

    def test_linediff_closes_the_pre_pipeline(self, template_dir: Path) -> None:
        from src.builder import PRE_PASSES
        from src.template import load_template

        result = load_template("parser", "preparser_linediff.js")
        assert "__mdcssRecordLineDiff" in result
        assert PRE_PASSES[-1][0] == "preparser_linediff.js"

    def test_postparser_linerestore_content(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template("parser", "postparser_linerestore.js")
        assert "data-source-line" in result
        assert "__mdcssOrigLine" in result

    def test_postparser_columnsync_content(self, template_dir: Path) -> None:
        from src.template import load_template

        result = load_template("parser", "postparser_columnsync.js")
        assert "data-mdcss-cols" in result
        assert 'data-mdcss-col="main"' in result
        assert "data-source-line" in result


class TestTemplateDirectory:
    """TEMPLATE_DIR path resolution."""

    def test_template_dir_exists(self) -> None:
        from src.template import TEMPLATE_DIR

        assert TEMPLATE_DIR.exists()
        assert TEMPLATE_DIR.is_dir()
        assert (TEMPLATE_DIR / "css").exists()
        assert (TEMPLATE_DIR / "parser").exists()
        assert (TEMPLATE_DIR / "docheader").exists()