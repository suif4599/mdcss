"""Tests for the Inkstone bridge emission (src.inkstone)."""

from pathlib import Path


class TestBuildInkstoneBridge:
    """build_inkstone_bridge() output."""

    def test_exports_pre_and_post(self) -> None:
        from src.inkstone import build_inkstone_bridge

        bridge = build_inkstone_bridge("none, chinese, number, number, latin, roman")
        assert "export function mdcssPre(source)" in bridge
        assert "export function mdcssPost(html)" in bridge

    def test_no_comments_in_emitted_code(self) -> None:
        from src.inkstone import build_inkstone_bridge

        bridge = build_inkstone_bridge("none, chinese, number, number, latin, roman")
        for line in bridge.splitlines():
            assert not line.lstrip().startswith("//"), f"comment line leaked: {line!r}"
        assert "/*" not in bridge
        assert "*/" not in bridge

    def test_mpe_only_fragments_excluded(self) -> None:
        from src.inkstone import build_inkstone_bridge

        bridge = build_inkstone_bridge("none, chinese, number, number, latin, roman")
        # preparser_pdf (@import rewriting), postparser_uri_decode (crossnote
        # double-encoding fix), postparser_columnsync (crossnote scroll-sync)
        assert "@import" not in bridge
        assert "%25" not in bridge
        assert "containerRe" not in bridge
        # the invert-brightness filter element exists exactly once (appended
        # by postparser_svgfilter; the pre-pass variant is excluded — the
        # second string occurrence is the guard in svgfilter itself)
        assert bridge.count('<filter id="invert-brightness"') == 1

    def test_pre_fragment_order(self) -> None:
        from src.inkstone import build_inkstone_bridge

        bridge = build_inkstone_bridge("none, chinese, number, number, latin, roman")
        pre = bridge[bridge.index("mdcssPre"):bridge.index("mdcssPost")]
        # ledger before any line-count-changing fragment, fence extraction
        # before the line rewriters, fence restore last
        assert pre.index("__MDCSS_LINE_SHIFTS__") < pre.index("has-indent")
        assert pre.index("MDCSS_FENCE_TOKEN") < pre.index("mergeColumnSpec")
        assert pre.index("MDCSS_FENCE_TOKEN") < pre.index("preprocessMarkdown")
        # fence restore is the last pre fragment, so its lookup of the
        # extracted blocks comes after the column and title rewriters
        assert pre.rindex("__MDCSS_FENCED_BLOCKS__") > pre.index("mergeColumnSpec")
        assert pre.rindex("__MDCSS_FENCED_BLOCKS__") > pre.index("preprocessMarkdown")

    def test_post_fragment_order(self) -> None:
        from src.inkstone import build_inkstone_bridge

        bridge = build_inkstone_bridge("none, chinese, number, number, latin, roman")
        post = bridge[bridge.index("mdcssPost"):]
        assert post.index("MDCSS_CONTROL_RE") < post.index("cr_regex")
        assert post.index("cr_regex") < post.index("TABLE_COUNT_PLACEHOLDER")
        assert post.index("TABLE_COUNT_PLACEHOLDER") < post.index("mdcss-fig-row")
        # column style rebuild and svg filter append come after image/figure
        # work, and line-number restore runs last
        assert post.index("data-mdcss-col-align=") < post.index("invert-brightness")
        assert post.rindex("__mdcssOrigLine") > post.index("invert-brightness")

    def test_linerestore_uses_inkstone_attribute(self) -> None:
        from src.inkstone import build_inkstone_bridge

        bridge = build_inkstone_bridge("none, chinese, number, number, latin, roman")
        assert "data-source-line" not in bridge
        assert 'data-line="' in bridge

    def test_mappers_injected(self) -> None:
        from src.inkstone import build_inkstone_bridge

        bridge = build_inkstone_bridge("number, latin, roman, none, chinese, latinUpper")
        assert "number, latin, roman, none, chinese, latinUpper" in bridge

    def test_table_caption_toggle(self) -> None:
        from src.inkstone import build_inkstone_bridge

        assert "TABLE_COUNT_PLACEHOLDER" in build_inkstone_bridge(
            "none, chinese, number, number, latin, roman", enable_table_caption=True
        )
        assert "TABLE_COUNT_PLACEHOLDER" not in build_inkstone_bridge(
            "none, chinese, number, number, latin, roman", enable_table_caption=False
        )

    def test_invalid_mapper_raises(self) -> None:
        import pytest

        from src.inkstone import build_inkstone_bridge

        with pytest.raises(ValueError, match="Unsupported mapper"):
            build_inkstone_bridge("bogus")


class TestInkstoneCss:
    """The inkstone mdcss.css template content."""

    def css(self) -> str:
        from src.template import load_template

        return load_template("inkstone", "mdcss.css")

    def test_effects_gated_on_dark_theme(self) -> None:
        css = self.css()
        assert ":root[data-theme='dark'] .ink-prose img.mdcss-inv" in css
        assert ":root[data-theme='dark'] .ink-prose img.mdcss-bright" in css
        assert ":root[data-theme='dark'] .ink-prose img.mdcss-mix" in css

    def test_no_comments(self) -> None:
        assert "/*" not in self.css()

    def test_scoped_to_ink_prose(self) -> None:
        css = self.css()
        assert ".ink-prose .has-indent p" in css
        assert ".ink-prose img.mdcss-float-left" in css
        assert ".ink-prose figure.mdcss-fig-float-right" in css

    def test_no_print_or_font_face(self) -> None:
        css = self.css()
        assert "@media print" not in css
        assert "@font-face" not in css

    def test_zebra_avoids_hover_conflict(self) -> None:
        assert "tbody tr:nth-child(2n):not(:hover)" in self.css()

    def test_all_rules_scoped_to_ink_prose(self) -> None:
        css = self.css()
        for rule in css.split("}"):
            if rule.strip():
                assert ".ink-prose" in rule, rule


class TestWriteInkstoneOutput:
    """write_inkstone_output() file generation."""

    def test_writes_bridge_and_css_into_repo_tree(self, tmp_path: Path) -> None:
        from src.inkstone import write_inkstone_output

        repo = tmp_path / "inkstone"
        write_inkstone_output(repo, "none, chinese, number, number, latin, roman")
        assert (repo / "src" / "client" / "lib" / "markdown" / "mdcss-bridge.js").exists()
        assert (repo / "src" / "client" / "styles" / "mdcss.css").exists()


class TestParseMappers:
    """The shared parse_mappers() helper."""

    def test_expands_to_six_levels(self) -> None:
        from src.builder import parse_mappers

        assert parse_mappers("number") == ["number", "none", "none", "none", "none", "none"]

    def test_rejects_invalid(self) -> None:
        import pytest

        from src.builder import parse_mappers

        with pytest.raises(ValueError, match="Unsupported mapper"):
            parse_mappers("nope")
