"""Recon the 已买到的宝贝 (bought items) page: order#, status, tracking, 取件码 availability."""

from __future__ import annotations

import asyncio

from src.browser.pacing import human_delay, human_scroll
from src.browser.session import BrowserSession

CANDIDATE_URLS = [
    "https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm",
    "https://i.taobao.com/my_taobao.htm",
]


async def main() -> None:
    s = BrowserSession()
    page = await s.start()
    for url in CANDIDATE_URLS:
        await page.goto(url, wait_until="domcontentloaded")
        await s.guard_captcha(page)
        await human_scroll(page, 3)
        await human_delay(2.0, 3.0)
        print(f"\n=== {url}")
        print("landed:", page.url[:80], "| title:", await page.title())
        data = await page.evaluate(
            r"""() => {
              const txt = document.body.innerText || '';
              return {
                len: txt.length,
                statuses: [...new Set((txt.match(/待付款|待发货|待收货|待评价|交易成功|运输中|待取件|已签收/g)||[]))],
                orderNos: (txt.match(/订单(?:号|编号)[:：]?\s*\d{10,}/g)||[]).slice(0,4),
                bareLongNums: [...new Set((txt.match(/\b\d{15,}\b/g)||[]))].slice(0,4),
                quqian: (txt.match(/取(?:件|货)码[:：]?\s*[\dA-Za-z\-]+/g)||[]).slice(0,4),
                tracking: (txt.match(/(顺丰|中通|圆通|韵达|申通|邮政|京东|极兔)[^\n]{0,18}/g)||[]).slice(0,4),
                viewLogistics: /查看物流|物流详情/.test(txt),
                orderCards: document.querySelectorAll('[class*="order"],[class*="Order"],[class*="bought"],[class*="trade"]').length,
              };
            }"""
        )
        for k, v in data.items():
            print(f"  {k}: {v}")
    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())
