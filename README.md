# Taobao Sourcing Assistant

A **local, human-paced MCP server** that removes the drudgery of sourcing products
on Taobao/Tmall. You keep all judgment (search intuition, buy decisions, sending
supplier messages); the tool drives a real Chrome window to extract — for every
product — **a price for every SKU variant**, specs, images, and **reviews linked to
the variant bought**, then tabulates it into a comparison spreadsheet. Ships with a
Claude **Skill** (sourcing playbook) and **Chinese supplier-message templates**
(drafted by Claude, sent manually by you).

> Built on the QR-login + persistent-session approach of `JeremyDong22/taobao_mcp`,
> rebuilt as **10 FastMCP tools** with embedded-data + DOM extraction (mtop interception
> kept as a fallback): search, per-SKU pricing, variant-linked reviews, xlsx export,
> **gated cart staging** (adds via the `mtop.trade.addBag` API — works on Taobao *and*
> Tmall), **confirm-then-send seller messaging**, and a **daily order-tracking + 取件码
> pickup-code digest** — plus a captcha human-handoff and anti-detection pacing.

## Scope — it does four things
**Find** legitimate products · **add to cart** · **communicate with sellers** (you confirm
each message) · **track orders** (+ 取件码 pickup codes). You + your buying agent handle
**payment, the delivery address, checkout, and all logistics** — the tool hands off at the
cart and the tracking digest.

## What it does NOT do
No headless scraping, no proxy rotation, no captcha-solving service, no cloud. It **never
pays, checks out, or picks a shipping address**, and it **never blind-sends** a seller
message (confirm-then-send — you approve each one). **Not getting your account flagged is
the priority, not speed.**

---

## Install (one time)

```bash
# from the project root
uv venv --python 3.12
uv pip install -e ".[dev]"
```

You need **Google Chrome** installed (the real app, not Chromium, not Comet). The
launcher is pinned to it in `config.toml`. If Chrome lives somewhere non-standard,
edit `[browser] executable_path`, or clear it ("") to let Playwright resolve the
`chrome` channel.

## Configure

Edit `config.toml` (defaults are sensible):
- `[browser] executable_path` — pinned Google Chrome binary (avoids launching Comet/other Chromium).
- `[browser] user_data_dir` — the persistent profile (your login lives here; gitignored).
- `[pacing]` — random delays + `max_products_per_minute` (keep it low).
- `[limits]` — `max_reviews`, `review_pages`.
- `[output] dir` — where xlsx + `run.log` land.

## Run

```bash
.venv/bin/python server.py                                   # stdio MCP server
npx @modelcontextprotocol/inspector .venv/bin/python server.py   # interactive inspect
```

For Claude Desktop, register it as an MCP server pointing at the **full venv python
path** and `server.py` (use absolute paths — `/Volumes/...`).

## First-run login (once per session)
You log in with **your own** Taobao account — no account, cookie, or profile ships in this
repo (`user_data/` is gitignored and lives only on your machine).
1. Call `taobao_initialize_login` (or just `taobao_fetch_product` — it auto-ensures login).
2. A **visible Chrome window** opens to the Taobao QR page.
3. **Scan the QR with your Taobao app.** The server polls and continues automatically.
4. The session persists in `user_data_dir` — restarts reuse it, no re-scan.

## Tools
| Tool | Purpose |
|---|---|
| `taobao_initialize_login` | Open Chrome, QR login (you scan). |
| `taobao_session_status` | Login/health (read-only). |
| `taobao_search` | Keyword → result list for you to pick from. |
| `taobao_fetch_product` | One product: **every SKU variant + price/stock**, specs, images. (`deep_price=True` clicks each variant for the live after-subsidy price.) |
| `taobao_fetch_reviews` | Recent reviews, each tagged with the variant bought. |
| `taobao_add_to_cart` | **Gated** cart staging — preview, then `confirm=True`; selects + validates the variant, adds via the cart API (Taobao **and** Tmall). Never buys/checks out. |
| `taobao_read_messages` | Read seller IM conversations + a thread's messages (read-only). |
| `taobao_send_reply` | Send a seller message — **confirm-then-send** (preview, then `confirm=True`). |
| `taobao_track_orders` | Daily digest: per order — status, carrier + tracking#, **取件码 pickup code** + station. Caps to one live run/day. |
| `taobao_export_xlsx` | 3-sheet comparison workbook (Summary / Variants / Reviews). |

## The Skill
`skill/SKILL.md` is the sourcing playbook (search → you pick → fetch → translate →
summarize reviews → normalize price-per-unit → compare → export → flag risks).
`skill/supplier_templates.md` has Chinese message templates — **Claude drafts; sent via
`taobao_send_reply` only after you confirm that exact message** (never blind auto-send).

---

## Troubleshooting
- **It launched Comet / the wrong browser** — set `[browser] executable_path` to your
  Google Chrome binary (default: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`).
- **"login_required" / NotLoggedInError** — run `taobao_initialize_login` and scan the QR; keep the window open.
- **A slider/verification appeared** — solve it yourself in the Chrome window; the tool pauses (`human_action_required`) and resumes. It logs to `output/run.log`.
- **Screenshots/automation "page still loading"** — the new detail page holds a connection open; this server uses embedded-data + DOM extraction (not screenshot-waits), so this only affects ad-hoc scripts.
- **`SelectorDriftError`** — Taobao changed its layout; patch the one file `src/extract/selectors.py`.
- **Wrong price on a multi-model listing** — the headline price is the cheapest model; always read the **per-SKU price** for the exact variant. `补贴后` prices may include a 国补 subsidy that needs a mainland ID — verify the real checkout price.
- **Only a few reviews returned** — deep review pagination is shallow (known limit); increase scrolling in `src/extract/reviews.py` if needed.
- **Reset everything** — delete `user_data/chrome_profile/` and re-scan the QR.

## Risks (don't hide these)
- Scraping Taobao violates its ToS; using your own logged-in account carries
  account-limitation risk. Keep volume low and human-paced.
- mtop endpoints / selectors drift — budget periodic maintenance (selectors are centralized).

## Tests
```bash
.venv/bin/python -m pytest -q     # parsers, output, MCP contract, drift, evals
```
