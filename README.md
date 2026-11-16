# MdCSS：Beyond Markdown

**使用文档** · [语法文档(在线预览)](https://suif4599.github.io/mdcss/) · [参数列表](./docs/CONFIG.md) · [Flake](./docs/FLAKE.md) · [Inkstone 桥接](./docs/INKSTONE.md)

MdCSS 是一个 Markdown 语法拓展，为 Markdown 增加图片宽度与文字环绕、表格合并单元格、多列布局、标题自动编号、块间空行、图片反相、去背景等排版能力，同时完全向下兼容标准 Markdown

MdCSS 无法独立工作，依赖 [Markdown Preview Enhanced](https://github.com/shd101wyy/vscode-markdown-preview-enhanced)（MPE，VS Code 插件）或者 [inkstone](https://github.com/shuaiplus/inkstone)

## 功能介绍

| 类别 | 功能 |
| --- | --- |
| **图片** | 宽度控制、单行多图、对齐、文字环绕、反相、去背景、图片标题等 |
| **表格** | 合并单元格、表格标题、自动列宽、斑马纹等 |
| **排版** | 多列布局、标题自动编号、段落缩进、块间空行等 |

可以 [在线预览](https://suif4599.github.io/mdcss/) MdCSS 的大多数效果，下图是一个简单的展示，包括图片效果、图片排版、多列排版、合并单元格、表格斑马纹、标题与自动编号等功能

<div style="width:80%; margin:0 auto; text-align:center; border:2px solid #ccc; border-radius:16px; overflow:hidden; box-sizing:border-box;">
  <img src="./docs/assets/demo.png" alt="demo" />
</div>

## 快速开始

MdCSS 同时支持使用 pixi 或者 flake 安装，flake 方式请参考[文档](docs/install_nix.md)，下面将介绍通用的 pixi 安装

### pixi

```bash
git clone https://github.com/suif4599/mdcss.git
cd mdcss
pixi run python mdcss.py \
    --main-css preview_theme/github-light.css \
    --codeblock-css prism_theme/github.css \
    --enable-parser
```

然后在 VSCode 中执行 `Developer: Reload Window` 或者重启 VSCode

> [!TIP]
> 若使用 `MPE >= 0.8.36`，且需要 `I/M` 两个效果器，需要额外执行下面的步骤
> ```bash
> pixi run python tools/patch_mpe.py
> ```
> 在 VSCode 中将 `markdown-preview-enhanced.enablePreviewScripts` 设置为 `true`
> 执行 `Developer: Reload Window` 或者重启 VSCode

> 完整参数列表见[参数列表](docs/CONFIG.md)，部分打印效果必须使用 **Chrome (Puppeteer)** 导出才能生效

## License

[MIT](LICENSE)
