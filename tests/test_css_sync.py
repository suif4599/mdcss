"""Cross-target CSS consistency pins.

templates/css/style.css (MPE preview) and templates/inkstone/mdcss.css are
separate static files — the inkstone one is scope-prefixed (.ink-prose),
theme-gated for the preview effects, hover-aware on stripes and uses host
color tokens. These tests pin their shared core (and the builder-side
constants) so one side cannot be edited without the other failing loudly —
the same pinning pattern the I/M bounds use.
"""

import json
import re
from pathlib import Path

import pytest

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

# Rules present in both files with identical declarations (modulo the
# inkstone-only scope/theme/hover/token transformations).
SHARED_SELECTORS = [
    "img.mdcss-inv",
    "img.mdcss-mix",
    "img.mdcss-float-left",
    "img.mdcss-float-right",
    "figure.mdcss-fig-float-left",
    "figure.mdcss-fig-float-right",
    "figure.mdcss-fig-float-left > img",
    "figure.mdcss-fig-float-right > img",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "tbody tr:nth-child(2n)",
    "table.mdcss-auto tbody tr:nth-child(2n)",
    "table.mdcss-nozebra tbody tr:nth-child(2n)",
    "table.mdcss-auto tbody tr.mdcss-z",
    ".has-indent p",
    ".has-indent li > p",
]


def _strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def _rules(css_text: str) -> dict[str, dict[str, str]]:
    """selector -> {prop: value}; later rules win, like the CSS cascade."""
    rules: dict[str, dict[str, str]] = {}
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", _strip_comments(css_text)):
        decls = {}
        for part in m.group(2).split(";"):
            if ":" in part:
                prop, value = part.split(":", 1)
                decls[prop.strip()] = value.strip()
        for sel in m.group(1).split(","):
            sel = " ".join(sel.split())
            if sel:
                rules[sel] = decls
    return rules


def _unwrap_var(value: str) -> str:
    return re.sub(r"var\([^,]+,\s*(.*)\)$", r"\1", value)


def _mpe_rules() -> dict[str, dict[str, str]]:
    return _rules((TEMPLATE_DIR / "css" / "style.css").read_text(encoding="utf-8"))


def _inkstone_rules() -> dict[str, dict[str, str]]:
    """mdcss.css rules normalized to MPE selector spelling and literal values."""
    rules = _rules((TEMPLATE_DIR / "inkstone" / "mdcss.css").read_text(encoding="utf-8"))
    out: dict[str, dict[str, str]] = {}
    for sel, decls in rules.items():
        sel = sel.replace(":root[data-theme='dark'] ", "").replace(".ink-prose ", "")
        sel = sel.replace(":not(:hover)", "")
        sel = " ".join(sel.split())
        out[sel] = {p: _unwrap_var(v) for p, v in decls.items()}
    return out


class TestSharedRules:
    @pytest.mark.parametrize("sel", SHARED_SELECTORS)
    def test_declarations_in_sync(self, sel: str) -> None:
        assert _mpe_rules()[sel] == _inkstone_rules()[sel]


class TestKnownDivergences:
    """Documented one-sided rules — extend here when a divergence is intended."""

    def test_mpe_only_header_shading(self) -> None:
        assert "thead th" in _mpe_rules()
        assert "thead th" not in _inkstone_rules()  # host theme owns it

    def test_inkstone_only_matte_and_table_layout(self) -> None:
        ink = _inkstone_rules()
        assert "img.mdcss-matte" in ink  # runtime canvas effect support
        assert "table" in ink  # host-side table layout
        assert "table" not in _mpe_rules()  # MPE gets it from builder.py inline


class TestTableLayoutMirror:
    def test_builder_block_matches_inkstone_rules(self) -> None:
        from src.builder import _TABLE_LAYOUT_BLOCK

        mpe = _rules(_TABLE_LAYOUT_BLOCK)
        ink = _inkstone_rules()
        # same declaration set except the inkstone-only host-token fill
        assert set(mpe["table"]) == set(ink["table"]) - {"background-color"}
        assert mpe["table"]["display"] == ink["table"]["display"]
        assert set(mpe["th"]) == set(ink["th"])
        assert set(mpe["td"]) == set(ink["td"])


class TestBuilderConstants:
    def test_effect_props_match_css_rules(self) -> None:
        from src.builder import _FALLBACK_EFFECT_PROPS

        classes = {"i": "mdcss-inv", "m": "mdcss-mix"}
        for token, decl in _FALLBACK_EFFECT_PROPS.items():
            prop, value = decl.rstrip(";").split(": ")
            cls = classes[token]
            assert _mpe_rules()[f"img.{cls}"][prop] == value
            assert _inkstone_rules()[f"img.{cls}"][prop] == value

    def test_layout_props_json_shape(self) -> None:
        from src.builder import LAYOUT_INLINE_PROPS, layout_props_json

        assert set(LAYOUT_INLINE_PROPS) == {"", "r", "L", "R"}
        decoded = json.loads(layout_props_json())
        assert decoded == LAYOUT_INLINE_PROPS
        for props in LAYOUT_INLINE_PROPS.values():
            assert all("important" in v for v in props.values())
