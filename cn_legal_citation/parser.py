"""脚注文本 → 字段的逆向解析。

项目原本只有正向渲染（字段 → 脚注）。要让技能能处理「已有的论文」，
必须有逆向能力：把作者已经写好的脚注拆回字段，交给引擎重新渲染，
再比对差异。

设计原则：

1. 规则解析优先。常见中文类型（图书、期刊、报纸、判例、法条、网络文献
   等）与英文著作论文用模式匹配直接拆解，确定性高、可测试。
2. 不猜。拆不出来就如实返回 ``None``，由调用方转人工或交给模型补字段。
   宁可报「未能解析」，也不要给一个看起来合理但错误的字段组合。
3. 解析结果必须可验证。引擎会拿解析出的字段重新渲染，与原文逐字比对，
   比对不通过就说明字段填错了 —— 这是本模块唯一的正确性保障。

所有模式以《法学引注手册》（第二版）的式样为准，条款号见各规则文件的
source 字段。法、德、意、俄、日各语种体例复杂，本期不作规则解析，
交由模型补字段。
"""

from __future__ import annotations

import re

__all__ = ["parse", "parse_one", "ParseResult", "normalize"]

_LEAD_WORDS = ("参见", "又见", "另见", "见")

_PUNCT_MAP = {
    "，": ",",
    "：": ":",
    "；": ";",
    "（": "(",
    "）": ")",
    "“": '"',
    "”": '"',
    "「": '"',
    "」": '"',
    "『": '"',
    "』": '"',
}

# 域外法律的国别标记（用于与中文著作区分）
_COUNTRIES = (
    "中国|美国|英国|德国|法国|日本|意大利|俄罗斯|瑞士|西班牙|葡萄牙|荷兰|"
    "奥地利|韩国|印度|巴西|加拿大|澳大利亚|新西兰|新加坡|泰国|越南|马来西亚|"
    "印度尼西亚|菲律宾|埃及|南非|瑞典|挪威|丹麦|芬兰|比利时|希腊|波兰|匈牙利|"
    "捷克|墨西哥|阿根廷|智利|以色列|土耳其|伊朗|沙特阿拉伯|阿联酋"
)

# 标题类字段里不应被吃进"作者"的词
_TITLE_SIGNS = ("报告书", "白皮书")


class ParseResult(dict):
    """解析结果。

    ``type`` 为 None 表示未能解析；``reason`` 说明原因；
    ``data`` 为字段字典，可直接喂给 ``cite(type, data)``。
    """

    @property
    def ok(self) -> bool:
        return bool(self.get("type"))


def normalize(text: str) -> str:
    """把全角标点折叠为半角，便于统一匹配。

    注意：手册印刷示例本身用半角，但用户实际写作常见全角，
    因此解析入口一律先归一化。
    """
    return "".join(_PUNCT_MAP.get(ch, ch) for ch in text).strip()


def strip_lead_and_tail(text: str) -> tuple[str, str]:
    """剥离引领词，返回 ``(正文, 引领词)``。"""
    lead = ""
    body = text.strip()
    for word in _LEAD_WORDS:
        if body.startswith(word):
            lead = word
            body = body[len(word) :]
            break
    return body.strip(), lead


def restore_quotes(text: str) -> str:
    """把配对出现的直角双引号还原为中文引号。

    ``normalize`` 为了统一匹配会把中文引号折成 ``"``，但标题、账号名等
    字段是用户内容，直接带直角引号渲染出来就不对了。这里按出现顺序
    交替还原为左右引号。
    """
    if text.count('"') < 2:
        return text
    out = []
    opening = True
    for ch in text:
        if ch == '"':
            out.append("“" if opening else "”")
            opening = not opening
        else:
            out.append(ch)
    return "".join(out)


def restore_data_quotes(data: dict) -> dict:
    """对解析结果里的所有字符串字段还原中文引号。"""
    return {
        key: restore_quotes(value) if isinstance(value, str) else value
        for key, value in data.items()
    }


# --------------------------------------------------------------------------
# 公共小工具
# --------------------------------------------------------------------------

_NATIONALITY_RE = re.compile(r"^\[([^\]]+)\]")
_DYNASTY_RE = re.compile(r"^\((?P<dynasty>[\u4e00-\u9fff]{1,3})\)(?=[\u4e00-\u9fff])")
_AUTHORSHIP_RE = re.compile(r"(主编|编著|编译|整理|译注|口述|编)$")
_AUTHORITY_HINT = re.compile(r"(发布|制定|印发|颁布|批准)的?$")

# 文号：含阿拉伯数字并带"号"字
_DOCNUM = r"[^,。]*?\d+[^,。]*?号"
# 条文序号：第X条/节 起头，可继续带 款/项/目/小节
_ARTICLE = (
    r"第[0-9一二三四五六七八九十百零]+[条章节]"
    r"(?:之[一二三四五六七八九十]+)?"
    r"(?:第[0-9一二三四五六七八九十百零]+[款项目])*"
    r"(?:第[0-9一二三四五六七八九十百零]+小节)?"
)
# 出版社：不写死"出版社"三字（商务印书馆、中华书局均不含该串）
_PUBLISHER = r"(?P<pub>[^,。]{2,30}?)(?P<y>\d{4})年版"


def split_authors(chunk: str) -> dict:
    """把"王名扬""[美]富勒""(清)沈家本""高鸿钧、程汉大主编"拆成字段。"""
    data: dict = {}
    s = chunk.strip().rstrip(":,")
    if not s:
        return data
    m = _NATIONALITY_RE.match(s)
    if m:
        data["nationality"] = m.group(1)
        s = s[m.end() :]
    m = _DYNASTY_RE.match(s)
    if m:
        data["dynasty"] = m.group("dynasty")
        s = s[m.end() :]
    m = _AUTHORSHIP_RE.search(s)
    if m:
        data["authorship"] = m.group(1)
        s = s[: m.start()]
    names = [n.strip() for n in re.split(r"[、,]", s) if n.strip()]
    if names:
        data["authors"] = names
    return data


def _page_value(token: str) -> str | int:
    """把"第73-75页"还原成 18 / "18-75" / "9a" 等页码输入值。

    非页码定位（如"第二章'英美判例法'"）原样返回。
    """
    s = token.strip().rstrip("。")
    m = re.match(r"^第(?P<num>[^,]*?)页(?P<side>[ab])?$", s)
    if m:
        s = m.group("num") + (m.group("side") or "")
        if re.match(r"^\d+$", s):
            return int(s)
        return s
    return s


# --------------------------------------------------------------------------
# 一、司法案例
# --------------------------------------------------------------------------


def _try_case(body: str):
    m = re.search(r"人民法院案例库(?P<num>[0-9A-Za-z\-]+)", body)
    if m:
        data = {"database_number": m.group("num")}
        name = body[: m.start()].rstrip(",，")
        if name:
            data["case_name"] = name
        return "case", data

    m = re.search(r"载《最高人民法院公报》(?P<y>\d{4})年第(?P<i>\d+)期", body)
    if m:
        data = {
            "gazette_year": int(m.group("y")),
            "gazette_issue": int(m.group("i")),
        }
        name = body[: m.start()].rstrip(",，")
        if name:
            data["case_name"] = name
        return "case", data

    m = re.search(
        r"(?P<organ>最高人民法院|最高人民检察院)指导案例(?P<no>\d+)号"
        r"(?:\((?P<y>\d{4})年\))?",
        body,
    )
    if m:
        data = {
            "guiding_organ": m.group("organ"),
            "guiding_no": int(m.group("no")),
        }
        if m.group("y"):
            data["guiding_year"] = int(m.group("y"))
        name = body[: m.start()].rstrip(",，")
        if name:
            data["case_name"] = name
        return "case", data

    m = re.search(
        r"载(?P<compiler>[^:]+)编:《(?P<ctitle>[^》]+)》"
        r",(?P<cpub>[^,]+?)(?P<cy>\d{4})年版,案例(?P<cno>[^,。]+)",
        body,
    )
    if m:
        data = {
            "compiler": m.group("compiler"),
            "compilation_title": m.group("ctitle"),
            "compilation_publisher": m.group("cpub"),
            "compilation_year": int(m.group("cy")),
            "case_no": m.group("cno"),
        }
        name = body[: m.start()].rstrip(",，")
        if name:
            data["case_name"] = name
        return "case", data

    m = re.search(
        r"参见(?P<rauthor>[^:]+):《(?P<rtitle>[^》]+)》"
        r",载《(?P<rpaper>[^》]+)》"
        r"(?P<ry>\d{4})年(?P<rm>\d+)月(?P<rd>\d+)日"
        r",第(?P<rpage>\d+)版",
        body,
    )
    if m:
        data = {
            "report_author": m.group("rauthor"),
            "report_title": m.group("rtitle"),
            "report_newspaper": m.group("rpaper"),
            "report_date": f"{m.group('ry')}年{int(m.group('rm'))}月{int(m.group('rd'))}日",
            "report_page": int(m.group("rpage")),
        }
        name = body[: m.start()].rstrip(",，")
        if name:
            data["case_name"] = name
        return "case", data

    m = re.search(
        r"(?P<court>[^,]*?(?:人民法院|法院|证监会|仲裁委员会|司法厅|司法局))"
        r"(?P<num>\(\d{4}\)[^,]*?号)"
        r"(?P<dtype>[^,。]*?(?:判决书|裁定书|决定书|调解书))",
        body,
    )
    if m:
        data = {
            "court": m.group("court"),
            "case_number": m.group("num"),
            "document_type": m.group("dtype"),
        }
        name = body[: m.start()].rstrip(",，")
        if name:
            data["case_name"] = name
        tail = body[m.end() :].strip(",，。")
        dm = re.match(r"(?P<y>\d{4})年(?P<m>\d+)月(?P<d>\d+)日$", tail)
        if dm:
            data.update(
                year=int(dm.group("y")),
                month=int(dm.group("m")),
                day=int(dm.group("d")),
            )
        return "case", data
    return None


# --------------------------------------------------------------------------
# 二、法律文件与官方文件
# --------------------------------------------------------------------------


def _try_legal(body: str):
    # 版本年份：《公司法》(2005年修订)第16条、《行政诉讼法》(1989年)第54条
    m = re.match(
        r"^(?P<issuing>[^《]*?)《(?P<name>[^》]+)》"
        r"\((?P<revision>\d{4}年(?:修订|修正|修改)?)\)"
        r",?(?P<art>" + _ARTICLE + r")。?$",
        body,
    )
    if m:
        data: dict = {
            "name": m.group("name"),
            "revision": m.group("revision"),
            "article": m.group("art"),
        }
        if m.group("issuing"):
            data["issuing_authority"] = m.group("issuing")
        return "legal", data

    # 有出处的规范性文件
    m = re.match(
        r"^(?P<issuing>[^《]*?)《(?P<name>[^》]+)》"
        r"\((?P<docnum>[^)]+)\)"
        r"(?:,(?P<art>" + _ARTICLE + r"))?"
        r",载(?P<sc>[^:]+)编:《(?P<st>[^》]+)》"
        r",(?P<spub>[^,]+?)(?P<sy>\d{4})年版,第(?P<spg>\d+)页。?$",
        body,
    )
    if m:
        data = {
            "name": m.group("name"),
            "document_number": m.group("docnum"),
            "source_compiler": m.group("sc"),
            "source_title": m.group("st"),
            "source_publisher": m.group("spub"),
            "source_year": int(m.group("sy")),
            "source_pages": int(m.group("spg")),
        }
        if m.group("issuing"):
            data["issuing_authority"] = m.group("issuing")
        if m.group("art"):
            data["article"] = m.group("art")
        return "regulation", data

    # 名称 + 官网链接
    m = re.match(
        r"^(?P<issuing>[^《]*?)《(?P<name>[^》]+)》,"
        r"(?P<date>\d{4}年\d+月\d+日),"
        r"(?P<url>https?://\S+)。?$",
        body,
    )
    if m:
        data = {"name": m.group("name"), "date": m.group("date"), "url": m.group("url")}
        if m.group("issuing"):
            data["issuing_authority"] = m.group("issuing")
        return "regulation", data

    # 名称 + 括号文号 (+ 条/节)
    m = re.match(
        r"^(?P<issuing>[^《]*?)《(?P<name>[^》]+)》"
        r"\((?P<docnum>[^)]+)\)"
        r",?(?P<art>" + _ARTICLE + r")?。?$",
        body,
    )
    if m:
        data = {"name": m.group("name"), "document_number": m.group("docnum")}
        if m.group("issuing"):
            data["issuing_authority"] = m.group("issuing")
        if m.group("art"):
            data["article"] = m.group("art")
        return "regulation", data

    # 名称 + 逗号文号
    m = re.match(
        r"^(?P<issuing>[^《]*?)《(?P<name>[^》]+)》,"
        r"(?P<docnum>" + _DOCNUM + r")"
        r"(?:,(?P<art>" + _ARTICLE + r"))?。?$",
        body,
    )
    if m:
        data = {
            "name": m.group("name"),
            "document_number": m.group("docnum"),
            "number_style": "comma",
        }
        if m.group("issuing"):
            data["issuing_authority"] = m.group("issuing")
        if m.group("art"):
            data["article"] = m.group("art")
        return "regulation", data

    # 法律性质的决定：《决定》,1991年9月4日……会议通过
    m = re.match(
        r"^(?P<issuing>[^《]*?)《(?P<name>[^》]+)》,"
        r"(?P<adoption>\d{4}年.+?(?:通过|批准))。?$",
        body,
    )
    if m:
        data = {"name": m.group("name"), "adoption_info": m.group("adoption")}
        if m.group("issuing"):
            data["issuing_authority"] = m.group("issuing")
        return "legal", data

    # 纯条文：《民法典》第1224条第1款第2项
    m = re.match(
        r"^(?P<issuing>[^《]*?)《(?P<name>[^》]+)》"
        r"(?P<art>" + _ARTICLE + r")。?$",
        body,
    )
    if m:
        data = {"name": m.group("name"), "article": m.group("art")}
        if m.group("issuing"):
            data["issuing_authority"] = m.group("issuing")
        return "legal", data
    return None


def _try_hk_macau(body: str):
    if not re.search(r"香港法例|法律公告|澳门特别行政区|香港特别行政区", body):
        return None
    m = re.match(
        r"^《(?P<name>[^》]+)》"
        r"(?:\((?P<chapter>[^)]+)\))?"
        r"(?:,(?P<article>第[^,。]+?条[^,。]*))?"
        r"(?:,(?P<announcement>\d{4}年第\d+号法律公告))?"
        r"(?:,(?P<url>https?://\S+))?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {"name": m.group("name")}
    for key in ("chapter", "article", "announcement"):
        if m.group(key):
            data[key] = m.group(key)
    if m.group("url"):
        data["url"] = m.group("url").rstrip("。")
    return "hk_macau_law", data


def _try_taiwan_law(body: str):
    m = re.match(
        r"^(?P<note>我国台湾地区|台湾地区)"
        r'["“]?(?P<name>[^"”。]+)["”]?。?$',
        body,
    )
    if not m:
        return None
    return "taiwan_law", {"note": m.group("note"), "name": m.group("name")}


def _try_foreign_law(body: str):
    # 约定俗成的简称不加书名号：美国宪法第十四修正案
    m = re.match(
        r"^(?P<country>" + _COUNTRIES + r")(?P<name>[^《》]{2,20}修正案)。?$",
        body,
    )
    if m:
        return "foreign_law", {
            "country": m.group("country"),
            "name": m.group("name"),
            "plain_name": True,
        }

    m = re.match(
        r"^(?P<country>" + _COUNTRIES + r")"
        r"(?P<year_before>\d{4}年)?"
        r"《(?P<name>[^》]+)》"
        r"(?:\((?P<tail>[^)]+)\))?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {"country": m.group("country"), "name": m.group("name")}
    if m.group("year_before"):
        data["year_before"] = m.group("year_before")
    if m.group("tail"):
        tail = m.group("tail")
        if re.match(r"^\d{4}年$", tail):
            data["year"] = tail
        else:
            data["original"] = tail
    return "foreign_law", data


def _try_treaty(body: str):
    m = re.match(
        r"^(?P<org>联合国|国际|世界|欧洲联盟|世界贸易组织|国际劳工组织)?"
        r"《(?P<name>[^》]*(?:公约|条约|协定|议定书|宪章|规约))》"
        r"(?:\((?P<original>[^)]+)\))?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {"name": m.group("name")}
    if m.group("org"):
        data["organization"] = m.group("org")
    if m.group("original"):
        data["original"] = m.group("original")
    return "treaty", data


def _try_un_document(body: str):
    m = re.match(
        r"^《(?P<name>[^》]+)》,"
        r"(?P<organ>联合国[^,]*?)(?P<doc_type>决议|报告),"
        r"(?P<number>[^,。]+?)"
        r"(?:,(?P<date>\d{4}年\d+月\d+日)(?P<action>通过)?)?"
        r"(?:,(?P<url>https?://\S+))?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "name": m.group("name"),
        "organ": m.group("organ"),
        "doc_type": m.group("doc_type"),
        "number": m.group("number"),
    }
    if m.group("date"):
        data["date"] = m.group("date")
        data["action"] = m.group("action") or ""
    if m.group("url"):
        data["url"] = m.group("url").rstrip("。")
    return "un_document", data


def _try_standard(body: str):
    m = re.match(
        r"^(?P<authority>[^《]+?)《(?P<name>[^》]+)》,"
        r"(?P<number>[A-Z][A-Za-z]*(?:/[A-Za-z]+)?\s*\d+[^,。]*)。?$",
        body,
    )
    if not m:
        return None
    return "standard", {
        "authority": m.group("authority"),
        "name": m.group("name"),
        "number": m.group("number"),
    }


def _try_report(body: str):
    m = re.match(
        r"^(?P<author>[^《:]*?)"
        r"(?:\((?P<identity>[^)]+)\))?"
        r":《(?P<title>[^》]+)》,"
        r"(?P<date>\d{4}年\d+月\d+日)在(?P<meeting>[^,。]+?)上"
        r"(?P<suffix>的报告|的说明)?"
        r"(?:,(?P<pub>[^,。]+))?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "title": m.group("title"),
        "date": m.group("date"),
        "meeting": m.group("meeting"),
    }
    if m.group("author"):
        data["author"] = m.group("author")
    if m.group("identity"):
        data["identity"] = f"({m.group('identity')})"
    if m.group("suffix"):
        data["report_suffix"] = m.group("suffix")
    if m.group("pub"):
        data["publication"] = m.group("pub")
    return "report", data


def _try_white_paper(body: str):
    m = re.match(
        r"^(?P<authority>[^《:]+):《(?P<name>[^》]+)》,"
        r"(?P<date>\d{4}年\d+月\d+日)发布"
        r"(?:,(?P<url>https?://\S+)|,(?P<pub>[^,]+?)(?P<y>\d{4})年版)?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "authority": m.group("authority"),
        "name": m.group("name"),
        "date": m.group("date"),
    }
    if m.group("url"):
        data["url"] = m.group("url").rstrip("。")
    if m.group("pub"):
        data["publisher"] = m.group("pub")
        data["year"] = int(m.group("y"))
    return "white_paper", data


# --------------------------------------------------------------------------
# 三、中文纸质出版文献
# --------------------------------------------------------------------------


def _try_journal(body: str):
    # 只引期刊本身：《台大法学论丛》第47卷第4期（2018年）
    m = re.match(
        r"^《(?P<journal>[^》]+)》"
        r"第(?P<vol>\d+)卷第(?P<issue>\d+)期\((?P<y>\d{4})年\)。?$",
        body,
    )
    if m:
        return "journal", {
            "journal": m.group("journal"),
            "volume": int(m.group("vol")),
            "issue": int(m.group("issue")),
            "year": int(m.group("y")),
        }

    m = re.match(
        r"^(?P<head>[^《]*?)《(?P<title>[^》]+)》"
        r",载《(?P<journal>[^》]+)》"
        r"(?P<info>.+?)"
        r"(?:,(?P<pages>第[^,。]+页[ab]?))?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {"title": m.group("title"), "journal": m.group("journal")}
    head = m.group("head").rstrip(":,")
    if head:
        data.update(split_authors(head))
    info = m.group("info")
    v = re.search(r"第(?P<v>\d+)卷第(?P<i>\d+)期\((?P<y>\d{4})年\)", info)
    if v:
        data.update(
            volume=int(v.group("v")),
            issue=int(v.group("i")),
            year=int(v.group("y")),
        )
    else:
        y = re.search(r"(?P<y>\d{4})年第(?P<i>\d+)期", info)
        if not y:
            return None
        data.update(year=int(y.group("y")), issue=int(y.group("i")))
    d = re.search(r"\((?P<d>\d{4}年\d+月\d+日)\)", info)
    if d:
        data["issue_date"] = d.group("d")
    if m.group("pages"):
        data["pages"] = _page_value(m.group("pages"))
    return "journal", data


def _try_newspaper(body: str):
    m = re.match(
        r"^(?P<head>[^《]*?)《(?P<title>[^》]+)》"
        r",载《(?P<paper>[^》]+)》"
        r"(?P<y>\d{4})年(?P<m>\d+)月(?P<d>\d+)日"
        r"(?:,第(?P<page>[^版]+)版)?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "title": m.group("title"),
        "newspaper": m.group("paper"),
        "year": int(m.group("y")),
        "month": int(m.group("m")),
        "day": int(m.group("d")),
    }
    head = m.group("head").rstrip(":,")
    if head:
        data.update(split_authors(head))
    if m.group("page"):
        data["page"] = int(m.group("page"))
    return "newspaper", data


def _try_thesis(body: str):
    m = re.match(
        r"^(?P<head>[^《]*?)《(?P<title>[^》]+)》"
        r",(?P<school>[^,]+?)(?P<y>\d{4})年(?P<degree>博士|硕士|学士)学位论文"
        r"(?:,(?P<pages>第[^,。]+页))?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "title": m.group("title"),
        "school": m.group("school"),
        "year": int(m.group("y")),
        "degree": m.group("degree"),
    }
    head = m.group("head").rstrip(":,")
    if head:
        data.update(split_authors(head))
    if m.group("pages"):
        data["pages"] = _page_value(m.group("pages"))
    return "thesis", data


def _try_conference(body: str):
    if "会议论文" not in body and "年会论文" not in body:
        return None
    m = re.match(
        r"^(?P<head>[^《]*?)《(?P<title>[^》]+)》"
        r",(?P<meeting>.+?)"
        r"(?:,(?P<y>\d{4})年(?P<mo>\d+)月(?:于(?P<place>[^,。]+))?)?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {"title": m.group("title"), "meeting_info": m.group("meeting")}
    head = m.group("head").rstrip(":,")
    if head:
        data.update(split_authors(head))
    if m.group("y"):
        data.update(year=int(m.group("y")), month=int(m.group("mo")))
        if m.group("place"):
            data["place"] = m.group("place")
    return "conference", data


def _try_collection(body: str):
    m = re.match(
        r"^(?P<head>[^《]*?)《(?P<title>[^》]+)》"
        r"(?:,(?P<translator>[^,]+)译)?"
        r",载(?P<editor>[^:]+?)(?P<role>主编|编|编著|编译):"
        r"《(?P<container>[^》]+)》"
        r"(?:第(?P<vol>\d+)卷)?"
        r"(?:,(?P<ctranslator>[^,]+)译)?"
        r"," + _PUBLISHER +
        r"(?:,(?P<pages>第[^,。]+页))?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "title": m.group("title"),
        "editor": m.group("editor"),
        "editor_role": m.group("role"),
        "container_title": m.group("container"),
        "publisher": m.group("pub"),
        "year": int(m.group("y")),
    }
    head = m.group("head").rstrip(":,")
    if head:
        data.update(split_authors(head))
    if m.group("translator"):
        data["translator"] = m.group("translator")
    if m.group("ctranslator"):
        data["container_translator"] = m.group("ctranslator")
    if m.group("vol"):
        data["volume"] = int(m.group("vol"))
    if m.group("pages"):
        data["pages"] = _page_value(m.group("pages"))
    return "collection", data


def _try_book(body: str):
    m = re.match(
        r"^(?P<head>[^《]*?)《(?P<title>[^》]+)》"
        r"(?:\((?P<edition>[^)]+)\))?"
        r"(?:,(?P<translator>[^,]+?)译)?"
        r"(?:,(?P<collator>[^,]+?(?:点校|整理)))?"
        r"(?:,(?P<volume_note>卷[^,]+))?"
        r"(?:,(?P<container>载《[^》]+》))?"
        r"(?:," + _PUBLISHER + r")?"
        r"(?:,(?P<pages>第?[^,。]+?页[ab]?|第[^,。]+章[^,。]*))?。?$",
        body,
    )
    if not m:
        return None
    head = m.group("head").rstrip(":,")
    if _AUTHORITY_HINT.search(head):
        return None  # 形如"国务院发布的"，交给法律文件分支
    data: dict = {"title": m.group("title")}
    if head:
        data.update(split_authors(head))
    if m.group("edition"):
        data["edition"] = m.group("edition")
    if m.group("translator"):
        data["translator"] = m.group("translator")
    if m.group("collator"):
        data["collator"] = m.group("collator")
    if m.group("volume_note"):
        data["volume_note"] = m.group("volume_note")
    if m.group("container"):
        data["container_title"] = m.group("container")[2:-1]
    if m.group("pub"):
        data["publisher"] = m.group("pub")
        data["year"] = int(m.group("y"))
    if m.group("pages"):
        data["pages"] = _page_value(m.group("pages"))
    return "book", data


# --------------------------------------------------------------------------
# 四、未发表文献与档案
# --------------------------------------------------------------------------


def _try_unpublished(body: str):
    m = re.match(
        r"^(?P<author>笔者|.+?教授)与(?P<who>[^,]+?)访谈,"
        r"(?P<y>\d{4})年(?P<mo>\d+)月(?P<d>\d+)日"
        r"(?:,(?P<place>[^,。]+))?。?$",
        body,
    )
    if m:
        data: dict = {
            "description": f"{m.group('author')}与{m.group('who')}访谈",
            "year": int(m.group("y")),
            "month": int(m.group("mo")),
            "day": int(m.group("d")),
        }
        if m.group("place"):
            data["place"] = m.group("place")
        return "interview", data

    m = re.match(
        r"^(?P<desc>.+?访谈),(?P<y>\d{4})年(?P<mo>\d+)月(?P<d>\d+)日。?$",
        body,
    )
    if m and m.group("desc").startswith("笔者"):
        return "interview", {
            "description": m.group("desc"),
            "year": int(m.group("y")),
            "month": int(m.group("mo")),
            "day": int(m.group("d")),
        }

    if "给笔者" in body or "电子邮件" in body:
        m = re.match(
            r"^(?P<desc>[^,]+?),(?P<y>\d{4})年(?P<mo>\d+)月(?P<d>\d+)日。?$",
            body,
        )
        if m:
            return "correspondence", {
                "description": m.group("desc"),
                "year": int(m.group("y")),
                "month": int(m.group("mo")),
                "day": int(m.group("d")),
            }

    if "档案号" in body:
        m = re.match(
            r"^(?P<head>[^《]*?)《(?P<title>[^》]+)》"
            r"\((?P<date>[^)]+)\),"
            r"(?P<repo>[^,]*?档案[^,]*?)"
            r"(?:,(?P<note>[^,]*?档案)?)?,档案号(?P<num>[^,。]+)。?$",
            body,
        )
        if m:
            data = {
                "title": m.group("title"),
                "date": m.group("date"),
                "archive_number": m.group("num"),
            }
            head = m.group("head").rstrip(":,")
            if head:
                data.update(split_authors(head))
            repo = m.group("repo")
            note = m.group("note") or ""
            if note and note in repo:
                data["repository"] = repo.replace(note, "")
                data["archive_note"] = note
            else:
                data["repository"] = repo + note
            return "archive", data
    return None


# --------------------------------------------------------------------------
# 五、英文文献
# --------------------------------------------------------------------------

_EN_EDITION_RE = re.compile(r"^(?P<base>.+?)\s*\((?P<edition>\d+\w*\s*ed\.)\)$")
_EN_ROLE_RE = re.compile(r"^(?P<name>.+?)\s+(?P<role>chief ed\.|eds?\.|trans\.)$")


def _try_en_article(body: str):
    # 第二种卷次标注法：期刊名后写卷数、页码
    m = re.match(
        r"^(?P<authors>.+?),(?P<title>.+?),"
        r"\s*(?P<journal>[A-Z][^,]*?),\s*(?P<info>Vol\.[^,]+)"
        r"(?:,\s*(?P<pages>p\.\s*[\d\-]+))?\s*\((?P<year>\d{4})\)\.?$",
        body,
    )
    if m:
        data: dict = {
            "authors": [a.strip() for a in m.group("authors").split(" & ")],
            "title": m.group("title").strip(),
            "journal": m.group("journal").strip(),
            "volume_info": m.group("info").strip(),
            "year": int(m.group("year")),
        }
        if m.group("pages"):
            data["pages"] = m.group("pages")
        return "en_article", data

    m = re.match(
        r"^(?P<authors>.+?),(?P<title>.+?),"
        r"\s*(?P<vol>\d+)\s(?P<journal>[A-Z][^,]*?)\s(?P<first>\d+)"
        r"(?:,\s(?P<pin>[\d\-]+))?\s\((?P<year>\d{4})\)\.?$",
        body,
    )
    if not m:
        return None
    data = {
        "authors": [a.strip() for a in m.group("authors").split(" & ")],
        "title": m.group("title").strip(),
        "journal": m.group("journal").strip(),
        "volume": int(m.group("vol")),
        "first_page": int(m.group("first")),
        "year": int(m.group("year")),
    }
    if m.group("pin"):
        data["pincite"] = m.group("pin")
    return "en_article", data


def _try_en_book(body: str):
    m = re.match(
        r"^(?P<authors>[^,]+?),(?P<title>.+?),"
        r"\s*(?P<pub>[^,]+?),\s*(?P<year>\d{4})"
        r"(?:,\s*(?:p\.\s*)?(?P<pages>[\d\-]+))?\.?$",
        body,
    )
    if not m:
        return None

    author_str = m.group("authors").strip()
    data: dict = {}
    role = _EN_ROLE_RE.match(author_str)
    if role:
        data["authors"] = [role.group("name")]
        data["authorship"] = role.group("role")
    else:
        data["authors"] = [a.strip() for a in author_str.split(",")]

    title = m.group("title").strip()
    edition = _EN_EDITION_RE.match(title)
    if edition:
        data["title"] = edition.group("base")
        data["edition"] = edition.group("edition")
    else:
        data["title"] = title

    data["publisher"] = m.group("pub").strip()
    data["year"] = int(m.group("year"))
    if m.group("pages"):
        data["pages"] = "p. " + m.group("pages")
    return "en_book", data


def _try_blog(body: str):
    """博客文章：与网络文献同形，靠"博客"二字区分。"""
    if "博客" not in body:
        return None
    m = re.match(
        r"^(?P<head>[^《,]*?)(?:《(?P<title>[^》]+)》)"
        r",载(?P<blog>[^,\d]+?博客)"
        r"(?P<y>\d{4})年(?P<mo>\d+)月(?P<d>\d+)日"
        r",(?P<url>https?://\S+)。?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "title": m.group("title"),
        "blog": m.group("blog"),
        "year": int(m.group("y")),
        "month": int(m.group("mo")),
        "day": int(m.group("d")),
        "url": m.group("url").rstrip("。"),
    }
    head = m.group("head").rstrip(":,")
    if head:
        data.update(split_authors(head))
    return "blog", data


def _try_internal(body: str):
    if "座谈会" not in body:
        return None
    m = re.match(
        r"^(?P<meeting>[^,]+?)(?P<y>\d{4})年(?P<mo>\d+)月(?P<d>\d+)日"
        r"(?:,(?P<place>[^,。]+))?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "meeting": m.group("meeting"),
        "year": int(m.group("y")),
        "month": int(m.group("mo")),
        "day": int(m.group("d")),
    }
    if m.group("place"):
        data["place"] = m.group("place")
    return "internal", data


def _try_audiovisual(body: str):
    m = re.match(
        r"^《(?P<name>[^》]+)》,(?P<producer>[^,]+?)制作,(?P<y>\d{4})年。?$",
        body,
    )
    if not m:
        return None
    return "audiovisual", {
        "name": m.group("name"),
        "producer": m.group("producer"),
        "year": int(m.group("y")),
    }


def _try_website(body: str):
    """网站或栏目本身作为来源：名称,网址,访问日期。"""
    m = re.match(
        r"^(?P<name>[^,]+?),"
        r"(?P<url>https?://\S+?)"
        r",(?P<vy>\d{4})年(?P<vm>\d+)月(?P<vd>\d+)日访问。?$",
        body,
    )
    if not m:
        return None
    name = m.group("name")
    data: dict = {
        "url": m.group("url").rstrip("。"),
        "visit_year": int(m.group("vy")),
        "visit_month": int(m.group("vm")),
        "visit_day": int(m.group("vd")),
    }
    col = re.search(r"^(?P<base>.+?)(?P<column>[\"].+?[\"]栏目)$", name)
    if col:
        data["name"] = col.group("base")
        data["column"] = col.group("column")
    else:
        data["name"] = name
    return "website", data


def _try_wechat(body: str):
    m = re.match(
        r"^(?P<head>[^《]*?)《(?P<title>[^》]+)》"
        r",载微信公众号[\"“](?P<account>[^\"”]+)[\"”]"
        r"(?P<y>\d{4})年(?P<m>\d+)月(?P<d>\d+)日。?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "title": m.group("title"),
        "account": m.group("account"),
        "year": int(m.group("y")),
        "month": int(m.group("m")),
        "day": int(m.group("d")),
    }
    head = m.group("head").rstrip(":,")
    if head:
        data.update(split_authors(head))
    return "wechat", data


def _try_app(body: str):
    m = re.match(
        r"^(?P<head>[^《]*?)《(?P<title>[^》]+)》"
        r",载[\"“](?P<app>[^\"”]+)[\"”]App"
        r"(?P<y>\d{4})年(?P<m>\d+)月(?P<d>\d+)日。?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "title": m.group("title"),
        "app": m.group("app"),
        "year": int(m.group("y")),
        "month": int(m.group("m")),
        "day": int(m.group("d")),
    }
    head = m.group("head").rstrip(":,")
    if head:
        data.update(split_authors(head))
    return "app", data


def _try_weibo(body: str):
    m = re.match(
        r"^(?P<platform>[^,]*?微博)(?P<account>[^,]+),"
        r"(?P<y>\d{4})年(?P<m>\d+)月(?P<d>\d+)日,"
        r"(?P<url>https?://\S+)。?$",
        body,
    )
    if not m:
        return None
    return "weibo", {
        "platform": m.group("platform"),
        "account": m.group("account"),
        "year": int(m.group("y")),
        "month": int(m.group("m")),
        "day": int(m.group("d")),
        "url": m.group("url").rstrip("。"),
    }


def _try_broadcast(body: str):
    m = re.match(
        r"^(?P<host>[^《]*)主持:《(?P<title>[^》]+)》"
        r",(?P<station>[^\"“]+)[\"“](?P<column>[^\"”]+)[\"”]栏"
        r"(?P<y>\d{4})年(?P<m>\d+)月(?P<d>\d+)日播出"
        r"(?:,(?P<url>https?://\S+))?。?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "title": m.group("title"),
        "station": m.group("station"),
        "column": m.group("column"),
        "year": int(m.group("y")),
        "month": int(m.group("m")),
        "day": int(m.group("d")),
    }
    if m.group("host"):
        data["host"] = m.group("host")
    if m.group("url"):
        data["url"] = m.group("url").rstrip("。")
    return "broadcast", data


def _try_online(body: str):
    if "http" not in body:
        return None
    m = re.match(
        r"^(?P<head>[^《,]*?)(?:《(?P<title>[^》]+)》)"
        r"(?:,载(?P<site>[^,\d]+))?"
        r"(?:(?P<y>\d{4})年(?P<mo>\d+)月(?P<d>\d+)日)?"
        r",(?P<url>https?://\S+?)"
        r"(?:,(?P<vy>\d{4})年(?P<vm>\d+)月(?P<vd>\d+)日访问)?。?$",
        body,
    )
    if not m or not m.group("title"):
        return None
    data: dict = {"title": m.group("title"), "url": m.group("url").rstrip("。")}
    if m.group("site"):
        data["site"] = m.group("site")
    if m.group("y"):
        data.update(
            year=int(m.group("y")), month=int(m.group("mo")), day=int(m.group("d"))
        )
    if m.group("vy"):
        data.update(
            visit_year=int(m.group("vy")),
            visit_month=int(m.group("vm")),
            visit_day=int(m.group("vd")),
        )
    head = (m.group("head") or "").rstrip(":,")
    if head:
        data.update(split_authors(head))
    return "online", data


def _try_en_periodical(body: str):
    m = re.match(
        r"^(?P<authors>[^,]+?),(?P<title>.+?),"
        r"\s*(?P<periodical>[^,]+?),\s*(?P<date>\d{1,2}\s+\w+\s+\d{4})"
        r"(?:,\s*(?P<page>(?:p\.|at)\s*\S+))?\.?$",
        body,
    )
    if not m:
        return None
    data: dict = {
        "authors": [a.strip() for a in m.group("authors").split(",")],
        "title": m.group("title").strip(),
        "periodical": m.group("periodical").strip(),
        "date": m.group("date"),
    }
    if m.group("page"):
        data["page"] = m.group("page")
    return "en_periodical", data


def _try_en_online(body: str):
    if "http" not in body:
        return None
    m = re.match(
        r"^(?P<head>.+?),\s*(?P<url>https?://\S+?)"
        r"(?:,\s*visited on\s*(?P<visit>[^,]+?))?\.?$",
        body,
    )
    if not m:
        return None
    data: dict = {}
    head = m.group("head").strip()
    # 头部形如 "作者, 标题, 网站 (日期)" 或 "标题"
    parts = [p.strip() for p in head.split(",")]
    site_date = None
    if parts:
        tail = parts[-1]
        sd = re.match(r"^(?P<site>.+?)\s*\((?P<date>[^)]+)\)$", tail)
        if sd:
            site_date = sd.group("site").strip()
            data["date"] = sd.group("date").strip()
            parts = parts[:-1]
    if site_date:
        data["site"] = site_date
    if len(parts) >= 2:
        data["authors"] = parts[0]
        data["title"] = ", ".join(parts[1:])
    elif parts:
        data["authors"] = parts[0]
    data["url"] = m.group("url").rstrip("。")
    if m.group("visit"):
        data["visit_date"] = m.group("visit").strip()
    if not (data.get("title") or data.get("site") or data.get("authors")):
        return None
    return "en_online", data


def _try_en_case(body: str):
    # 尚未宣判的案件：只标案件号与审理法院
    m = re.match(
        r"^(?P<name>.+?),\s*(?P<docket>No\.\s*\S+)\s*\((?P<court>[^)]+)\)\.?$",
        body,
    )
    if m:
        return "en_case", {
            "case_name": m.group("name").strip(),
            "docket": m.group("docket").strip(),
            "court": m.group("court").strip(),
        }

    m = re.match(
        r"^(?P<name>.+?),\s*(?P<reports>\d+\s+[A-Z][^,]*?\s\d+)"
        r"(?:,\s*(?P<more>\d+\s+[A-Z][^,]*?\s\d+))*"
        r"\s*\((?P<court_year>[^)]+)\)\.?$",
        body,
    )
    if not m:
        return None
    name = m.group("name").strip()
    reports = [m.group("reports")]
    if m.group("more"):
        reports.append(m.group("more"))
    cy = m.group("court_year").strip()
    data: dict = {"case_name": name, "reports": reports}
    ym = re.match(r"^(?P<year>\d{4})$", cy)
    if ym:
        data["year"] = int(ym.group("year"))
    else:
        cm = re.match(r"^(?P<court>.+?)\s+(?P<year>\d{4})$", cy)
        if cm:
            data["court"] = cm.group("court")
            data["year"] = int(cm.group("year"))
        else:
            data["court"] = cy
    return "en_case", data


# --------------------------------------------------------------------------
# 分派
# --------------------------------------------------------------------------

# 顺序即优先级：越具体、越不可能误伤的越靠前
_EXTRACTORS = (
    _try_case,
    _try_legal,
    _try_hk_macau,
    _try_taiwan_law,
    _try_foreign_law,
    _try_treaty,
    _try_un_document,
    _try_standard,
    _try_report,
    _try_white_paper,
    _try_journal,
    _try_newspaper,
    _try_thesis,
    _try_conference,
    _try_unpublished,
    _try_internal,
    _try_broadcast,
    _try_blog,
    _try_wechat,
    _try_app,
    _try_weibo,
    _try_website,
    _try_online,
    _try_audiovisual,
    _try_collection,
    _try_book,
    _try_en_article,
    _try_en_book,
    _try_en_periodical,
    _try_en_case,
    _try_en_online,
)


def parse_one(text: str) -> ParseResult:
    """解析单条脚注，返回 ``ParseResult``。"""
    original = text.strip()
    if not original:
        return ParseResult(type=None, reason="空文本", data={}, lead="")
    body, lead = strip_lead_and_tail(original)
    body = normalize(body).strip()
    for extractor in _EXTRACTORS:
        try:
            hit = extractor(body)
        except Exception:  # 单个模式异常不应中断整批解析
            hit = None
        if hit:
            kind, data = hit
            return ParseResult(
                type=kind,
                data=restore_data_quotes(data),
                lead=lead,
                body=body,
                original=original,
            )
    return ParseResult(
        type=None,
        reason="未匹配到已知式样，需人工或模型补字段",
        data={},
        lead=lead,
        body=body,
        original=original,
    )


def parse(texts) -> list[ParseResult]:
    """批量解析。``texts`` 可以是字符串（按行切分）或字符串序列。"""
    if isinstance(texts, str):
        items = [line for line in texts.splitlines() if line.strip()]
    else:
        items = list(texts)
    return [parse_one(item) for item in items]
