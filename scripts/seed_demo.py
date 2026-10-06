"""写入演示存档。

用于在没有 API Key 的情况下预览界面（档案列表、趋势图、报告详情）。
也会被视觉验收流程使用。

用法：
    python scripts/seed_demo.py            # 写入演示数据
    python scripts/seed_demo.py --reset    # 先清空再写入
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from assistant import store  # noqa: E402
from assistant.metrics import compute_metrics  # noqa: E402

_ROUNDS = [
    {
        "version": "4.1.0",
        "created_at": "2026-08-18T10:12:00+08:00",
        "data": {
            "version": "4.1.0",
            "total_cases": 486,
            "passed": 441,
            "failed": 31,
            "blocked": 14,
            "defects": [
                {"id": "BUG-011", "title": "批量导出内存溢出", "priority": "P0", "module": "报表导出", "status": "open"},
                {"id": "BUG-012", "title": "登录态偶发失效", "priority": "P1", "module": "权限管理", "status": "open"},
                {"id": "BUG-013", "title": "列表排序不稳定", "priority": "P2", "module": "案件管理", "status": "open"},
            ],
        },
        "body": """## 测试概况
本轮覆盖 4.1.0 全量回归，共执行 486 条用例，阻塞 14 条集中在第三方对账接口不可用。

## 关键指标解读
通过率 90.7%，低于上一版本的验收基线。失败用例中 19 条集中在报表导出与权限管理两个模块。

## 主要缺陷与风险
BUG-011 批量导出内存溢出为 P0 未关闭，直接影响月末结账场景，属于阻断性风险。

## 风险判断依据
存在未关闭的 P0 缺陷，且失败率高于 5% 阈值，两项均触发不建议发版的判定。

## 建议与下一步
先修复 BUG-011 并回归报表导出全部用例，再补测权限管理的登录态失效路径。""",
    },
    {
        "version": "4.2.0",
        "created_at": "2026-09-08T16:40:00+08:00",
        "data": {
            "version": "4.2.0",
            "total_cases": 500,
            "passed": 468,
            "failed": 22,
            "blocked": 10,
            "defects": [
                {"id": "BUG-001", "title": "导出任务队列积压", "priority": "P0", "module": "报表导出", "status": "open"},
                {"id": "BUG-002", "title": "角色切换后菜单未刷新", "priority": "P1", "module": "权限管理", "status": "open"},
                {"id": "BUG-003", "title": "接口超时未重试", "priority": "P1", "module": "接口", "status": "resolved"},
            ],
        },
        "body": """## 测试概况
4.2.0 回归执行 500 条用例，通过 468 条，失败 22 条，阻塞 10 条。

## 关键指标解读
通过率 93.6%，较 4.1.0 提升 2.9 个百分点。执行率 98.0%，未执行项为零。

## 主要缺陷与风险
P0 缺陷 1 条（BUG-001 导出任务队列积压）仍未关闭，风险集中在报表导出模块。

## 风险判断依据
存在未关闭的 P0 缺陷，按判定规则直接进入不建议发版，与失败率高低无关。

## 建议与下一步
BUG-001 修复后需针对导出模块做一次专项回归；权限管理的角色切换建议纳入冒烟集。""",
    },
    {
        "version": "4.3.0",
        "created_at": "2026-10-05T09:05:00+08:00",
        "data": {
            "version": "4.3.0",
            "total_cases": 640,
            "passed": 634,
            "failed": 4,
            "blocked": 2,
            "defects": [
                {"id": "BUG-201", "title": "并发提交重复建单", "priority": "P1", "module": "案件管理", "status": "resolved"},
                {"id": "BUG-202", "title": "搜索关键字高亮丢失", "priority": "P2", "module": "全局搜索", "status": "resolved"},
            ],
        },
        "body": """## 测试概况
4.3.0 全量回归执行 640 条用例，通过 634 条，失败 4 条，阻塞 2 条。

## 关键指标解读
通过率 99.1%，执行率 99.7%。全部缺陷均已关闭，本轮无遗留未关闭项。

## 主要缺陷与风险
历史 P0 缺陷已全部验证关闭；剩余 4 条失败为环境相关的偶发用例，复跑均已通过。

## 风险判断依据
失败率 0.6% 低于 5% 阈值，未关闭缺陷为 0，判定为建议发版。

## 建议与下一步
发版前补一次冒烟；把两条偶发失败用例的稳定性问题单独立项跟踪。""",
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description="写入演示存档")
    parser.add_argument("--reset", action="store_true", help="先删除已有存档")
    args = parser.parse_args()

    store.init_db()

    if args.reset:
        items, _ = store.list_reports(limit=1000)
        for item in items:
            store.delete_report(item["id"])
        print(f"已清空 {len(items)} 份存档")

    for round_ in _ROUNDS:
        result = compute_metrics(json_dumps(round_["data"]))
        metrics = result.metrics
        report_id = store.save_report(
            {
                "created_at": round_["created_at"],
                "title": f"{round_['version']} 测试报告",
                "version": round_["version"],
                "model": "deepseek-chat",
                "provider": "DeepSeek",
                "instruction": "重点分析高优先级缺陷、版本风险，并给出回归建议。",
                "source_data": json_dumps(round_["data"], indent=2),
                "report": round_["body"],
                "metrics": metrics.model_dump() if metrics else None,
                "defects": [d.model_dump() for d in result.defects],
                "usage": None,
                "warnings": result.warnings,
                "elapsed_ms": 4200,
            }
        )
        label = metrics.verdict_label if metrics else "无法判定"
        print(f"已写入 {round_['version']} → {report_id} · {label}")

    print(f"当前共 {store.count_reports()} 份存档 · {store.db_path()}")


def json_dumps(value, indent: int | None = None) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, indent=indent)


if __name__ == "__main__":
    main()
