"""Generates the GitHub Pages site into site/ from the repo's documents.

docs/SYNTAX.md goes through the real pipeline (pre fragments ->
markdown-it -> post fragments, assembled by src.builder.build_parser_blocks)
and lands on a single page with a sticky multi-level TOC that scrolls in
place. Pages exists only because the syntax showcase needs rendered HTML;
the written documentation lives in the repo README (sidebar link). The look is inkstone's: the
renderer rules (callouts, code blocks, table wrappers, Prism highlighting)
and the prose/token styles are borrowed from the inkstone source, and the
mdcss rules come from the inkstone bridge CSS verbatim, dark-theme gate
included: with the theme toggle (browser preference by default) the image
effects follow the theme exactly like inkstone, restoring originals on
light. site/ is
a pure build artifact — gitignored, rebuilt by the Pages workflow on push;
edit docs/SYNTAX.md, never the site.

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

from src.builder import build_parser_blocks, inject_image_effects_defaults  # noqa: E402
from src.filters import DEFAULT_INVERT_BOUNDS, DEFAULT_MATTE_BOUNDS  # noqa: E402
from src.template import TEMPLATE_DIR, load_template, strip_test_hooks  # noqa: E402

RENDERER = ROOT / "tools" / "site_render.mjs"
NODE = shutil.which("node")
REPO = "https://github.com/suif4599/mdcss"

PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@ · MdCSS</title>
<script>
(function () {
  var stored = localStorage.getItem('mdcss-theme');
  var theme = stored || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.dataset.theme = theme;
})();
</script>
<link rel="stylesheet" href="tokens.css">
<link rel="stylesheet" href="prose.css">
<link rel="stylesheet" href="mdcss.css">
<link rel="stylesheet" href="chrome.css">
</head>
<body>
<button class="theme-toggle" type="button" aria-label="切换深浅主题"></button>
<nav class="toc">
<div class="brand"><a href="index.html">MdCSS</a></div>
@@NAV@@
<div class="sep"></div>
<a href="@@REPO@@">GitHub 仓库</a>
</nav>
<main>
<div class="ink-prose">
@@BODY@@
</div>
</main>
<script src="mdcss.js"></script>
<script src="site.js"></script>
</body>
</html>
"""


def render_document(md_text: str) -> tuple[str, list[dict]]:
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
    result = json.loads(proc.stdout)
    return result["html"], result["headings"]


def prose_css() -> str:
    css = (TEMPLATE_DIR / "site" / "prose.css").read_text(encoding="utf-8")
    return css.replace("padding-block: 0 42vh;", "padding-block: 0 96px;")


def runtime_js() -> str:
    block = inject_image_effects_defaults(
        load_template("docheader", "image_effects.js"),
        DEFAULT_INVERT_BOUNDS,
        DEFAULT_MATTE_BOUNDS,
        theme_gated=True,
    )
    return strip_test_hooks(block)


def section_nav(headings: list[dict]) -> str:
    entries = []
    for heading in headings:
        if heading["level"] not in (2, 3):
            continue
        sub = " sub" if heading["level"] == 3 else ""
        entries.append(
            f'<a href="#{heading["id"]}" data-target="{heading["id"]}" class="toc-item{sub}">{heading["text"]}</a>'
        )
    return "\n".join(entries)


def generate(out_dir: Path | None = None) -> list[Path]:
    out_dir = out_dir or ROOT / "site"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    for name in ("tokens.css", "prose.css", "chrome.css", "site.js"):
        shutil.copy(TEMPLATE_DIR / "site" / name, out_dir / name)
    (out_dir / "mdcss.css").write_text(load_template("inkstone", "mdcss.css"), encoding="utf-8")
    (out_dir / "mdcss.js").write_text(runtime_js(), encoding="utf-8")
    shutil.copytree(ROOT / "docs" / "assets", out_dir / "assets")

    source = (ROOT / "docs" / "SYNTAX.md").read_text(encoding="utf-8")
    source = re.sub(r"\*\*目录\*\*：.*?(?=\n## )", "", source, flags=re.DOTALL)
    html, headings = render_document(source)
    page = (
        PAGE.replace("@@TITLE@@", "语法预览")
        .replace("@@NAV@@", section_nav(headings))
        .replace("@@REPO@@", REPO)
                .replace("@@BODY@@", html.strip("\n"))
    )
    (out_dir / "index.html").write_text(page, encoding="utf-8")

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
