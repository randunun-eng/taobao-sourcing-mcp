"""Validate the click-through 平台加补后 (after-subsidy) price read on the P100, per tier.

Selects each variant chip and reads the displayed price — proving the mechanism before
it's wired into parse_product(deep_price=True).

Usage:  .venv/bin/python scripts/deep_price_check.py 736546459871
"""

from __future__ import annotations

import asyncio
import sys

from src.browser.pacing import human_delay, human_scroll
from src.browser.session import BrowserSession
from src.extract.product import build_variants, extract_ice_res

CLICK_JS = r"""(value) => {
  const norm = s => (s||'').replace(/\s+/g,' ').trim();
  const els = [...document.querySelectorAll('div,span,button,li,a')];
  let exact=null, contains=null;
  for (const e of els) {
    const t = norm(e.innerText); if(!t) continue;
    const r = e.getBoundingClientRect();
    const chip = r.width>30 && r.width<380 && r.height>14 && r.height<80;
    if (t === value && chip) { exact=e; break; }
    if (!contains && chip && t.includes(value) && t.length < value.length+6) contains=e;
  }
  const target = exact||contains;
  if (!target) return false;
  target.scrollIntoView({block:'center'});
  target.click(); target.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
  return true;
}"""

PRICE_JS = r"""() => {
  const all=[...document.querySelectorAll('*')];
  let best=null, bestLen=999;
  for (const e of all) { const t=(e.innerText||'').replace(/\s+/g,'');
    if (t.includes('平台加补后') && /\d/.test(t) && t.length<40 && t.length<bestLen) { best=t; bestLen=t.length; } }
  if (best) { const m=best.match(/平台加补后[¥￥]?([\d.]+)/); return {after:m?m[1]:null, ctx:best}; }
  return null;
}"""


async def main(pid: str) -> None:
    s = BrowserSession()
    page = await s.start()
    await page.goto(f"https://item.taobao.com/item.htm?id={pid}", wait_until="domcontentloaded")
    await s.guard_captcha(page)
    await human_scroll(page, 2)
    await human_delay(1.5, 2.5)
    res = extract_ice_res(await page.content())
    variants = build_variants(res.get("skuBase", {}) or {}, (res.get("skuCore", {}) or {}).get("sku2info", {}) or {})
    print(f"{len(variants)} variants — clicking each to read the displayed (after-subsidy) price:\n")
    for v in variants:
        ok = True
        for value in v.properties.values():
            try:
                loc = page.get_by_text(value, exact=True).first   # exact → the chip, not the spec table
                if await loc.count() == 0:
                    loc = page.get_by_text(value[:14], exact=False).first  # badge fallback (推荐 etc.)
                await loc.scroll_into_view_if_needed(timeout=3000)
                await loc.click(timeout=4000)            # REAL trusted click (React responds)
            except Exception as e:
                ok = False
                print("   click-fail:", value[:24], type(e).__name__)
                break
            await human_delay(0.8, 1.4)
        await human_delay(1.0, 1.6)
        shown = await page.evaluate(PRICE_JS) if ok else None
        url = page.url
        skuid = url.split("skuId=")[1][:16] if "skuId=" in url else "—"
        label = " / ".join(v.properties.values())
        print(f"  优惠前=¥{v.price}  skuId={skuid}  read={shown}   {label[:42]}")
    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
