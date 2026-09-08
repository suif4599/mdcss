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
        # 解码块以 `%25` 规则为标志，图片宽度块以 extractWidthFromAlt 为标志
        assert combined.index("%25[0-9A-Fa-f]{2}") < combined.index("extractWidthFromAlt")

    def test_enable_table_caption_adds_block(self) -> None:
        from src.builder import build_parser_blocks

        _, html_no = build_parser_blocks("none, number, number, none, latin, roman", enable_table_caption=False)
        _, html_yes = build_parser_blocks("none, number, number, none, latin, roman", enable_table_caption=True)
        assert len(html_yes) > len(html_no)

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