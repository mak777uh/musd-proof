#!/usr/bin/env python3
r"""make_page.py — собрать статическую страницу-демо из RECEIPT.json.

Страница не «рассказывает», а показывает: те же числа, что в квитанции, и команду, которой их можно
перепроверить. Никакой аналитики, никаких куки.

    python make_page.py   # -> docs/index.html
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).parent
rec = json.loads((ROOT / "RECEIPT.json").read_text(encoding="utf-8"))
i = rec["inputs"]


def fmt(v, suffix=""):
    if isinstance(v, float):
        return f"{v:,.6f}".rstrip("0").rstrip(".") + suffix
    return f"{v}{suffix}"


rows = [
    ("MUSD supply on Mezo", fmt(i["musd_supply_mezo"])),
    ("MUSD supply on Ethereum", fmt(i["musd_supply_ethereum"])),
    ("BTC held by protocol pools", fmt(i["total_btc_in_protocol"]) + " BTC"),
    ("BTC price (protocol feed)", "$" + fmt(i["btc_price_usd"])),
    ("Collateral value", "$" + fmt(i["total_btc_value_usd"])),
    ("User debt (troves)", fmt(i["system_debt_musd"]) + " MUSD"),
    ("Collateral / user debt", fmt(i["user_collateral_ratio_total"]) + "x"),
    ("Collateral / total supply", fmt(i["collateral_to_supply_ratio"] * 100) + "%"),
    ("PCV bootstrap loan", fmt(i["pcv_bootstrap_loan_musd"]) + " MUSD"),
    ("of which unpaid", fmt(i["pcv_debt_to_pay_musd"]) + " MUSD"),
]
pool_rows = [(k, fmt(v) + " BTC") for k, v in i["btc_in_protocol_pools"].items()]
not_verified = "".join(f"<li>{n}</li>" for n in rec["not_verified"])
blocks = rec["chain"].get("blocks", {})
block_txt = ", ".join(f"chain {k.split('//')[-1][:24]}: block {v}" for k, v in blocks.items())

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MUSD Proof — reproducible attestation</title>
<style>
 body{{font:16px/1.6 -apple-system,Segoe UI,Roboto,sans-serif;max-width:46rem;margin:0 auto;padding:2.5rem 1.25rem 4rem}}
 h1{{font-size:1.7rem;margin:0 0 .3rem}} .sub{{color:#666;margin:0 0 2rem}}
 table{{border-collapse:collapse;width:100%;margin:.5rem 0 1.5rem;font-size:.95rem}}
 th,td{{text-align:left;padding:.45rem .6rem;border-bottom:1px solid #8883}}
 td:last-child{{text-align:right;font-variant-numeric:tabular-nums}}
 code{{font-family:ui-monospace,Consolas,monospace;font-size:.9em;word-break:break-all}}
 .verdict{{display:inline-block;padding:.25rem .6rem;border-radius:.4rem;background:#f5c54233;border:1px solid #f5c54266}}
 ul{{padding-left:1.1rem}} footer{{margin-top:2.5rem;color:#666;font-size:.9rem}}
</style></head><body>
<h1>MUSD Proof</h1>
<p class="sub">What the MUSD contracts actually return — and the command to check it yourself.</p>

<p>Verdict: <span class="verdict">{rec['verdict']}</span></p>
<p><small>Pinned state: {block_txt}</small></p>

<h2>Numbers</h2>
<table>
{''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in rows)}
</table>

<h2>BTC by pool</h2>
<table>
{''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in pool_rows)}
</table>

<h2>Statement hash</h2>
<p><code>{rec['statement_sha256']}</code></p>
<p>Change any number above and this hash changes. <code>python verify_receipt.py</code> re-reads the same
blocks and prints the difference instead of hiding it.</p>

<h2>What this does not claim</h2>
<ul>{not_verified}</ul>

<h2>Run it</h2>
<pre><code>git clone https://github.com/mak777uh/musd-proof
cd musd-proof
python attest.py
python verify_receipt.py</code></pre>

<footer>No cookies, no analytics. Generated {rec['generated_utc']} from RECEIPT.json.</footer>
</body></html>
"""
(ROOT / "docs" / "index.html").write_text(html, encoding="utf-8")
print("страница собрана: docs/index.html")
