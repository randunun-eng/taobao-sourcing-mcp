"""Recon the add-to-cart controls: 加入购物车 button, quantity input, cart count."""

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
    await human_scroll(page, 2)
    await human_delay(2.0, 3.0)
    data = await page.evaluate(
        r"""() => {
          const norm = s => (s||'').replace(/\s+/g,'').trim();
          const add = [...document.querySelectorAll('button,div,span,a')]
            .filter(e => { const t = norm(e.innerText); return t && t.length<10 && t.includes('加入购物车'); })
            .map(e => ({ t: norm(e.innerText), cls: (e.className||'').toString().slice(0,34), tag: e.tagName })).slice(0,4);
          const buy = [...document.querySelectorAll('button,div,span,a')]
            .filter(e => { const t = norm(e.innerText); return t && t.length<14 && (t.includes('购买')||t.includes('领券')); })
            .map(e => norm(e.innerText)).slice(0,4);
          const qty = [...document.querySelectorAll('input')]
            .map(i => ({ type: i.type, val: i.value, cls: (i.className||'').toString().slice(0,30) }))
            .filter(i => i.type==='text'||i.type==='number'||i.type==='tel').slice(0,5);
          const cart = (document.body.innerText.match(/购物车\s*(\d+)/)||[])[1] || null;
          return { add, buy, qty, cart };
        }"""
    )
    print("加入购物车:", data["add"])
    print("buy buttons:", data["buy"])
    print("qty inputs:", data["qty"])
    print("cart count:", data["cart"])
    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
