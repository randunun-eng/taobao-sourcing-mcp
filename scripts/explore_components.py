"""Dump componentsVO (specs + embedded reviews) structure from a captured page.html."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.extract.product import extract_ice_res

pid = sys.argv[1] if len(sys.argv) > 1 else "736546459871"
html = (Path("tests/fixtures") / pid / "page.html").read_text(encoding="utf-8")
res = extract_ice_res(html)
print("res keys:", list(res.keys()))

cv = res.get("componentsVO", {}) or {}
print("componentsVO keys:", list(cv.keys()))

ext = cv.get("extensionInfoVO", {}) or {}
print("extensionInfoVO keys:", list(ext.keys()))
infos = ext.get("infos", []) or []
print("infos types:", [i.get("type") for i in infos] if isinstance(infos, list) else type(infos).__name__)
for i in (infos if isinstance(infos, list) else []):
    if i.get("type") == "BASE_PROPS":
        items = i.get("items", []) or []
        print("BASE_PROPS first item full:", json.dumps(items[0], ensure_ascii=False) if items else "none")
        print("BASE_PROPS all keys seen:", sorted({k for it in items for k in it.keys()}))
        print("BASE_PROPS pairs:", [(it.get("name") or it.get("title") or it.get("label"), it.get("text") or it.get("value")) for it in items[:14]])
    print("rateVO.totalCount / favorableRate:", res.get("componentsVO", {}).get("rateVO", {}).get("totalCount"),
          res.get("componentsVO", {}).get("rateVO", {}).get("favorableRate"))

print("\n--- priceVO ---")
print(json.dumps(cv.get("priceVO", {}), ensure_ascii=False)[:600])
print("--- umpPriceLogVO ---")
print(json.dumps(cv.get("umpPriceLogVO", {}), ensure_ascii=False)[:400])
print("--- one full sku2info price entry ---")
_s2i = (res.get("skuCore", {}) or {}).get("sku2info", {}) or {}
for _sid, _info in _s2i.items():
    if _sid != "0":
        print(_sid, json.dumps(_info.get("price", {}), ensure_ascii=False))
        break

rate = cv.get("rateVO", {}) or {}
print("\nrateVO keys:", list(rate.keys()))
grp = rate.get("group", {}) or {}
print("rateVO.group keys:", list(grp.keys()) if isinstance(grp, dict) else type(grp).__name__)
items = grp.get("items", []) if isinstance(grp, dict) else []
print("rate items count:", len(items))
for it in items[:3]:
    print("  item keys:", list(it.keys()))
    print("   sample:", json.dumps({k: it.get(k) for k in
          ("feedback", "content", "rateContent", "skuInfo", "auctionSku", "sku", "date", "feedbackDate", "media", "pics", "photos")
          if k in it}, ensure_ascii=False)[:300])
