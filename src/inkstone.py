"""Emission of the Inkstone bridge artifacts.

Inkstone (a markdown-it based browser notebook) embeds the mdcss syntax
extensions through two generated files committed into its repository:

- mdcss-bridge.js — an ESM module exporting mdcssPre(source) / mdcssPost(html),
  assembled from the same parser fragments as the MPE parser.js but wrapped
  for a sanitize-in-the-middle pipeline: Inkstone runs DOMPurify between the
  markdown-it render and the post pass, and DOMPurify strips inline style
  attributes. Therefore the pre pass only emits sanitizer-safe markup
  (classes + data-* attributes), and everything needing inline styles is
  applied by the post pass (image widths/layouts, table merges, column grids
  rebuilt from data attributes by postparser_columnstyle.js).
  The emitted code must be comment-free: Inkstone's repo check
  (scripts/check-comments.mjs) rejects any comment under src/.

- mdcss.css — the portable subset of the preview CSS, scoped to .ink-prose.
  Image effects (i/I/m) are gated on the dark theme (:root[data-theme='dark'])
  instead of MPE's @media print reset: they follow the active browser theme.
  Fonts, print styles, and theme colors are intentionally not bridged.
"""

import re
from pathlib import Path

from src.builder import parse_mappers
from src.template import load_template

# Pre-pass fragments in execution order. Fence extraction must come before the
# line-rewriting passes and its restore must come last (same contract as the
# MPE assembly in builder.build_parser_blocks). The MPE-only fragments
# (preparser_pdf, preparser_invert_brightness, postparser_uri_decode,
# postparser_columnsync) are not part of the bridge: the pdf import depends on
# crossnote's pdf2svg, the SVG filter is appended post-sanitization by
# postparser_svgfilter instead, uri_decode fixes a crossnote-only double
# encoding bug, and columnsync targets crossnote's scroll-sync internals.
PRE_FRAGMENTS = (
    "preparser_lineshift.js",
    "preparser_indent.js",
    "preparser_fence_extract.js",
    "preparser_titleprefix.js",
    "preparser_column.js",
    "preparser_fence_restore.js",
)

# Post-pass fragments in execution order: image/table/tablecaption/imagetitle
# mirror the MPE order; columnstyle rebuilds the styles DOMPurify stripped;
# svgfilter appends the invert-brightness filter definition; linerestore maps
# data-line values back to original editor lines (renamed from crossnote's
# data-source-line attribute).
POST_FRAGMENTS = (
    "postparser_image.js",
    "postparser_table.js",
    "postparser_tablecaption.js",
    "postparser_imagetitle.js",
    "postparser_columnstyle.js",
    "postparser_svgfilter.js",
    "postparser_linerestore.js",
)

_COMMENT_LINE_RE = re.compile(r"^\s*//")
_COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_comments(code: str) -> str:
    """Remove whole-line // comments and /* */ blocks from assembled JS.

    Only safe for the fragment set assembled here: those files contain no
    string or regex literal starting a line with // or containing /* (the
    lone http:// URL sits mid-line). tests/test_inkstone_emit.py guards this
    by asserting the emitted file contains no comment markers.
    """
    code = _COMMENT_BLOCK_RE.sub("", code)
    return "\n".join(line for line in code.splitlines() if not _COMMENT_LINE_RE.match(line))


def _load_pre_blocks(mappers: str) -> list[str]:
    blocks = []
    for name in PRE_FRAGMENTS:
        block = load_template("parser", name)
        if name == "preparser_titleprefix.js":
            # The mapper list is injected build-time into the fragment.
            block = block.replace("@MAPPER_PLACEHOLDER@", ", ".join(parse_mappers(mappers)))
        blocks.append(block)
    return blocks


def _load_post_blocks(enable_table_caption: bool) -> list[str]:
    blocks = []
    for name in POST_FRAGMENTS:
        if name == "postparser_tablecaption.js" and not enable_table_caption:
            continue
        block = load_template("parser", name)
        if name == "postparser_linerestore.js":
            # Inkstone's renderer emits data-line (not crossnote's
            # data-source-line) on top-level tokens; remap the restore pass.
            block = block.replace("data-source-line", "data-line")
        blocks.append(block)
    return blocks


def build_inkstone_bridge(mappers: str, enable_table_caption: bool = True) -> str:
    """Assemble the ESM bridge module (mdcss-bridge.js) content."""
    pre_body = "\n".join(block.strip("\n") for block in _load_pre_blocks(mappers))
    post_body = "\n".join(block.strip("\n") for block in _load_post_blocks(enable_table_caption))
    bridge = f"""export function mdcssPre(source) {{
let markdown = source;
let __mdcssHasIndent;
let mappers;
{pre_body}
return markdown;
}}

export function mdcssPost(html) {{
{post_body}
return html;
}}
"""
    bridge = _strip_comments(bridge)
    try:
        import jsbeautifier  # pyright: ignore[reportMissingImports]
    except ImportError:
        jsbeautifier = None
    if jsbeautifier:
        bridge = jsbeautifier.beautify(bridge, {"indent_size": 2})  # pyright: ignore[reportArgumentType]
    return bridge if bridge.endswith("\n") else bridge + "\n"


def write_inkstone_output(inkstone_repo: Path, mappers: str, enable_table_caption: bool = True) -> None:
    """Write mdcss-bridge.js and mdcss.css into an Inkstone repository tree."""
    client_dir = inkstone_repo / "src" / "client"
    bridge_path = client_dir / "lib" / "markdown" / "mdcss-bridge.js"
    css_path = client_dir / "styles" / "mdcss.css"
    bridge_path.parent.mkdir(parents=True, exist_ok=True)
    css_path.parent.mkdir(parents=True, exist_ok=True)
    bridge_path.write_text(build_inkstone_bridge(mappers, enable_table_caption), encoding="utf-8")
    css_path.write_text(load_template("inkstone", "mdcss.css"), encoding="utf-8")
    print(f"Generated mdcss-bridge.js written to: {bridge_path}")
    print(f"Generated mdcss.css written to: {css_path}")
