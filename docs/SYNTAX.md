# MdCSS 语法文档

本文是 MdCSS 的语法文档，本身使用 MdCSS 扩展语法编写，推荐使用 [GitHub Pages](https://suif4599.github.io/mdcss/) 或者安装本项目后使用 Markdown Preview Enhanced 拓展进行浏览

## .图片

### .语法总览

> 控制串的完整解析需要 `--enable-parser`，纯 CSS 模式的降级行为见下方 NOTE 与「语法速查」

图片默认语法为：

```markdown
![alt](src)
```

MdCSS 将其扩展为：

```markdown
![control|caption|alt](src)
```

用 `|` 分隔为三段，可以省略 alt 或者同时省略 alt 和 caption

| 段 | 名称 | 说明 |
| :---: | :---: | :---: |
| 1 | `control` | 控制串，按顺序组合宽度、布局字母、效果字母 |
| 2 | `caption` | 图标题，需 `--enable-parser` |
| 3 | `alt` | 真实无障碍文本 |

**控制串规则**：

- 宽度为 1–4 位数字，可带单位：
  - `%`：默认单位，封顶 100
  - `px`：不封顶
- 宽度后可继续添加布局字母和效果字母
- 控制串可以整体留空，此时只写图注或 alt

> [!NOTE]
> 未启用 `--enable-parser` 的纯 CSS 模式下：
>
> - 带 `%` 的宽度始终生效
> - 布局/效果字母需通过 `--css-fallback-features` 显式启用，规则按前缀精确匹配生成，不会误伤真实 alt
> - `px` 宽度、无单位宽度、图标题为 parser 专属

> [!NOTE]
> 为了与标准 markdown 尽可能兼容，当只提供一段 alt 且无法匹配控制串语法时，解析器将其作为 alt text 原样输出
> 这是兼容性设计，不建议使用这种方式书写 alt

### .宽度

> 带 `%` 的宽度为纯 CSS 功能；`px` 与无单位宽度需要 parser

> 标准 markdown 会将图片宽度设置为 100%，这导致在插入纵向图片时排版效果糟糕
> MdCSS 提供简洁的语法控制图片宽度

代码：

`![25%i|.这是宽度25%的图片](./assets/image.jpeg)`

效果：

![25%i|.这是宽度25%的图片](./assets/image.jpeg)

代码：

`![100pxi|.这是宽度100px的图片](./assets/image.jpeg)`

效果：

![100pxi|.这是宽度100px的图片](./assets/image.jpeg)

### .效果

> `i`/`m` 为 CSS 滤镜：需要 parser 应用类（纯 CSS 模式可经 `--css-fallback-features` 回退），预览中生效；`I`/`M` 需要 parser 与 head.html 运行时脚本（随 `--enable-parser` 自动注入，见下方 NOTE）

> 标准 markdown 对暗色党不太友好，若是插入深色图表，那么导出成亮色 PDF 时会极其丑陋，若是插入浅色图表，则在预览时与环境格格不入
> MdCSS 提供了四种图片效果，用来解决这个问题
> - `i`/`m` 为 CSS 滤镜，在预览中生效，导出/打印时自动还原为原图
> - `I`/`M` 为运行时 canvas 效果，在 MPE 预览中始终应用；在 inkstone 桥接与 GitHub Pages 站点中仅在深色主题下生效，切回浅色主题自动还原为原图

在控制串中添加效果字母 `iImM` 来实现特殊效果：

| 字母 | 作用 | 说明 |
| :--: | :---: | --- |
| `i` | 反相 | / |
| `I`/`I(下界,上界)` | 亮度两端互换 | 实验性功能<br>需 `--enable-parser`<br>及 head.html 运行时脚本 |
| `m` | 去除背景 | 实验性功能 |
| `M`/`M(下界,上界)` | 亮部抠图＋暗部提亮 | 实验性功能<br>需 `--enable-parser`<br>及 head.html 运行时脚本 |

`I` 与 `M` 可以指定生效阈值：`I` 互换亮度低于下界或高于上界的像素，`M` 提亮低于下界的像素、将高于上界的像素设为透明。省略时使用全局默认（`I` 为 32,239，`M` 为 64,239），可通过 `--invert-bounds` / `--matte-bounds` 配置默认值

> [!NOTE]
> `I`/`M` 由 head.html 中的运行时 canvas 处理器（随 `--enable-parser` 自动注入）在图片原始分辨率上逐像素完成；若图片因跨域限制无法读取像素，则保持原样
> crossnote 自 0.9.31 起在预览与导出中剥离 head.html 的脚本，但 0.9.36 之前对仅含脚本的 head.html 存在空回退漏洞，剥离并未实际生效——MPE 0.8.30 至 0.8.35（含 nixpkgs 当前版本）中 `I`/`M` 正常工作；MPE 0.8.36 起内联脚本被真正剥除，`I`/`M` 在 MPE 预览与导出中失效，仅 inkstone 桥接与 GitHub Pages 站点不受影响

> [!NOTE]
> 在几乎所有情况下，都推荐仅使用 `i` 作为效果器，其余效果器是为对色相有特殊要求的图表设计的（比如热力图）

代码：

`![19%r|.原图](./assets/colorwheel.png) ![19%ri|.反相（实验性）](./assets/colorwheel.png) ![19%rI|.亮度两端互换（实验性）](./assets/colorwheel.png) ![19%rm|.去除背景（实验性）](./assets/colorwheel.png) ![19%rM|.亮部抠图＋暗部提亮（实验性）](./assets/colorwheel.png)`

效果（请开启深色模式）：

![19%r|.原图](./assets/colorwheel.png) ![19%ri|.反相（实验性）](./assets/colorwheel.png) ![19%rI|.亮度两端互换（实验性）](./assets/colorwheel.png) ![19%rm|.去除背景（实验性）](./assets/colorwheel.png) ![19%rM|.亮部抠图＋暗部提亮（实验性）](./assets/colorwheel.png)


### .布局

> 布局字母需要 parser 应用类；纯 CSS 模式可经 `--css-fallback-features` 为 `r`/`L`/`R`/`Lf`/`Rf` 生成回退规则

#### .单行多图

在控制串中添加 `r` 来将多张图片排在同一行

代码：

`![25%ri](./assets/image.jpeg) ![25%ri](./assets/image.jpeg) ![25%ri](./assets/image.jpeg)`

效果：

![25%ri](./assets/image.jpeg) ![25%ri](./assets/image.jpeg) ![25%ri](./assets/image.jpeg)

`r` 可以与其他效果字母组合使用

多行多图只需重复多组 `r`，每行一组：

代码：

```markdown
![40%ri](./assets/image.jpeg) ![40%ri](./assets/image.jpeg)
![40%ri](./assets/image.jpeg) ![25%ri](./assets/image.jpeg)
```

效果：

![40%ri](./assets/image.jpeg) ![40%ri](./assets/image.jpeg)
![40%ri](./assets/image.jpeg) ![25%ri](./assets/image.jpeg)

#### .左右对齐

在控制串中添加 `L/R` 来强迫图片向左/右对齐

代码：

`![30%Ri|.这是靠右对齐的图片](./assets/image.jpeg)`

效果：

![30%Ri|.这是靠右对齐的图片](./assets/image.jpeg)

#### .浮动排版

在控制串中添加 `f` 来启用浮动排版，`f` 必须与 `L/R` 连用，写作 `Lf`/`Rf`

> [!WARNING]
> 浮动排版在多列排版中会失效！

代码：

```markdown
![40%Lfi|.文字环绕图片](./assets/image.jpeg)
啊啊啊啊啊宝宝你是一个……
```

效果：

![40%Lfi|.这是被文字环绕的图片](./assets/image.jpeg)
啊啊啊啊啊啊宝宝你是一个香香软软甜甜糯糯蜂蜜奶油甜甜腻腻酥酥脆脆滑滑嫩嫩绵绵密密弹弹润润丝丝滑滑蓬蓬松松香香甜甜油油润润细细软软密密实实润润甜甜酥酥软软嫩嫩滑滑松松软软甜甜蜜蜜细细绵绵香香浓浓弹弹嫩嫩香香甜甜酸酸甜甜辣辣爽爽咸咸鲜鲜苦苦甘甘滑滑嫩嫩酥酥脆脆软软绵绵弹弹润润油油腻腻清清爽爽浓浓醇醇淡淡幽幽热热乎乎冰冰凉凉黏黏糊糊爽爽脆脆鲜鲜嫩嫩辣辣麻苦苦辣辣酱油醋橄榄油菜籽油葵花籽油鱼虾蟹龙虾贝类牛肉羊肉猪肉鸡肉鸭肉鹅肉火鸡肉香肠火腿培根肉丸汉堡热狗披萨寿司拉面咖喱炖肉烤肉烤鱼烤鸡沙拉汤粥芒果柠檬柚子百香果茼蒿芥蓝芹菜荠菜苋菜意式烤蔬菜配香草酱和橄榄油鲜美多汁香脆可口滑嫩浓郁醇厚甘甜爽口香辣酸甜苦辣咸香酥软糯滑爽劲道鲜美清香扑鼻诱人色泽鲜艳香气扑鼻口感丰富层次分明风味独特香气四溢回味无穷色香味俱佳口感细腻肉质鲜嫩色泽金黄外酥里嫩香气浓郁味道鲜美口感滑嫩味道醇厚味道独特风味独特香气诱人口感鲜美味道浓郁口感丰富味道鲜美味道醇厚味道独特香气扑鼻口感细腻肉质鲜嫩色泽金黄外酥里嫩香气浓郁味道鲜美口感滑嫩味道醇厚味道独特风味独特香气诱人口感鲜美味道浓郁口感丰富味道鲜美味道醇厚味道独特香气扑鼻的小蛋糕

### .图标题

> 需要 parser；MPE 与 inkstone 桥接均支持

当 `--enable-parser` 启用时，在第二个 `|` 分隔段写图注，前导 `.` 会被替换成递增的 `图N:`。第三个分隔段为真实 alt

对于 `r` 样式的多图布局：
- **子图标题**开头的 `.` 会被替换成 `(a)(b)(c)` 递增字母编号（按组内顺序，每组从 `(a)` 重新开始），**不占用全局图号**
- **整体标题**（写在第一个子图的图注 `(.总标题)` 中）开头的 `.` 仍使用 `图N:` 全局编号

例如：`![40%ri|.子图A(.总标题)](./assets/image.jpeg) ![25%ri|.子图B](./assets/image.jpeg)`

效果

![40%ri|.子图A(.总标题)](./assets/image.jpeg) ![25%ri|.子图B](./assets/image.jpeg)

## .表格

### .合并单元格

> 需要 parser；MPE 与 inkstone 桥接均支持

> 标准 markdown 不提供合并单元格这个十分实用的功能
> MdCSS 提供了这个功能

- 使用 `\` 删除单元格（包括标题）
- 使用 `c\d` 和 `r\d` 的前缀来表示合并单元格
- 使用 `:` 为单元格单独设置对齐
- 使用 `\\` 输入一个反斜杠（单个 `\` 是删除单元格；N ≥ 2 个连续反斜杠渲染为 N−1 个）

代码：

```markdown
| c2: 标题1 | \ | 标题2 | 标题3 |
| --- | --- | --- | --- |
| 文本1 | :c2: 文本2 | \ | \\ |
| r2 文本3 | 文本4 | :r2c2: 文本5 | \ |
| \ | 文本6 | \ | \ |
```

效果：

| c2: 标题1 | \ | 标题2 | 标题3 |
| --- | --- | --- | --- |
| 文本1 | :c2: 文本2 | \ | \\ |
| r2 文本3 | 文本4 | :r2c2: 文本5 | \ |
| \ | 文本6 | \ | \ |

### .表标题

> 需要 parser；受 `--enable-table-caption` 控制（默认开启）

在表格前添加一行表格标题，支持类似图片的格式自动添加编号

|||-

```markdown
Table: .这是一个表格

| 第 1 列 | 第 2 列 |
| --- | --- |
| 这是小明 | 和小红 |
```

|||

Table: .这是一个表格

| 第 1 列 | 第 2 列 |
| --- | --- |
| 这是小明 | 和小红 |

-|||

### .斑马纹

> 基础斑马纹为纯 CSS；`Table<auto|zebra|nozebra>` 策略标签与跨行合并感知需要 parser

表格默认应用斑马纹，便于确认表格的行，斑马纹有 `auto`, `zebra`,`nozebra` 三个策略

默认策略为 `auto`，该策略会应用斑马纹，并自动处理跨行单元格；`zebra` 会强制应用斑马纹而无视跨行合并；`nozebra` 会禁用斑马纹

|||-

```markdown
Table<nozebra>: .无斑马纹的表格

| 第 1 列 | 第 2 列 |
| --- | --- |
| 这是小明 | 和小红 |
| 这是小红 | 和小明 |
```

|||

Table<nozebra>: .无斑马纹的表格

| 第 1 列 | 第 2 列 |
| --- | --- |
| 这是小明 | 和小红 |
| 这是小红 | 和小明 |

-|||

## .文档

### .多列布局

> 需要 parser；`!` 主列标记的滚动同步仅在 MPE 中生效

使用 `|||-` 来开始多列排版，`|||` 来分隔列，`-|||` 来结束

> [!TIP]
> 使用 `::` 要求其在竖直方向上居中对齐
> 还可以使用数字来指定列宽，不提供时默认平均分配
> 比如 `:240px` 表示列宽 240px 且向上对齐
> 比如 `:50%:` 表示列宽 50% 且居中对齐，`%` 也可以省略
> 此外，单独的 `:` 表示向下对齐
> 在列参数末尾追加 `!` 可以把该列标记为主列，比如 `|||60!` 表示该列列宽 60% 且为主列，未标记时默认第一列为主列
> 主列用于控制双窗口预览的滚动同步：编辑其他列的内容时预览保持不动，编辑到主列的内容时预览才跟随滚动

代码：

```markdown
|||-40

![40%ri|.竖直居中的图片](./assets/image.jpeg) ![40%ri](./assets/image.jpeg)

|||

> [!TIP]
> 这是一个 tip 的 Callout

-|||
```

|||-40

![40%ri|.竖直居中的图片](./assets/image.jpeg) ![40%ri](./assets/image.jpeg)

|||

> [!TIP]
> 这是一个 tip 的 Callout

-|||

### .自动标题编号

> 需要 parser；MPE 与 inkstone 桥接均支持

在标题前加上 `.`，例如 `## .这是我的二级标题`，开头的 `.` 会被替换为编号

|||-

代码：

`#### .这是我的四级标题`

|||

效果（仅示意）：

#### 1.1 这是我的四级标题

-|||

自动标题编号功能支持多种编号格式，通过 `--auto-count` 参数设置，用逗号分隔 6 个值对应 h1–h6：

Table: .编号样式

| 样式 | 输出示例 |
| :---: | --- |
| `number` | `1.`, `2.`, `3.`，连续使用时可生成 `1.1.`, `1.2.` |
| `latin` | `a)`, `b)`, `c)` |
| `latinUpper` | `A)`, `B)`, `C)` |
| `roman` | `i)`, `ii)`, `iii)`（上限 3999） |
| `romanUpper` | `I)`, `II)`, `III)`（上限 3999） |
| `chinese` | `一、`, `二、`, `三、` |
| `none` | 不编号 |

默认值：`none, chinese, number, number, latin, roman`（即 h1 不编号，h2 中文数字，h3–h4 阿拉伯数字，h5–h6 小写拉丁/罗马）

### .段落缩进

> 需要 parser；MPE 与 inkstone 桥接均支持

在文档开头添加 `@indent` 或 `<indent>` 来为该文档启用段落缩进

|||-

代码：

```markdown
@indent

正文内容……
```

|||

效果：

首行自动缩进两个字符

-|||

## .错误修复

MPE 存在许多零碎的错误，MdCSS 修复了它们

### .非 ASCII 文件名

> 需要 parser，仅 MPE；只影响「Open in Browser」与导出 HTML，预览不受影响

MPE 的「Open in Browser」/ 导出 HTML 会对含非 ASCII 字符（如中文）的本地图片路径二次 URL 编码，导致浏览器中图片 404。`--enable-parser` 启用时，parser 会自动将 `src` 中的双重编码还原一次，无需手动处理。注意：文件名本身含字面 `%` 的场景无法还原，建议图片文件使用 ASCII 文件名

### .PDF 导入居中

> 需要 parser，仅 MPE；需安装 pdf2svg

MPE 的 `@import` 导入的 PDF 不会居中显示，MdCSS 修复了这个错误（当 `--enable-parser` 启用时生效）

> [!NOTE]
> 需要安装 pdf2svg 工具且能在 PATH 中找到

### .基础字号

> 纯 CSS；`--font-size` 参数，预览与导出均生效

在部分情况下 MPE 导出的表格会通过缩小字体而不是换行来应对单元格过宽的情况，这会导致渲染效果不稳定，强制应用基础字号可以缓解该问题

使用 `--font-size` 参数设置文档基础字号（默认 16px）

示例：

```bash
pixi run python mdcss.py --font-size 12px --main-css preview_theme/github-light.css --codeblock-css prism_theme/github.css
```

### .代码行数

> 纯 CSS；排版修复仅打印/导出生效（`{.line-numbers}` 语法本身为 MPE 内置）

MPE 支持在语言后添加 `{.line-numbers}` 来显示行号，但会出现行号与代码块错位的 bug，MdCSS 修复了这个问题

示例代码：

````plaintext
```javascript {.line-numbers}
function add(x, y) {
  return x + y
}
```
````

### .长代码排版

> 纯 CSS；仅打印/导出生效

MPE 导出的 PDF 倾向于不让代码块换页，这会导致大量的页内空白，MdCSS 修复了这个问题，代码块不再会另起一页，而是直接跟随上一页

## .语法速查

本章按「启用开关」汇总全部功能，便于快速查询。开关均由生成器（`mdcss.py` / `mdcss-bridge`）控制，详见 README 的参数说明：`--enable-parser` 生成 parser.js（markdown 渲染前后处理管线）与 head.html（`I`/`M` 运行时脚本），`--css-fallback-features` 在纯 CSS 模式下为指定 token 生成回退规则。各语法章节开头的引用块也标注了对应要求

### .纯 CSS

无需开关，部署 style.less 即生效：

- 图片 `%` 宽度（1–100，封顶 100）
- 表格基础斑马纹与表头底色
- 表格自动列宽与防横向滚动（`--enable-table-horizontal-scroll` 可改回滚动）
- 基础字号（`--font-size`）
- 标题下划线（`--heading-underline`）
- 代码行号排版修复（仅打印）
- 长代码不另起一页（仅打印）
- Callout 打印不跨页（仅打印）
- 打印展开折叠 Callout（仅打印，Chromium 131+，旧引擎保持折叠）

纯 CSS 模式（未启用 parser）下，还可通过 `--css-fallback-features` 为布局字母 `r`/`L`/`R`/`Lf`/`Rf` 与效果字母 `i`/`m` 生成回退规则（规则数随 token 组合增长，超过 200 条时需 `--yes` 确认）

### .需要 parser

启用 `--enable-parser` 后生效（MPE 与 inkstone 桥接均支持）：

- 图片控制串完整解析（`px` 与无单位宽度、布局/效果字母的类应用）
- 图标题（`图N:` 编号、`(a)(b)(c)` 子图编号、`(.总标题)` 整体标题）
- 表格合并单元格（`\` 删除、`c\d`/`r\d` 合并、`:` 对齐、`\\` 字面反斜杠）
- 表标题（`Table:`，受 `--enable-table-caption` 控制，默认开启）
- 斑马纹策略标签（`Table<auto|zebra|nozebra>`）与跨行合并感知
- 多列布局（`|||-`/`|||`/`-|||`）
- 自动标题编号（标题前缀 `.`，`--auto-count` 配置样式）
- 段落缩进（`@indent`/`<indent>`）
- `I`/`M` 图片效果（canvas 运行时随 `--enable-parser` 自动写入 head.html；MPE 0.8.36 起受脚本剥离影响，见下方 NOTE）

> [!NOTE]
> MPE 0.8.36 起内联脚本被真正剥除，`I`/`M` 在 MPE 预览与导出中失效，仅 inkstone 桥接与 GitHub Pages 站点不受影响

### .MPE 专有

以下功能仅在与 MPE（crossnote）配合时存在：

- 非 ASCII 文件名修复（`--enable-parser`，仅影响「Open in Browser」与导出 HTML）
- PDF `@import` 居中（`--enable-parser`，需 PATH 中有 pdf2svg）
- 多列 `!` 主列标记的滚动同步（双窗口预览跟随主列滚动）
- 字体、打印/导出样式与主题 CSS（inkstone 不桥接）

### .inkstone 专有

没有专有语法，桥接产物覆盖与 MPE 相同的语法集，仅行为有差异：

- 四种图片效果均跟随浏览器主题，仅在深色主题下生效，切回浅色主题自动还原原图（MPE 中 `i`/`m` 预览生效、导出还原，`I`/`M` 见「需要 parser」）
- 列布局的内联样式经 `data-*` 属性在 DOMPurify 净化后重建

不桥接的部分：字体、打印/导出样式、主题 CSS、`@import` PDF、非 ASCII 文件名修复、主列滚动同步

### .仅在导出时生效

以下效果只在打印/导出（PDF、HTML）中出现，预览中无感：

- 代码行号排版修复
- 长代码不另起一页
- Callout 打印不跨页
- 表格打印配色（固定浅灰实色）
- `i`/`m` 效果还原为原图
- 打印展开折叠 Callout
- 非 ASCII 文件名修复（只影响「Open in Browser」与导出 HTML，预览本身不受影响）
