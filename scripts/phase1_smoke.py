"""Phase 1 smoke / gate check for the browser + session layer.

Usage (from project root, with the venv python):
  .venv/bin/python scripts/phase1_smoke.py          # quick: launch, webdriver check, login state, close
  .venv/bin/python scripts/phase1_smoke.py login    # interactive: open QR page and poll until you scan

The quick mode is non-interactive (proves real-Chrome launch + stealth). The
login mode opens the visible window and waits for you to scan the QR.
"""

from __future__ import annotations

import asyncio
import sys

from src.browser.session import BrowserSession


async def main(mode: str) -> None:
    s = BrowserSession()
    print(f"[1] launching real Chrome (channel={s.config.browser.channel!r}, "
          f"profile={s.config.browser.user_data_dir}) ...")
    page = await s.start()
    print("    LAUNCH_OK")

    wd = await page.evaluate("navigator.webdriver")
    print(f"[2] navigator.webdriver = {wd!r}  (gate wants false)")

    await page.goto("https://www.taobao.com", wait_until="domcontentloaded")
    print(f"[3] navigated: {page.url[:70]}")
    print(f"[4] is_logged_in = {await s.is_logged_in()}")

    if mode == "login":
        print("[5] Opening QR login — SCAN IT in the Chrome window with your Taobao app ...")
        result = await s.ensure_logged_in(timeout_s=240)
        print(f"    ensure_logged_in -> {result}")
        print(f"    final is_logged_in = {await s.is_logged_in()}")

    await s.close()
    print("CLOSED_OK")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "quick"))
