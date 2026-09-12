from src.config import (
    build_parser,
    confirm_rule_count,
    load_config,
    parse_css_fallback_features,
    resolve_crossnote_style_path,
    save_config,
    resolve_extension_dir,
)
from src.builder import (
    build_style_blocks,
    build_parser_blocks,
    write_output,
    load_template,
    count_fallback_rules,
    RULE_COUNT_THRESHOLD,
)


def main() -> None:
    config = load_config()
    parser = build_parser(config)
    args = parser.parse_args()

    if args.main_css is None:
        parser.error("--main-css is required (set it via CLI or 'main_css' in config.json)")
    if args.codeblock_css is None:
        parser.error("--codeblock-css is required (set it via CLI or 'codeblock_css' in config.json)")

    try:
        css_fallback_features = parse_css_fallback_features(args.css_fallback_features)
    except ValueError as exc:
        parser.error(str(exc))

    if args.save_config:
        save_config(args)
        return

    if not args.enable_parser:
        confirm_rule_count(
            count_fallback_rules(css_fallback_features),
            args.yes,
            threshold=RULE_COUNT_THRESHOLD,
        )

    extension_dir = resolve_extension_dir(
        extensions_root=args.extensions_root,
        extension_pattern=args.extension_pattern,
        explicit_extension_dir=args.extension_dir,
    )

    main_css_path = resolve_crossnote_style_path(
        extension_dir=extension_dir,
        css_path=args.main_css,
    )
    codeblock_css_path = resolve_crossnote_style_path(
        extension_dir=extension_dir,
        css_path=args.codeblock_css,
    )

    print_margin = args.print_margin.strip()
    output_path = args.output.expanduser().resolve()
    font_assets_dir = output_path / "fonts"

    blocks = build_style_blocks(
        font_path=args.font,
        main_css_path=main_css_path,
        codeblock_css_path=codeblock_css_path,
        print_margin=print_margin,
        font_assets_dir=font_assets_dir,
        code_font_path=args.code_font,
        enable_parser=args.enable_parser,
        enable_table_horizontal_scroll=args.enable_table_horizontal_scroll,
        heading_underline=args.heading_underline,
        font_size=args.font_size,
        css_fallback_features=css_fallback_features,
    )

    if args.enable_parser:
        parse_blocks, html_blocks = build_parser_blocks(args.auto_count, args.enable_table_caption)
    else:
        parse_blocks, html_blocks = [], []

    header_blocks: list[str] = []
    if args.enable_header:
        if args.expand_detail:
            header_blocks.append(
                load_template("docheader", "expand_detail.js")
            )

    write_output(output_path, blocks, parse_blocks, html_blocks, header_blocks)


if __name__ == "__main__":
    main()
