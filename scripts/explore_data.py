"""Extract the embedded ICE data object from a fixture and dump SKU structure.

Usage:  .venv/bin/python scripts/explore_data.py 736546459871
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def extract_object(text: str, anchor: str) -> str | None:
    """Return the balanced {...} JSON object that follows `anchor` (string-aware)."""
    i = text.find(anchor)
    if i < 0:
        return None
    j = text.find("{", i)
    if j < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for k in range(j, len(text)):
        c = text[k]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[j:k + 1]
    return None


pid = sys.argv[1]
html = (Path("tests/fixtures") / pid / "page.html").read_text(encoding="utf-8")

raw = extract_object(html, "var b = {")
print("extracted var b:", "OK" if raw else "FAILED", "len=", len(raw or ""))
b = json.loads(raw)
print("top keys:", list(b.keys()))

res = b["loaderData"]["home"]["data"]["res"]
print("res keys:", list(res.keys()))

skuBase = res.get("skuBase", {})
skuCore = res.get("skuCore", {})
sku2info = skuCore.get("sku2info", {})
print("skuCore keys:", list(skuCore.keys()))
print("\n--- skuBase.props (groups) ---")
for g in skuBase.get("props", []):
    print(f"  pid={g.get('pid')} name={g.get('name')!r} values=", [(v.get('vid'), v.get('name')) for v in g.get('values', [])])
print("\n--- skuBase.skus ---")
print(json.dumps(skuBase.get("skus"), ensure_ascii=False)[:600])
print("\n--- skuCore.sku2info entries ---")
for sid, info in sku2info.items():
    price = info.get("price", {})
    print(f"  sku {sid}: price={json.dumps(price, ensure_ascii=False)} quantity={info.get('quantity')} qtyText={info.get('quantityText')}")

print("\n--- item / seller / params (for title, shop, specs) ---")
item = res.get("item", {})
seller = res.get("seller", {})
print("item keys:", list(item.keys()))
print("  title:", item.get("title"))
print("  images (first 2):", (item.get("images") or [])[:2])
print("seller keys:", list(seller.keys()))
print("  shopName:", seller.get("shopName"), "| sellerNick:", seller.get("sellerNick"))
params = res.get("params", {})
print("params type:", type(params).__name__, "| keys/len:", list(params.keys()) if isinstance(params, dict) else len(params))
