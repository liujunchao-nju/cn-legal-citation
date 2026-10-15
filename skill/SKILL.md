---
name: cn-legal-citation
description: 按《法学引注手册（第二版）》生成、核查、改写法学脚注。脚注格式由确定性规则引擎产出（69 类文献、覆盖手册 150 条），不是模型现场拼格式，因此同一输入永远得到同一结果、可逐条核查。支持单条生成、整篇核查报告、以及把已有的 Word 或 Markdown 文稿里的脚注批量改成规范式样（输出副本，原件不动）。触发词：引注、脚注、页下注、注释格式、引注手册、法学引注、改脚注、核脚注、脚注不规范、投稿格式、参考文献格式、查引注。Use when the user asks to generate, check, or reformat legal academic footnotes/citations per the Chinese Legal Citation Manual, especially for .docx or .md papers.
agent_created: true
version: "0.3.0"
display_name: "法学引注（手册第二版·确定性引擎）"
display_name_en: "Chinese Legal Citation (Deterministic Engine)"
description_zh: "按《法学引注手册》第二版生成、核查、改写法学脚注，格式由确定性规则引擎产出，覆盖 69 类文献与手册 150 条。支持单条生成、整篇核查、Word/Markdown 脚注批量规范化。"
description_en: "Generate, check, and reformat Chinese legal footnotes per the Handbook of Legal Citation (2nd ed.) using a deterministic rule engine covering 69 document types and all 150 clauses."
---

# 法学引注（《法学引注手册》第二版）

脚注格式由**规则引擎**产出，覆盖手册第二版全部 150 条、69 类文献。
模型只负责读懂材料、填字段、调工具、解释结果，**不负责拼格式**。

## 一、为什么不能自己拼格式

这个技能唯一的价值就是「确定性」：同一条文献，今天明天、你我这台机器，
产出的脚注必须逐字相同，并且能拿手册条款回查。

所以：

- 脚注文本**一律**由 `scripts/run.py` 产出，不要凭记忆手写格式。
- 字段拿不准就问用户，**不要猜**。宁可少填一个字段，也不要编一个看起来
  合理的出版社或年份。
- 引擎说「未能解析」，就如实告诉用户解析不了，不要硬凑一个格式。

## 二、三种场景

先判断用户要做哪一件事，再走对应流程。

| 场景 | 用户说的话 | 走什么 |
|---|---|---|
| L1 单条生成 | 「这段话引了张新宝侵权责任法第5版，给我加个脚注」 | 直接调 `cite` |
| L2 整篇核查 | 「帮我核一下这篇论文的脚注规不规范」 | `doc-check`，出报告 |
| L3 批量改写 | 「把这篇论文的脚注都改成规范格式」 | `doc-rewrite`，出新文件 |

### L1：单条生成

1. 从用户的话、截图、链接或文献片段里提取字段（作者、书名、出版社、年份、页码……）。
2. 先查类型：`python scripts/run.py types`，或 `show --type <类型>` 看该类型的字段与示例。
3. 把字段写成 JSON，调 `cite`：

```bash
python scripts/run.py cite --type book --file data.json
```

`data.json`：

```json
{"authors": ["张新宝"], "title": "侵权责任法", "edition": 5,
 "publisher": "中国人民大学出版社", "year": 2020, "pages": [73, 75]}
```

输出：`张新宝:《侵权责任法》(第5版),中国人民大学出版社2020年版,第73-75页。`

**信息不全时**：把已确定的写进 JSON，缺的那部分直接问用户。例如只说了书名
和作者，就输出已能确定的部分，并明确列出还缺什么（出版社、年份、页码）。

### L2：整篇核查

```bash
python scripts/run.py doc-check --file 论文.docx            # 打印报告
python scripts/run.py doc-check --file 论文.docx --out 报告.md   # 写入文件
```

报告把每条脚注分成四类：

| 状态 | 含义 | 怎么跟用户说 |
|---|---|---|
| 完全合规 | 引擎能逐字复现 | 没问题 |
| 标点需规范化 | 字段都对，只是用了全角标点 | 可一键规范化 |
| 格式不符 | 字段对但式样不对（缺"载"、案号顺序反了等） | 给出建议改法 |
| 未能解析 | 模式没认出 | **如实说明，请用户确认字段** |

拿到报告后，用自然语言跟用户讲清楚：多少条、哪几条、问题是什么、建议怎么改。
**不要**把整份 markdown 报告原样倒给用户。

### L3：批量改写

```bash
python scripts/run.py doc-rewrite --file 论文.docx --out 论文_已规范.docx --table 变更对照.md
```

**必须先跟用户确认再执行**，并说明三件事：

1. 输出的是**新文件**，原件一个字节都不会动；
2. 只改「标点需规范化」和「格式不符」的脚注；
3. 「未能解析」的脚注**不会**被改动，需要用户补字段后才处理。

改完后把变更对照表给用户看（位置 / 改前 / 改后），并报告写回复核结果。

## 三、硬性纪律

以下四条不得违反：

1. **脚注文本只能来自引擎。** 任何情况下都不要自己拼格式，包括"就差一个字
   我手动补一下"。
2. **不覆盖原件。** `--out` 必须与输入路径不同；引擎会拒绝同路径写入，不要
   试图绕过。
3. **不替用户猜字段。** 引擎报「未能解析」时，把这些脚注列给用户，请他确认
   文献信息。
4. **不静默改写。** L3 必须先说明会改什么、改成什么，得到确认后再执行。

## 四、支持的文件类型

| 类型 | 说明 |
|---|---|
| `.docx` | Word 真实页下脚注（读 `word/footnotes.xml`）。若文档里的"脚注"是用上标数字手打的，读不到，需先转成真实脚注 |
| `.md` | Markdown 脚注定义（`[^1]: 文本`） |

不支持 `.doc`（旧格式）、`.tex`、`.pdf`。遇到这些请告诉用户先另存为 `.docx` 或 `.md`。

## 五、环境

技能自带引擎，**不需要 pip 安装任何东西**。

```bash
# 任选一个能用的 python；先用管理版
PY="C:/Users/ljcljc/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
$PY scripts/run.py types
```

若管理版路径不存在，退回 `python` 或 `py -3` 即可 —— 引擎只依赖标准库
（PyYAML 缺失时自动读内置的 `rules.json`）。

开工前可先跑一次自检：

```bash
$PY scripts/selfcheck.py
```

自检覆盖：规则加载、中英文渲染、逆向解析、核查分级、手册示例往返。
全部 OK 说明技能完好；有 FAIL 说明环境有问题，先解决再干活。

## 六、命令速查

```bash
run.py types                           # 69 类文献一览
run.py show --type case                # 某类型的字段、依据、示例
run.py cite --type book --file d.json  # 单条生成
run.py batch --file items.json         # 批量生成
run.py parse --text "…"                # 脚注 → 字段（逆向解析）
run.py check --file notes.txt          # 核查脚注文本（每行一条）
run.py doc-extract --file 论文.docx    # 只提取脚注
run.py doc-check --file 论文.docx      # 整篇核查
run.py doc-rewrite --file a.docx --out b.docx --table t.md
run.py export --out rules.json         # 导出规则为 JSON
```

加 `--rules <目录>` 可加载自定义规则目录（例如某刊物改过的式样）。

## 七、规则依据

式样以《法学引注手册》（第二版，北京大学出版社 2025 年版）为准，共 150 条。
每个类型的依据条款写在规则文件的 `source` 字段里，`show --type <类型>` 可看。

引擎当前覆盖 69 类文献：中文纸质出版文献、网络电子文献、未发表文献、
法律文件与官方文件、司法案例与统计数据，以及英、法、德、意、俄、日六种外文。

## 八、与相邻技能的边界

| 需求 | 归谁 |
|---|---|
| 引注**格式**对不对 | 本技能 |
| 法条**内容**是否现行有效、条文原文 | `legal-citation-verify` |
| 把长文从 Markdown 排成 Word 报告 | `legal-docx-formatter` |
| 文档里根本没有脚注、需要注入 | `docx-real-footnotes` |

用户问的是法条内容本身，不是格式，就转 `legal-citation-verify`，别硬用本技能。

## 九、常见问题

**用户说「脚注没识别出来」**
先确认是真实脚注还是手打上标数字：`doc-extract --file 论文.docx` 若返回 0 条，
说明文档里没有 Word 脚注对象。请他先把上标转成真实脚注（Word 里可以用查找替换
或宏），再重跑。

**某条脚注引擎认不出来**
把该条原文和引擎的提示一起给用户，问清作者、书名、出版社、年份等要素，再
用 `cite` 生成规范版本。认不出来通常是少见类型（如法德日文献），不是技能故障。

**用户想改全局标点（全角/半角）**
告诉他默认按手册示例用半角；若目标刊物要求全角，改规则目录下 `index.yaml`
的 `punctuation` 即可，无需改代码。也可用 `--rules` 指定一份自定义规则目录。
