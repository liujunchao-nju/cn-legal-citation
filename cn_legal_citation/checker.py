"""脚注核查：解析 → 重新渲染 → 与原文字比对。

这是确定性的核心用法之一：如果一条脚注能被引擎的字段重新渲染出完全
相同的文本，说明它符合手册式样；渲染不出来，差异就是问题所在。

比对分三档：

- ``ok``：逐字一致。
- ``style``：字段与式样都对，只是标点用了全角或句末标点不同。手册印刷示例
  用半角冒号与逗号，因此这类可以自动规范化，单列一档避免噪音又不漏掉。
- ``diff``：结构不一致，给出原文与引擎渲染结果，并列出差异点。
- ``unparsed``：模式没认出，需要人工或模型补字段。
"""

from __future__ import annotations

import difflib

from .formatter import cite
from .parser import normalize, parse_one

__all__ = ["check_one", "check_many", "summarize"]

# 可自动改写的状态
FIXABLE = ("style", "diff")


def _compare(original: str, rendered: str) -> str:
    if original == rendered:
        return "ok"
    if normalize(original) == normalize(rendered):
        return "style"
    return "diff"


def _diff_detail(original: str, rendered: str) -> list[str]:
    """给出人类可读的差异点。"""
    if original == rendered:
        return []
    if normalize(original) == normalize(rendered):
        return ["仅标点全角/半角不同，手册示例用半角"]
    matcher = difflib.SequenceMatcher(None, original, rendered)
    details = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            details.append(f"「{original[i1:i2]}」应为「{rendered[j1:j2]}」")
        elif tag == "delete":
            details.append(f"多余「{original[i1:i2]}」")
        elif tag == "insert":
            details.append(f"缺少「{rendered[j1:j2]}」")
    return details


def check_one(text: str, rules_dir=None) -> dict:
    """核查单条脚注。"""
    parsed = parse_one(text)
    result = {
        "text": text.strip(),
        "type": parsed.get("type"),
        "data": parsed.get("data") or {},
    }
    if not parsed.ok:
        result.update(
            status="unparsed",
            reason=parsed.get("reason", ""),
            rendered="",
            details=[],
        )
        return result

    try:
        rendered = cite(parsed["type"], parsed["data"], rules_dir)
    except Exception as exc:  # 字段缺失或类型未知
        result.update(
            status="error",
            reason=f"渲染失败: {exc}",
            rendered="",
            details=[],
        )
        return result

    status = _compare(result["text"], rendered)
    result.update(
        status=status,
        rendered=rendered,
        details=_diff_detail(result["text"], rendered) if status != "ok" else [],
    )
    return result


def check_many(entries, rules_dir=None) -> list[dict]:
    """核查一批脚注。

    ``entries`` 可以是字符串列表，也可以是形如
    ``{"locator": "脚注 3", "text": "..."}`` 的字典列表。
    """
    results = []
    for index, item in enumerate(entries, start=1):
        if isinstance(item, dict):
            locator = item.get("locator") or f"第 {index} 条"
            text = item.get("text", "")
        else:
            locator = f"第 {index} 条"
            text = item
        record = check_one(text, rules_dir)
        record["locator"] = locator
        results.append(record)
    return results


def summarize(results: list[dict]) -> dict:
    """汇总核查结果。"""
    counter = {"ok": 0, "style": 0, "diff": 0, "unparsed": 0, "error": 0}
    for item in results:
        counter[item["status"]] = counter.get(item["status"], 0) + 1
    total = len(results)
    return {
        "total": total,
        "ok": counter["ok"],
        "style": counter["style"],
        "diff": counter["diff"],
        "unparsed": counter["unparsed"],
        "error": counter["error"],
        "pass_rate": round(counter["ok"] / total * 100, 1) if total else 0.0,
        "fixable": counter["style"] + counter["diff"],
    }


def to_markdown(results: list[dict]) -> str:
    """把核查结果渲染成 Markdown 报告。"""
    stats = summarize(results)
    lines = [
        "# 脚注核查报告",
        "",
        f"- 脚注总数：{stats['total']}",
        f"- 完全合规：{stats['ok']}",
        f"- 标点需规范化：{stats['style']}",
        f"- 格式不符：{stats['diff']}",
        f"- 未能解析：{stats['unparsed']}",
        f"- 渲染出错：{stats['error']}",
        f"- 合规率：{stats['pass_rate']}%",
        f"- 可自动改写：{stats['fixable']}",
        "",
    ]
    problems = [r for r in results if r["status"] != "ok"]
    if not problems:
        lines.append("全部脚注均能用引擎逐字复现，未发现问题。")
        return "\n".join(lines)

    lines.append("## 问题清单")
    lines.append("")
    for item in problems:
        lines.append(f"### {item['locator']}")
        lines.append("")
        lines.append(f"- 原文：{item['text']}")
        if item["status"] == "unparsed":
            lines.append(f"- 状态：未能解析（{item.get('reason', '')}）")
        elif item["status"] == "error":
            lines.append(f"- 状态：{item.get('reason', '')}")
        else:
            label = "标点需规范化" if item["status"] == "style" else "格式不符"
            lines.append(f"- 状态：{label}（识别为 {item['type']}）")
            lines.append(f"- 建议改为：{item['rendered']}")
            for detail in item.get("details", []):
                lines.append(f"  - {detail}")
        lines.append("")
    return "\n".join(lines)
