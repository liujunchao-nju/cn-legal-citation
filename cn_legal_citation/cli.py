"""命令行入口。

推荐用 JSON 文件传入文献信息，避免命令行引号转义的麻烦。
"""

from __future__ import annotations

import argparse
import json
import sys

from .formatter import cite, cite_many
from .rules import load_rules

__all__ = ["main"]


def _read_json(path: str):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cn-legal-citation",
        description="按《法学引注手册》（第二版）生成中文法学脚注",
    )
    parser.add_argument("--rules", help="自定义规则目录，默认使用包内 rules/")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("types", help="列出所有文献类型").set_defaults(func=_cmd_types)

    cite_cmd = sub.add_parser("cite", help="生成单条脚注")
    cite_cmd.add_argument("--type", required=True, help="文献类型，如 book")
    cite_cmd.add_argument("--data", help='文献信息 JSON 字符串')
    cite_cmd.add_argument("--file", help="文献信息 JSON 文件路径")
    cite_cmd.set_defaults(func=_cmd_cite)

    batch_cmd = sub.add_parser("batch", help="批量生成脚注")
    batch_cmd.add_argument("--file", required=True, help="JSON 文件，含条目数组")
    batch_cmd.set_defaults(func=_cmd_batch)

    show_cmd = sub.add_parser("show", help="查看某类型的规则说明与示例")
    show_cmd.add_argument("--type", required=True)
    show_cmd.set_defaults(func=_cmd_show)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
