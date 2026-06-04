"""Dump the rendered review-card layout so we can build the DOM parser.

Usage:  .venv/bin/python scripts/review_dom_recon.py 736546459871
"""

from __future__ import annotations

import asyncio
import sys

from src.browser.pacing import human_delay, human_scroll
from src.browser.session import BrowserSession


async def main(pid: str) -> None:
    s = BrowserSession()
    page = await s.start()
    await page.goto(f"https://item.taobao.com/item.htm?id={pid}", wait_until="domcontentloaded")
    await s.guard_captcha(page)
    for _ in range(5):
        await human_scroll(page, 2)
        await human_delay(1.0, 1.5)
    try:
        loc = page.get_by_text("评价", exact=False).first
        await loc.scroll_into_view_if_needed(timeout=3000)
        await loc.click(timeout=3000)
    except Exception as e:
        print("review-tab click note:", e)
    for _ in range(4):
        await human_scroll(page, 2)
        await human_delay(1.0, 1.5)

    data = await page.evaluate(
        r"""() => {
          const cards=[...document.querySelectorAll('[class*="Comment--"]')];
          const sample = cards.slice(0,6).map(c => ({
            text: c.innerText.replace(/\n+/g,' | ').slice(0,400),
            imgs: c.querySelectorAll('img').length,
            childClasses: [...new Set([...c.querySelectorAll('*')].map(e=>(e.className||'').toString().split('--')[0]).filter(Boolean))].slice(0,15)
          }));
          return {count: cards.length, sample};
        }"""
    )
    print("review card count:", data["count"])
    for i, c in enumerate(data["sample"]):
        print(f"\n--- card {i} (imgs={c['imgs']}) ---")
        print("text:", c["text"])
        print("childClasses:", c["childClasses"])

    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
