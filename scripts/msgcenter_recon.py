"""Recon the buyer MESSAGE CENTER (消息) — the surface for read_messages + send_reply.
READ-ONLY: navigates, dumps conversation-list + thread + input structure. Sends nothing."""

from __future__ import annotations

import asyncio

from src.browser.pacing import human_delay
from src.browser.session import BrowserSession

# Candidate entry points (try in order until one renders a chat-like UI).
CANDIDATES = [
    "https://www.taobao.com",                # find the 消息 nav entry
    "https://msg.taobao.com",
    "https://amos.alicdn.com/msg.aw",
]

FIND_MSG_LINK_JS = r"""() => {
  const norm = s => (s||'').replace(/\s+/g,'').trim();
  const out = [];
  for (const e of document.querySelectorAll('a,div,span,li')) {
    const t = norm(e.innerText);
    if (t && t.length < 6 && (t === '消息' || t.includes('消息') || t.includes('旺旺'))) {
      out.push({ t, tag: e.tagName, href: (e.getAttribute && e.getAttribute('href'))||'',
                 cls: (e.className||'').toString().slice(0,34) });
    }
  }
  const seen=new Set(); const u=[];
  for (const h of out){const k=h.t+h.href; if(!seen.has(k)){seen.add(k); u.push(h);}}
  return u.slice(0,10);
}"""

STRUCT_JS = r"""() => {
  const norm = s => (s||'').replace(/\s+/g,'').trim();
  const inputs = [...document.querySelectorAll('textarea,div[contenteditable=true],input[type=text]')]
    .map(e => ({ tag:e.tagName, editable:e.getAttribute('contenteditable')||'',
                 ph:e.getAttribute('placeholder')||'', cls:(e.className||'').toString().slice(0,44) })).slice(0,8);
  const sends = [...document.querySelectorAll('a,button,div,span')]
    .filter(e => { const t=norm(e.innerText); return t && t.length<6 && t.includes('发送'); })
    .map(e => ({ t:norm(e.innerText), tag:e.tagName, cls:(e.className||'').toString().slice(0,40) })).slice(0,5);
  // conversation-list-ish rows: clickable items with a short name + maybe unread dot
  const convs = [...document.querySelectorAll('[class*="conv"],[class*="session"],[class*="contact"],[class*="list-item"]')]
    .map(e => ({ cls:(e.className||'').toString().slice(0,40), t: norm(e.innerText).slice(0,30) }))
    .filter(x => x.t).slice(0,8);
  return { url: location.href.slice(0,70), inputs, sends, convs, bodyLen:(document.body.innerText||'').length };
}"""


async def main() -> None:
    s = BrowserSession()
    page = await s.start()

    # 1) homepage → find the 消息 entry
    await page.goto("https://www.taobao.com", wait_until="domcontentloaded")
    await s.guard_captcha(page)
    await human_delay(2.0, 3.0)
    print("消息/旺旺 links on homepage:")
    links = await page.evaluate(FIND_MSG_LINK_JS)
    for h in links:
        print("  ", h)

    before = set(p.url for p in s.context.pages)
    # try clicking the 消息 entry
    clicked = False
    try:
        await page.get_by_text("消息", exact=True).first.click(timeout=4000)
        clicked = True
    except Exception as exc:
        print("  click 消息 failed:", str(exc)[:80])
    await human_delay(3.0, 4.5)

    pages = s.context.pages
    print(f"\nafter click: {len(pages)} page(s)")
    for i, p in enumerate(pages):
        new = "  (NEW)" if p.url not in before else ""
        print(f"  page[{i}] {p.url[:72]}{new} frames={len(p.frames)}")

    target = pages[-1]
    try:
        await target.bring_to_front()
        await human_delay(2.5, 3.5)
    except Exception:
        pass
    print("\n--- message UI structure (newest page top-level) ---")
    try:
        print("  ", await target.evaluate(STRUCT_JS))
    except Exception as exc:
        print("   err:", str(exc)[:80])
    for j, fr in enumerate(target.frames):
        try:
            d = await fr.evaluate(STRUCT_JS)
            if d["inputs"] or d["sends"] or d["convs"]:
                print(f"  frame[{j}] -> {d}")
        except Exception:
            pass

    await s.close()
    print("\nDONE; clicked=", clicked)


if __name__ == "__main__":
    asyncio.run(main())
