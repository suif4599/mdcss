"""PDF/SVG rasterization helpers.

Both the blessed reference and the current render go through the same
converter (PyMuPDF) before comparison: the PDF is converted to SVG with
path.get_svg_image(), and both SVGs are rasterized at the same zoom. Any
conversion artifact is therefore common to both sides.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pymupdf

_METADATA_RE = re.compile(r"<metadata\b.*?</metadata>", re.DOTALL)
_DATA_TEXT_RE = re.compile(r'\sdata-text="[^"]*"')
_INKSCAPE_NS = ' xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"'


def clean_svg(svg: str) -> str:
    """Drop extraction metadata that has no effect on rendering."""
    svg = _METADATA_RE.sub("", svg)
    svg = _DATA_TEXT_RE.sub("", svg)
    return svg.replace(_INKSCAPE_NS, "")


def pdf_pages_as_svg(pdf_path: Path, svg_dir: Path) -> list[Path]:
    svg_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    with pymupdf.open(str(pdf_path)) as document:
        for index, page in enumerate(document, start=1):
            path = svg_dir / f"page-{index}.svg"
            path.write_text(clean_svg(page.get_svg_image()), encoding="utf-8")
            paths.append(path)
    return paths


def rasterize_svg(svg_path: Path, dpi: int) -> np.ndarray:
    zoom = dpi / 72
    with pymupdf.open(str(svg_path)) as document:
        page = document[0]
        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(zoom, zoom),
            colorspace=pymupdf.csRGB,
            alpha=False,
        )
        samples = np.frombuffer(pixmap.samples, dtype=np.uint8)
        return samples.reshape(pixmap.height, pixmap.width, pixmap.n)[:, :, :3].copy()
