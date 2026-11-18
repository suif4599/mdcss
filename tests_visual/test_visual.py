"""Pixel regression tests for the MPE/crossnote render path."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from tests_visual.harness.compare import compare_pixels
from tests_visual.harness.raster import pdf_pages_as_svg, rasterize_svg
from tests_visual.harness.render import (
    CASES_DIR,
    TESTS_VISUAL,
    load_config,
    read_case_markdown,
    render_pdf,
)

OUT_DIR = TESTS_VISUAL / "out"
CASES = sorted(path for path in CASES_DIR.iterdir() if (path / "input.md").is_file())


def expected_pages(case_dir: Path) -> list[Path]:
    return sorted(
        case_dir.glob("expected.*.svg"),
        key=lambda path: int(path.name.split(".")[1]),
    )


def _save_debug_images(
    out_dir: Path, page_index: int, actual: np.ndarray, expected: np.ndarray, mask: np.ndarray
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(actual).save(out_dir / f"actual-{page_index}.png")
    Image.fromarray(expected).save(out_dir / f"expected-{page_index}.png")
    Image.fromarray((mask.astype(np.uint8) * 255)).save(out_dir / f"diff-{page_index}.png")


@pytest.mark.parametrize("case_dir", CASES, ids=[path.name for path in CASES])
def test_case_inputs(case_dir: Path) -> None:
    read_case_markdown(case_dir)
    load_config(case_dir)
    assert expected_pages(case_dir), f"{case_dir.name}: no expected.<n>.svg reference"


@pytest.mark.parametrize("case_dir", CASES, ids=[path.name for path in CASES])
def test_case_matches_reference(case_dir: Path) -> None:
    config = load_config(case_dir)
    out_dir = OUT_DIR / case_dir.name
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    pdf = render_pdf(case_dir, out_dir)
    rendered = pdf_pages_as_svg(pdf, out_dir)
    references = expected_pages(case_dir)
    if len(rendered) != len(references):
        pytest.fail(
            f"{case_dir.name}: rendered {len(rendered)} page(s), "
            f"reference has {len(references)} (debug files in {out_dir})"
        )

    compare = config["compare"]
    for index, (rendered_svg, reference_svg) in enumerate(zip(rendered, references), start=1):
        actual = rasterize_svg(rendered_svg, compare["dpi"])
        expected = rasterize_svg(reference_svg, compare["dpi"])
        try:
            result = compare_pixels(
                actual, expected, compare["delta_color"], compare["delta_x"]
            )
        except ValueError as exc:
            pytest.fail(f"{case_dir.name}: page {index}: {exc} (debug files in {out_dir})")
        if result.ok:
            continue
        _save_debug_images(out_dir, index, actual, expected, result.mask)
        rows, cols = np.nonzero(result.mask)
        first = [f"({int(y)},{int(x)})" for y, x in zip(rows[:10], cols[:10])]
        pytest.fail(
            f"{case_dir.name}: page {index}: {result.failed} pixel(s) outside tolerance "
            f"(delta_color={compare['delta_color']}, delta_x={compare['delta_x']}); "
            f"first: {', '.join(first)} (debug files in {out_dir})"
        )
