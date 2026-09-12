"""Tests for src.builder."""

from pathlib import Path

import pytest


class TestBuildParserBlocks:
    """build_parser_blocks() output."""

    def test_returns_tuple_of_two_lists(self) -> None:
        from src.builder import build_parser_blocks

        parser_blocks, html_blocks = build_parser_blocks("none, number, number, none, latin, roman")
        assert isinstance(parser_blocks, list)
        assert isinstance(html_blocks, list)

    def test_uri_decode_block_runs_before_image_block(self) -> None:
        from src.builder import build_parser_blocks

        _, html_blocks = build_parser_blocks("none, number, number, none, latin, roman")
        combined = "\n".join(html_blocks)
        # 解码块以 `%25` 规则为标志，图片控制块以 MDCSS_CONTROL_RE 为标志
        assert combined.index("%25[0-9A-Fa-f]{2}") < combined.index("MDCSS_CONTROL_RE")

    def test_enable_table_caption_adds_block(self) -> None:
        from src.builder import build_parser_blocks

        _, html_no = build_parser_blocks("none, number, number, none, latin, roman", enable_table_caption=False)
        _, html_yes = build_parser_blocks("none, number, number, none, latin, roman", enable_table_caption=True)
        assert len(html_yes) > len(html_no)

    def test_lineshift_block_runs_before_indent(self) -> None:
        from src.builder import build_parser_blocks

        parser_blocks, _ = build_parser_blocks("none, number, number, none, latin, roman")
        combined = "\n".join(parser_blocks)
        # 行号账本块必须先于任何改变行数的 pre-parser（indent 以 has-indent 为标志）
        assert combined.index("__MDCSS_LINE_SHIFTS__") < combined.index("has-indent")

    def test_linerestore_runs_before_columnsync(self) -> None:
        from src.builder import build_parser_blocks

        _, html_blocks = build_parser_blocks("none, number, number, none, latin, roman")
        combined = "\n".join(html_blocks)
        # 行号还原块必须先于主列锚定块（linerestore 以 __mdcssOrigLine 为标志，columnsync 以 data-mdcss-cols 为标志）
        assert combined.index("__mdcssOrigLine") < combined.index("data-mdcss-cols")

    def test_mappers_are_joined_in_output(self) -> None:
        from src.builder import build_parser_blocks

        parser_blocks, _ = build_parser_blocks("number, latin, roman, none, chinese, latinUpper")
        combined = "\n".join(parser_blocks)
        assert "number" in combined
        assert "latin" in combined
        assert "roman" in combined
        assert "chinese" in combined
        assert "latinUpper" in combined

    def test_invalid_mapper_raises(self) -> None:
        from src.builder import build_parser_blocks

        with pytest.raises(ValueError, match="Unsupported mapper"):
            build_parser_blocks("invalid_mapper")

    def test_too_many_mappers_raises(self) -> None:
        from src.builder import build_parser_blocks

        with pytest.raises(ValueError, match="Too many mappers"):
            build_parser_blocks("number, number, number, number, number, number, number")


class TestBuildStyleBlocks:
    """build_style_blocks() output."""

    def test_basic_structure(self, sample_css: Path, codeblock_css: Path, tmp_path: Path) -> None:
        from src.builder import build_style_blocks

        blocks = build_style_blocks(
            font_path=None,
            main_css_path=sample_css,
            codeblock_css_path=codeblock_css,
            print_margin="5mm",
            font_assets_dir=tmp_path / "fonts",
        )
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        combined = "\n".join(blocks)
        assert ".markdown-preview.markdown-preview" in combined

    def test_heading_underline_adds_block(self, sample_css: Path, codeblock_css: Path, tmp_path: Path) -> None:
        from src.builder import build_style_blocks

        blocks_no = build_style_blocks(
            font_path=None,
            main_css_path=sample_css,
            codeblock_css_path=codeblock_css,
            print_margin="5mm",
            font_assets_dir=tmp_path / "fonts",
            heading_underline="",
        )
        blocks_yes = build_style_blocks(
            font_path=None,
            main_css_path=sample_css,
            codeblock_css_path=codeblock_css,
            print_margin="5mm",
            font_assets_dir=tmp_path / "fonts",
            heading_underline="1,2",
        )
        assert len(blocks_yes) > len(blocks_no)

    def test_table_scroll_block_added_when_disabled(self, sample_css: Path, codeblock_css: Path, tmp_path: Path) -> None:
        from src.builder import build_style_blocks

        blocks = build_style_blocks(
            font_path=None,
            main_css_path=sample_css,
            codeblock_css_path=codeblock_css,
            print_margin="5mm",
            font_assets_dir=tmp_path / "fonts",
            enable_table_horizontal_scroll=False,
        )
        combined = "\n".join(blocks)
        assert "overflow-x" in combined

    def test_fallback_rules_injected_without_parser(self, sample_css: Path, codeblock_css: Path, tmp_path: Path) -> None:
        from src.builder import build_style_blocks

        blocks = build_style_blocks(
            font_path=None,
            main_css_path=sample_css,
            codeblock_css_path=codeblock_css,
            print_margin="5mm",
            font_assets_dir=tmp_path / "fonts",
            css_fallback_features=["r"],
        )
        combined = "\n".join(blocks)
        assert 'img[alt^="30%r"]' in combined
        assert 'img[alt*=' not in combined

    def test_no_fallback_rules_with_parser(self, sample_css: Path, codeblock_css: Path, tmp_path: Path) -> None:
        from src.builder import build_style_blocks

        blocks = build_style_blocks(
            font_path=None,
            main_css_path=sample_css,
            codeblock_css_path=codeblock_css,
            print_margin="5mm",
            font_assets_dir=tmp_path / "fonts",
            enable_parser=True,
            css_fallback_features=["r"],
        )
        combined = "\n".join(blocks)
        assert 'img[alt^=' not in combined
        assert 'img[alt*=' not in combined
        assert "mdcss-inv" in combined


class TestFallbackRules:
    """build_fallback_rules() / count_fallback_rules() output."""

    def test_default_generates_100_width_only_rules(self) -> None:
        from src.builder import build_fallback_rules

        rules = build_fallback_rules([])
        assert len(rules) == 100
        assert ":has(" not in "\n".join(rules)

    def test_selectors_are_prefix_anchored(self) -> None:
        from src.builder import build_fallback_rules

        combined = "\n".join(build_fallback_rules(["r", "i"]))
        assert 'img[alt^="' in combined
        assert 'alt*=' not in combined

    def test_no_width_prefix_collision(self) -> None:
        from src.builder import build_fallback_rules

        combined = "\n".join(build_fallback_rules([]))
        assert 'img[alt^="10%"]' in combined
        assert 'img[alt^="100%"]' in combined

    def test_layout_effect_combos(self) -> None:
        from src.builder import build_fallback_rules

        combined = "\n".join(build_fallback_rules(["r", "i"]))
        assert 'img[alt^="40%ri"]' in combined
        assert 'img[alt^="40%r"]' in combined
        assert 'img[alt^="40%i"]' in combined
        assert ':has(> img[alt^="40%r"])' in combined
        assert ':has(> img[alt^="40%ri"])' in combined
        assert "filter: invert(85%);" in combined

    def test_combo_after_width_only_in_source(self) -> None:
        from src.builder import build_fallback_rules

        rules = build_fallback_rules(["r"])
        width_only = next(r for r in rules if 'img[alt^="40%"]' in r)
        row = next(r for r in rules if 'img[alt^="40%r"]' in r)
        assert rules.index(width_only) < rules.index(row)

    def test_px_never_enumerated(self) -> None:
        from src.builder import build_fallback_rules

        combined = "\n".join(build_fallback_rules(["r", "L", "R", "Lf", "Rf", "i", "m"]))
        assert "px" not in combined

    def test_single_effect_hits_threshold_exactly(self) -> None:
        from src.builder import count_fallback_rules

        assert count_fallback_rules(["i"]) == 200

    def test_count_matches_len(self) -> None:
        from src.builder import build_fallback_rules, count_fallback_rules

        assert count_fallback_rules(["r", "i"]) == len(build_fallback_rules(["r", "i"]))


class TestFallbackPrintResets:
    """build_fallback_print_resets() output."""

    def test_empty_without_effects(self) -> None:
        from src.builder import build_fallback_print_resets

        assert build_fallback_print_resets([]) == ""
        assert build_fallback_print_resets(["r"]) == ""

    def test_effect_prefixes_enumerated(self) -> None:
        from src.builder import build_fallback_print_resets

        resets = build_fallback_print_resets(["r", "i"])
        assert 'img[alt^="40%i"]' in resets
        assert 'img[alt^="40%ri"]' in resets
        assert "filter: none !important;" in resets
        assert "mix-blend-mode: normal !important;" in resets


class TestWriteOutput:
    """write_output() file generation."""

    def test_creates_style_less(self, tmp_output_dir: Path) -> None:
        from src.builder import write_output

        write_output(tmp_output_dir, [".test-class { color: red; }"])
        assert (tmp_output_dir / "style.less").exists()

    def test_creates_parser_js_with_blocks(self, tmp_output_dir: Path) -> None:
        from src.builder import write_output

        write_output(tmp_output_dir, [], parse_blocks=["// test parser"], html_blocks=[])
        assert (tmp_output_dir / "parser.js").exists()

    def test_creates_head_html_with_header_blocks(self, tmp_output_dir: Path) -> None:
        from src.builder import write_output

        write_output(tmp_output_dir, [], header_blocks=["// test header"])
        assert (tmp_output_dir / "head.html").exists()

    def test_no_parser_when_no_blocks(self, tmp_output_dir: Path) -> None:
        from src.builder import write_output

        write_output(tmp_output_dir, [".a { color: red; }"])
        assert not (tmp_output_dir / "parser.js").exists()