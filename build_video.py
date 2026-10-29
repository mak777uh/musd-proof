#!/usr/bin/env python3
"""Build the 2-minute MUSD Proof pitch: PIL frames + Windows TTS + ffmpeg.

Output: C:\\111\\work\\musd-proof\\MUSD-Proof-pitch.mp4 (1920x1080, H.264 + AAC).

Everything is generated locally: no network, no cloud TTS, no stock footage.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(r"C:\111\work\musd-proof")
BUILD = ROOT / "_video"
BUILD.mkdir(exist_ok=True)
W, H = 1920, 1080
INK = (17, 20, 24)
MUTED = (90, 98, 107)
ACCENT = (31, 111, 235)
LINE = (214, 219, 226)

FFMPEG = r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.exe"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"

rec = json.loads((ROOT / "RECEIPT.json").read_text(encoding="utf-8"))
i = rec["inputs"]

SLIDES = [
    {
        "kicker": "AKINDO x MEZO — WAVE 2 — TRACK 2",
        "title": "MUSD Proof",
        "lines": [
            "One command reads what the protocol actually holds.",
            "It prints the numbers, the block they came from,",
            "and a hash anyone can re-run.",
        ],
        "foot": "mak777uh.github.io/musd-proof",
        "speech": (
            "MUSD Proof. A stablecoin's promise is that it is backed. This tool makes that promise "
            "checkable. One command, one receipt, no account."
        ),
    },
    {
        "kicker": "THE PROBLEM",
        "title": "The promise is public. The proof is not.",
        "lines": [
            "MUSD says it is backed by Bitcoin.",
            "The state is spread over two chains and six contracts.",
            "Part of the supply is a protocol bootstrap loan —",
            "not Bitcoin locked in troves.",
            "",
            "Anyone can give you an answer. Nobody gives you one you can re-run.",
        ],
        "foot": "",
        "speech": (
            "Here is the problem. MUSD says it is backed by Bitcoin. But the state is spread across two "
            "chains and six contracts, and part of the supply is a protocol bootstrap loan that is not "
            "Bitcoin in troves. Anyone can give you an answer. Nobody can give you one you can re-run."
        ),
    },
    {
        "kicker": "HOW IT WORKS",
        "title": "One pinned block, six reads",
        "table": [
            ("MUSD total supply — Mezo", f"{i['musd_supply_mezo']:,.0f}"),
            ("MUSD total supply — Ethereum", f"{i['musd_supply_ethereum']:,.0f}"),
            ("System collateral (TroveManager)", f"{i['system_collateral_btc']:,.6f} BTC"),
            ("BTC price (protocol's own feed)", f"${i['btc_price_usd']:,.0f}"),
            ("PCV bootstrap loan / unpaid", f"{i['pcv_bootstrap_loan_musd']:,.0f} / {i['pcv_debt_to_pay_musd']:,.0f}"),
            ("BTC in all six protocol pools", f"{i['total_btc_in_protocol']:,.6f} BTC"),
        ],
        "foot": "Every read uses the same block number, recorded in the receipt.",
        "speech": (
            "So the tool pins a block and reads six things at that block: total supply on Mezo and on "
            "Ethereum, the system collateral, the protocol's own price feed, the bootstrap loan and what "
            "is left of it, and the native balance of every pool that holds Bitcoin."
        ),
    },
    {
        "kicker": "RESULT",
        "title": "What the numbers say — and what they do not",
        "table": [
            ("Collateral / user debt", f"{i['user_collateral_ratio_total']:,.2f}x"),
            ("Collateral / total supply", f"{i['collateral_to_supply_ratio'] * 100:,.2f}%"),
            ("Verdict", rec["verdict"]),
        ],
        "lines": [
            "",
            "The low ratio is explained, not hidden:",
            "96% of supply is the bootstrap loan.",
            "User debt is over-collateralised by two orders of magnitude.",
        ],
        "foot": "A tool that only reassures is marketing. This one prints its boundary.",
        "speech": (
            "The numbers: twenty-nine point five million MUSD in supply, seven hundred forty-four thousand "
            "on Ethereum, twenty-one point seven Bitcoin across all protocol contracts, and a hundred and "
            "one times coverage of user debt. Against total supply the ratio is four point five percent, "
            "and the receipt explains why: ninety-six percent of supply is the bootstrap loan."
        ),
    },
    {
        "kicker": "VERIFICATION",
        "title": "The receipt is what makes it a result",
        "lines": [
            "statement_sha256",
            rec["statement_sha256"][:32],
            rec["statement_sha256"][32:],
            "",
            "Change any input and the hash changes.",
            "verify_receipt.py re-reads the same blocks",
            "and prints the difference instead of hiding it.",
        ],
        "mono_lines": [1, 2],
        "foot": "github.com/mak777uh/musd-proof",
        "speech": (
            "What makes it a result and not an opinion is the receipt. Every input, the block, the command, "
            "and a statement hash. Change any number and the hash changes. A verifier re-reads the same "
            "block and prints the difference instead of hiding it."
        ),
    },
    {
        "kicker": "AUDIENCE",
        "title": "Who it is for",
        "lines": [
            "Holders and Curve LPs — what backs this, checkable themselves.",
            "The Mezo team and its investors — a diligence artefact,",
            "not a screenshot.",
            "New protocols on Mezo — a template for publishing reserves",
            "the same way.",
        ],
        "foot": "Desktop, CLI, no account, no wallet, no API key.",
        "speech": (
            "It is for three audiences: holders who want to know what backs their MUSD, the Mezo team and "
            "its investors who need a diligence artefact, and new protocols that want a template for "
            "publishing reserves."
        ),
    },
    {
        "kicker": "NEXT",
        "title": "Three milestones, and one honest boundary",
        "lines": [
            "1. Public attestation page with history by block.",
            "2. Curve metapool composition: depth, spread, LP mix.",
            "3. Pluggable config — any protocol declares its reserve.",
            "",
            "What this is not: it does not verify deployed bytecode,",
            "and it does not replace an audit.",
        ],
        "foot": "Built solo. Prior work: verified-cells-cairo, rocketpool-invariants, flowguard-spec.",
        "speech": (
            "Next: a public page with history by block, the composition of the Curve metapool, and a "
            "pluggable config so any protocol can declare its own reserve. What it is not: it does not "
            "verify bytecode, and it does not replace an audit."
        ),
    },
]


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        probe = (cur + " " + w).strip()
        if draw.textlength(probe, font=fnt) <= max_w:
            cur = probe
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def frame(spec: dict, n: int) -> pathlib.Path:
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_kick = font(FONT_BOLD, 24)
    f_title = font(FONT_BOLD, 68)
    f_body = font(FONT_REG, 34)
    f_mono = font(FONT_MONO, 30)
    f_foot = font(FONT_REG, 26)

    d.text((110, 92), spec["kicker"], font=f_kick, fill=ACCENT)
    y = 140
    for line in wrap(d, spec["title"], f_title, W - 220):
        d.text((110, y), line, font=f_title, fill=INK)
        y += 82
    y += 34
    d.line([(110, y), (W - 110, y)], fill=LINE, width=2)
    y += 44

    if spec.get("table"):
        col2 = W - 220
        for a, b in spec["table"]:
            d.text((110, y), a, font=f_body, fill=MUTED)
            tw = d.textlength(str(b), font=f_body)
            d.text((col2 - tw, y), str(b), font=f_body, fill=INK)
            y += 54
        y += 10

    for k, line in enumerate(spec.get("lines", [])):
        if not line:
            y += 18
            continue
        fnt = f_mono if k in spec.get("mono_lines", []) else f_body
        color = ACCENT if k in spec.get("mono_lines", []) else INK
        for part in wrap(d, line, fnt, W - 220):
            d.text((110, y), part, font=fnt, fill=color)
            y += 46

    if spec.get("foot"):
        d.text((110, H - 96), spec["foot"], font=f_foot, fill=MUTED)

    d.text((W - 110 - d.textlength(f"{n}/{len(SLIDES)}", font=f_foot), H - 96),
           f"{n}/{len(SLIDES)}", font=f_foot, fill=MUTED)
    out = BUILD / f"frame{n}.png"
    img.save(out)
    return out


def tts(text: str, out: pathlib.Path) -> float:
    ps = f'''
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice("Microsoft David Desktop")
$s.Rate = 0
$s.SetOutputToWaveFile("{out}")
$s.Speak(@"
{text}
"@)
$s.Dispose()
'''
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, timeout=180)
    dur = subprocess.run([FFMPEG.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", str(out)],
                         capture_output=True, text=True, timeout=60).stdout.strip()
    return float(dur or 0)


def main() -> int:
    segments = []
    total = 0.0
    for n, spec in enumerate(SLIDES, 1):
        png = frame(spec, n)
        wav = BUILD / f"voice{n}.wav"
        dur = tts(spec["speech"], wav)
        total += dur + 0.6
        print(f"  slide {n}: frame + voice {dur:.2f} s")
        segments.append((png, wav, dur))

    # each segment: the frame held for the whole track plus a 0.6 s pause
    parts = []
    for n, (png, wav, dur) in enumerate(segments, 1):
        seg = BUILD / f"seg{n}.mp4"
        subprocess.run([
            FFMPEG, "-y", "-loop", "1", "-i", str(png), "-i", str(wav),
            "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-shortest", "-t", f"{dur + 0.6:.2f}", str(seg),
        ], check=True, capture_output=True, timeout=300)
        parts.append(seg)

    listing = BUILD / "list.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    out = ROOT / "MUSD-Proof-pitch.mp4"
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", str(out)], check=True, capture_output=True, timeout=300)
    print(f"video: {out} · expected duration ~{total:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
