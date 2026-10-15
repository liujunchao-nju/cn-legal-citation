"""字段规范化器。

每个规范化器把原始输入转成可直接拼接的片段，签名统一为
``fn(*args, data=None, **options) -> str``。

规则来源以《法学引注手册》（第二版，北京大学出版社 2025 年版）为准，
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
    """原样输出。用于标题、期刊名、出版社等无需加工的文本。"""
    return _clean(value)


def author_list(
    value=None,
    data=None,
    max_before_et_al: int = 3,
    et_al: str = ET_AL,
    sep: str = "、",
    sep_two: str | None = None,
    sep_last: str | None = None,
    keep_before_et_al: int = 1,
    **options,
) -> str:
    """作者列表。

    - 多名作者的连接符可在 YAML 中配置：中文默认顿号；英文 ``&``；
      法文 ``et``；德文 ``/``；俄文 ``и``；日文 ``=``。
      ``sep`` 用于中间位置，``sep_two`` 用于仅两位作者，
      ``sep_last`` 用于三位作者时最后一位之前，未设置时沿用 ``sep``。
    - 作者数超过 max_before_et_al 时只保留前 keep_before_et_al 位并加 et_al
      （第 35 条：两人或三人一一列明；人数众多可列一到两位后加"等"；
      俄文示例保留前两位后加"и др."，故俄文规则设 keep_before_et_al=2）；
    - 存在 nationality 字段时，首位作者前加国别标记，如"[美]富勒"
      （第 33 条：方括号注国籍，同一国籍只标第一人）；
    - 存在 dynasty 字段时，首位作者前加朝代标记，如"（清）沈家本"
      （第 34 条：古籍作者用圆括号注明朝代）。
    """
    names = [n for n in _as_list(value) if n.strip()]
    if not names:
        return ""
    data = data or {}
    nationality = _clean(data.get("nationality"))
    if nationality:
        names = [f"[{nationality}]{names[0]}"] + names[1:]
    dynasty = _clean(data.get("dynasty"))
    if dynasty:
        names = [f"({dynasty}){names[0]}"] + names[1:]
    if len(names) > max_before_et_al:
        keep = max(1, min(keep_before_et_al, len(names)))
        if keep == 1:
            return f"{names[0]}{et_al}"
        return f"{sep.join(names[:keep])}{et_al}"
    if len(names) == 1:
        return names[0]
    two = sep_two if sep_two is not None else sep
    last = sep_last if sep_last is not None else sep
    if len(names) == 2:
        return f"{names[0]}{two}{names[1]}"
    return f"{two.join(names[:-1])}{last}{names[-1]}"


def authorship(value=None, data=None, space: bool = False, **options) -> str:
    """著作身份。原创作品省略"著"；主编、编著、编译、整理、译注等照写（第 27、28 条）。

    ``space=True`` 时输出前加一个空格，用于英文 "chief ed."、法文 "dir."
    等写在姓名之后的著作方式。
    """
    s = _clean(value)
    if not s:
        return ""
    return f" {s}" if space else s


def issue_info(year=None, volume=None, issue=None, data=None, **options) -> str:
    """期刊卷期与出版年（第 43、44 条）。

    - 有卷次：``第47卷第4期（2018年）``（年份括注于后）；
    - 无卷次：``1993年第1期``（年份在前）；
    - issue 传 "2辑" 等非数字值时原样拼接（``第4卷第2辑``）。
    """
    volume = _clean(volume)
    issue = _clean(issue)
    year = _clean(year)
    issue_part = ""
    if issue:
        issue_part = f"第{issue}期" if re.match(r"^\d+$", issue) else issue
    if volume:
        s = f"第{volume}卷{issue_part}"
        if year:
            s += f"（{year}年）"
        return s
    return f"{year}年{issue_part}" if year else issue_part


def eu_number(value=None, data=None, **options) -> str:
    """欧盟法律编号（第 110 条）。

    以方括号起始的（《欧盟公报》引注，如 "[2008] OJ C115/13"）用空格衔接；
    其余（法规编号，如 "(EU) 2016/679"）用逗号衔接。
    """
    s = _clean(value)
    if not s:
        return ""
    return f" {s}" if s.startswith("[") else f", {s}"


def journal_ref(value=None, data=None, **options) -> str:
    """英文学术期刊的卷次与页码（第 105、107 条）。

    第一种：卷数与首页页码分列期刊名前后，特定内容页码以逗号隔开，
    如 "73 Yale Law Journal 733, 737-738"（出版年份由 segments 括注）；
    第二种：期刊名之后写卷数、页码，
    如 "Stanford Law Review, Vol. 56:1, p. 1-73"。
    """
    journal = _clean(value)
    data = data or {}
    volume = _clean(data.get("volume"))
    first_page = _clean(data.get("first_page"))
    pincite = _clean(data.get("pincite"))
    info = _clean(data.get("volume_info"))
    pages = _clean(data.get("pages"))
    if not journal:
        return ""
    if volume and first_page:
        s = f"{volume} {journal} {first_page}"
        if pincite:
            s += f", {pincite}"
        return s
    if info:
        s = f"{journal}, {info}"
        if pages:
            s += f", {pages}"
        return s
    return journal


def site_date(value=None, data=None, **options) -> str:
    """英文网络文献的网站名与上传日期（第 100 条）。

    网站名后以圆括号括注上传日期；无上传日期时只输出网站名。
    """
    site = _clean(value)
    if not site:
        return ""
    date = _clean((data or {}).get("date"))
    return f"{site} ({date})" if date else site


def court_year(court=None, data=None, **options) -> str:
    """英文案例的法院与年份括注（第 114 条）。

    法院与年份同时存在时为 ``(D.C. Cir. 1982)``，仅年份为 ``(1984)``，
    仅法院（尚未宣判的案件）为 ``(W.D. North Carolina)``。
    """
    court = _clean(court)
    year = _clean((data or {}).get("year"))
    if court and year:
        return f"({court} {year})"
    if year:
        return f"({year})"
    if court:
        return f"({court})"
    return ""


def report_list(value=None, data=None, **options) -> str:
    """案例报告引注列表。同时援引几个案例报告系统时用逗号连接（第 114 条第 2 项）。"""
    if isinstance(value, (list, tuple)):
        return ", ".join(_clean(v) for v in value if _clean(v))
    return _clean(value)


def ru_issue(issue=None, data=None, **options) -> str:
    """俄文期刊的期次衔接（第 136、137 条）。

    期刊期次写作 "No 3"（逗号衔接）；文集卷次写作 "(2)"（空格衔接）。
    """
    s = _clean(issue)
    if not s:
        return ""
    return f", {s}" if s.lower().startswith("no") else f" {s}"


def ja_title(value=None, data=None, **options) -> str:
    """日文文献名称的书名号（第 143 条）。

    书名用双引号『』；编辑作品中的文章名用単引号「」
    （数据中传 ``"title_style": "article"``）。
    """
    s = _clean(value)
    if not s:
        return ""
    if _clean((data or {}).get("title_style")) == "article":
        return f"「{s}」"
    return f"『{s}』"


def edition(value=None, data=None, **options) -> str:
    """版次。输入 4 得到"(第4版)"，输入"修订版"得到"(修订版)"（第 40 条：
    初版不标示，再版在书名后括注版次）。"""
    s = _clean(value)
    if not s:
        return ""
    if s.startswith("第") or s.endswith("版"):
        return f"({s})"
    return f"(第{s}版)"


def translator(value=None, data=None, **options) -> str:
    """译者。输出形如"郑戈译"（第 29 条：译者位于文献名称之后、出版信息之前）。"""
    s = _clean(value)
    return f"{s}译" if s else ""


def publisher_year(value=None, data=None, **options) -> str:
    """出版社与出版年。

    手册第二版第 41 条：写明出版社，不写出版社所在城市；只写年份，不写月份。
    """
    press = _clean(value)
    if not press:
        return ""
    year = _clean((data or {}).get("year"))
    return f"{press}{year}年版" if year else press


def _page_fragment(value: Any) -> str:
    return str(value).strip().replace("—", "-").replace("－", "-")


def page_range(value=None, data=None, **options) -> str:
    """页码（第 48 条）。

    - ``18`` 或 ``"18"`` -> "第18页"；
    - ``(18, 75)`` 或 ``"18-75"`` -> "第18-75页"（连续起止用短横线）；
    - ``[55, "64-68"]`` 或 ``"55、64-68"`` -> "第55、64-68页"（不连续页码用顿号）；
    - ``"9a"`` -> "第9页a"（古籍刻本两面用 a、b 标明）；
    - 非数字定位（如"第二章'英美判例法'"）原样保留，不加"第…页"。
    """
    if value is None or value == "":
        return ""
    if isinstance(value, (list, tuple)):
        parts = [p for p in (_page_fragment(v) for v in value) if p]
        if not parts:
            return ""
        if len(parts) == 2 and all(re.match(r"^\d+$", p) for p in parts):
            return f"第{parts[0]}-{parts[1]}页"
        return "第" + "、".join(parts) + "页"
    s = _page_fragment(value)
    if not s:
        return ""
    if not re.match(r"^\d", s):
        return s
    m = re.match(r"^(\d+)\s*([ab])$", s)
    if m:
        return f"第{m.group(1)}页{m.group(2)}"
    return f"第{s}页"


def date_cn(year=None, month=None, day=None, data=None, **options) -> str:
    """中文日期。2000, 5, 21 ->"2000年5月21日"。"""
    s = ""
    if year:
        s += f"{year}年"
    if month:
        s += f"{int(month)}月"
    if day:
        s += f"{int(day)}日"
    return s


def statute_ref(value=None, data=None, **options) -> str:
    """法条序号（第 70 条：条、款、项、目序数用阿拉伯数字，括号省略）。

    接受整数（->"第32条"）或字典
    ``{"article": 1224, "paragraph": 1, "item": 2}``
    ->"第1224条第1款第2项"；字典亦支持 ``sub_item``（->"目"）与
    ``item``/``paragraph`` 的省略。字符串中已含"条"的（如"17条之一"）
    自动补"第"字。
    """
    if isinstance(value, dict):
        s = f"第{value['article']}条"
        if value.get("paragraph"):
            s += f"第{value['paragraph']}款"
        if value.get("item"):
            s += f"第{value['item']}项"
        if value.get("sub_item"):
            s += f"第{value['sub_item']}目"
        return s
    s = _clean(value)
    if not s:
        return ""
    if "条" in s:
        return s if s.startswith("第") else f"第{s}"
    return f"第{s}条"


def case_number(value=None, data=None, **options) -> str:
    """案号（第 89 条：案号中的年份加圆括号，案号置于文书类型之前）。

    字符串原样输出（2016 年启用的现行案号不带"字""第"，从裁判文书原文）；
    字典按"(1998)海行初字第142号"组装，code 填"海行初"或"海行初字"均可，
    末尾的"字"会自动去重。
    """
    if isinstance(value, dict):
        code = _clean(value.get("code"))
        suffix = "" if code.endswith("字") else "字"
        return f"({value['year']}){code}{suffix}第{value['number']}号"
    return _clean(value)


def document_number(value=None, data=None, **options) -> str:
    """规范性文件文号（第 74 条）。

    文号在文件名称之后，默认用圆括号括注；数据中传
    ``"number_style": "comma"`` 则改为逗号分隔（叙述中提及具体内容时
    为行文紧凑，用括号括注）；传 ``"none"`` 则只输出文号本身。
    发文字号中的年份用六角括号〔〕。
    """
    s = _clean(value)
    if not s:
        return ""
    style = _clean((data or {}).get("number_style")) or "paren"
    if style == "comma":
        return f",{s}"
    if style == "none":
        return s
    return f"({s})"


def titled(value=None, data=None, **options) -> str:
    """法律文件名称（第 67 条：名称加书名号）。

    数据中传 ``"plain_name": true`` 时不加书名号，用于约定俗成的简称，
    如"美国宪法第十四修正案"。
    """
    s = _clean(value)
    if not s:
        return ""
    if (data or {}).get("plain_name"):
        return s
    return f"《{s}》"


BARE_MARKERS = (
    "authors",
    "authorship",
    "publisher",
    "pages",
    "volume_note",
    "collator",
    "translator",
    "container_title",
)


def tail_period(value=None, data=None, **options) -> str:
    """结尾句号。

    仅有文献名称（如常用典籍"《论语·述而》"）的极简引用不附加句号；
    出现作者、出版信息、页码等任一要素时补句号（第 27-49 条体例）。
    """
    data = data or {}
    for key in BARE_MARKERS:
        if _clean(data.get(key)):
            return "。"
    return ""


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
    "titled": titled,
    "issue_info": issue_info,
    "eu_number": eu_number,
    "journal_ref": journal_ref,
    "site_date": site_date,
    "court_year": court_year,
    "report_list": report_list,
    "ru_issue": ru_issue,
    "ja_title": ja_title,
    "tail_period": tail_period,
}
