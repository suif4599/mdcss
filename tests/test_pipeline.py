"""Functional tests for the assembled parser.js pipeline.

The pre fragments (markdown -> markdown) run directly; the post fragments
(html -> html) run against fixtures baked from a real markdown-it 14
(html: true) capture — the shapes carry the exact paragraph/table/attribute
structure the regexes are coupled to (data-source-line placement, table cell
backslash halving, <p>/<table> adjacency). MPE's own crossnote renderer
cannot be imported here; test_md/ is the manual crosscheck against the real
preview. When a fixture starts drifting from a crossnote update, re-capture
and re-bake.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RUNNER = Path(__file__).parent / "pipeline" / "runner.mjs"
NODE = shutil.which("node")

needs_node = pytest.mark.skipif(NODE is None, reason="node not available")

DEFAULT_MAPPERS = "none, chinese, number, number, latin, roman"


def run_pipeline(
    markdown: str = "",
    html: str = "",
    mappers: str = DEFAULT_MAPPERS,
    enable_table_caption: bool = True,
) -> dict:
    """Run the assembled pre/post fragments in one node process.

    The fragment order comes from build_parser_blocks — the single source of
    truth for the emitted parser.js. One process per call so the line-shift
    ledger on globalThis is fresh, mirroring MPE's persistent context.
    """
    from src.builder import build_parser_blocks

    parse_blocks, html_blocks = build_parser_blocks(mappers, enable_table_caption)
    payload = json.dumps(
        {
            "pre": "\n".join(parse_blocks),
            "post": "\n".join(html_blocks),
            "markdown": markdown,
            "html": html,
        }
    )
    proc = subprocess.run([NODE, RUNNER], input=payload, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def pre(markdown: str, mappers: str = DEFAULT_MAPPERS) -> dict:
    return run_pipeline(markdown=markdown, mappers=mappers)


def post(html: str) -> str:
    return run_pipeline(html=html)["html"]


# Baked markdown-it output shapes (see module docstring).
FLOAT_IMG_HTML = (
    '<p data-source-line="1"><img src="x.png" alt="40%Lf|.f"></p>\n'
    '<p data-source-line="3">wrapped text</p>\n'
)
ROW_IMGS_HTML = (
    '<p data-source-line="1">'
    '<img src="x.png" alt="25%r|.subA(.title)"> '
    '<img src="x.png" alt="25%r|.subB"></p>\n'
)
CAPTION_IMG_HTML = '<p data-source-line="1"><img src="x.png" alt="40%|.cap"></p>\n'


def _table_html(first_col: str, rows: list[tuple[str, ...]]) -> str:
    # markdown-it emits every th/td on its own line; the merge regexes'
    # trailing (.*)</td> silently relies on this one-cell-per-line shape.
    head = "\n".join(f"<th>{c}</th>" for c in (first_col, "b")) + "\n"
    body = "".join(
        f'<tr data-source-line="{3 + i}">\n' + "\n".join(f"<td>{c}</td>" for c in row) + "\n</tr>\n"
        for i, row in enumerate(rows)
    )
    return (
        '<table data-source-line="1">\n<thead data-source-line="1">\n'
        f'<tr data-source-line="1">\n{head}</tr>\n</thead>\n'
        f'<tbody data-source-line="3">\n{body}</tbody>\n</table>\n'
    )


TAGGED_TABLE_HTML = (
    '<p data-source-line="1">Table@zebra@: .cap</p>\n' + _table_html("a", [("1", "2")])
)
CAPTION_TABLE_HTML = '<p data-source-line="1">Table: .cap</p>\n' + _table_html("a", [("1", "2")])
BANDS_TABLE_HTML = _table_html("a", [("r2 x", "y"), ("@MDCSS_BS_1@", "z"), ("p", "q")])
MERGE_TABLE_HTML = _table_html("c2: H1", [(":c2: x", "r2 y"), ("@MDCSS_BS_1@", "@MDCSS_BS_1@")])
COL_HTML = (
    '<p data-source-line="1">para</p>\n'
    '<div style="display: grid; grid-template-columns: minmax(auto, 1fr) minmax(auto, 30%); '
    'gap: 20px; width: 100%; min-width: 0; box-sizing: border-box;" '
    'data-mdcss-cols="minmax(auto, 1fr) minmax(auto, 30%)">\n'
    '<div style="display: flex; flex-direction: column; justify-content: flex-start; '
    'min-width: 0; max-width: 100%;" data-mdcss-col="main" data-mdcss-col-align="flex-start">\n'
    '<p data-source-line="15">main text</p>\n</div>\n'
    '<div style="display: flex; flex-direction: column; justify-content: flex-start; '
    'min-width: 0; max-width: 100%;" data-mdcss-col="side" data-mdcss-col-align="flex-start">\n'
    '<p data-source-line="25">side text</p>\n</div></div>\n'
    '<p data-source-line="31">after</p>\n'
)
INDENT_HTML = (
    '<div class="has-indent">\n'
    '<p data-source-line="5">para one</p>\n'
    '<p data-source-line="7">para two</p>\n'
    '</div>\n'
)


@needs_node
class TestPreFence:
    """Fence extraction protects mdcss syntax inside column-0 fences."""

    def test_column_syntax_inside_fence_untouched(self) -> None:
        out = pre("```\n|||-40\nfenced\n|||\n```\n")["markdown"]
        assert "|||-40" in out
        assert "data-mdcss-cols" not in out

    def test_heading_dot_inside_fence_not_numbered(self) -> None:
        out = pre("```md\n## .fenced\n```\n")["markdown"]
        assert "## .fenced" in out
        assert "一、" not in out

    def test_zebra_tag_inside_fence_untouched(self) -> None:
        out = pre("```md\nTable<zebra>: x\n```\n")["markdown"]
        assert "Table<zebra>: x" in out
        assert "Table@" not in out

    def test_zebra_tag_in_indented_fence_untouched(self) -> None:
        # Regression (was bug B1): the old column-0-only fence regex let the
        # zebra rewrite corrupt tagged lines inside indented fences (lists).
        out = pre("  ```md\n  Table<zebra>: x\n  ```\n")["markdown"]
        assert "Table<zebra>: x" in out
        assert "Table@" not in out

    def test_tilde_fence_untouched(self) -> None:
        out = pre("~~~\n|||-40\nTable<zebra>: x\n~~~\n")["markdown"]
        assert "|||-40" in out
        assert "Table<zebra>: x" in out
        assert "data-mdcss-cols" not in out

    def test_unclosed_fence_protected_to_eof(self) -> None:
        out = pre("```md\n|||-40\n## .never numbered\n")["markdown"]
        assert "|||-40" in out
        assert "## .never numbered" in out

    def test_fence_inside_list_item_protected(self) -> None:
        md = "- item\n\n  ```\n  |||-\n  fenced\n  |||\n  ```\n"
        out = pre(md)["markdown"]
        assert "|||-" in out
        assert "data-mdcss-cols" not in out

    def test_column_syntax_in_indented_content_ignored(self) -> None:
        # Documented limitation: column markup only fires at column 0, so
        # indented (e.g. in-list) ||| lines are inert — no corruption though.
        out = pre("  |||-40\n  left\n\n  |||\n\n  right\n\n  -|||\n")["markdown"]
        assert "data-mdcss-cols" not in out


@needs_node
class TestPreColumn:
    def test_basic_two_column_grid(self) -> None:
        out = pre("|||-40\n\nleft\n\n|||\n\nright\n\n-|||\n")["markdown"]
        assert 'data-mdcss-cols="minmax(auto, 40%) minmax(auto, 1fr)"' in out
        assert 'data-mdcss-col="main"' in out
        assert 'data-mdcss-col="side"' in out

    def test_percent_widths_over_100_normalized(self) -> None:
        out = pre("|||-60\n\na\n\n|||60\n\nb\n\n-|||\n")["markdown"]
        assert 'data-mdcss-cols="minmax(auto, 50%) minmax(auto, 50%)"' in out

    def test_main_marker_selects_column(self) -> None:
        out = pre("|||-\n\na\n\n|||50!\n\nb\n\n-|||\n")["markdown"]
        assert out.index('data-mdcss-col="side"') < out.index('data-mdcss-col="main"')

    def test_center_alignment_marker(self) -> None:
        out = pre("|||-\n\na\n\n|||:50%:\n\nb\n\n-|||\n")["markdown"]
        assert 'data-mdcss-col-align="center"' in out

    def test_line_mapping_restored_through_ledger(self) -> None:
        # The auto-diff ledger (preparser_linediff.js) maps every final line
        # back to its original editor line: content lines keep their numbers,
        # spec lines collapse into the div blocks.
        md = "para\n\n|||-\n\nmain\n\n|||30\n\nside\n\n-|||\n\nafter\n"
        res = pre(md)
        final = res["markdown"].split("\n")
        for text, orig in (("para", 1), ("main", 5), ("side", 9), ("after", 13)):
            assert res["mapped"][final.index(text)] == orig


@needs_node
class TestPreTitlePrefix:
    def test_default_mappers(self) -> None:
        out = pre("# .Top\n\n## .Alpha\n\n### .Beta\n\n#### .Gamma\n\n## Plain\n")["markdown"]
        assert "# Top" in out
        assert "## 一、Alpha" in out
        assert "### 1​. Beta" in out
        assert "#### 1​.​1 Gamma" in out  # number composes with a numeric prefix
        assert "## Plain" in out

    def test_latin_roman_mappers(self) -> None:
        out = pre("## .a\n\n### .b\n", mappers="none, latin, roman, none, none, none")["markdown"]
        assert "## a) a" in out
        assert "### i) b" in out


@needs_node
class TestPreIndent:
    def test_indent_wraps_document(self) -> None:
        res = pre("@indent\n\npara\n")
        assert '<div class="has-indent">' in res["markdown"]
        final = res["markdown"].split("\n")
        assert res["mapped"][final.index("para")] == 3

    def test_angle_bracket_form(self) -> None:
        assert "<indent>" not in pre("<indent>\n\npara\n")["markdown"]
        assert '<div class="has-indent">' in pre("<indent>\n\npara\n")["markdown"]


@needs_node
class TestPreTableCell:
    """Backslash-run protection: whole-cell runs become @MDCSS_BS_N@ tokens."""

    def test_delete_marker_tokenized(self) -> None:
        assert "@MDCSS_BS_1@" in pre("| a | \\\n| - | -\n")["markdown"]

    def test_two_backslashes_tokenized(self) -> None:
        assert "@MDCSS_BS_2@" in pre("| a | \\\\\n")["markdown"]

    def test_indented_rows_still_tokenized(self) -> None:
        assert "@MDCSS_BS_1@" in pre("  | a | \\\n")["markdown"]

    def test_indented_code_block_rows_untouched(self) -> None:
        # 4-space indent is an indented code block, not a table row
        src = "    | a | \\\n"
        assert pre(src)["markdown"] == src

    def test_backslashes_inside_content_untouched(self) -> None:
        src = "| a\\*b | c |\n"
        assert pre(src)["markdown"] == src

    def test_escaped_pipe_separator_untouched(self) -> None:
        src = "| a\\|b | c |\n"
        assert pre(src)["markdown"] == src


@needs_node
class TestPreZebraAndPdf:
    def test_zebra_tag_normalized_to_sentinel(self) -> None:
        assert "Table@zebra@: .cap" in pre("Table<zebra>: .cap\n")["markdown"]

    def test_zebra_tag_case_insensitive(self) -> None:
        assert "Table@nozebra@: x" in pre("TABLE<NOZEBRA>: x\n")["markdown"]

    def test_pdf_import_args_preserved_verbatim(self) -> None:
        out = pre('@import "./doc.pdf" {page_no=1}\n')["markdown"]
        assert 'display: flex; justify-content: center' in out
        assert '@import "./doc.pdf" {page_no=1}' in out
        assert "{{" not in out  # regression: braces used to double

    def test_pdf_import_without_args(self) -> None:
        out = pre('@import "./plain.pdf"\n')["markdown"]
        assert '@import "./plain.pdf"' in out
        assert "undefined" not in out  # regression: used to emit {undefined}


@needs_node
class TestPreFixtures:
    """Smoke: test_md/ manual-verification docs pass the pre pipeline cleanly."""

    @pytest.mark.parametrize("name", ["test_column.md", "test_image.md", "test_table.md"])
    def test_no_leftover_fence_tokens(self, name: str, project_root: Path) -> None:
        md = (project_root / "test_md" / name).read_text(encoding="utf-8")
        out = pre(md)["markdown"]
        assert "@@MDCSS_FENCE_BLOCK" not in out

    def test_column_fixture_produces_grids(self, project_root: Path) -> None:
        md = (project_root / "test_md" / "test_column.md").read_text(encoding="utf-8")
        assert "data-mdcss-cols" in pre(md)["markdown"]


@needs_node
class TestLineDiff:
    def test_combined_transforms_map_exact_lines(self) -> None:
        # indent + fence + column + pdf in one document: every original
        # content line must map back to exactly its own line number.
        md = (
            "@indent\n\npara\n\n```\n|||-40\nfenced\n```\n\n"
            "|||-\n\nmain\n\n|||30\n\nside\n\n-|||\n\n"
            '@import "./x.pdf" {page_no=1}\n'
        )
        res = pre(md)
        final = res["markdown"].split("\n")
        original = md.split("\n")
        for text in ("para", "fenced", "main", "side", '@import "./x.pdf" {page_no=1}'):
            assert res["mapped"][final.index(text)] == original.index(text) + 1


@needs_node
class TestPostImage:
    def img(self, alt: str) -> str:
        return post(f'<p><img src="x.png" alt="{alt}"></p>')

    def test_width_percent(self) -> None:
        out = self.img("40%")
        assert "width: 40% !important" in out
        assert 'alt=""' in out  # control string never leaks into the output alt

    def test_width_caps_at_100_percent(self) -> None:
        assert "width: 100% !important" in self.img("250%")

    def test_px_width_uncapped(self) -> None:
        assert "width: 360px !important" in self.img("360px")

    @pytest.mark.parametrize(
        ("token", "cls"),
        [("40%L", "mdcss-left"), ("40%R", "mdcss-right"), ("40%r", "mdcss-row"),
         ("40%Lf", "mdcss-float-left"), ("40%Rf", "mdcss-float-right")],
    )
    def test_layout_classes(self, token: str, cls: str) -> None:
        assert cls in self.img(token)

    def test_effect_classes(self) -> None:
        assert 'mdcss-inv"' in self.img("40%i")
        assert 'mdcss-mix"' in self.img("40%m")

    def test_canvas_effect_bounds_become_class_suffix(self) -> None:
        assert "mdcss-bright-10-250" in self.img("40%I(10,250)")

    def test_invalid_bounds_fall_back_to_plain_class(self) -> None:
        out = self.img("40%I(250,10)")
        assert 'mdcss-bright"' in out
        assert "mdcss-bright-" not in out

    def test_real_alt_untouched(self) -> None:
        img = '<p><img src="x.png" alt="An English alt"></p>'
        assert post(img) == img

    def test_pipe_fields_beyond_control_do_not_trigger(self) -> None:
        img = '<p><img src="x.png" alt="a|b"></p>'
        assert post(img) == img

    def test_caption_and_real_alt(self) -> None:
        out = self.img("40%|.cap|real alt|with pipes")
        assert 'alt="real alt|with pipes"' in out
        assert "图1:\tcap" in out  # imagetitle consumes the caption marker
        assert "40%" not in out.split("alt=")[1][:12]

    def test_numeric_alt_becomes_width_known_footgun(self) -> None:
        # Documented footgun: a pure-number alt parses as a width control.
        out = self.img("2023")
        assert "width: 100% !important" in out
        assert 'alt=""' in out


@needs_node
class TestPostImageTitle:
    def test_caption_becomes_numbered_figure(self) -> None:
        out = post(CAPTION_IMG_HTML)
        assert '<figure class="mdcss-fig"' in out
        assert "图1:\tcap" in out
        assert 'alt="cap"' in out  # caption doubles as the output alt

    def test_numbering_increments(self) -> None:
        out = post(
            '<p><img src="x.png" alt="40%|.a"></p>\n<p><img src="x.png" alt="40%|.b"></p>\n'
        )
        assert "图1:\ta" in out
        assert "图2:\tb" in out

    def test_caption_without_dot_not_numbered(self) -> None:
        out = post('<p><img src="x.png" alt="40%|plain"></p>')
        assert "plain</figcaption>" in out
        assert "图" not in out

    def test_row_group_subfigure_labels_and_group_title(self) -> None:
        out = post(ROW_IMGS_HTML)
        assert "mdcss-fig-group" in out
        assert "(a)\tsubA" in out
        assert "(b)\tsubB" in out
        assert "图1:\ttitle" in out

    def test_float_figure_built_but_paragraph_merge_inert(self) -> None:
        # Characterization: the merge regex expects the float figure OUTSIDE a
        # <p>, but markdown-it wraps a lone image paragraph — so figure and
        # text stay in separate <p> blocks and text wrapping relies on CSS
        # float alone. Whether crossnote emits the unwrapped shape is
        # unverified; revisit with the real preview.
        out = post(FLOAT_IMG_HTML)
        assert "mdcss-fig-float-left" in out
        assert "图1:\tf" in out
        assert out.count("<p") == 2  # merge did not fire


@needs_node
class TestPostTable:
    def test_merge_and_delete(self) -> None:
        out = post(MERGE_TABLE_HTML)
        # header: c2: -> colspan 2, trailing ':' = right align
        assert 'colspan="2">H1</th>' in out
        assert "text-align: right" in out
        # :c2: x -> colspan 2 centered; r2 y -> rowspan 2
        assert 'colspan="2" rowspan="1">x</td>' in out
        assert "text-align: center" in out
        assert 'rowspan="2">y</td>' in out
        # backslash cells arrive as protected tokens and are deleted
        assert "@MDCSS_BS_1@" not in out

    def test_backslash_token_semantics(self) -> None:
        # N source backslashes -> @MDCSS_BS_N@ (pre pass) -> N=1 deletes the
        # cell, N>=2 renders N-1 literal backslashes.
        def cell(n: int) -> str:
            return post(f'<table><tbody><tr><td>@MDCSS_BS_{n}@</td><td>x</td></tr></tbody></table>')

        assert "<td>x</td>" in cell(1) and "@MDCSS_BS_1@" not in cell(1)  # deleted
        assert "<td>\\</td>" in cell(2)  # 2 -> one literal
        assert "<td>\\\\</td>" in cell(3)  # 3 -> two literals
        assert cell(5).count("\\") == 4

    def test_leftover_tokens_restored_as_markdown_it_would(self) -> None:
        out = post("<p>@MDCSS_BS_2@ and @MDCSS_BS_1@</p>")
        assert "<p>\\ and \\</p>" in out

    def test_legacy_raw_backslash_fallback(self) -> None:
        # Pipe-less tables never pass the pre pass's '|' guard; markdown-it
        # halves their backslashes, and the legacy exactly-N rules still apply.
        deleted = post("<table><tbody><tr><td>\\</td><td>x</td></tr></tbody></table>")
        assert "<td>x</td>" in deleted and "<td>\\</td>" not in deleted
        escaped = post("<table><tbody><tr><td>\\\\</td><td>x</td></tr></tbody></table>")
        assert "<td>\\</td>" in escaped


@needs_node
class TestPostZebra:
    def test_untagged_table_defaults_to_auto_bands(self) -> None:
        out = post(BANDS_TABLE_HTML)
        assert 'class="mdcss-auto"' in out
        # rowspan merge unions rows 1-2 into band 0 (unstriped); row 3 is band 1
        assert '<tr class="mdcss-z" data-source-line="5">' in out
        assert '<tr class="mdcss-z" data-source-line="3">' not in out

    def test_tagged_zebra_keeps_plain_striping(self) -> None:
        out = post(TAGGED_TABLE_HTML)
        assert 'class="mdcss-zebra"' in out
        assert 'mdcss-z"' not in out  # no band marking outside auto mode
        assert "Table@zebra@:" not in out  # tag consumed

    def test_tagged_nozebra(self) -> None:
        html = TAGGED_TABLE_HTML.replace("Table@zebra@:", "Table@nozebra@:")
        out = post(html)
        assert 'class="mdcss-nozebra"' in out
        assert 'mdcss-z"' not in out


@needs_node
class TestPostTableCaption:
    def test_caption_wraps_table_in_figure(self) -> None:
        out = post(CAPTION_TABLE_HTML)
        assert "<figure" in out
        assert "表1:\tcap" in out
        assert "<table" in out

    def test_disabled_via_flag(self) -> None:
        out = run_pipeline(html=CAPTION_TABLE_HTML, enable_table_caption=False)["html"]
        assert "表1:" not in out
        assert "Table: .cap" in out


@needs_node
class TestPostUriDecode:
    def test_double_encoded_local_src_restored(self) -> None:
        out = post('<p><img src="img%25E4%B8%AD.png" alt="alt"></p>')
        assert 'src="img%E4%B8%AD.png"' in out

    def test_remote_src_untouched(self) -> None:
        img = '<p><img src="https://e.com/a%25b.png" alt="alt"></p>'
        assert post(img) == img


@needs_node
class TestLineRestore:
    def test_indent_shifts_mapped_back(self) -> None:
        out = run_pipeline(markdown="@indent\n\npara one\n\npara two\n", html=INDENT_HTML)["html"]
        assert '<p data-source-line="3">para one</p>' in out
        assert '<p data-source-line="5">para two</p>' in out


@needs_node
class TestColumnSync:
    """Columnsync consumes the baked column html (transformed line coords 15/25/31)."""

    MD = "para\n\n|||-\n\nmain text\n\n|||30\n\nside text\n\n-|||\n\nafter\n"

    def test_main_column_anchored_side_column_frozen(self) -> None:
        out = run_pipeline(markdown=self.MD, html=COL_HTML)["html"]
        # container + main column content anchored at the section's first line (5)
        assert 'data-mdcss-cols="minmax(auto, 1fr) minmax(auto, 30%)" data-source-line="5"' in out
        assert '<p data-source-line="5">main text</p>' in out
        # side column stops driving the scroll map
        assert "<p>side text</p>" in out
        # side lines after the main range get sentinel anchors at the main column bottom
        assert '<div data-source-line="9"></div><div data-source-line="9"></div>' in out
        # content after the section keeps its own line
        assert '<p data-source-line="13">after</p>' in out
