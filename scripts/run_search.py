"""Run a live search via the built server's parser and print results as JSON lines.

Usage:  .venv/bin/python scripts/run_search.py "NVIDIA P100"
"""

from __future__ import annotations

import asyncio
import json
import sys

from src.browser.session import get_session
from src.extract.search import parse_search


async def main(kw: str) -> None:
    results = await parse_search(kw)
    print(f"RESULTS {len(results)}")
    for i, r in enumerate(results, 1):
        print(json.dumps({
            "i": i, "id": r.product_id, "title": r.title, "price": r.price,
            "sales": r.monthly_sales, "shop": r.shop_name, "loc": r.location,
        }, ensure_ascii=False))
    await get_session().close()
    print("SEARCH_DONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "NVIDIA P100"))
