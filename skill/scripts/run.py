#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""技能统一入口：把参数转交给内嵌的引注引擎。

这样技能不需要 pip 安装任何东西，解压即用。

用法与引擎命令行完全一致：

    python scripts/run.py types
    python scripts/run.py cite --type book --file data.json
    python scripts/run.py check --file footnotes.txt
    python scripts/run.py doc-check --file 论文.docx
    python scripts/run.py doc-rewrite --file 论文.docx --out 论文_已规范.docx

引擎读不到 PyYAML 时会自动回退读取 vendor/cn_legal_citation/rules.json，
因此本技能零第三方依赖。
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
VENDOR = HERE.parent / "vendor"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from cn_legal_citation.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
