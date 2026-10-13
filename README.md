# cn-legal-citation

按《法学引注手册》（第二版）生成中文法学脚注。规则与代码分离，式样写在 YAML 里，改格式不需要动 Python。

## 为什么做这个

写法学论文时，脚注格式是最不值得手动调、又最容易出错的部分：著作要不要写出版社城市、期刊前加不加"载"、案号是"法院+案号+文书类型"还是旧式写法，各家刊物要求并不一致，改投一家就得重排一遍。

这个工具把式样从代码里抽出来，做成一个可配置、可校验、可提 PR 的规则集。你会得到两样东西：一条能直接用的脚注，以及一份可以自己改的式样定义。

## 安装

```bash
pip install -e .
```

只依赖 `PyYAML`。Python 3.9 及以上。

## 用法

### 命令行

推荐用 JSON 文件传入文献信息，省掉命令行引号转义的麻烦。

```bash
# 列出全部文献类型
python -m cn_legal_citation types

# 查看某一类型的规则依据与示例
python -m cn_legal_citation show --type case

# 单条生成
python -m cn_legal_citation cite --type book --file examples/book.json

# 批量生成
python -m cn_legal_citation batch --file examples/samples.json
```

也可以直接传 JSON 字符串。Git Bash / macOS：

```bash
python -m cn_legal_citation cite --type book \
  --data '{"authors":["王名扬"],"title":"美国行政法","publisher":"北京大学出版社","year":2007,"pages":18}'
```

PowerShell 需要对内部的双引号做转义：

```powershell
python -m cn_legal_citation cite --type book --data '{\"authors\":[\"王名扬\"],\"title\":\"美国行政法\",\"publisher\":\"北京大学出版社\",\"year\":2007,\"pages\":18}'
```

输出：

```
王名扬:《美国行政法》,北京大学出版社2007年版,第18页。
```

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
```

## 支持的文献类型

| 类型 | 说明 | 主要字段 |
|---|---|---|
| `book` | 中文著作（含译著、主编作品、版次） | authors, title, publisher, year, pages, 可选 nationality / translator / edition / authorship |
| `journal` | 期刊论文、集刊论文 | authors, title, journal, year, issue, pages, 可选 volume / publisher |
| `collection` | 论文集析出文献 | authors, title, editor, editor_role, container_title, publisher, year, pages |
| `newspaper` | 报纸文章 | authors, title, newspaper, year, month, day, page |
| `thesis` | 学位论文 | authors, title, school, year, degree, pages |
| `online` | 网络文献 | authors（可省）, title, site, url, 可选 year/month/day |
| `wechat` | 微信公众号文章 | authors, title, account, year, month, day |
| `legal` | 法律、法规、规章、规范性文件 | name, 可选 article / document_number / adoption_info |
| `case` | 裁判文书 | court, case_number, document_type, 可选 case_name / 日期 |
| `foreign_book` | 外文著作（英文） | authors, title, publisher, year, pages |
| `foreign_article` | 外文论文（英文） | authors, title, journal, volume, first_page, year |

用 `python -m cn_legal_citation show --type <类型>` 可以查看每个类型内置的规则依据与示例。

## 设计：规则即数据

所有式样定义在 `cn_legal_citation/rules/*.yaml`，一个文件对应一种文献类型，代码里没有任何硬编码的标点或语序。

```yaml
type: book
label: 中文著作
source: 《法学引注手册》(第二版)示例〔1〕〔2〕〔3〕〔4〕
segments:
  - text: "{authors}{authorship}{colon}"
    requires: [authors]
  - text: "《{title}》"
    requires: [title]
  - text: "{comma}{translator}"
    requires: [translator]
  - text: "{comma}{publisher}"
    requires: [publisher]
  - text: "{comma}{pages}"
    requires: [pages]
  - text: "。"
```

渲染时按顺序拼接各段，只有 `requires` 列出的字段全部非空，该段才参与拼接。译者、版次、页码这些可选信息缺失时，不会留下悬空的逗号。

由此带来两个直接好处：

- **新增文献类型不用改代码。** 在 `rules/` 下加一个 YAML 文件即可，`types` 命令会自动识别。
- **改标点不用改代码。** `rules/index.yaml` 里的 `punctuation` 控制全局冒号与逗号。默认按手册示例呈现的半角形式；若目标刊物要求全角，改成 `"："` 和 `"，"` 即可。

字段值的加工（作者超过三人省略为"甲等"、页码转"第73-75页"、法条转"第1224条第1款第2项"）由 `normalize.py` 里的规范化器完成，在 YAML 的 `fields` 中声明，同样是可配置的。

## 规则依据与验证

式样以《法学引注手册》（第二版，北京大学出版社 2020 年版）为准，参考了何海波《〈法学引注手册〉（第二版）修订说明》以及《法律科学》编辑部 2021 年执行该标准的公告。每个规则文件的 `source` 字段都写明了依据出处。

测试包含 31 个用例，其中 11 条直接取自《法学引注手册》（第二版）公开示例，作为回归基准：

```bash
pip install -e ".[dev]"
pytest
```

这批用例的作用是防止后续调整规则时把已确认的式样改坏。如果你发现某条式样与目标刊物要求不符，改 YAML 里的 `segments` 即可，测试会明确告诉你改坏了哪一条。

## 已知限制

以下几项尚未实现，按优先级排列，欢迎提 issue 或 PR：

1. **学位论文式样**依据的是通行体例，手册第二版未单列示例，欢迎依据手册原文校正。
2. **外文部分**只实现了英文的两种基本式样，作者并列仍用顿号连接（英文宜用 `and` 或逗号）；手册第二版新增的意大利文、俄文体例尚未实现。
3. **重复引用的略写**（"同前注 X"）刻意不实现。手册第二版明确不建议作者使用略写，编辑会在定稿后处理。
4. **脚注编号**不在本工具职责内。编号方式（全文连续还是每页重新起算）由各刊物自定，本工具只生成脚注文本本身。
5. **裁判文书案号**支持字典与字符串两种输入，但不校验案号本身的真实性。引用前请自行核对。

## 免责声明

本项目是学习方法论与工具实践的产物，不构成法律意见，也不保证输出符合任何特定刊物的审稿要求。引用前请自行核对条文、案号与文献信息；正式投稿前请按目标刊物的最新要求复核一遍。

## English

`cn-legal-citation` renders Chinese legal footnotes according to the *Handbook of Legal Citation* (《法学引注手册》, 2nd edition, Peking University Press, 2020). Citation styles live in YAML rule files rather than in Python code, so a formatter change is a one-line edit, not a refactor. Eleven of the 31 test cases are taken verbatim from the handbook's published examples and serve as regression anchors.

## 许可

MIT。见 [LICENSE](LICENSE)。
