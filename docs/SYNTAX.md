# Syntax for MdCSS

可视化 Markdown 新增语法汇总。

**目录**：

- [1. 图片](#1-图片)
  - [图片宽度设置](#图片宽度设置)
  - [图片效果](#图片效果)
  - [单行多图布局](#单行多图布局)
  - [图片左右对齐](#图片左右对齐)
  - [浮动排版](#浮动排版)
  - [图片标题](#图片标题)
- [2. 表格](#2-表格)
  - [单元格合并与删除](#单元格合并与删除)
  - [跨页重复标题](#跨页重复标题)
  - [表格标题](#表格标题)
  - [自动列宽](#自动列宽)
- [3. 多列排版](#3-多列排版)
- [4. 标题标号](#4-标题标号)
- [5. 代码行数](#5-代码行数)
- [6. Callout](#6-callout不是新加的但很有用)
- [7. 长代码排版](#7-长代码排版)
- [8. 段落缩进](#8-段落缩进)
- [9. PDF 导入居中](#9-pdf-导入居中)

## 1. 图片

将默认语法 `![alt](src)` 扩展为 `![control|caption|alt](src)`，以 `|` 分隔为三段，后两段可整体省略：

- `control`：控制串，按顺序组合 宽度（1-4 位数字 + 可选单位 `%`（默认，封顶 100）/ `px`（不封顶））+ 布局字母 + 效果字母；也可整体留空（仅图注/alt）
- `caption`：图注（需 `--enable-parser`），前导 `.` 会被替换成递增的 `图N:`
- `alt`：真实替代文本，从第三个 `|` 起的所有内容都属于它（可以包含 `|`）；输出 HTML 的 `alt=` 依次取真实 alt、图注文本、空串，控制串不会出现在输出中

第一段（无 `|` 时取整段）不匹配控制语法且非空时，整段 alt 视为真实替代文本，不触发任何控制语法——英文 alt（如 `![An English alt](src)`）完全安全。注意表格单元格内的 `|` 需转义为 `\|`，纯数字 alt（如 `2023`）会被当作宽度。

> [!NOTE]
> 未启用 `--enable-parser` 的纯 CSS 模式下：带 `%` 的宽度始终生效；布局/效果字母需通过 `--css-fallback-features` 显式启用（规则按前缀精确匹配生成，不会误伤真实 alt）；`px` 宽度、无单位宽度、图注为 parser 专属。

### 图片宽度设置

代码：

`![25%|.这是宽度25%的图片](./assets/image.jpeg)`

效果：

![25%|.这是宽度25%的图片](./assets/image.jpeg)

代码：

`![100px|.这是宽度100px的图片](./assets/image.jpeg)`

效果：

![100px|.这是宽度100px的图片](./assets/image.jpeg)

### 图片效果

在控制串中添加字母来实现特殊效果：

| 字母 | 作用 | 生效时机 |
| :--: | :---: | ------- |
| `r` | 单行多图布局 | 始终生效（纯 CSS 模式需配置回退） |
| `L` / `R` | 左对齐 / 右对齐 | 始终生效（纯 CSS 模式需配置回退） |
| `Lf` / `Rf` | 文字环绕 | 始终生效（纯 CSS 模式需配置回退） |
| `i` | 反相 | 预览时（纯 CSS 模式需配置回退） |
| `I` | 亮度反转（实验性） | 需 `--enable-parser` |
| `m` | 去除背景（实验性） | 预览时（纯 CSS 模式需配置回退） |

会在接下来的 2 节中说明。

### 单行多图布局

在控制串中添加 `r` 来将多张图片排在同一行。

代码：

`![25%r](./assets/image.jpeg) ![25%r](./assets/image.jpeg) ![25%r](./assets/image.jpeg)`

效果：

![25%r](./assets/image.jpeg) ![25%r](./assets/image.jpeg) ![25%r](./assets/image.jpeg)

`r` 可以与其他效果字母组合使用：

代码：

`![25%ri|.反相](./assets/image.jpeg) ![25%rI|.反转亮度](./assets/image.jpeg) ![25%rm|.去除背景](./assets/image.jpeg)`

效果：

![25%ri|.反相](./assets/image.jpeg) ![25%rI|.反转亮度（实验性）](./assets/image.jpeg) ![25%rm|.去除背景（实验性）](./assets/image.jpeg)

多行多图只需重复多组 `r`，每行一组：

代码：

```markdown
![40%r](./assets/image.jpeg) ![40%r](./assets/image.jpeg)
![40%r](./assets/image.jpeg) ![25%r](./assets/image.jpeg)
```

效果：

![40%r](./assets/image.jpeg) ![40%r](./assets/image.jpeg)
![40%r](./assets/image.jpeg) ![25%r](./assets/image.jpeg)

### 图片左右对齐

代码：

`![30%R|.这是靠右对齐的图片](./assets/image.jpeg)`

效果：

![30%R|.这是靠右对齐的图片](./assets/image.jpeg)

### 浮动排版

> [!WARNING]
> 浮动排版在多列排版中会失效！

代码：

```markdown
![40%Lf|.文字环绕图片](./assets/image.jpeg)
啊啊啊啊啊宝宝你是一个……
```

效果：

![40%Lf|.这是被文字环绕的图片](./assets/image.jpeg)
啊啊啊啊啊啊宝宝你是一个香香软软甜甜糯糯蜂蜜奶油甜甜腻腻酥酥脆脆滑滑嫩嫩绵绵密密弹弹润润丝丝滑滑蓬蓬松松香香甜甜油油润润细细软软密密实实润润甜甜酥酥软软嫩嫩滑滑松松软软甜甜蜜蜜细细绵绵香香浓浓弹弹嫩嫩香香甜甜酸酸甜甜辣辣爽爽咸咸鲜鲜苦苦甘甘滑滑嫩嫩酥酥脆脆软软绵绵弹弹润润油油腻腻清清爽爽浓浓醇醇淡淡幽幽热热乎乎冰冰凉凉黏黏糊糊爽爽脆脆鲜鲜嫩嫩辣辣麻苦苦辣辣酱油醋橄榄油菜籽油葵花籽油鱼虾蟹龙虾贝类牛肉羊肉猪肉鸡肉鸭肉鹅肉火鸡肉香肠火腿培根肉丸汉堡热狗披萨寿司拉面咖喱炖肉烤肉烤鱼烤鸡沙拉汤粥芒果柠檬柚子百香果茼蒿芥蓝芹菜荠菜苋菜意式烤蔬菜配香草酱和橄榄油鲜美多汁香脆可口滑嫩浓郁醇厚甘甜爽口香辣酸甜苦辣咸香酥软糯滑爽劲道鲜美清香扑鼻诱人色泽鲜艳香气扑鼻口感丰富层次分明风味独特香气四溢回味无穷色香味俱佳口感细腻肉质鲜嫩色泽金黄外酥里嫩香气浓郁味道鲜美口感滑嫩味道醇厚味道独特风味独特香气诱人口感鲜美味道浓郁口感丰富味道鲜美味道醇厚味道独特香气扑鼻口感细腻肉质鲜嫩色泽金黄外酥里嫩香气浓郁味道鲜美口感滑嫩味道醇厚味道独特风味独特香气诱人口感鲜美味道浓郁口感丰富味道鲜美味道醇厚味道独特香气扑鼻的小蛋糕

### 图片标题

当 `--enable-parser` 启用时，在第二个 `|` 分隔段写图注，前导 `.` 会被替换成递增的 `图N:`。第三个分隔段为真实 alt。

对于 `r` 样式的多图布局：
- **子图标题**开头的 `.` 会被替换成 `(a)(b)(c)` 递增字母编号（按组内顺序，每组从 `(a)` 重新开始），**不占用全局图号**；
- **整体标题**（写在第一个子图的图注 `(.总标题)` 中）开头的 `.` 仍使用 `图N:` 全局编号。

例如：`![40%r|.子图A(.总标题)](assets/image.jpeg) ![25%r|.子图B](assets/image.jpeg)`

效果：子图分别显示 `(a) 子图A`、`(b) 子图B`，整体标题显示 `图1: 总标题`。

![40%r|.子图A(.总标题)](assets/image.jpeg) ![25%r|.子图B](assets/image.jpeg)

### 非 ASCII 文件名的路径修复

MPE 的「Open in Browser」/ 导出 HTML 会对含非 ASCII 字符（如中文）的本地图片路径二次 URL 编码，导致浏览器中图片 404。`--enable-parser` 启用时，parser 会自动将 `src` 中的双重编码还原一次，无需手动处理。注意：文件名本身含字面 `%` 的场景无法还原，建议图片文件使用 ASCII 文件名。

## 2. 表格

### 单元格合并与删除

- 使用 `\` 删除单元格（包括标题）；
- 使用 `c\d` 和 `r\d` 的前缀来表示合并单元格；
- 使用 `:` 为单元格单独设置对齐；
- 使用 `\\\` 输入一个反斜杠。

代码：

```markdown
| c2: 标题1 |      \     |     标题2    | 标题3 |
| --------- | ---------- | ------------ | ----- |
|   文本1   | :c2: 文本2 |       \      |  \\\  |
|  r2 文本3 |    文本4   | :r2c2: 文本5 |   \   |
|     \     |    文本6   |       \      |   \   |
```

效果：

| c2: 标题1 |      \     |     标题2    | 标题3 |
| --------- | ---------- | ------------ | ----- |
|   文本1   | :c2: 文本2 |       \      |  \\\  |
|  r2 文本3 |    文本4   | :r2c2: 文本5 |   \   |
|     \     |    文本6   |       \      |   \   |

### 跨页重复标题

启用 `--enable-parser` 后，当表格跨页时，下一页的部分也会重复表格标题栏（不是表格名称）。

类似于：

| 第 1 列 | 第 2 列 |
| --- | --- |
| 这里是第 1 行 | ... |

--- 这里是跨页分割线 ---

| 第 1 列 | 第 2 列 |
| --- | --- |
| 这里是第 2 行 | ... |

### 表格标题

在表格前添加一列表格标题，支持类似图片的格式自动添加编号。

|||-50

代码：

```markdown
Table: .这是一个表格

| 第 1 列 | 第 2 列 |
| --- | --- |
| 这是小明 | 和小红 |
```

|||

效果：

Table: .这是一个表格

| 第 1 列 | 第 2 列 |
| --- | --- |
| 这是小明 | 和小红 |

-|||

### 间行深浅背景色

表格自动应用浅色间行条纹（斑马纹），便于阅读多行表格；表头使用略深一档的背景色以与首行数据区分。预览中颜色为半透明灰色，深浅主题下均适用；打印导出 PDF 时使用对应的浅灰色实色（表头 `#e8e8e8`、间行 `#f2f2f2`），打印友好。

### 自动列宽

根据各列内容自动确定列宽。

### 基础字号

使用 `--font-size` 参数设置文档基础字号（默认 16px）。

**作用**：较小的字号可避免宽表格自动缩小。当表格列数较多、内容较丰富时，浏览器为适应页面宽度会自动缩小字体；设置较小的基础字号可避免此问题。

**示例**：

```bash
python mdcss.py --font-size 12px --main-css preview_theme/github-light.css --codeblock-css prism_theme/github.css
```

## 3. 多列排版

当 `--enable-parser` 启用时生效。

使用 `|||-` 来开始多列排版，`|||` 来分隔列，`-|||` 来结束。

> [!TIP]
> 使用 `::` 要求其在竖直方向上居中对齐
> 还可以使用数字来指定列宽，不提供时默认平均分配
> 比如 `:240px` 表示列宽 240px 且向上对齐
> 比如 `:50%:` 表示列宽 50% 且居中对齐，`%` 也可以省略
> 此外，单独的 `:` 表示向下对齐

|||60

代码：

```markdown
|||-40

![40%r|.竖直居中的图片](./assets/image.jpeg) ![40%r](./assets/image.jpeg)

|||

> [!TIP]
> 这是一个 tip 的 Callout

-|||
```

|||-40

![40%r|.竖直居中的图片](./assets/image.jpeg) ![40%r](./assets/image.jpeg)

|||

> [!TIP]
> 这是一个 tip 的 Callout

-|||

**注**：在多列排版中除了浮动排版的图片外，所有语法均可使用。

## 4. 标题标号

在标题前加上 `.`，例如 `## .这是我的二级标题`，开头的 `.` 会被替换为编号。

|||-50

代码：

`## .这是我的二级标题`

|||

效果（类似于）：

1.1 这是我的二级标题

-|||

**编号样式**：

支持多种编号格式，通过 `--auto-count` 参数设置，用逗号分隔 6 个值对应 h1–h6：

| 样式 | 输出示例 |
| --- | ------- |
| `number` | `1.`, `2.`, `3.`，连续使用时可生成 `1.1.`, `1.2.` |
| `latin` | `a)`, `b)`, `c)` |
| `latinUpper` | `A)`, `B)`, `C)` |
| `roman` | `i)`, `ii)`, `iii)`（上限 3999） |
| `romanUpper` | `I)`, `II)`, `III)`（上限 3999） |
| `chinese` | `一、`, `二、`, `三、` |
| `none` | 不编号 |

默认值：`none, chinese, number, number, latin, roman`（即 h1 不编号，h2 中文数字，h3–h4 阿拉伯数字，h5–h6 小写拉丁/罗马）。

## 5. 代码行数

显示代码行数时，在语言后添加 `{.line-numbers}`。

**注**：这个功能本来就有，这里修复了行数数字高度与代码行数不一致的问题。

|||-50

代码：

````plaintext
```javascript {.line-numbers}
function add(x, y) {
  return x + y
}
```
````

|||

效果：

```javascript {.line-numbers}
function add(x, y) {
  return x + y
}
```

-|||

## 6. Callout（不是新加的，但很有用）

显示有颜色的特定功能文本框。支持以下样式：

> [!abstract]
> 这里是内容

> [!bug]

> [!danger]

> [!example]

> [!failure]

> [!info]

> [!note]

> [!question]

> [!quote]

> [!success]

> [!tip]

> [!todo]

> [!warning]

**基本语法**：

|||-50

代码：

```markdown
> [!abstract]
> 这是 Callout 语法
```

|||

效果：

> [!abstract]
> 这是 Callout 语法

-|||

**支持更换默认标题**：

|||-50

代码：

```markdown
> [!abstract] 这里可以修改标题
> 这是 Callout 语法
```

|||

效果：

> [!abstract] 这里可以修改标题
> 这是 Callout 语法

-|||

**支持展开与嵌套**：

|||-50

代码：

```markdown
> [!tip]+
> Callout 语法是支持展开的
> 只需要在 `[!]` 后加上 `+/-` 即可
> 也即本例中的 `> [!tip]+`
>> [!tip]- 也可以默认收起
>> 还能递归展开
```

|||

效果：

> [!tip]+
> Callout 语法是支持展开的
> 只需要在 `[!]` 后加上 `+/-` 即可
> 也即本例中的 `> [!tip]+`
>> [!tip]- 也可以默认收起
>> 还能递归展开

-|||

> [!warning]
> 默认收起的 Callout 在打印时不会自动显示。如果需要自动展开，启用 `--expand-detail` 和 `--enable-header`。

## 7. 长代码排版

代码块不会另起一页，而是直接跟随上一页。

代码：

````markdown
```python
def resolve_extension_dir(
    extensions_root: Path,
    extension_pattern: str,
    explicit_extension_dir: Optional[Path] = None,
) -> Path:
    if explicit_extension_dir is not None:
        if not explicit_extension_dir.exists():
            raise FileNotFoundError(...)
        return explicit_extension_dir
    ...
```
````

效果：

```python
def resolve_extension_dir(
    extensions_root: Path,
    extension_pattern: str,
    explicit_extension_dir: Optional[Path] = None,
) -> Path:
    if explicit_extension_dir is not None:
        if not explicit_extension_dir.exists():
            raise FileNotFoundError(f"Extension directory not found: {explicit_extension_dir}")
        return explicit_extension_dir

    matches = sorted(extensions_root.glob(extension_pattern))
    if not matches:
        raise FileNotFoundError(
            "No extension directory matched pattern "
            f"'{extension_pattern}' under '{extensions_root}'"
        )

    return matches[-1]
```

## 8. 段落缩进

当 `--enable-parser` 启用时生效。在文档开头添加 `@indent` 或 `<indent>` 来为该文档启用段落缩进。

|||-50

代码：

```markdown
@indent

正文内容……
```

|||

效果：

首行自动缩进两个字符

-|||

## 9. PDF 导入居中

当 `--enable-parser` 启用时生效。`@import` 导入的 PDF 会居中显示。

需要安装 pdf2svg 工具。若未安装，会出现 `Error: spawn pdf2svg ENOENT` 报错。

代码：

```markdown
@import "./SYNTAX.pdf" {page_no=1}
```

效果：

@import "./SYNTAX.pdf" {page_no=1}
