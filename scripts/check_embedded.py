"""Confirm parse_product now returns specs + variant-linked reviews from ONE navigation."""

from __future__ import annotations

import asyncio

from src.browser.session import get_session
from src.extract.product import parse_product


async def main() -> None:
    p = await parse_product("736546459871")  # deep_reviews=False → single navigation
    print("TITLE  :", p.title[:48])
    print("VARIANTS:", [(round(v.price, 2) if v.price else None) for v in p.variants])
    print("SPECS  :", p.specs)
    print("REVIEWS:", len(p.reviews), [(r.sku_bought, r.has_images) for r in p.reviews])
    print("BY VAR :", {k: len(v) for k, v in p.reviews_by_variant.items()})
    await get_session().close()
    print("OK")


if __name__ == "__main__":
    asyncio.run(main())
