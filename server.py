"""FastMCP entrypoint — tool registration ONLY (CLAUDE.md §3).

The six tools are thin shims over the src/* extraction + output layers.

Run locally:  .venv/bin/python server.py        (stdio transport)
Inspect:      npx @modelcontextprotocol/inspector .venv/bin/python server.py
"""

from __future__ import annotations

import anyio
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from src.browser.session import ensure_logged_in, get_session
from src.errors import NotLoggedInError
from src.extract.product import parse_product
from src.extract.reviews import parse_reviews
from src.extract.search import parse_search
from src.models import Product, Review, SearchResult
from src.output.xlsx_writer import write_xlsx

mcp = FastMCP("taobao-sourcing")


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
async def taobao_initialize_login() -> str:
    """Open the visible Chrome window and ensure login. The human scans the QR by phone.

    Call this first, once per session. Returns 'logged_in', or a 'login_required:
    ...' message instructing the human to scan the QR code in the Chrome window.
    """
    return await ensure_logged_in()


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def taobao_session_status() -> str:
    """Report login/session health. Read-only and idempotent."""
    s = get_session()
    if s.context is None:
        return "not_started: call taobao_initialize_login first (opens Chrome for QR login)."
    logged_in = await s.is_logged_in()
    note = (
        " — human_action_required (scan the QR / solve the slider in the Chrome window)"
        if s.human_action_required
        else ""
    )
    return f"status={s.status}; logged_in={logged_in}{note}"


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True))
async def taobao_search(keyword: str, page: int = 1, filters: dict | None = None) -> list[SearchResult]:
    """Search Taobao for `keyword` and return the result list for the human to pick from.

    Example: {"keyword": "tesla p100 16g", "page": 1}
    """
    return await parse_search(keyword, page_num=page, filters=filters)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def taobao_fetch_product(product_url_or_id: str) -> Product:
    """Fetch one product: title, shop, EVERY SKU variant + its price/stock, specs, images.

    Auto-ensures login first. Example: {"product_url_or_id": "736546459871"}
    """
    if await ensure_logged_in() != "logged_in":
        raise NotLoggedInError()
    return await parse_product(product_url_or_id)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def taobao_fetch_reviews(
    product_url_or_id: str,
    only_with_images: bool = False,
    most_recent_first: bool = True,
    max: int = 60,
) -> list[Review]:
    """Fetch recent reviews (raw Chinese), each tagged with the variant bought (sku_bought).

    Example: {"product_url_or_id": "736546459871", "only_with_images": true, "max": 40}
    """
    if await ensure_logged_in() != "logged_in":
        raise NotLoggedInError()
    return await parse_reviews(
        product_url_or_id,
        only_with_images=only_with_images,
        most_recent_first=most_recent_first,
        max_reviews=max,
    )


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
async def taobao_export_xlsx(products: list[Product], filename: str) -> str:
    """Write a 3-sheet (summary/variants/reviews) comparison workbook; return its path.

    Example: {"products": [...], "filename": "p100_compare.xlsx"}
    """
    path = await anyio.to_thread.run_sync(write_xlsx, products, filename)  # don't block the loop
    return f"Wrote {len(products)} product(s) to {path} — sheets: Summary, Variants, Reviews."


def main() -> None:
    """Run the stdio MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
