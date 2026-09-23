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
- [6. inkstone 桥接](#6-inkstone-桥接)

这是一个增强 VS Code 的 Markdown Preview Enhanced (MPE) 插件功能的脚本，旨在扩展 Markdown 文件的排版能力，让相对轻量的排版需求不必使用 $\LaTeX$。

脚本生成的配置文件允许为 PDF 导出设置单独的主题，同时实现了图片的排版增强、表格的合并单元格、自定义字体、自定义页边距等功能。

注意，脚本提供的部分功能必须使用 **Chrome (Puppeteer)** 才能生效

**部署生效说明**（parser.js / style.less / head.html）：

- MPE 以工作区 `.crossnote/` 中的文件**优先于**全局配置目录（`~/.local/state/crossnote`）：若工作区存在 `.crossnote/parser.js`，部署到全局的版本会被遮蔽、不生效
- MPE 仅在预览引擎初始化时读取 parser.js，重新生成后需执行 `Developer: Reload Window` 才能在预览 / Open in Browser 中生效

## 1. 功能一览

若想获得可视化的说明，请参阅 [语法文档](docs/SYNTAX.md)。

| 类别 | 功能 |
| --- | --- |
| **图片** | 宽度控制（百分比/px）、单行多图、对齐、文字环绕、反相、亮度两端互换（可调阈值）、亮部抠图＋暗部提亮（可调阈值）、去背景、图片标题 |
| **表格** | 合并单元格、删除单元格、跨页重复标题、表格标题、自动列宽、间行深浅背景色（预览+打印） |
| **多列排版** | 多列布局、列宽控制（百分比/px）、竖直对齐（上/中/下）、主列标记 |
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
| `--font` | `None` | 正文字体文件路径（.ttf/.otf/.woff/.woff2/.ttc/.otc）或字体名称，路径自动解析同目录下的同族变体 |
| `--font-size` | `16px` | 基础字号，较小的字号可避免宽表格自动缩小 |
| `--code-font` | `None` | 代码块字体文件路径或字体名称，其余语义同 `--font` |
| `--print-margin` | `5mm` | 打印页边距，支持 CSS 长度单位和 1-4 值语法（如 `2cm`、`20mm 10mm`） |
| `--output` | `~/.local/state/crossnote` | 输出目录（style.less、parser.js、head.html） |
| `--extensions-root` | `~/.vscode/extensions` | VS Code 扩展根目录 |
| `--extension-pattern` | `shd101wyy.markdown-preview-enhanced-*` | 匹配 MPE 扩展目录的 glob |
| `--extension-dir` | `None` | 显式指定扩展目录（覆盖前两个参数） |
| `--enable-parser` | `False` | 启用 parser.js 增强功能（图片控制语法、表格合并、多列、标题编号、缩进等） |
| `--css-fallback-features` | `""` | 纯 CSS 模式（未启用 `--enable-parser`）下额外覆盖的布局/效果 token，逗号分隔：`r`/`L`/`R`/`Lf`/`Rf`/`i`/`m`。空 = 仅宽度回退（100 条规则）；生成的规则数超过 200 时需要确认 |
| `--yes` | `False` | 跳过规则数确认提示（无人值守场景，如 nix 构建；非交互且无此参数时直接报错退出） |
| `--invert-bounds` | `32,239` | `I` 效果的默认亮度阈值 `lo,hi`（8-bit）：低于 `lo` 或高于 `hi` 的像素亮度互换；单图可用 `I(lo,hi)` 覆盖 |
| `--matte-bounds` | `64,239` | `M` 效果的默认亮度阈值 `lo,hi`：低于 `lo` 的像素提亮、高于 `hi` 的像素透明；单图可用 `M(lo,hi)` 覆盖 |
| `--enable-header` | `False` | 启用 head.html 注入（`--expand-detail`，以及 `--enable-parser` 时自动包含的 I/M 运行时处理器） |
| `--expand-detail` | `False` | 打印时自动展开 `<detail>` 标签（需要 `--enable-header`） |
| `--enable-table-horizontal-scroll` | `False` | 允许宽表格水平滚动（默认强制换行避免滚动） |
| `--auto-count` | `none, chinese, number, number, latin, roman` | 标题编号样式，逗号分隔的 6 个值对应 h1-h6，支持 `number`/`latin`/`latinUpper`/`roman`/`romanUpper`/`chinese`/`none` |
| `--save-config` | `False` | 将生效的参数保存到 `mdcss/config.json` 后退出 |

## 4. 功能详细说明

### 打印样式

- 使用 `--main-css` 来设置打印时使用的正文主题，传入的相对路径在 `{EXTENSION_DIR}/crossnote` 中搜索
- 使用 `--codeblock-css` 来设置打印时使用的代码块主题，传入的相对路径在 `{EXTENSION_DIR}/crossnote` 中搜索

### 图片

图片语法为 `![control|caption|alt](src)`，以 `|` 分隔为三段，后两段可整体省略；第一段（无 `|` 时取整段）不匹配控制语法且非空时，整段 alt 视为真实替代文本，不触发任何控制语法（`![An English alt](src)` 完全安全）。

> **Breaking change**：旧版把控制串直接混写在 alt 里的语法（如 `![80ri(.标题)](x.png)`）已移除，此类 alt 现在会被当作真实替代文本原样输出。

**control 控制串**（按顺序组合，宽度必须存在，也可整体留空表示仅图注/alt）：

- 宽度：1-4 位整数 + 可选单位 `%`（默认，封顶 100）/ `px`（不封顶）；纯 CSS 模式（未启用 `--enable-parser`）只识别带 `%` 的宽度
- 布局：`r` 单行多图、`L`/`R` 左右对齐、`Lf`/`Rf` 文字环绕
- 效果：`i` 反相、`m` 去背景（实验性，混合模式 `multiply`）、`I` 亮度两端互换（实验性，需 parser + head.html）、`M` 亮部抠图＋暗部提亮（实验性，需 parser + head.html）；效果仅在预览时生效
- `I`/`M` 由 head.html 中的运行时 canvas 处理器在图片原始分辨率上逐像素完成（画质与原图一致，含抗锯齿边缘的连续处理），可按图指定阈值（如 `I(10,253)`/`M(64,250)`），默认值见 `--invert-bounds`/`--matte-bounds`；跨域不可读的图片（如导出的 file:// 页面）保持原样

**caption 图注与 alt 真实替代文本**（需 parser）：

- 普通图注前导 `.` 会被替换成递增的 `图N:`；`r` 布局的子图标题前导 `.` 改为 `(a)(b)(c)` 字母编号（按组内顺序，不占用全局图号），整组总标题（写在第一个子图的图注 `(.总标题)` 中）前导 `.` 仍使用 `图N:` 编号
- 第三个 `|` 之后的所有内容都属于真实 alt（可包含 `|`）；输出 HTML 的 `alt=` 依次取真实 alt、图注文本、空串，控制串不会泄漏
- 注意：表格单元格内的 `|` 需转义为 `\|`；纯数字 alt（如 `2023`）会被当作宽度控制串

- 非 ASCII 文件名（如中文）的本地图片在 MPE 的「Open in Browser」/ 导出 HTML 中会被二次 URL 编码导致失效，`--enable-parser` 启用时 parser 会自动还原一次双重编码；文件名本身含字面 `%` 的除外

示例：`![40%ri|.图注|A photo](src.png)`、`![80%](src.png)`（纯 CSS 模式同样生效）、`![|.仅图注](src.png)`

**纯 CSS 回退**（未启用 `--enable-parser`）：

- 宽度规则始终生成（`![40%](src)` 有效；无单位宽度与 `px` 需 parser）
- 布局/效果字母可通过 `--css-fallback-features` 选择性覆盖（如 `"r,i"`），规则按前缀精确匹配穷举生成（`img[alt^="40%ri"]`），不会误伤真实 alt；规则数超过 200 时需交互确认或加 `--yes`
- 图注、子图总标题、浮动与段落合并为 parser 专属功能

### 字体

- 使用 `--font` 设置全局字体，只需给出一个字体文件，程序会自动解析同族字体；也可以直接给字体名称（如 `Segoe UI`），程序会在系统字体中自动查找（Linux 用 fontconfig，Windows 用字体注册表 / 系统字体目录）
- 使用 `--code-font` 设置代码块字体，只需给出一个字体文件，程序会自动解析同族字体，同样支持按字体名称查找
- 使用 `--font-size` 设置基础字号（默认 16px），较小的字号可避免宽表格自动缩小
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

#### 主列标记

- 在列参数末尾追加 `!` 将该列标记为主列，比如 `|||60!` 表示该列列宽 60% 且为主列；出现多个 `!` 时以第一个为准，未标记时默认第一列为主列
- 主列用于控制 MPE 双窗口预览的滚动同步：编辑其他列内容时预览冻结不动，编辑主列内容时预览跟随滚动
- 该功能同时修复了启用 `--enable-parser` 时滚动同步的行号漂移问题（多列、`@indent`、PDF 导入会改变 markdown 行数，导致预览同步定位偏移）

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
- 表格标题行可用 `Table<auto|zebra|nozebra>:` 选择斑马纹策略，默认 `auto`：按条带着色，跨行合并块整块同色，交错合并自动传递

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

    enableParser = true;  # 图片控制语法 / 表格合并 / 多列 / 标题编号等
    cssFallbackFeatures = [ "r" "i" ];  # 纯 CSS 回退覆盖的布局/效果 token（enableParser = false 时生效，可选）
    enableHeader = true;  # head.html 注入
    expandDetail = true;  # 打印时自动展开 <details>（需 enableHeader）

    # 推荐显式指定扩展目录，避免运行时去 ~/.vscode/extensions 匹配
    extensionDir = "${pkgs.vscode-extensions.shd101wyy.markdown-preview-enhanced}/share/vscode/extensions/shd101wyy.markdown-preview-enhanced";
  };
}
```

其余选项（`autoCount`、`headingUnderline`、`enableTableCaption` 等）与第 3 节的 CLI 参数一一对应。

PATH 中会安装 `mdcss-bridge` 命令——它就是 `mdcss.py`，只是把模块配置烘焙为默认参数（nix 安装方式下不存在 `config/config.json`，默认值即来源于此）；额外传入的 CLI 参数按 argparse 语义后出现者覆盖烘焙默认值：

```bash
mdcss-bridge  # 重新生成并热更新 crossnote 配置
mdcss-bridge --emit-inkstone ~/inkstone  # 生成 inkstone 桥接产物
```

部署方式说明：

- 构建产物 `style.less` / `parser.js` / `head.html` / `fonts/` 由 oneshot 服务 `mdcss-deploy.service` 在登录时以普通可写文件部署到 crossnote 的配置目录。
- 部署目标与 MPE 扩展自身的解析逻辑一致：设置了 `XDG_CONFIG_HOME` 时为 `$XDG_CONFIG_HOME/crossnote`，否则为 `~/.local/state/crossnote`。注意扩展在 Linux 下**不会**读取 `~/.config/crossnote`（除非通过 `XDG_CONFIG_HOME` 指过去）。
- 扩展会在同一目录维护自己的 `config.js`（katex/mathjax/mermaid 等设置），部署脚本只替换上述四个受管条目，不会触碰它；也因此不能使用指向 nix store 的只读符号链接（`xdg.configFile`）来部署。

## 6. inkstone 桥接

> [!TIP]
> mdcss 可以为 [inkstone](https://github.com/shuaiplus/inkstone) 生成同一套语法扩展的桥接产物
>
> 如果需要该功能，直接使用 [fork](https://github.com/suif4599/inkstone.git) 的 `mdcss-bridge` 分支
>
> 该分支跟随上游通过 `rebase` 更新

```bash
python mdcss.py --emit-inkstone <inkstone-repo>
```

产物：

| 文件 | 落点 | 内容 |
| --- | --- | --- |
| `mdcss-bridge.js` | `src/client/lib/markdown/` | ESM 模块，导出 `mdcssPre(source)` / `mdcssPost(html)`，由 inkstone 的 `renderMarkdown` 在 markdown-it 渲染前后调用 |
| `mdcss-runtime.js`（+ `mdcss-runtime.d.ts`） | `src/client/lib/markdown/` | 自启动运行时脚本（head.html 的桥接对应物，目前含 I/M canvas 处理器）：初始扫描 + MutationObserver 自观察，inkstone 侧经副作用导入加载一次，覆盖预览/分享等全部渲染面；处理结果按「效果+阈值+原图 URL」LRU 缓存（inkstone 预览每次防抖重渲都会重建 `<img>`） |
| `mdcss.css` | `src/client/styles/` | 可移植的排版 CSS（`.ink-prose` 作用域），在 `app.css` 中 `@import` |

与 MPE 输出的差异：

- 图片效果统一改为跟随浏览器主题：仅 `:root[data-theme='dark']` 下生效（MPE 中是「预览生效、`@media print` 重置」）。其中 `i` 反相 / `m` 去背景由 CSS 规则门控；`I` 亮度反转 / `M` 亮部抠图为运行时 canvas 效果，由 `mdcss-runtime.js` 在渲染后的 DOM 上处理，切回浅色主题时自动还原为原图。
- 行号账本（`data-source-line` 重映射）移植为 inkstone 的 `data-line` 属性名。
- 不桥接：字体、打印/导出样式、主题 CSS、head.html 的其余脚本（如 expand_detail）、`@import` PDF、uri 双重编码修复
