"""Produce a committable, token-free detail_res.json from a captured page.html.

Keeps only product data needed by the parser (props, skus, per-sku price/qty,
title, images, shop name) and asserts no account tokens leak.

Usage:  .venv/bin/python scripts/sanitize_fixture.py 736546459871
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from src.extract.product import extract_ice_res

pid = sys.argv[1]
d = Path("tests/fixtures") / pid
res = extract_ice_res((d / "page.html").read_text(encoding="utf-8"))

sku_base = res.get("skuBase", {}) or {}
sku2info = (res.get("skuCore", {}) or {}).get("sku2info", {}) or {}
item = res.get("item", {}) or {}
seller = res.get("seller", {}) or {}

clean = {
    "skuBase": {
        "props": [
            {
                "pid": g.get("pid"),
                "name": g.get("name"),
                "values": [{"vid": v.get("vid"), "name": v.get("name")} for v in g.get("values", [])],
            }
            for g in sku_base.get("props", [])
        ],
        "skus": [{"propPath": s.get("propPath"), "skuId": s.get("skuId")} for s in sku_base.get("skus", [])],
    },
    "skuCore": {
        "sku2info": {
            sid: {
                "price": {k: (info.get("price") or {}).get(k)
                          for k in ("priceText", "priceMoney", "priceTitle", "priceDesc")
                          if k in (info.get("price") or {})},
                "quantity": info.get("quantity"),
                "quantityText": info.get("quantityText"),
            }
            for sid, info in sku2info.items()
        }
    },
    "item": {"title": item.get("title"), "itemId": item.get("itemId"), "images": item.get("images", [])},
    "seller": {"shopName": seller.get("shopName")},
}

# componentsVO: 参数 specs (BASE_PROPS) + embedded preview reviews — strip reviewer identity.
_cv = res.get("componentsVO", {}) or {}
_infos = (_cv.get("extensionInfoVO", {}) or {}).get("infos", []) or []
_rate = _cv.get("rateVO", {}) or {}
_rate_items = ((_rate.get("group", {}) or {}).get("items", []) or [])
clean["componentsVO"] = {
    "extensionInfoVO": {"infos": [
        {"type": b.get("type"), "items": [{"title": it.get("title"), "text": it.get("text")} for it in b.get("items", [])]}
        for b in _infos if isinstance(b, dict) and b.get("type") == "BASE_PROPS"
    ]},
    "rateVO": {
        "totalCount": _rate.get("totalCount"),
        "favorableRate": _rate.get("favorableRate"),
        "group": {"items": [
            {"content": it.get("content"), "skuInfo": it.get("skuInfo"),
             "media": [{"type": (m or {}).get("type")} for m in (it.get("media") or [])],
             "dateTime": it.get("dateTime")}
            for it in _rate_items if isinstance(it, dict)
        ]},
    },
}

out = d / "detail_res.json"
out.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")

txt = out.read_text(encoding="utf-8")
# Account nick (if any) comes from env so it's never hardcoded in the repo.
_nick = os.environ.get("TAOBAO_ACCOUNT_NICK", "")
for bad in (b for b in (_nick, "_tb_token_", "tracknick", "mi_id", "aplusParams", "encryptUid") if b):
    assert bad not in txt, f"LEAK: {bad!r} still present in {out}"
print(f"wrote {out} ({len(txt)} bytes) — verified no account tokens")
