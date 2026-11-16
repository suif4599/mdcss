# MdCSS 参数

## 参数来源

生效值按下面的优先级合并：命令行参数 > `config/config.json` > 内置默认值

> 可使用 `--save-config` 将本次**生效值**写回 `config/config.json`
> Flake 方式安装的 MdCSS 没有 `config.json`，取而代之的是 Option，详见[文档](./FLAKE.md)

> MPE 会把编译后的 `~/.crossnote/style.less` 随预览服务一起缓存：重新生成后必须**重启预览服务**才生效——关闭预览再重新 "Open in Browser"（必要时重启 VS Code），只刷新页面或重新打印读到的仍是旧样式

## 参数列表

### 主题与字体

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--main-css` | 不可省略 | 正文打印主题 CSS，相对路径在 `<extension-dir>/crossnote/styles/` 中搜索 |
| `--codeblock-css` | 不可省略 | 代码块打印主题 CSS，相对路径同上 |
| `--font` | `None` | 正文字体文件路径（`.ttf`/`.otf`/`.woff`/`.woff2`/`.ttc`/`.otc`）或字体族名称；给路径时自动解析同目录下的同族变体 |
| `--code-font` | `None` | 代码块字体，语义同 `--font` |
| `--font-size` | `16px` | 基础字号，预览与打印一致（打印时在 `@media print` 中显式固定），不建议调整 |
| `--print-margin` | `5mm` | 打印边距，写入 `@page { margin }`，如 `2cm`、`20mm 10mm`。打印对话框需保持默认边距，手动设置的边距会覆盖它 |

字体名称的解析方式：Linux 走 fontconfig，Windows 走字体注册表与系统字体目录

### 功能配置

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--enable-parser` | Off | 启用 parser.js 增强功能：图片控制串、表格合并、多列、标题编号、段落缩进等，并自动向 head.html 注入 `I`/`M` 运行时处理器 |
| `--enable-table-caption` / `--no-enable-table-caption` | 开 | 是否把 `Table: ...` 渲染为编号表标题 |
| `--enable-table-horizontal-scroll` | Off | 允许宽表格水平滚动 |
| `--auto-count` | `none, chinese, number, number, latin, roman` | 标题编号样式，逗号分隔的 6 个值对应 h1–h6；支持 `number`/`latin`/`latinUpper`/`roman`/`romanUpper`/`chinese`/`none` |
| `--heading-underline` | Off | 需要加下划线的标题级别，如 `"1,2"` 表示 h1 与 h2 |
| `--css-fallback-features` | 空 | 未启用 `--enable-parser` 下额外支持的布局 / 效果，逗号分隔：`r`/`L`/`R`/`Lf`/`Rf`/`i`/`m`，建议启动 parser |
| `--invert-bounds` | `32,239` | `I` 效果的默认亮度阈值 `lo,hi`：低于 `lo` 或高于 `hi` 的像素亮度互换 |
| `--matte-bounds` | `64,239` | `M` 效果的默认亮度阈值 `lo,hi`：低于 `lo` 的像素提亮、高于 `hi` 的像素透明 |

### 运维

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--output` | `~/.local/state/crossnote` | 输出目录（`style.less` / `parser.js` / `head.html` / `fonts/`）。**Windows 上 MPE 实际读取 `%USERPROFILE%\.crossnote`，请显式指定**，见 [README 的说明](../README.md#2-自定义配置文件) |
| `--extensions-root` | `~/.vscode/extensions` | VS Code 扩展根目录 |
| `--extension-pattern` | `shd101wyy.markdown-preview-enhanced-*` | 匹配 MPE 扩展目录的 glob |
| `--extension-dir` | `None` | 显式指定扩展目录（覆盖上面两个参数），nix 构建等读不到 `~/.vscode/extensions` 的场景需要 |
| `--yes` | 关 | 跳过所有确认提示 |
| `--save-config` | 关 | 把生效参数写回 `config/config.json` |
| `--emit-inkstone` | `None` | 生成 inkstone 桥接产物到指定仓库路径后退出，复用 `--auto-count` 与 `--enable-table-caption`。见 [inkstone 桥接](inkstone.md) |
