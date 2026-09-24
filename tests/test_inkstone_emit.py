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
        # the I/M effects are runtime-canvas only; no SVG filter defs remain
        assert "<filter" not in bridge
        assert "url(#invert-brightness" not in bridge
        assert "url(#matte-brightness" not in bridge

    def test_pre_fragment_order(self) -> None:
        from src.inkstone import build_inkstone_bridge

        bridge = build_inkstone_bridge("none, chinese, number, number, latin, roman")
        pre = bridge[bridge.index("mdcssPre"):bridge.index("mdcssPost")]
        # ledger before any line-count-changing fragment, fence extraction
        # before the line rewriters, fence restore last
        assert pre.index("__MDCSS_LINE_SHIFTS__") < pre.index("has-indent")
        assert pre.index("MDCSS_FENCE_TOKEN") < pre.index("mergeColumnSpec")
        assert pre.index("MDCSS_FENCE_TOKEN") < pre.index("preprocessMarkdown")
        # zebra tag normalization after fence extraction, before the rewriters
        assert pre.index("MDCSS_FENCE_TOKEN") < pre.index("mode.toLowerCase()")
        # fence restore is the last pre fragment, so its lookup of the
        # extracted blocks comes after the column and title rewriters
        assert pre.rindex("__MDCSS_FENCED_BLOCKS__") > pre.index("mergeColumnSpec")
        assert pre.rindex("__MDCSS_FENCED_BLOCKS__") > pre.index("preprocessMarkdown")

    def test_post_fragment_order(self) -> None:
        from src.inkstone import build_inkstone_bridge

        bridge = build_inkstone_bridge("none, chinese, number, number, latin, roman")
        post = bridge[bridge.index("mdcssPost"):]
        assert post.index("MDCSS_CONTROL_RE") < post.index("cr_regex")
        # zebra strategies read rowspan attrs (table.js) and strip the tag
        # before the caption wrap rewrites the "Table:" paragraph
        assert post.index("cr_regex") < post.index("MDCSS_ZEBRA_TAG_RE")
        assert post.index("MDCSS_ZEBRA_TAG_RE") < post.index("TABLE_COUNT_PLACEHOLDER")
        assert post.index("TABLE_COUNT_PLACEHOLDER") < post.index("mdcss-fig-row")
        # column style rebuild comes after image/figure work, and the
        # line-number restore runs last
        assert post.index("data-mdcss-col-align=") < post.rindex("__mdcssOrigLine")

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
        assert ":root[data-theme='dark'] .ink-prose img.mdcss-mix" in css
        # I/M are runtime-canvas effects and carry no filter rule; the matte
        # rule only drops the host image backdrop (and frame) so the alpha
        # knocked out by the runtime actually shows through
        assert "mdcss-bright" not in css
        assert ":root[data-theme='dark'] .ink-prose img.mdcss-matte," in css
        assert ":root[data-theme='dark'] .ink-prose img[class*='mdcss-matte-']" in css
        assert "background: transparent" in css
        assert "border-color: transparent" in css

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

    def test_zebra_strategy_rules_present(self) -> None:
        css = self.css()
        # auto 条带规则让位于 hover；nth-child 抑制同样带 :not(:hover)
        assert ".ink-prose table.mdcss-auto tbody tr:not(:hover).mdcss-z" in css
        assert ".ink-prose table.mdcss-nozebra tbody tr:nth-child(2n):not(:hover)" in css

    def test_zebra_uses_host_stripe_token(self) -> None:
        # the host palette owns the stripe color; keep the neutral fallback for hosts without the token
        assert "var(--tbl-stripe, rgba(127, 127, 127, 0.07))" in self.css()

    def test_table_base_uses_host_token(self) -> None:
        # table body fill comes from the host too; token-less hosts get no fill (original behavior)
        assert "var(--tbl-bg, transparent)" in self.css()

    def test_all_rules_scoped_to_ink_prose(self) -> None:
        css = self.css()
        for rule in css.split("}"):
            if rule.strip():
                assert ".ink-prose" in rule, rule


class TestBuildInkstoneRuntime:
    """build_inkstone_runtime() output."""

    def runtime(self, invert_bounds=(10, 250), matte_bounds=(5, 240)) -> str:
        from src.inkstone import build_inkstone_runtime

        return build_inkstone_runtime(invert_bounds, matte_bounds)

    def test_injects_theme_gate_and_bounds(self) -> None:
        runtime = self.runtime()
        assert "var THEME_GATED = true;" in runtime
        assert "var INVERT_BOUNDS = [10, 250];" in runtime
        assert "var MATTE_BOUNDS = [5, 240];" in runtime

    def test_default_bounds(self) -> None:
        runtime = self.runtime(
            invert_bounds=(32, 239), matte_bounds=(64, 239)
        )
        assert "var INVERT_BOUNDS = [32, 239];" in runtime
        assert "var MATTE_BOUNDS = [64, 239];" in runtime

    def test_no_comments_in_emitted_code(self) -> None:
        # stronger than Inkstone's comment policy: this file has no URL or
        # division that could leave a "//" behind, so none may survive
        runtime = self.runtime()
        assert "//" not in runtime
        assert "/*" not in runtime
        assert "*/" not in runtime

    def test_node_test_hook_stripped(self) -> None:
        runtime = self.runtime()
        assert "module.exports" not in runtime
        assert "@MDCSS_TEST_HOOK_" not in runtime

    def test_self_booting_and_theme_aware(self) -> None:
        runtime = self.runtime()
        assert "MutationObserver" in runtime
        assert "attributeFilter: ['data-theme']" in runtime
        assert "DOMContentLoaded" in runtime

    def test_keeps_effect_class_for_theme_restore(self) -> None:
        runtime = self.runtime()
        # the effect class survives the src swap so a light-theme restore
        # can re-derive the effect on the next dark flip
        assert "classList.remove" not in runtime
        assert "mdcssSrc" in runtime


class TestWriteInkstoneOutput:
    """write_inkstone_output() file generation."""

    def test_writes_bridge_and_css_into_repo_tree(self, tmp_path: Path) -> None:
        from src.inkstone import write_inkstone_output

        repo = tmp_path / "inkstone"
        write_inkstone_output(repo, "none, chinese, number, number, latin, roman")
        assert (repo / "src" / "client" / "lib" / "markdown" / "mdcss-bridge.js").exists()
        assert (repo / "src" / "client" / "styles" / "mdcss.css").exists()

    def test_writes_runtime_artifacts_into_repo_tree(self, tmp_path: Path) -> None:
        from src.inkstone import write_inkstone_output

        repo = tmp_path / "inkstone"
        write_inkstone_output(repo, "none, chinese, number, number, latin, roman")
        runtime = repo / "src" / "client" / "lib" / "markdown" / "mdcss-runtime.js"
        runtime_dts = repo / "src" / "client" / "lib" / "markdown" / "mdcss-runtime.d.ts"
        assert runtime.exists()
        assert "THEME_GATED = true" in runtime.read_text(encoding="utf-8")
        assert runtime_dts.exists()
        assert runtime_dts.read_text(encoding="utf-8") == "export {};\n"


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
