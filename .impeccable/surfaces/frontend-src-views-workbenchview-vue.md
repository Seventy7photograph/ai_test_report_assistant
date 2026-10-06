---
version: 1
slug: "frontend-src-views-workbenchview-vue"
primary_target: "frontend/src/views/WorkbenchView.vue"
related_targets: ["frontend/src/views/ArchiveView.vue","frontend/src/views/ReportView.vue","frontend/src/views/SettingsView.vue"]
---

# Surface brief — 测试报告助手控制台

## Scope and visitor mode

Operate. Web console, one product, four views: 工作台 / 档案 / 报告详情 / 设置.

## Audience, job, action

- Audience: 测试工程师（主）、测试负责人（次）。
- Job: 把一轮原始测试执行数据变成一份结论明确、指标可追溯、可归档可导出的测试报告。
- Primary action: 送检 → 生成 → 定值 → 存档/导出。
- Proof/content: 服务端确定性指标（通过率、执行率、缺陷分布）+ 模型写的归纳与建议 + 本地 SQLite 存档 + 跨版本趋势。真实数据源：`sample_test_results.json`。

## Constraints

- 单机/内网自部署，SQLite 本地存档，无用户体系。
- 模型走 OpenAI-compatible Chat Completions，API Key 在 `.env`。
- 控件必须是访客已经会的标准 Web 控件（Element Plus）；世界只提供字体、配色、密度、一个签名动作。
- 不编造数据：报告中一切数字来自输入或对输入的计算。

## Chosen direction and memorable moment

列表第 6 项「计量仪器读数面板」，按模式约束**受限使用**（只取排印、配色、密度、签名动作；不取仪器的物理外形、不取旋钮/表盘/机箱倒角作为装饰）。seed key `d5810774`。

Signature move: **定值**。贴入数据时读数以未定值态亮起（电光青 + 虚线基线）；报告生成完成后读数落定为墨色、基线由左向右画实，判定以钢印压入。整站只有这一个时间性动作。

## Unresolved decisions

- 是否接入真实用例管理平台（禅道/TAPD/TestRail）——未定，本轮不做。
- 多用户与权限——未定，本轮不做。

---

## Direction contract

THESIS: 把"这版能不能发"做成一次可核对的**读数**，而不是一段叙述。拒绝的类别默认：AI 工具把答案写成一段加粗散文，再配几张"大数字 + 小标签"的卡片。这里每个数都有量程、单位和来源，每句判断都能指回数据。

OWN-WORLD: 仪表台。机箱石墨 `#1C1F23`（顶栏）；读数面板 `#F4F4F1`（工作面）、内页纯白；墨 `#14171A`；发丝线 `#D3D6D2`；唯一强调色 电光青 `#17787F`。状态只用**实心小色块**：通过 `#2E7D53`、失败 `#B02A20`、阻塞 `#B57A12`、跳过 `#7A8087`。零阴影，所有层次由 1px 线表达；圆角 2–4px。数字等宽、右对齐、小数点对齐，单位另起小字列。正文用宋体族，标签/表头用黑体族（中文报告体裁的固有配对）。

STORY: 访客先读到上一轮读数与判定 → 贴入本轮数据 → 数字实时亮起为未定值态 → 点「生成报告」 → 模型补齐文字分析 → 读数**定值**、判定盖章 → 存档或导出。访客相信：数字是算的，文字是模型写的，二者分开。

FIRST VIEWPORT: 顶部 56px 石墨机箱条：左侧产品铭牌与版本，中间三个模式页签（工作台/档案/设置），右侧三枚实时读数（模型 / 存档 / 服务）。下方读数面板。工作台为 `380px + 1fr` 两栏：左栏「送检」——测试数据输入（等宽）、分析要求、模型选择、生成按钮；右栏「读数」——第一屏视觉权重最高的是**检验项目表**（发丝线读数表，首行为判定）与用例分布条，报告正文在其下方。签名动作在第一屏可见。

FORM: 有序列表第 6 项「计量仪器读数面板」（受限：字体、配色、密度、签名动作）。seed key `d5810774`。roll 裁定 build candidate 6；六个 challenger 全部未在两轴上同时胜出（详见下）。

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

---

## Roll record（seed d5810774, mode operate）

Challenger verdicts（两轴：受众认同 / 产品清晰）：

1. 角色周边商品目录 — 都不占。**declined**。捐献：每条记录使用固定的字段组（"铭牌式"固定字段），以及"退役项转灰而不消失"的状态纪律。
2. 喷气时代机票夹 — 产品清晰占优，受众认同是借来的。**competitive**（完整备选）。
3. 地铁排版色块 — 都不占。**declined**。捐献：色块本身就是内容（分布条是数据，不是装饰）。
4. 十九世纪词典页 — 两轴都部分占优。**competitive**（完整备选）。捐献：书眉"guide words"指明当前所在区间。
5. 定向越野地图与图例 — 都不占。**declined**。捐献：常驻图例，定义每一个出现的颜色。
6. 可变字体样本 — 都不占。**declined**。捐献：与操作联动的实时等宽读数。

进入构建的提升：实时读数（6）、常驻图例（5）、色块即内容（3）、固定字段组（1）。
