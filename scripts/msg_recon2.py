"""Recon pass 2: dump href/attrs of the 商家客服/客服 entries, then hover→click 商家客服
and capture the chat page/popup structure. READ-ONLY (sends nothing)."""

from __future__ import annotations

import asyncio
import sys

from src.browser.pacing import human_delay, human_scroll
from src.browser.session import BrowserSession

ATTRS_JS = r"""() => {
  const norm = s => (s||'').replace(/\s+/g,'').trim();
  const KW = ['客服','旺旺','咨询','联系卖家'];
  const out = [];
  for (const e of document.querySelectorAll('a,button,div,span')) {
    const t = norm(e.innerText);
    if (t && t.length < 8 && KW.some(k => t.includes(k))) {
      const ds = {}; for (const k in e.dataset) ds[k] = e.dataset[k];
      out.push({ t, tag: e.tagName, cls: (e.className||'').toString().slice(0,36),
                 href: (e.getAttribute && e.getAttribute('href')) || '', data: ds });
    }
  }
  const seen = new Set(); const u = [];
  for (const h of out) { const k = h.t+h.tag+h.href; if (!seen.has(k)) { seen.add(k); u.push(h); } }
  return u.slice(0, 14);
}"""

DUMP_JS = r"""() => {
  const norm = s => (s||'').replace(/\s+/g,'').trim();
  const inputs = [...document.querySelectorAll('textarea,input[type=text],div[contenteditable=true]')]
    .map(e => ({ tag: e.tagName, editable: e.getAttribute('contenteditable')||'',
                 ph: e.getAttribute('placeholder')||'', cls: (e.className||'').toString().slice(0,40) })).slice(0,8);
  const sends = [...document.querySelectorAll('a,button,div,span')]
    .filter(e => { const t = norm(e.innerText); return t && t.length<6 && t.includes('发送'); })
    .map(e => ({ t: norm(e.innerText), tag: e.tagName, cls: (e.className||'').toString().slice(0,40) })).slice(0,6);
  return { inputs, sends, bodyLen: (document.body.innerText||'').length };
}"""


async def main(pid: str) -> None:
    s = BrowserSession()
    page = await s.start()
    await page.goto(f"https://item.taobao.com/item.htm?id={pid}", wait_until="domcontentloaded")
    await s.guard_captcha(page)
    await human_scroll(page, 2)
    await human_delay(2.0, 3.0)

    print("contact entries (with href/data):")
    for h in await page.evaluate(ATTRS_JS):
        print("  ", h)

    # hover the visible 客服 button to reveal the menu, then click 商家客服
    before = set(p.url for p in s.context.pages)
    try:
        btn = page.locator('a[class*="button--"], span[class*="buttonText--"]').filter(has_text="客服").first
        await btn.hover(timeout=4000)
        await human_delay(1.0, 1.8)
        print("\nhovered 客服; clicking 商家客服…")
        await page.get_by_text("商家客服", exact=True).first.click(timeout=5000)
    except Exception as exc:
        print("  hover/click failed:", exc)
    await human_delay(3.5, 5.0)

    pages = s.context.pages
    print(f"\ncontext now has {len(pages)} page(s):")
    for i, p in enumerate(pages):
        new = "  (NEW)" if p.url not in before else ""
        print(f"  page[{i}] {p.url[:74]}{new}  frames={len(p.frames)}")

    chat = pages[-1]
    try:
        await chat.bring_to_front()
        await human_delay(2.0, 3.0)
    except Exception:
        pass
    print("\n--- newest page inputs/send (top-level) ---")
    try:
        print("  ", await chat.evaluate(DUMP_JS))
    except Exception as exc:
        print("   err:", exc)
    for j, fr in enumerate(chat.frames):
        try:
            d = await fr.evaluate(DUMP_JS)
            if d["inputs"] or d["sends"]:
                print(f"  frame[{j}] url={fr.url[:54]} -> {d}")
        except Exception:
            pass

    await s.close()
    print("\nDONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
