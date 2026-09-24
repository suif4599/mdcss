"""Emission of the Inkstone bridge artifacts.

Inkstone (a markdown-it based browser notebook) embeds the mdcss syntax
extensions through generated files committed into its repository:

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
  Image effects (i/m) are gated on the dark theme (:root[data-theme='dark'])
  instead of MPE's @media print reset: they follow the active browser theme.
  Fonts, print styles, and theme colors are intentionally not bridged.

- mdcss-runtime.js (+ mdcss-runtime.d.ts) — the Inkstone counterpart of the
  head.html docheader scripts: a self-booting script (initial scan plus
  MutationObserver) that Inkstone loads once via a side-effect import, so
  it covers every render surface without pipeline wiring. It carries the
  I/M canvas processor: the effect classes the bridge leaves as inert
  markers are picked up on the live DOM (after sanitization, trusted code
  only — user notes still cannot inject scripts). The emission replaces
  THEME_GATED with true, so the I/M effects follow the theme like i/m:
  applied only under :root[data-theme='dark'], with the original image
  restored on light; processed URLs are LRU-cached because the Inkstone
  preview re-creates every <img> on each debounced re-render.
"""

import re
from pathlib import Path

from src.builder import inject_image_effects_defaults, parse_mappers
from src.filters import DEFAULT_INVERT_BOUNDS, DEFAULT_MATTE_BOUNDS
from src.template import load_template

# Pre-pass fragments in execution order. Fence extraction must come before the
# line-rewriting passes and its restore must come last (same contract as the
# MPE assembly in builder.build_parser_blocks). The MPE-only fragments
# (preparser_pdf, postparser_uri_decode, postparser_columnsync) are not part
# of the bridge: the pdf import depends on crossnote's pdf2svg, uri_decode
# fixes a crossnote-only double encoding bug, and columnsync targets
# crossnote's scroll-sync internals.
PRE_FRAGMENTS = (
    "preparser_lineshift.js",
    "preparser_indent.js",
    "preparser_fence_extract.js",
    "preparser_tablecell.js",
    "preparser_zebra.js",
    "preparser_titleprefix.js",
    "preparser_column.js",
    "preparser_fence_restore.js",
)

# Post-pass fragments in execution order: image/table/tablecaption/imagetitle
# mirror the MPE order; columnstyle rebuilds the styles DOMPurify stripped;
# linerestore maps data-line values back to original editor lines (renamed
# from crossnote's data-source-line attribute). The I/M image effects are
# runtime-canvas only, so their classes pass through as inert markers here;
# mdcss-runtime.js picks them up on the live DOM after rendering.
POST_FRAGMENTS = (
    "postparser_image.js",
    "postparser_table.js",
    "postparser_zebra.js",
    "postparser_tablecaption.js",
    "postparser_imagetitle.js",
    "postparser_columnstyle.js",
    "postparser_linerestore.js",
)

# Runtime fragments assembled into mdcss-runtime.js: the Inkstone counterpart
# of the head.html docheader scripts. image_effects.js carries the I/M canvas
# processor; further docheader scripts can be bridged by extending this list.
RUNTIME_FRAGMENTS = ("image_effects.js",)

_COMMENT_LINE_RE = re.compile(r"^\s*//")
_COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_line_comment(line: str) -> str:
    """Strip a trailing // comment, skipping string literals.

    Walks the line tracking single/double quotes (with backslash escapes);
    the first // outside a literal cuts the line. Safe for the fragment set
    assembled here: no string contains //, no regex literal contains // or a
    quote (the lone http:// URL sits inside a string and is left alone).
    """
    quote = None
    index = 0
    while index < len(line):
        char = line[index]
        if quote is not None:
            if char == "\\":
                index += 1
            elif char == quote:
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif char == "/" and line[index + 1 : index + 2] == "/":
            return line[:index].rstrip()
        index += 1
    return line


def _strip_comments(code: str) -> str:
    """Remove // comments (whole-line and trailing) and /* */ blocks from
    assembled JS.

    Only safe for the fragment set assembled here: those files contain no
    regex literal with // or a quote, and no string containing /* (the lone
    http:// URL sits mid-line inside a string). tests/test_inkstone_emit.py
    guards this by asserting the emitted files contain no comment markers.
    """
    code = _COMMENT_BLOCK_RE.sub("", code)
    kept: list[str] = []
    for line in code.splitlines():
        if _COMMENT_LINE_RE.match(line):
            continue
        stripped = _strip_line_comment(line)
        if not stripped and line.strip():
            continue
        kept.append(stripped)
    return "\n".join(kept)


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


def build_inkstone_runtime(
    invert_bounds: tuple[int, int] = DEFAULT_INVERT_BOUNDS,
    matte_bounds: tuple[int, int] = DEFAULT_MATTE_BOUNDS,
) -> str:
    """Assemble the self-booting runtime script (mdcss-runtime.js) content."""
    blocks = []
    for name in RUNTIME_FRAGMENTS:
        block = load_template("docheader", name)
        if name == "image_effects.js":
            block = inject_image_effects_defaults(
                block, invert_bounds, matte_bounds, theme_gated=True
            )
        blocks.append(block)
    runtime = _strip_comments("\n".join(block.strip("\n") for block in blocks))
    try:
        import jsbeautifier  # pyright: ignore[reportMissingImports]
    except ImportError:
        jsbeautifier = None
    if jsbeautifier:
        runtime = jsbeautifier.beautify(runtime, {"indent_size": 2})  # pyright: ignore[reportArgumentType]
    return runtime if runtime.endswith("\n") else runtime + "\n"


def write_inkstone_output(
    inkstone_repo: Path,
    mappers: str,
    enable_table_caption: bool = True,
    invert_bounds: tuple[int, int] = DEFAULT_INVERT_BOUNDS,
    matte_bounds: tuple[int, int] = DEFAULT_MATTE_BOUNDS,
) -> None:
    """Write mdcss-bridge.js, mdcss.css and the runtime artifacts into an Inkstone repository tree."""
    client_dir = inkstone_repo / "src" / "client"
    bridge_path = client_dir / "lib" / "markdown" / "mdcss-bridge.js"
    runtime_path = client_dir / "lib" / "markdown" / "mdcss-runtime.js"
    runtime_dts_path = client_dir / "lib" / "markdown" / "mdcss-runtime.d.ts"
    css_path = client_dir / "styles" / "mdcss.css"
    bridge_path.parent.mkdir(parents=True, exist_ok=True)
    css_path.parent.mkdir(parents=True, exist_ok=True)
    bridge_path.write_text(build_inkstone_bridge(mappers, enable_table_caption), encoding="utf-8")
    runtime_path.write_text(build_inkstone_runtime(invert_bounds, matte_bounds), encoding="utf-8")
    runtime_dts_path.write_text("export {};\n", encoding="utf-8")
    css_path.write_text(load_template("inkstone", "mdcss.css"), encoding="utf-8")
    print(f"Generated mdcss-bridge.js written to: {bridge_path}")
    print(f"Generated mdcss-runtime.js written to: {runtime_path}")
    print(f"Generated mdcss-runtime.d.ts written to: {runtime_dts_path}")
    print(f"Generated mdcss.css written to: {css_path}")
