"""Characterize how SKU data is embedded in a captured page.html (Phase 2 recon).

Usage:  .venv/bin/python scripts/analyze_fixture.py 736546459871
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

pid = sys.argv[1]
html = (Path("tests/fixtures") / pid / "page.html").read_text(encoding="utf-8")
print(f"html size: {len(html)//1024} KB")

# Common SSR wrapper markers
for marker in ("__GLOBAL_DATA", "__PRELOADED_STATE__", "__INITIAL_DATA__", "window._DATA",
               "JSON.parse(", "application/json", "TShop", "Hybrid.recommend", "skuBase", "sku2info"):
    print(f"  marker {marker!r}: {html.count(marker)}")

scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
print(f"\n<script> blocks: {len(scripts)}")
for i, sc in enumerate(scripts):
    if "sku2info" in sc and "skuBase" in sc:
        print(f"\n=== script #{i}: len={len(sc)} ===")
        print("HEAD(160):", repr(sc[:160]))
        for key in ("skuBase", "sku2info", "propPath", "\"props\"", "priceText", "priceMoney"):
            idx = sc.find(key)
            if idx >= 0:
                print(f"\n  ~{key} @ {idx}:", repr(sc[max(0, idx - 40):idx + 160]))
        break
