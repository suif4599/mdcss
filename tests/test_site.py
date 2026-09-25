"""The Pages site generator renders docs/DEMO.md through the full pipeline.

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
    def test_generates_pages_and_assets_from_demo(self, tmp_path: Path) -> None:
        sys.path.insert(0, str(TOOLS))
        import gen_site

        written = gen_site.generate(out_dir=tmp_path)
        names = {f.relative_to(tmp_path).as_posix() for f in written}
        assert {"index.html", "chrome.css", "mdcss.css", "mdcss.js", "images.html", "tables.html"} <= names
        assert (tmp_path / "assets" / "image.jpeg").is_file()

        tables = (tmp_path / "tables.html").read_text(encoding="utf-8")
        assert 'colspan="2"' in tables  # live merge demo survived the chain
        assert "表1:\t" in tables

        images = (tmp_path / "images.html").read_text(encoding="utf-8")
        assert 'src="./assets/' in images  # same-origin assets for the canvas
        assert "mdcss-bright" in images and "mdcss-inv" in images

        columns = (tmp_path / "columns.html").read_text(encoding="utf-8")
        assert "grid-template-columns" in columns

        css = (tmp_path / "mdcss.css").read_text(encoding="utf-8")
        assert css.startswith(".markdown-preview {")  # scoped like style.less
        assert "img.mdcss-inv" in css

        js = (tmp_path / "mdcss.js").read_text(encoding="utf-8")
        assert "MutationObserver" in js
        assert "module.exports" not in js  # test hook stripped from emission

        index = (tmp_path / "index.html").read_text(encoding="utf-8")
        assert "docs/DEMO.md" in index  # generated-note points at the source
        assert '<div class="markdown-preview">' in index

    def test_regeneration_wipes_stale_files(self, tmp_path: Path) -> None:
        sys.path.insert(0, str(TOOLS))
        import gen_site

        gen_site.generate(out_dir=tmp_path)
        stale = tmp_path / "removed-section.html"
        stale.write_text("old page", encoding="utf-8")
        gen_site.generate(out_dir=tmp_path)
        assert not stale.exists()
        assert (tmp_path / "index.html").is_file()
