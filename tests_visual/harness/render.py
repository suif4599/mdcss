"""Render a case markdown to PDF through the MPE/crossnote pipeline.

MPE renders markdown with crossnote and exports PDF by feeding crossnote's
print template to Chrome. This module reproduces that path: crossnote builds
the HTML from the note plus the generated .crossnote artifacts (style.less,
parser.js, head.html, fonts), and the pinned Playwright Chromium prints it
with the same PDF options crossnote's chromeExport uses.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

TESTS_VISUAL = Path(__file__).resolve().parents[1]
PROJECT_ROOT = TESTS_VISUAL.parent
CASES_DIR = TESTS_VISUAL / "cases"
CROSSNOTE_STYLES = TESTS_VISUAL / "node_modules" / "crossnote" / "out" / "styles"
BASE_CONFIG = TESTS_VISUAL / "config" / "base.json"
BROWSER_PIN = TESTS_VISUAL / "config" / "browser.json"
HARNESS = Path(__file__).resolve().parent
IMAGE_EFFECTS_SCRIPT_NAME = "mdcss_image_effects.js"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.builder import (  # noqa: E402
    build_parser_blocks,
    build_style_blocks,
    inject_image_effects_defaults,
    write_output,
)
from src.filters import parse_bounds  # noqa: E402
from src.template import load_template  # noqa: E402


def _flatten(value: Any, prefix: tuple[str, ...] = ()) -> dict[tuple[str, ...], Any]:
    if isinstance(value, dict):
        items: dict[tuple[str, ...], Any] = {}
        for key, child in value.items():
            items.update(_flatten(child, prefix + (str(key),)))
        return items
    return {prefix: value}


def _merge(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            merged[key] = _merge(base.get(key), value)
        return merged
    return override


def check_single_override(base: dict, override: dict, case_name: str) -> None:
    flat_base = _flatten(base)
    flat_override = _flatten(override)
    differing = [
        ".".join(key)
        for key, value in flat_override.items()
        if key not in flat_base or flat_base[key] != value
    ]
    if len(differing) > 1:
        raise ValueError(
            f"{case_name}: options.json may differ from config/base.json in at most "
            f"one parameter, got {len(differing)}: {differing}"
        )


def load_config(case_dir: Path | None = None) -> dict:
    base = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    if case_dir is None:
        return base
    options_path = case_dir / "options.json"
    if not options_path.exists():
        return base
    override = json.loads(options_path.read_text(encoding="utf-8"))
    check_single_override(base, override, case_dir.name)
    return _merge(base, override)


def read_case_markdown(case_dir: Path) -> str:
    data = (case_dir / "input.md").read_bytes()
    try:
        return data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"{case_dir.name}: input.md must be ASCII-only (byte {exc.start} is not)"
        ) from exc


def _env_path(value: str) -> Path:
    if value.startswith("{env}/"):
        return Path(sys.prefix) / value[len("{env}/"):]
    return TESTS_VISUAL / value


def chromium_pin() -> dict:
    try:
        import playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is missing; run the visual tests with "
            "`pixi run -e visual ...` (see tests_visual/README.md)"
        ) from exc

    pin = json.loads(BROWSER_PIN.read_text(encoding="utf-8"))
    installed = package_version("playwright")
    browsers = json.loads(
        (Path(playwright.__file__).parent / "driver" / "package" / "browsers.json").read_text(
            encoding="utf-8"
        )
    )
    chromium = next(item for item in browsers["browsers"] if item["name"] == "chromium")
    if (
        installed != pin["playwright"]
        or chromium["revision"] != pin["chromium"]
        or chromium.get("browserVersion") != pin["chrome"]
    ):
        raise RuntimeError(
            "Chromium pin is stale: config/browser.json expects Playwright "
            f"{pin['playwright']} / Chromium {pin['chromium']} "
            f"({pin['chrome']}), the environment has Playwright {installed} / "
            f"Chromium {chromium['revision']} ({chromium.get('browserVersion')}). "
            "Update config/browser.json and re-bless the references."
        )
    return chromium


def _build_artifacts(config: dict, notebook_dir: Path) -> None:
    mdcss = config["mdcss"]
    crossnote = config["crossnote"]
    output_dir = notebook_dir / ".crossnote"
    font_path = _env_path(mdcss["font"])
    code_font_path = _env_path(mdcss["code_font"]) if mdcss.get("code_font") else None
    main_css = CROSSNOTE_STYLES / "preview_theme" / crossnote["previewTheme"]
    codeblock_css = CROSSNOTE_STYLES / "prism_theme" / crossnote["codeBlockTheme"]

    with contextlib.redirect_stdout(io.StringIO()):
        blocks = build_style_blocks(
            font_path=font_path,
            main_css_path=main_css,
            codeblock_css_path=codeblock_css,
            print_margin=mdcss["print_margin"],
            font_assets_dir=output_dir / "fonts",
            code_font_path=code_font_path,
            enable_parser=mdcss["enable_parser"],
            enable_table_horizontal_scroll=mdcss["enable_table_horizontal_scroll"],
            heading_underline=mdcss["heading_underline"],
            font_size=mdcss["font_size"],
            css_fallback_features=mdcss["css_fallback_features"],
        )
        parse_blocks: list[str] = []
        html_blocks: list[str] = []
        header_blocks: list[str] = []
        header_script_files: list[tuple[str, str]] = []
        if mdcss["enable_parser"]:
            parse_blocks, html_blocks = build_parser_blocks(
                mdcss["auto_count"], mdcss["enable_table_caption"]
            )
            effects = inject_image_effects_defaults(
                load_template("docheader", "image_effects.js"),
                parse_bounds(mdcss["invert_bounds"], "invert bounds"),
                parse_bounds(mdcss["matte_bounds"], "matte bounds"),
            )
            header_blocks.append(effects)
            header_script_files.append((IMAGE_EFFECTS_SCRIPT_NAME, effects))
        write_output(
            output_dir,
            blocks,
            parse_blocks,
            html_blocks,
            header_blocks,
            header_script_files,
        )


def _render_html(notebook_dir: Path, config: dict, html_output: Path) -> None:
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("node not found on PATH; run through `pixi run -e visual`")
    payload = json.dumps(
        {
            "notebookPath": str(notebook_dir),
            "noteFile": "note.md",
            "config": config["crossnote"],
            "htmlOutput": str(html_output),
        }
    )
    proc = subprocess.run(
        [node, str(HARNESS / "render.mjs")],
        input=payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=TESTS_VISUAL,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"crossnote render failed:\n{proc.stderr}")


def _use_env_libraries() -> None:
    if not sys.platform.startswith("linux"):
        return
    lib_dir = str(Path(sys.prefix) / "lib")
    current = [part for part in os.environ.get("LD_LIBRARY_PATH", "").split(":") if part]
    if lib_dir not in current:
        os.environ["LD_LIBRARY_PATH"] = ":".join([lib_dir, *current])


def _print_pdf(html_path: Path, pdf_path: Path, config: dict) -> None:
    from playwright.sync_api import sync_playwright

    _use_env_libraries()
    pdf = config["pdf"]
    margin = {"top": pdf["margin"], "bottom": pdf["margin"], "left": pdf["margin"], "right": pdf["margin"]}
    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            raise RuntimeError(
                f"Chromium is not installed at {executable}; run "
                "`pixi run -e visual visual-setup`"
            )
        browser = playwright.chromium.launch(
            channel=pdf["channel"], args=pdf["chromium_args"]
        )
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")
        page.evaluate(
            "Promise.all(Array.from(document.images).map((img) => img.decode().catch(() => {})))"
        )
        page.add_style_tag(
            content="*, *::before, *::after { animation: none !important; transition: none !important; }"
        )
        page.pdf(
            path=str(pdf_path),
            format=pdf["format"],
            margin=margin,
            print_background=pdf["print_background"],
            prefer_css_page_size=False,
        )
        browser.close()


def render_pdf(case_dir: Path, out_dir: Path) -> Path:
    config = load_config(case_dir)
    chromium_pin()
    notebook_dir = out_dir / "notebook"
    notebook_dir.mkdir(parents=True, exist_ok=True)
    assets = PROJECT_ROOT / "docs" / "assets"
    if assets.is_dir():
        shutil.copytree(assets, notebook_dir / "assets", dirs_exist_ok=True)
    (notebook_dir / "note.md").write_text(read_case_markdown(case_dir), encoding="ascii")
    _build_artifacts(config, notebook_dir)
    html_path = notebook_dir / "export.html"
    _render_html(notebook_dir, config, html_path)
    pdf_path = out_dir / "actual.pdf"
    _print_pdf(html_path, pdf_path, config)
    return pdf_path
