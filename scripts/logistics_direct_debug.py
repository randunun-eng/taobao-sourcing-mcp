"""Debug: navigate DIRECTLY to a logistics URL and dump frames (does the dinamic frame load?)."""

from __future__ import annotations

import asyncio
import sys

from src.browser.pacing import human_delay
from src.browser.session import BrowserSession

OID = sys.argv[1] if len(sys.argv) > 1 else "<order_id>"  # pass a real order id as arg1
URL = f"https://market.m.taobao.com/app/dinamic/pc-trade-logistics/home.html?orderId={OID}"


async def main() -> None:
    s = BrowserSession()
    page = await s.start()
    await page.goto(URL, wait_until="domcontentloaded")
    await s.guard_captcha(page)
    await human_delay(4.0, 5.0)   # give the dinamic frame time to render
    print("url:", page.url[:80], "| frames:", len(page.frames))
    for i, fr in enumerate(page.frames):
        try:
            t = await fr.evaluate("() => document.body ? document.body.innerText : ''")
        except Exception as e:
            t = f"<err {type(e).__name__}>"
        t = (t or "").replace("\n", " | ")
        has = ("快递" in t) or ("驿站" in t)
        print(f"  frame[{i}] url={fr.url[:46]} len={len(t)} logistics={has}")
        if has or (10 < len(t) < 500):
            print("    ", t[:240])
    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())
