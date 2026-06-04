"""Add-to-cart staging — gated, reversible (CLAUDE.md §0 scope item 2).

The cart is the hand-off to the China agent, who checks out (picks the forwarder
address + pays). This module ONLY clicks 加入购物车 — it NEVER touches 领券购买/立即购买,
never selects an address, never pays. Default is a dry preview; confirm=True actually adds.
"""

from __future__ import annotations

from src.errors import CaptchaError, ProductNotFoundError  # noqa: F401

_ADD_BTN = "加入购物车"
_SUCCESS_RE = r"加入购物车成功|已加入购物车|成功加入|添加成功|加购成功"


async def add_to_cart(
    product_url_or_id: str,
    options: list[str] | None = None,
    qty: int = 1,
    confirm: bool = False,
) -> str:
    """Stage one product+variant+qty into the cart. Preview unless confirm=True.

    options = one option VALUE per group (e.g. ["P100 质保3年 以换代修"] or ["黑色","L"]).
    Reversible (cart only); never buys, never picks an address.
    """
    from src.browser.pacing import human_delay, human_scroll
    from src.browser.session import get_session
    from src.extract.product import _to_product_id, parse_product_html

    options = options or []
    pid = _to_product_id(product_url_or_id)
    session = get_session()
    page = await session.start()
    url = f"https://item.taobao.com/item.htm?id={pid}"
    await page.goto(url, wait_until="domcontentloaded")
    await session.guard_captcha(page)
    await human_scroll(page, 2)
    await human_delay(1.5, 2.5)

    product = parse_product_html(await page.content(), pid, url)
    group_names = {k for v in product.variants for k in v.properties}
    if product.variants and group_names and not options:
        choices = sorted({" / ".join(v.properties.values()) for v in product.variants})
        return ("Specify the variant to add via `options` (one value per group). Available: "
                + "; ".join(choices[:8]))

    # select each option (exact chip match → real selection)
    selected: list[str] = []
    for value in options:
        loc = page.get_by_text(value, exact=True).first
        if await loc.count() == 0:
            loc = page.get_by_text(value[:14], exact=False).first
        try:
            await loc.scroll_into_view_if_needed(timeout=3000)
            await loc.click(timeout=4000)
            selected.append(value)
        except Exception as exc:
            raise ProductNotFoundError(f"could not select option {value!r} on product {pid}: {exc}")
        await human_delay(0.6, 1.2)

    if qty and int(qty) != 1:
        try:
            await page.locator('input[class*="countValue"]').first.fill(str(int(qty)), timeout=3000)
            await human_delay(0.4, 0.9)
        except Exception:
            pass

    label = " / ".join(selected) or (product.title[:40] or pid)
    if not confirm:
        return (f"PREVIEW — ready to add: {product.title[:44]} · variant: {label} · qty {qty}. "
                f"Re-call with confirm=True to add it. (Cart only — never buys or picks an address.)")

    try:
        btn = page.get_by_text(_ADD_BTN, exact=True).first
        await btn.scroll_into_view_if_needed(timeout=3000)
        await btn.click(timeout=5000)
    except Exception as exc:
        raise ProductNotFoundError(f"could not click 加入购物车 on product {pid}: {exc}")
    await human_delay(1.5, 2.5)
    await session.guard_captcha(page)  # adding can trigger a slider

    import re
    added = bool(re.search(_SUCCESS_RE, await page.evaluate("() => document.body ? document.body.innerText : ''")))
    head = "added to cart" if added else "clicked 加入购物车 (no success toast seen — check the cart)"
    return f"{head}: {product.title[:44]} · {label} · qty {qty}."
