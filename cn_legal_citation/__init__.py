"""cn-legal-citation：按《法学引注手册》（第二版）生成中文法学脚注。"""

from __future__ import annotations

from .checker import check_many, check_one, summarize, to_markdown
from .docflow import check_document, document_report, rewrite_document
from .docio import (
    extract,
    extract_docx,
    extract_markdown,
    rewrite,
    rewrite_docx,
    rewrite_markdown,
)
from .formatter import cite, cite_many, render
from .parser import parse, parse_one
from .rules import available_types, export_rules, load_rules

__version__ = "0.3.0"

__all__ = [
    "cite",
    "cite_many",
    "render",
    "load_rules",
    "available_types",
    "export_rules",
    "parse",
    "parse_one",
    "check_one",
    "check_many",
    "summarize",
    "to_markdown",
    "check_document",
    "document_report",
    "rewrite_document",
    "extract",
    "extract_docx",
    "extract_markdown",
    "rewrite",
    "rewrite_docx",
    "rewrite_markdown",
    "__version__",
]
