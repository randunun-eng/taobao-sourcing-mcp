"""Capture the review XHR shape for a product (Phase 2c recon).

Navigates the product, scrolls to the reviews, tries the reviews tab, and prints
every mtop endpoint seen + any review-ish payload (by name fragment), saving raw
bodies to tests/fixtures/<id>/reviews_raw.json for offline parser development.

Usage:  .venv/bin/python scripts/capture_reviews.py 736546459871
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from src.browser.pacing import human_delay, human_scroll
from src.browser.session import BrowserSession
from src.extract.interceptor import MtopInterceptor


async def _try_click_reviews(page) -> str:
    for label in ("宝贝评价", "累计评价", "商品评价", "评价"):
        try:
            loc = page.get_by_text(label, exact=False).first
            if await loc.count() > 0:
                await loc.scroll_into_view_if_needed(timeout=3000)
                await loc.click(timeout=3000)
                return f"clicked {label!r}"
        except Exception:
            continue
    return "no reviews tab clicked (relying on scroll)"


async def main(pid: str) -> None:
    s = BrowserSession()
    page = await s.start()
    interc = MtopInterceptor()
    interc.attach(page)

    url = f"https://item.taobao.com/item.htm?id={pid}"
    print(f"[*] navigating {url}")
    await page.goto(url, wait_until="domcontentloaded")
    await s.guard_captcha(page)

    for _ in range(5):
        await human_scroll(page, 2)
        await human_delay(1.0, 1.8)
    print("[*]", await _try_click_reviews(page))
    for _ in range(4):
        await human_scroll(page, 2)
        await human_delay(1.0, 1.8)
    await interc.settle(2.5)

    eps = sorted(set(interc.all_endpoints()))
    print(f"[*] {len(eps)} unique mtop endpoints:")
    for e in eps:
        print("      ", e)

    review_ish = interc.find_bodies("rate", "review", "comment", "feed")
    print(f"[*] review-ish payloads: {len(review_ish)} -> {[n for n, _ in review_ish]}")

    html = await page.content()
    print(f"[*] DOM markers: rateContent={'rateContent' in html} feedback={'feedback' in html} Comment--={'Comment--' in html}")

    d = Path("tests/fixtures") / pid
    d.mkdir(parents=True, exist_ok=True)
    if review_ish:
        (d / "reviews_raw.json").write_text(
            json.dumps([{"endpoint": n, "body": b} for n, b in review_ish], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[*] saved {d/'reviews_raw.json'}")
    else:
        # save all endpoint bodies' keys to help locate reviews
        print("[*] no review-ish endpoint matched; all endpoints listed above")

    await s.close()
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "736546459871"))
