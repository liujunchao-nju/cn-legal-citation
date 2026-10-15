# cn-legal-citation

[![tests](https://github.com/liujunchao-nju/cn-legal-citation/actions/workflows/tests.yml/badge.svg)](https://github.com/liujunchao-nju/cn-legal-citation/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://pypi.org/project/cn-legal-citation/)

按《法学引注手册》（第二版，北京大学出版社 2025 年版）生成、核查、改写中文法学脚注。规则与代码分离，式样写在 YAML 里，改格式不需要动 Python。

## 两种用法

**如果你不写代码**，用技能形态：说一句「帮我把这篇论文的脚注按引注手册核一遍」，就能拿到核查报告或规范后的文件。技能自带引擎，**不需要装 Python 包**。

```bash
# 下载 dist/cn-legal-citation-skill-v0.3.0.zip，解压到技能目录即可
python scripts/selfcheck.py     # 先自检，确认技能完好
```

**如果你写代码**，用 Python 包：`pip install -e .` 之后调 API 或命令行。

两条路走的是**同一个规则引擎**，输出完全一致。技能只是把引擎包了一层，让不会命令行的人也能用。

## 为什么做这个

写法学论文时，脚注格式是最不值得手动调、又最容易出错的部分：著作要不要写出版社城市、期刊前加不加"载"、案号是"法院+案号+文书类型"还是旧式写法，各家刊物要求并不一致，改投一家就得重排一遍。

这个工具把式样从代码里抽出来，做成一个可配置、可校验、可提 PR 的规则集。你会得到两样东西：一条能直接用的脚注，以及一份可以自己改的式样定义。

## 与市面工具的区别

- **确定性输出。** 同样输入永远得到同样结果，221 项测试覆盖，可回归、可 CI。不依赖大模型现场生成，不会出现"这次对下次错"。
- **能核查已有文档。** 不只是生成新脚注：可以读一篇写好的论文，逐条判断每个脚注是否合规，输出问题清单，再另存一份改好的副本。这一点是纯提示词方案做不到的。
- **规则即数据。** 式样在 YAML 里，程序可读、可校验、可扩展；不是给 AI 看的一段提示词。
- **覆盖完整。** 69 种文献类型，覆盖《法学引注手册》第二版全部 150 条，含英法德意俄日六种外文和港澳台、国际组织文件。
- **零重依赖。** 只依赖 PyYAML（技能形态连这个都不需要，改用内置 JSON 规则）。

## 安装

```bash
pip install -e .
```

只依赖 `PyYAML`。Python 3.9 及以上。

## 用法

### 命令行

推荐用 JSON 文件传入文献信息，省掉命令行引号转义的麻烦。

```bash
# 列出全部 69 种文献类型
python -m cn_legal_citation types

# 查看某一类型的规则依据、说明与示例
python -m cn_legal_citation show --type case

# 单条生成
python -m cn_legal_citation cite --type book --file examples/book.json

# 批量生成
python -m cn_legal_citation batch --file examples/samples.json
```

也可以直接传 JSON 字符串。Git Bash / macOS：

```bash
python -m cn_legal_citation cite --type book \
  --data '{"authors":["王名扬"],"title":"美国行政法","publisher":"中国法制出版社","year":1995,"pages":18}'
```

PowerShell 需要对内部的双引号做转义：

```powershell
python -m cn_legal_citation cite --type book --data '{\"authors\":[\"王名扬\"],\"title\":\"美国行政法\",\"publisher\":\"中国法制出版社\",\"year\":1995,\"pages\":18}'
```

输出：

```
王名扬:《美国行政法》,中国法制出版社1995年版,第18页。
```

### 核查与改写已有文档

这是 0.3.0 新增的能力：不只能生成新脚注，还能读一篇写好的文稿，逐条判断
脚注是否合规。

```bash
# 提取脚注（先确认文档里是真脚注）
python -m cn_legal_citation doc-extract --file 论文.docx

# 整篇核查，输出报告
python -m cn_legal_citation doc-check --file 论文.docx --out 核查报告.md

# 批量改写：另存副本，原件不动，附变更对照表
python -m cn_legal_citation doc-rewrite --file 论文.docx --out 论文_已规范.docx --table 变更对照.md
```

核查把每条脚注分成四类：

| 状态 | 含义 |
|---|---|
| 完全合规 | 引擎能逐字复现 |
| 标点需规范化 | 字段都对，只是用了全角标点（手册示例用半角） |
| 格式不符 | 字段对但式样不对，报告给出差异点 |
| 未能解析 | 超出规则解析范围，如实报出，不硬猜 |

原理很朴素：**能否用引擎的字段把这条脚注逐字重新渲染出来，就是它合不合规的
标准**。渲染结果与原文字有出入，差异就是问题所在。所以核查不需要额外的判断
逻辑，它和生成能力是同一件事的两面。

改写有两条硬约束：只输出副本（原件字节不变，有测试守着），只改「标点需规范化」
与「格式不符」两类（未解析的一律不动，不经确认不替用户猜）。

支持 `.docx`（Word 真实页下脚注，读 `word/footnotes.xml`）与 `.md`
（`[^1]: 文本` 形式）。

### 逆向解析

```bash
# 脚注文本 → 字段
python -m cn_legal_citation parse --text "王名扬:《美国行政法》,中国法制出版社1995年版,第18页。"

# 核查一组脚注（每行一条）
python -m cn_legal_citation check --file footnotes.txt
```

解析采用「规则匹配优先，认不出就如实返回未解析」的策略，覆盖中文常见类型
（图书、期刊、报纸、文集、判例、法条、网络文献、公众号等）与英文著作论文。
法、德、意、俄、日文献体例复杂，本版不做规则解析，交由使用者补字段。

### Python API

```python
from cn_legal_citation import cite

cite("case", {
    "court": "北京市海淀区人民法院",
    "case_number": {"year": 1998, "code": "海行初字", "number": 142},
    "document_type": "行政判决书",
})
# '北京市海淀区人民法院(1998)海行初字第142号行政判决书。'

cite("legal", {"name": "民法典", "article": {"article": 1224, "paragraph": 1, "item": 2}})
# '《民法典》第1224条第1款第2项。'

cite("en_article", {
    "authors": ["Cass R. Sunstein"],
    "title": "Interpreting Statutes in the Regulatory State",
    "journal": "Harvard Law Review",
    "volume": 103,
    "first_page": 405,
    "year": 1989,
})
# 'Cass R. Sunstein, Interpreting Statutes in the Regulatory State, 103 Harvard Law Review 405 (1989).'

cite("ja_book", {
    "authors": ["我妻栄"],
    "title": "新訂担保物権法(民法講義Ⅲ)",
    "publisher": "有斐閣",
    "year": 1971,
    "pages": 50,
})
# '我妻栄『新訂担保物権法(民法講義Ⅲ)』(有斐閣,1971年)50頁。'
```

## 支持的文献类型（69 种）

### 中文纸质出版文献

| 类型 | 说明 | 依据 |
|---|---|---|
| `book` | 著作、译著、编著、古籍 | 第 25-49 条 |
| `journal` | 期刊论文、集刊论文、杂志 | 第 43-45 条 |
| `collection` | 论文集、集刊析出文献 | 第 42、44 条 |
| `newspaper` | 报纸文章 | 第 45 条 |
| `thesis` | 学位论文 | 第 64 条 |
| `conference` | 会议论文 | 第 63 条 |
| `archive` | 档案文献 | 第 65 条 |

### 中文网络电子文献

| 类型 | 说明 | 依据 |
|---|---|---|
| `online` | 网站文章 | 第 50-55 条 |
| `website` | 网站、栏目本身 | 第 54 条 |
| `wechat` | 微信公众号文章 | 第 56 条 |
| `blog` | 博客文章 | 第 56 条 |
| `weibo` | 微博 | 第 56 条 |
| `app` | App 文章 | 第 56 条 |
| `broadcast` | 广播电视节目 | 第 57 条 |
| `audiovisual` | 音像制品 | 第 58 条 |

### 未发表文献

| 类型 | 说明 | 依据 |
|---|---|---|
| `interview` | 访谈 | 第 60 条 |
| `correspondence` | 私人通讯 | 第 61 条 |
| `internal` | 内部资料 | 第 62 条 |

### 法律文件与官方文件

| 类型 | 说明 | 依据 |
|---|---|---|
| `legal` | 法律、法规、规章 | 第 67-71 条 |
| `regulation` | 规范性文件 | 第 72-76 条 |
| `standard` | 国家标准 | 第 77 条 |
| `resolution` | 会议决议 | 第 78 条 |
| `report` | 会议报告 | 第 79 条 |
| `white_paper` | 白皮书 | 第 80 条 |
| `hk_macau_law` | 中国香港、中国澳门法律文件 | 第 81-82 条 |
| `taiwan_law` | 中国台湾地区法律文件 | 第 83 条 |
| `foreign_law` | 外国法律（中文版本） | 第 84 条 |
| `treaty` | 国际公约（中文版本） | 第 85 条 |
| `un_document` | 联合国文件（中文版本） | 第 86 条 |

### 司法案例与统计数据

| 类型 | 说明 | 依据 |
|---|---|---|
| `case` | 裁判文书、指导性案例、公报案例、案例库案例、媒体报道、案例选编 | 第 87-91 条 |
| `statistics` | 统计数据来源与检索方法 | 第 92-94 条 |

### 外文文献

| 类型 | 说明 | 依据 |
|---|---|---|
| `en_book` `en_article` `en_periodical` `en_online` | 英文著作、论文、报刊、网络文献 | 第 99-107 条 |
| `en_law_uk` `en_law_us` `en_law_eu` `en_doc_un` | 英国法律、美国法律、欧盟法律、联合国文件 | 第 108-111 条 |
| `en_case` `en_case_uk` `en_case_intl` | 美国案例、英国案例、国际法院与仲裁机构案例 | 第 112-115 条 |
| `fr_book` `fr_article` `fr_thesis` `fr_law` `fr_case` `fr_online` | 法文图书、论文、学位论文、法律、法院案例、网络文献 | 第 116-122 条 |
| `de_book` `de_article` `de_law` `de_case` | 德文图书、论文、法律、法院案例 | 第 123-128 条 |
| `it_book` `it_periodical` `it_law` `it_case` `it_roman` | 意大利文图书、报刊、法律、法院案例、罗马法文献 | 第 129-134 条 |
| `ru_book` `ru_article` `ru_periodical` `ru_law` `ru_case` `ru_online` | 俄文图书、论文、报刊、法律、法院案例、网络文献 | 第 135-141 条 |
| `ja_book` `ja_article` `ja_law` `ja_case` `ja_official` `ja_online` | 日文图书、论文、法律、法院案例、官方文件、网络文献 | 第 142-150 条 |

用 `python -m cn_legal_citation show --type <类型>` 可以查看每个类型内置的规则依据与示例。

## 设计：规则即数据

所有式样定义在 `cn_legal_citation/rules/*.yaml`，一个文件对应一种文献类型，代码里没有任何硬编码的标点或语序。

```yaml
type: book
label: 中文著作
source: 《法学引注手册》(第二版)第 25-49 条
segments:
  - text: "{authors}{authorship}{colon}"
    requires: [authors]
  - text: "《{title}》"
    requires: [title]
  - text: "{edition}"
    requires: [edition]
  - text: "{comma}{publisher}"
    requires: [publisher]
  - text: "{comma}{pages}"
    requires: [pages]
  - text: "{tail_period}"
    requires: [tail_period]
```

渲染时按顺序拼接各段，只有 `requires` 列出的字段全部非空（且 `absent` 列出的字段全部为空）时，该段才参与拼接。译者、版次、页码这些可选信息缺失时，不会留下悬空的逗号。同一 `mutex` 分组内只取第一个条件成立的段，用于日文书名号 `『』` 与文章号 `「」` 这类互斥体例。

由此带来两个直接好处：

- **新增文献类型不用改代码。** 在 `rules/` 下加一个 YAML 文件即可，`types` 命令会自动识别。
- **改标点不用改代码。** `rules/index.yaml` 里的 `punctuation` 控制全局冒号与逗号。默认按手册示例呈现的半角形式；若目标刊物要求全角，改成 `"："` 和 `"，"` 即可。

字段值的加工（作者超过三人省略为"甲等"、页码转"第73-75页"、法条转"第1224条第1款第2项"、期刊卷期转"第47卷第4期（2018年）"）由 `normalize.py` 里的规范化器完成，在 YAML 的 `fields` 中声明，同样是可配置的。

## 技能形态

`skill/` 目录是技能形态的源码。构建脚本会把手写的 `SKILL.md`、脚本、参考文档
与引擎源码、导出的 JSON 规则组装成一个可离线运行的技能包：

```bash
python tools/build_skill.py
# 组装到 ~/.workbuddy/skills/cn-legal-citation，并打包到 dist/*.zip
```

三种使用场景（`SKILL.md` 里有给智能体的完整操作细则）：

| 场景 | 用户说什么 | 走什么 |
|---|---|---|
| L1 单条生成 | 「这段引了张新宝侵权责任法第5版，帮我加个注」 | `cite` |
| L2 整篇核查 | 「帮我核一下这篇论文的脚注规不规范」 | `doc-check` |
| L3 批量改写 | 「把脚注都改成规范格式，另存一份给我」 | `doc-rewrite` |

技能对智能体有一条硬性纪律：**脚注文本一律由引擎产出，智能体不得自己拼格式**。
这是技能与「把规则写成一段提示词」的本质区别 —— 前者可复现、可核查，后者不能。

技能自带引擎（`vendor/`），零第三方依赖：缺 PyYAML 时自动读内置的
`rules.json`。附 `scripts/selfcheck.py`，被复制到新环境后先跑一次即可确认
技能完好。

`references/types.md` 与 `references/fields.md` 由 `tools/gen_skill_refs.py`
从规则文件生成，规则改动后重跑一次即可保持同步。

## 规则依据与验证

式样以《法学引注手册》（第二版，北京大学出版社 2025 年版）为准，条文共 150 条。每个规则文件的 `source` 字段都写明了依据条款。

测试包含 221 个用例，其中 32 条直接取自手册第二版「示例」部分的公开示例，作为回归基准：

```bash
pip install -e ".[dev]"
pytest
```

每次 push 与 PR 会由 [GitHub Actions](https://github.com/liujunchao-nju/cn-legal-citation/actions/workflows/tests.yml) 在 Python 3.9 / 3.11 / 3.13 上自动复跑这批用例，并执行 CLI 冒烟测试。

这批用例的作用是防止后续调整规则时把已确认的式样改坏。如果你发现某条式样与目标刊物要求不符，改 YAML 里的 `segments` 即可，测试会明确告诉你改坏了哪一条。

## 第一版与第二版的差异

《法学引注手册》第一版于 2020 年出版（101 条），第二版于 2025 年 9 月出版（150 条）。本项目在 0.2.0 版本由第一版体例升级到第二版，主要变化包括：

- 裁判文书格式统一为"审判法院名称+案号+文书类型"（第 89 条）。
- 微信公众号文章不再要求标注网页链接（第 56 条）。
- 「载」字统一适用于期刊、报纸、图书和互联网上的析出文献。
- 新增意大利文、俄文引注体例，以及英国法律、欧盟法律、联合国文件的引用规范。
- 新增会议报告、白皮书、港澳法律文件等类型。
- 页码之间统一用短横线，不连续页码用顿号（第 48 条）。

## 已知限制

以下几项尚未实现，欢迎提 issue 或 PR：

1. **斜体与小型大写字母无法表达。** 手册要求英文文章名、图书名用斜体，本项目输出纯文本，不携带格式信息。若需在 Word 中保留斜体，请在文档中自行设置。
2. **脚注编号**不在本工具职责内。编号方式（全文连续还是每页重新起算）由各刊物自定，本工具只生成脚注文本本身。
3. **音频与视频的具体栏目写法**：手册第 57、58 条只给出文字性要求，未附完整示例，本项目的式样按条款文字推导，如与手册原文有出入欢迎指正。
4. **裁判文书案号**支持字典与字符串两种输入，但不校验案号本身的真实性。引用前请自行核对。
5. **逆向解析只覆盖中文常见类型与英文著作论文。** 法、德、意、俄、日文献的体例过于复杂，本版不做规则解析；核查到这类脚注时会如实报「未能解析」，不会给出错误字段。需要处理时请手工补字段后用 `cite` 生成。
6. **文档通道只支持 .docx 与 .md。** 不支持旧版 `.doc`、`.tex`、`.pdf`。Word 文档里的脚注必须是**真实页下脚注**（Word 脚注对象）；若是用上标数字手打的，读不到。
7. **改写不覆盖原件。** 这是有意为之的设计约束，不是限制：`--out` 必须与输入不同，引擎会拒绝同路径写入。

## 免责声明

本项目是学习方法论与工具实践的产物，不构成法律意见，也不保证输出符合任何特定刊物的审稿要求。引用前请自行核对条文、案号与文献信息；正式投稿前请按目标刊物的最新要求复核一遍。

## English

`cn-legal-citation` renders, checks, and reformats Chinese legal footnotes according to the *Handbook of Legal Citation* (《法学引注手册》, 2nd edition, Peking University Press, 2025). Citation styles live in YAML rule files rather than in Python code, so a formatter change is a one-line edit, not a refactor. The package covers all 150 clauses across 69 document types, including English, French, German, Italian, Russian and Japanese sources; 32 test cases are taken verbatim from the handbook's published examples as regression anchors.

Beyond generation, it can **audit an existing paper**: extract the footnotes from a `.docx` or `.md`, re-render each one from parsed fields, and report every place where the rendering differs from the original. The audit needs no separate rule set — being reproducible by the engine *is* the conformance criterion. Rewriting always writes to a new file; the original is byte-for-byte untouched (enforced by tests).

A companion agent **skill** (`skill/`, built by `tools/build_skill.py`) wraps the engine with zero third-party dependencies, so users who don't write code can just describe what they want.

## 许可

MIT。见 [LICENSE](LICENSE)。
