"""Recon the seller-contact / messaging UI (READ-ONLY — sends nothing).

Finds the 联系卖家/旺旺/咨询 entry on a product page, clicks it, and dumps whatever
opens (popup/new tab/iframe) + any text input + send button, so we can build
read_messages + (gated) send_reply against the real structure.

Run: .venv/bin/python scripts/msg_recon.py [product_id]
"""

from __future__ import annotations

import asyncio
import sys

from src.browser.pacing import human_delay, human_scroll
from src.browser.session import BrowserSession

FIND_CONTACT_JS = r"""() => {
  const norm = s => (s||'').replace(/\s+/g,'').trim();
  const KW = ['联系卖家','旺旺','咨询','客服','联系客服','在线咨询'];
  const hits = [];
  for (const e of document.querySelectorAll('a,button,div,span,img')) {
    const t = norm(e.innerText) || norm(e.getAttribute && (e.getAttribute('title')||e.getAttribute('alt')));
    if (t && t.length < 12 && KW.some(k => t.includes(k))) {
      hits.push({ t, tag: e.tagName, cls: (e.className||'').toString().slice(0,40) });
    }
  }
  // dedupe by text+tag
  const seen = new Set(); const out = [];
  for (const h of hits) { const k = h.t+h.tag; if (!seen.has(k)) { seen.add(k); out.push(h); } }
  return out.slice(0, 12);
}"""

DUMP_PAGE_JS = r"""() => {
  const norm = s => (s||'').replace(/\s+/g,'').trim();
  const inputs = [...document.querySelectorAll('textarea,input[type=text],div[contenteditable=true]')]
    .map(e => ({ tag: e.tagName, type: e.type||'', editable: e.getAttribute('contenteditable')||'',
                 ph: e.getAttribute('placeholder')||'', cls: (e.className||'').toString().slice(0,40) })).slice(0,8);
  const sends = [...document.querySelectorAll('a,button,div,span')]
    .filter(e => { const t = norm(e.innerText); return t && t.length<6 && (t.includes('发送')||t==='发'); })
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

    hits = await page.evaluate(FIND_CONTACT_JS)
    print("contact entries on product page:")
    for h in hits:
        print("  ", h)

    if not hits:
        print("no contact button found — dumping message-center candidates instead")
        await s.close()
        return

    # click the first 联系卖家/旺旺-like entry and see what opens
    target = next((h["t"] for h in hits if "联系" in h["t"] or "旺旺" in h["t"] or "咨询" in h["t"]), hits[0]["t"])
    print(f"\nclicking: {target!r}")
    before = set(p.url for p in s.context.pages)
    try:
        await page.get_by_text(target, exact=True).first.click(timeout=5000)
    except Exception as exc:
        print("  click failed:", exc)
    await human_delay(3.0, 4.5)

    pages = s.context.pages
    print(f"\ncontext now has {len(pages)} page(s):")
    for i, p in enumerate(pages):
        new = "  (NEW)" if p.url not in before else ""
        print(f"  page[{i}] {p.url[:70]}{new}  frames={len(p.frames)}")

    # dump the newest page's inputs/send + its frames
    chat = pages[-1]
    try:
        await chat.bring_to_front()
        await human_delay(1.5, 2.5)
    except Exception:
        pass
    print("\n--- newest page top-level inputs/send ---")
    try:
        print("  ", await chat.evaluate(DUMP_PAGE_JS))
    except Exception as exc:
        print("   err:", exc)
    for j, fr in enumerate(chat.frames):
        try:
            d = await fr.evaluate(DUMP_PAGE_JS)
            if d["inputs"] or d["sends"]:
                print(f"  frame[{j}] url={fr.url[:50]} -> {d}")
        except Exception:
            pass

    await s.close()
    print("\nDONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
