"""Live end-to-end: fetch product (every SKU priced) + reviews (variant-linked).

Usage:  .venv/bin/python scripts/e2e_smoke.py 736546459871
"""

from __future__ import annotations

import asyncio
import sys

from src.extract.product import parse_product
from src.extract.reviews import group_by_variant, parse_reviews
from src.browser.session import get_session


async def main(pid: str) -> None:
    session = get_session()
    await session.start()
    if not await session.is_logged_in():
        print("NOT LOGGED IN — run scripts/phase1_smoke.py login first")
        await session.close()
        return

    print("=" * 60)
    product = await parse_product(pid)
    print(f"TITLE : {product.title[:64]}")
    print(f"SHOP  : {product.shop_name}")
    print(f"PRICE : {product.price_range}  |  images: {len(product.image_urls)}")
    print(f"VARIANTS ({len(product.variants)}):")
    for v in product.variants:
        label = " / ".join(f"{k}={val}" for k, val in v.properties.items())
        print(f"   ¥{v.price}  stock={v.stock}  avail={v.available}   {label}")

    reviews = await parse_reviews(pid, max_reviews=20)
    product.reviews = reviews
    product.reviews_by_variant = group_by_variant(reviews)
    print(f"\nREVIEWS ({len(reviews)}):")
    for r in reviews[:8]:
        print(f"   [{r.date}] img={r.has_images} «{r.sku_bought}» {r.text[:46]}")
    print("\nREVIEWS BY VARIANT:")
    for label, rs in product.reviews_by_variant.items():
        imgs = sum(1 for r in rs if r.has_images)
        print(f"   {label}: {len(rs)} reviews ({imgs} with photos)")
    print("=" * 60)

    await session.close()
    print("E2E_OK")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
