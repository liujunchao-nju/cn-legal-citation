#!/usr/bin/env python
"""从规则文件生成技能的速查参考。

规则改了以后重跑一次，保证技能里的参考与引擎一致：

    python tools/gen_skill_refs.py [技能目录]
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cn_legal_citation import load_rules  # noqa: E402
from cn_legal_citation.normalize import NORMALIZERS  # noqa: E402

GROUP_ORDER = [
    ("中文纸质出版文献", ["book", "journal", "newspaper", "collection", "thesis", "conference", "archive"]),
    ("中文网络电子文献", ["online", "website", "wechat", "blog", "weibo", "app", "broadcast", "audiovisual"]),
    ("未发表文献", ["interview", "correspondence", "internal"]),
    (
        "法律文件与官方文件",
        [
            "legal",
            "regulation",
            "standard",
            "resolution",
            "report",
            "white_paper",
            "hk_macau_law",
            "taiwan_law",
            "foreign_law",
            "treaty",
            "un_document",
        ],
    ),
    ("司法案例与统计数据", ["case", "statistics"]),
    (
        "英文文献",
        [
            "en_book",
            "en_article",
            "en_periodical",
            "en_online",
            "en_law_uk",
            "en_law_us",
            "en_law_eu",
            "en_doc_un",
            "en_case",
            "en_case_uk",
            "en_case_intl",
        ],
    ),
    ("法文文献", ["fr_book", "fr_article", "fr_thesis", "fr_law", "fr_case", "fr_online"]),
    ("德文文献", ["de_book", "de_article", "de_law", "de_case"]),
    ("意大利文文献", ["it_book", "it_periodical", "it_law", "it_case", "it_roman"]),
    ("俄文文献", ["ru_book", "ru_article", "ru_periodical", "ru_law", "ru_case", "ru_online"]),
    ("日文文献", ["ja_book", "ja_article", "ja_law", "ja_case", "ja_official", "ja_online"]),
]


def clause_of(source: str) -> str:
    """从 source 字段里抽出条款号，做简要展示。"""
    marker = "第二版)"
    index = source.find(marker)
    text = source[index + len(marker) :] if index >= 0 else source
    return text.split("；")[0].strip()[:40]


def gen_types(rules: dict, path: pathlib.Path) -> None:
    lines = [
        "# 文献类型速查（69 类）",
        "",
        "用 `run.py show --type <类型名>` 可查看该类型的字段、依据条款与示例。",
        "",
    ]
    listed = set()
    for group, names in GROUP_ORDER:
        present = [n for n in names if n in rules]
        if not present:
            continue
        lines.append(f"## {group}")
        lines.append("")
        lines.append("| 类型名 | 名称 | 依据 |")
        lines.append("|---|---|---|")
        for name in present:
            rule = rules[name]
            lines.append(f"| `{name}` | {rule['label']} | {clause_of(rule.get('source', ''))} |")
            listed.add(name)
        lines.append("")
    missing = sorted(set(rules) - listed)
    if missing:
        lines.append("## 其他")
        lines.append("")
        for name in missing:
            lines.append(f"- `{name}` — {rules[name]['label']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def gen_fields(rules: dict, path: pathlib.Path) -> None:
    lines = [
        "# 字段速查",
        "",
        "把字段写成 JSON 传给 `run.py cite --type <类型> --file data.json`。",
        "字段缺失不会留下多余标点 —— 引擎只拼接条件成立的段落。",
        "",
        "## 通用字段",
        "",
        "| 字段 | 类型 | 说明 |",
        "|---|---|---|",
        "| `authors` | 列表 | 作者名。超过三位按手册省略为「甲等」 |",
        "| `nationality` | 字符串 | 外籍作者国籍，输出为 `[美]富勒` 形式 |",
        "| `dynasty` | 字符串 | 古籍作者朝代，输出为 `（清）沈家本` 形式 |",
        "| `authorship` | 字符串 | 著作方式：主编、编著、编译、整理、译注、口述 |",
        "| `title` | 字符串 | 文献名称，引擎自动加书名号 |",
        "| `edition` | 整数或字符串 | 版次：`5` 得 `(第5版)`，`修订版` 得 `(修订版)` |",
        "| `translator` | 字符串 | 译者，输出为 `郑戈译` |",
        "| `publisher` | 字符串 | 出版社。不写城市名 |",
        "| `year` | 整数 | 出版年份 |",
        "| `pages` | 整数/字符串/列表 | 页码：`18`、`\"73-75\"`、`[55, \"64-68\"]`、`\"9a\"` |",
        "",
        "## 分类型字段",
        "",
    ]
    for group, names in GROUP_ORDER:
        present = [n for n in names if n in rules]
        if not present:
            continue
        lines.append(f"### {group}")
        lines.append("")
        for name in present:
            rule = rules[name]
            fields = rule.get("fields") or {}
            spec = []
            for fname, fspec in fields.items():
                kind = fspec.get("type", "plain")
                spec.append(f"`{fname}`({kind})")
            lines.append(f"- **`{name}`** — {rule['label']}")
            lines.append(f"  - 字段：{'、'.join(spec)}")
            examples = rule.get("examples") or []
            if examples:
                lines.append(f"  - 示例：{examples[0]}")
        lines.append("")
    lines.append("## 规范化器")
    lines.append("")
    lines.append("字段值由规范化器加工，可在规则文件的 `fields` 里指定：")
    lines.append("")
    lines.append("| 规范化器 | 作用 |")
    lines.append("|---|---|")
    for name, fn in sorted(NORMALIZERS.items()):
        doc = (fn.__doc__ or "").strip().splitlines()
        lines.append(f"| `{name}` | {doc[0] if doc else ''} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    target = (
        pathlib.Path(sys.argv[1])
        if len(sys.argv) > 1
        else pathlib.Path.home() / ".workbuddy" / "skills" / "cn-legal-citation"
    )
    refs = target / "references"
    refs.mkdir(parents=True, exist_ok=True)
    rules, _ = load_rules()
    gen_types(rules, refs / "types.md")
    gen_fields(rules, refs / "fields.md")
    print(f"已写入 {refs / 'types.md'}")
    print(f"已写入 {refs / 'fields.md'}")
    print(f"文献类型 {len(rules)} 类")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
