"""Recon the "查看全部评价" (View all reviews) UI: modal vs page, selectors, pagination.

Usage:  .venv/bin/python scripts/review_viewall_recon.py 736546459871
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
        await human_delay(1.0, 1.3)

    url_before = page.url
    cards_before = await page.evaluate('document.querySelectorAll(\'[class*="Comment--"]\').length')

    clicked = "no"
    for label in ("查看全部评价", "全部评价", "查看更多"):
        try:
            loc = page.get_by_text(label, exact=False).first
            if await loc.count() > 0:
                await loc.scroll_into_view_if_needed(timeout=3000)
                await loc.click(timeout=3000)
                clicked = label
                break
        except Exception as e:
            clicked = f"err:{e}"
    await human_delay(2.5, 3.5)

    info = await page.evaluate(
        r"""() => {
          const dlg = [...document.querySelectorAll('[role="dialog"], [class*="Dialog"], [class*="Modal"], [class*="Drawer"], [class*="Popup"], [class*="popup"]')];
          const dialogInfo = dlg.slice(0,4).map(d=>({
            cls:(d.className||'').toString().slice(0,50),
            comment_cards: d.querySelectorAll('[class*="Comment--"]').length,
            rate_cards: d.querySelectorAll('[class*="rate"], [class*="Rate"]').length,
            scrollable: d.scrollHeight > d.clientHeight + 20
          }));
          const cards = document.querySelectorAll('[class*="Comment--"]').length;
          const tabs = [...new Set([...document.querySelectorAll('*')]
              .filter(e=>e.children.length===0)
              .map(e=>(e.innerText||'').trim())
              .filter(t=>/有图|全部|追评|好评|中评|差评|视频|下一页|加载更多/.test(t) && t.length<18))].slice(0,18);
          return {cards, dialogs: dialogInfo, tabs};
        }"""
    )
    print("url_before:", url_before[:64])
    print("url_after :", page.url[:64])
    print("clicked   :", clicked)
    print("cards_before:", cards_before, "| cards_after:", info["cards"])
    print("dialogs:")
    for d in info["dialogs"]:
        print("   ", d)
    print("tabs/controls:", info["tabs"])
    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
