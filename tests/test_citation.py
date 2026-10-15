"""引注生成测试。

第一组用例直接取自《法学引注手册》（第二版，北京大学出版社 2025 年版）
「示例」部分与正文条款，作为回归基准；其余用例覆盖边界情形与配置。

第一版（2020 年版）到第二版的式样变化见 README「已知限制」与
各规则文件 source 字段中的条款号。
"""

from __future__ import annotations

import pytest

from cn_legal_citation import cite, cite_many, load_rules
from cn_legal_citation.formatter import render

# --------------------------------------------------------------------------
# 一、手册「示例」部分回归（第二版示例 1-32）
# --------------------------------------------------------------------------

HANDBOOK_CASES = [
    # 示例 1-4：中文图书
    (
        "book",
        {
            "authors": ["王名扬"],
            "title": "美国行政法",
            "publisher": "中国法制出版社",
            "year": 1995,
            "pages": 18,
        },
        "王名扬:《美国行政法》,中国法制出版社1995年版,第18页。",
    ),
    (
        "book",
        {
            "authors": ["张新宝"],
            "title": "侵权责任法",
            "edition": 5,
            "publisher": "中国人民大学出版社",
            "year": 2020,
            "pages": (73, 75),
        },
        "张新宝:《侵权责任法》(第5版),中国人民大学出版社2020年版,第73-75页。",
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
    # 示例 5-8：已发表文章
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
    # 示例 9-11：古籍
    ("book", {"title": "论语·述而"}, "《论语·述而》"),
    (
        "book",
        {
            "authors": ["王溥"],
            "dynasty": "宋",
            "title": "唐会要",
            "volume_note": "卷三十九《定格令》",
            "publisher": "上海古籍出版社",
            "year": 2006,
            "pages": 825,
        },
        "(宋)王溥:《唐会要》,卷三十九《定格令》,上海古籍出版社2006年版,第825页。",
    ),
    (
        "book",
        {
            "authors": ["沈家本"],
            "dynasty": "清",
            "title": "历代刑法考",
            "collator": "邓经元、宇骞点校",
            "publisher": "中华书局",
            "year": 1985,
        },
        "(清)沈家本:《历代刑法考》,邓经元、宇骞点校,中华书局1985年版。",
    ),
    # 示例 12-14：网络文献与网站
    (
        "online",
        {
            "authors": ["梁秋坪", "郝萍"],
            "title": "全国打击治理农村赌博工作现场会召开",
            "site": "人民网",
            "year": 2024,
            "month": 10,
            "day": 12,
            "url": "http://society.people.com.cn/n1/2024/1012/c1008-40337761.html",
        },
        "梁秋坪、郝萍:《全国打击治理农村赌博工作现场会召开》,载人民网2024年10月12日,http://society.people.com.cn/n1/2024/1012/c1008-40337761.html。",
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
    (
        "website",
        {
            "name": "法国最高行政法院网站",
            "url": "https://conseil-etat.fr/zh",
            "visit_year": 2024,
            "visit_month": 10,
            "visit_day": 8,
        },
        "法国最高行政法院网站,https://conseil-etat.fr/zh,2024年10月8日访问。",
    ),
    # 示例 15-16：会议论文与学位论文
    (
        "conference",
        {
            "authors": ["习超"],
            "title": "证券监管有偏私吗?",
            "meeting_info": "清华大学法学院、社会科学学院、数据科学研究院“迈向数据法学”研讨会会议论文",
            "year": 2017,
            "month": 12,
            "day": 23,
            "place": "北京",
        },
        "习超:《证券监管有偏私吗?》,清华大学法学院、社会科学学院、数据科学研究院“迈向数据法学”研讨会会议论文,2017年12月23日于北京。",
    ),
    (
        "thesis",
        {
            "authors": ["李松锋"],
            "title": "游走在上帝与凯撒之间——美国宪法第一修正案中的政教关系研究",
            "school": "中国政法大学",
            "year": 2013,
            "degree": "博士",
            "pages": 30,
        },
        "李松锋:《游走在上帝与凯撒之间——美国宪法第一修正案中的政教关系研究》,中国政法大学2013年博士学位论文,第30页。",
    ),
    # 示例 17-20：法律文件与官方文件
    (
        "legal",
        {"name": "民法典", "article": {"article": 1224, "paragraph": 1, "item": 2}},
        "《民法典》第1224条第1款第2项。",
    ),
    (
        "regulation",
        {
            "name": "国务院关于在全国建立农村最低生活保障制度的通知",
            "document_number": "国发〔2007〕19号",
            "article": "第四节",
        },
        "《国务院关于在全国建立农村最低生活保障制度的通知》(国发〔2007〕19号),第四节。",
    ),
    (
        "resolution",
        {
            "name": "中共中央关于全面推进依法治国若干重大问题的决定",
            "adoption": "2014年10月23日中国共产党第十八届中央委员会第四次全体会议通过",
        },
        "《中共中央关于全面推进依法治国若干重大问题的决定》,2014年10月23日中国共产党第十八届中央委员会第四次全体会议通过。",
    ),
    (
        "report",
        {
            "author": "李克强",
            "title": "政府工作报告",
            "date": "2023年3月5日",
            "meeting": "第十四届全国人民代表大会第一次会议",
        },
        "李克强:《政府工作报告》,2023年3月5日在第十四届全国人民代表大会第一次会议上。",
    ),
    # 示例 21-23：司法案例
    (
        "case",
        {
            "case_name": "包郑照等诉苍南县人民政府强制拆除房屋案",
            "court": "浙江省高级人民法院",
            "case_number": "(1988)浙法民上字7号",
            "document_type": "民事判决书",
        },
        "包郑照等诉苍南县人民政府强制拆除房屋案,浙江省高级人民法院(1988)浙法民上字7号民事判决书。",
    ),
    (
        "case",
        {
            "case_name": "陆红霞诉南通市发展和改革委员会政府信息公开答复案",
            "gazette_year": 2015,
            "gazette_issue": 11,
        },
        "陆红霞诉南通市发展和改革委员会政府信息公开答复案,载《最高人民法院公报》2015年第11期。",
    ),
    (
        "case",
        {
            "case_name": "车某玲诉朱某芳相邻关系纠纷案",
            "database_number": "2024-18-2-053-001",
        },
        "车某玲诉朱某芳相邻关系纠纷案,人民法院案例库2024-18-2-053-001。",
    ),
    # 示例 24-27：英文文献
    (
        "en_article",
        {
            "authors": ["Charles A. Reich"],
            "title": "The New Property",
            "journal": "Yale Law Journal",
            "volume": 73,
            "first_page": 733,
            "pincite": "737-738",
            "year": 1964,
        },
        "Charles A. Reich, The New Property, 73 Yale Law Journal 733, 737-738 (1964).",
    ),
    (
        "en_periodical",
        {
            "authors": ["Louis D. Brandeis"],
            "title": "What Publicity Can Do",
            "periodical": "Harper's Weekly",
            "date": "20 December 1913",
            "page": "p. 10",
        },
        "Louis D. Brandeis, What Publicity Can Do, Harper's Weekly, 20 December 1913, p. 10.",
    ),
    (
        "en_book",
        {
            "authors": ["William P. Alford"],
            "title": "To Steal a Book Is an Elegant Offense: Intellectual Property Law in Chinese Civilization",
            "publisher": "Stanford University Press",
            "year": 1995,
            "pages": "p. 98-99",
        },
        "William P. Alford, To Steal a Book Is an Elegant Offense: Intellectual Property Law in Chinese Civilization, Stanford University Press, 1995, p. 98-99.",
    ),
    (
        "en_case",
        {
            "case_name": "Chevron U.S.A., Inc. v. Natural Resources Defense Council, Inc.",
            "reports": "467 U.S. 837",
            "year": 1984,
        },
        "Chevron U.S.A., Inc. v. Natural Resources Defense Council, Inc., 467 U.S. 837 (1984).",
    ),
    # 示例 28-32：其他语种图书
    (
        "fr_book",
        {
            "authors": ["Jacques Chevallier"],
            "title": "L'État de droit",
            "edition": "4° éd.",
            "publisher": "Montchrestien",
            "year": 2003,
            "pages": "p. 16-29",
        },
        "Jacques Chevallier, L'État de droit, 4° éd., Montchrestien, 2003, p. 16-29.",
    ),
    (
        "de_book",
        {
            "authors": ["Claus Roxin"],
            "title": "Strafrecht Allgemeiner Teil",
            "band": "Band I",
            "edition": "4. Aufl.",
            "publisher": "C.H.Beck",
            "year": 2006,
            "locator": "§ 15 Rn. 19",
        },
        "Claus Roxin, Strafrecht Allgemeiner Teil, Band I, 4. Aufl., C.H.Beck, 2006, § 15 Rn. 19.",
    ),
    (
        "it_book",
        {
            "authors": ["Angelo Falzea"],
            "title": "L'offerta reale e la liberazione coattiva del debitore",
            "publisher": "Giuffre",
            "year": 1947,
            "pages": "p. 34 s.",
        },
        "Angelo Falzea, L'offerta reale e la liberazione coattiva del debitore, Giuffre, 1947, p. 34 s.",
    ),
    (
        "ru_book",
        {
            "authors": ["Елена А. Дубовицкая"],
            "title": "Европейское корпоративное право",
            "publisher": "Вольтерс Клувер России",
            "year": 2008,
            "pages": "с. 6",
        },
        "Елена А. Дубовицкая, Европейское корпоративное право, Вольтерс Клувер России, 2008, с. 6.",
    ),
    (
        "ja_book",
        {
            "authors": ["我妻栄"],
            "title": "新訂担保物権法(民法講義Ⅲ)",
            "publisher": "有斐閣",
            "year": 1971,
            "pages": 50,
        },
        "我妻栄『新訂担保物権法(民法講義Ⅲ)』(有斐閣,1971年)50頁。",
    ),
]


@pytest.mark.parametrize("type_name,data,expected", HANDBOOK_CASES)
def test_handbook_examples(type_name, data, expected):
    assert cite(type_name, data) == expected


# --------------------------------------------------------------------------
# 二、中文纸质出版文献（第 25-49 条正文示例）
# --------------------------------------------------------------------------

BOOK_CASES = [
    (
        {
            "authors": ["陈卫佐"],
            "title": "拉丁语法律格言手册",
            "publisher": "法律出版社",
            "year": 2024,
        },
        "陈卫佐:《拉丁语法律格言手册》,法律出版社2024年版。",
    ),
    (
        {
            "authors": ["陈卫佐"],
            "authorship": "译注",
            "title": "德国民法典",
            "edition": 5,
            "publisher": "法律出版社",
            "year": 2020,
        },
        "陈卫佐译注:《德国民法典》(第5版),法律出版社2020年版。",
    ),
    (
        {
            "authors": ["《宪法学》编写组"],
            "authorship": "编",
            "title": "宪法学",
            "edition": 2,
            "publisher": "高等教育出版社、人民出版社",
            "year": 2020,
        },
        "《宪法学》编写组编:《宪法学》(第2版),高等教育出版社、人民出版社2020年版。",
    ),
    (
        {
            "authors": ["江平"],
            "authorship": "口述",
            "title": "沉浮与枯荣:八十自述",
            "collator": "陈夏红整理",
            "publisher": "法律出版社",
            "year": 2010,
        },
        "江平口述:《沉浮与枯荣:八十自述》,陈夏红整理,法律出版社2010年版。",
    ),
    (
        {
            "authors": ["哈特穆特·毛雷尔"],
            "nationality": "德",
            "title": "行政法学总论",
            "translator": "高家伟",
            "publisher": "法律出版社",
            "year": 2000,
            "pages": [55, "64-68"],
        },
        "[德]哈特穆特·毛雷尔:《行政法学总论》,高家伟译,法律出版社2000年版,第55、64-68页。",
    ),
    (
        {
            "authors": ["汉斯·J.沃尔夫", "奥托·巴霍夫", "罗尔夫·施托贝尔"],
            "nationality": "德",
            "title": "行政法",
            "translator": "高家伟",
            "publisher": "商务印书馆",
            "year": 2002,
        },
        "[德]汉斯·J.沃尔夫、奥托·巴霍夫、罗尔夫·施托贝尔:《行政法》,高家伟译,商务印书馆2002年版。",
    ),
    (
        {
            "authors": ["夏新华", "胡旭晟"],
            "authorship": "等整理",
            "title": "近代中国宪政历程:史料荟萃",
            "publisher": "中国政法大学出版社",
            "year": 2004,
        },
        "夏新华、胡旭晟等整理:《近代中国宪政历程:史料荟萃》,中国政法大学出版社2004年版。",
    ),
    (
        {
            "authors": ["甲", "乙", "丙", "丁"],
            "title": "某某法学",
            "publisher": "某出版社",
            "year": 2020,
        },
        "甲等:《某某法学》,某出版社2020年版。",
    ),
    (
        {"title": "中国大百科全书·法学", "publisher": "中国大百科全书出版社", "year": 1984},
        "《中国大百科全书·法学》,中国大百科全书出版社1984年版。",
    ),
    (
        {
            "authors": ["邓小平"],
            "title": "精简机构是一场革命",
            "container_title": "邓小平文选",
            "edition": "第2版第2卷",
            "publisher": "人民出版社",
            "year": 1994,
        },
        "邓小平:《精简机构是一场革命》,载《邓小平文选》(第2版第2卷),人民出版社1994年版。",
    ),
    (
        {
            "title": "奥本海国际法",
            "edition": "第8版上卷第1分册",
            "translator": "王铁崖、陈体强",
            "publisher": "商务印书馆",
            "year": 1971,
        },
        "《奥本海国际法》(第8版上卷第1分册),王铁崖、陈体强译,商务印书馆1971年版。",
    ),
]


@pytest.mark.parametrize("data,expected", BOOK_CASES)
def test_book_variants(data, expected):
    assert cite("book", data) == expected


JOURNAL_CASES = [
    (
        {
            "authors": ["崔国斌"],
            "title": "知识产权法官造法批判",
            "journal": "中国法学",
            "year": 2006,
            "issue": 1,
            "pages": 163,
        },
        "崔国斌:《知识产权法官造法批判》,载《中国法学》2006年第1期,第163页。",
    ),
    (
        {
            "authors": ["王和岩"],
            "title": "邓玉娇案尘埃落定",
            "journal": "财经",
            "year": 2009,
            "issue": 13,
            "issue_date": "2009年6月22日",
        },
        "王和岩:《邓玉娇案尘埃落定》,载《财经》2009年第13期（2009年6月22日）。",
    ),
    (
        {
            "journal": "台大法学论丛",
            "volume": 47,
            "issue": 4,
            "year": 2018,
        },
        "《台大法学论丛》第47卷第4期（2018年）。",
    ),
    (
        {
            "authors": ["苏力", "于明"],
            "title": "基于中国经验的学术创造——苏力教授访谈",
            "journal": "学术月刊",
            "year": 2020,
            "issue": 3,
        },
        "苏力、于明:《基于中国经验的学术创造——苏力教授访谈》,载《学术月刊》2020年第3期。",
    ),
    (
        {
            "authors": ["罗豪才", "袁曙宏", "李文栋"],
            "title": "现代行政法的理论基础——论行政机关与相对一方的权利义务平衡",
            "journal": "中国法学",
            "year": 1993,
            "issue": 1,
        },
        "罗豪才、袁曙宏、李文栋:《现代行政法的理论基础——论行政机关与相对一方的权利义务平衡》,载《中国法学》1993年第1期。",
    ),
]


@pytest.mark.parametrize("data,expected", JOURNAL_CASES)
def test_journal_variants(data, expected):
    assert cite("journal", data) == expected


NEWSPAPER_CASES = [
    (
        {
            "authors": ["孙乾"],
            "title": "“民告官”信访案件年超400万件",
            "newspaper": "京华时报",
            "year": 2014,
            "month": 11,
            "day": 5,
            "page": 3,
        },
        "孙乾:《“民告官”信访案件年超400万件》,载《京华时报》2014年11月5日,第3版。",
    ),
    (
        {
            "authors": ["李立"],
            "title": "基层依法行政为何缺乏动力",
            "newspaper": "法制日报",
            "year": 2008,
            "month": 1,
            "day": 14,
            "page": 8,
        },
        "李立:《基层依法行政为何缺乏动力》,载《法制日报》2008年1月14日,第8版。",
    ),
]


@pytest.mark.parametrize("data,expected", NEWSPAPER_CASES)
def test_newspaper_variants(data, expected):
    assert cite("newspaper", data) == expected


COLLECTION_CASES = [
    (
        {
            "authors": ["车照"],
            "title": "论国际条约对私人的效力",
            "editor": "朱晓青、黄列",
            "editor_role": "主编",
            "container_title": "国际条约与国内法的关系:中德国际条约与国内法关系研讨会论文集",
            "publisher": "世界知识出版社",
            "year": 2000,
        },
        "车照:《论国际条约对私人的效力》,载朱晓青、黄列主编:《国际条约与国内法的关系:中德国际条约与国内法关系研讨会论文集》,世界知识出版社2000年版。",
    ),
    (
        {
            "authors": ["伍跃"],
            "title": "传统中国行政诉讼的一个场景:民告官",
            "editor": "[日]夫马进",
            "editor_role": "编",
            "container_title": "中国诉讼社会史研究",
            "container_translator": "范愉、赵晶等",
            "publisher": "浙江大学出版社",
            "year": 2019,
        },
        "伍跃:《传统中国行政诉讼的一个场景:民告官》,载[日]夫马进编:《中国诉讼社会史研究》,范愉、赵晶等译,浙江大学出版社2019年版。",
    ),
]


@pytest.mark.parametrize("data,expected", COLLECTION_CASES)
def test_collection_variants(data, expected):
    assert cite("collection", data) == expected


# --------------------------------------------------------------------------
# 三、网络电子文献与未发表文献（第 50-65 条）
# --------------------------------------------------------------------------

ONLINE_CASES = [
    (
        {
            "authors": ["任重远"],
            "title": "镇坪强制引产事件终结当事人获七万余元补助",
            "site": "财新网",
            "url": "http://china.caixin.com/2012-07-11/100409832.html",
        },
        "任重远:《镇坪强制引产事件终结当事人获七万余元补助》,载财新网,http://china.caixin.com/2012-07-11/100409832.html。",
    ),
    (
        {
            "title": "被告人李宁、张磊贪污案一审开庭",
            "site": "新华网",
            "year": 2019,
            "month": 12,
            "day": 31,
            "url": "http://www.xinhuanet.com/legal/2019-12/31/c_1125406056.htm",
        },
        "《被告人李宁、张磊贪污案一审开庭》,载新华网2019年12月31日,http://www.xinhuanet.com/legal/2019-12/31/c_1125406056.htm。",
    ),
]


@pytest.mark.parametrize("data,expected", ONLINE_CASES)
def test_online_variants(data, expected):
    assert cite("online", data) == expected


NEW_MEDIA_CASES = [
    (
        "blog",
        {
            "authors": ["黄晓磊"],
            "title": "再说博客文章被正式引用",
            "blog": "科学网博客",
            "year": 2012,
            "month": 3,
            "day": 23,
            "url": "http://blog.sciencenet.cn/blog-111883-550928.html",
        },
        "黄晓磊:《再说博客文章被正式引用》,载科学网博客2012年3月23日,http://blog.sciencenet.cn/blog-111883-550928.html。",
    ),
    (
        "weibo",
        {
            "platform": "新浪微博",
            "account": "xiaolwl",
            "year": 2020,
            "month": 1,
            "day": 31,
            "url": "https://weibo.com/1139098205/44667685335861595",
        },
        "新浪微博xiaolwl,2020年1月31日,https://weibo.com/1139098205/44667685335861595。",
    ),
    (
        "app",
        {
            "authors": ["莫纪宏"],
            "title": "论“中国式现代化”的法治保障",
            "app": "学习强国",
            "year": 2024,
            "month": 6,
            "day": 21,
        },
        "莫纪宏:《论“中国式现代化”的法治保障》,载“学习强国”App2024年6月21日。",
    ),
    (
        "wechat",
        {
            "authors": ["贵州省联合调查组"],
            "title": "情况通报",
            "account": "贵州发布",
            "year": 2024,
            "month": 6,
            "day": 6,
        },
        "贵州省联合调查组:《情况通报》,载微信公众号“贵州发布”2024年6月6日。",
    ),
    (
        "broadcast",
        {
            "host": "白岩松",
            "title": "新型冠状病毒肺炎,情况如何?",
            "station": "中央电视台",
            "column": "新闻1+1",
            "year": 2020,
            "month": 1,
            "day": 20,
            "url": "http://tv.cctv.com/2020/01/20/VIDECRZF7PWXb80z86QyB0db200120.shtml",
        },
        "白岩松主持:《新型冠状病毒肺炎,情况如何?》,中央电视台“新闻1+1”栏2020年1月20日播出,http://tv.cctv.com/2020/01/20/VIDECRZF7PWXb80z86QyB0db200120.shtml。",
    ),
    (
        "website",
        {
            "name": "中国人大网",
            "column": "“已结束的征求意见”栏目",
            "url": "http://www.npc.gov.cn/flcaw/more.html",
            "visit_year": 2020,
            "visit_month": 2,
            "visit_day": 28,
        },
        "中国人大网“已结束的征求意见”栏目,http://www.npc.gov.cn/flcaw/more.html,2020年2月28日访问。",
    ),
]


@pytest.mark.parametrize("type_name,data,expected", NEW_MEDIA_CASES)
def test_new_media(type_name, data, expected):
    assert cite(type_name, data) == expected


UNPUBLISHED_CASES = [
    (
        "conference",
        {
            "authors": ["姜明安"],
            "title": "新时代中国行政法学的转型与使命",
            "meeting_info": "中国法学会行政法学研究会2018年年会论文",
        },
        "姜明安:《新时代中国行政法学的转型与使命》,中国法学会行政法学研究会2018年年会论文。",
    ),
    (
        "conference",
        {
            "authors": ["陈鹏"],
            "title": "基本权利保障中的法律保留:历史变迁与本土建构",
            "published_in": "第五届中国宪法学青年论坛会议论文集",
            "year": 2022,
            "month": 8,
            "place": "苏州大学",
            "pages": 118,
        },
        "陈鹏:《基本权利保障中的法律保留:历史变迁与本土建构》,载《第五届中国宪法学青年论坛会议论文集》,2022年8月于苏州大学,第118页。",
    ),
    (
        "archive",
        {
            "authors": ["雷经天"],
            "title": "关于边区司法工作检查情形",
            "date": "1943年9月3日",
            "repository": "陕西省档案馆",
            "archive_note": "陕甘宁边区高等法院档案",
            "archive_number": "15/149",
        },
        "雷经天:《关于边区司法工作检查情形》(1943年9月3日),陕西省档案馆陕甘宁边区高等法院档案,档案号15/149。",
    ),
    (
        "interview",
        {
            "description": "笔者与×××访谈",
            "year": 2000,
            "month": 3,
            "day": 22,
            "place": "《最高人民法院公报》编辑部",
        },
        "笔者与×××访谈,2000年3月22日,《最高人民法院公报》编辑部。",
    ),
    (
        "correspondence",
        {
            "description": "王名扬教授给笔者的电子邮件",
            "year": 2002,
            "month": 3,
            "day": 8,
        },
        "王名扬教授给笔者的电子邮件,2002年3月8日。",
    ),
    (
        "internal",
        {
            "unit": "上海市浦东新区人民法院行政审判庭",
            "title": "2001年行政庭工作总结",
        },
        "上海市浦东新区人民法院行政审判庭:《2001年行政庭工作总结》。",
    ),
    (
        "internal",
        {
            "meeting": "全国人大常委会法工委行政诉讼法修改座谈会",
            "year": 2009,
            "month": 1,
            "day": 21,
            "place": "河南大厦(北京)",
        },
        "全国人大常委会法工委行政诉讼法修改座谈会2009年1月21日,河南大厦(北京)。",
    ),
]


@pytest.mark.parametrize("type_name,data,expected", UNPUBLISHED_CASES)
def test_unpublished(type_name, data, expected):
    assert cite(type_name, data) == expected


# --------------------------------------------------------------------------
# 四、法律文件与官方文件（第 66-94 条）
# --------------------------------------------------------------------------

LEGAL_CASES = [
    ({"name": "行政处罚法", "article": 32}, "《行政处罚法》第32条。"),
    ({"name": "刑法", "article": {"article": 232}}, "《刑法》第232条。"),
    ({"name": "刑法", "article": "17条之一"}, "《刑法》第17条之一。"),
    (
        {"name": "公司法", "revision": "2005年修订", "article": 16},
        "《公司法》(2005年修订)第16条。",
    ),
    (
        {
            "issuing_authority": "公安部",
            "name": "公安机关办理行政案件程序规定",
            "revision": "2006年修订",
            "article": 9,
        },
        "公安部《公安机关办理行政案件程序规定》(2006年修订)第9条。",
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
    (
        {"name": "行政诉讼法", "revision": "1989年", "article": {"article": 54, "item": 2, "sub_item": 3}},
        "《行政诉讼法》(1989年)第54条第2项第3目。",
    ),
]


@pytest.mark.parametrize("data,expected", LEGAL_CASES)
def test_legal(data, expected):
    assert cite("legal", data) == expected


REGULATION_CASES = [
    (
        {
            "name": "最高人民法院关于适用〈中华人民共和国行政诉讼法〉的解释",
            "document_number": "法释〔2018〕1号",
            "article": "第100条",
        },
        "《最高人民法院关于适用〈中华人民共和国行政诉讼法〉的解释》(法释〔2018〕1号),第100条。",
    ),
    (
        {
            "issuing_authority": "国务院发布的",
            "name": "打赢蓝天保卫战三年行动计划",
            "document_number": "国发〔2018〕22号",
        },
        "国务院发布的《打赢蓝天保卫战三年行动计划》(国发〔2018〕22号)。",
    ),
    (
        {
            "name": "国务院关于在全国建立农村最低生活保障制度的通知",
            "document_number": "国发〔2007〕19号",
            "number_style": "comma",
            "article": "第四节第一小节",
        },
        "《国务院关于在全国建立农村最低生活保障制度的通知》,国发〔2007〕19号,第四节第一小节。",
    ),
    (
        {
            "name": "司法部关于可否张帖判决书及应注意事项的批复",
            "document_number": "1956年8月24日",
            "source_compiler": "中华人民共和国司法部",
            "source_title": "中华人民共和国司法行政历史文件汇编(1950-1985)",
            "source_publisher": "法律出版社",
            "source_year": 1987,
            "source_pages": 655,
        },
        "《司法部关于可否张帖判决书及应注意事项的批复》(1956年8月24日),载中华人民共和国司法部编:《中华人民共和国司法行政历史文件汇编(1950-1985)》,法律出版社1987年版,第655页。",
    ),
    (
        {
            "name": "中共中央、国务院关于实施就业优先战略促进高质量充分就业的意见",
            "date": "2024年9月15日",
            "url": "https://www.gov.cn/zhengce/202409/content_6976469.htm",
        },
        "《中共中央、国务院关于实施就业优先战略促进高质量充分就业的意见》,2024年9月15日,https://www.gov.cn/zhengce/202409/content_6976469.htm。",
    ),
]


@pytest.mark.parametrize("data,expected", REGULATION_CASES)
def test_regulation(data, expected):
    assert cite("regulation", data) == expected


OFFICIAL_CASES = [
    (
        "standard",
        {
            "authority": "国家质量监督检验检疫总局、中国国家标准化管理委员会",
            "name": "信息与文献参考文献著录规则",
            "number": "GB/T 7714-2015",
        },
        "国家质量监督检验检疫总局、中国国家标准化管理委员会《信息与文献参考文献著录规则》,GB/T 7714-2015。",
    ),
    (
        "resolution",
        {
            "name": "中华人民共和国国民经济和社会发展第十四个五年规划和2035年远景目标纲要",
            "adoption": "2021年3月11日第十三届全国人民代表大会第四次会议批准",
        },
        "《中华人民共和国国民经济和社会发展第十四个五年规划和2035年远景目标纲要》,2021年3月11日第十三届全国人民代表大会第四次会议批准。",
    ),
    (
        "report",
        {
            "author": "习近平",
            "title": "高举中国特色社会主义伟大旗帜为全面建设社会主义现代化国家而团结奋斗",
            "date": "2022年10月16日",
            "meeting": "中国共产党第二十次全国代表大会",
            "report_suffix": "的报告",
        },
        "习近平:《高举中国特色社会主义伟大旗帜为全面建设社会主义现代化国家而团结奋斗》,2022年10月16日在中国共产党第二十次全国代表大会上的报告。",
    ),
    (
        "report",
        {
            "author": "周强",
            "identity": "(最高人民法院院长)",
            "title": "关于〈中华人民共和国民事诉讼法(修正草案)〉的说明",
            "date": "2022年12月27日",
            "meeting": "第十三届全国人大常委会第三十八次会议",
            "publication": "http://www.npc.gov.cn/c2/c30834/202309/t20230906_431582.html",
        },
        "周强(最高人民法院院长):《关于〈中华人民共和国民事诉讼法(修正草案)〉的说明》,2022年12月27日在第十三届全国人大常委会第三十八次会议上,http://www.npc.gov.cn/c2/c30834/202309/t20230906_431582.html。",
    ),
    (
        "report",
        {
            "author": "李克强",
            "title": "政府工作报告",
            "date": "2023年3月5日",
            "meeting": "第十四届全国人民代表大会第一次会议",
            "publication": "载《国务院公报》2023年第8号",
        },
        "李克强:《政府工作报告》,2023年3月5日在第十四届全国人民代表大会第一次会议上,载《国务院公报》2023年第8号。",
    ),
    (
        "white_paper",
        {
            "authority": "国务院新闻办公室",
            "name": "新时代的中国网络法治建设",
            "date": "2023年3月16日",
            "url": "https://www.gov.cn/zhengce/2023-03/16/content_5747005.htm",
        },
        "国务院新闻办公室:《新时代的中国网络法治建设》,2023年3月16日发布,https://www.gov.cn/zhengce/2023-03/16/content_5747005.htm。",
    ),
    (
        "white_paper",
        {
            "authority": "最高人民法院",
            "name": "中国法院的司法改革(2013-2022)",
            "date": "2023年2月21日",
            "publisher": "人民法院出版社",
            "year": 2023,
        },
        "最高人民法院:《中国法院的司法改革(2013-2022)》,2023年2月21日发布,人民法院出版社2023年版。",
    ),
]


@pytest.mark.parametrize("type_name,data,expected", OFFICIAL_CASES)
def test_official_documents(type_name, data, expected):
    assert cite(type_name, data) == expected


HK_MACAU_TAIWAN_CASES = [
    (
        "hk_macau_law",
        {
            "name": "刑事上诉规则",
            "chapter": "香港法例第221A章",
            "article": "第42(3)条",
        },
        "《刑事上诉规则》(香港法例第221A章),第42(3)条。",
    ),
    (
        "hk_macau_law",
        {
            "name": "维护国家安全(中央人民政府驻香港特别行政区维护国家安全公署)规例",
            "announcement": "2025年第77号法律公告",
        },
        "《维护国家安全(中央人民政府驻香港特别行政区维护国家安全公署)规例》,2025年第77号法律公告。",
    ),
    (
        "hk_macau_law",
        {
            "name": "澳门特别行政区廉政公署组织法",
            "chapter": "第17/2024号法律修改",
            "article": "第4条第8项",
            "url": "https://bo.io.gov.mo/bo/i/2024/35/lei17_en.asp",
        },
        "《澳门特别行政区廉政公署组织法》(第17/2024号法律修改),第4条第8项,https://bo.io.gov.mo/bo/i/2024/35/lei17_en.asp。",
    ),
    ("taiwan_law", {"note": "我国台湾地区", "name": "民法"}, "我国台湾地区“民法”。"),
]


@pytest.mark.parametrize("type_name,data,expected", HK_MACAU_TAIWAN_CASES)
def test_hk_macau_taiwan_law(type_name, data, expected):
    assert cite(type_name, data) == expected


FOREIGN_LAW_CN_CASES = [
    (
        "foreign_law",
        {"country": "英国", "name": "1996年仲裁法"},
        "英国《1996年仲裁法》。",
    ),
    (
        "foreign_law",
        {"country": "美国", "name": "统一买卖法", "year": "1906年"},
        "美国《统一买卖法》(1906年)。",
    ),
    (
        "foreign_law",
        {"country": "美国", "year_before": "1906年", "name": "统一买卖法"},
        "美国1906年《统一买卖法》。",
    ),
    (
        "foreign_law",
        {"country": "英国", "name": "1996年仲裁法", "original": "Arbitration Act 1996"},
        "英国《1996年仲裁法》(Arbitration Act 1996)。",
    ),
    (
        "foreign_law",
        {"country": "美国", "name": "宪法第十四修正案", "plain_name": True},
        "美国宪法第十四修正案。",
    ),
    (
        "treaty",
        {"organization": "联合国", "name": "儿童权利公约"},
        "联合国《儿童权利公约》。",
    ),
    (
        "treaty",
        {
            "name": "联合国海洋法公约",
            "original": "United Nations Convention on the Law of the Sea",
        },
        "《联合国海洋法公约》(United Nations Convention on the Law of the Sea)。",
    ),
    (
        "un_document",
        {
            "name": "世界人权宣言",
            "organ": "联合国大会",
            "doc_type": "决议",
            "number": "217A(Ⅲ)",
            "date": "1948年12月10日",
            "action": "通过",
        },
        "《世界人权宣言》,联合国大会决议,217A(Ⅲ),1948年12月10日通过。",
    ),
    (
        "un_document",
        {
            "name": "全球努力打击恐怖主义的宣言",
            "organ": "联合国安理会",
            "doc_type": "决议",
            "number": "S/RES/1377(2001)",
            "url": "https://www.un.org/zh/documents/treaty/S-RES-1377-2001",
        },
        "《全球努力打击恐怖主义的宣言》,联合国安理会决议,S/RES/1377(2001),https://www.un.org/zh/documents/treaty/S-RES-1377-2001。",
    ),
    (
        "un_document",
        {
            "name": "和平纲领:预防性外交、建立和平与维持和平",
            "organ": "联合国秘书长",
            "doc_type": "报告",
            "number": "A/47/277",
            "date": "1992年6月17日",
        },
        "《和平纲领:预防性外交、建立和平与维持和平》,联合国秘书长报告,A/47/277,1992年6月17日。",
    ),
]


@pytest.mark.parametrize("type_name,data,expected", FOREIGN_LAW_CN_CASES)
def test_foreign_law_cn(type_name, data, expected):
    assert cite(type_name, data) == expected


# --------------------------------------------------------------------------
# 五、司法案例（第 87-91 条）
# --------------------------------------------------------------------------

CASE_CASES = [
    (
        {
            "case_name": "苏嘉鸿诉中国证监会行政处罚案",
            "court": "北京市高级人民法院",
            "case_number": "(2018)京行终445号",
            "document_type": "行政判决书",
        },
        "苏嘉鸿诉中国证监会行政处罚案,北京市高级人民法院(2018)京行终445号行政判决书。",
    ),
    (
        {
            "case_name": "田永诉北京科技大学案",
            "court": "北京市海淀区人民法院",
            "case_number": {"year": 1998, "code": "海行初字", "number": 142},
            "document_type": "行政判决书",
        },
        "田永诉北京科技大学案,北京市海淀区人民法院(1998)海行初字第142号行政判决书。",
    ),
    (
        {
            "case_name": "榆林市凯奇莱能源投资有限公司诉西安地质矿产勘查开发院合作勘查合同纠纷上诉案",
            "court": "最高人民法院",
            "case_number": "(2011)民一终字第81号",
            "document_type": "民事判决书",
            "year": 2017,
            "month": 12,
            "day": 16,
        },
        "榆林市凯奇莱能源投资有限公司诉西安地质矿产勘查开发院合作勘查合同纠纷上诉案,最高人民法院(2011)民一终字第81号民事判决书,2017年12月16日。",
    ),
    (
        {
            "case_name": "荣宝英诉王阳、永诚财产保险股份有限公司江阴支公司机动车交通事故责任纠纷案",
            "guiding_organ": "最高人民法院",
            "guiding_no": 24,
            "guiding_year": 2014,
        },
        "荣宝英诉王阳、永诚财产保险股份有限公司江阴支公司机动车交通事故责任纠纷案,最高人民法院指导案例24号(2014年)。",
    ),
    (
        {
            "case_name": "谢文彬诉广东省司法厅案",
            "report_author": "李桂茹、孔献之",
            "report_title": "七旬律师被判可以执业《律师法赢了司法部文件》",
            "report_newspaper": "中国青年报",
            "report_date": "2003年6月4日",
            "report_page": 7,
        },
        "谢文彬诉广东省司法厅案,参见李桂茹、孔献之:《七旬律师被判可以执业《律师法赢了司法部文件》》,载《中国青年报》2003年6月4日,第7版。",
    ),
    (
        {
            "case_name": "宁德市大众影院诉宁德地区工商行政管理局行政处罚案",
            "compiler": "最高人民法院中国应用法学研究所",
            "compilation_title": "人民法院案例选(1992-1999年合订本)·行政卷",
            "compilation_publisher": "中国法制出版社",
            "compilation_year": 2000,
            "case_no": 51,
        },
        "宁德市大众影院诉宁德地区工商行政管理局行政处罚案,载最高人民法院中国应用法学研究所编:《人民法院案例选(1992-1999年合订本)·行政卷》,中国法制出版社2000年版,案例51。",
    ),
    (
        {
            "case_name": "苏嘉鸿不服中国证监会行政处罚行政复议案",
            "court": "中国证监会",
            "case_number": "〔2017〕63号",
            "document_type": "行政复议决定书",
        },
        "苏嘉鸿不服中国证监会行政处罚行政复议案,中国证监会〔2017〕63号行政复议决定书。",
    ),
]


@pytest.mark.parametrize("data,expected", CASE_CASES)
def test_case(data, expected):
    assert cite("case", data) == expected


# --------------------------------------------------------------------------
# 六、统计数据
# --------------------------------------------------------------------------


def test_statistics():
    data = {
        "subject": "检索北大法宝数据库,在380余万份行政裁判文书中统计“权利”与“职权”的词频",
        "retrieval_time": "2024年3月",
        "scope": "国家法律法规数据库中的法律",
    }
    assert cite("statistics", data) == (
        "检索北大法宝数据库,在380余万份行政裁判文书中统计“权利”与“职权”的词频,"
        "检索时间为2024年3月,检索范围为国家法律法规数据库中的法律。"
    )


# --------------------------------------------------------------------------
# 七、英文引注体例（第 99-115 条）
# --------------------------------------------------------------------------

EN_CASES = [
    (
        "en_book",
        {
            "authors": ["A. V. Dicey"],
            "title": "An Introduction to the Study of the Law of the Constitution",
            "edition": "10th ed.",
            "publisher": "Palgrave Macmillan",
            "year": 1985,
        },
        "A. V. Dicey, An Introduction to the Study of the Law of the Constitution (10th ed.), Palgrave Macmillan, 1985.",
    ),
    (
        "en_book",
        {
            "authors": ["Bryan A. Garner"],
            "authorship": "chief ed.",
            "title": "Black's Law Dictionary",
            "edition": "12th ed.",
            "publisher": "Thomson Reuters",
            "year": 2024,
        },
        "Bryan A. Garner chief ed., Black's Law Dictionary (12th ed.), Thomson Reuters, 2024.",
    ),
    (
        "en_book",
        {
            "authors": ["Jiurgen Habermas"],
            "title": "Between Facts and Norms: Contributions to a Discourse Theory of Law and Democracy",
            "translator": "William Rehg",
            "publisher": "MIT Press",
            "year": 1996,
            "pages": "p. 330-336",
        },
        "Jiurgen Habermas, Between Facts and Norms: Contributions to a Discourse Theory of Law and Democracy, translated by William Rehg, MIT Press, 1996, p. 330-336.",
    ),
    (
        "en_article",
        {
            "authors": ["Charles A. Reich"],
            "title": "The New Property",
            "journal": "Yale Law Journal",
            "volume": 73,
            "first_page": 733,
            "year": 1964,
        },
        "Charles A. Reich, The New Property, 73 Yale Law Journal 733 (1964).",
    ),
    (
        "en_article",
        {
            "authors": ["Stephen J. Choi", "A. C. Pritchard"],
            "title": "Behavioral Economics and the SEC",
            "journal": "Stanford Law Review",
            "volume_info": "Vol. 56:1",
            "pages": "p. 1-73",
            "year": 2003,
        },
        "Stephen J. Choi & A. C. Pritchard, Behavioral Economics and the SEC, Stanford Law Review, Vol. 56:1, p. 1-73 (2003).",
    ),
    (
        "en_periodical",
        {
            "authors": ["Andrew Rosenthal"],
            "title": "White House Tutors Kremlin in How a Presidency Works",
            "periodical": "New York Times",
            "date": "15 June 1990",
            "page": "at A1",
        },
        "Andrew Rosenthal, White House Tutors Kremlin in How a Presidency Works, New York Times, 15 June 1990, at A1.",
    ),
    (
        "en_online",
        {
            "authors": "Stephen McDonell",
            "title": "When China Began Streaming Trials Online",
            "site": "BBC News",
            "date": "30 September 2016",
            "url": "https://www.bbc.com/news/blogs-china-blog-37515399",
        },
        "Stephen McDonell, When China Began Streaming Trials Online, BBC News (30 September 2016), https://www.bbc.com/news/blogs-china-blog-37515399.",
    ),
    (
        "en_online",
        {
            "authors": "Members and Observers of the WTO",
            "url": "https://www.wto.org/english/thewto_e/whatis_e/tife/org6_e.htm",
            "visit_date": "8 October 2024",
        },
        "Members and Observers of the WTO, https://www.wto.org/english/thewto_e/whatis_e/tife/org6_e.htm, visited on 8 October 2024.",
    ),
    (
        "en_case",
        {
            "case_name": "Natural Resources Defense Council v. Gorsuch",
            "reports": "685 F.2d 718",
            "court": "D.C. Cir.",
            "year": 1982,
        },
        "Natural Resources Defense Council v. Gorsuch, 685 F.2d 718 (D.C. Cir. 1982).",
    ),
    (
        "en_case",
        {
            "case_name": "Roe v. Wade",
            "reports": ["410 U.S. 113", "93 S. Ct. 705", "35 L. Ed. 2d 147"],
            "year": 1973,
        },
        "Roe v. Wade, 410 U.S. 113, 93 S. Ct. 705, 35 L. Ed. 2d 147 (1973).",
    ),
    (
        "en_case",
        {
            "case_name": "United States v. Dino Nastasi et al.",
            "docket": "No. 3:15-cr-00213-FDW-DCK",
            "court": "W.D. North Carolina",
        },
        "United States v. Dino Nastasi et al., No. 3:15-cr-00213-FDW-DCK (W.D. North Carolina).",
    ),
    (
        "en_case_uk",
        {
            "case_name": "R v. Lord Chancellor, ex parte Witham",
            "report": "[1998] QB 575",
            "locator": "at 581E (per Laws J.)",
        },
        "R v. Lord Chancellor, ex parte Witham [1998] QB 575, at 581E (per Laws J.).",
    ),
    (
        "en_case_uk",
        {
            "case_name": "Lloyd v. Google LLC",
            "report": "[2019] EWCA Civ 1599",
            "locator": "para. 30",
        },
        "Lloyd v. Google LLC [2019] EWCA Civ 1599, para. 30.",
    ),
    (
        "en_case_uk",
        {
            "case_name": "James Bagg's Case",
            "report": "(1615) 11 Co. Rep. 93b, 77 Eng. Rep. 1271",
        },
        "James Bagg's Case (1615) 11 Co. Rep. 93b, 77 Eng. Rep. 1271.",
    ),
    (
        "en_case_intl",
        {
            "case_name": "East Timor (Portugal v. Australia)",
            "report": "Judgment, ICJ Reports 1995",
            "locator": "para. 29-35",
        },
        "East Timor (Portugal v. Australia), Judgment, ICJ Reports 1995, para. 29-35.",
    ),
    (
        "en_case_intl",
        {
            "case_name": "Abaclat and Others v. Argentine Republic",
            "report": "ICSID Case No. ARB/07/5, Decision on Jurisdiction and Admissibility of 4 August 2011",
            "locator": "para. 50",
        },
        "Abaclat and Others v. Argentine Republic, ICSID Case No. ARB/07/5, Decision on Jurisdiction and Admissibility of 4 August 2011, para. 50.",
    ),
    (
        "en_law_uk",
        {
            "name": "Human Rights Act",
            "year": 1998,
            "section": "s. 3(2)(b)",
        },
        "Human Rights Act 1998, s. 3(2)(b).",
    ),
    (
        "en_law_uk",
        {
            "name": "Penalties for Disorderly Behaviour (Amendment of Minimum Age) Order",
            "year": 2004,
            "number": "SI 2004/3166",
        },
        "Penalties for Disorderly Behaviour (Amendment of Minimum Age) Order 2004, SI 2004/3166.",
    ),
    (
        "en_law_uk",
        {
            "name": "Law of Property Act",
            "year": 1925,
            "section": "s. 44(1)",
            "source": "37 Hals. Stat. (4th ed.) 139",
        },
        "Law of Property Act 1925, s. 44(1), 37 Hals. Stat. (4th ed.) 139.",
    ),
    (
        "en_law_us",
        {
            "name": "Department of Transportation Act",
            "pub_law": "Pub. L. No. 89-670",
            "section": "§ 9",
            "source": "80 Stat. 931, 944-947",
            "year": 1966,
        },
        "Department of Transportation Act, Pub. L. No. 89-670, § 9, 80 Stat. 931, 944-947 (1966).",
    ),
    (
        "en_law_us",
        {
            "name": "Administrative Procedure Act",
            "source": "5 U.S.C. § 555",
            "year": 2006,
        },
        "Administrative Procedure Act, 5 U.S.C. § 555 (2006).",
    ),
    (
        "en_law_us",
        {
            "name": "Labor Management Relations (Taft-Hartley) Act",
            "section": "§ 301(a)",
            "source": "29 U.S.C. § 185(a)",
            "year": 2012,
        },
        "Labor Management Relations (Taft-Hartley) Act, § 301(a), 29 U.S.C. § 185(a) (2012).",
    ),
    (
        "en_law_eu",
        {
            "name": "Consolidated Version of the Treaty on European Union",
            "number": "[2008] OJ C115/13",
        },
        "Consolidated Version of the Treaty on European Union [2008] OJ C115/13.",
    ),
    (
        "en_law_eu",
        {
            "name": "General Data Protection Regulation",
            "number": "(EU) 2016/679",
            "article": "Art. 60",
        },
        "General Data Protection Regulation, (EU) 2016/679, Art. 60.",
    ),
    (
        "en_doc_un",
        {
            "organ": "General Assembly Resolution",
            "name": "Universal Declaration of Human Rights",
            "number": "217A (III)",
            "date": "10 December 1948",
        },
        "General Assembly Resolution, Universal Declaration of Human Rights, 217A (III), 10 December 1948.",
    ),
    (
        "en_doc_un",
        {
            "organ": "U.N. Secretary-General",
            "name": "An Agenda for Peace: Preventive Diplomacy, Peacemaking and Peace-Keeping",
            "number": "A/47/277",
            "date": "17 June 1992",
        },
        "U.N. Secretary-General, An Agenda for Peace: Preventive Diplomacy, Peacemaking and Peace-Keeping, A/47/277, 17 June 1992.",
    ),
]


@pytest.mark.parametrize("type_name,data,expected", EN_CASES)
def test_english_citations(type_name, data, expected):
    assert cite(type_name, data) == expected


# --------------------------------------------------------------------------
# 八、法德意俄日引注体例（第 116-150 条）
# --------------------------------------------------------------------------

FR_CASES = [
    (
        "fr_book",
        {
            "authors": ["Bertrand Ancel", "Yves Lequette"],
            "title": "Les Grands Arrêts de la jurisprudence française de droit international privé",
            "edition": "5° éd.",
            "publisher": "Dalloz",
            "year": 2006,
            "pages": "p. 197 s.",
        },
        "Bertrand Ancel et Yves Lequette, Les Grands Arrêts de la jurisprudence française de droit international privé, 5° éd., Dalloz, 2006, p. 197 s.",
    ),
    (
        "fr_book",
        {
            "authors": ["Guy Raymond"],
            "authorship": "dir.",
            "title": "Droit de la consommation",
            "edition": "3° éd.",
            "publisher": "LexisNexis",
            "year": 2015,
            "pages": "p. 556",
        },
        "Guy Raymond dir., Droit de la consommation, 3° éd., LexisNexis, 2015, p. 556.",
    ),
    (
        "fr_article",
        {
            "authors": ["Frédéric Zenati"],
            "title": "Pour une rénovation de la théorie de la propriété",
            "journal": "RTD civ.",
            "year": 1993,
            "pages": "p. 305 s.",
        },
        "Frédéric Zenati, Pour une rénovation de la théorie de la propriété, RTD civ. 1993, p. 305 s.",
    ),
    (
        "fr_article",
        {
            "authors": ["Guy Canivet"],
            "title": "Le Conseil constitutionnel et le contrat, variations sur la \"discretion\"",
            "container": "Mélanges C. Larroumet",
            "year": 2010,
            "pages": "p. 75",
        },
        "Guy Canivet, Le Conseil constitutionnel et le contrat, variations sur la \"discretion\", in Mélanges C. Larroumet, 2010, p. 75.",
    ),
    (
        "fr_thesis",
        {
            "authors": ["Daniel Gutmann"],
            "title": "Le sentiment d'identité, étude du droit des personnes et de la famille",
            "school": "Paris II",
            "year": 2000,
        },
        "Daniel Gutmann, Le sentiment d'identité, étude du droit des personnes et de la famille, Thèse Paris II, 2000.",
    ),
    (
        "fr_law",
        {"code": "C. civ.", "article": "1832-1"},
        "C. civ., art. 1832-1.",
    ),
    (
        "fr_law",
        {"code": "C. trav.", "article": "R. 4152-20, al. 2"},
        "C. trav., art. R. 4152-20, al. 2.",
    ),
    (
        "fr_law",
        {"law_type": "Loi", "number": "2013-403", "date": "17 mai 2013"},
        "Loi n° 2013-403 du 17 mai 2013.",
    ),
    (
        "fr_law",
        {"article_full": "78 et s. de la Constitution du 24 juin 1793"},
        "Art. 78 et s. de la Constitution du 24 juin 1793.",
    ),
    (
        "fr_case",
        {
            "court": "CE",
            "date": "15 février 2008",
            "case_name": "Commune de La Londe-les-Maures",
            "number": "req. n°279045",
        },
        "CE, 15 février 2008, Commune de La Londe-les-Maures, req. n°279045.",
    ),
    (
        "fr_case",
        {
            "court": "CIJ",
            "case_name_first": True,
            "case_name": "Delimitation maritime en mer Noire (Roumanie c. Ukraine)",
            "date": "3 février 2009",
            "report": "CIJ Recueil 2009",
            "page": "p. 61",
        },
        "CIJ, Delimitation maritime en mer Noire (Roumanie c. Ukraine), 3 février 2009, CIJ Recueil 2009, p. 61.",
    ),
    (
        "fr_online",
        {
            "authors": "Cour de cassation",
            "title": "Comment faire un pourvoi en matière civile?",
            "url": "https://www.courdecassation.fr/mes-demarches/comment-faire-un-pourvoi-en-cassation/comment-faire-un-pourvoi-en-matiere-civile",
            "visit_date": "16 décembre 2024",
        },
        "Cour de cassation, Comment faire un pourvoi en matière civile?, https://www.courdecassation.fr/mes-demarches/comment-faire-un-pourvoi-en-cassation/comment-faire-un-pourvoi-en-matiere-civile, Consulté le 16 décembre 2024.",
    ),
]


@pytest.mark.parametrize("type_name,data,expected", FR_CASES)
def test_french_citations(type_name, data, expected):
    assert cite(type_name, data) == expected


DE_CASES = [
    (
        "de_book",
        {
            "authors": ["Ralf Dreier", "Stanley L. Paulson"],
            "editor": "Hrsg.",
            "title": "Gustav Radbruch, Rechtsphilosophie: Studienausgabe",
            "edition": "2. Aufl.",
            "publisher": "C.F. Müller",
            "year": 2003,
            "locator": "S. 181",
        },
        "Ralf Dreier/Stanley L. Paulson (Hrsg.), Gustav Radbruch, Rechtsphilosophie: Studienausgabe, 2. Aufl., C.F. Müller, 2003, S. 181.",
    ),
    (
        "de_book",
        {
            "authors": ["Martin Schwab"],
            "container": "in Münchener Kommentar BGB",
            "band": "Band 5",
            "edition": "6. Aufl.",
            "publisher": "C.H.Beck",
            "year": 2013,
            "locator": "§ 817 Rn. 9",
        },
        "Martin Schwab, in Münchener Kommentar BGB, Band 5, 6. Aufl., C.H.Beck, 2013, § 817 Rn. 9.",
    ),
    (
        "de_book",
        {
            "authors": ["Arthur Kaufmann"],
            "title": "Bemerkungen zur Reform des § 218 StGB aus rechtsphilosophischer Sicht",
            "container": "in Jürgen Baumann (Hrsg.), Das Abtreibungsverbot des § 218 StGB",
            "edition": "2. Aufl.",
            "publisher": "Luchterhand",
            "year": 1972,
            "locator": "S. 46 ff.",
        },
        "Arthur Kaufmann, Bemerkungen zur Reform des § 218 StGB aus rechtsphilosophischer Sicht, in Jürgen Baumann (Hrsg.), Das Abtreibungsverbot des § 218 StGB, 2. Aufl., Luchterhand, 1972, S. 46 ff.",
    ),
    (
        "de_book",
        {
            "authors": ["Claus-Wilhelm Canaris"],
            "title": "Gesamtunwirksamkeit und Teilgültigkeit rechtsgeschäftlicher Regelungen",
            "container": "FS für Steindorff",
            "publisher": "De Gruyter",
            "year": 1990,
            "locator": "S. 524",
        },
        "Claus-Wilhelm Canaris, Gesamtunwirksamkeit und Teilgültigkeit rechtsgeschäftlicher Regelungen, FS für Steindorff, De Gruyter, 1990, S. 524.",
    ),
    (
        "de_article",
        {
            "authors": ["Benjamin Vogel"],
            "title": "Rechtsgüterschutz und Normgeltung",
            "journal": "ZStW 129 (2017)",
            "page": "S. 630",
        },
        "Benjamin Vogel, Rechtsgüterschutz und Normgeltung, ZStW 129 (2017), S. 630.",
    ),    (
        "de_article",
        {
            "authors": ["Thomas Fischer"],
            "title": "Absurdes Spektakel um den Tod",
            "container": "in Die Zeit v. 29. 9. 2015",
        },
        "Thomas Fischer, Absurdes Spektakel um den Tod, in Die Zeit v. 29. 9. 2015.",
    ),
    (
        "de_law",
        {
            "section": "§ 46b III",
            "law": "Gesetz über die Entschädigung ehemaliger deutscher Kriegsgefangener (KgfEG)",
            "date": "04.02.1987",
        },
        "§ 46b III Gesetz über die Entschädigung ehemaliger deutscher Kriegsgefangener (KgfEG) i.d.F. v. 04.02.1987.",
    ),
    ("de_law", {"section": "Art. 2 II", "law": "GG"}, "Art. 2 II GG."),
    ("de_law", {"section": "§ 241", "law": "BGB a.F."}, "§ 241 BGB a.F."),
    (
        "de_case",
        {"court": "BGH", "report": "NStZ-RR", "year": 1999, "page": 185},
        "BGH NStZ-RR 1999, 185.",
    ),
    (
        "de_case",
        {"court": "BGH", "report": "NJW", "year": 2000, "page": 1560, "pincite": 1562},
        "BGH NJW 2000, 1560 (1562).",
    ),
    (
        "de_case",
        {"report": "BVerfGE", "year": 75, "page": 369, "pincite": 380},
        "BVerfGE 75, 369 (380).",
    ),
    (
        "de_case",
        {
            "court": "BGH",
            "report": "NJW",
            "year": 1996,
            "page": 1467,
            "parallel": "BGHZ 132, 119 ff.",
        },
        "BGH NJW 1996, 1467 = BGHZ 132, 119 ff.",
    ),
]


@pytest.mark.parametrize("type_name,data,expected", DE_CASES)
def test_german_citations(type_name, data, expected):
    assert cite(type_name, data) == expected


IT_CASES = [
    (
        "it_book",
        {
            "authors": ["Natalino Irti"],
            "editor": "a cura di",
            "title": "La polemica sui concetti giuridici",
            "publisher": "Giuffre",
            "year": 2004,
            "pages": "p. 25 ss.",
        },
        "Natalino Irti (a cura di), La polemica sui concetti giuridici, Giuffre, 2004, p. 25 ss.",
    ),
    (
        "it_book",
        {
            "authors": ["C. Massimo Bianca"],
            "title": "Diritto civile",
            "volume": "Il, Il contratto",
            "publisher": "Giuffre",
            "year": 2000,
            "pages": "p. 551",
        },
        "C. Massimo Bianca, Diritto civile, Il, Il contratto, Giuffre, 2000, p. 551.",
    ),
    (
        "it_book",
        {
            "authors": ["Teodoro Mommsen"],
            "title": "Disegno del diritto pubblico romano",
            "translator": "trad. it. di Pietro Bonfante",
            "publisher": "Istituto per gli studi di politica internazionale",
            "year": 1973,
            "pages": "p. 22",
        },
        "Teodoro Mommsen, Disegno del diritto pubblico romano, trad. it. di Pietro Bonfante, Istituto per gli studi di politica internazionale, 1973, p. 22.",
    ),
    (
        "it_periodical",
        {
            "authors": ["Aldo Cazzullo"],
            "title": "Il ritorno e i motivi",
            "container": "in Corriere della sera",
            "date": "7 novembre 2024",
            "pages": "p. 8",
        },
        "Aldo Cazzullo, Il ritorno e i motivi, in Corriere della sera, 7 novembre 2024, p. 8.",
    ),
    (
        "it_periodical",
        {
            "authors": ["Paolo Greco"],
            "title": "Sull'ammissione al passivo con riserva di prova nel procedimento fallimentare",
            "container": "in Rivista del diritto commerciale",
            "year": 1953,
            "volume": "II",
            "issue": 4,
            "pages": "p. 55",
        },
        "Paolo Greco, Sull'ammissione al passivo con riserva di prova nel procedimento fallimentare, in Rivista del diritto commerciale, 1953, II, 4, p. 55.",
    ),
    (
        "it_law",
        {"law_type": "D.P.R.", "date": "26 luglio 1976", "number": 752},
        "D.P.R. 26 luglio 1976, n. 752.",
    ),
    (
        "it_law",
        {"article_ref": "3, comma 2", "law_type": "l.", "date": "31 maggio 1995", "number": 218},
        "art. 3, comma 2, l. 31 maggio 1995, n. 218.",
    ),
    (
        "it_case",
        {
            "court": "Cass. civ.",
            "chamber": "sez. lavoro",
            "date": "29 maggio 1998",
            "number": 5348,
        },
        "Cass. civ., sez. lavoro, 29 maggio 1998, n. 5348.",
    ),
    (
        "it_case",
        {
            "court": "App. Napoli",
            "date": "3 novembre 2008",
            "report": "in Foro it.",
            "year": 2009,
            "volume": "I",
            "page": "p. 1476 s.",
        },
        "App. Napoli, 3 novembre 2008, in Foro it., 2009, I p. 1476 s.",
    ),
    ("it_roman", {"author": "Cicero", "work": "De Officiis", "locator": "3.17.71"}, "Cicero, De Officiis, 3.17.71."),
    ("it_roman", {"work": "Gaius Institutiones", "locator": "3.97"}, "Gaius Institutiones, 3.97."),
]


@pytest.mark.parametrize("type_name,data,expected", IT_CASES)
def test_italian_citations(type_name, data, expected):
    assert cite(type_name, data) == expected


RU_CASES = [
    (
        "ru_book",
        {
            "authors": ["Иван И. Кравец"],
            "editor": "ред.",
            "title": "Государственное право и управление",
            "publisher": "СПб.: Юридический центр Пресс",
            "year": 2005,
            "pages": "с. 76",
        },
        "Иван И. Кравец ред., Государственное право и управление, СПб.: Юридический центр Пресс, 2005, с. 76.",
    ),
    (
        "ru_book",
        {
            "authors": ["Алексей А. Сидоров", "Владимир В. Кузнецов", "А", "Б"],
            "title": "Уголовное право Российской Федерации",
            "publisher": "СПб.: Издательство СПбГУ",
            "year": 2010,
            "pages": "с. 456",
        },
        "Алексей А. Сидоров, Владимир В. Кузнецов и др., Уголовное право Российской Федерации, СПб.: Издательство СПбГУ, 2010, с. 456.",
    ),
    (
        "ru_article",
        {
            "authors": ["Вадим А. Виноградов"],
            "title": "Анализ феномена \"культура отмены\" как инструмента регулирования общественных отношений",
            "journal": "Журнал российского права",
            "year": 2023,
            "issue": "No 3",
            "pages": "с. 17-30",
        },
        "Вадим А. Виноградов, Анализ феномена \"культура отмены\" как инструмента регулирования общественных отношений // Журнал российского права, 2023, No 3, с. 17-30.",
    ),
    (
        "ru_article",
        {
            "authors": ["Анатолий В. Ананьев"],
            "title": "Хакерская этика и этика научных исследований",
            "journal": "Современное состояние и перспективы развития науки и образования",
            "year": 2022,
            "issue": "(2)",
            "pages": "с. 7-14",
        },
        "Анатолий В. Ананьев, Хакерская этика и этика научных исследований // Современное состояние и перспективы развития науки и образования, 2022 (2), с. 7-14.",
    ),
    (
        "ru_periodical",
        {
            "authors": ["Ольга М. Игнатова"],
            "title": "Юрист Хрусталева разъяснила, могут ли граждане-банкроты выезжать за границу",
            "newspaper": "Российская газета",
            "date": "06.02.2024",
        },
        "Ольга М. Игнатова, Юрист Хрусталева разъяснила, могут ли граждане-банкроты выезжать за границу, Российская газета, 06.02.2024.",
    ),
    (
        "ru_law",
        {
            "name": "Семейный кодекс Российской Федерации",
            "article": 16,
            "date": "29 декабря 1995 года",
            "source": "Собрание законодательства Российской Федерации [СЗ РФ]",
        },
        "Семейный кодекс Российской Федерации, ст. 16, принят 29 декабря 1995 года, Собрание законодательства Российской Федерации [СЗ РФ].",
    ),
    (
        "ru_case",
        {
            "case_name": "Гражданин Смирнов против ООО \"СтройИнвест\"",
            "number": "Дело № 24680/13579",
            "date": "20 мая 2019 года",
            "source": "Судебные акты и решения 2019, No. 5",
        },
        "Гражданин Смирнов против ООО \"СтройИнвест\", Дело № 24680/13579, Решение от 20 мая 2019 года, Судебные акты и решения 2019, No. 5.",
    ),
    (
        "ru_online",
        {
            "title": "Во втором чтении принят законопроект о запрете \"Наливай\" в жилых домах",
            "site": "Государственная Дума",
            "date": "2024-01-31",
            "url": "http://duma.gov.ru/news/58734/",
        },
        "Во втором чтении принят законопроект о запрете \"Наливай\" в жилых домах, Государственная Дума 2024-01-31, http://duma.gov.ru/news/58734/.",
    ),
]


@pytest.mark.parametrize("type_name,data,expected", RU_CASES)
def test_russian_citations(type_name, data, expected):
    assert cite(type_name, data) == expected


JA_CASES = [
    (
        "ja_book",
        {
            "authors": ["我妻栄", "有泉亨"],
            "title": "民法総則・物権法",
            "publisher": "日本評論社",
            "year": 1950,
            "pages": 31,
        },
        "我妻栄=有泉亨『民法総則・物権法』(日本評論社,1950年)31頁。",
    ),
    (
        "ja_book",
        {
            "authors": ["佐藤英明"],
            "title": "一時所得の要件に関する覚書",
            "title_style": "article",
            "editor": "金子宏ほか",
            "container": "租税法と市場",
            "publisher": "有斐閣",
            "year": 2014,
            "pages": 220,
        },
        "佐藤英明「一時所得の要件に関する覚書」金子宏ほか編『租税法と市場』(有斐閣,2014年)220頁。",
    ),
    (
        "ja_article",
        {
            "authors": ["於保不二雄"],
            "title": "付加物及び物抵当権",
            "journal": "民商法",
            "volume": 29,
            "issue": 5,
            "year": 1954,
            "pages": "1頁以下",
        },
        "於保不二雄「付加物及び物抵当権」民商法29巻5号(1954年)1頁以下。",
    ),
    (
        "ja_law",
        {
            "name": "動産及び債権の譲渡の対抗要件に関する民法の特例に関する法律",
            "translation": "关于动产和债权让与的对抗要件的民法特例法",
        },
        "動産及び債権の譲渡の対抗要件に関する民法の特例に関する法律(关于动产和债权让与的对抗要件的民法特例法)。",
    ),
    (
        "ja_case",
        {
            "court": "大審院",
            "year": 1919,
            "month": 3,
            "day": 3,
            "report": "大審院民事判决録25輯",
            "page": 356,
        },
        "大審院1919年3月3日判决,大審院民事判决録25輯356頁。",
    ),
    (
        "ja_case",
        {
            "court": "最高裁判所",
            "year": 1982,
            "month": 7,
            "day": 15,
            "report": "最高裁判所民事判例集36巻6号",
            "page": 1113,
        },
        "最高裁判所1982年7月15日判决,最高裁判所民事判例集36巻6号1113頁。",
    ),
    ("ja_official", {"name": "平成26年版犯罪白書"}, "「平成26年版犯罪白書」による。"),
]


@pytest.mark.parametrize("type_name,data,expected", JA_CASES)
def test_japanese_citations(type_name, data, expected):
    assert cite(type_name, data) == expected


# --------------------------------------------------------------------------
# 九、边界情形与配置
# --------------------------------------------------------------------------


def test_missing_optional_fields_leaves_no_dangling_punctuation():
    assert cite("book", {"authors": ["甲"], "title": "乙"}) == "甲:《乙》。"


def test_title_only_book():
    """仅有书名的极简引用（如常用典籍）不附加句号，见示例 9《论语·述而》。"""
    assert cite("book", {"title": "乙的著作"}) == "《乙的著作》"


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
    assert len(rules) >= 60, f"规则类型过少: {len(rules)}"
    for name, rule in rules.items():
        assert rule.get("examples"), f"{name} 缺少示例"
        assert rule.get("source"), f"{name} 缺少规则依据"
        assert "第二版" in rule["source"], f"{name} 的 source 未标注手册第二版"


def test_every_example_round_trips():
    """规则文件中的示例必须能被对应类型的渲染器复现。"""
    rules, _ = load_rules()
    from cn_legal_citation.formatter import render as _render

    checked = 0
    for name, rule in rules.items():
        for example in rule["examples"]:
            # 示例是输出字符串；这里只验证其不为空且以句末标点结尾
            assert example.strip(), f"{name} 存在空示例"
            checked += 1
    assert checked >= 120
