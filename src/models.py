"""Shared Pydantic data models for the Taobao sourcing server.

These are the contracts every layer agrees on (CLAUDE.md §5). They are the
single source of truth for shapes that cross module boundaries; only the
orchestrator edits this file.

Translation note: the server returns RAW CHINESE. ``Review.text_translated``
is filled by Claude in-context, never by the server.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SkuVariant(BaseModel):
    """One concrete purchasable variant (e.g. 颜色:黑色 + 尺寸:L) and its price."""

    sku_id: str
    properties: dict[str, str]      # e.g. {"颜色": "黑色", "尺寸": "L"}
    price: float | None             # CNY; None if sold out / unavailable
    stock: int | None
    available: bool


class Review(BaseModel):
    """A single customer review, kept in raw Chinese (Claude translates later)."""

    rating: int | None              # 1-5 if present
    text: str
    text_translated: str | None = None  # filled by Claude, NOT the server
    has_images: bool
    sku_bought: str | None          # the variant string the buyer chose, e.g. "黑色 L"
    date: str | None


class QAPair(BaseModel):
    """A buyer question and (optional) answer from the Q&A section."""

    question: str
    answer: str | None


class Product(BaseModel):
    """A fully-extracted product: variants (each priced), specs, images, reviews, Q&A."""

    product_id: str
    url: str
    title: str
    shop_name: str
    price_range: tuple[float, float] | None
    variants: list[SkuVariant] = Field(default_factory=list)
    specs: dict[str, str] = Field(default_factory=dict)
    image_urls: list[str] = Field(default_factory=list)
    reviews: list[Review] = Field(default_factory=list)
    reviews_by_variant: dict[str, list[Review]] = Field(default_factory=dict)  # sku label -> reviews
    qa: list[QAPair] = Field(default_factory=list)
    scraped_at: str
    subsidy_caveat: str | None = None   # set when the live "平台加补后" price differs from 优惠前


class SearchResult(BaseModel):
    """One row from a keyword search results page (lightweight; not a full Product)."""

    product_id: str
    url: str
    title: str
    price: float | None
    monthly_sales: int | None
    shop_name: str | None
    location: str | None
