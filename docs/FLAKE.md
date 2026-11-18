# 通过 Nix flake 安装

## 示例配置

```nix
# flake.nix
inputs.mdcss.url = "github:suif4599/mdcss";
```

```nix
# Home Manager 配置
## 需要 `I/M` 效果器版本
{
  imports = [
    developInputs.mdcss.homeManagerModules.mdcss
    developInputs.mdcss.homeManagerModules.markdown-preview-enhanced
  ];

  home.packages = [
    (developPkgs.vscode-with-extensions.override {
      vscode = vscodium-patched;
      vscodeExtensions = with developPkgs.vscode-extensions; [
        config.programs.markdown-preview-enhanced.finalPackage
      ];
    })
  ];

  programs.markdown-preview-enhanced.enable = true;

  services.mdcss = {
    enable = true;

    mainCss = "preview_theme/github-light.css";
    codeblockCss = "prism_theme/github.css";
    printMargin = "5mm";

    # 以下均为可选项
    font = "${some-font-pkg}/share/fonts/....otf";  # 正文字体
    codeFont = "${some-font-pkg}/share/fonts/....ttf";  # 代码块字体

    enableParser = true;  # 图片控制语法 / 表格合并 / 多列 / 标题编号等
  };
}
## 不需要 `I/M` 效果器版本
{
  imports = [
    developInputs.mdcss.homeManagerModules.mdcss
  ];

  services.mdcss = let
    mpe = pkgs.vscode-extensions.shd101wyy.markdown-preview-enhanced;
  in {
    enable = true;

    mainCss = "preview_theme/github-light.css";
    codeblockCss = "prism_theme/github.css";
    printMargin = "5mm";

    # 以下均为可选项
    font = "${some-font-pkg}/share/fonts/....otf";  # 正文字体
    codeFont = "${some-font-pkg}/share/fonts/....ttf";  # 代码块字体

    enableParser = true;  # 图片控制语法 / 表格合并 / 多列 / 标题编号等
  };
}
```

## Options

`services.mdcss` 的选项与命令行参数一一对应，语义见[完整参数](./CONFIG.md)：

| 选项 | 对应参数 | 默认值 |
| --- | --- | --- |
| `mainCss` / `codeblockCss` | `--main-css` / `--codeblock-css` | `preview_theme/github-light.css` / `prism_theme/github.css` |
| `font` / `codeFont` | `--font` / `--code-font` | `null`（不覆盖字体） |
| `printMargin` | `--print-margin` | `5mm` |
| `fontSize` | `--font-size` | `16px` |
| `autoCount` | `--auto-count` | `none, chinese, number, number, latin, roman` |
| `headingUnderline` | `--heading-underline` | `""`（关闭） |
| `enableParser` | `--enable-parser` | `false` |
| `enableTableCaption` | `--enable-table-caption` / `--no-...` | `true` |
| `tableCaptionPosition` | `--table-caption-position` | `"bottom"` |
| `enableTableHorizontalScroll` | `--enable-table-horizontal-scroll` | `false` |
| `cssFallbackFeatures` | `--css-fallback-features` | `[]`（字符串列表，等价于逗号分隔的 CLI 写法） |
| `extensionDir` | `--extension-dir` | `null` |
| `extensionsRoot` / `extensionPattern` | `--extensions-root` / `--extension-pattern` | `~/.vscode/extensions` / `shd101wyy.markdown-preview-enhanced-*` |

## `mdcss-bridge` 命令

Flake 安装方式不存在 `config/config.json`，options 会被烘焙进 `mdcss-bridge` 命令

```bash
mdcss-bridge                                # 重新生成并热更新
mdcss-bridge --emit-inkstone ~/inkstone     # 生成 inkstone 桥接产物
mdcss-bridge --auto-count chinese, number, number, number, latin, roman
                                            # 覆盖默认参数
```
