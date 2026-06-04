"""Recon the 查看物流 (logistics) drill-down: is tracking# / 取件码 / station extractable?"""

from __future__ import annotations

import asyncio

from src.browser.pacing import human_delay, human_scroll
from src.browser.session import BrowserSession


async def main() -> None:
    s = BrowserSession()
    page = await s.start()
    await page.goto("https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm", wait_until="domcontentloaded")
    await s.guard_captcha(page)
    await human_scroll(page, 2)
    await human_delay(2.0, 3.0)

    ctx = page.context
    n_before = len(ctx.pages)
    try:
        loc = page.get_by_text("查看物流", exact=False).first
        await loc.scroll_into_view_if_needed(timeout=3000)
        await loc.click(timeout=5000)
    except Exception as e:
        print("查看物流 click error:", type(e).__name__, e)
    await human_delay(2.5, 3.5)

    target = ctx.pages[-1] if len(ctx.pages) > n_before else page  # new tab, or same-page modal
    try:
        await target.wait_for_load_state("domcontentloaded", timeout=8000)
    except Exception:
        pass
    print("opened new tab:", len(ctx.pages) > n_before, "| url:", target.url[:90])

    import re

    print("frames:", len(target.frames))
    for fr in target.frames:
        try:
            t = await fr.evaluate("() => document.body ? document.body.innerText : ''")
        except Exception:
            t = ""
        if not (t or "").strip():
            continue
        quqian = re.findall(r"取(?:件|货)码[:：]?\s*[\dA-Za-z\-]+", t)
        tracking = re.findall(r"运单(?:号|编号)?[:：]?\s*[\dA-Za-z]{8,}", t)
        carrier = sorted(set(re.findall(r"顺丰|中通|圆通|韵达|申通|邮政|京东|极兔|菜鸟|德邦", t)))
        station = re.findall(r".{0,8}(?:驿站|快递柜|代收点|自提点).{0,6}", t)
        print(f"\n  frame[{fr.url[:46]}] len={len(t)}")
        print(f"    取件码={quqian[:2]} tracking={tracking[:2]} carrier={carrier} station={station[:2]}")
        print(f"    snippet: {t[:220].replace(chr(10), ' | ')}")
    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())
