---
name: AI 测试报告助手
description: 把测试执行数据变成可核对读数的计量台式控制台
colors:
  case: "#1c1f23"
  case-line: "#34393f"
  case-ink: "#e9ebe7"
  case-ink-2: "#9aa1a8"
  case-accent: "#4fb3ba"
  face: "#f4f4f1"
  sheet: "#ffffff"
  ink: "#14171a"
  ink-2: "#5a6068"
  ink-3: "#656b73"
  rule: "#d3d6d2"
  rule-soft: "#e6e8e4"
  accent: "#17787f"
  accent-weak: "#e8f1f2"
  pass: "#2e7d53"
  pass-fill: "#3e8f63"
  fail: "#b02a20"
  fail-fill: "#c0342a"
  blocked: "#8f6010"
  blocked-fill: "#b57a12"
  skipped: "#62686f"
  skipped-fill: "#7c838a"
typography:
  readout:
    fontFamily: "JetBrains Mono Variable, JetBrains Mono, Cascadia Mono, Consolas, monospace"
    fontSize: "21px"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "-0.01em"
    fontFeature: "\"tnum\" 1"
  title:
    fontFamily: "Noto Serif SC, Source Han Serif SC, Songti SC, SimSun, serif"
    fontSize: "22px"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "Noto Serif SC, Source Han Serif SC, Songti SC, SimSun, serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.85
  ui:
    fontFamily: "Noto Sans SC, PingFang SC, Microsoft YaHei, Source Han Sans SC, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Noto Sans SC, PingFang SC, Microsoft YaHei, Source Han Sans SC, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 500
    lineHeight: 1.6
    letterSpacing: "0.14em"
rounded:
  block: "1px"
  sm: "2px"
  md: "3px"
spacing:
  space-1: "4px"
  space-2: "8px"
  space-3: "12px"
  space-4: "16px"
  space-5: "24px"
  space-6: "32px"
  space-7: "48px"
components:
  case:
    backgroundColor: "{colors.case}"
    textColor: "{colors.case-ink}"
    height: "56px"
  panel:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "16px"
  readout-value:
    typography: "{typography.readout}"
    textColor: "{colors.accent}"
  readout-value-locked:
    textColor: "{colors.ink}"
  stamp-pass:
    textColor: "{colors.pass}"
    rounded: "{rounded.sm}"
    padding: "7px 16px"
  stamp-conditional:
    textColor: "{colors.blocked}"
    rounded: "{rounded.sm}"
    padding: "7px 16px"
  stamp-reject:
    textColor: "{colors.fail}"
    rounded: "{rounded.sm}"
    padding: "7px 16px"
  stamp-unknown:
    textColor: "{colors.ink-3}"
    rounded: "{rounded.sm}"
    padding: "7px 16px"
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.sheet}"
    rounded: "{rounded.md}"
    padding: "8px 15px"
    height: "32px"
  button-primary-hover:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.sheet}"
  button-default:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.md}"
    padding: "8px 15px"
    height: "32px"
  button-default-hover:
    backgroundColor: "{colors.accent-weak}"
    textColor: "{colors.accent}"
  preset-chip:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.sm}"
    padding: "3px 10px"
---

# Design System: AI 测试报告助手

## Overview

**Creative North Star: 「计量台」**

这个世界把界面当成一台计量仪器：机箱在上，读数面板在下，中间只有发丝线。产品要回答的唯一问题是"这版能不能发"，所以界面不写散文、不给结论卡片，只给读数——每个数有量程（单位）、有来源（服务端计算）、有判定（盖章）。数字右对齐成列、小数点对齐、单位另起一列小字；层次靠 1px 线和地面明度，不靠阴影、不靠留白堆砌、不靠"大数字 + 小标签"的营销卡。

受限使用：只取仪器的排印、配色、密度与一个签名动作，不取仪器的物理外形。没有旋钮、没有表盘、没有机箱倒角、没有螺丝。它看起来像读数面板，不像一台设备。

唯一的时间性动作是签名动作**定值**：数据贴入后读数以电光青 + 虚线基线亮起（未定值）；报告生成完成后落定为墨色、基线由左向右画实，判定以钢印压入。整站只有这一个动作，其余过渡克制到几乎看不见。

**Key Characteristics:**
- 石墨机箱 + 纸白读数面板的双色地面；零阴影，层次只由 1px 线表达。
- 唯一强调色电光青，语义是"尚未定值"，不是装饰。
- 三种字体各司其职：黑体做界面、宋体做文书、等宽做读数。
- 高密度：13px 界面正文、9px 级行距、11px 刻印标签。
- 状态只以 6–7px 实心方色块出现，不用药丸、圆点、环形或光晕。
- 一个签名动作：定值（青色虚线 → 墨色实线 + 钢印）。

## Colors

调色板是一台被照亮的仪器：深石墨机箱、纸白工作面、单色墨、一条电光青。颜色分两组——机箱（暗）与面板（亮）——两组共享同一套发丝线逻辑。

### Primary
- **电光青 (#17787f)**: 全站唯一的强调色，只承担一个语义——**未定值**（数据已贴入、指标已算出、报告尚未生成时的读数颜色），另用于焦点环与默认按钮 hover 底。它从不代表"成功"或"品牌"。配套的 **青雾 (#e8f1f2)** 只做焦点外环与 hover 底这类薄层。

### Secondary
状态色成对出现：文字版用于文本与描边（对比度 ≥4.5:1），填充版用于实心色块（≥3:1）。同一个语义，两个明度。
- **通过绿 (#2e7d53) / 色块绿 (#3e8f63)**: 通过用例、已修复缺陷、探活成功、建议发版。
- **失败红 (#b02a20) / 色块红 (#c0342a)**: 失败用例、未关闭缺陷、P0 优先级、不建议发版。
- **阻塞琥珀 (#8f6010) / 色块琥珀 (#b57a12)**: 阻塞用例、P1 优先级、需注意的告警条、有条件通过。
- **跳过灰 (#62686f) / 色块灰 (#7c838a)**: 未执行用例、无法判定、已驳回、中性标注。

### Neutral
- **墨 (#14171a)**: 面板上的主文字，也是所有"已定值"读数的颜色——它是这个世界的"落定"色。
- **墨二级 (#5a6068)**: 次级说明与表格单元文字。
- **墨三级 (#656b73)**: 刻印标签、表头、元信息、空态读数这类最不重要的文字。
- **面板纸 (#f4f4f1)**: 工作面底色；也是表头、告警条、面板脚的底。
- **内页白 (#ffffff)**: 面板与表格的真正背景，必须比面板纸更亮——靠这一点点反差把"读数框"从背景里切出来。
- **发丝线 (#d3d6d2)**: 结构性分界：面板边、面板头下沿、表头下沿。
- **细发丝线 (#e6e8e4)**: 面板内部的逐行分界。

### Neutral — 机箱
- **机箱石墨 (#1c1f23)**: 顶栏。**机箱线 (#34393f)** 是它的底边分界。**机箱字 (#e9ebe7)** 与 **机箱次字 (#9aa1a8)** 是暗底上的两级文字，**机箱青 (#4fb3ba)** 是同一色相在暗底上的高亮版本——#17787f 在石墨上读不出来，暗底换用亮版；铭牌图标与页签指示块用它。

### Named Rules
**The One Accent Rule.** 电光青是唯一点缀色，一屏面积不超过约 5%。它的语义是"尚未定值"，不是"品牌色"。把它当作装饰色块、渐变起点或成功提示都越界——成功是绿，不是青。
**The Two Tones Rule.** 每个状态色都有文字版与填充版两个明度：文字与描边用深版，实心色块用亮版。不要在文字上放填充版，也不要在色块上放文字版。
**The Solid Block Rule.** 状态一律是 6–7px 的实心方色块（1px 圆角）。不用药丸、圆点、环形、也不用带光晕的指示灯。色块是数据，不是徽章。

## Typography

**Display Font:** Noto Serif SC（宋体族，回退 Source Han Serif SC / Songti SC / SimSun）
**Body Font:** Noto Sans SC（黑体族，回退 PingFang SC / Microsoft YaHei / Source Han Sans SC / system-ui）
**Label/Mono Font:** JetBrains Mono（等宽，回退 Cascadia Mono / Consolas）

**Character:** 中文报告体裁的固有配对。三种字体不是三种风格，而是三种"谁在说话"：黑体是界面在说话，宋体是模型在说话（报告正文与视图大标题），等宽是计算在说话（一切数字、编号、时间、字段名）。字体全部自托管，内网可用，不依赖任何 CDN。

### Hierarchy
- **读数 (readout) (400, 21px, 1.2, 字距 -0.01em)**: 面板上的关键数字。等宽 + 表格数字，右对齐，单位另起一列更小的等宽字。窄屏降到 18px。
- **页面标题 (title) (600, 22px, 1.3)**: 宋体，只在视图级标题出现一次（报告档案 / 设置 / 报告详情）。
- **报告正文 (body) (400, 15px, 1.85)**: 宋体，模型生成的报告正文，宽松行高，最大宽度 74ch。
- **界面正文 (ui) (400, 13px, 1.6)**: 黑体，全站默认字号；表格单元、说明、按钮都在这档。
- **刻印标签 (label) (500, 11px, 字距 0.14em, 大写)**: 黑体，字距拉开、转大写的小标签（字段名、表头、眉标）。它是这个世界的标签母语。
- **次级界面 (400, 12px, 1.6)**: 面板标题、次级行、单位、图例。
- **微字 (400, 10–11px, 等宽)**: 时间戳、百分比注、来源脚注、面板元信息，等宽 + 表格数字。

### Named Rules
**The Tabular Rule.** 一切数字都用等宽 + `tnum` 表格数字，右对齐成列；单位与百分比放在独立的小字列里。永远不把单位拼进读数本身——"500"和"条"是两格，"98.0%"是墨三级的小字而不是读数的主色。
**The Stencil Label Rule.** 字段名、表头、眉标一律用刻印标签的形制（11px、字距 0.14em、大写、墨三级），并让它可以跟一条自动延伸的细发丝线组成"标签 + 长线"。这是世界的原生标签动作——保留它，但不要把它放大或加粗成更响的标题。
**The Three Voices Rule.** 黑体 = 界面，宋体 = 模型，等宽 = 计算。不要混用：不要把界面文案排成宋体，也不要把模型正文排成等宽。

## Layout

空间模型是"顶栏 + 单列内容区 + 面板网格"。
- 顶栏恒高 56px、sticky、贯穿全宽，不参与内容栅格。
- 内容区四周内边距 24px（下沿 48px）；窄屏收为 16px / 12px / 32px。
- 页面容器居中，最大宽度 1480px（设置页 1100px）；面板之间统一 16px 间距。
- 工作台是 `minmax(320px, 400px) + 1fr` 双栏：左栏「送检」sticky 在 `calc(56px + 16px)`，右栏「读数 + 报告」。两栏在 1080px 以下并成单列。
- 报告详情是 `1fr / 1.35fr` 双栏（读数 | 报告），同样在 1080px 以下并成单列。
- 设置是 `auto-fit minmax(340px, 1fr)` 自适应列；档案是纵向堆叠（趋势 → 筛选 + 表格 → 两轮对比）。

**密度：** 间距节奏是 4 / 8 / 12 / 16 / 24 / 32 / 48px，实际最常用的是 12 与 16。面板头最小高 42px、内边距 10px / 16px；读数行上下 9px、左右 16px（窄屏 8px / 12px）；表格单元 9px / 16px、表头 7px。密度靠"线多、边距刚好"实现，不靠字号压缩。

**响应式：** 1080px 并单栏并隐藏顶栏第一枚读数（模型）；860px 隐藏全部实时读数；720px 收紧内容内边距、趋势图换窄画布几何、缺陷表单元收紧；560px 压缩顶栏间距并隐藏版本号，读数降到 18px，判定块改纵向堆叠。

### Named Rules
**The Fixed 56 Rule.** 顶栏恒为 56px 且 sticky。所有 sticky 子元素的上沿按 `calc(var(--shell-height) + 16px)` 计算，不写魔法数字。
**The Hairline Index Rule.** 面板内部的每一行由一条细发丝线结束，最后一行不封边。不要用斑马纹，也不要用行间距代替线。

## Elevation & Depth

这个系统**没有阴影**，这是硬约束而不是缺省。Element Plus 的四个阴影变量被显式设为 `none`，全站也没有任何自定义 `box-shadow`、`drop-shadow` 或发光。层次完全由两样东西表达：**地面明度**（机箱石墨 → 面板纸 → 内页白，三级递亮）与 **1px 线**（结构用发丝线，行内用细发丝线）。浮层——下拉、弹窗、消息、气泡——同样没有阴影，只靠 1px 边框和白色底从面板纸里"切"出来。焦点不靠阴影而靠外环。

### Named Rules
**The Flat Case Rule.** 零阴影。任何"浮起来"的需求都用边框 + 地面明度解决，不用阴影、不用模糊、不用发光。
**The Ring Not Glow Rule.** 焦点是描边与圆环，不是光晕。输入焦点 = 1px 青色内描边 + 3px 青雾外环；状态灯 = 1px 描边 + 实心填充，不做 halo。

## Shapes

方角仪器。基准圆角 3px，小元素（chip、钢印、色板）2px，状态色块与指示块 1px——是"方块"而不是"圆点"。发丝线一律 1px，永不加粗成 2px 的分隔带；判定章是唯一例外，用 2px 描边表达"盖章"。表格只保留横线，没有竖线也没有外框。唯一的斜置元素是判定章：`rotate(-3deg)` 的钢印。整体轮廓语言是"被照亮的读数框"——矩形、直角、被 1px 线切开。

### Named Rules
**The Near-Square Rule.** 状态指示是方块不是圆点：6–7px、1px 圆角。全站圆角上限 3px；任何超过 4px 的圆角都属于另一个世界。

## Components

### Buttons
- **Shape:** 近方角（3px 圆角），黑体 500，字号 13px。
- **Primary:** 底为墨色、文字为内页白；hover 时底转电光青。它是所在区域唯一的实心重色按钮（「生成报告」在左栏底部通栏）。语义上"墨 = 已定值"，所以主按钮用墨，hover 才亮起。
- **Secondary / Default:** 白底 + 发丝线描边 + 墨二级文字；hover 时底转青雾、描边与文字转电光青。用于导出（Markdown / HTML / Word / JSON）、刷新、清空、载入。
- **Danger:** 删除用 danger plain，描边与文字走失败红。
- **Focus:** 全局可见焦点 = 2px 青色外环 + 2px 偏移。

### Chips
- **预设 chip（发版评估 / 回归建议 / 缺陷复盘）:** 白底、1px 发丝线、2px 圆角、11px 黑体、墨二级文字；hover 描边与文字转电光青。它填的是提示词，不是筛选状态，所以没有选中态。
- **标签 (tag):** 等宽 11px、2px 圆角；中性标签底为极浅灰、描边发丝线、文字墨二级。

### Cards / Containers
- **Character:** 这个世界的基本容器是"读数框"。
- **Corner Style:** 3px 圆角。
- **Background:** 内页白；表头与告警条底为面板纸。
- **Shadow Strategy:** 无（见 Elevation & Depth）。
- **Border:** 1px 发丝线；面板头下方一条发丝线；内部行用细发丝线，最后一行不封边。
- **Internal Padding:** 面板头 10px / 16px、最小高 42px；面板体 16px；读数行 9px / 16px。
- **Head pattern:** 左侧面板标题（12px 黑体、字距 0.08em）+ 右侧等宽微字元信息（"由服务端计算""mock-report-model 撰写 79ms"）。

### Inputs / Fields
- **Style:** 白底、1px 发丝线内描边、3px 圆角、无投影。测试数据文本域用等宽 12.5px、行高 1.7。
- **Focus:** 1px 青色内描边 + 3px 青雾外环。
- **Hover:** 内描边转墨三级。
- **Disabled:** 极浅灰底 + 细发丝线描边。
- **Select / Switch:** 沿用 Element Plus 形态，只换色：选中项文字电光青，开关打开为电光青。

### Navigation
- **Style:** 56px 石墨机箱条，底边 1px 机箱线。左侧铭牌（1px 描边的仪表图标 + 产品名 + 等宽版本号），中间模式页签，右侧三枚实时读数。
- **Typography:** 页签 12px 黑体、字距 0.08em；读数标签 10px 大写、字距 0.16em；读数值 12px 等宽表格数字。
- **States:** 默认机箱次字；hover 转机箱字且指示块画到 40%；active（当前路由）机箱字 + 指示块满宽。指示块是 2px 机箱青方块，不是下边框。
- **Mobile:** 1080px 以下隐藏模型读数，860px 以下隐藏全部读数，560px 以下压缩间距并隐藏版本号。

### Readout Row
检验项目表：每行"左标签 + 右值"。左标签可带一枚 6px 状态色块；右侧是三列网格——读数值（等宽 21px，右对齐）、单位（11px 等宽、墨三级）、百分比注（11px 等宽、墨三级）。
- **未定值态:** 电光青 + 1px 虚线基线。
- **已定值态:** 墨色，虚线消失，基线由左向右画实（620ms），颜色过渡 320ms。
- **空态:** 墨三级 + 虚线基线，显示 "——"。空读数绝不用电光青假装它在读数。

### Verdict Stamp
判定以钢印压入：2px `currentColor` 描边、2px 圆角、`rotate(-3deg)`、黑体 15px 700、字距 0.22em（含同值 `text-indent` 补偿）。颜色随判定走状态文字色（通过绿 / 阻塞琥珀 / 失败红 / 墨三级）。报告生成完成时播放压印动画（从 1.4× 模糊缩放压到 1×，480ms）。左侧是章，右侧是"判定依据"刻印标签 + 逐条依据（每条前置一枚 5px 短横线）。

### Outcome Bar
一条 10px 高、1px 描边、2px 圆角的分段条：通过 / 失败 / 阻塞 / 未执行按数量占比横向铺满，段间用 1px 内页白分隔。**色块即数据**：颜色宽度就是用例数，不是装饰。空态是虚线描边 + 细发丝斜纹。下方一行等宽微字：左"共 N 条"，右"执行 M 条"。

### Trend Chart
通过率趋势线：1.5px 墨色折线，判定点用 7px 实心方色块（按判定着色，1.5px 内页白描边）。纵轴不写死 0–100%，下界按数据自适应（最低值向下取整到 10%），95% 判定线用墨三级虚线 + 端点标注。图例常驻，逐一解释每一种颜色与两种线型（色块 = 判定，虚线 = 判定线，实线 = 通过率）。720px 以下换用窄画布几何（viewBox 360×240、2 条刻度、隔点标标签），而不是把宽画布等比压扁——压扁会让 10 单位字号只剩约 3px。

### Element Plus 映射
控件保持访客已经会用的标准形态，世界只换主题：字体、配色、圆角、零阴影、表格只留横线且读数右对齐。组件不重新发明；世界只在排印、配色、密度与签名动作上生效。

## Do's and Don'ts

### Do:
- **Do** 用 1px 发丝线分格、用地面明度分层次，绝不用阴影。
- **Do** 把一切数字排成等宽 + 表格数字、右对齐，单位和百分比各占一列微字。
- **Do** 用 6–7px 实心方色块表达状态（通过绿 / 失败红 / 阻塞琥珀 / 跳过灰）。
- **Do** 保留刻印标签（11px、字距 0.14em、大写、墨三级）作为字段名与表头的母语。
- **Do** 让每个读数遵守定值规则：未定值 = 电光青 + 虚线，已定值 = 墨 + 实线。
- **Do** 控制圆角在 1–3px：面板 3px，chip 与钢印 2px，状态色块 1px。
- **Do** 用宋体排模型写的报告正文与视图标题，用黑体排界面，用等宽排读数。

### Don't:
- **Don't** 加任何 `box-shadow`、发光、模糊或渐变（唯一的渐变是空态 45° 发丝斜纹）。浮层也没有阴影。
- **Don't** 引入第二个强调色；电光青是唯一的，且只表示"尚未定值"。
- **Don't** 把状态做成药丸、圆点、环形或带光晕的 LED；状态永远是实心方块。
- **Don't** 用超过 4px 的圆角做卡片或按钮；这个世界是方角仪器。
- **Don't** 把未定值的读数排成墨色，也不要把已定值的读数留成青色——颜色就是状态。
- **Don't** 用系统 display 字体或衬线体排界面控件文字。
- **Don't** 用 emoji 或字形图标；图标是 1px 描边的内联 SVG 或 Element Plus 图标组件。
- **Don't** 把刻印标签放大成标题或加粗成眉标；它的 11px 与墨三级就是它的克制。
