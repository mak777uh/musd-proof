#!/usr/bin/env python3
"""Build the terminal demo: the real run of attest.py and verify_receipt.py, recorded as frames.

No slides, no claims: the viewer sees the tool's own output, line by line, and the verifier confirming the hash.

Output: C:\\111\\work\\musd-proof\\MUSD-Proof-terminal.mp4
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(r"C:\111\work\musd-proof")
BUILD = ROOT / "_term"
BUILD.mkdir(exist_ok=True)
W, H = 1920, 1080
BG = (14, 17, 22)
FG = (222, 228, 236)
DIM = (128, 138, 150)
GREEN = (86, 200, 120)
ACCENT = (90, 160, 255)
RED = (232, 110, 110)

FFMPEG = (r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget."
          r"Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.exe")
FONT = r"C:\Windows\Fonts\consola.ttf"
PY = r"C:\111\env\python\.venv\Scripts\python.exe"

LINE_H = 34
TOP = 190
LEFT = 130
MAX_LINES = 22


def run(cmd: list[str]) -> list[str]:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(ROOT))
    out = (r.stdout or "") + (r.stderr or "")
    return [ln.rstrip() for ln in out.splitlines()], r.returncode


def draw_frame(visible: list[str], caption: str, prompt: str, idx: int) -> pathlib.Path:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 26)
    f_small = ImageFont.truetype(FONT, 22)
    f_cap = ImageFont.truetype(FONT, 28)

    # окно терминала
    d.rounded_rectangle([LEFT - 40, TOP - 130, W - LEFT + 40, H - 90], radius=18, outline=(44, 52, 64), width=2)
    for k, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse([LEFT - 14 + k * 30, TOP - 112, LEFT + 4 + k * 30, TOP - 94], fill=c)

    d.text((LEFT + 120, TOP - 118), "musd-proof — powershell", font=f_small, fill=DIM)

    y = TOP
    for line in visible[-MAX_LINES:]:
        color = FG
        low = line.lower()
        if "refused" in low or "error" in low or "mismatch" in low:
            color = RED
        elif "matches" in low or "pass" in low or '"verdict"' in low:
            color = GREEN
        elif line.strip().startswith('"') and ":" in line:
            color = FG
        elif "python" in low or "$ " in line:
            color = ACCENT
        d.text((LEFT, y), line[:120], font=f, fill=color)
        y += LINE_H

    if prompt:
        d.text((LEFT, y), prompt + "▌", font=f, fill=ACCENT)

    d.text((LEFT - 40, H - 66), caption, font=f_cap, fill=DIM)
    d.text((W - 260, H - 66), f"{idx}", font=f_small, fill=DIM)
    out = BUILD / f"t{idx:03d}.png"
    img.save(out)
    return out


def build_segment(lines: list[str], caption: str, per_line: float, idx_start: int) -> tuple[pathlib.Path, int]:
    frames = []
    idx = idx_start
    for n in range(1, len(lines) + 1):
        frames.append(draw_frame(lines[:n], caption, "", idx))
        idx += 1
    # последний кадр держим дольше
    hold = draw_frame(lines, caption, "", idx)
    idx += 1
    frames.append(hold)

    listing = BUILD / f"seg{idx_start}.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\nduration {per_line}\n" for p in frames)
                       + f"file '{hold.as_posix()}'\nduration 2.5\n", encoding="utf-8")
    seg = BUILD / f"seg{idx_start}.mp4"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-fps_mode", "vfr", "-pix_fmt", "yuv420p", "-c:v", "libx264", str(seg)],
                   check=True, capture_output=True, timeout=600)
    return seg, idx


def tts(text: str, out: pathlib.Path) -> float:
    ps = f'''
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice("Microsoft David Desktop")
$s.Rate = 1
$s.SetOutputToWaveFile("{out}")
$s.Speak(@"
{text}
"@)
$s.Dispose()
'''
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, timeout=180)
    fp = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")
    d = subprocess.run([fp, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                       capture_output=True, text=True, timeout=60).stdout.strip()
    return float(d or 0)


def main() -> int:
    print("  запускаю attest.py ...")
    att, rc1 = run([PY, "attest.py"])
    print("  запускаю verify_receipt.py ...")
    ver, rc2 = run([PY, "verify_receipt.py"])
    print(f"  attest exit={rc1} ({len(att)} строк), verify exit={rc2} ({len(ver)} строк)")

    voice = BUILD / "voice.wav"
    dur = tts("This is not a slide. This is the tool running. One command reads the supply, the collateral and "
              "every pool that holds Bitcoin, on a pinned block. Then the verifier re-reads the same blocks and "
              "compares. The hash matches. What it could not verify is printed next to the number.", voice)
    print(f"  голос: {dur:.1f} с")
    total_lines = len(att) + len(ver)
    per = max(0.12, (dur - 2.5) / total_lines)
    print(f"  строк {total_lines} → {per:.2f} с на строку")
    seg1, idx = build_segment(att, "1/2  python attest.py — one command, one receipt", per, 1)
    seg2, idx = build_segment(ver, "2/2  python verify_receipt.py — the same blocks, compared", per, idx)

    out = ROOT / "MUSD-Proof-terminal.mp4"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(seg1), "-i", str(seg2), "-i", str(voice),
                    "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
                    "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)],
                   check=True, capture_output=True, timeout=900)
    print(f"  видео: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
