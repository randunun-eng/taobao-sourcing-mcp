"""Recon the search-results shape (Phase 2b).

Usage:  .venv/bin/python scripts/capture_search.py "tesla p100 16g"
"""

from __future__ import annotations

import asyncio
import sys
from urllib.parse import quote

from src.browser.pacing import human_delay, human_scroll
from src.browser.session import BrowserSession

EXTRACT_JS = r"""() => {
  const sels=['a[href*="item.htm"]','a[href*="//item.taobao.com"]','a[href*="detail.tmall.com"]'];
  let links=[]; sels.forEach(s=>links.push(...document.querySelectorAll(s)));
  links=[...new Set(links)];
  const seen=new Set(); const rows=[];
  for(const a of links){
    const m=(a.getAttribute('href')||'').match(/[?&]id=(\d{6,})/); const id=m?m[1]:null;
    if(!id||seen.has(id)) continue;
    let card=a, found=null;
    for(let i=0;i<8;i++){ if(!card) break; const t=card.innerText||'';
      if(t.includes('¥')&&(t.includes('付款')||t.includes('人付'))&&t.length<260){found=card;break;} card=card.parentElement; }
    if(!found) continue; seen.add(id);
    rows.push({id, text:(found.innerText||'').replace(/\s+/g,' ').trim().slice(0,200)});
  }
  return rows;
}"""


async def main(kw: str) -> None:
    s = BrowserSession()
    page = await s.start()
    await page.goto(f"https://s.taobao.com/search?q={quote(kw)}", wait_until="domcontentloaded")
    await s.guard_captcha(page)
    for _ in range(3):
        await human_scroll(page, 3)
        await human_delay(1.0, 2.0)
    html = await page.content()
    print("embedded-data markers:",
          "g_page_config=", html.count("g_page_config"),
          "| mtopjsonp=", html.count("mtopjsonp"),
          "| 'var b = {'=", html.count("var b = {"),
          "| itemList=", html.count("itemList"),
          "| 'data-id'=", html.count("data-id"))
    rows = await page.evaluate(EXTRACT_JS)
    print(f"DOM-climb extracted {len(rows)} cards; sample:")
    for r in rows[:5]:
        print("  #", r["id"], "|", r["text"][:110])
    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "tesla p100 16g"))
