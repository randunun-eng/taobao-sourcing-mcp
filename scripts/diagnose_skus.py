"""Diagnose per-SKU price completeness for a product (multi-dimension / needs-click).

Reports the option groups (dimensions), and for every SKU whether it is priced,
out-of-stock, or NEEDS_CLICK (in stock but no price in the embedded sku2info — i.e.
the price only appears after selecting the option combination live).

Usage:  .venv/bin/python scripts/diagnose_skus.py <product_id>
"""

from __future__ import annotations

import asyncio
import sys

from src.browser.pacing import human_delay, human_scroll
from src.browser.session import BrowserSession
from src.extract.product import build_variants, extract_ice_res


async def main(pid: str) -> None:
    s = BrowserSession()
    page = await s.start()
    await page.goto(f"https://item.taobao.com/item.htm?id={pid}", wait_until="domcontentloaded")
    await s.guard_captcha(page)
    await human_scroll(page, 2)
    await human_delay(1.5, 2.5)
    res = extract_ice_res(await page.content())

    sku_base = res.get("skuBase", {}) or {}
    sku2info = (res.get("skuCore", {}) or {}).get("sku2info", {}) or {}
    props = sku_base.get("props", []) or []
    skus = sku_base.get("skus", []) or []

    print("TITLE :", (res.get("item", {}) or {}).get("title", "")[:54])
    print("GROUPS:", [(g.get("name"), len(g.get("values", []))) for g in props], "→ dims:", len(props))
    print(f"SKUs declared: {len(skus)}   sku2info entries: {len(sku2info)}")

    variants = build_variants(sku_base, sku2info)
    priced = [v for v in variants if v.price is not None]
    oos = [v for v in variants if v.price is None and v.stock == 0]
    needs_click = [v for v in variants if v.price is None and (v.stock is None or v.stock > 0)]
    print(f"priced: {len(priced)}   OOS(null+stock0): {len(oos)}   NEEDS_CLICK(null+in-stock): {len(needs_click)}")
    for v in needs_click[:10]:
        print("   NEEDS_CLICK:", v.properties, "stock=", v.stock)
    for v in priced[:4]:
        print("   priced:", v.properties, "¥", v.price)
    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
