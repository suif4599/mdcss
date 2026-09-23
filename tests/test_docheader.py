"""Tests for templates/docheader/image_effects.js (runtime canvas processor).

The pure functions (tables, LUT, background filters, pixel transform) are
exercised under node via the module.exports hook in the template; these
tests skip when no node binary is available. The DOM wiring (canvas,
MutationObserver) is covered by the smoke tests below.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "docheader" / "image_effects.js"
NODE = shutil.which("node")

needs_node = pytest.mark.skipif(NODE is None, reason="node not available")


def run_node(script: str) -> dict:
    proc = subprocess.run([NODE, "--input-type=module", "-e", script],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def node_prelude() -> str:
    return f"import m from {str(TEMPLATE)!r};\n"


class TestSmoke:
    """Template content markers (no node needed)."""

    def test_template_exists_and_targets_effect_classes(self) -> None:
        js = TEMPLATE.read_text(encoding="utf-8")
        assert "mdcss-bright" in js and "mdcss-matte" in js
        assert "mdcss-bright-10-250" not in js  # class suffixes are dynamic
        assert "module.exports" in js  # test hook
        assert "toDataURL" in js and "crossOrigin" in js

    def test_defaults_match_filters_module(self) -> None:
        from src.filters import DEFAULT_INVERT_BOUNDS, DEFAULT_MATTE_BOUNDS

        js = TEMPLATE.read_text(encoding="utf-8")
        assert f"var INVERT_BOUNDS = [{DEFAULT_INVERT_BOUNDS[0]}, {DEFAULT_INVERT_BOUNDS[1]}];" in js
        assert f"var MATTE_BOUNDS = [{DEFAULT_MATTE_BOUNDS[0]}, {DEFAULT_MATTE_BOUNDS[1]}];" in js

    def test_theme_gate_literal_defaults_off(self) -> None:
        # MPE consumes the template as-is; the Inkstone emission flips this
        # literal at build time
        js = TEMPLATE.read_text(encoding="utf-8")
        assert "var THEME_GATED = false;" in js


@needs_node
class TestTables:
    def test_band_tables(self) -> None:
        out = run_node(node_prelude() + """
        const d = m.darkTable(10), b = m.brightTable(250);
        const r = { darkLen: d.length, brightLen: b.length,
                    d10: d[10], d14: d[14], d11: d[11], d15: d[15],
                    b250: b[250], b246: b[246], b249: b[249], b245: b[245] };
        console.log(JSON.stringify(r));
        """)
        assert out["darkLen"] == out["brightLen"] == 256
        assert out["d10"] == 1 and out["d14"] == 0          # full band at lo, none past knee
        assert abs(out["d11"] - 0.75) < 1e-6                # linear quarter steps outward
        assert out["b250"] == 1 and out["b246"] == 0
        assert abs(out["b249"] - 0.75) < 1e-6

    def test_lut_interpolates(self) -> None:
        out = run_node(node_prelude() + """
        const t = m.darkTable(10);
        console.log(JSON.stringify({ lo: m.lut(t, 0), mid: m.lut(t, 12.5),
                                     hi: m.lut(t, 300), neg: m.lut(t, -5) }));
        """)
        assert out["lo"] == 1 and out["hi"] == 0 and out["neg"] == 1
        assert abs(out["mid"] - 0.375) < 1e-6


@needs_node
class TestLocalBackground:
    def test_min_and_max_filters(self) -> None:
        # 5x5 luma: a dark spot in the middle, bright corner, flat elsewhere
        out = run_node(node_prelude() + """
        const w = 5, h = 5;
        const luma = new Float32Array(w * h).fill(128);
        luma[2 * w + 2] = 0;        // center dark
        luma[0] = 255;              // corner bright
        const d = m.localBackground(luma, w, h, true);
        const b = m.localBackground(luma, w, h, false);
        const r = { center: d[12], ring: d[11], far: d[2],
                    bcenter: b[12], bring: b[11], bcorner: b[0],
                    badj: b[1], bfar: b[2] };
        console.log(JSON.stringify(r));
        """)
        assert out["center"] == 0                 # dark spot is its own background
        assert out["ring"] == 0                   # one pixel away still sees it (FRINGE=1)
        assert out["far"] == 128                  # two pixels away does not
        assert out["bcenter"] == 128              # bright side is symmetric
        assert out["bring"] == 128                # two away from the bright corner
        assert out["bcorner"] == 255 and out["badj"] == 255
        assert out["bfar"] == 128


@needs_node
class TestTransformPixels:
    def _run(self, kind: str, lo: int, hi: int, pixels: list[tuple], w: int, h: int) -> list:
        flat = [v for px in pixels for v in px]
        script = node_prelude() + f"""
        const w = {w}, h = {h};
        const px = new Uint8ClampedArray({json.dumps(flat)});
        const n = w * h;
        const luma = new Float32Array(n);
        for (let i = 0; i < n; i++) luma[i] = 0.299 * px[i*4] + 0.587 * px[i*4+1] + 0.114 * px[i*4+2];
        const bgd = m.localBackground(luma, w, h, true);
        const bgb = m.localBackground(luma, w, h, false);
        m.transformPixels(px, luma, bgd, bgb, {kind!r}, m.darkTable({lo}), m.brightTable({hi}));
        console.log(JSON.stringify(Array.from(px)));
        """
        return run_node(script)

    def test_matte_semantics(self) -> None:
        # 5x5: mid-gray field, black text core at center, white border ring
        gray, black, white = (128, 128, 128), (0, 0, 0), (255, 255, 255)
        px = [[*gray, 255]] * 25
        px[12] = [*black, 255]
        for i in (6, 8, 16, 18):
            px[i] = [*white, 255]
        out = self._run("matte", 10, 250, px, 5, 5)
        get = lambda i: (out[i*4:i*4+3], out[i*4+3])  # noqa: E731
        # dark core: mirrored to white, opaque
        rgb, a = get(12)
        assert rgb == [255, 255, 255] and a == 255
        # mid-gray far from any dark/bright content: untouched
        rgb, a = get(2)
        assert rgb == [128, 128, 128] and a == 255
        # white pixels: matted out regardless of neighbors
        for i in (6, 18):
            assert get(i)[1] == 0
        # gray next to the black core follows the dark background (FRINGE=1)
        rgb, a = get(7)
        assert a == 255

    def test_bright_semantics(self) -> None:
        # 5x5 flat mid-gray: nothing in either band, bit-exact identity
        px = [[96, 96, 96, 255]] * 25
        out = self._run("bright", 32, 239, px, 5, 5)
        assert out == [v for _ in range(25) for v in (96, 96, 96, 255)]
