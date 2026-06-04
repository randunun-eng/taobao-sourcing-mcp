"""Live smoke for seller comms — READ + PREVIEW only (sends NOTHING).

Validates read_messages (list + open a thread) and send_reply's preview path
(confirm=False). The real send is never exercised here — that needs the human's
per-message confirm. Run: .venv/bin/python scripts/messages_smoke.py [seller]
"""

from __future__ import annotations

import asyncio
import sys

from src.browser.session import ensure_logged_in, get_session
from src.extract.messages import read_messages, send_reply


async def main(seller: str) -> None:
    status = await ensure_logged_in()
    print("login:", status)
    if status != "logged_in":
        print("Not logged in — scan the QR in Chrome, then re-run.")
        return

    convs = await read_messages(max_conversations=12)
    print(f"\n[1] {len(convs)} conversations:")
    for c in convs:
        print(f"    • {c.seller}  ({c.time})  — {c.last_message[:36]}")

    if convs:
        target = next((c.seller for c in convs if seller in c.seller), convs[0].seller)
        print(f"\n[2] opening thread: {target}")
        opened = await read_messages(max_conversations=12, open_seller=target)
        t = next((c for c in opened if c.seller == target), None)
        if t:
            for m in t.messages[-8:]:
                who = "我" if m.is_self else "卖家"
                print(f"    [{who}] {m.text[:48]}")

        # preview ONLY — confirm defaults False, so nothing is sent
        print("\n[3] send_reply PREVIEW (no send):")
        print(await send_reply(target, "请问这款现在还有现货吗？", confirm=False))

    await get_session().close()
    print("\nDONE — nothing was sent.")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "南京海雀显卡"))
