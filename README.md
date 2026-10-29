# MUSD Proof

A reproducible attestation of what the MUSD numbers actually are — **not** a claim that they are good or bad.

Anyone can run one command and see the same numbers, then check them against the receipt.

## What it reads (read-only, no keys)

| what | where |
|---|---|
MUSD total supply | Mezo mainnet (31612) and Ethereum (1), same token address |
system collateral | `TroveManager.getEntireSystemColl()` on Mezo |
BTC price | the protocol's own `PriceFeed.fetchPrice()` |
system debt | `TroveManager.getEntireSystemDebt()` |
where the supply sits | `balanceOf` of ActivePool, DefaultPool, BorrowerOperations, PCV |

Addresses are taken from `mezo-org/musd` → `solidity/artifacts/deployments/mainnet/`.

## Run

```bash
python attest.py            # prints the report, writes RECEIPT.json
python verify_receipt.py    # re-reads the chain, compares, prints the statement hash
```

Requires `requests` and `eth_hash`. No API key, no account, no wallet.

## What a receipt contains

- every raw input, as read at a timestamp;
- the derived ratio, computed in one place so it cannot drift;
- `statement_sha256` over the inputs, so a changed number changes the hash;
- an explicit **`not_verified`** list.

## What this does not claim

> A ratio below 1 is **not** proof of under-collateralisation. It means the contracts listed here hold less
> collateral than the token supply, and that the reserve — if it exists elsewhere — was not found. The tool
> says exactly that, in the receipt, instead of implying a verdict.

That is the point: a claim a reviewer can re-run, with its own limits printed next to it.

## Why it exists

MUSD's core promise is that it is backed by Bitcoin. Today a third party cannot check that promise with one
command, and the numbers are spread across two chains and several contracts. This tool makes the state
reproducible: same inputs, same hash, same conclusion — or an honest "inconclusive".

## Deck and pitch

| file | what |
|---|---|
| `media/MUSD-Proof-deck.pptx` | 7 slides, every number pulled from `RECEIPT.json` |
| `media/MUSD-Proof-full.mp4` | **the pitch (115 s)**: the real run first (16 s), then the story |
| `media/MUSD-Proof-pitch.mp4` | the slides alone (118 s) |
| `media/MUSD-Proof-terminal.mp4` | the real run alone (16 s) |

Both are regenerated from the receipt by `build_deck.py` and `build_video.py`, so a changed number changes the
slides — the deck cannot drift away from the data.
