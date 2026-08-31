import re
from pathlib import Path

from src.font import resolve_font_family, resolve_font_path
from src.print_style import generate_print_style
from src.template import load_template


def build_style_blocks(
    font_path: Path | None,
    main_css_path: Path,
    codeblock_css_path: Path,
    print_margin: str,
    font_assets_dir: Path,
    code_font_path: Path | None = None,
    enable_parser: bool = False,
    enable_table_horizontal_scroll: bool = False,
    heading_underline: str = "",
    font_size: str = "16px",
) -> list[str]:
    blocks: list[str] = []

    font_family_name = None
    content_font_faces = None
    if font_path is not None:
        resolved_font_path = resolve_font_path(font_path)
        font_family_name, content_font_faces = resolve_font_family(resolved_font_path, font_assets_dir)
        blocks.append(content_font_faces)

    code_font_family = None
    blocks.append(
        f"""
.markdown-preview.markdown-preview {{
  font-size: {font_size} !important;
"""
    )
    if code_font_path is not None:
        resolved_code_font_path = resolve_font_path(code_font_path)
        code_font_family, code_font_faces = resolve_font_family(resolved_code_font_path, font_assets_dir)
        if code_font_faces != content_font_faces:
            blocks.append(code_font_faces)
        if font_family_name:
            blocks.append(f"""
  *:not(:is(
    pre, pre *, code, code *, kbd, kbd *, samp, samp *,
    .katex, .katex *, .MathJax, .MathJax *, mjx-container, mjx-container *
  )) {{
    font-family: '{font_family_name}', 'Source Sans Pro', 'Noto Sans CJK SC', 'Noto Sans SC', sans-serif !important;
  }}
""")

    if not enable_parser:
        for i in range(1, 101):
            blocks.append(f"""
  img[alt*="{i}"] {{
    width: {i}% !important;
    height: auto;
    display: block;
    margin: 0 auto;
  }}
""")

    blocks.append(
        load_template("css", "style.css")
    )

    if heading_underline:
        levels = [f"h{l.strip()}::after" for l in heading_underline.replace("，", ",").split(",") if l.strip().isdigit()]
        if levels:
            blocks.append(
                load_template("css", "heading_underline.css",
                              heading_selectors=",\n".join(levels))
            )

    if not enable_table_horizontal_scroll:
        blocks.append("""
  table {
    display: table !important;
    width: fit-content !important;
    max-width: 100% !important;
    margin: 0 auto !important;
    table-layout: auto !important;
    overflow-x: visible !important;
    font-size: inherit !important;
  }
  th, td {
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    word-break: break-word !important;
    font-size: inherit !important;
  }
""")

    if code_font_family:
        blocks.append(f"""
  pre, pre *, code, code *, kbd, kbd *, samp, samp *, pre[class*="language-"], pre[class*="language-"] *, code[class*="language-"], code[class*="language-"] * {{
    font-family: '{code_font_family}', monospace !important;
  }}
  .line-numbers-rows, .line-numbers-rows > span:before {{
    font-family: '{code_font_family}', monospace !important;
  }}
""")

    blocks.append("\n}\n")

    blocks.append(
        generate_print_style(
            main_css_path,
            codeblock_css_path,
            print_margin=print_margin,
        )
    )

    return blocks


def build_parser_blocks(mappers: str, enable_table_caption: bool = True) -> tuple[list[str], list[str]]:
    parser_blocks: list[str] = []
    html_blocks: list[str] = []
    # Paragraph indent
    parser_blocks.append(
        load_template("parser", "preparser_indent.js")
    )
    # Invert brightness
    parser_blocks.append(
        load_template("parser", "preparser_invert_brightness.js")
    )
    # Fence extract (must run first in markdown preprocess)
    parser_blocks.append(
        load_template("parser", "preparser_fence_extract.js")
    )
    # PDF center
    parser_blocks.append(
        load_template("parser", "preparser_pdf.js")
    )
    # Image alt size
    html_blocks.append(
        load_template("parser", "postparser_image.js")
    )
    # Table
    html_blocks.append(
        load_template("parser", "postparser_table.js")
    )
    # Table caption
    if enable_table_caption:
        html_blocks.append(
            load_template("parser", "postparser_tablecaption.js")
        )
    # Image title
    html_blocks.append(
        load_template("parser", "postparser_imagetitle.js")
    )
    # title prefix
    levels: list[str] = []
    for i in re.split(r"\s*,\s*", mappers.strip()):
        if i not in {"roman", "romanUpper", "latin", "latinUpper", "chinese", "number", "none"}:
            raise ValueError(f"Unsupported mapper: {i}, only <roman|romanUpper|latin|latinUpper|chinese|number|none> are supported.")
        levels.append(i)
    while len(levels) < 6:
        levels.append("none")
    if len(levels) > 6:
        raise ValueError(f"Too many mappers: {len(levels)}, at most 6 levels are supported.")
    parser_blocks.append(
        load_template("parser", "preparser_titleprefix.js")
        .replace("@MAPPER_PLACEHOLDER@", ", ".join(levels))
    )
    # Multicolunn
    parser_blocks.append(
        load_template("parser", "preparser_column.js")
    )
    # Fence restore (must run last in markdown preprocess)
    parser_blocks.append(
        load_template("parser", "preparser_fence_restore.js")
    )
    return parser_blocks, html_blocks


def write_output(
    output_path: Path,
    blocks: list[str],
    parse_blocks: list[str] = [],
    html_blocks: list[str] = [],
    header_blocks: list[str] = [],
) -> None:
    try:
        import jsbeautifier  # pyright: ignore[reportMissingImports]
    except ImportError:
        jsbeautifier = None
    try:
        import cssbeautifier  # pyright: ignore[reportMissingImports]
    except ImportError:
        cssbeautifier = None
    output_path.mkdir(parents=True, exist_ok=True)
    style_less = output_path / "style.less"
    text = "\n".join(map(lambda x: x.strip("\n"), blocks))
    if cssbeautifier:
        text = cssbeautifier.beautify(text, {"indent_size": 2})
    style_less.write_text(text, encoding="utf-8")
    print(f"Generated style.less written to: {style_less.resolve()}")
    parser_blocks: list[str] = []
    if parse_blocks:
        parser_blocks.append(
            "  onWillParseMarkdown: async function(markdown) {"
        )
        parser_blocks.extend(parse_blocks)
        parser_blocks.append("    return markdown;")
        parser_blocks.append("  },")
    elif html_blocks:
        parser_blocks.append(
            "  onWillParseMarkdown: async function(markdown) { return markdown; },"
        )
    if html_blocks:
        parser_blocks.append(
            "  onDidParseMarkdown: async function(html) {"
        )
        parser_blocks.extend(html_blocks)
        parser_blocks.append("    return html;")
        parser_blocks.append("  },")
    elif parse_blocks:
        parser_blocks.append("  onDidParseMarkdown: async function(html) { return html; },")
    if parser_blocks:
        parser_js = output_path / "parser.js"
        output = "\n" + "\n".join(map(lambda x: x.strip("\n"), parser_blocks)) + "\n"
        output = f"({{{output}}})"
        if jsbeautifier:
            output = jsbeautifier.beautify(output, {"indent_size": 2}) # pyright: ignore[reportArgumentType]
        parser_js.write_text(output, encoding="utf-8")
        print(f"Generated parser.js written to: {parser_js.resolve()}")
    if header_blocks:
        header_js = "\n".join(map(lambda x: x.strip("\n"), header_blocks))
        if jsbeautifier:
            header_js = jsbeautifier.beautify(header_js, {"indent_size": 2}) # pyright: ignore[reportArgumentType]
        header_html = f"<script type=\"text/javascript\">\n{header_js}\n</script>"
        header_html_path = output_path / "head.html"
        header_html_path.write_text(header_html, encoding="utf-8")
        print(f"Generated head.html written to: {header_html_path.resolve()}")
