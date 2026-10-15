"""cn-legal-citation：按《法学引注手册》（第二版）生成中文法学脚注。"""

from __future__ import annotations

from .formatter import cite, cite_many, render
from .rules import available_types, load_rules

__version__ = "0.2.0"

__all__ = ["cite", "cite_many", "render", "load_rules", "available_types", "__version__"]
