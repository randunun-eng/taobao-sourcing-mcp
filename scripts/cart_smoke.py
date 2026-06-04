"""Live smoke for add_to_cart: list variants → preview → ONE real gated add (confirm=True).

Reversible (cart only). Run: .venv/bin/python scripts/cart_smoke.py [product_id]
"""

from __future__ import annotations

import asyncio
import sys

from src.browser.session import ensure_logged_in, get_session
from src.cart import add_to_cart


async def main(pid: str) -> None:
    status = await ensure_logged_in()
    print("login:", status)
    if status != "logged_in":
        print("Not logged in — scan the QR in the Chrome window, then re-run.")
        return

    # 1) no options → tool returns the available variant choices
    choices_msg = await add_to_cart(pid)
    print("\n[1] choices:", choices_msg)

    # pull the first concrete variant label from the message ("Available: A; B; C")
    first = None
    if "Available:" in choices_msg:
        first = choices_msg.split("Available:", 1)[1].split(";")[0].strip()
    print("    picked variant:", first)

    opts = [first] if first else []

    # 2) preview (confirm=False)
    print("\n[2] preview:", await add_to_cart(pid, options=opts, qty=1, confirm=False))

    # 3) REAL add (confirm=True) — reversible cart write
    print("\n[3] add:", await add_to_cart(pid, options=opts, qty=1, confirm=True))

    await get_session().close()
    print("\nDONE — verify the item is in your Taobao cart.")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
