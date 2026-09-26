{lib, pkgs, config, ...}: let
  cfg = config.services.mdcss;

  pythonEnv = pkgs.python3.withPackages (ps:
    with ps; [
      cssutils
      fonttools
      jsbeautifier
      cssbeautifier
    ]);

  scriptSrc = ./.;

  cliArgs =
    [
      "--main-css"
      cfg.mainCss
      "--codeblock-css"
      cfg.codeblockCss
      "--print-margin"
      cfg.printMargin
      "--auto-count"
      cfg.autoCount
    ]
    ++ lib.optionals (cfg.font != null) ["--font" cfg.font]
    ++ lib.optionals (cfg.codeFont != null) ["--code-font" cfg.codeFont]
    ++ lib.optionals (cfg.headingUnderline != "") ["--heading-underline" cfg.headingUnderline]
    ++ lib.optional cfg.enableParser "--enable-parser"
    ++ lib.optional cfg.enableTableHorizontalScroll "--enable-table-horizontal-scroll"
    ++ lib.optional cfg.enableTableCaption "--enable-table-caption"
    ++ lib.optional (!cfg.enableTableCaption) "--no-enable-table-caption"
    # runCommand has no TTY; the declared configuration is the confirmation.
    ++ lib.optionals (cfg.cssFallbackFeatures != []) [
      "--css-fallback-features" (lib.concatStringsSep "," cfg.cssFallbackFeatures)
    ]
    ++ lib.optional (!cfg.enableParser) "--yes"
    ++ (
      if cfg.extensionDir != null
      then ["--extension-dir" "${cfg.extensionDir}"]
      else ["--extensions-root" "${cfg.extensionsRoot}" "--extension-pattern" cfg.extensionPattern]
    );

  escapedArgs = lib.concatMapStringsSep " " lib.escapeShellArg cliArgs;

  crossnoteHome = pkgs.runCommand "mdcss-crossnote-home" {
    nativeBuildInputs = [pythonEnv];
  } ''
    mkdir -p $out/crossnote
    cd ${scriptSrc}
    PYTHONDONTWRITEBYTECODE=1 python mdcss.py ${escapedArgs} --output $out/crossnote
  '';

  deployScript = pkgs.writeShellScript "mdcss-deploy" ''
    set -euo pipefail
    if [ -n "''${XDG_CONFIG_HOME:-}" ]; then
      DEST="$XDG_CONFIG_HOME/crossnote"
    else
      DEST="$HOME/.local/state/crossnote"
    fi
    mkdir -p "$DEST"
    rm -rf -- "$DEST/style.less" "$DEST/parser.js" "$DEST/head.html" "$DEST/fonts"
    cp -a -- "${crossnoteHome}/crossnote/." "$DEST/"
    find "$DEST" -type d -exec chmod 755 {} +
    find "$DEST" -type f -exec chmod 644 {} +
    echo "Wrote $DEST" >&2
  '';

  # Nix installs have no config/config.json, so expose mdcss.py as a callable
  # wrapper with the module configuration baked in as defaults; extra CLI
  # arguments are appended and override them (argparse keeps the last
  # occurrence). Bare invocation regenerates and hot-deploys the crossnote
  # config; --emit-inkstone <repo-root> writes the Inkstone bridge artifacts
  # instead and skips the deployment steps.
  mdcssBridgeScript = pkgs.writeShellScriptBin "mdcss-bridge" ''
    set -euo pipefail
    emitInkstone=false
    for arg in "$@"; do
      if [ "$arg" = "--emit-inkstone" ]; then emitInkstone=true; fi
    done
    if [ -n "''${XDG_CONFIG_HOME:-}" ]; then
      DEST="$XDG_CONFIG_HOME/crossnote"
    else
      DEST="$HOME/.local/state/crossnote"
    fi
    if [ "$emitInkstone" = false ]; then
      mkdir -p "$DEST"
      rm -rf -- "$DEST/style.less" "$DEST/parser.js" "$DEST/head.html" "$DEST/fonts"
    fi
    PYTHONDONTWRITEBYTECODE=1 ${pythonEnv}/bin/python ${scriptSrc}/mdcss.py \
      ${escapedArgs} \
      --output "$DEST" \
      "$@"
    if [ "$emitInkstone" = false ]; then
      find "$DEST" -type d -exec chmod 755 {} +
      find "$DEST" -type f -exec chmod 644 {} +
      echo "Wrote $DEST" >&2
    fi
  '';
in {
  options.services.mdcss = {
    enable = lib.mkEnableOption "CrossNote style generation for markdown-preview-enhanced";

    font = lib.mkOption {
      type = with lib.types; nullOr (either str path);
      default = null;
      description = ''
        Main document font: either a path to a font file
        (.ttf/.otf/.woff/.woff2) or a font family name (Linux only,
        resolved via fontconfig's <literal>fc-match</literal>).
        When null, the document body font-family is not overridden.
      '';
    };

    codeFont = lib.mkOption {
      type = with lib.types; nullOr (either str path);
      default = null;
      description = ''
        Code block font. Same semantics as <option>services.mdcss.font</option>.
      '';
    };

    mainCss = lib.mkOption {
      type = lib.types.str;
      default = "preview_theme/github-light.css";
      description = ''
        Main theme CSS path. Relative paths are resolved under
        <literal>&lt;extension-dir&gt;/crossnote/styles/</literal>.
      '';
    };

    codeblockCss = lib.mkOption {
      type = lib.types.str;
      default = "prism_theme/github.css";
      description = ''
        Code block theme CSS path. Relative paths are resolved under
        <literal>&lt;extension-dir&gt;/crossnote/styles/</literal>.
      '';
    };

    printMargin = lib.mkOption {
      type = lib.types.str;
      default = "5mm";
      description = ''
        Print content margin. Supports CSS length units and 1-4 value
        syntax (e.g. <literal>2cm</literal>, <literal>20mm 10mm</literal>).
      '';
    };

    extensionDir = lib.mkOption {
      type = with lib.types; nullOr (either str path);
      default = null;
      description = ''
        Explicit markdown-preview-enhanced extension directory. Preferred
        over <option>extensionsRoot</option> + <option>extensionPattern</option>
        for Nix usage (the build sandbox cannot read ~/.vscode/extensions);
        set automatically by the markdown-preview-enhanced module. Example:
        <literal>"''${pkgs.vscode-extensions.shd101wyy.markdown-preview-enhanced}/share/vscode/extensions/shd101wyy.markdown-preview-enhanced"</literal>
      '';
    };

    extensionsRoot = lib.mkOption {
      type = with lib.types; either str path;
      default = "${config.home.homeDirectory}/.vscode/extensions";
      defaultText = "~/.vscode/extensions";
      description = ''
        Base directory containing VS Code extensions. Only consulted when
        <option>extensionDir</option> is null.
      '';
    };

    extensionPattern = lib.mkOption {
      type = lib.types.str;
      default = "shd101wyy.markdown-preview-enhanced-*";
      description = ''
        Glob pattern used to find the MPE extension directory under
        <option>extensionsRoot</option>. Only consulted when
        <option>extensionDir</option> is null.
      '';
    };

    enableParser = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Generate features that require parser.js support.";
    };

    enableTableHorizontalScroll = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = ''
        Allow horizontal scrolling for wide tables. Default forces content
        wrapping to avoid scroll.
      '';
    };

    enableTableCaption = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = ''
        Render "Table: caption" as a numbered figure caption below tables.
      '';
    };

    cssFallbackFeatures = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [];
      description = ''
        Layout/effect tokens (r, L, R, Lf, Rf, i, m) covered by CSS fallback
        rules when <option>enableParser</option> is false. Empty means
        width-only fallback (100 rules). Each selected token multiplies the
        generated rule count (e.g. ["r", "i"] produces 400 rules); builds
        pass --yes automatically, so large combinations never block.
      '';
    };

    autoCount = lib.mkOption {
      type = lib.types.str;
      default = "none, chinese, number, number, latin, roman";
      description = ''
        Comma-separated list of heading auto-count formatters for heading
        levels 1-6. Supported: roman, romanUpper, latin, latinUpper, chinese,
        number, none.
      '';
    };

    headingUnderline = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = ''
        Comma-separated heading levels to render with an underline (e.g.
        <literal>"1,2"</literal> for h1 and h2). Empty disables.
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    home.packages = [crossnoteHome mdcssBridgeScript];

    systemd.user.services.mdcss-deploy = {
      Unit = {
        Description = "Deploy CrossNote config (regular files, not symlinks)";
      };
      Service = {
        Type = "oneshot";
        ExecStart = deployScript;
        RemainAfterExit = true;
      };
      Install = {
        WantedBy = ["default.target"];
      };
    };
  };
}
