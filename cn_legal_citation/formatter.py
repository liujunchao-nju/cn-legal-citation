"""引注渲染。

渲染过程分三步：
1. 按 rules/*.yaml 中声明的 fields，用规范化器把原始输入加工成片段；
2. 按 segments 顺序拼接，只有 requires 字段全部非空时该段才参与拼接；
   同一 ``mutex`` 组内只取第一个条件成立的段（用于书名号与文章号等
   互斥体例，如日文的『』与「」）；
3. 折叠因字段缺失产生的重复标点。

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
    """折叠标点。

    除中文全角标点的重复外，也处理外文加句点体例中出现的 ``s..``、``ff..``
    （段落定位符本身以句点结尾时不再追加句点），以及空段产生的悬空标点。
    """
    text = re.sub(r"，\s*[。.]", "。", text)
    text = re.sub(r"：\s*[。.]", "。", text)
    text = re.sub(r"，\s*，", "，", text)
    text = re.sub(r"^[，,]\s*", "", text)
    # 连续标点折叠：",," -> ","，".." -> "."，"。, " -> "。"，"。." -> "。"
    text = re.sub(r"\.\.+", ".", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"。\s*[。.]+", "。", text)
    text = re.sub(r"。\s*,", "。", text)
    text = re.sub(r"\s+([,.;])", r"\1", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def satisfied(segment: dict, ctx: dict) -> bool:
    """段的成立条件：``requires`` 字段全部非空，``absent`` 字段全部为空。"""
    for field in segment.get("requires") or []:
        if not str(ctx.get(field, "")).strip():
            return False
    for field in segment.get("absent") or []:
        if str(ctx.get(field, "")).strip():
            return False
    return True


def render(rule: dict, data: dict, punctuation: dict) -> str:
    ctx = build_context(rule, data, punctuation)
    segments = rule["segments"]

    # 先确定每个 mutex 组内实际成立的段（同组只取第一个成立的）
    group_selected: dict[str, int] = {}
    for index, segment in enumerate(segments):
        mutex = segment.get("mutex")
        if mutex and mutex not in group_selected and satisfied(segment, ctx):
            group_selected[mutex] = index

    parts = []
    for index, segment in enumerate(segments):
        mutex = segment.get("mutex")
        if mutex and group_selected.get(mutex) != index:
            continue
        if not satisfied(segment, ctx):
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