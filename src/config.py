import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

HOME = Path.home()
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_EXTENSIONS_ROOT = HOME / ".vscode" / "extensions"
DEFAULT_OUTPUT = HOME / ".local" / "state" / "crossnote"
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_FILE_NAME = "config.json"


def load_config(config_dir: Path | None = None) -> dict[str, Any]:
    """Load user configuration from config/config.json.

    Returns a dict; missing file or parse errors result in an empty dict + warning.
    """
    config_path = (config_dir or CONFIG_DIR) / CONFIG_FILE_NAME
    if not config_path.exists():
        return {}

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: failed to parse {config_path}: {exc}")
        return {}

    if not isinstance(data, dict):
        print(f"Warning: {config_path} must contain a JSON object, got {type(data).__name__}")
        return {}

    return data


def _nested_get(cfg: dict[str, Any], dotted: str, default: Any = None) -> Any:
    """Read a value from a possibly nested dict via dot-separated keys.

    Supports both flat (``"font"``) and nested (``"fonts.font"``) lookups
    so that config.json grouping can change without breaking the script.
    """
    keys = dotted.split(".")
    val: Any = cfg
    for k in keys:
        if not isinstance(val, dict):
            return default
        val = val.get(k)
        if val is None:
            return default
    return val


def _resolve_path(value: str | None) -> Path | None:
    """Convert a config string value to a Path, expanding ~ only.

    Relative paths are left relative — resolved against cwd at use-site.
    Returns None for empty or None values.
    """
    if not value:
        return None
    return Path(value).expanduser()


def _raw_path(value: str | None) -> Path | None:
    """Like _resolve_path but keeps relative paths untouched.

    Use for main_css / codeblock_css so they stay as extension-relative
    strings for resolve_crossnote_style_path() to handle later.
    Returns None for empty or None values.
    """
    if not value:
        return None
    return Path(value).expanduser()


def _serialize_path(value: Path | None) -> str | None:
    """Inverse of _resolve_path: make a Path portable for config.json.

    Priority: relative-to-cwd → ~/... → absolute.
    """
    if value is None:
        return None
    p = Path(value).expanduser().resolve()
    try:
        return str(p.relative_to(Path.cwd()))
    except ValueError:
        pass
    try:
        return str(Path("~") / p.relative_to(HOME))
    except (ValueError, OSError):
        pass
    return str(p)


def _css_fallback_features_default(cfg: dict[str, Any]) -> str:
    """Read features.css_fallback_features from config as a comma-separated string."""
    value = _nested_get(cfg, "features.css_fallback_features", "")
    if isinstance(value, list):
        return ",".join(str(v) for v in value)
    return str(value or "")


VALID_FALLBACK_LAYOUTS = ("r", "L", "R", "Lf", "Rf")
VALID_FALLBACK_EFFECTS = ("i", "m")


def parse_css_fallback_features(value: str | list[str] | None) -> list[str]:
    """Parse and validate CSS fallback feature tokens.

    Accepts a comma-separated string (CLI) or a list of strings (config.json).
    Returns deduplicated tokens preserving order. Raises ValueError for tokens
    that have no pure-CSS fallback coverage.
    """
    if value is None:
        return []
    tokens = value if isinstance(value, list) else str(value).split(",")
    result: list[str] = []
    for token in tokens:
        token = token.strip()
        if not token or token in result:
            continue
        if token not in VALID_FALLBACK_LAYOUTS and token not in VALID_FALLBACK_EFFECTS:
            raise ValueError(
                f"Unsupported css-fallback token: {token!r}. "
                f"Valid layout tokens: {', '.join(VALID_FALLBACK_LAYOUTS)}; "
                f"valid effect tokens: {', '.join(VALID_FALLBACK_EFFECTS)}. "
                "('I' requires --enable-parser.)"
            )
        result.append(token)
    return result


def confirm_rule_count(
    total: int,
    assume_yes: bool,
    threshold: int = 200,
    isatty: Callable[[], bool] | None = None,
    ask: Callable[[str], str] | None = None,
) -> bool:
    """Confirm generating `total` CSS fallback rules when above `threshold`.

    --yes (assume_yes) always passes. Non-interactive stdin without --yes
    fails loudly (SystemExit) instead of hanging unattended runs.
    """
    if total <= threshold or assume_yes:
        return True
    if isatty is None:
        isatty = sys.stdin.isatty
    if not isatty():
        print(
            f"Error: CSS fallback would generate {total} rules (> {threshold}). "
            "Re-run with --yes to confirm.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if ask is None:
        ask = input
    answer = ask(f"CSS fallback will generate {total} style rules (> {threshold}). Continue? [y/N] ")
    return answer.strip().lower() in {"y", "yes"}


def save_config(args: argparse.Namespace, config_dir: Path | None = None) -> None:
    """Write effective settings to config/config.json (nested group format)."""
    config_path = (config_dir or CONFIG_DIR) / CONFIG_FILE_NAME

    def _set(d: dict[str, Any], dotted: str, value: Any) -> None:
        *parts, last = dotted.split(".")
        for p in parts:
            d = d.setdefault(p, {})
        if value is not None:
            d[last] = value

    data: dict[str, Any] = {}

    # Path-valued keys
    for key in ["fonts.font", "fonts.code_font", "paths.extensions_root",
                 "paths.extension_dir", "paths.output"]:
        _set(data, key, _serialize_path(getattr(args, key, None)))

    # main_css / codeblock_css — keep extension-relative path as-is
    for key, dotted in [("main_css", "themes.main_css"), ("codeblock_css", "themes.codeblock_css")]:
        val: Path | None = getattr(args, key, None)
        if val is not None:
            _set(data, dotted,
                 str(val) if not val.is_absolute() else _serialize_path(val))

    # String-valued keys
    for key, dotted in [("extension_pattern", "paths.extension_pattern"),
                        ("print_margin", "print.print_margin"),
                        ("auto_count", "headings.auto_count"),
                        ("heading_underline", "headings.heading_underline"),
                        ("font_size", "fonts.font_size"),
                        ("invert_bounds", "features.invert_bounds"),
                        ("matte_bounds", "features.matte_bounds")]:
        _set(data, dotted, getattr(args, key, None))

    # Boolean flags
    for key in ["expand_detail", "enable_parser",
                "enable_header", "enable_table_horizontal_scroll",
                "enable_table_caption"]:
        val = getattr(args, key, None)
        if val:
            _set(data, f"features.{key}", True)

    # List-valued keys (always written so the key stays visible in config.json)
    _set(data, "features.css_fallback_features",
         parse_css_fallback_features(getattr(args, "css_fallback_features", None)))

    config_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Config saved to: {config_path}")


def resolve_extension_dir(
    extensions_root: Path,
    extension_pattern: str,
    explicit_extension_dir: Path | None = None,
) -> Path:
    if explicit_extension_dir is not None:
        if not explicit_extension_dir.exists():
            raise FileNotFoundError(f"Extension directory not found: {explicit_extension_dir}")
        return explicit_extension_dir

    matches = sorted(extensions_root.glob(extension_pattern))
    if not matches:
        raise FileNotFoundError(
            "No extension directory matched pattern "
            f"'{extension_pattern}' under '{extensions_root}'"
        )

    # Pick the latest-looking directory by lexical order to handle version suffixes.
    return matches[-1]


def resolve_crossnote_style_path(extension_dir: Path, css_path: Path) -> Path:
    if css_path.is_absolute():
        return css_path
    return extension_dir / "crossnote" / "styles" / css_path


def build_parser(config: dict[str, Any]) -> argparse.ArgumentParser:
    cfg: dict[str, Any] = config

    parser = argparse.ArgumentParser(
        description="Generate Crossnote style.less with more features."
    )
    parser.add_argument(
        "--extensions-root",
        type=Path,
        default=_resolve_path(_nested_get(cfg, "paths.extensions_root")) or DEFAULT_EXTENSIONS_ROOT,
        help="Base directory containing VS Code extensions.",
    )
    parser.add_argument(
        "--extension-pattern",
        type=str,
        default=_nested_get(cfg, "paths.extension_pattern", "shd101wyy.markdown-preview-enhanced-*"),
        help="Glob pattern for the markdown-preview-enhanced extension directory.",
    )
    parser.add_argument(
        "--extension-dir",
        type=Path,
        default=_resolve_path(_nested_get(cfg, "paths.extension_dir")),
        help="Explicit extension directory (overrides pattern matching).",
    )
    parser.add_argument(
        "--expand-detail",
        action="store_true",
        default=_nested_get(cfg, "features.expand_detail", False),
        help="Expand details in print mode automatically.",
    )
    parser.add_argument(
        "--font",
        type=Path,
        default=_resolve_path(_nested_get(cfg, "fonts.font")),
        help=(
            "Optional font file path or font family name for the main document font. "
            "If a path to a .ttf/.otf/.woff/.woff2/.ttc/.otc file is given, the script reads its family "
            "name from metadata and scans sibling files in the same directory for variants. "
            "Otherwise the value is treated as a font family name and resolved via fontconfig "
            "(fc-match) on Linux or the Windows font registry / font directories on Windows. "
            "If omitted, document body font-family will not be overridden."
        ),
    )
    parser.add_argument(
        "--font-size",
        type=str,
        default=_nested_get(cfg, "fonts.font_size", "16px"),
        help=(
            "Base font size for the document body (e.g., '12px', '14px', '16px'). "
            "Smaller sizes help wide tables fit without automatic shrinking. "
            "Default: 16px"
        ),
    )
    parser.add_argument(
        "--main-css",
        type=Path,
        default=_raw_path(_nested_get(cfg, "themes.main_css")),
        help=(
            "Main theme CSS path. If relative, it is resolved under "
            "<extension-dir>/crossnote/styles/."
        ),
    )
    parser.add_argument(
        "--codeblock-css",
        type=Path,
        default=_raw_path(_nested_get(cfg, "themes.codeblock_css")),
        help=(
            "Code block theme CSS path. If relative, it is resolved under "
            "<extension-dir>/crossnote/styles/."
        ),
    )
    parser.add_argument(
        "--code-font",
        type=Path,
        default=_resolve_path(_nested_get(cfg, "fonts.code_font")),
        help=(
            "Optional font file path or font family name for code blocks. "
            "Path and family-name semantics match --font (fc-match on Linux, "
            "registry/font directories on Windows)."
        ),
    )
    parser.add_argument(
        "--print-margin",
        type=str,
        default=_nested_get(cfg, "print.print_margin", "5mm"),
        help=(
            "Print content margin value used as CSS padding in @media print body. "
            "Supports CSS length units and 1-4 value syntax, e.g. '2cm', '20mm', '1in 0.8in'."
        ),
    )
    parser.add_argument(
        "--enable-parser",
        action="store_true",
        default=_nested_get(cfg, "features.enable_parser", False),
        help="Generate features that require parser.js support.",
    )
    parser.add_argument(
        "--enable-table-caption",
        action=argparse.BooleanOptionalAction,
        default=_nested_get(cfg, "features.enable_table_caption", True),
        help="Render \"Table: caption\" as a numbered figure caption below tables (--no-enable-table-caption to disable).",
    )
    parser.add_argument(
        "--enable-header",
        action="store_true",
        default=_nested_get(cfg, "features.enable_header", False),
        help="Generate features that require head.html support.",
    )
    parser.add_argument(
        "--enable-table-horizontal-scroll",
        action="store_true",
        default=_nested_get(cfg, "features.enable_table_horizontal_scroll", False),
        help=(
            "Allow horizontal scrolling for wide tables (keep current behavior). "
            "If not set, tables will avoid horizontal scroll and force content wrapping."
        ),
    )
    parser.add_argument(
        "--auto-count",
        type=str,
        default=_nested_get(cfg, "headings.auto_count", "none, chinese, number, number, latin, roman"),
        help=(
            "Comma-separated list of title auto-count formatter for heading levels 1-6. "
            "Supported formatter: roman, romanUpper, latin, latinUpper, chinese, number, none."
        )
    )
    parser.add_argument(
        "--heading-underline",
        type=str,
        default=_nested_get(cfg, "headings.heading_underline", ""),
        help=(
            "Comma-separated heading levels to show a underline below, e.g. \"1,2\" for h1 and h2. "
            "Leave empty to disable. Default: \"\" (disabled)."
        )
    )
    parser.add_argument(
        "--css-fallback-features",
        type=str,
        default=_css_fallback_features_default(cfg),
        help=(
            "Comma-separated layout/effect tokens to cover with CSS fallback rules when "
            "--enable-parser is off. Valid tokens: r, L, R, Lf, Rf, i, m. "
            "Default: empty (width-only fallback, 100 rules). Ignored with --enable-parser."
        ),
    )
    parser.add_argument(
        "--invert-bounds",
        type=str,
        default=_nested_get(cfg, "features.invert_bounds", "32,239"),
        help=(
            "Default luma thresholds \"lo,hi\" (8-bit, 0-255) for the I image effect: "
            "pixels with luma below lo or above hi are brightness-mirrored. "
            "Overridable per image with I(lo,hi). Default: 32,239."
        ),
    )
    parser.add_argument(
        "--matte-bounds",
        type=str,
        default=_nested_get(cfg, "features.matte_bounds", "64,239"),
        help=(
            "Default luma thresholds \"lo,hi\" (8-bit, 0-255) for the M image effect: "
            "pixels with luma below lo are brightened, pixels above hi become transparent. "
            "Overridable per image with M(lo,hi). Default: 64,239."
        ),
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Assume yes at confirmation prompts (for unattended nix/systemd runs).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_resolve_path(_nested_get(cfg, "paths.output")) or DEFAULT_OUTPUT,
        help="Output crossnote style directory (style.less and optionally parser.js will be written here).",
    )
    parser.add_argument(
        "--emit-inkstone",
        type=Path,
        default=_resolve_path(_nested_get(cfg, "paths.emit_inkstone")),
        help=(
            "Generate the Inkstone bridge artifacts and exit: "
            "mdcss-bridge.js into <dir>/src/client/lib/markdown/ and mdcss.css into "
            "<dir>/src/client/styles/, where <dir> is an Inkstone repository root. "
            "Reuses --auto-count and --enable-table-caption; MPE outputs are not generated."
        ),
    )
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="Save the effective settings (after CLI and config merge) to config.json and exit.",
    )
    return parser
