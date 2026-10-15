"""整篇文档的核查与改写。

把「提取 → 解析 → 渲染比对 → 写回副本 → 复核」串成一条流水线，
供技能与命令行直接调用。

改写遵循两条安全约定：只输出副本；写回后重新读取输出文件复核。
"""

from __future__ import annotations

import pathlib

from .checker import FIXABLE, check_many, summarize, to_markdown
from .docio import DocError, extract, rewrite

__all__ = [
    "check_document",
    "rewrite_document",
    "document_report",
    "change_table",
]


def check_document(path: str | pathlib.Path, rules_dir=None) -> list[dict]:
    """核查整篇文档的脚注。返回带 locator 的核查结果列表。"""
    entries = extract(path)
    results = check_many(
        [{"locator": e["locator"], "text": e["text"]} for e in entries],
        rules_dir,
    )
    for record, entry in zip(results, entries):
        if entry.get("id") is not None:
            record["id"] = entry["id"]
        if entry.get("label") is not None:
            record["label"] = entry["label"]
    return results


def document_report(path: str | pathlib.Path, rules_dir=None) -> str:
    """生成整篇文档的核查报告（Markdown）。"""
    return to_markdown(check_document(path, rules_dir))


def _replacement_key(record: dict) -> str | None:
    if record.get("id") is not None:
        return str(record["id"])
    if record.get("label") is not None:
        return str(record["label"])
    return None


def rewrite_document(
    path: str | pathlib.Path,
    out_path: str | pathlib.Path,
    rules_dir=None,
    only_statuses=FIXABLE,
) -> dict:
    """把文档中格式不符的脚注改写为引擎结果，写入副本。

    默认只改「可自动改写」的状态（标点需规范化、格式不符）；未解析的
    一律不动 —— 不经确认不替用户猜。
    """
    results = check_document(path, rules_dir)
    replacements: dict[str, str] = {}
    changes: list[dict] = []

    for record in results:
        if record["status"] not in only_statuses:
            continue
        key = _replacement_key(record)
        if key is None or not record.get("rendered"):
            continue
        replacements[key] = record["rendered"]
        changes.append(
            {
                "locator": record["locator"],
                "type": record["type"],
                "before": record["text"],
                "after": record["rendered"],
                "details": record.get("details", []),
            }
        )

    skipped = [
        {"locator": r["locator"], "status": r["status"], "text": r["text"]}
        for r in results
        if r["status"] not in only_statuses
    ]

    if not replacements:
        return {
            "out_path": None,
            "changed": 0,
            "skipped": skipped,
            "changes": [],
            "summary": summarize(results),
            "verified": True,
            "note": "没有需要改写的脚注，未生成新文件。",
        }

    written = rewrite(path, replacements, out_path)

    # 写回后复核：重新读取输出文件，确认改动确实落地
    verified = True
    verify_notes: list[str] = []
    try:
        after = extract(written)
        index = {}
        for entry in after:
            if entry.get("id") is not None:
                index[str(entry["id"])] = entry["text"]
            if entry.get("label") is not None:
                index[str(entry["label"])] = entry["text"]
        for key, expected in replacements.items():
            actual = index.get(key)
            if actual is None:
                verified = False
                verify_notes.append(f"{key}: 输出文件中找不到该脚注")
            elif actual.strip() != expected.strip():
                verified = False
                verify_notes.append(
                    f"{key}: 期望「{expected}」，实际「{actual}」"
                )
    except DocError as exc:  # pragma: no cover - 兜底
        verified = False
        verify_notes.append(str(exc))

    return {
        "out_path": str(written),
        "changed": len(replacements),
        "skipped": skipped,
        "changes": changes,
        "summary": summarize(results),
        "verified": verified,
        "verify_notes": verify_notes,
        "note": "",
    }


def change_table(changes: list[dict]) -> str:
    """把改动渲染成 Markdown 对照表。"""
    if not changes:
        return "本次没有改写任何脚注。"
    lines = [
        "| 位置 | 识别类型 | 改前 | 改后 |",
        "|---|---|---|---|",
    ]
    for item in changes:
        before = item["before"].replace("|", "\\|")
        after = item["after"].replace("|", "\\|")
        lines.append(
            f"| {item['locator']} | {item['type']} | {before} | {after} |"
        )
    return "\n".join(lines)
