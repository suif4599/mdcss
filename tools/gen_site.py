"""Generates the GitHub Pages site into site/ from docs/DEMO.md.

The whole demo document goes through the real pipeline (pre fragments ->
markdown-it -> post fragments, assembled by src.builder.build_parser_blocks)
and is split at <h2> boundaries into pages. The site ships the actual preview
rules (scoped under .markdown-preview, exactly like the generated
style.less) and the canvas runtime as real assets, so even the I/M effects
run live; images are copied into site/assets so relative paths and the
canvas stay same-origin. site/ is a pure build artifact — gitignored,
rebuilt by the Pages workflow on push; edit docs/DEMO.md, never the site.

Regenerate locally with: pixi run site   (then open site/index.html)
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.builder import (  # noqa: E402
    _TABLE_LAYOUT_BLOCK,
    build_parser_blocks,
    inject_image_effects_defaults,
)
from src.filters import DEFAULT_INVERT_BOUNDS, DEFAULT_MATTE_BOUNDS  # noqa: E402
from src.template import TEMPLATE_DIR, load_template, strip_test_hooks  # noqa: E402

RENDERER = ROOT / "tools" / "site_render.mjs"
NODE = shutil.which("node")
REPO = "https://github.com/suif4599/mdcss"

SECTION_SLUGS = {
    "1. 图片": "images",
    "2. 表格": "tables",
    "3. 多列排版": "columns",
    "4. 标题标号": "headings",
    "5. 代码行数": "code-line-numbers",
    "6. Callout（不是新加的，但很有用）": "callouts",
    "7. 长代码排版": "long-code",
    "8. 段落缩进": "paragraph-indent",
    "9. PDF 导入居中": "pdf-import",
}

PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@ · MdCSS</title>
<link rel="stylesheet" href="chrome.css">
<link rel="stylesheet" href="mdcss.css">
</head>
<body>
<nav class="toc">
<div class="brand"><a href="index.html">MdCSS</a></div>
@@NAV@@
<div class="sep"></div>
<a href="@@REPO@@">GitHub 仓库</a>
<a href="@@REPO@@#readme">README</a>
</nav>
<main>
<div class="generated-note">本站由 <a href="@@REPO@@/blob/main/docs/DEMO.md">docs/DEMO.md</a> 经完整渲染管线自动生成（含真实 CSS 与 canvas 运行时）——修改请编辑源文档，推送后由 Pages 工作流重新构建。</div>
<div class="markdown-preview">
@@BODY@@
</div>
</main>
<script src="mdcss.js"></script>
</body>
</html>
"""


def render_body(md_text: str) -> str:
    if NODE is None:
        raise RuntimeError("node not found on PATH")
    parse_blocks, html_blocks = build_parser_blocks(
        "none, chinese, number, number, latin, roman"
    )
    payload = json.dumps(
        {
            "pre": "\n".join(parse_blocks),
            "post": "\n".join(html_blocks),
            "markdown": md_text,
        }
    )
    proc = subprocess.run([NODE, RENDERER], input=payload, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"site_render failed:\n{proc.stderr}")
    return json.loads(proc.stdout)["html"]


def content_css() -> str:
    return (
        ".markdown-preview {\n"
        "  font-size: 16px !important;\n"
        + load_template("css", "style.css").strip("\n")
        + "\n"
        + _TABLE_LAYOUT_BLOCK.strip("\n")
        + "\n}\n"
    )


def runtime_js() -> str:
    block = inject_image_effects_defaults(
        load_template("docheader", "image_effects.js"),
        DEFAULT_INVERT_BOUNDS,
        DEFAULT_MATTE_BOUNDS,
    )
    return strip_test_hooks(block)


def generate(out_dir: Path | None = None) -> list[Path]:
    out_dir = out_dir or ROOT / "site"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    (out_dir / "chrome.css").write_text(
        (TEMPLATE_DIR / "site" / "chrome.css").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (out_dir / "mdcss.css").write_text(content_css(), encoding="utf-8")
    (out_dir / "mdcss.js").write_text(runtime_js(), encoding="utf-8")
    shutil.copytree(ROOT / "docs" / "assets", out_dir / "assets")

    source = (ROOT / "docs" / "DEMO.md").read_text(encoding="utf-8")
    source = re.sub(r"\*\*目录\*\*：.*?(?=\n## )", "", source, flags=re.DOTALL)

    html = render_body(source)
    parts = re.split(r"(?=<h2>)", html)
    preamble, sections = parts[0], parts[1:]

    order: list[tuple[str, str]] = []
    for sec in sections:
        title = re.match(r"<h2>(.*?)</h2>", sec).group(1)
        if title not in SECTION_SLUGS:
            raise ValueError(f"DEMO.md section {title!r} has no page slug in SECTION_SLUGS")
        order.append((title, SECTION_SLUGS[title]))

    nav = "\n".join(f'<a href="{slug}.html">{title}</a>' for title, slug in order)

    def page(title: str, body: str) -> str:
        return (
            PAGE.replace("@@TITLE@@", title)
            .replace("@@NAV@@", nav)
            .replace("@@REPO@@", REPO)
            .replace("@@BODY@@", body.strip("\n"))
        )

    (out_dir / "index.html").write_text(page("演示文档", preamble), encoding="utf-8")
    for (title, slug), body in zip(order, sections):
        (out_dir / f"{slug}.html").write_text(page(title, body), encoding="utf-8")

    files = sorted(f for f in out_dir.rglob("*") if f.is_file())
    for f in files:
        try:
            shown = f.relative_to(ROOT)
        except ValueError:
            shown = f
        print(f"wrote {shown}")
    return files


def main() -> None:
    generate()


if __name__ == "__main__":
    main()
