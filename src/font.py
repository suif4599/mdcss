import logging
import platform
import shutil
import subprocess
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTFont  # pyright: ignore[reportMissingImports]


def _silence_bogus_head_timestamp(record: logging.LogRecord) -> bool:
    # 某些字体（如方正舒体/方正姚体）head 表的 created 时间戳早于 1970，
    # fontTools 会打无害告警并自动补偿；按名解析扫描系统字体目录时噪音较大。
    return "timestamp seems very low" not in record.getMessage()


logging.getLogger("fontTools.ttLib.tables._h_e_a_d").addFilter(_silence_bogus_head_timestamp)

FONT_FORMATS = {
    ".ttf": "truetype",
    ".otf": "opentype",
    ".woff": "woff",
    ".woff2": "woff2",
}

# Collection 格式：一个文件里包含多个字体（TrueType Collection / OpenType Collection）。
# 浏览器 @font-face 的 format 不能直接用 "collection"，需按每个子字体内部的
# 实际格式（truetype / opentype）给出，因此这里不放进 FONT_FORMATS。
FONT_COLLECTION_EXTENSIONS = frozenset({".ttc", ".otc"})
SUPPORTED_FONT_EXTENSIONS = frozenset({*FONT_FORMATS, *FONT_COLLECTION_EXTENSIONS})


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
        if candidate.suffix.lower() not in SUPPORTED_FONT_EXTENSIONS:
            raise ValueError(
                f"Unsupported font file: {candidate} "
                "(.ttf/.otf/.woff/.woff2/.ttc/.otc only)"
            )
        return candidate.resolve()

    # A path-shaped input that does not exist must fail loudly: fc-match
    # answers any family query with some unrelated font, so a typo'd path
    # would otherwise resolve silently to the wrong font.
    looks_like_path = (
        "/" in str(candidate)
        or "\\" in str(candidate)
        or candidate.suffix.lower() in SUPPORTED_FONT_EXTENSIONS
    )
    if looks_like_path:
        raise FileNotFoundError(
            f"Font file not found: {candidate}. To resolve by family name, "
            "pass a plain name without separators or font extension."
        )

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
                p for p in d.iterdir() if p.suffix.lower() in SUPPORTED_FONT_EXTENSIONS
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
        # 先只读 name 表快速比对家族名，命中后再解码完整元数据
        if not any(
            _normalize_font_family_name(name) == target
            for name in _read_family_names(candidate)
        ):
            continue
        try:
            entries = read_font_metadata_many(candidate)
        except Exception:
            continue
        for family_name, *_ in entries:
            if _normalize_font_family_name(family_name) == target:
                return candidate.resolve()

    raise ValueError(
        f"Font family not found on Windows: {family!r}. "
        "Searched the font registry and C:\\Windows\\Fonts / per-user Fonts."
    )


def _read_font_entry(
    font: TTFont,
    font_path: Path,
    explicit_format: str | None,
) -> tuple[str, int, str, str, list[str]]:
    """从一个已打开的 TTFont 对象读取元数据。

    ``explicit_format`` 用于单字体文件（.ttf/.otf/.woff/.woff2 按后缀映射）；
    为 None 时（集合文件内子字体）按字体内部的字形表判断实际格式。
    """
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

    font_format = explicit_format or ("truetype" if "glyf" in font else "opentype")
    return family_name, weight, style, font_format, aliases


def _read_family_names(font_path: Path) -> list[str]:
    """轻量读取字体文件中各字体的家族名（只解析 name 表）。

    用于按名解析时的候选快速筛查：不触碰 head/OS/2/post 表，既避免为
    不相关字体付出完整解码的开销，也不会触发 head 表相关的 fontTools
    告警。返回与 :func:`read_font_metadata_many` 子字体一一对应的家族名
    列表；解析失败时返回空列表（与完整读取被跳过的行为一致）。
    """
    suffix = font_path.suffix.lower()
    if suffix in FONT_COLLECTION_EXTENSIONS:
        from fontTools.ttLib import TTCollection  # pyright: ignore[reportMissingImports]

        try:
            with TTCollection(font_path, lazy=True) as collection:
                return [
                    name
                    for font in collection.fonts
                    if (name := _get_name_record(font, (16, 1))) is not None
                ]
        except Exception:
            return []

    try:
        with TTFont(font_path, lazy=True) as font:
            name = _get_name_record(font, (16, 1))
            return [name] if name else []
    except Exception:
        return []


def read_font_metadata(font_path: Path) -> tuple[str, int, str, str, list[str]]:
    """读取字体文件的主字体的元数据（兼容接口）。

    对 .ttc/.otc 集合文件返回第一个子字体的元数据；需要全部子字体时请用
    :func:`read_font_metadata_many`。
    """
    return read_font_metadata_many(font_path)[0]


def read_font_metadata_many(
    font_path: Path,
) -> list[tuple[str, int, str, str, list[str]]]:
    """返回一个字体文件中所有字体的元数据。

    普通 .ttf/.otf/.woff/.woff2 文件返回 1 项；.ttc/.otc 集合文件返回其中
    每一个子字体的元数据。
    """
    if not font_path.exists():
        raise FileNotFoundError(f"Font file not found: {font_path}")
    if not font_path.is_file():
        raise ValueError(f"Font path is not a file: {font_path}")

    suffix = font_path.suffix.lower()
    if suffix not in SUPPORTED_FONT_EXTENSIONS:
        raise ValueError(
            f"Unsupported font file: {font_path} (.ttf/.otf/.woff/.woff2/.ttc/.otc only)"
        )

    if suffix in FONT_COLLECTION_EXTENSIONS:
        from fontTools.ttLib import TTCollection  # pyright: ignore[reportMissingImports]

        with TTCollection(font_path) as collection:
            return [_read_font_entry(f, font_path, None) for f in collection.fonts]

    with TTFont(font_path) as font:
        return [_read_font_entry(font, font_path, FONT_FORMATS[suffix])]


def resolve_font_family(font_path: Path, font_assets_dir: Path) -> tuple[str, str]:
    font_path = font_path.expanduser().resolve()
    base_entries = read_font_metadata_many(font_path)
    if not base_entries:
        raise ValueError(f"No font found in: {font_path}")
    base_family_name = base_entries[0][0]
    base_family_key = _normalize_font_family_name(base_family_name)

    variant_files: list[tuple[Path, int, str, str, list[str]]] = []
    for candidate in sorted(font_path.parent.iterdir()):
        if candidate.suffix.lower() not in SUPPORTED_FONT_EXTENSIONS or not candidate.is_file():
            continue

        # 先只读 name 表快速比对家族名，命中后再解码完整元数据
        if not any(
            _normalize_font_family_name(name) == base_family_key
            for name in _read_family_names(candidate)
        ):
            continue

        try:
            entries = read_font_metadata_many(candidate)
        except Exception:
            continue

        for family_name, weight, style, font_format, aliases in entries:
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
