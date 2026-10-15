"""引注规则加载。

规则与代码分离：所有式样定义在 rules/*.yaml 中，本模块只负责读取与校验。
新增一种文献类型不需要改代码，新增一个 YAML 文件即可。

为便于把引擎内嵌进技能包等免安装场景运行，本模块支持在缺少 PyYAML 时
回退读取 rules.json（由 ``cn-legal-citation export`` 生成）。
"""

from __future__ import annotations

import json
import pathlib

try:  # PyYAML 为可选依赖：缺失时回退 JSON 规则
    import yaml
except ImportError:  # pragma: no cover - 取决于运行环境
    yaml = None

PACKAGE_DIR = pathlib.Path(__file__).resolve().parent
RULES_DIR = PACKAGE_DIR / "rules"
JSON_RULES = PACKAGE_DIR / "rules.json"

DEFAULT_PUNCTUATION = {
    "colon": ":",
    "comma": ",",
    "period": "。",
}

REQUIRED_RULE_KEYS = ("type", "label", "segments")


class RuleError(ValueError):
    """规则文件不合法。"""


def _validate(doc: dict, source: str) -> dict:
    if not isinstance(doc, dict):
        raise RuleError(f"{source} 内容必须是映射")
    missing = [k for k in REQUIRED_RULE_KEYS if k not in doc]
    if missing:
        raise RuleError(f"{source} 缺少必要字段: {', '.join(missing)}")
    if not isinstance(doc["segments"], list) or not doc["segments"]:
        raise RuleError(f"{source} 的 segments 必须是非空列表")
    return doc


def _load_from_yaml(directory: pathlib.Path):
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
        _validate(doc, path.name)
        doc["_file"] = path.name
        rules[doc["type"]] = doc
    return rules, punctuation


def _load_from_json(path: pathlib.Path):
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    punctuation = dict(DEFAULT_PUNCTUATION)
    punctuation.update(payload.get("punctuation") or {})
    rules: dict[str, dict] = {}
    for name, doc in (payload.get("rules") or {}).items():
        _validate(doc, f"{path.name}:{name}")
        doc.setdefault("_file", f"{name}.yaml")
        rules[doc["type"]] = doc
    return rules, punctuation


def load_rules(rules_dir: str | pathlib.Path | None = None):
    """返回 ``(rules, punctuation)``。

    rules 形如 ``{"book": {...}, "journal": {...}}``；
    punctuation 为全局标点配置，可在 rules/index.yaml 中覆盖。

    优先读取 YAML；YAML 不可用（缺 PyYAML）或目录内没有 YAML 时，
    回退读取同目录的 rules.json，再退回包内自带的 rules.json。
    """
    directory = pathlib.Path(rules_dir) if rules_dir else RULES_DIR

    if yaml is not None and directory.is_dir():
        yaml_files = sorted(directory.glob("*.yaml"))
        if yaml_files:
            rules, punctuation = _load_from_yaml(directory)
            if rules:
                return rules, punctuation

    for candidate in (directory / "rules.json", JSON_RULES):
        if candidate.is_file():
            rules, punctuation = _load_from_json(candidate)
            if rules:
                return rules, punctuation

    raise RuleError(
        f"未能加载规则：{directory} 下既没有 YAML 规则，也没有 rules.json"
    )


def export_rules(target: str | pathlib.Path, rules_dir: str | pathlib.Path | None = None) -> pathlib.Path:
    """把规则导出为单个 JSON 文件，供免安装环境（如内嵌技能包）使用。"""
    rules, punctuation = load_rules(rules_dir)
    payload = {"punctuation": punctuation, "rules": rules}
    path = pathlib.Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def available_types(rules_dir: str | pathlib.Path | None = None) -> list[str]:
    rules, _ = load_rules(rules_dir)
    return sorted(rules)
