"""字段规范化器。

每个规范化器把原始输入转成可直接拼接的中文片段，签名统一为
``fn(*args, data=None, **options) -> str``。

规则来源以《法学引注手册》（第二版，北京大学出版社 2020 年版）为准，
具体条款号标注在各 rules/*.yaml 的 source 字段中。
"""

from __future__ import annotations

import re
from typing import Any

ET_AL = "等"


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def plain(value=None, data=None, **options) -> str:
    """原样输出。用于出版社、标题、期刊名等无需加工的文本。"""
    return _clean(value)


def author_list(
    value=None, data=None, max_before_et_al: int = 3, et_al: str = ET_AL, **options
) -> str:
    """作者列表。

    - 多名作者用顿号连接；
    - 作者数超过 max_before_et_al 时只标第一作者并加“等”
      （《法学引注手册》第二版：三人以上只标注第一作者）；
      外文规则可在 YAML 中把 et_al 设为 " et al."；
    - 存在 nationality 字段时，首位作者前加国别标记，如“[美]富勒”。
    """
    names = [n for n in _as_list(value) if n.strip()]
    if not names:
        return ""
    nationality = _clean((data or {}).get("nationality"))
    if nationality:
        names = [f"[{nationality}]{names[0]}"] + names[1:]
    if len(names) > max_before_et_al:
        return f"{names[0]}{et_al}"
    return "、".join(names)


def authorship(value=None, data=None, **options) -> str:
    """著作身份。默认为独著，不标注；非独著注明“主编”“编著”“编译”等。"""
    return _clean(value)


def edition(value=None, data=None, **options) -> str:
    """版次。输入 4 得到“(第4版)”，输入“修订版”得到“(修订版)”。"""
    s = _clean(value)
    if not s:
        return ""
    if s.startswith("第") or s.endswith("版"):
        return f"({s})"
    return f"(第{s}版)"


def translator(value=None, data=None, **options) -> str:
    """译者。输出形如“郑戈译”。"""
    s = _clean(value)
    return f"{s}译" if s else ""


def publisher_year(value=None, data=None, **options) -> str:
    """出版社与出版年。

    手册第二版明确：图书的出版信息写明出版社，不写出版社所在城市。
    """
    press = _clean(value)
    if not press:
        return ""
    year = _clean((data or {}).get("year"))
    return f"{press}{year}年版" if year else press


def page_range(value=None, data=None, **options) -> str:
    """页码。18 ->“第18页”；(18, 75) 或“18-75” ->“第18-75页”。"""
    if value is None or value == "":
        return ""
    if isinstance(value, (list, tuple)):
        if len(value) == 1:
            return f"第{value[0]}页"
        return f"第{value[0]}-{value[1]}页"
    s = str(value).strip().replace("—", "-").replace("－", "-")
    if not s:
        return ""
    # 非数字定位（如“第二章‘英美判例法’”）原样保留，不加“第…页”
    if not re.match(r"^\d", s):
        return s
    return f"第{s}页"


def date_cn(year=None, month=None, day=None, data=None, **options) -> str:
    """中文日期。2000, 5, 21 ->“2000年5月21日”。"""
    s = ""
    if year:
        s += f"{year}年"
    if month:
        s += f"{int(month)}月"
    if day:
        s += f"{int(day)}日"
    return s


def statute_ref(value=None, data=None, **options) -> str:
    """法条序号。

    接受整数（->“第32条”）或字典
    ``{"article": 1224, "paragraph": 1, "item": 2}``
    ->“第1224条第1款第2项”。条文序号一律用阿拉伯数字。
    """
    if isinstance(value, dict):
        s = f"第{value['article']}条"
        if value.get("paragraph"):
            s += f"第{value['paragraph']}款"
        if value.get("item"):
            s += f"第{value['item']}项"
        return s
    s = _clean(value)
    return f"第{s}条" if s else ""


def case_number(value=None, data=None, **options) -> str:
    """案号。字符串原样输出；字典按“(1998)海行初字第142号”组装。

    code 填“海行初”或“海行初字”均可，末尾的“字”会自动去重。
    """
    if isinstance(value, dict):
        code = _clean(value.get("code"))
        suffix = "" if code.endswith("字") else "字"
        return f"({value['year']}){code}{suffix}第{value['number']}号"
    return _clean(value)


def document_number(value=None, data=None, **options) -> str:
    """规范性文件文号，如“法释〔2018〕1号”。原样输出。"""
    return _clean(value)


NORMALIZERS = {
    "plain": plain,
    "author_list": author_list,
    "authorship": authorship,
    "edition": edition,
    "translator": translator,
    "publisher_year": publisher_year,
    "page_range": page_range,
    "date_cn": date_cn,
    "statute_ref": statute_ref,
    "case_number": case_number,
    "document_number": document_number,
}
