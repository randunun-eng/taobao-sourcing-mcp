"""Capture a golden fixture for one product (Phase 2 prerequisite).

Navigates to item.taobao.com/item.htm?id=<id> with mtop interception attached,
human-paced and captcha-guarded, then saves to tests/fixtures/<id>/:
  - detail.json   (the captured product-detail mtop payload, if any)
  - reviews.json  (captured review payloads, if any)
  - page.html     (full rendered HTML — fallback source if data is SSR-embedded)
and prints every mtop endpoint seen + whether the HTML embeds skuBase/sku2info.

Usage:  .venv/bin/python scripts/capture_fixture.py 736546459871
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from src.browser.pacing import human_delay, human_scroll
from src.browser.session import BrowserSession
from src.extract.interceptor import MtopInterceptor


async def main(pid: str) -> None:
    s = BrowserSession()
    page = await s.start()
    if not await s.is_logged_in():
        print("WARNING: not logged in — run scripts/phase1_smoke.py login first")

    interc = MtopInterceptor()
    interc.attach(page)

    url = f"https://item.taobao.com/item.htm?id={pid}"
    print(f"[*] navigating {url}")
    await page.goto(url, wait_until="domcontentloaded")
    await s.guard_captcha(page)
    await human_scroll(page, 3)        # trigger lazy loads
    await human_delay(2.0, 3.0)
    await interc.settle(2.0)

    html = await page.content()
    title = await page.title()

    outdir = Path("tests/fixtures") / str(pid)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "page.html").write_text(html, encoding="utf-8")

    detail = interc.get_detail_json()
    reviews = interc.get_review_jsons()
    if detail:
        (outdir / "detail.json").write_text(json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")
    if reviews:
        (outdir / "reviews.json").write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[*] title: {title[:70]}")
    print(f"[*] mtop endpoints seen ({len(set(interc.all_endpoints()))} unique):")
    for ep in sorted(set(interc.all_endpoints())):
        print(f"      {ep}")
    print(f"[*] detail.json captured via XHR: {bool(detail)}")
    print(f"[*] review payloads captured: {len(reviews)}")
    print(f"[*] HTML embeds skuBase: {'skuBase' in html} | sku2info: {'sku2info' in html} | size(KB): {len(html)//1024}")
    print(f"[*] saved to {outdir}")

    await s.close()
    print("DONE")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: capture_fixture.py <product_id>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
