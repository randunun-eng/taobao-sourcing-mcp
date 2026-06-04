"""Find the listing's STATED total review count (not just rendered cards).

Taobao keeps one review pool per listing (no per-variant sections); the total is
shown as a label like 累计评价(N) / 宝贝评价 N / N条评价. This prints count-bearing
lines + tab labels + how many cards are currently rendered.

Usage:  .venv/bin/python scripts/review_count.py 736546459871
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
    except Exception:
        pass
    await human_delay(2.0, 3.0)

    data = await page.evaluate(
        r"""() => {
          const lines = (document.body.innerText||'').split('\n').map(s=>s.trim()).filter(Boolean);
          const hits = [...new Set(lines.filter(l => /(评价|好评)/.test(l) && /\d/.test(l) && l.length<32))].slice(0,25);
          const labels = [...new Set([...document.querySelectorAll('*')]
              .filter(e=>e.children.length===0)
              .map(e=>(e.innerText||'').trim())
              .filter(t=>/评价/.test(t) && t.length<20))].slice(0,15);
          const cards = document.querySelectorAll('[class*="Comment--"]').length;
          return {cards, hits, labels};
        }"""
    )
    print("rendered review cards:", data["cards"])
    print("count-bearing lines (评价/好评 + number):")
    for h in data["hits"]:
        print("   ", h)
    print("labels mentioning 评价:", data["labels"])
    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
