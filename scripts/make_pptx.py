"""One-page summary slide in simple English (editable text boxes):  python scripts/make_pptx.py
Numbers are read from evals/results/latest.json so the slide never drifts from the real run.
"""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
NAVY, ORANGE, GREY, WHITE = RGBColor(0x1E, 0x29, 0x3B), RGBColor(0xEA, 0x58, 0x0C), RGBColor(0x47, 0x55, 0x69), RGBColor(0xFF, 0xFF, 0xFF)
RED, BLUE, GREEN, LIGHT = RGBColor(0xDC, 0x26, 0x26), RGBColor(0x25, 0x63, 0xEB), RGBColor(0x16, 0xA3, 0x4A), RGBColor(0xF1, 0xF5, 0xF9)


def box(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1.25)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = 0.08
    s.shadow.inherit = False
    return s


def text(slide, x, y, w, h, lines, size=12, color=NAVY, bold_first=False, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, Inches(0.04))
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(3)
        if isinstance(ln, tuple):
            content, sz, col, bold = ln
        else:
            content, sz, col, bold = ln, size, color, bold_first and i == 0
        r = p.add_run()
        r.text = content
        r.font.size, r.font.color.rgb, r.font.bold, r.font.name = Pt(sz), col, bold, "Calibri"
    return tb


def main() -> None:
    res = json.loads((ROOT / "evals" / "results" / "latest.json").read_text(encoding="utf-8"))["summary"]
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    s = prs.slides.add_slide(prs.slide_layouts[6])

    # Header band
    box(s, 0, 0, 13.333, 1.15, fill=NAVY, shape=MSO_SHAPE.RECTANGLE)
    text(s, 0.45, 0.14, 9.5, 0.6, [("MIKRA: the right answer from the right manual", 28, WHITE, True)])
    text(s, 0.45, 0.68, 10, 0.4, [("A team of AI agents that sends each question to the Safety, Maintenance or Quality manuals and answers with sources.", 13, RGBColor(0xCB, 0xD5, 0xE1), False)])
    tag = box(s, 10.55, 0.33, 2.4, 0.48, fill=ORANGE)
    tag.text_frame.text = "Prototype · synthetic data"
    for p in tag.text_frame.paragraphs:
        p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            r.font.size, r.font.bold, r.font.color.rgb = Pt(12), True, WHITE

    # Row 1: problem | how it works
    box(s, 0.45, 1.4, 4.0, 2.55, fill=LIGHT)
    text(s, 0.65, 1.5, 3.65, 2.4, [
        ("The problem", 16, ORANGE, True),
        "Supervisors dig through three binders to fix floor problems.",
        "That costs time on the line.",
        "A fix done without the right safety step can hurt someone.",
        "Managers can't see which problems keep coming back."], size=12.5)

    text(s, 4.75, 1.4, 8.2, 0.4, [("How it works", 16, ORANGE, True)])
    steps = [("1  Ask", "Type a question in plain words, e.g. \"Conveyor C3 is jammed\".", NAVY),
             ("2  Plan", "A router agent understands the question and picks the right manuals.", BLUE),
             ("3  Research", "Expert agents search Safety, Maintenance and Quality at the same time.", GREEN),
             ("4  Answer", "One clear answer with steps and sources. Safety always comes first.", RED)]
    for i, (h, body, col) in enumerate(steps):
        x = 4.75 + i * 2.07
        box(s, x, 1.85, 1.95, 2.1, fill=WHITE, line=col)
        text(s, x + 0.1, 1.93, 1.75, 2.0, [(h, 16, col, True), (body, 13.5, GREY, False)])

    # Row 2: who | results | trust
    box(s, 0.45, 4.2, 4.0, 2.55, fill=LIGHT)
    text(s, 0.65, 4.3, 3.65, 2.4, [
        ("Who it helps", 16, ORANGE, True),
        ("Floor supervisors", 12.5, NAVY, True),
        ("Quick, trusted answers during the shift.", 12, GREY, False),
        ("Plant managers", 12.5, NAVY, True),
        ("Approve document updates, review flagged answers and see the top repeat problems (e.g. CNC-04 spindle alarms).", 12, GREY, False)])

    box(s, 4.75, 4.2, 4.1, 2.55, fill=LIGHT)
    text(s, 4.95, 4.3, 3.8, 0.4, [("Tests so far (rule-based version)", 16, ORANGE, True)])
    kpis = [(f"{res['routing_accuracy']:.0f}%", "routed to the right source"),
            (f"{res['safety_inclusion_recall']:.0f}%", "risky tasks showed the safety step"),
            (f"{res['abstain_correctness']:.0f}%", "said \"not found\" instead of guessing"),
            (f"{res['draft_leak_count']}", "unapproved drafts shown")]
    for i, (num, label) in enumerate(kpis):
        x, y = 4.95 + (i % 2) * 1.92, 4.8 + (i // 2) * 0.95
        text(s, x, y, 1.85, 0.9, [(num, 24, NAVY, True), (label, 10.5, GREY, False)])

    box(s, 9.15, 4.2, 3.75, 2.55, fill=LIGHT)
    text(s, 9.35, 4.3, 3.45, 2.4, [
        ("Built-in trust", 16, ORANGE, True),
        "Answers only from approved documents.",
        "Every claim must cite a source.",
        "Agents can read documents, never change them.",
        "Blocks requests to skip safety steps.",
        "Emergency? Shows \"call ext. 5555\" first.",
        "Every action is logged for audit."], size=12)

    # Footer
    text(s, 0.45, 6.88, 12.4, 0.5, [(
        f"Status: the rule-based version passed {res['passed']}/{res['total']} tests on a test (mock) model, so these numbers check the wiring only. "
        f"The AI agents are being built and will be re-tested with the live model  ·  next: real documents, sign-in",
        10.5, GREY, False)])

    out = ROOT / "docs" / "one_pager.pptx"
    tmp = out.with_name("_" + out.name)
    prs.save(tmp)
    tmp.replace(out)
    print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
