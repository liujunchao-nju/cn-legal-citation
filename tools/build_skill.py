#!/usr/bin/env python
"""把仓库源码组装成可分发、可离线运行的技能包。

做三件事：

1. 把 ``skill/`` 下的手写内容（SKILL.md、脚本、参考）与引擎源码
   （``cn_legal_citation/``）组装到目标技能目录；
2. 导出 ``rules.json``，使技能在缺 PyYAML 的环境也能跑；
3. 打成一个 zip，便于分发。

用法：

    python tools/build_skill.py                     # 组装并打包
    python tools/build_skill.py --target <目录>     # 指定技能安装目录
    python tools/build_skill.py --no-zip            # 只组装不打包
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from cn_legal_citation import __version__, export_rules, load_rules  # noqa: E402
import gen_skill_refs  # noqa: E402

SKILL_SRC = ROOT / "skill"
PACKAGE = ROOT / "cn_legal_citation"
DIST = ROOT / "dist"
SKILL_NAME = "cn-legal-citation"

# 手写文件（会从 skill/ 复制）；引擎文件从包目录复制
HANDWRITTEN = ("SKILL.md",)
HANDWRITTEN_DIRS = ("scripts",)


def build(target: pathlib.Path, clean: bool = True, refs: bool = True) -> pathlib.Path:
    if not SKILL_SRC.is_dir():
        raise SystemExit(f"找不到技能源码目录：{SKILL_SRC}")

    if clean and target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    # 1. 手写内容
    for name in HANDWRITTEN:
        shutil.copy2(SKILL_SRC / name, target / name)
    for name in HANDWRITTEN_DIRS:
        src = SKILL_SRC / name
        if src.is_dir():
            shutil.copytree(src, target / name, dirs_exist_ok=True)

    # 2. 引擎源码（去掉 __pycache__）
    vendor = target / "vendor" / "cn_legal_citation"
    rules_dir = vendor / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(PACKAGE.glob("*.py")):
        shutil.copy2(path, vendor / path.name)
    for path in sorted((PACKAGE / "rules").glob("*.yaml")):
        shutil.copy2(path, rules_dir / path.name)

    # 3. 导出 JSON 规则（免 PyYAML 环境的回退）
    export_rules(vendor / "rules.json")

    # 4. 重新生成速查参考，保证与引擎一致（不依赖仓库里的旧副本）
    if refs:
        refs_dir = target / "references"
        refs_dir.mkdir(parents=True, exist_ok=True)
        loaded, _ = load_rules()
        gen_skill_refs.gen_types(loaded, refs_dir / "types.md")
        gen_skill_refs.gen_fields(loaded, refs_dir / "fields.md")
        # workflow.md 是手写文档，从源码复制
        manual = SKILL_SRC / "references" / "workflow.md"
        if manual.is_file():
            shutil.copy2(manual, refs_dir / "workflow.md")

    return target


def zip_skill(target: pathlib.Path) -> pathlib.Path:
    DIST.mkdir(parents=True, exist_ok=True)
    archive = DIST / f"{SKILL_NAME}-skill-v{__version__}.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(target.rglob("*")):
            if path.is_file():
                zf.write(path, pathlib.Path(SKILL_NAME) / path.relative_to(target))
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description="组装 cn-legal-citation 技能包")
    parser.add_argument(
        "--target",
        help="技能安装目录，默认 ~/.workbuddy/skills/cn-legal-citation",
        default=str(pathlib.Path.home() / ".workbuddy" / "skills" / SKILL_NAME),
    )
    parser.add_argument("--no-zip", action="store_true", help="只组装，不打包")
    args = parser.parse_args()

    target = pathlib.Path(args.target)
    build(target)
    files = [p for p in target.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    print(f"技能已组装到 {target}")
    print(f"  文件 {len(files)} 个，共 {total / 1024:.0f} KB")

    if not args.no_zip:
        archive = zip_skill(target)
        print(f"  已打包 {archive}（{archive.stat().st_size / 1024:.0f} KB）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
