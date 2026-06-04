"""Live: run the order tracker + print the pickup digest."""

from __future__ import annotations

import asyncio

from src.browser.session import get_session
from src.extract.orders import order_digest, track_orders


async def main() -> None:
    orders = await track_orders(only_active=False, max_drill=6)
    print(f"orders parsed: {len(orders)}\n")
    print(order_digest(orders))
    await get_session().close()
    print("\nDONE")


if __name__ == "__main__":
    asyncio.run(main())
