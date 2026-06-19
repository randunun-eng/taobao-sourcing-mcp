"""Read 已买到的宝贝 (purchased items) — titles + statuses, to learn buying patterns. READ-ONLY."""

from __future__ import annotations

import asyncio

from src.browser.session import ensure_logged_in, get_session
from src.browser.pacing import human_delay, human_scroll

JS = r"""() => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const items = [...document.querySelectorAll('a')]
    .map(a => ({ t: norm(a.innerText), h: a.getAttribute('href') || '' }))
    .filter(x => /item\.htm|detail\.tmall/.test(x.h) && x.t.length > 6)
    .map(x => x.t);
  const statuses = (document.body.innerText.match(/交易成功|待发货|待收货|待评价|退款成功|退款中|交易关闭|卖家已发货/g) || []);
  const sc = {}; statuses.forEach(s => sc[s] = (sc[s] || 0) + 1);
  return { items: [...new Set(items)].slice(0, 30), statusCounts: sc, head: norm(document.body.innerText).slice(0, 110) };
}"""


async def main() -> None:
    s = await ensure_logged_in()
    if s != "logged_in":
        print("login:", s)
        return
    sess = get_session()
    page = await sess.start()
    await page.goto("https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm",
                    wait_until="domcontentloaded")
    await sess.guard_captcha(page)
    await human_delay(3, 4)
    await human_scroll(page, 3)
    await human_delay(2, 3)
    d = await page.evaluate(JS)
    print("head:", d["head"])
    print("statuses:", d["statusCounts"])
    print("--- purchased items (distinct, recent) ---")
    for t in d["items"]:
        print("  -", t[:64])
    await sess.close()


if __name__ == "__main__":
    asyncio.run(main())
