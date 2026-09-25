# MdCSS：Beyond Markdown

增强 VS Code [Markdown Preview Enhanced](https://github.com/shd101wyy/vscode-markdown-preview-enhanced) (MPE) 的排版能力：在不动 markdown-it 的前提下，用前后处理管线为 Markdown 加上图片排版、表格合并、多列布局、标题编号等扩展——让相对轻量的排版需求不必动用 $\LaTeX$。

**文档**：[Wiki](https://github.com/suif4599/mdcss/wiki)（安装、完整参数、Nix 集成、inkstone 桥接） · [语法预览（GitHub Pages）](https://suif4599.github.io/mdcss/)（语法展示的在线渲染） · [语法文档](docs/SYNTAX.md)

## 功能一览

| 类别 | 功能 |
| --- | --- |
| **图片** | 宽度控制（百分比/px）、单行多图、对齐、文字环绕、反相、亮度两端互换（可调阈值）、亮部抠图＋暗部提亮（可调阈值）、去背景、图片标题 |
| **表格** | 合并单元格、删除单元格、跨页重复标题、表格标题、自动列宽、间行深浅背景色（预览+打印） |
| **多列排版** | 多列布局、列宽控制（百分比/px）、竖直对齐（上/中/下）、主列标记（滚动同步） |
| **标题编号** | 多级编号、6 种样式（数字/拉丁/罗马/中文等）、可配置各级格式 |
| **代码行数** | 语言种类后添加 `{.line-numbers}` 启用行号 |
| **Callout** | 支持展开/嵌套、多种样式（abstract/tip/warning 等） |
| **排版** | 段落缩进、代码块不断页 |
| **PDF** | 导入 PDF 居中显示 |

## 快速开始

需要 [pixi](https://pixi.sh) 与 MPE 插件：

```bash
git clone https://github.com/suif4599/mdcss.git
cd mdcss
cp config/config.example.json config/config.json   # 按需修改主题与字体
pixi run python mdcss.py --enable-parser --enable-header
```

生成后执行 `Developer: Reload Window` 使预览生效；NixOS / Home Manager 集成、全部参数、部署机制与排障见 [Wiki](https://github.com/suif4599/mdcss/wiki)。mdcss 也可为 [inkstone](https://github.com/shuaiplus/inkstone) 生成同一套语法扩展的桥接产物，详见 [Wiki 的 inkstone 页](https://github.com/suif4599/mdcss/wiki/Inkstone-Bridge)。

## 更多

- 语法文档 `docs/SYNTAX.md` 用 MdCSS 扩展语法写成，安装后用 MPE 预览即可逐项体验；其在线渲染版即 [GitHub Pages](https://suif4599.github.io/mdcss/) 站点（仅语法预览，深浅色跟随主题）。
- 其余文档（安装、参数、Nix 集成、inkstone 桥接）都在 [Wiki](https://github.com/suif4599/mdcss/wiki)。

## License

[MIT](LICENSE)
