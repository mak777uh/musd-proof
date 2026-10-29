#!/usr/bin/env python3
r"""verify_receipt.py — перечитать цепь и сравнить с квитанцией.

Если числа разошлись — скрипт печатает, какие именно. Если совпали — печатает statement_sha256,
который должен совпасть с записанным.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import attest

ROOT = pathlib.Path(__file__).parent


def main() -> int:
    rec = json.loads((ROOT / "RECEIPT.json").read_text(encoding="utf-8"))
    now = attest.gather(blocks=(rec.get('chain') or {}).get('blocks'))
    ok = True
    for k in sorted(now):
        was, cur = rec["inputs"].get(k), now[k]
        if isinstance(was, (int, float)) and isinstance(cur, (int, float)):
            if was and abs(was - cur) / max(abs(was), 1) < 1e-6:
                print(f"OK       {k}: {cur}")
            elif was == cur:
                print(f"OK       {k}: {cur}")
            else:
                print(f"CHANGED  {k}: был {was} → сейчас {cur}")
                ok = False
        else:
            same = was == cur
            print(f"{'OK      ' if same else 'CHANGED '} {k}: {cur}")
            ok = False if not same else ok
    core = {k: now[k] for k in sorted(now)}
    h = hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()
    print(f"statement_sha256: {'совпал' if h == rec['statement_sha256'] else 'НЕ СОВПАЛ'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
