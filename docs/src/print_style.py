from pathlib import Path
from typing import Any

import cssutils  # pyright: ignore[reportMissingImports]

from src.template import load_template

cssutils.log.setLevel("CRITICAL")

ui_keywords = {
    ".sidebar",
    ".app-nav",
    ".github-corner",
    ".progress",
    "#app",
    ".search",
    "section.cover",
    ".sidebar-toggle",
    ".emoji",
    "::-webkit-scrollbar",
    "main",
    ".anchor",
    ".md-sidebar-toc",
    ".cover-main",
    "body.close",
    "body.sticky",
}

disallowed_global_props = {
    "-webkit-overflow-scrolling",
    "-webkit-tap-highlight-color",
    "-webkit-text-size-adjust",
    "-webkit-touch-callout",
}

disallowed_print_props = {
    "font-family",
}


def _is_ui_selector(selector_text: str) -> bool:
    return any(kw in selector_text for kw in ui_keywords)


def _convert_selector(selector_text: str) -> str:
    return (
        selector_text.replace(".markdown-preview.markdown-preview", "body").replace(
            ".markdown-preview", "body"
        )
    )


def generate_print_style(
    main_css_path: Path,
    codeblock_css_path: Path,
    reveal_css_path: Path | None = None,
    print_margin: str = "2cm",
    fallback_print_resets: str = "",
):
    """Generate @media print CSS safely with cssutils."""

    def load_css(path: Path | None):
        if path is None:
            return None
        if not path.exists():
            print(f"Warning: path not found, skipped: {path}")
            return None
        return path.read_text(encoding="utf-8")

    all_css = ""
    for path in [main_css_path, codeblock_css_path, reveal_css_path]:
        content = load_css(path)
        if content:
            all_css += content + "\n"

    if not all_css.strip():
        return "/* Error: no CSS content loaded */"

    sheet = cssutils.parseString(all_css)
    new_rules: list[str] = []

    def append_style_rule(rule_obj: Any):
        selector = rule_obj.selectorText

        if not selector or _is_ui_selector(selector):
            return

        new_rule = cssutils.css.CSSStyleRule()
        new_rule.selectorText = _convert_selector(selector)

        for prop in rule_obj.style:
            if selector.strip() == "*" and prop.name in disallowed_global_props:
                continue
            if prop.name in disallowed_print_props:
                continue
            new_rule.style.setProperty(prop.name, prop.value, priority="important")

        if new_rule.style.length > 0:
            new_rules.append(new_rule.cssText)

    for rule in sheet:
        if rule.type == rule.STYLE_RULE:
            append_style_rule(rule)
        elif rule.type == rule.MEDIA_RULE:
            if "print" not in rule.media.mediaText.lower():
                continue

            nested_rules: list[str] = []
            for nested in rule.cssRules:
                if nested.type != nested.STYLE_RULE:
                    continue

                selector = nested.selectorText
                if not selector or _is_ui_selector(selector):
                    continue

                nested_rule = cssutils.css.CSSStyleRule()
                nested_rule.selectorText = _convert_selector(selector)
                for prop in nested.style:
                    if prop.name in disallowed_print_props:
                        continue
                    nested_rule.style.setProperty(
                        prop.name,
                        prop.value,
                        priority="important",
                    )
                if nested_rule.style.length > 0:
                    nested_rules.append(nested_rule.cssText)

            if nested_rules:
                new_rules.extend(nested_rules)

    if not new_rules:
        raise ValueError("No valid styles extracted for print media")

    return load_template(
        "css", "printstyle.css",
        new_rules="\n".join(new_rules),
        print_margin=print_margin,
        fallback_print_resets=fallback_print_resets,
    )
