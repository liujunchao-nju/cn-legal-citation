"""命令行入口。

推荐用 JSON 文件传入文献信息，避免命令行引号转义的麻烦。
"""

from __future__ import annotations

import argparse
import json
import sys

from .checker import check_many, summarize, to_markdown
from .docflow import change_table, document_report, rewrite_document
from .docio import DocError, extract
from .formatter import cite, cite_many
from .parser import parse_one
from .rules import export_rules, load_rules

__all__ = ["main"]


def _read_json(path: str):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _read_lines(path: str) -> list[str]:
    with open(path, encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def _cmd_types(args) -> int:
    rules, _ = load_rules(args.rules)
    width = max(len(name) for name in rules)
    for name in sorted(rules):
        rule = rules[name]
        print(f"{name.ljust(width)}  {rule['label']}")
    return 0


def _cmd_cite(args) -> int:
    if args.file:
        data = _read_json(args.file)
    elif args.data:
        data = json.loads(args.data)
    else:
        print("错误：需要 --data 或 --file", file=sys.stderr)
        return 2
    print(cite(args.type, data, args.rules))
    return 0


def _cmd_batch(args) -> int:
    items = _read_json(args.file)
    if isinstance(items, dict):
        items = items.get("items") or []
    for line in cite_many(items, args.rules):
        print(line)
    return 0


def _cmd_show(args) -> int:
    rules, _ = load_rules(args.rules)
    if args.type not in rules:
        print(f"错误：未知类型 {args.type}", file=sys.stderr)
        return 2
    rule = rules[args.type]
    print(f"类型: {rule['type']}")
    print(f"名称: {rule['label']}")
    print(f"文件: {rule['_file']}")
    print(f"说明: {rule.get('description', '').strip()}")
    print(f"依据: {rule.get('source', '').strip()}")
    print("示例:")
    for example in rule.get("examples") or []:
        print(f"  {example}")
    return 0


def _cmd_export(args) -> int:
    path = export_rules(args.out, args.rules)
    print(f"已导出规则到 {path}")
    return 0


def _cmd_parse(args) -> int:
    """脚注文本 → 字段。用于人工核对与模型补字段前的预解析。"""
    if args.file:
        texts = _read_lines(args.file)
    elif args.text:
        texts = [args.text]
    else:
        print("错误：需要 --text 或 --file", file=sys.stderr)
        return 2

    payload = []
    for text in texts:
        result = parse_one(text)
        payload.append(
            {
                "text": result.get("original", text),
                "type": result.get("type"),
                "data": result.get("data") or {},
                "ok": result.ok,
                "reason": result.get("reason", ""),
            }
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item in payload:
            flag = item["type"] if item["ok"] else f"未解析（{item['reason']}）"
            print(f"{item['text']}\n  -> {flag}")
            if item["ok"]:
                print(f"     {json.dumps(item['data'], ensure_ascii=False)}")
    return 0


def _cmd_check(args) -> int:
    """核查脚注文本（按行读入）。"""
    if args.file:
        entries = [{"locator": f"第 {i} 行", "text": t} for i, t in enumerate(_read_lines(args.file), 1)]
    elif args.text:
        entries = [{"locator": "输入", "text": args.text}]
    else:
        print("错误：需要 --text 或 --file", file=sys.stderr)
        return 2

    results = check_many(entries, args.rules)
    if args.json:
        print(json.dumps({"summary": summarize(results), "results": results}, ensure_ascii=False, indent=2))
        return 0
    print(to_markdown(results))
    return 0


def _cmd_doc_extract(args) -> int:
    entries = extract(args.file)
    if args.json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
    else:
        print(f"共 {len(entries)} 条脚注：")
        for entry in entries:
            print(f"  {entry['locator']}: {entry['text']}")
    return 0


def _cmd_doc_check(args) -> int:
    report = document_report(args.file, args.rules)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"报告已写入 {args.out}")
    else:
        print(report)
    return 0


def _cmd_doc_rewrite(args) -> int:
    try:
        result = rewrite_document(args.file, args.out, args.rules)
    except DocError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    stats = result["summary"]
    print(
        f"脚注总数 {stats['total']}，完全合规 {stats['ok']}，"
        f"标点需规范化 {stats['style']}，格式不符 {stats['diff']}，"
        f"未能解析 {stats['unparsed']}"
    )
    if result["changed"]:
        print(f"已改写 {result['changed']} 条，输出到 {result['out_path']}")
        print(f"写回复核：{'通过' if result['verified'] else '未通过'}")
        for note in result.get("verify_notes", []):
            print(f"  - {note}")
        if args.table:
            with open(args.table, "w", encoding="utf-8") as fh:
                fh.write(change_table(result["changes"]))
            print(f"对照表已写入 {args.table}")
        else:
            print()
            print(change_table(result["changes"]))
    else:
        print(result.get("note", "没有需要改写的脚注。"))

    if result["skipped"]:
        print()
        print("以下脚注未改动：")
        for item in result["skipped"]:
            if item["status"] == "unparsed":
                print(f"  {item['locator']}（未能解析）：{item['text']}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cn-legal-citation",
        description="按《法学引注手册》（第二版）生成、核查、改写中文法学脚注",
    )
    parser.add_argument("--rules", help="自定义规则目录，默认使用包内 rules/")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("types", help="列出所有文献类型").set_defaults(func=_cmd_types)

    cite_cmd = sub.add_parser("cite", help="生成单条脚注")
    cite_cmd.add_argument("--type", required=True, help="文献类型，如 book")
    cite_cmd.add_argument("--data", help="文献信息 JSON 字符串")
    cite_cmd.add_argument("--file", help="文献信息 JSON 文件路径")
    cite_cmd.set_defaults(func=_cmd_cite)

    batch_cmd = sub.add_parser("batch", help="批量生成脚注")
    batch_cmd.add_argument("--file", required=True, help="JSON 文件，含条目数组")
    batch_cmd.set_defaults(func=_cmd_batch)

    show_cmd = sub.add_parser("show", help="查看某类型的规则说明与示例")
    show_cmd.add_argument("--type", required=True)
    show_cmd.set_defaults(func=_cmd_show)

    export_cmd = sub.add_parser(
        "export", help="把规则导出为单个 JSON，供免安装环境使用"
    )
    export_cmd.add_argument("--out", required=True, help="输出路径，如 rules.json")
    export_cmd.set_defaults(func=_cmd_export)

    parse_cmd = sub.add_parser("parse", help="脚注文本 → 字段（逆向解析）")
    parse_cmd.add_argument("--text", help="单条脚注文本")
    parse_cmd.add_argument("--file", help="文本文件，每行一条脚注")
    parse_cmd.add_argument("--json", action="store_true", help="输出 JSON")
    parse_cmd.set_defaults(func=_cmd_parse)

    check_cmd = sub.add_parser("check", help="核查脚注文本是否合式样")
    check_cmd.add_argument("--text", help="单条脚注文本")
    check_cmd.add_argument("--file", help="文本文件，每行一条脚注")
    check_cmd.add_argument("--json", action="store_true", help="输出 JSON")
    check_cmd.set_defaults(func=_cmd_check)

    doc_extract = sub.add_parser("doc-extract", help="提取文档中的脚注")
    doc_extract.add_argument("--file", required=True, help=".md 或 .docx")
    doc_extract.add_argument("--json", action="store_true")
    doc_extract.set_defaults(func=_cmd_doc_extract)

    doc_check = sub.add_parser("doc-check", help="核查整篇文档的脚注")
    doc_check.add_argument("--file", required=True, help=".md 或 .docx")
    doc_check.add_argument("--out", help="报告输出路径，缺省打印到屏幕")
    doc_check.set_defaults(func=_cmd_doc_check)

    doc_rewrite = sub.add_parser(
        "doc-rewrite", help="把文档中格式不符的脚注改写为规范式样（输出副本）"
    )
    doc_rewrite.add_argument("--file", required=True, help=".md 或 .docx")
    doc_rewrite.add_argument("--out", required=True, help="输出副本路径，不得与原件相同")
    doc_rewrite.add_argument("--table", help="改动对照表输出路径")
    doc_rewrite.set_defaults(func=_cmd_doc_rewrite)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
