"""Regenerate the SVG references from the current render.

Run through `pixi run -e visual visual-bless [case ...]`, then review the
written SVG files before committing them: they become the regression baseline.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from tests_visual.harness.raster import pdf_pages_as_svg
from tests_visual.harness.render import CASES_DIR, TESTS_VISUAL, render_pdf

OUT_DIR = TESTS_VISUAL / "out"


def case_dirs(selection: list[str]) -> list[Path]:
    cases = sorted(path for path in CASES_DIR.iterdir() if (path / "input.md").is_file())
    if not selection:
        return cases
    known = {path.name: path for path in cases}
    missing = [name for name in selection if name not in known]
    if missing:
        raise SystemExit(f"Unknown cases: {', '.join(missing)}")
    return [known[name] for name in selection]


def bless(case_dir: Path) -> int:
    out_dir = OUT_DIR / case_dir.name
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    pdf = render_pdf(case_dir, out_dir)
    pages = pdf_pages_as_svg(pdf, out_dir)
    for stale in case_dir.glob("expected.*.svg"):
        stale.unlink()
    for index, page in enumerate(pages, start=1):
        (case_dir / f"expected.{index}.svg").write_text(
            page.read_text(encoding="utf-8"), encoding="utf-8"
        )
    print(f"{case_dir.name}: wrote {len(pages)} SVG page(s)")
    return len(pages)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", nargs="*", help="case directory names (default: all)")
    args = parser.parse_args(argv)
    total = 0
    for case_dir in case_dirs(args.cases):
        total += bless(case_dir)
    print(f"Blessed {total} page(s). Review the SVGs before committing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
