"""The Pages site generator renders docs/SYNTAX.md through the full pipeline.

Optional integration test: needs node plus the tools/node_modules markdown-it
install (cd tools && npm install). This is the only place the whole chain —
including the real markdown-it render — runs in the test suite.
"""

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
NEEDS = pytest.mark.skipif(
    shutil.which("node") is None or not (TOOLS / "node_modules" / "markdown-it").is_dir(),
    reason="node and tools/node_modules markdown-it required",
)


@NEEDS
class TestSiteGeneration:
    def test_generates_single_syntax_page(self, tmp_path: Path) -> None:
        sys.path.insert(0, str(TOOLS))
        import gen_site

        written = gen_site.generate(out_dir=tmp_path)
        names = {f.relative_to(tmp_path).as_posix() for f in written}
        assert {
            "index.html", "tokens.css", "prose.css", "chrome.css", "site.js",
            "mdcss.css", "mdcss.js",
        } <= names
        assert not any(name.endswith(".html") and name != "index.html" for name in names)
        assert (tmp_path / "assets" / "image.jpeg").is_file()

    def test_syntax_showcase_survives_the_chain(self, tmp_path: Path) -> None:
        sys.path.insert(0, str(TOOLS))
        import gen_site

        gen_site.generate(out_dir=tmp_path)
        page = (tmp_path / "index.html").read_text(encoding="utf-8")
        body = page[page.index('<div class="ink-prose">'):]
        assert 'colspan="2"' in body  # live merge demo survived the chain
        assert "表1:\t" in body
        assert 'class="table-wrap"' in body
        assert 'class="callout callout-tip"' in body
        assert 'class="code-block-head"' in body
        assert "token keyword" in body  # build-time Prism highlighting
        assert 'src="./assets/' in body  # same-origin assets for the canvas
        assert "mdcss-bright" in body and "mdcss-inv" in body

    def test_sidebar_links_repo_and_wiki(self, tmp_path: Path) -> None:
        sys.path.insert(0, str(TOOLS))
        import gen_site

        gen_site.generate(out_dir=tmp_path)
        page = (tmp_path / "index.html").read_text(encoding="utf-8")
        nav = page[page.index('<nav class="toc">'):page.index("</nav>")]
        assert 'href="https://github.com/suif4599/mdcss"' in nav  # repo
        assert 'href="https://github.com/suif4599/mdcss/wiki"' in nav  # wiki
        assert "#readme" not in nav

    def test_toc_scrolls_in_place(self, tmp_path: Path) -> None:
        sys.path.insert(0, str(TOOLS))
        import gen_site

        gen_site.generate(out_dir=tmp_path)
        page = (tmp_path / "index.html").read_text(encoding="utf-8")
        assert 'data-target="1-图片"' in page  # anchors scroll, not page links
        assert 'class="toc-item sub"' in page
        assert "doc-link" not in page  # no multi-document nav machinery

    def test_theme_system(self, tmp_path: Path) -> None:
        sys.path.insert(0, str(TOOLS))
        import gen_site

        gen_site.generate(out_dir=tmp_path)
        index = (tmp_path / "index.html").read_text(encoding="utf-8")
        assert "prefers-color-scheme: dark" in index  # browser default, pre-paint
        assert 'class="theme-toggle"' in index

        tokens = (tmp_path / "tokens.css").read_text(encoding="utf-8")
        assert ":root[data-theme='dark']" in tokens
        assert tokens.index(":root[data-theme='dark']") > tokens.index(":root {")

        css = (tmp_path / "mdcss.css").read_text(encoding="utf-8")
        assert ":root[data-theme='dark'] .ink-prose img.mdcss-inv" in css

        js = (tmp_path / "mdcss.js").read_text(encoding="utf-8")
        assert "var THEME_GATED = true;" in js
        assert "module.exports" not in js

        site_js = (tmp_path / "site.js").read_text(encoding="utf-8")
        assert "mdcss-theme" in site_js

    def test_regeneration_wipes_stale_files(self, tmp_path: Path) -> None:
        sys.path.insert(0, str(TOOLS))
        import gen_site

        gen_site.generate(out_dir=tmp_path)
        stale = tmp_path / "removed-page.html"
        stale.write_text("old page", encoding="utf-8")
        gen_site.generate(out_dir=tmp_path)
        assert not stale.exists()
        assert (tmp_path / "index.html").is_file()
