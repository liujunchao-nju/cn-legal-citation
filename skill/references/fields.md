# 字段速查

把字段写成 JSON 传给 `run.py cite --type <类型> --file data.json`。
字段缺失不会留下多余标点 —— 引擎只拼接条件成立的段落。

## 通用字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `authors` | 列表 | 作者名。超过三位按手册省略为「甲等」 |
| `nationality` | 字符串 | 外籍作者国籍，输出为 `[美]富勒` 形式 |
| `dynasty` | 字符串 | 古籍作者朝代，输出为 `（清）沈家本` 形式 |
| `authorship` | 字符串 | 著作方式：主编、编著、编译、整理、译注、口述 |
| `title` | 字符串 | 文献名称，引擎自动加书名号 |
| `edition` | 整数或字符串 | 版次：`5` 得 `(第5版)`，`修订版` 得 `(修订版)` |
| `translator` | 字符串 | 译者，输出为 `郑戈译` |
| `publisher` | 字符串 | 出版社。不写城市名 |
| `year` | 整数 | 出版年份 |
| `pages` | 整数/字符串/列表 | 页码：`18`、`"73-75"`、`[55, "64-68"]`、`"9a"` |

## 分类型字段

### 中文纸质出版文献

- **`book`** — 中文著作
  - 字段：`authors`(author_list)、`authorship`(authorship)、`title`(plain)、`edition`(edition)、`translator`(translator)、`collator`(plain)、`volume_note`(plain)、`publisher`(publisher_year)、`pages`(page_range)、`page_note`(plain)、`container_title`(plain)、`tail_period`(tail_period)
  - 示例：王名扬:《美国行政法》,中国法制出版社1995年版,第18页。
- **`journal`** — 期刊论文
  - 字段：`authors`(author_list)、`authorship`(authorship)、`title`(plain)、`journal`(plain)、`year`(plain)、`volume`(plain)、`issue`(plain)、`issue_info`(issue_info)、`issue_date`(plain)、`pages`(page_range)
  - 示例：季卫东:《法律程序的意义——对中国法制建设的另一种思考》,载《中国社会科学》1993年第1期,第91页。
- **`newspaper`** — 报纸文章
  - 字段：`authors`(author_list)、`authorship`(authorship)、`title`(plain)、`newspaper`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)、`page`(plain)
  - 示例：何海波:《判决书上网》,载《法制日报》2000年5月21日,第2版。
- **`collection`** — 文集析出文献
  - 字段：`authors`(author_list)、`authorship`(authorship)、`title`(plain)、`translator`(translator)、`editor`(plain)、`editor_role`(authorship)、`container_title`(plain)、`container_translator`(translator)、`volume`(plain)、`publisher`(publisher_year)、`year`(plain)、`pages`(page_range)
  - 示例：王保树:《股份有限公司机关构造中的董事和董事会》,载梁慧星主编:《民商法论丛》第1卷,法律出版社1994年版,第110页。
- **`thesis`** — 学位论文
  - 字段：`authors`(author_list)、`title`(plain)、`school`(plain)、`year`(plain)、`degree`(plain)、`pages`(page_range)
  - 示例：李松锋:《游走在上帝与凯撒之间——美国宪法第一修正案中的政教关系研究》,中国政法大学2013年博士学位论文,第30页。
- **`conference`** — 会议论文
  - 字段：`authors`(author_list)、`title`(plain)、`meeting_info`(plain)、`published_in`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)、`place`(plain)、`pages`(page_range)
  - 示例：习超:《证券监管有偏私吗?》,清华大学法学院、社会科学学院、数据科学研究院“迈向数据法学”研讨会会议论文,2017年12月23日于北京。
- **`archive`** — 档案文献
  - 字段：`authors`(author_list)、`title`(plain)、`date`(plain)、`repository`(plain)、`archive_note`(plain)、`archive_number`(plain)
  - 示例：雷经天:《关于边区司法工作检查情形》(1943年9月3日),陕西省档案馆陕甘宁边区高等法院档案,档案号15/149。

### 中文网络电子文献

- **`online`** — 网络文献
  - 字段：`authors`(author_list)、`title`(plain)、`site`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)、`url`(plain)、`visit_year`(plain)、`visit_month`(plain)、`visit_day`(plain)、`visit_date`(date_cn)
  - 示例：梁秋坪、郝萍:《全国打击治理农村赌博工作现场会召开》,载人民网2024年10月12日,http://society.people.com.cn/n1/2024/1012/c1008-40337761.html。
- **`website`** — 网站
  - 字段：`name`(plain)、`column`(plain)、`url`(plain)、`visit_year`(plain)、`visit_month`(plain)、`visit_day`(plain)、`visit_date`(date_cn)
  - 示例：法国最高行政法院网站,https://conseil-etat.fr/zh,2024年10月8日访问。
- **`wechat`** — 微信公众号文章
  - 字段：`authors`(author_list)、`title`(plain)、`account`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)
  - 示例：刘松山:《失信惩戒立法的三大问题》,载微信公众号“中国法律评论”2019年11月19日。
- **`blog`** — 博客文章
  - 字段：`authors`(author_list)、`title`(plain)、`blog`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)、`url`(plain)
  - 示例：黄晓磊:《再说博客文章被正式引用》,载科学网博客2012年3月23日,http://blog.sciencenet.cn/blog-111883-550928.html。
- **`weibo`** — 微博
  - 字段：`platform`(plain)、`account`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)、`url`(plain)
  - 示例：新浪微博xiaolwl,2020年1月31日,https://weibo.com/1139098205/44667685335861595。
- **`app`** — App 文章
  - 字段：`authors`(author_list)、`title`(plain)、`app`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)
  - 示例：莫纪宏:《论“中国式现代化”的法治保障》,载“学习强国”App2024年6月21日。
- **`broadcast`** — 广播电视节目
  - 字段：`host`(plain)、`title`(plain)、`station`(plain)、`column`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)、`url`(plain)
  - 示例：白岩松主持:《新型冠状病毒肺炎,情况如何?》,中央电视台“新闻1+1”栏2020年1月20日播出,http://tv.cctv.com/2020/01/20/VIDECRZF7PWXb80z86QyB0db200120.shtml。
- **`audiovisual`** — 音像制品
  - 字段：`name`(plain)、`producer`(plain)、`year`(plain)
  - 示例：《行政诉讼法讲义》,中国政法大学法学院制作,2010年。

### 未发表文献

- **`interview`** — 访谈
  - 字段：`description`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)、`place`(plain)
  - 示例：笔者与×××访谈,2000年3月22日,《最高人民法院公报》编辑部。
- **`correspondence`** — 私人通讯
  - 字段：`description`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)
  - 示例：王名扬教授给笔者的电子邮件,2002年3月8日。
- **`internal`** — 内部资料
  - 字段：`unit`(plain)、`title`(plain)、`meeting`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)、`place`(plain)
  - 示例：上海市浦东新区人民法院行政审判庭:《2001年行政庭工作总结》。

### 法律文件与官方文件

- **`legal`** — 法律法规规章
  - 字段：`issuing_authority`(plain)、`name`(titled)、`revision`(plain)、`document_number`(document_number)、`article`(statute_ref)、`adoption_info`(plain)
  - 示例：《行政处罚法》第32条。
- **`regulation`** — 规范性文件
  - 字段：`issuing_authority`(plain)、`name`(titled)、`document_number`(document_number)、`article`(plain)、`source_compiler`(plain)、`source_title`(plain)、`source_publisher`(plain)、`source_year`(plain)、`source_pages`(page_range)、`date`(plain)、`url`(plain)
  - 示例：《最高人民法院关于适用〈中华人民共和国行政诉讼法〉的解释》(法释〔2018〕1号),第100条。
- **`standard`** — 国家标准
  - 字段：`authority`(plain)、`name`(plain)、`number`(plain)、`date`(plain)
  - 示例：国家质量监督检验检疫总局、中国国家标准化管理委员会《信息与文献参考文献著录规则》,GB/T 7714-2015。
- **`resolution`** — 会议决议
  - 字段：`name`(titled)、`adoption`(plain)
  - 示例：《中共中央关于全面推进依法治国若干重大问题的决定》,2014年10月23日中国共产党第十八届中央委员会第四次全体会议通过。
- **`report`** — 会议报告
  - 字段：`author`(plain)、`identity`(plain)、`title`(plain)、`date`(plain)、`meeting`(plain)、`report_suffix`(plain)、`publication`(plain)
  - 示例：李克强:《政府工作报告》,2023年3月5日在第十四届全国人民代表大会第一次会议上。
- **`white_paper`** — 白皮书
  - 字段：`authority`(plain)、`name`(plain)、`date`(plain)、`url`(plain)、`publisher`(plain)、`year`(plain)
  - 示例：国务院新闻办公室:《新时代的中国网络法治建设》,2023年3月16日发布,https://www.gov.cn/zhengce/2023-03/16/content_5747005.htm。
- **`hk_macau_law`** — 港澳法律文件
  - 字段：`name`(plain)、`chapter`(plain)、`announcement`(plain)、`article`(plain)、`url`(plain)
  - 示例：《刑事上诉规则》(香港法例第221A章),第42(3)条。
- **`taiwan_law`** — 台湾地区法律文件
  - 字段：`note`(plain)、`name`(plain)
  - 示例：我国台湾地区“民法”。
- **`foreign_law`** — 外国法律（中文版本）
  - 字段：`country`(plain)、`year_before`(plain)、`name`(titled)、`year`(plain)、`original`(plain)
  - 示例：英国《1996年仲裁法》。
- **`treaty`** — 国际公约（中文版本）
  - 字段：`organization`(plain)、`name`(plain)、`original`(plain)
  - 示例：联合国《儿童权利公约》。
- **`un_document`** — 联合国文件（中文版本）
  - 字段：`name`(plain)、`organ`(plain)、`doc_type`(plain)、`number`(plain)、`date`(plain)、`action`(plain)、`url`(plain)
  - 示例：《世界人权宣言》,联合国大会决议,217A(Ⅲ),1948年12月10日通过。

### 司法案例与统计数据

- **`case`** — 司法案例
  - 字段：`case_name`(plain)、`court`(plain)、`case_number`(case_number)、`document_type`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`judgment_date`(date_cn)、`gazette_year`(plain)、`gazette_issue`(plain)、`guiding_organ`(plain)、`guiding_no`(plain)、`guiding_year`(plain)、`database_number`(plain)、`report_author`(plain)、`report_title`(plain)、`report_newspaper`(plain)、`report_date`(plain)、`report_page`(plain)、`compiler`(plain)、`compilation_title`(plain)、`compilation_publisher`(plain)、`compilation_year`(plain)、`case_no`(plain)
  - 示例：苏嘉鸿诉中国证监会行政处罚案,北京市高级人民法院(2018)京行终445号行政判决书。
- **`statistics`** — 统计数据
  - 字段：`subject`(plain)、`retrieval_time`(plain)、`scope`(plain)、`keywords`(plain)、`method`(plain)
  - 示例：检索北大法宝数据库,在380余万份行政裁判文书中统计"权利"与"职权"的词频,检索时间为2024年3月,检索范围为国家法律法规数据库中的法律。

### 英文文献

- **`en_book`** — 英文著作
  - 字段：`authors`(author_list)、`authorship`(authorship)、`title`(plain)、`edition`(plain)、`translator`(plain)、`container`(plain)、`publisher`(plain)、`year`(plain)、`pages`(plain)
  - 示例：William P. Alford, To Steal a Book Is an Elegant Offense: Intellectual Property Law in Chinese Civilization, Stanford University Press, 1995, p. 98.
- **`en_article`** — 英文学术论文
  - 字段：`authors`(author_list)、`title`(plain)、`journal`(plain)、`journal_ref`(journal_ref)、`volume`(plain)、`first_page`(plain)、`pincite`(plain)、`volume_info`(plain)、`pages`(plain)、`year`(plain)
  - 示例：Charles A. Reich, The New Property, 73 Yale Law Journal 733 (1964).
- **`en_periodical`** — 英文报纸杂志
  - 字段：`authors`(author_list)、`title`(plain)、`periodical`(plain)、`date`(plain)、`page`(plain)
  - 示例：Louis D. Brandeis, What Publicity Can Do, Harper's Weekly, 20 December 1913, p. 10.
- **`en_online`** — 英文网络文献
  - 字段：`authors`(plain)、`title`(plain)、`site`(plain)、`site_date`(site_date)、`date`(plain)、`url`(plain)、`visit_date`(plain)
  - 示例：Stephen McDonell, When China Began Streaming Trials Online, BBC News (30 September 2016), https://www.bbc.com/news/blogs-china-blog-37515399.
- **`en_law_uk`** — 英国法律
  - 字段：`name`(plain)、`year`(plain)、`section`(plain)、`number`(plain)、`source`(plain)、`url`(plain)
  - 示例：Human Rights Act 1998, s. 3(2)(b).
- **`en_law_us`** — 美国法律
  - 字段：`name`(plain)、`pub_law`(plain)、`section`(plain)、`source`(plain)、`year`(plain)
  - 示例：Department of Transportation Act, Pub. L. No. 89-670, § 9, 80 Stat. 931, 944-947 (1966).
- **`en_law_eu`** — 欧盟法律
  - 字段：`name`(plain)、`number`(plain)、`eu_number`(eu_number)、`article`(plain)、`url`(plain)
  - 示例：Consolidated Version of the Treaty on European Union [2008] OJ C115/13.
- **`en_doc_un`** — 联合国文件（英文）
  - 字段：`organ`(plain)、`name`(plain)、`number`(plain)、`date`(plain)
  - 示例：General Assembly Resolution, Universal Declaration of Human Rights, 217A (III), 10 December 1948.
- **`en_case`** — 英文案例（美国）
  - 字段：`case_name`(plain)、`reports`(report_list)、`docket`(plain)、`court`(plain)、`court_year`(court_year)、`year`(plain)
  - 示例：Chevron U.S.A., Inc. v. Natural Resources Defense Council, Inc., 467 U.S. 837 (1984).
- **`en_case_uk`** — 英文案例（英国）
  - 字段：`case_name`(plain)、`report`(plain)、`locator`(plain)
  - 示例：R v. Lord Chancellor, ex parte Witham [1998] QB 575, at 581E (per Laws J.).
- **`en_case_intl`** — 英文案例（国际法院与仲裁机构）
  - 字段：`case_name`(plain)、`report`(plain)、`locator`(plain)
  - 示例：East Timor (Portugal v. Australia), Judgment, ICJ Reports 1995, para. 29-35.

### 法文文献

- **`fr_book`** — 法文图书
  - 字段：`authors`(author_list)、`authorship`(authorship)、`title`(plain)、`edition`(plain)、`publisher`(plain)、`year`(plain)、`pages`(plain)
  - 示例：Jacques Chevallier, L'État de droit, 4° éd., Montchrestien, 2003, p. 16-29.
- **`fr_article`** — 法文论文
  - 字段：`authors`(author_list)、`title`(plain)、`container`(plain)、`journal`(plain)、`year`(plain)、`pages`(plain)
  - 示例：Frédéric Zenati, Pour une rénovation de la théorie de la propriété, RTD civ. 1993, p. 305 s.
- **`fr_thesis`** — 法文学位论文
  - 字段：`authors`(author_list)、`title`(plain)、`school`(plain)、`year`(plain)
  - 示例：Daniel Gutmann, Le sentiment d'identité, étude du droit des personnes et de la famille, Thèse Paris II, 2000.
- **`fr_law`** — 法国法律
  - 字段：`code`(plain)、`article`(plain)、`law_type`(plain)、`number`(plain)、`date`(plain)、`subject`(plain)、`article_full`(plain)
  - 示例：C. civ., art. 1832-1.
- **`fr_case`** — 法国法院案例
  - 字段：`court`(plain)、`chamber`(plain)、`date`(plain)、`case_name`(plain)、`number`(plain)、`report`(plain)、`page`(plain)
  - 示例：CE, 15 février 2008, Commune de La Londe-les-Maures, req. n°279045.
- **`fr_online`** — 法文网络文献
  - 字段：`authors`(plain)、`title`(plain)、`site`(plain)、`date`(plain)、`modified`(plain)、`url`(plain)、`visit_date`(plain)
  - 示例：Conseil d'État, Stationnement payant: le Conseil d'État précise le cadre juridique du recours à la géolocalisation des véhicules, 18 novembre 2024, https://www.conseil-etat.fr/actualites/stationnement-payant-le-conseil-d-etat-precise-le-cadre-juridique-du-recours-a-la-geolocalisation-des-vehicules.

### 德文文献

- **`de_book`** — 德文图书
  - 字段：`authors`(author_list)、`editor`(plain)、`title`(plain)、`container`(plain)、`band`(plain)、`edition`(plain)、`publisher`(plain)、`year`(plain)、`locator`(plain)
  - 示例：Claus Roxin, Strafrecht Allgemeiner Teil, Band I, 4. Aufl., C.H.Beck, 2006, § 15 Rn. 19.
- **`de_article`** — 德文论文
  - 字段：`authors`(author_list)、`title`(plain)、`journal`(plain)、`page`(plain)、`container`(plain)
  - 示例：Benjamin Vogel, Rechtsgüterschutz und Normgeltung, ZStW 129 (2017), S. 630.
- **`de_law`** — 德国法律
  - 字段：`section`(plain)、`law`(plain)、`date`(plain)
  - 示例：§ 46b III Gesetz über die Entschädigung ehemaliger deutscher Kriegsgefangener (KgfEG) i.d.F. v. 04.02.1987.
- **`de_case`** — 德国法院案例
  - 字段：`court`(plain)、`report`(plain)、`year`(plain)、`page`(plain)、`pincite`(plain)、`parallel`(plain)
  - 示例：BGH NStZ-RR 1999, 185.

### 意大利文文献

- **`it_book`** — 意大利文图书
  - 字段：`authors`(author_list)、`editor`(plain)、`title`(plain)、`volume`(plain)、`edition`(plain)、`translator`(plain)、`container`(plain)、`publisher`(plain)、`year`(plain)、`pages`(plain)
  - 示例：Angelo Falzea, L'offerta reale e la liberazione coattiva del debitore, Giuffre, 1947, p. 34 s.
- **`it_periodical`** — 意大利文报刊
  - 字段：`authors`(author_list)、`title`(plain)、`container`(plain)、`date`(plain)、`year`(plain)、`volume`(plain)、`issue`(plain)、`pages`(plain)
  - 示例：Aldo Cazzullo, Il ritorno e i motivi, in Corriere della sera, 7 novembre 2024, p. 8.
- **`it_law`** — 意大利法律
  - 字段：`law_type`(plain)、`date`(plain)、`number`(plain)、`article_ref`(plain)
  - 示例：D.P.R. 26 luglio 1976, n. 752.
- **`it_case`** — 意大利法院案例
  - 字段：`court`(plain)、`chamber`(plain)、`date`(plain)、`number`(plain)、`report`(plain)、`year`(plain)、`volume`(plain)、`page`(plain)
  - 示例：Cass. civ., sez. lavoro, 29 maggio 1998, n. 5348.
- **`it_roman`** — 罗马法文献
  - 字段：`author`(plain)、`work`(plain)、`locator`(plain)
  - 示例：Cicero, De Officiis, 3.17.71.

### 俄文文献

- **`ru_book`** — 俄文图书
  - 字段：`authors`(author_list)、`editor`(plain)、`title`(plain)、`edition`(plain)、`publisher`(plain)、`year`(plain)、`pages`(plain)
  - 示例：Елена А. Дубовицкая, Европейское корпоративное право, Вольтерс Клувер России, 2008, с. 6.
- **`ru_article`** — 俄文学术论文
  - 字段：`authors`(author_list)、`title`(plain)、`journal`(plain)、`issue`(plain)、`ru_issue`(ru_issue)、`year`(plain)、`pages`(plain)
  - 示例：Вадим А. Виноградов, Анализ феномена "культура отмены" как инструмента регулирования общественных отношений // Журнал российского права, 2023, No 3, с. 17-30.
- **`ru_periodical`** — 俄文报刊
  - 字段：`authors`(author_list)、`title`(plain)、`newspaper`(plain)、`date`(plain)、`page`(plain)
  - 示例：Ольга М. Игнатова, Юрист Хрусталева разъяснила, могут ли граждане-банкроты выезжать за границу, Российская газета, 06.02.2024.
- **`ru_law`** — 俄罗斯法律
  - 字段：`name`(plain)、`article`(plain)、`date`(plain)、`source`(plain)
  - 示例：Семейный кодекс Российской Федерации, ст. 16, принят 29 декабря 1995 года, Собрание законодательства Российской Федерации [СЗ РФ].
- **`ru_case`** — 俄罗斯法院案例
  - 字段：`case_name`(plain)、`number`(plain)、`date`(plain)、`source`(plain)
  - 示例：Петрова против Министерства здравоохранения заявление № 54321/98765, Решение от 10 сентября 2021 года, Официальный вестник судебных решений 2021-Ⅲ.
- **`ru_online`** — 俄文网络文献
  - 字段：`authors`(plain)、`title`(plain)、`site`(plain)、`date`(plain)、`url`(plain)
  - 示例：Юлия Л. Яковлева, Пост крушения вертолета Ми-8 в Карелии возбуждено уголовное дело, ФОНТАНКА 2024-02-05, https://www.fontanka.ru/2024/02/05/73195217/.

### 日文文献

- **`ja_book`** — 日文图书
  - 字段：`authors`(author_list)、`title`(plain)、`ja_title`(ja_title)、`editor`(plain)、`container`(plain)、`publisher`(plain)、`year`(plain)、`pages`(plain)
  - 示例：我妻栄『新訂担保物権法(民法講義Ⅲ)』(有斐閣,1971年)50頁。
- **`ja_article`** — 日文期刊论文
  - 字段：`authors`(author_list)、`title`(plain)、`journal`(plain)、`volume`(plain)、`issue`(plain)、`year`(plain)、`pages`(plain)
  - 示例：於保不二雄「付加物及び物抵当権」民商法29巻5号(1954年)1頁以下。
- **`ja_law`** — 日本法律
  - 字段：`name`(plain)、`translation`(plain)
  - 示例：動産及び債権の譲渡の対抗要件に関する民法の特例に関する法律。
- **`ja_case`** — 日本法院案例
  - 字段：`court`(plain)、`year`(plain)、`month`(plain)、`day`(plain)、`date`(date_cn)、`report`(plain)、`page`(plain)
  - 示例：大審院1919年3月3日判决,大審院民事判决録25輯356頁。
- **`ja_official`** — 日本官方文件
  - 字段：`name`(plain)
  - 示例：「平成26年版犯罪白書」による。
- **`ja_online`** — 日文网络文献
  - 字段：`authors`(author_list)、`title`(plain)、`url`(plain)、`date`(plain)
  - 示例：佐藤英明「一時所得の要件に関する覚書」 https://www.example.jp/paper,2024年6月1日。

## 规范化器

字段值由规范化器加工，可在规则文件的 `fields` 里指定：

| 规范化器 | 作用 |
|---|---|
| `author_list` | 作者列表。 |
| `authorship` | 著作身份。原创作品省略"著"；主编、编著、编译、整理、译注等照写（第 27、28 条）。 |
| `case_number` | 案号（第 89 条：案号中的年份加圆括号，案号置于文书类型之前）。 |
| `court_year` | 英文案例的法院与年份括注（第 114 条）。 |
| `date_cn` | 中文日期。2000, 5, 21 ->"2000年5月21日"。 |
| `document_number` | 规范性文件文号（第 74 条）。 |
| `edition` | 版次。输入 4 得到"(第4版)"，输入"修订版"得到"(修订版)"（第 40 条： |
| `eu_number` | 欧盟法律编号（第 110 条）。 |
| `issue_info` | 期刊卷期与出版年（第 43、44 条）。 |
| `ja_title` | 日文文献名称的书名号（第 143 条）。 |
| `journal_ref` | 英文学术期刊的卷次与页码（第 105、107 条）。 |
| `page_range` | 页码（第 48 条）。 |
| `plain` | 原样输出。用于标题、期刊名、出版社等无需加工的文本。 |
| `publisher_year` | 出版社与出版年。 |
| `report_list` | 案例报告引注列表。同时援引几个案例报告系统时用逗号连接（第 114 条第 2 项）。 |
| `ru_issue` | 俄文期刊的期次衔接（第 136、137 条）。 |
| `site_date` | 英文网络文献的网站名与上传日期（第 100 条）。 |
| `statute_ref` | 法条序号（第 70 条：条、款、项、目序数用阿拉伯数字，括号省略）。 |
| `tail_period` | 结尾句号。 |
| `titled` | 法律文件名称（第 67 条：名称加书名号）。 |
| `translator` | 译者。输出形如"郑戈译"（第 29 条：译者位于文献名称之后、出版信息之前）。 |
