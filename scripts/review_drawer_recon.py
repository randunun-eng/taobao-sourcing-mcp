"""Verify in-drawer pagination grows the card count + we can get real (non-boilerplate) reviews.

Usage:  .venv/bin/python scripts/review_drawer_recon.py 736546459871
"""

from __future__ import annotations

import asyncio
import sys

from src.browser.pacing import human_delay, human_scroll
from src.browser.session import BrowserSession

SCROLL_JS = r"""() => {
  const drawer = document.querySelector('[class*="Drawer--"]');
  if(!drawer) return -1;
  let best=null, bestGap=0;
  drawer.querySelectorAll('*').forEach(e=>{
    const gap=e.scrollHeight-e.clientHeight; const st=getComputedStyle(e).overflowY;
    if(gap>bestGap && (st==='auto'||st==='scroll')){bestGap=gap;best=e;}
  });
  const el=best||drawer; el.scrollTop=el.scrollHeight; return bestGap;
}"""

COUNT_JS = "document.querySelectorAll('[class*=\"Comment--\"]').length"

SAMPLE_JS = r"""() => {
  const boiler = ['该用户觉得商品非常好','此用户没有填写评价','系统默认好评','默认好评','卖家未及时','15天内','追评'];
  const cards=[...document.querySelectorAll('[class*="Comment--"]')];
  const out=[];
  for(const c of cards){
    const t=(c.querySelector('[class*="content--"]')?.innerText||'').trim();
    if(!t||boiler.some(b=>t.includes(b))) continue;
    const meta=(c.querySelector('[class*="meta--"]')?.innerText||'').replace(/\n+/g,' ').trim();
    const imgs=c.querySelectorAll('[class*="album--"] img, [class*="photo--"] img').length;
    out.push({t:t.slice(0,46), meta:meta.slice(0,42), imgs});
  }
  return out;
}"""


async def main(pid: str) -> None:
    s = BrowserSession()
    page = await s.start()
    await page.goto(f"https://item.taobao.com/item.htm?id={pid}", wait_until="domcontentloaded")
    await s.guard_captcha(page)
    for _ in range(5):
        await human_scroll(page, 2)
        await human_delay(1.0, 1.3)
    try:
        loc = page.get_by_text("查看全部评价", exact=False).first
        await loc.scroll_into_view_if_needed(timeout=3000)
        await loc.click(timeout=3000)
    except Exception as e:
        print("click err:", e)
    await human_delay(2.0, 3.0)

    counts = []
    gap = 0
    for _ in range(12):
        gap = await page.evaluate(SCROLL_JS)
        await human_delay(1.2, 2.0)
        counts.append(await page.evaluate(COUNT_JS))
        if len(counts) >= 3 and counts[-1] == counts[-3]:
            break
    print("inner scroll gap:", gap)
    print("card counts per scroll round:", counts)

    sample = await page.evaluate(SAMPLE_JS)
    real = [r for r in sample if r["t"]]
    print(f"real (non-boilerplate) reviews extracted: {len(real)} (of {counts[-1] if counts else 0} cards)")
    for r in real[:10]:
        print("   imgs=%d «%s» %s" % (r["imgs"], r["meta"], r["t"]))
    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
