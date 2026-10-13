"""引注渲染。

渲染过程分两步：
1. 按 rules/*.yaml 中声明的 fields，用规范化器把原始输入加工成片段；
2. 按 segments 顺序拼接，只有 requires 字段全部非空时该段才参与拼接。

这样可选信息（译者、版次、页码、访问日期）缺失时不会留下悬空标点。
"""

from __future__ import annotations

import re

from .normalize import NORMALIZERS
from .rules import load_rules


class _SafeDict(dict):
    def __missing__(self, key):
        return ""


def build_context(rule: dict, data: dict, punctuation: dict) -> dict:
    ctx = dict(punctuation)
    for name, spec in (rule.get("fields") or {}).items():
        fn = NORMALIZERS[spec["type"]]
        options = dict(spec.get("options") or {})
        if "from" in spec:
            args = [data.get(key) for key in spec["from"]]
        else:
            args = [data.get(name)]
        ctx[name] = fn(*args, data=data, **options)
    for key, value in data.items():
        ctx.setdefault(key, "" if value is None else str(value))
    return ctx


def tidy(text: str) -> str:
    text = re.sub(r"[，,]\s*[。.]", "。", text)
    text = re.sub(r"[：:]\s*[。.]", "。", text)
    text = re.sub(r"，\s*，", "，", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def render(rule: dict, data: dict, punctuation: dict) -> str:
    ctx = build_context(rule, data, punctuation)
    parts = []
    for segment in rule["segments"]:
        requires = segment.get("requires") or []
        if not all(str(ctx.get(field, "")).strip() for field in requires):
            continue
        parts.append(segment["text"].format_map(_SafeDict(ctx)))
    return tidy("".join(parts))


def cite(type_name: str, data: dict, rules_dir=None) -> str:
    """生成一条脚注。

    >>> cite("book", {"authors": ["王名扬"], "title": "美国行政法",
    ...               "publisher": "北京大学出版社", "year": 2007, "pages": 18})
    '王名扬:《美国行政法》,北京大学出版社2007年版,第18页。'
    """
    rules, punctuation = load_rules(rules_dir)
    if type_name not in rules:
        raise KeyError(
            f"未知的文献类型: {type_name}；可用类型: {', '.join(sorted(rules))}"
        )
    return render(rules[type_name], data, punctuation)


def cite_many(items: list[dict], rules_dir=None) -> list[str]:
    """批量生成。每项需含 type 与 data 两个键。"""
    rules, punctuation = load_rules(rules_dir)
    results = []
    for item in items:
        type_name = item["type"]
        if type_name not in rules:
            raise KeyError(f"未知的文献类型: {type_name}")
        results.append(render(rules[type_name], item.get("data") or {}, punctuation))
    return results
