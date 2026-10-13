"""引注规则加载。

规则与代码分离：所有式样定义在 rules/*.yaml 中，本模块只负责读取与校验。
新增一种文献类型不需要改代码，新增一个 YAML 文件即可。
"""

from __future__ import annotations

import pathlib

import yaml

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent
RULES_DIR = PACKAGE_DIR / "rules"

DEFAULT_PUNCTUATION = {
    "colon": ":",
    "comma": ",",
    "period": "。",
}

REQUIRED_RULE_KEYS = ("type", "label", "segments")


class RuleError(ValueError):
    """规则文件不合法。"""


def load_rules(rules_dir: str | pathlib.Path | None = None):
    """返回 ``(rules, punctuation)``。

    rules 形如 ``{"book": {...}, "journal": {...}}``；
    punctuation 为全局标点配置，可在 rules/index.yaml 中覆盖。
    """
    directory = pathlib.Path(rules_dir) if rules_dir else RULES_DIR
    if not directory.is_dir():
        raise RuleError(f"规则目录不存在: {directory}")

    rules: dict[str, dict] = {}
    punctuation = dict(DEFAULT_PUNCTUATION)

    for path in sorted(directory.glob("*.yaml")):
        with path.open(encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
        if not isinstance(doc, dict):
            raise RuleError(f"{path.name} 内容必须是映射")

        if path.stem == "index":
            punctuation.update(doc.get("punctuation") or {})
            continue

        missing = [k for k in REQUIRED_RULE_KEYS if k not in doc]
        if missing:
            raise RuleError(f"{path.name} 缺少必要字段: {', '.join(missing)}")
        if not isinstance(doc["segments"], list) or not doc["segments"]:
            raise RuleError(f"{path.name} 的 segments 必须是非空列表")

        doc["_file"] = path.name
        rules[doc["type"]] = doc

    if not rules:
        raise RuleError(f"规则目录中没有可用的规则文件: {directory}")
    return rules, punctuation


def available_types(rules_dir: str | pathlib.Path | None = None) -> list[str]:
    rules, _ = load_rules(rules_dir)
    return sorted(rules)
