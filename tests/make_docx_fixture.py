"""生成含真实 Word 页下脚注的 .docx 测试样本。

python-docx 没有脚注 API，因此这里直接拼 OOXML。生成的 .docx 是完整
合法的文档包（content types、rels、styles 齐备），Word 可直接打开，
用于验证 docio 的脚注提取与写回。

仅在测试中使用，不属于运行时依赖。
"""

from __future__ import annotations

import pathlib
import zipfile

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
FN_CT = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.footnotes+xml"
)
DOC_CT = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document.main+xml"
)
STYLES_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"

_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _esc_attr(text: str) -> str:
    return _esc(text).replace('"', "&quot;")


def _content_types() -> str:
    return (
        _HEAD
        + f'<Types xmlns="{CT_NS}">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f'<Override PartName="/word/document.xml" ContentType="{DOC_CT}"/>'
        f'<Override PartName="/word/styles.xml" ContentType="{STYLES_CT}"/>'
        f'<Override PartName="/word/footnotes.xml" ContentType="{FN_CT}"/>'
        "</Types>"
    )


def _root_rels() -> str:
    return (
        _HEAD
        + f'<Relationships xmlns="{PKG_REL}">'
        f'<Relationship Id="rId1" Type="{R_NS}/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )


def _document_rels() -> str:
    return (
        _HEAD
        + f'<Relationships xmlns="{PKG_REL}">'
        f'<Relationship Id="rId1" Type="{R_NS}/styles" Target="styles.xml"/>'
        f'<Relationship Id="rId2" Type="{R_NS}/footnotes" Target="footnotes.xml"/>'
        "</Relationships>"
    )


def _styles() -> str:
    sz = 18  # 9pt
    return (
        _HEAD
        + f'<w:styles xmlns:w="{W_NS}">'
        "<w:docDefaults><w:rPrDefault><w:rPr>"
        '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="宋体"/>'
        '<w:sz w:val="21"/><w:szCs w:val="21"/>'
        "</w:rPr></w:rPrDefault></w:docDefaults>"
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
        '<w:style w:type="character" w:styleId="FootnoteReference">'
        '<w:name w:val="footnote reference"/>'
        '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="FootnoteText">'
        '<w:name w:val="footnote text"/><w:basedOn w:val="Normal"/>'
        f'<w:rPr><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr></w:style>'
        "</w:styles>"
    )


def _document(footnote_count: int, body_text: str = "这是一篇测试文稿。") -> str:
    refs = "".join(
        '<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr>'
        f'<w:footnoteReference w:id="{i}"/></w:r>'
        for i in range(1, footnote_count + 1)
    )
    return (
        _HEAD
        + f'<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}"><w:body>'
        f"<w:p><w:r><w:t>{_esc(body_text)}</w:t></w:r>{refs}</w:p>"
        '<w:sectPr><w:footnotePr><w:numFmt w:val="decimal"/></w:footnotePr>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1800" w:bottom="1440" w:left="1800"/>'
        "</w:sectPr></w:body></w:document>"
    )


def _footnotes(texts: list[str]) -> str:
    sep = (
        '<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>'
        '<w:footnote w:type="continuationSeparator" w:id="0">'
        "<w:p><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>"
    )
    body = ""
    for index, text in enumerate(texts, start=1):
        body += (
            f'<w:footnote w:id="{index}"><w:p>'
            '<w:pPr><w:pStyle w:val="FootnoteText"/></w:pPr>'
            '<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteRef/></w:r>'
            f'<w:r><w:t xml:space="preserve">{_esc(text)}</w:t></w:r>'
            "</w:p></w:footnote>"
        )
    return _HEAD + f'<w:footnotes xmlns:w="{W_NS}">{sep}{body}</w:footnotes>'


def make_docx(
    path: str | pathlib.Path,
    footnotes: list[str],
    body_text: str = "这是一篇测试文稿。",
) -> pathlib.Path:
    """写出一个含 ``len(footnotes)`` 条真实页下脚注的 .docx。"""
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _content_types())
        zf.writestr("_rels/.rels", _root_rels())
        zf.writestr("word/_rels/document.xml.rels", _document_rels())
        zf.writestr("word/document.xml", _document(len(footnotes), body_text))
        zf.writestr("word/styles.xml", _styles())
        zf.writestr("word/footnotes.xml", _footnotes(footnotes))
    return target


if __name__ == "__main__":
    import sys

    out = sys.argv[1] if len(sys.argv) > 1 else "fixture.docx"
    make_docx(out, ["第一条脚注。", "第二条脚注。"])
    print("written:", out)
