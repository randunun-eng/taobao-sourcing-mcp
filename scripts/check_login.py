"""Confirm the persistent Chrome profile is still logged in (and validate the auth-cookie check)."""

from __future__ import annotations

import asyncio

from src.browser.session import _AUTH_COOKIE_NAMES, BrowserSession


async def main() -> None:
    s = BrowserSession()
    await s.start()
    cookies = await s.context.cookies()
    names = {c.get("name") for c in cookies}
    print("is_logged_in:", await s.is_logged_in())
    print("auth cookies present:", [n for n in _AUTH_COOKIE_NAMES if n in names])
    print("nick cookies (tracknick/lgc):", [n for n in ("tracknick", "lgc") if n in names])
    await s.close()


if __name__ == "__main__":
    asyncio.run(main())
