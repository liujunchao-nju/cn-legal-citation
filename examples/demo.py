"""Python API 演示。

运行：python examples/demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cn_legal_citation import cite, cite_many  # noqa: E402

SAMPLES = [
    ("book", {
        "authors": ["王名扬"],
        "title": "美国行政法",
        "publisher": "北京大学出版社",
        "year": 2007,
        "pages": 18,
    }),
    ("journal", {
        "authors": ["季卫东"],
        "title": "法律程序的意义——对中国法制建设的另一种思考",
        "journal": "中国社会科学",
        "year": 1993,
        "issue": 1,
        "pages": 91,
    }),
    ("legal", {"name": "民法典", "article": {"article": 1224, "paragraph": 1, "item": 2}}),
    ("case", {
        "court": "北京市海淀区人民法院",
        "case_number": {"year": 1998, "code": "海行初字", "number": 142},
        "document_type": "行政判决书",
    }),
]


def main() -> int:
    for type_name, data in SAMPLES:
        print(f"[{type_name}] {cite(type_name, data)}")

    print("\n批量：")
    for line in cite_many([{"type": t, "data": d} for t, d in SAMPLES]):
        print(" ", line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
