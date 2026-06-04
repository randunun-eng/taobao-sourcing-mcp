"""Head-to-head: fetch product + deep reviews for several IDs, print + export xlsx + JSON.

Usage:  .venv/bin/python scripts/compare.py 963112367340 1001947739217 981256389688
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from src.browser.pacing import human_delay
from src.browser.session import get_session
from src.extract.product import parse_product
from src.extract.reviews import group_by_variant, parse_reviews
from src.output.xlsx_writer import write_xlsx


async def main(ids: list[str]) -> None:
    products = []
    for pid in ids:
        print(f"\n========== {pid} ==========")
        try:
            p = await parse_product(pid)
            reviews = await parse_reviews(pid, max_reviews=20)
            p.reviews = reviews
            p.reviews_by_variant = group_by_variant(reviews)
            products.append(p)
            print(f"TITLE {p.title[:56]}")
            print(f"SHOP {p.shop_name} | PRICE {p.price_range} | variants {len(p.variants)} | reviews {len(reviews)}")
            for v in p.variants:
                lbl = " / ".join(f"{k}={val}" for k, val in v.properties.items())
                print(f"   ¥{v.price} stock={v.stock} avail={v.available} {lbl[:54]}")
            for r in reviews[:5]:
                print(f"   [{r.date}] img={r.has_images} «{r.sku_bought}» {r.text[:44]}")
        except Exception as e:
            print(f"   ERROR: {type(e).__name__}: {e}")
        await human_delay(2.0, 4.0)

    if products:
        summary = [{
            "id": p.product_id, "title": p.title, "shop": p.shop_name, "price_range": p.price_range,
            "variants": [{"label": " / ".join(f"{k}:{v}" for k, v in vv.properties.items()),
                          "price": vv.price, "stock": vv.stock, "available": vv.available} for vv in p.variants],
            "n_reviews": len(p.reviews),
            "n_reviews_with_images": sum(1 for r in p.reviews if r.has_images),
            "reviews": [{"date": r.date, "img": r.has_images, "sku": r.sku_bought, "text": r.text} for r in p.reviews[:14]],
        } for p in products]
        Path("output").mkdir(exist_ok=True)
        Path("output/compare_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        path = write_xlsx(products, "p100_compare.xlsx")
        print(f"\nXLSX: {path}")
        print("JSON: output/compare_summary.json")

    await get_session().close()
    print("COMPARE_DONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or ["963112367340", "1001947739217", "981256389688"]))
