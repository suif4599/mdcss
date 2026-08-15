# MdCSS：Beyond Markdown

**目录**：

- [1. 功能一览](#1-功能一览)
- [2. 使用示例](#2-使用示例)
- [3. 参数说明](#3-参数说明)
- [4. 功能详细说明](#4-功能详细说明)
  - [打印样式](#打印样式)
  - [图片](#图片)
  - [字体](#字体)
  - [多列排版](#多列排版)
  - [页边距](#页边距)
  - [小标题编号](#小标题编号)
  - [段落缩进](#段落缩进)
  - [PDF 导入居中](#pdf-导入居中)
  - [表格增强](#表格增强)
  - [代码块](#代码块)
  - [自动展开 detail](#自动展开-detail)
- [5. 在 nix 中使用](#5-在nix中使用)

这是一个增强 VS Code 的 Markdown Preview Enhanced (MPE) 插件功能的脚本，旨在扩展 Markdown 文件的排版能力，让相对轻量的排版需求不必使用 $\LaTeX$。

脚本生成的配置文件允许为 PDF 导出设置单独的主题，同时实现了图片的排版增强、表格的合并单元格、自定义字体、自定义页边距等功能。

注意，脚本提供的部分功能必须使用 **Chrome (Puppeteer)** 才能生效

## 1. 功能一览

若想获得可视化的说明，请参阅 [语法文档](docs/SYNTAX.md)。

| 类别 | 功能 |
| --- | --- |
| **图片** | 宽度控制（百分比/px）、单行多图、对齐、文字环绕、反相、亮度反转、去背景、图片标题 |
| **表格** | 合并单元格、删除单元格、跨页重复标题、表格标题、自动列宽 |
| **多列排版** | 多列布局、列宽控制（百分比/px）、竖直对齐（上/中/下） |
| **标题编号** | 多级编号、6 种样式（数字/拉丁/罗马/中文等）、可配置各级格式 |
| **代码行数** | 语言种类后添加 `{.line-numbers}` 启用行号 |
| **Callout** | 支持展开/嵌套、多种样式（abstract/tip/warning 等） |
| **排版** | 段落缩进、代码块不断页 |
| **PDF** | 导入 PDF 居中显示 |

## 2. 使用示例

```bash
python mdcss/mdcss.py \
    --font ~/.local/share/fonts/HanSans/CN/SourceHanSansCN-Regular.otf \
    --code-font ~/.local/share/fonts/maple-NF-CN/MapleMonoNL-NF-CN-Regular.ttf \
    --main-css preview_theme/github-light.css \
    --codeblock-css prism_theme/github.css \
    --save-config
```

## 3. 参数说明

使用前可从 `config/config.example.json` 复制一份到同目录下，命名为 `config.json`。配置文件已加入 `.gitignore`，不会误提交。

所有参数均可通过命令行或 `config/config.json` 配置。CLI 参数优先级高于配置文件。

| 参数 | 默认值 | 说明 |
| --- | ----- | ----- |
| `--main-css` | **必需** | 正文打印主题 CSS，相对路径在 `<extension-dir>/crossnote/styles/` 中搜索 |
| `--codeblock-css` | **必需** | 代码块打印主题 CSS，相对路径在 `<extension-dir>/crossnote/styles/` 中搜索 |
| `--font` | `None` | 正文字体文件路径（.ttf/.otf/.woff/.woff2），自动解析同目录下的同族变体 |
| `--code-font` | `None` | 代码块字体文件路径，同上 |
| `--print-margin` | `5mm` | 打印页边距，支持 CSS 长度单位和 1-4 值语法（如 `2cm`、`20mm 10mm`） |
| `--output` | `~/.local/state/crossnote` | 输出目录（style.less、parser.js、head.html） |
| `--extensions-root` | `~/.vscode/extensions` | VS Code 扩展根目录 |
| `--extension-pattern` | `shd101wyy.markdown-preview-enhanced-*` | 匹配 MPE 扩展目录的 glob |
| `--extension-dir` | `None` | 显式指定扩展目录（覆盖前两个参数） |
| `--enable-parser` | `False` | 启用 parser.js 增强功能（图片 alt 宽度、表格合并、多列、标题编号、缩进等） |
| `--enable-header` | `False` | 启用 head.html 注入（配合 `--expand-detail`） |
| `--expand-detail` | `False` | 打印时自动展开 `<detail>` 标签（需要 `--enable-header`） |
| `--enable-table-horizontal-scroll` | `False` | 允许宽表格水平滚动（默认强制换行避免滚动） |
| `--auto-count` | `none, chinese, number, number, latin, roman` | 标题编号样式，逗号分隔的 6 个值对应 h1-h6，支持 `number`/`latin`/`latinUpper`/`roman`/`romanUpper`/`chinese`/`none` |
| `--save-config` | `False` | 将生效的参数保存到 `mdcss/config.json` 后退出 |

## 4. 功能详细说明

### 打印样式

- 使用 `--main-css` 来设置打印时使用的正文主题，传入的相对路径在 `{EXTENSION_DIR}/crossnote` 中搜索
- 使用 `--codeblock-css` 来设置打印时使用的代码块主题，传入的相对路径在 `{EXTENSION_DIR}/crossnote` 中搜索

### 图片

- 宽度设置：在alt中以1-2位整数开头，设置宽度百分比，`--enable-parser` 启用时还支持添加单位 `px` 来设置绝对宽度
- 单行多图布局：在alt中添加 `r`
- 左右对齐：在alt中添加 `L/R`
- 文字环绕图片：在alt中添加 `f`
- 反相：在alt中添加 `i`，反相仅在预览时生效
- 去除背景（实验性）：在alt中添加 `m`，原理为设置混合模式为 `multiply`，去除背景仅在预览时生效，该功能为实验性功能，可能存在部分异常
- 亮度反转（实验性）：当 `--enable-parser` 启用时，可以在alt中添加 `I`，亮度反转仅在预览时生效，该功能为实验性功能，可能存在部分异常
- 图片标题：当 `--enable-parser` 启用时，可以在alt中使用 `([.]title)` 来插入标题，开头的`.`会被替换成递增的 `图N:`，对于 `r` 样式的图片，可以在第一个子图中添加 `([.]subfigure-title([.]figure-title))` 来添加整体标题

### 字体

- 使用 `--font` 设置全局字体，只需要给出一个字体文件，程序会自动解析同族字体
- 使用 `--code-font` 设置代码块字体，只需要给出一个字体文件，程序会自动解析同族字体
- 对于公式，始终使用默认字体

### 多列排版

当 `--enable-parser` 启用时生效

- 使用 `|||-` 来开始一个多列排版，`|||` 来分隔列，`-|||` 来结束多列排版，可以添加参数用来设置列宽和对齐方式
- 多列排版支持除了浮动布局的图片之外的所有语法

#### 设置列宽

- 列宽支持百分比和像素的设置方式，使用 `%` 与 `px`，默认使用百分比
- 不填写列宽时会平均分配（不是按内容宽度分配）

#### 竖直对齐

- 默认竖直对齐方式为向上对齐，使用 `:` 来指定对齐方式
- 比如 `:240px` 表示列宽 240px 且向上对齐
- 比如 `:50%:` 表示列宽 50% 且居中对齐

### 页边距

- 使用 `--print-margin` 设置页边距

### 小标题编号

当 `--enable-parser` 启用时生效

- 在标题开头的 `.` 会被替换成编号

**编号样式**：

- `latin[Upper]`: `a)`, `b)`, `c)`
- `roman[Upper]`: `i)`, `ii)`, `iii)`，上限3999
- `chinese`: `一、`, `二、`, `三、`
- `number`: `1.`, `2.`, `3.`，且 `number` 在连续使用时可以生成 `1.1.`, `1.2.`, `1.3.`
- `none`: 不编号

**配置方式**：

设置 `--auto-count` 参数为 `,` 分割的六个编号样式，默认 `none, chinese, number, number, latin, roman`

### 段落缩进

当 `--enable-parser` 启用时生效

- 在文档开头添加 `@indent` 或 `<indent>` 来为该文档启用段落缩进

### PDF 导入居中

当 `--enable-parser` 启用时生效

- `@import` 导入的PDF会居中显示

### 表格增强

当 `--enable-parser` 启用时生效

- 使用 `\` 删除单元格（包括标题），如需要输入`\`，请使用`\\\\`
- 使用 `c\d` 和 `d\d` 的前缀来表示合并单元格，使用 `:` 为单元格单独设置对齐

```markdown
| c2: 标题1 |      \     |     标题2    | 标题3 |
| --------- | ---------- | ------------ | ----- |
|   文本1   | :c2: 文本2 |       \      |  \\\  |
|  r2 文本3 |    文本4   | :r2c2: 文本5 |   \   |
|     \     |    文本6   |       \      |   \   |
```

### 代码块

代码块不会另起一页，而是直接跟随上一页

### 自动展开 detail

使用 `--expand-detail`（当 `--enable-header` 启用时生效）之后，`<detail>` 标签（比如Callout）会在打印时自动展开

## 5. 在nix中使用

仓库本身是一个 flake，提供 Home Manager module（`homeManagerModules.mdcss`），无需手动 fetchgit：

```nix
# flake.nix
inputs.mdcss.url = "github:suif4599/mdcss";
```

```nix
# Home Manager 配置
{
  imports = [inputs.mdcss.homeManagerModules.mdcss];

  services.mdcss = {
    enable = true;

    mainCss = "preview_theme/github-light.css";
    codeblockCss = "prism_theme/github.css";
    printMargin = "5mm";

    # 以下均为可选项
    font = "${some-font-pkg}/share/fonts/....otf";  # 正文字体
    codeFont = "${some-font-pkg}/share/fonts/....ttf";  # 代码块字体

    enableParser = true;  # 图片宽度 / 表格合并 / 多列 / 标题编号等
    enableHeader = true;  # head.html 注入
    expandDetail = true;  # 打印时自动展开 <details>（需 enableHeader）

    # 推荐显式指定扩展目录，避免运行时去 ~/.vscode/extensions 匹配
    extensionDir = "${pkgs.vscode-extensions.shd101wyy.markdown-preview-enhanced}/share/vscode/extensions/shd101wyy.markdown-preview-enhanced";
  };
}
```

其余选项（`autoCount`、`headingUnderline`、`enableTableCaption` 等）与第 3 节的 CLI 参数一一对应。

部署方式说明：

- 构建产物 `style.less` / `parser.js` / `head.html` / `fonts/` 由 oneshot 服务 `mdcss-deploy.service` 在登录时以普通可写文件部署到 crossnote 的配置目录。
- 部署目标与 MPE 扩展自身的解析逻辑一致：设置了 `XDG_CONFIG_HOME` 时为 `$XDG_CONFIG_HOME/crossnote`，否则为 `~/.local/state/crossnote`。注意扩展在 Linux 下**不会**读取 `~/.config/crossnote`（除非通过 `XDG_CONFIG_HOME` 指过去）。
- 扩展会在同一目录维护自己的 `config.js`（katex/mathjax/mermaid 等设置），部署脚本只替换上述四个受管条目，不会触碰它；也因此不能使用指向 nix store 的只读符号链接（`xdg.configFile`）来部署。
