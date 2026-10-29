#!/usr/bin/env python3
"""Build the MUSD Proof deck for the AKINDO x Mezo Wave 2 submission.

Seven slides, all text editable, no network assets. Numbers come from RECEIPT.json.
"""
from __future__ import annotations

import json
import pathlib

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches, Pt

ROOT = pathlib.Path(r"C:\111\work\musd-proof")
rec = json.loads((ROOT / "RECEIPT.json").read_text(encoding="utf-8"))
i = rec["inputs"]

INK = RGBColor(0x11, 0x14, 0x18)
MUTED = RGBColor(0x5A, 0x62, 0x6B)
ACCENT = RGBColor(0x1F, 0x6F, 0xEB)
WARN = RGBColor(0xB4, 0x6A, 0x00)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def slide(title: str, kicker: str | None = None):
    s = prs.slides.add_slide(BLANK)
    if kicker:
        k = s.shapes.add_textbox(Inches(0.7), Inches(0.42), Inches(12), Inches(0.35))
        r = k.text_frame.paragraphs[0].add_run()
        r.text = kicker.upper()
        r.font.size = Pt(11)
        r.font.color.rgb = ACCENT
        r.font.bold = True
    t = s.shapes.add_textbox(Inches(0.7), Inches(0.78), Inches(12), Inches(0.9))
    run = t.text_frame.paragraphs[0].add_run()
    run.text = title
    run.font.size = Pt(30)
    run.font.bold = True
    run.font.color.rgb = INK
    return s


def bullets(s, items, top=1.95, size=17, width=12.0, height=2.4):
    box = s.shapes.add_textbox(Inches(0.7), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    for n, item in enumerate(items):
        p = tf.paragraphs[0] if n == 0 else tf.add_paragraph()
        p.space_after = Pt(10)
        r = p.add_run()
        r.text = item
        r.font.size = Pt(size)
        r.font.color.rgb = INK
    return box


def table(s, rows, top=1.95, widths=(5.6, 6.4), size=15):
    shape = s.shapes.add_table(len(rows), 2, Inches(0.7), Inches(top),
                               Inches(widths[0] + widths[1]), Inches(0.42 * len(rows)))
    tbl = shape.table
    tbl.columns[0].width = Inches(widths[0])
    tbl.columns[1].width = Inches(widths[1])
    for r, (a, b) in enumerate(rows):
        for c, val in enumerate((a, b)):
            cell = tbl.cell(r, c)
            cell.text = ""
            para = cell.text_frame.paragraphs[0]
            run = para.add_run()
            run.text = str(val)
            run.font.size = Pt(size)
            run.font.bold = c == 1
            run.font.color.rgb = INK if r else MUTED
    return shape


def note(s, text, top=6.55, color=MUTED, size=12):
    box = s.shapes.add_textbox(Inches(0.7), Inches(top), Inches(12), Inches(0.5))
    r = box.text_frame.paragraphs[0].add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.italic = True


# 1 -------------------------------------------------------------------------
s = slide("MUSD Proof", "AKINDO x Mezo — Wave 2 — Track 2")
bullets(s, [
    "One command reads MUSD on two chains, the protocol's own collateral and every pool that holds it.",
    "It prints the numbers, the block they came from, and a hash anyone can re-run.",
    "It says plainly what it could not verify.",
], top=2.0, size=20)
note(s, "Live: https://mak777uh.github.io/musd-proof/   ·   Code: github.com/mak777uh/musd-proof (MIT)")

# 2 -------------------------------------------------------------------------
s = slide("The problem: the promise is public, the proof is not", "Problem")
bullets(s, [
    "MUSD's core claim is that it is backed by Bitcoin. Today a third party cannot check that claim.",
    "The state is spread over two chains and six contracts; supply includes a protocol bootstrap loan "
    "that is not BTC in troves.",
    "Any answer from a party you cannot re-run is an opinion, and opinions do not survive diligence.",
], top=2.0, size=19)
note(s, "The question is not 'how much'. The question is 'out of what' — and nobody publishes a re-runnable answer.")

# 3 -------------------------------------------------------------------------
s = slide("What it reads, on one pinned block", "How it works")
table(s, [
    ("Source", "What it gives"),
    ("MUSD.totalSupply — Mezo + Ethereum", f"{i['musd_supply_mezo']:,.0f} / {i['musd_supply_ethereum']:,.0f}"),
    ("TroveManager.getEntireSystemColl", f"{i['system_collateral_btc']:,.6f} BTC"),
    ("PriceFeed.fetchPrice (the protocol's own)", f"${i['btc_price_usd']:,.0f}"),
    ("PCV.BOOTSTRAP_LOAN / debtToPay", f"{i['pcv_bootstrap_loan_musd']:,.0f} / {i['pcv_debt_to_pay_musd']:,.0f}"),
    ("Native balances of all six pools", f"{i['total_btc_in_protocol']:,.6f} BTC"),
], top=1.95)
note(s, "Every read uses one block number, recorded in the receipt. That is what makes the result reproducible.")

# 4 -------------------------------------------------------------------------
s = slide("What the numbers say — and what they do not", "Result")
table(s, [
    ("Measure", "Value"),
    ("Collateral / user debt", f"{i['user_collateral_ratio_total']:,.2f}x"),
    ("Collateral / total supply", f"{i['collateral_to_supply_ratio'] * 100:,.2f}%"),
    ("Verdict", rec["verdict"]),
], top=1.95)
bullets(s, [
    "The low supply ratio is explained, not hidden: 96% of the supply is the PCV bootstrap loan.",
    "User debt is over-collateralised by two orders of magnitude.",
    "The receipt carries a `not_verified` list — four items, written down rather than left implicit.",
], top=4.0, size=16)
note(s, "A tool that only reassures is marketing. This one prints the boundary next to the number.")

# 5 -------------------------------------------------------------------------
s = slide("Why it holds up: the receipt", "Verification")
bullets(s, [
    f"statement_sha256 = {rec['statement_sha256'][:32]}…",
    "Change any input and the hash changes — a claim cannot drift silently.",
    "verify_receipt.py re-reads the same blocks and prints the difference instead of hiding it.",
    "The toolchain, the command and the raw values are in the receipt, so a stranger can reproduce it.",
], top=1.95, size=17)
note(s, "Receipt: github.com/mak777uh/musd-proof/blob/main/RECEIPT.json")

# 6 -------------------------------------------------------------------------
s = slide("Who it is for", "Audience")
table(s, [
    ("Audience", "What they get"),
    ("MUSD holders and Curve LPs", "an answer to 'what backs this' they can check themselves"),
    ("The Mezo team and its investors", "a diligence artefact that is not a screenshot"),
    ("New protocols on Mezo", "a template for publishing reserves the same way"),
], top=1.95)
note(s, "Desktop, CLI, no account, no wallet, no API key.")

# 7 -------------------------------------------------------------------------
s = slide("Next three milestones", "Roadmap")
bullets(s, [
    "1. Public attestation page with history by block (2 weeks after the wave).",
    "2. Curve metapool composition on Ethereum: depth, spread, LP mix (3 weeks).",
    "3. Pluggable config — any protocol declares what counts as its reserve (2 months).",
    "",
    "What this is not: it does not verify deployed bytecode, and it does not replace an audit.",
], top=1.95, size=18)
note(s, "Built solo. Prior work: verified-cells-cairo (6 invariant cells with receipts), rocketpool-invariants, flowguard-spec.")

out = ROOT / "MUSD-Proof-deck.pptx"
prs.save(out)
print(f"deck: {out} · slides: {len(prs.slides)}")
