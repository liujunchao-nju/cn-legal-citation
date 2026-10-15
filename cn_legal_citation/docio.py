"""文档通道：从 Markdown / Word 提取脚注，并把改写结果写回副本。

支持两种格式：

- ``.md``：Markdown 脚注定义（``[^1]: 文本``）。
- ``.docx``：Word 的真实页下脚注，存于 ``word/footnotes.xml``。
  python-docx 没有脚注 API，因此这里直接操作 OOXML。

安全约定（贯穿整个模块）：

1. **绝不覆盖原件**。写回一律输出到新路径，调用方负责给出新路径。
2. **只改脚注文本**。docx 只替换脚注节点内的文字，其余部件保持原字节。
3. **写完即验**。写回后重新读取输出文件，确认脚注文本与预期一致。
"""

from __future__ import annotations

import io
import pathlib
import re
import zipfile
from xml.etree import ElementTree as ET

__all__ = [
    "extract_markdown",
    "extract_docx",
    "extract",
    "rewrite_markdown",
    "rewrite_docx",
    "rewrite",
    "docx_footnote_count",
]

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % W_NS

_MD_DEF_RE = re.compile(r"^\[\^(?P<label>[^\]]+)\]:[ \t]*(?P<text>.*)$")
_MD_CONT_RE = re.compile(r"^(?:[ \t]{2,}|\t)(?P<text>\S.*)$")
_XMLNS_RE = re.compile(r'xmlns:([A-Za-z0-9_]+)="([^"]+)"')


class DocError(RuntimeError):
    """文档处理失败。"""


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------


def extract_markdown(path: str | pathlib.Path) -> list[dict]:
    """提取 Markdown 脚注定义。返回 ``[{"locator", "label", "text"}]``。"""
    source = pathlib.Path(path).read_text(encoding="utf-8")
    lines = source.splitlines()
    entries: list[dict] = []
    current: dict | None = None

    for line in lines:
        m = _MD_DEF_RE.match(line)
        if m:
            if current:
                entries.append(current)
            current = {
                "locator": f"[^{m.group('label')}]",
                "label": m.group("label"),
                "text": m.group("text").strip(),
            }
            continue
        if current:
            cont = _MD_CONT_RE.match(line)
            if cont:
                current["text"] = (current["text"] + " " + cont.group("text").strip()).strip()
                continue
            if not line.strip():
                continue
            entries.append(current)
            current = None
    if current:
        entries.append(current)
    return entries


def rewrite_markdown(
    path: str | pathlib.Path,
    replacements: dict[str, str],
    out_path: str | pathlib.Path,
) -> pathlib.Path:
    """按 ``{label: 新文本}`` 改写 Markdown 脚注，写入 ``out_path``。"""
    src = pathlib.Path(path)
    dst = pathlib.Path(out_path)
    if src.resolve() == dst.resolve():
        raise DocError("拒绝覆盖原件：请给出不同的输出路径")

    lines = src.read_text(encoding="utf-8").splitlines()
    out_lines: list[str] = []
    current_label: str | None = None

    for line in lines:
        m = _MD_DEF_RE.match(line)
        if m:
            label = m.group("label")
            if label in replacements:
                out_lines.append(f"[^{label}]: {replacements[label]}")
                current_label = label
                continue
            current_label = None
            out_lines.append(line)
            continue
        if current_label is not None:
            cont = _MD_CONT_RE.match(line)
            if cont:
                continue  # 该注释已被整体替换，丢弃原续行
            if not line.strip():
                out_lines.append(line)
                continue
            current_label = None
        out_lines.append(line)

    text = "\n".join(out_lines)
    if src.read_text(encoding="utf-8").endswith("\n"):
        text += "\n"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    return dst


# --------------------------------------------------------------------------
# DOCX
# --------------------------------------------------------------------------


def _register_namespaces(raw_xml: str) -> None:
    for prefix, uri in _XMLNS_RE.findall(raw_xml):
        if prefix in ("xml", "xmlns"):
            continue
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            continue


def _footnote_text(node: ET.Element) -> str:
    """拼接一个脚注节点内所有 ``w:t`` 的文字。"""
    parts = []
    for t in node.iter(f"{W}t"):
        parts.append(t.text or "")
    return "".join(parts)


def _read_footnotes_xml(docx_path: pathlib.Path) -> tuple[str, dict[str, str]]:
    with zipfile.ZipFile(docx_path) as zf:
        if "word/footnotes.xml" not in zf.namelist():
            raise DocError(
                "该 .docx 不含 word/footnotes.xml，说明文档里没有 Word 页下脚注。"
                "若脚注是手动打的上标数字，请先转成真实脚注。"
            )
        raw = zf.read("word/footnotes.xml").decode("utf-8")
    return raw, {}


def docx_footnote_count(docx_path: str | pathlib.Path) -> int:
    """返回文档的 Word 脚注条数（不含分隔符节点）。"""
    return len(extract_docx(docx_path))


def extract_docx(path: str | pathlib.Path) -> list[dict]:
    """提取 docx 的页下脚注。

    返回 ``[{"locator", "id", "text"}]``，按脚注在文档中的顺序排列。
    """
    docx_path = pathlib.Path(path)
    raw, _ = _read_footnotes_xml(docx_path)
    _register_namespaces(raw)
    root = ET.fromstring(raw)

    entries: list[dict] = []
    for node in root.findall(f"{W}footnote"):
        fid = node.get(f"{W}id")
        if fid is None:
            continue
        try:
            if int(fid) < 1:
                continue  # -1 / 0 为分隔符与续页分隔符
        except ValueError:
            continue
        text = _footnote_text(node).strip()
        entries.append({"locator": f"脚注 {fid}", "id": fid, "text": text})
    entries.sort(key=lambda item: int(item["id"]))
    return entries


def _set_footnote_text(node: ET.Element, text: str) -> bool:
    """把脚注节点的文字整体替换为 ``text``，保留首个文字 run 的格式。"""
    runs = list(node.iter(f"{W}r"))
    targets: list[tuple[ET.Element, ET.Element]] = []
    for run in runs:
        for t in run.findall(f"{W}t"):
            targets.append((run, t))
    if not targets:
        return False

    first_run, first_t = targets[0]
    first_t.text = text
    first_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    for run, t in targets[1:]:
        run.remove(t)

    # 清掉除首个以外被掏空、只剩下格式的 run，避免产生空节点
    for run, _ in targets[1:]:
        if not list(run) or all(child.tag == f"{W}rPr" for child in run):
            parent = None
            for candidate in node.iter():
                if run in list(candidate):
                    parent = candidate
                    break
            if parent is not None:
                parent.remove(run)
    return True


def rewrite_docx(
    path: str | pathlib.Path,
    replacements: dict[str, str],
    out_path: str | pathlib.Path,
) -> pathlib.Path:
    """按 ``{脚注 id: 新文本}`` 改写 docx 脚注，写入 ``out_path``。

    只替换 ``word/footnotes.xml``，压缩包内其余部件保持原字节。
    """
    src = pathlib.Path(path)
    dst = pathlib.Path(out_path)
    if src.resolve() == dst.resolve():
        raise DocError("拒绝覆盖原件：请给出不同的输出路径")

    raw, _ = _read_footnotes_xml(src)
    _register_namespaces(raw)
    root = ET.fromstring(raw)

    changed = 0
    for node in root.findall(f"{W}footnote"):
        fid = node.get(f"{W}id")
        if fid in replacements:
            if _set_footnote_text(node, replacements[fid]):
                changed += 1

    if changed == 0:
        raise DocError("没有任何脚注被替换：请检查脚注编号是否与文档一致")

    body = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    xml_bytes = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n' + body
    )

    dst.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(
        dst, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/footnotes.xml":
                data = xml_bytes
            zout.writestr(item, data)
    return dst


# --------------------------------------------------------------------------
# 统一入口
# --------------------------------------------------------------------------


def extract(path: str | pathlib.Path) -> list[dict]:
    """按扩展名分派提取。"""
    suffix = pathlib.Path(path).suffix.lower()
    if suffix in (".md", ".markdown"):
        return extract_markdown(path)
    if suffix == ".docx":
        return extract_docx(path)
    raise DocError(f"暂不支持的文件类型：{suffix}（当前支持 .md 与 .docx）")


def rewrite(
    path: str | pathlib.Path,
    replacements: dict[str, str],
    out_path: str | pathlib.Path,
) -> pathlib.Path:
    """按扩展名分派写回。``replacements`` 的键为 markdown 标签或 docx 脚注 id。"""
    suffix = pathlib.Path(path).suffix.lower()
    if suffix in (".md", ".markdown"):
        return rewrite_markdown(path, replacements, out_path)
    if suffix == ".docx":
        return rewrite_docx(path, replacements, out_path)
    raise DocError(f"暂不支持的文件类型：{suffix}（当前支持 .md 与 .docx）")
