# MdCSS：Beyond Markdown

**目录**：

- [1. 功能一览](#1-功能一览)
- [2. 使用示例](#2-使用示例)
- [3. 参数说明](#3-参数说明)
- [4. 文档](#4-文档)
- [5. 在 nix 中使用](#5-在nix中使用)
- [6. inkstone 桥接](#6-inkstone-桥接)

这是一个增强 VS Code 的 Markdown Preview Enhanced (MPE) 插件功能的脚本，旨在扩展 Markdown 文件的排版能力，让相对轻量的排版需求不必使用 $\LaTeX$。

脚本生成的配置文件允许为 PDF 导出设置单独的主题，同时实现了图片的排版增强、表格的合并单元格、自定义字体、自定义页边距等功能。

注意，脚本提供的部分功能必须使用 **Chrome (Puppeteer)** 才能生效

**部署生效说明**（parser.js / style.less / head.html）：

- MPE 以工作区 `.crossnote/` 中的文件**优先于**全局配置目录（`~/.local/state/crossnote`）：若工作区存在 `.crossnote/parser.js`，部署到全局的版本会被遮蔽、不生效
- MPE 仅在预览引擎初始化时读取 parser.js，重新生成后需执行 `Developer: Reload Window` 才能在预览 / Open in Browser 中生效

## 1. 功能一览

若想获得可视化的说明，请参阅 [GitHub Pages](https://suif4599.github.io/mdcss/) 与[演示文档](docs/DEMO.md)。

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

## 4. 文档

- **[GitHub Pages](https://suif4599.github.io/mdcss/)**：语法参考与效果演示——由 [docs/DEMO.md](docs/DEMO.md) 经完整渲染管线自动生成（真实 CSS 与 canvas 运行时，`I`/`M` 等效果在线即可运行），推送到 main 后由 [Pages 工作流](.github/workflows/pages.yml) 自动构建部署
- **[演示文档](docs/DEMO.md)**：同一源文档——安装并启用 `--enable-parser` 后用 MPE 预览它，即可逐项体验全部特性

本地预览站点：`pixi run site` 后打开 `site/index.html`（`site/` 为构建产物，不入库；生成器在 [tools/gen_site.py](tools/gen_site.py)）。`wiki/` 子模块仅保留指向 Pages 的跳转页。

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
