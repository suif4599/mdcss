"""Tests for src.config."""

import json
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Redirect CONFIG_DIR to a throwaway directory (never touch the real config/)
# ---------------------------------------------------------------------------

@pytest.fixture
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr("src.config.CONFIG_DIR", tmp_path)
    return tmp_path


class TestLoadConfig:
    """load_config() behavior."""

    def test_no_config_file(self, isolated_config: Path) -> None:
        from src.config import load_config

        result = load_config()
        assert result == {}

    def test_empty_config(self, isolated_config: Path) -> None:
        from src.config import load_config

        (isolated_config / "config.json").write_text("{}")
        result = load_config()
        assert result == {}

    def test_valid_config(self, isolated_config: Path) -> None:
        from src.config import load_config

        data = {"fonts": {"font": "~/test.ttf"}, "features": {"enable_parser": True}}
        (isolated_config / "config.json").write_text(json.dumps(data))
        result = load_config()
        assert result == data

    def test_invalid_json(self, isolated_config: Path, capsys: Any) -> None:
        from src.config import load_config

        (isolated_config / "config.json").write_text("{invalid json}")
        result = load_config()
        assert result == {}
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_non_dict_json(self, isolated_config: Path, capsys: Any) -> None:
        from src.config import load_config

        (isolated_config / "config.json").write_text(json.dumps(["a", "b"]))
        result = load_config()
        assert result == {}
        captured = capsys.readouterr()
        assert "Warning" in captured.out


class TestBuildParser:
    """build_parser() — argparse argument defaults."""

    def test_parser_has_expected_args(self) -> None:
        from src.config import build_parser

        parser = build_parser({})
        actions = {a.dest for a in parser._actions}

        for expected in {
            "extensions_root",
            "extension_pattern",
            "extension_dir",
            "expand_detail",
            "font",
            "code_font",
            "main_css",
            "codeblock_css",
            "print_margin",
            "enable_parser",
            "enable_table_caption",
            "enable_header",
            "enable_table_horizontal_scroll",
            "auto_count",
            "output",
            "save_config",
        }:
            assert expected in actions, f"Missing argument: {expected}"

    def test_parser_default_margin(self) -> None:
        from src.config import build_parser

        parser = build_parser({})
        args = parser.parse_args([])
        assert args.print_margin == "5mm"

    def test_parser_default_auto_count(self) -> None:
        from src.config import build_parser

        parser = build_parser({})
        args = parser.parse_args([])
        assert args.auto_count == "none, chinese, number, number, latin, roman"


class TestSaveConfig:
    """save_config() — round-trip."""

    def test_save_and_reload(self, isolated_config: Path) -> None:
        from argparse import Namespace

        from src.config import load_config, save_config

        args = Namespace(
            font=Path("~/test-font.ttf"),
            code_font=None,
            extensions_root=Path("~/.vscode/extensions"),
            extension_dir=None,
            extension_pattern="shd101wyy.markdown-preview-enhanced-*",
            output=Path("~/.local/state/crossnote"),
            print_margin="2cm",
            main_css=Path("github.css"),
            codeblock_css=Path("prism.css"),
            auto_count=None,
            enable_parser=True,
            enable_table_caption=True,
            enable_header=False,
            enable_table_horizontal_scroll=False,
            expand_detail=False,
            save_config=False,
        )
        save_config(args)
        loaded = load_config()
        assert isinstance(loaded, dict)
        assert loaded.get("features", {}).get("enable_parser") is True


class TestCssFallbackFeatures:
    """parse_css_fallback_features() and CLI wiring."""

    def test_parse_string_trims_and_dedupes(self) -> None:
        from src.config import parse_css_fallback_features

        assert parse_css_fallback_features(" r, i ,r, ") == ["r", "i"]

    def test_parse_list(self) -> None:
        from src.config import parse_css_fallback_features

        assert parse_css_fallback_features(["L", "Rf"]) == ["L", "Rf"]

    def test_parse_none_and_empty(self) -> None:
        from src.config import parse_css_fallback_features

        assert parse_css_fallback_features(None) == []
        assert parse_css_fallback_features("") == []

    def test_invalid_token_raises(self) -> None:
        from src.config import parse_css_fallback_features

        with pytest.raises(ValueError, match="Unsupported css-fallback token"):
            parse_css_fallback_features("r, I")
        with pytest.raises(ValueError, match="Unsupported css-fallback token"):
            parse_css_fallback_features("f")

    def test_parser_has_new_args(self) -> None:
        from src.config import build_parser

        parser = build_parser({})
        args = parser.parse_args([])
        assert args.css_fallback_features == ""
        assert args.yes is False

    def test_config_default_reads_list(self) -> None:
        from src.config import build_parser

        parser = build_parser({"features": {"css_fallback_features": ["r", "i"]}})
        args = parser.parse_args([])
        assert args.css_fallback_features == "r,i"

    def test_save_config_round_trip(self, isolated_config: Path) -> None:
        from argparse import Namespace

        from src.config import load_config, save_config

        args = Namespace(css_fallback_features="r,i")
        save_config(args)
        loaded = load_config()
        assert loaded.get("features", {}).get("css_fallback_features") == ["r", "i"]


class TestConfirmRuleCount:
    """confirm_rule_count() threshold behavior."""

    def test_at_or_below_threshold_passes(self) -> None:
        from src.config import confirm_rule_count

        assert confirm_rule_count(100, False) is True
        assert confirm_rule_count(200, False) is True

    def test_assume_yes_passes(self) -> None:
        from src.config import confirm_rule_count

        assert confirm_rule_count(2400, True) is True

    def test_tty_yes(self) -> None:
        from src.config import confirm_rule_count

        assert confirm_rule_count(400, False, isatty=lambda: True, ask=lambda p: "y\n") is True
        assert confirm_rule_count(400, False, isatty=lambda: True, ask=lambda p: "Yes") is True

    def test_tty_no(self) -> None:
        from src.config import confirm_rule_count

        assert confirm_rule_count(400, False, isatty=lambda: True, ask=lambda p: "") is False
        assert confirm_rule_count(400, False, isatty=lambda: True, ask=lambda p: "n") is False

    def test_non_tty_without_yes_exits(self) -> None:
        from src.config import confirm_rule_count

        with pytest.raises(SystemExit) as exc_info:
            confirm_rule_count(400, False, isatty=lambda: False)
        assert exc_info.value.code == 2


class TestNestedGet:
    """_nested_get() helper."""

    def test_flat_key(self) -> None:
        from src.config import _nested_get as f

        assert f({"a": 1}, "a") == 1

    def test_nested_key(self) -> None:
        from src.config import _nested_get as f

        assert f({"a": {"b": 2}}, "a.b") == 2

    def test_missing_key_returns_default(self) -> None:
        from src.config import _nested_get as f

        assert f({"a": 1}, "b") is None
        assert f({"a": 1}, "b", 42) == 42

    def test_partial_path_returns_default(self) -> None:
        from src.config import _nested_get as f

        assert f({"a": {"b": 1}}, "a.x.y") is None