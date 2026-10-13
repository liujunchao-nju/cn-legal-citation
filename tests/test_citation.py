"""引注生成测试。

第一组用例直接取自《法学引注手册》（第二版）公开示例，作为回归基准；
其余用例覆盖法律条文、裁判文书、学位论文、外文文献与边界情形。
"""

from __future__ import annotations

import pytest

from cn_legal_citation import cite, cite_many, load_rules
from cn_legal_citation.formatter import render

# --------------------------------------------------------------------------
# 一、《法学引注手册》（第二版）公开示例回归
# --------------------------------------------------------------------------

HANDBOOK_CASES = [
    (
        "book",
        {
            "authors": ["王名扬"],
            "title": "美国行政法",
            "publisher": "北京大学出版社",
            "year": 2007,
            "pages": 18,
        },
        "王名扬:《美国行政法》,北京大学出版社2007年版,第18页。",
    ),
    (
        "book",
        {
            "authors": ["张新宝"],
            "title": "侵权责任法",
            "edition": 4,
            "publisher": "中国人民大学出版社",
            "year": 2016,
            "pages": (73, 75),
        },
        "张新宝:《侵权责任法》(第4版),中国人民大学出版社2016年版,第73-75页。",
    ),
    (
        "book",
        {
            "authors": ["高鸿钧", "程汉大"],
            "authorship": "主编",
            "title": "英美法原论",
            "publisher": "北京大学出版社",
            "year": 2013,
            "pages": "第二章“英美判例法”",
        },
        "高鸿钧、程汉大主编:《英美法原论》,北京大学出版社2013年版,第二章“英美判例法”。",
    ),
    (
        "book",
        {
            "authors": ["富勒"],
            "nationality": "美",
            "title": "法律的道德性",
            "translator": "郑戈",
            "publisher": "商务印书馆",
            "year": 2005,
        },
        "[美]富勒:《法律的道德性》,郑戈译,商务印书馆2005年版。",
    ),
    (
        "journal",
        {
            "authors": ["季卫东"],
            "title": "法律程序的意义——对中国法制建设的另一种思考",
            "journal": "中国社会科学",
            "year": 1993,
            "issue": 1,
            "pages": 91,
        },
        "季卫东:《法律程序的意义——对中国法制建设的另一种思考》,载《中国社会科学》1993年第1期,第91页。",
    ),
    (
        "collection",
        {
            "authors": ["王保树"],
            "title": "股份有限公司机关构造中的董事和董事会",
            "editor": "梁慧星",
            "editor_role": "主编",
            "container_title": "民商法论丛",
            "volume": 1,
            "publisher": "法律出版社",
            "year": 1994,
            "pages": 110,
        },
        "王保树:《股份有限公司机关构造中的董事和董事会》,载梁慧星主编:《民商法论丛》第1卷,法律出版社1994年版,第110页。",
    ),
    (
        "collection",
        {
            "authors": ["莱纳·沃尔夫"],
            "nationality": "德",
            "title": "风险法的风险",
            "translator": "陈霄",
            "editor": "刘刚",
            "editor_role": "编译",
            "container_title": "风险规制:德国的理论与实践",
            "publisher": "法律出版社",
            "year": 2012,
        },
        "[德]莱纳·沃尔夫:《风险法的风险》,陈霄译,载刘刚编译:《风险规制:德国的理论与实践》,法律出版社2012年版。",
    ),
    (
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
        "何海波:《判决书上网》,载《法制日报》2000年5月21日,第2版。",
    ),
    (
        "online",
        {
            "authors": ["汪波"],
            "title": "哈尔滨市政法机关正对“宝马案”认真调查复查",
            "site": "人民网",
            "year": 2004,
            "month": 1,
            "day": 10,
            "url": "http://www.people.com.cn/GB/shehui/1062/2289764.html",
        },
        "汪波:《哈尔滨市政法机关正对“宝马案”认真调查复查》,载人民网2004年1月10日,http://www.people.com.cn/GB/shehui/1062/2289764.html。",
    ),
    (
        "online",
        {
            "title": "被告人李宁、张磊贪污案一案开庭",
            "site": "新华网",
            "url": "http://www.xinhuanet.com/legal/2019-12/31/c_1125406056.htm",
        },
        "《被告人李宁、张磊贪污案一案开庭》,载新华网,http://www.xinhuanet.com/legal/2019-12/31/c_1125406056.htm。",
    ),
    (
        "wechat",
        {
            "authors": ["刘松山"],
            "title": "失信惩戒立法的三大问题",
            "account": "中国法律评论",
            "year": 2019,
            "month": 11,
            "day": 19,
        },
        "刘松山:《失信惩戒立法的三大问题》,载微信公众号“中国法律评论”2019年11月19日。",
    ),
]


@pytest.mark.parametrize("type_name,data,expected", HANDBOOK_CASES)
def test_handbook_examples(type_name, data, expected):
    assert cite(type_name, data) == expected


# --------------------------------------------------------------------------
# 二、法律条文与规范性文件
# --------------------------------------------------------------------------

LEGAL_CASES = [
    ({"name": "行政处罚法", "article": 32}, "《行政处罚法》第32条。"),
    (
        {"name": "民法典", "article": {"article": 1224, "paragraph": 1, "item": 2}},
        "《民法典》第1224条第1款第2项。",
    ),
    (
        {"name": "刑法", "article": {"article": 232}},
        "《刑法》第232条。",
    ),
    (
        {
            "name": "最高人民法院关于适用〈中华人民共和国刑事诉讼法〉的解释",
            "document_number": "法释〔2021〕1号",
            "article": 100,
        },
        "《最高人民法院关于适用〈中华人民共和国刑事诉讼法〉的解释》(法释〔2021〕1号)第100条。",
    ),
    (
        {
            "name": "全国人民代表大会常务委员会关于严禁卖淫嫖娼的决定",
            "adoption_info": "1991年9月4日第七届全国人大常委会第二十一次会议通过",
        },
        "《全国人民代表大会常务委员会关于严禁卖淫嫖娼的决定》,1991年9月4日第七届全国人大常委会第二十一次会议通过。",
    ),
]


@pytest.mark.parametrize("data,expected", LEGAL_CASES)
def test_legal(data, expected):
    assert cite("legal", data) == expected


# --------------------------------------------------------------------------
# 三、裁判文书
# --------------------------------------------------------------------------

CASE_CASES = [
    (
        {
            "court": "北京市海淀区人民法院",
            "case_number": {"year": 1998, "code": "海行初字", "number": 142},
            "document_type": "行政判决书",
        },
        "北京市海淀区人民法院(1998)海行初字第142号行政判决书。",
    ),
    (
        {
            "case_name": "田永诉北京科技大学案",
            "court": "北京市海淀区人民法院",
            "case_number": "(1998)海行初字第142号",
            "document_type": "行政判决书",
        },
        "田永诉北京科技大学案,北京市海淀区人民法院(1998)海行初字第142号行政判决书。",
    ),
    (
        {
            "court": "最高人民法院",
            "case_number": "(2021)最高法民终34号",
            "document_type": "民事判决书",
            "year": 2021,
            "month": 6,
            "day": 18,
        },
        "最高人民法院(2021)最高法民终34号民事判决书,2021年6月18日。",
    ),
]


@pytest.mark.parametrize("data,expected", CASE_CASES)
def test_case(data, expected):
    assert cite("case", data) == expected


# --------------------------------------------------------------------------
# 四、学位论文
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "data,expected",
    [
        (
            {
                "authors": ["刘俊超"],
                "title": "论个人信息处理的正当性基础",
                "school": "南京大学法学院",
                "year": 2026,
                "degree": "硕士",
                "pages": 33,
            },
            "刘俊超:《论个人信息处理的正当性基础》,南京大学法学院2026年硕士学位论文,第33页。",
        ),
        (
            {
                "authors": ["甲"],
                "title": "行政法上的第三方义务",
                "school": "清华大学法学院",
                "year": 2020,
                "degree": "博士",
            },
            "甲:《行政法上的第三方义务》,清华大学法学院2020年博士学位论文。",
        ),
    ],
)
def test_thesis(data, expected):
    assert cite("thesis", data) == expected


# --------------------------------------------------------------------------
# 五、外文文献
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "type_name,data,expected",
    [
        (
            "foreign_book",
            {
                "authors": ["H. L. A. Hart"],
                "title": "The Concept of Law",
                "publisher": "Oxford University Press",
                "year": 1961,
                "pages": 123,
            },
            "H. L. A. Hart, The Concept of Law 123 (Oxford University Press 1961).",
        ),
        (
            "foreign_book",
            {
                "authors": ["John Rawls"],
                "title": "A Theory of Justice",
                "publisher": "Harvard University Press",
                "year": 1971,
            },
            "John Rawls, A Theory of Justice (Harvard University Press 1971).",
        ),
        (
            "foreign_article",
            {
                "authors": ["Cass R. Sunstein"],
                "title": "Interpreting Statutes in the Regulatory State",
                "volume": 103,
                "journal": "Harvard Law Review",
                "first_page": 405,
                "year": 1989,
            },
            "Cass R. Sunstein, Interpreting Statutes in the Regulatory State, 103 Harvard Law Review 405 (1989).",
        ),
    ],
)
def test_foreign(type_name, data, expected):
    assert cite(type_name, data) == expected


# --------------------------------------------------------------------------
# 六、边界情形与配置
# --------------------------------------------------------------------------


def test_authors_more_than_three_collapse():
    data = {
        "authors": ["甲", "乙", "丙", "丁"],
        "title": "某某法学",
        "publisher": "某出版社",
        "year": 2020,
    }
    assert cite("book", data) == "甲等:《某某法学》,某出版社2020年版。"


def test_missing_optional_fields_leaves_no_dangling_punctuation():
    assert cite("book", {"authors": ["甲"], "title": "乙"}) == "甲:《乙》。"


def test_title_only_book():
    assert cite("book", {"title": "乙的著作"}) == "《乙的著作》。"


def test_punctuation_is_configurable():
    rules, _ = load_rules()
    data = {"authors": ["甲"], "title": "乙", "publisher": "丙出版社", "year": 2020}
    full = render(rules["book"], data, {"colon": "：", "comma": "，", "period": "。"})
    assert full == "甲：《乙》，丙出版社2020年版。"


def test_unknown_type_raises():
    with pytest.raises(KeyError):
        cite("not_a_type", {"title": "x"})


def test_cite_many():
    items = [
        {"type": "legal", "data": {"name": "行政处罚法", "article": 32}},
        {"type": "book", "data": {"authors": ["甲"], "title": "乙"}},
    ]
    assert cite_many(items) == ["《行政处罚法》第32条。", "甲:《乙》。"]


def test_every_rule_declares_examples_and_source():
    rules, _ = load_rules()
    for name, rule in rules.items():
        assert rule.get("examples"), f"{name} 缺少示例"
        assert rule.get("source"), f"{name} 缺少规则依据"
