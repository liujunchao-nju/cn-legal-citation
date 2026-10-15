#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""技能自检：确认内嵌引擎可用、规则已加载、输出符合手册式样。

在技能被复制到新环境后先跑一次，能立刻区分「技能坏了」和「用户输入有问题」。

    python scripts/selfcheck.py
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
VENDOR = HERE.parent / "vendor"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from cn_legal_citation import __version__, check_one, cite, load_rules, parse_one  # noqa: E402

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    mark = "OK  " if condition else "FAIL"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def main() -> int:
    print(f"cn-legal-citation 技能自检（引擎版本 {__version__}）")
    print(f"内嵌引擎: {VENDOR}")
    print()

    try:
        rules, punctuation = load_rules()
        check("规则加载", len(rules) >= 60, f"仅加载到 {len(rules)} 类")
        print(f"       规则类型 {len(rules)} 类，标点配置 colon={punctuation['colon']!r}")
    except Exception as exc:
        check("规则加载", False, str(exc))
        print("\n自检未通过：引擎无法加载规则。")
        return 1

    sample = cite(
        "book",
        {
            "authors": ["王名扬"],
            "title": "美国行政法",
            "publisher": "中国法制出版社",
            "year": 1995,
            "pages": 18,
        },
    )
    check(
        "中文著作渲染",
        sample == "王名扬:《美国行政法》,中国法制出版社1995年版,第18页。",
        sample,
    )

    en = cite(
        "en_article",
        {
            "authors": ["Charles A. Reich"],
            "title": "The New Property",
            "journal": "Yale Law Journal",
            "volume": 73,
            "first_page": 733,
            "year": 1964,
        },
    )
    check(
        "英文论文渲染",
        en == "Charles A. Reich, The New Property, 73 Yale Law Journal 733 (1964).",
        en,
    )

    parsed = parse_one("王名扬:《美国行政法》,中国法制出版社1995年版,第18页。")
    check("逆向解析", parsed.ok and parsed["type"] == "book", str(parsed.get("reason")))

    result = check_one("张新宝：《侵权责任法》（第5版），中国人民大学出版社2020年版。")
    check("核查可识别全角标点", result["status"] == "style", result["status"])

    # 手册示例往返：抽 40 条验证解析后能逐字复现
    checked = 0
    bad = 0
    for name in ("book", "journal", "newspaper", "case", "legal", "online", "wechat"):
        for example in rules[name].get("examples") or []:
            checked += 1
            if check_one(example)["status"] != "ok":
                bad += 1
    check(f"手册示例往返（{checked} 条）", bad == 0, f"{bad} 条未能复现")

    print()
    if FAILURES:
        print(f"自检未通过，共 {len(FAILURES)} 项：{'、'.join(FAILURES)}")
        return 1
    print("自检全部通过，技能可正常使用。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
