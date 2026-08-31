import platform
import shutil
import subprocess
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont  # pyright: ignore[reportMissingImports]

FONT_FORMATS = {
    ".ttf": "truetype",
    ".otf": "opentype",
    ".woff": "woff",
    ".woff2": "woff2",
}


def _get_name_record(font: TTFont, name_ids: tuple[int, ...]) -> str | None:
    name_table = font.get("name")
    if name_table is None or not hasattr(name_table, "names"):
        return None
    for name_id in name_ids:
        for record in name_table.names:  # type: ignore[attr-defined]
            if record.nameID != name_id:
                continue
            try:
                value = record.toUnicode().strip()
            except Exception:
                continue
            if value:
                return value
    return None


def _normalize_font_family_name(name: str) -> str:
    return " ".join(name.split()).casefold()


def _safe_asset_stem(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    filtered = "".join(ch if ch.isalnum() else "-" for ch in ascii_text)
    cleaned = "-".join(part for part in filtered.split("-") if part)
    return cleaned.lower() or "font"


def _unique_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in values:
        key = item.strip()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return ordered


def _name_aliases(font: TTFont) -> list[str]:
    aliases: list[str] = []
    name_table = font.get("name")
    if name_table is None or not hasattr(name_table, "names"):
        return aliases
    for record in name_table.names:  # type: ignore[attr-defined]
        if record.nameID not in {1, 4, 6, 16, 17}:
            continue
        try:
            value = record.toUnicode().strip()
        except Exception:
            continue
        if value:
            aliases.append(value)
    return _unique_keep_order(aliases)


def _copy_font_to_assets(
    source_path: Path,
    assets_dir: Path,
    family_name: str,
    weight: int,
    style: str,
) -> str:
    assets_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_asset_stem(family_name)
    suffix = source_path.suffix.lower()
    dest_name = f"{stem}-{weight}-{style}{suffix}"
    dest_path = assets_dir / dest_name

    if not dest_path.exists() or source_path.stat().st_mtime > dest_path.stat().st_mtime:
        shutil.copy2(source_path, dest_path)

    return f"fonts/{dest_name}"


def resolve_font_path(font_input: str | Path) -> Path:
    candidate = Path(font_input).expanduser()
    if candidate.is_file():
        if candidate.suffix.lower() not in FONT_FORMATS:
            raise ValueError(
                f"Unsupported font file: {candidate} (.ttf/.otf/.woff/.woff2 only)"
            )
        return candidate.resolve()

    system = platform.system()
    if system == "Linux":
        return _resolve_via_fontconfig(str(font_input))
    if system == "Windows":
        return _resolve_via_windows(str(font_input))
    raise NotImplementedError(
        f"Font family resolution by name is not supported on {system}. "
        "Please provide a font file path directly."
    )


def _resolve_via_fontconfig(family: str) -> Path:
    system = platform.system()
    if system != "Linux":
        raise NotImplementedError(
            f"Font family resolution by name is only supported on Linux "
            f"(current system: {system}). Windows font family resolution is "
            "not yet implemented — please provide a font file path directly."
        )

    fc_match = shutil.which("fc-match")
    if fc_match is None:
        raise FileNotFoundError(
            "fc-match tool not found — install fontconfig (e.g. "
            "'apt install fontconfig' on Debian/Ubuntu, 'dnf install fontconfig' "
            "on Fedora) to resolve font families by name."
        )

    result = subprocess.run(
        [fc_match, r"--format=%{file}\n", family],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"fc-match returned no file path for font family: {family!r}")

    resolved = Path(lines[0])
    if not resolved.is_file():
        raise FileNotFoundError(
            f"fc-match returned a non-existent path for font family {family!r}: {resolved}"
        )

    return resolved


def _resolve_via_windows(family: str) -> Path:
    """Resolve a font family name to a font file on Windows.

    Candidates are gathered from:
      1. The system/user font registry keys (HKLM / HKCU).
      2. A directory scan of ``C:\\Windows\\Fonts`` and the per-user
         ``%LOCALAPPDATA%\\Microsoft\\Windows\\Fonts`` folder.

    Each candidate is matched against ``family`` using its real metadata
    family name (via :func:`read_font_metadata`), so matches are robust to
    registry key-name formatting and localized names.
    """
    import os
    import winreg

    windows_dir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    user_fonts_dir = (
        Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        / "Microsoft"
        / "Windows"
        / "Fonts"
    )

    candidates: list[Path] = []
    fonts_key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(hive, fonts_key) as key:
                for i in range(winreg.QueryInfoKey(key)[1]):
                    _, value, _ = winreg.EnumValue(key, i)
                    if not isinstance(value, str) or not value.strip():
                        continue
                    p = Path(value).expanduser()
                    if not p.is_absolute():
                        p = windows_dir / "Fonts" / p
                    candidates.append(p)
        except OSError:
            continue

    for d in (windows_dir / "Fonts", user_fonts_dir):
        if d.is_dir():
            candidates.extend(
                p for p in d.iterdir() if p.suffix.lower() in FONT_FORMATS
            )

    target = _normalize_font_family_name(family)
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).casefold()
        if key in seen:
            continue
        seen.add(key)
        if not candidate.is_file():
            continue
        try:
            family_name, *_ = read_font_metadata(candidate)
        except Exception:
            continue
        if _normalize_font_family_name(family_name) == target:
            return candidate.resolve()

    raise ValueError(
        f"Font family not found on Windows: {family!r}. "
        "Searched the font registry and C:\\Windows\\Fonts / per-user Fonts. "
        "Note: TrueType Collection (.ttc) files are not supported."
    )


def read_font_metadata(font_path: Path) -> tuple[str, int, str, str, list[str]]:
    if not font_path.exists():
        raise FileNotFoundError(f"Font file not found: {font_path}")
    if not font_path.is_file():
        raise ValueError(f"Font path is not a file: {font_path}")

    font_format = FONT_FORMATS.get(font_path.suffix.lower())
    if font_format is None:
        raise ValueError(
            f"Unsupported font file: {font_path} (.ttf/.otf/.woff/.woff2 only)"
        )

    with TTFont(font_path) as font:
        family_name = _get_name_record(font, (16, 1))
        if family_name is None:
            raise ValueError(f"Unable to determine font family name: {font_path}")
        aliases = _name_aliases(font)
        if family_name not in aliases:
            aliases.insert(0, family_name)

        weight = 400
        if "OS/2" in font:
            weight = int(getattr(font["OS/2"], "usWeightClass", 400) or 400)

        style = "normal"
        if "post" in font and float(getattr(font["post"], "italicAngle", 0) or 0) != 0:
            style = "italic"
        elif "head" in font and getattr(font["head"], "macStyle", 0) & 0b10:
            style = "italic"
        else:
            subfamily_name = _get_name_record(font, (17, 2)) or ""
            if "italic" in subfamily_name.casefold() or "oblique" in subfamily_name.casefold():
                style = "italic"

    return family_name, weight, style, font_format, aliases


def resolve_font_family(font_path: Path, font_assets_dir: Path) -> tuple[str, str]:
    font_path = font_path.expanduser().resolve()
    base_family_name, _, _, _, _ = read_font_metadata(font_path)
    base_family_key = _normalize_font_family_name(base_family_name)

    variant_files: list[tuple[Path, int, str, str, list[str]]] = []
    for candidate in sorted(font_path.parent.iterdir()):
        if candidate.suffix.lower() not in FONT_FORMATS or not candidate.is_file():
            continue

        try:
            family_name, weight, style, font_format, aliases = read_font_metadata(candidate)
        except Exception:
            continue

        if _normalize_font_family_name(family_name) != base_family_key:
            continue

        variant_files.append((candidate, weight, style, font_format, aliases))

    if not variant_files:
        raise ValueError(f"No usable font variants found for: {font_path}")

    variant_files.sort(key=lambda item: (item[1], item[2] == "italic", item[0].name.casefold()))

    css_lines = ["/* Auto-generated @font-face rules */"]
    for variant_path, weight, style, font_format, aliases in variant_files:
        asset_rel_path = _copy_font_to_assets(
            source_path=variant_path,
            assets_dir=font_assets_dir,
            family_name=base_family_name,
            weight=weight,
            style=style,
        )
        local_sources = ", ".join(f"local('{name}')" for name in _unique_keep_order(aliases))
        if local_sources:
            src_value = f"{local_sources}, url('{asset_rel_path}') format('{font_format}')"
        else:
            src_value = f"url('{asset_rel_path}') format('{font_format}')"
        css_lines.append("@font-face {")
        css_lines.append(f"  font-family: '{base_family_name}';")
        css_lines.append(f"  src: {src_value};")
        css_lines.append(f"  font-weight: {weight};")
        css_lines.append(f"  font-style: {style};")
        css_lines.append("  font-display: swap;")
        css_lines.append("}")
        css_lines.append("")

    return base_family_name, "\n".join(css_lines).strip()
