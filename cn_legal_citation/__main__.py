"""支持 ``python -m cn_legal_citation`` 调用。"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
