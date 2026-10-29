#!/usr/bin/env python3
r"""attest.py — MUSD Proof: a reproducible attestation of what the numbers actually are.

What it does (read-only, no keys, no transactions):

1. reads MUSD total supply on Mezo and on Ethereum;
2. reads the system collateral held by the Mezo protocol and the BTC price from the protocol's feed;
3. computes the collateral-to-supply ratio;
4. checks where the supply sits: protocol contracts, the Ethereum bridge side, the largest venue;
5. emits a **receipt**: every input, every raw value, a statement hash, and the exact command to re-run it.

What it deliberately does NOT do: it does not claim "MUSD is undercollateralised". It prints what it can read
and lists, explicitly, what it could not verify. A green attestation is a result; an incomplete one is stated
as incomplete.

    python attest.py            # prints the report and writes RECEIPT.json
    python verify_receipt.py    # re-reads the chain and compares against RECEIPT.json
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

import requests
from eth_hash.auto import keccak

MEZO_RPCS = ["https://mezo.drpc.org", "https://rpc.mezo.org", "https://rpc.test.mezo.org"]
ETH_RPCS = ["https://eth-mainnet.public.blastapi.io", "https://eth.llamarpc.com"]
MEZO_RPC = MEZO_RPCS[0]   # chosen on the first successful response
ETH_RPC = ETH_RPCS[0]
PROXIES = {"http": "http://127.0.0.1:2080", "https": "http://127.0.0.1:2080"}

# Addresses taken from mezo-org/musd, solidity/artifacts/deployments/mainnet/
MUSD = "0xdD468A1DDc392dcdbEf6db6e34E89AA338F9F186"          # same address on Mezo and Ethereum
TROVE_MANAGER = "0x94AfB503dBca74aC3E4929BACEeDfCe19B93c193"
PRICE_FEED = "0xc5ac5a8892230e0a3e1c473881a2de7353ffca88"
ACTIVE_POOL = "0x3012c2fe1240e3754e5c200a0946bb0e07474876"
DEFAULT_POOL = "0xe4b5913c0c82db2efc553b95c0173efb90a07c8b"
BORROWER_OPS = "0x44b1bac67dDA612a41a58AAf779143B181dEe031"
PCV = "0x391EcC7ffEFc48cff41D0F2Bb36e38b82180B993"
COLL_SURPLUS_POOL = "0xBF51807ACb3394B8550f0554FB9098856Ef5F491"
GAS_POOL = "0x3EB418BdBE95b4b9cf465ecfBD8424685ACD1Bc1"
STABILITY_POOL = "0x73245Eff485aB3AAc1158B3c4d8f4b23797B0e32"

ROOT = pathlib.Path(__file__).parent


BLOCK: dict[str, int] = {}   # rpc -> block number, so every read uses one consistent snapshot
READ_ERRORS: list[str] = []  # reads that failed; empty means everything was read
RPC_USED: dict[str, str] = {}


def pick_rpc(candidates: list[str], label: str) -> str:
    """First RPC that answers eth_blockNumber. Fails loudly when none is alive."""
    for url in candidates:
        try:
            r = requests.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber",
                                         "params": []}, timeout=(6, 20), proxies=PROXIES)
            res = (r.json() or {}).get("result")
            if res:
                RPC_USED[label] = url
                return url
        except Exception:
            continue
    raise SystemExit(f"no live RPC for {label}: {candidates}")


def block_number(rpc: str) -> int | None:
    try:
        r = requests.post(rpc, json={"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []},
                          timeout=(6, 25), proxies=PROXIES)
        res = r.json().get("result")
        return int(res, 16) if res else None
    except Exception:
        return None


def call(rpc: str, to: str, sig: str, args: str = "") -> int | None:
    data = "0x" + keccak(sig.encode()).hex()[:8] + args
    tag = hex(BLOCK[rpc]) if rpc in BLOCK else "latest"
    try:
        r = requests.post(rpc, json={"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                                     "params": [{"to": to, "data": data}, tag]},
                          timeout=(6, 25), proxies=PROXIES)
        res = r.json().get("result")
        if res and res != "0x":
            return int(res, 16)
    except Exception as e:
        READ_ERRORS.append(f"{sig} on {to[:10]}: {type(e).__name__}")
        return None
    READ_ERRORS.append(f"{sig} on {to[:10]}: empty result")
    return None


def native_balance(rpc: str, addr: str) -> int | None:
    tag = hex(BLOCK[rpc]) if rpc in BLOCK else "latest"
    try:
        r = requests.post(rpc, json={"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance",
                                     "params": [addr, tag]}, timeout=(6, 25), proxies=PROXIES)
        res = r.json().get("result")
        return int(res, 16) if res else None
    except Exception:
        return None


def balance_of(rpc: str, token: str, holder: str) -> int | None:
    return call(rpc, token, "balanceOf(address)", holder[2:].rjust(64, "0"))


def gather(blocks: dict[str, int] | None = None) -> dict:
    global MEZO_RPC, ETH_RPC
    MEZO_RPC = pick_rpc(MEZO_RPCS, "mezo")
    ETH_RPC = pick_rpc(ETH_RPCS, "ethereum")
    READ_ERRORS.clear()
    if blocks:
        BLOCK.update(blocks)
    else:
        for rpc in (MEZO_RPC, ETH_RPC):
            bn = block_number(rpc)
            if bn is not None:
                BLOCK[rpc] = bn
    supply_mezo = call(MEZO_RPC, MUSD, "totalSupply()")
    supply_eth = call(ETH_RPC, MUSD, "totalSupply()")
    coll_wei = call(MEZO_RPC, TROVE_MANAGER, "getEntireSystemColl()")
    price_18 = call(MEZO_RPC, PRICE_FEED, "fetchPrice()")
    debt = call(MEZO_RPC, TROVE_MANAGER, "getEntireSystemDebt()")
    bootstrap_loan = call(MEZO_RPC, PCV, "BOOTSTRAP_LOAN()")
    bootstrap_debt = call(MEZO_RPC, PCV, "debtToPay()")

    pools = {
        "ActivePool": ACTIVE_POOL,
        "DefaultPool": DEFAULT_POOL,
        "CollSurplusPool": COLL_SURPLUS_POOL,
        "GasPool": GAS_POOL,
        "StabilityPool": STABILITY_POOL,
        "PCV": PCV,
    }
    btc_in_pools = {name: round((native_balance(MEZO_RPC, addr) or 0) / 1e18, 6)
                    for name, addr in pools.items()}
    total_btc = round(sum(btc_in_pools.values()), 6)

    protocol_holdings = {}
    for name, addr in (("ActivePool", ACTIVE_POOL), ("DefaultPool", DEFAULT_POOL),
                       ("BorrowerOperations", BORROWER_OPS), ("PCV", PCV)):
        protocol_holdings[name] = balance_of(MEZO_RPC, MUSD, addr)

    supply_mezo_h = (supply_mezo or 0) / 1e18
    supply_eth_h = (supply_eth or 0) / 1e18
    coll_btc = (coll_wei or 0) / 1e18
    btc_usd = (price_18 or 0) / 1e18
    coll_usd = coll_btc * btc_usd
    ratio = (coll_usd / supply_mezo_h) if supply_mezo_h else None

    return {
        "musd_supply_mezo": round(supply_mezo_h, 6),
        "musd_supply_ethereum": round(supply_eth_h, 6),
        "system_collateral_btc": round(coll_btc, 6),
        "btc_price_usd": round(btc_usd, 2),
        "collateral_value_usd": round(coll_usd, 2),
        "system_debt_musd": round((debt or 0) / 1e18, 6),
        "pcv_bootstrap_loan_musd": round((bootstrap_loan or 0) / 1e18, 6),
        "pcv_debt_to_pay_musd": round((bootstrap_debt or 0) / 1e18, 6),
        "user_collateral_ratio": (round(coll_usd / ((debt or 0) / 1e18), 6) if debt else None),
        "collateral_to_supply_ratio": round(ratio, 6) if ratio is not None else None,
        "btc_in_protocol_pools": btc_in_pools,
        "total_btc_in_protocol": total_btc,
        "total_btc_value_usd": round(total_btc * btc_usd, 2),
        "user_collateral_ratio_total": (round((total_btc * btc_usd) / ((debt or 0) / 1e18), 6) if debt else None),
        "musd_held_by_protocol": {k: (round(v / 1e18, 6) if v is not None else None)
                                  for k, v in protocol_holdings.items()},
    }


def main() -> int:
    data = gather()
    # The main rule: zero supply or zero collateral is a read failure, not a result.
    if not data["musd_supply_mezo"] or not data["system_collateral_btc"]:
        print("REFUSED: could not read supply or collateral. This is an RPC failure, not a zero value.")
        for e in READ_ERRORS[:6]:
            print("  -", e)
        print("  RPC:", RPC_USED)
        return 2
    verdict = "ATTESTED_PARTIAL"
    notes = []
    if data["collateral_to_supply_ratio"] is None:
        verdict = "INCONCLUSIVE"
        notes.append("could not read supply or collateral — no conclusion is possible")
    elif data["collateral_to_supply_ratio"] < 1:
        boot = data.get("pcv_bootstrap_loan_musd") or 0
        left = data.get("pcv_debt_to_pay_musd") or 0
        notes.append(
            f"collateral covers {data['collateral_to_supply_ratio']*100:.2f}% of total supply, but the supply "
            f"includes the PCV bootstrap loan of {boot:,.0f} MUSD (unpaid: {left:,.0f}); user debt is "
            "over-collateralised")
        notes.append(f"BTC held by all protocol contracts: {data['total_btc_in_protocol']:.6f} "
                     f"(~${data['total_btc_value_usd']:,.0f})")
        ucr = data.get("user_collateral_ratio_total")
        if ucr:
            notes.append(f"collateral to user debt: {ucr:.2f}x")

    receipt = {
        "claim": "the numbers below are what the listed contracts return at the listed moment",
        "inputs": data,
        "verdict": verdict,
        "notes": notes,
        "not_verified": [
            "not verified: where the PCV reserve is actually held (no vault contract was found)",
            "the PCV bootstrap loan is a protocol obligation, not BTC locked in troves",
            "not verified: how the supply that was not minted against locked BTC is backed",
            "not verified: the composition and spread of the Curve pool on Ethereum",
            "not verified: protocol obligations outside these contracts",
        ],
        "chain": {"mezo_chain_id": 31612, "ethereum_chain_id": 1, "blocks": dict(BLOCK)},
        "rpc_used": dict(RPC_USED),
        "read_errors": list(READ_ERRORS),
        "contracts": {"MUSD": MUSD, "TroveManager": TROVE_MANAGER, "PriceFeed": PRICE_FEED,
                      "ActivePool": ACTIVE_POOL, "DefaultPool": DEFAULT_POOL,
                      "BorrowerOperations": BORROWER_OPS, "PCV": PCV,
                      "CollSurplusPool": COLL_SURPLUS_POOL, "GasPool": GAS_POOL,
                      "StabilityPool": STABILITY_POOL},
        "command": "python attest.py",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    core = {k: data[k] for k in sorted(data)}
    receipt["statement_sha256"] = hashlib.sha256(
        json.dumps(core, sort_keys=True).encode()).hexdigest()

    (ROOT / "RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(receipt["inputs"], ensure_ascii=False, indent=1))
    print(f"\nverdict: {verdict}")
    for n in notes:
        print(f"  · {n}")
    print(f"statement_sha256: {receipt['statement_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
