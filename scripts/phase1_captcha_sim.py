"""Phase 1 gate item 5: simulate a captcha/slider and prove the human-handoff.

Injects a fake slider element (#nc_1_n1z) onto a normal page so guard_captcha
detects a "block", sets human_action_required, and polls. We then remove the
element (simulating the human solving it) and confirm guard_captcha resumes.

Usage:  .venv/bin/python scripts/phase1_captcha_sim.py
"""

from __future__ import annotations

import asyncio

from src.browser.session import BrowserSession


async def main() -> None:
    s = BrowserSession()
    page = await s.start()
    await page.goto("https://www.taobao.com", wait_until="domcontentloaded")

    # Simulate a verification slider appearing.
    await page.evaluate(
        "var d=document.createElement('div'); d.id='nc_1_n1z'; "
        "d.textContent='请按住滑块拖动'; document.body.appendChild(d);"
    )
    print(f"[1] injected fake slider; _looks_blocked = {await s._looks_blocked(page)}  (want True)")

    # guard_captcha should detect it, flip human_action_required, and poll.
    guard = asyncio.create_task(s.guard_captcha(page, timeout_s=30, poll_s=1.0))
    await asyncio.sleep(2)
    print(f"[2] during block: human_action_required = {s.human_action_required}, status = {s.status!r}  (want True / 'human_action_required')")

    # Simulate the human solving it.
    await page.evaluate("var e=document.getElementById('nc_1_n1z'); if(e) e.remove();")
    await guard  # returns once the block clears
    print(f"[3] after clear: human_action_required = {s.human_action_required}, status = {s.status!r}  (want False / 'resumed')")

    await s.close()
    print("CAPTCHA_SIM_OK")


if __name__ == "__main__":
    asyncio.run(main())
