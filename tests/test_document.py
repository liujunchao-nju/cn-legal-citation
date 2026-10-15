"""逆向解析、核查与文档通道的测试。

三组内容：

1. 往返测试：手册示例经「解析 → 重新渲染」必须逐字复原。这是逆向能力
   的正确性基准 —— 解析错了就一定复现不出来。
2. 核查分级：完全合规、标点需规范化、格式不符、未能解析四种状态。
3. 文档通道：Markdown 与 Word 脚注的提取与写回，含「原件零改动」校验。
"""

from __future__ import annotations

import hashlib
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from make_docx_fixture import make_docx

from cn_legal_citation import (
    check_document,
    check_one,
    document_report,
    export_rules,
    extract_docx,
    extract_markdown,
    load_rules,
    parse_one,
    rewrite_document,
    rewrite_docx,
    rewrite_markdown,
    summarize,
)
from cn_legal_citation import rules as rules_module

# 规则解析覆盖范围：中文全部类型 + 英文著作论文。法德意俄日暂不做规则解析。
PARSE_SKIP_PREFIXES = (
    "fr_",
    "de_",
    "it_",
    "ru_",
    "ja_",
    "en_law_",
    "en_doc_un",
    "en_case_uk",
    "en_case_intl",
    "statistics",
)


def _in_parse_scope(name: str) -> bool:
    return not name.startswith(PARSE_SKIP_PREFIXES)


# --------------------------------------------------------------------------
# 一、往返测试
# --------------------------------------------------------------------------


def test_roundtrip_all_in_scope_examples():
    """解析范围内的手册示例，解析后必须能逐字重新渲染。"""
    rules, _ = load_rules()
    failures = []
    checked = 0
    for name, rule in sorted(rules.items()):
        if not _in_parse_scope(name):
            continue
        for example in rule.get("examples") or []:
            checked += 1
            result = check_one(example)
            if result["status"] != "ok":
                failures.append(
                    f"[{name}] {result['status']}: {example}"
                    + (f" -> {result['rendered']}" if result.get("rendered") else "")
                )
    assert checked >= 100, f"解析范围内的示例过少：{checked}"
    assert not failures, "以下示例未能往返复现：\n" + "\n".join(failures)


def test_out_of_scope_examples_report_unparsed_not_wrong():
    """范围外的语种如实报「未能解析」，不得给出错误字段。"""
    rules, _ = load_rules()
    for name in ("ja_book", "fr_law", "de_case"):
        for example in rules[name]["examples"]:
            result = check_one(example)
            assert result["status"] in ("unparsed", "ok", "style", "diff")
            if result["status"] == "unparsed":
                assert result["type"] is None


# --------------------------------------------------------------------------
# 二、解析单元测试
# --------------------------------------------------------------------------

PARSE_CASES = [
    (
        "王名扬:《美国行政法》,中国法制出版社1995年版,第18页。",
        "book",
        {
            "authors": ["王名扬"],
            "title": "美国行政法",
            "publisher": "中国法制出版社",
            "year": 1995,
            "pages": 18,
        },
    ),
    (
        "[美]富勒:《法律的道德性》,郑戈译,商务印书馆2005年版。",
        "book",
        {
            "authors": ["富勒"],
            "nationality": "美",
            "title": "法律的道德性",
            "translator": "郑戈",
            "publisher": "商务印书馆",
            "year": 2005,
        },
    ),
    (
        "(清)沈家本:《历代刑法考》,邓经元、宇骞点校,中华书局1985年版。",
        "book",
        {
            "authors": ["沈家本"],
            "dynasty": "清",
            "title": "历代刑法考",
            "collator": "邓经元、宇骞点校",
            "publisher": "中华书局",
            "year": 1985,
        },
    ),
    (
        "何海波:《判决书上网》,载《法制日报》2000年5月21日,第2版。",
        "newspaper",
        {
            "authors": ["何海波"],
            "title": "判决书上网",
            "newspaper": "法制日报",
            "year": 2000,
            "month": 5,
            "day": 21,
            "page": 2,
        },
    ),
    (
        "刘松山:《失信惩戒立法的三大问题》,载微信公众号“中国法律评论”2019年11月19日。",
        "wechat",
        {
            "authors": ["刘松山"],
            "title": "失信惩戒立法的三大问题",
            "account": "中国法律评论",
            "year": 2019,
            "month": 11,
            "day": 19,
        },
    ),
    (
        "《刑法》第17条之一。",
        "legal",
        {"name": "刑法", "article": "第17条之一"},
    ),
    (
        "《公司法》(2005年修订)第16条。",
        "legal",
        {"name": "公司法", "revision": "2005年修订", "article": "第16条"},
    ),
    (
        "田永诉北京科技大学案,北京市海淀区人民法院(1998)海行初字第142号行政判决书。",
        "case",
        {
            "case_name": "田永诉北京科技大学案",
            "court": "北京市海淀区人民法院",
            "case_number": "(1998)海行初字第142号",
            "document_type": "行政判决书",
        },
    ),
    (
        "车某玲诉朱某芳相邻关系纠纷案,人民法院案例库2024-18-2-053-001。",
        "case",
        {
            "case_name": "车某玲诉朱某芳相邻关系纠纷案",
            "database_number": "2024-18-2-053-001",
        },
    ),
    (
        "李松锋:《游走在上帝与凯撒之间》,中国政法大学2013年博士学位论文,第30页。",
        "thesis",
        {
            "authors": ["李松锋"],
            "title": "游走在上帝与凯撒之间",
            "school": "中国政法大学",
            "year": 2013,
            "degree": "博士",
            "pages": 30,
        },
    ),
]


@pytest.mark.parametrize("text,expected_type,expected_data", PARSE_CASES)
def test_parse_fields(text, expected_type, expected_data):
    result = parse_one(text)
    assert result.ok, f"未能解析：{text}"
    assert result["type"] == expected_type
    for key, value in expected_data.items():
        assert result["data"].get(key) == value, f"{key} 不符：{result['data']}"


def test_parse_returns_none_for_garbage():
    result = parse_one("某某随便写的东西,格式完全不对。")
    assert not result.ok
    assert result["type"] is None
    assert result["reason"]


def test_parse_tolerates_full_width_punctuation():
    """用户常用全角标点，解析入口应归一化后再匹配。"""
    full = parse_one("张新宝：《侵权责任法》（第5版），中国人民大学出版社2020年版，第73-75页。")
    half = parse_one("张新宝:《侵权责任法》(第5版),中国人民大学出版社2020年版,第73-75页。")
    assert full.ok and half.ok
    assert full["type"] == half["type"] == "book"
    assert full["data"] == half["data"]


# --------------------------------------------------------------------------
# 三、核查分级
# --------------------------------------------------------------------------


def test_check_status_ok():
    result = check_one("王名扬:《美国行政法》,中国法制出版社1995年版,第18页。")
    assert result["status"] == "ok"
    assert result["rendered"] == result["text"]


def test_check_status_style_for_full_width():
    result = check_one("张新宝：《侵权责任法》（第5版），中国人民大学出版社2020年版，第73-75页。")
    assert result["status"] == "style"
    assert result["rendered"] == "张新宝:《侵权责任法》(第5版),中国人民大学出版社2020年版,第73-75页。"


def test_check_status_unparsed():
    result = check_one("这句话不是引注。")
    assert result["status"] == "unparsed"
    assert result["type"] is None


def test_check_summary_has_fixable():
    results = [
        check_one("王名扬:《美国行政法》,中国法制出版社1995年版,第18页。"),
        check_one("张新宝：《侵权责任法》，中国人民大学出版社2020年版。"),
        check_one("这句话不是引注。"),
    ]
    stats = summarize(results)
    assert stats["total"] == 3
    assert stats["ok"] == 1
    assert stats["style"] == 1
    assert stats["unparsed"] == 1
    assert stats["fixable"] == 1


# --------------------------------------------------------------------------
# 四、Markdown 通道
# --------------------------------------------------------------------------

MD_SOURCE = """# 论文

正文一。[^1]正文二。[^2]

[^1]: 王名扬:《美国行政法》,中国法制出版社1995年版,第18页。

[^2]: 张新宝：《侵权责任法》（第5版），中国人民大学出版社
    2020年版，第73-75页。
"""


def test_markdown_extract(tmp_path):
    path = tmp_path / "paper.md"
    path.write_text(MD_SOURCE, encoding="utf-8")
    entries = extract_markdown(path)
    assert len(entries) == 2
    assert entries[0]["label"] == "1"
    assert entries[0]["text"] == "王名扬:《美国行政法》,中国法制出版社1995年版,第18页。"
    # 续行应被合并
    assert "2020年版" in entries[1]["text"]


def test_markdown_rewrite_keeps_original(tmp_path):
    src = tmp_path / "paper.md"
    src.write_text(MD_SOURCE, encoding="utf-8")
    before = src.read_bytes()
    out = tmp_path / "fixed.md"
    rewrite_markdown(src, {"2": "张新宝:《侵权责任法》(第5版),中国人民大学出版社2020年版,第73-75页。"}, out)
    assert src.read_bytes() == before, "原件被改动了"
    text = out.read_text(encoding="utf-8")
    assert "张新宝:《侵权责任法》(第5版),中国人民大学出版社2020年版,第73-75页。" in text
    assert "正文一。[^1]" in text, "正文被误改"


def test_markdown_rewrite_refuses_same_path(tmp_path):
    src = tmp_path / "paper.md"
    src.write_text(MD_SOURCE, encoding="utf-8")
    with pytest.raises(Exception):
        rewrite_markdown(src, {"1": "x"}, src)


# --------------------------------------------------------------------------
# 五、DOCX 通道
# --------------------------------------------------------------------------

SAMPLE_FOOTNOTES = [
    "王名扬:《美国行政法》,中国法制出版社1995年版,第18页。",
    "张新宝：《侵权责任法》（第5版），中国人民大学出版社2020年版，第73-75页。",
    "这句话不是引注。",
]


@pytest.fixture()
def sample_docx(tmp_path):
    path = tmp_path / "paper.docx"
    make_docx(path, SAMPLE_FOOTNOTES)
    return path


def test_docx_extract(sample_docx):
    entries = extract_docx(sample_docx)
    assert len(entries) == len(SAMPLE_FOOTNOTES)
    assert [e["id"] for e in entries] == ["1", "2", "3"]
    assert entries[0]["text"] == SAMPLE_FOOTNOTES[0]


def test_docx_rewrite_keeps_original_and_others(sample_docx, tmp_path):
    before = hashlib.sha256(sample_docx.read_bytes()).hexdigest()
    out = tmp_path / "fixed.docx"
    rewrite_docx(
        sample_docx,
        {"2": "张新宝:《侵权责任法》(第5版),中国人民大学出版社2020年版,第73-75页。"},
        out,
    )
    after = hashlib.sha256(sample_docx.read_bytes()).hexdigest()
    assert before == after, "原件字节被改动了"

    entries = extract_docx(out)
    assert len(entries) == len(SAMPLE_FOOTNOTES), "脚注数量发生变化"
    assert entries[1]["text"] == "张新宝:《侵权责任法》(第5版),中国人民大学出版社2020年版,第73-75页。"
    assert entries[0]["text"] == SAMPLE_FOOTNOTES[0], "未指定的脚注被改动"
    assert entries[2]["text"] == SAMPLE_FOOTNOTES[2], "未指定的脚注被改动"


def test_docx_rewrite_refuses_same_path(sample_docx):
    with pytest.raises(Exception):
        rewrite_docx(sample_docx, {"1": "x"}, sample_docx)


def test_docx_without_footnotes_reports_clearly(tmp_path):
    path = tmp_path / "plain.docx"
    make_docx(path, [])
    assert extract_docx(path) == []


# --------------------------------------------------------------------------
# 六、整篇流程
# --------------------------------------------------------------------------


def test_document_flow_end_to_end(sample_docx, tmp_path):
    results = check_document(sample_docx)
    stats = summarize(results)
    assert stats["total"] == 3
    assert stats["ok"] == 1
    assert stats["style"] == 1
    assert stats["unparsed"] == 1

    report = document_report(sample_docx)
    assert "脚注核查报告" in report
    assert "标点需规范化" in report
    assert "未能解析" in report

    out = tmp_path / "fixed.docx"
    result = rewrite_document(sample_docx, out)
    assert result["changed"] == 1
    assert result["verified"] is True
    assert result["changes"][0]["locator"] == "脚注 2"
    # 未解析的脚注不动
    assert [s["locator"] for s in result["skipped"]] == ["脚注 1", "脚注 3"]


def test_document_flow_no_change_when_all_ok(tmp_path):
    path = tmp_path / "clean.docx"
    make_docx(path, ["王名扬:《美国行政法》,中国法制出版社1995年版,第18页。"])
    result = rewrite_document(path, tmp_path / "out.docx")
    assert result["changed"] == 0
    assert result["out_path"] is None
    assert not (tmp_path / "out.docx").exists(), "没有改动时不应生成文件"


# --------------------------------------------------------------------------
# 七、JSON 规则回退（免 PyYAML 环境）
# --------------------------------------------------------------------------


def test_export_and_json_fallback(tmp_path, monkeypatch):
    target = export_rules(tmp_path / "rules.json")
    assert target.exists()

    # 模拟缺少 PyYAML：把模块里的 yaml 置空，强制走 JSON 回退
    monkeypatch.setattr(rules_module, "yaml", None)
    rules, punctuation = rules_module.load_rules(tmp_path)
    assert len(rules) >= 60
    assert rules["book"]["segments"]
    assert punctuation["colon"] == ":"
