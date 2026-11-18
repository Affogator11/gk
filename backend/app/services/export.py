# -*- coding: utf-8 -*-
"""导出 Word 试卷（试卷卷面 + 参考答案与解析）。"""
from __future__ import annotations

import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


def _set_font(run, name: str = "宋体", size: float = 10.5, bold: bool = False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), name)


def _p(doc, text="", *, size=10.5, bold=False, font="宋体", align=None,
       before=0, after=4, indent=False, line=18):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = Pt(line)
    if indent:
        pf.first_line_indent = Pt(21)
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if align == "right":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if text:
        parts = str(text).split("\n")
        run = p.add_run(parts[0])
        _set_font(run, font, size, bold)
        for extra in parts[1:]:
            run.add_break()
            run.add_text(extra)
    return p


def _rule(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    pPr = p._element.get_or_add_pPr()
    pbdr = pPr.makeelement(qn("w:pBdr"), {})
    bottom = pbdr.makeelement(qn("w:bottom"), {
        qn("w:val"): "single", qn("w:sz"): "6", qn("w:space"): "1", qn("w:color"): "BBBBBB"})
    pbdr.append(bottom)
    pPr.append(pbdr)


def build_docx(paper: dict, report: dict) -> bytes:
    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    sec.top_margin = sec.bottom_margin = Cm(2.2)
    sec.left_margin = sec.right_margin = Cm(2.2)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    _p(doc, paper["title"], size=16, bold=True, font="黑体", align="center", after=6)
    _p(doc, f"考试时间：{paper['duration_min']} 分钟　　满分：{int(paper['total_score'])} 分",
       size=10.5, align="center", after=2)
    _p(doc, "姓名：____________　　班级：____________　　考号：____________",
       size=10, align="center", after=8)
    _rule(doc)
    _p(doc, "注意事项：1．答题前请将姓名、班级、考号填写清楚。2．选择题答案填涂在答题卡上，"
            "非选择题答案写在答题卡指定区域内。", size=9, after=10)

    groups: dict[str, list[dict]] = {}
    for it in paper["items"]:
        groups.setdefault(it["section"], []).append(it)

    for section in report["sections"]:
        key = section["key"]
        items = sorted(groups.get(key, []), key=lambda i: i["position"])
        if not items:
            continue
        _p(doc, section["label"], size=12, bold=True, font="黑体", before=8, after=2)
        _p(doc, section.get("hint", ""), size=9, after=6)

        for idx, it in enumerate(items, start=1):
            _p(doc, f"{idx}．{it['stem']}", size=10.5, after=2)
            if it["options"]:
                opts = it["options"]
                for row in range(0, len(opts), 2):
                    pair = opts[row:row + 2]
                    _p(doc, "　　".join(pair), size=10.5, after=1, indent=True)
            if it["qtype"] == "blank":
                _p(doc, "答：______________________", size=10.5, after=6)
            elif it["qtype"] == "solve":
                blanks = max(4, int(it["score"] * 0.9))
                for _ in range(blanks):
                    _p(doc, "", size=10.5, after=0, line=22)
            else:
                _p(doc, "", size=8, after=2)

    doc.add_page_break()
    _p(doc, f"{paper['title']}　参考答案与解析", size=14, bold=True, font="黑体", align="center", after=10)

    n = 0
    for section in report["sections"]:
        items = sorted(groups.get(section["key"], []), key=lambda i: i["position"])
        for it in items:
            n += 1
            _p(doc, f"{n}．{it['answer']}", size=10.5, bold=True, after=1)
            if it.get("analysis"):
                _p(doc, f"【解析】{it['analysis']}", size=9.5, after=6)

    _p(doc, f"（本卷难度 {report['difficulty']:.2f}，即预期得分率 "
            f"{report['difficulty']*100:.0f}%；覆盖考点 {report['coverage_ratio']*100:.0f}%；"
            f"体检 {report['health']} 分）", size=8.5, after=0, align="right")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
