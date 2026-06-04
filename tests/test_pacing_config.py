"""Tests for config loading and the anti-detection pacing/RateLimiter (§7)."""

from __future__ import annotations

import asyncio

from src.browser.pacing import RateLimiter, human_delay
from src.config import load_config


def test_config_defaults_on_missing_file(tmp_path):
    cfg = load_config(str(tmp_path / "does_not_exist.toml"))
    assert cfg.browser.channel == "chrome"
    assert cfg.browser.headless is False
    assert cfg.pacing.max_products_per_minute == 6
    assert cfg.limits.max_reviews == 60
    assert cfg.output.dir == "./output"


def test_config_ignores_unknown_keys(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text('[browser]\nchannel = "chrome"\nbogus_key = "x"\n', encoding="utf-8")
    cfg = load_config(str(p))  # _filter must drop bogus_key without raising
    assert cfg.browser.channel == "chrome"


def test_rate_limiter_records_under_cap():
    rl = RateLimiter(max_per_minute=5)

    async def run():
        for _ in range(3):
            await rl.acquire()

    asyncio.run(run())
    assert len(rl._timestamps) == 3   # under cap → all recorded, no sleep


def test_rate_limiter_disabled():
    rl = RateLimiter(max_per_minute=0)
    asyncio.run(rl.acquire())         # disabled → returns immediately
    assert rl._timestamps == []


def test_human_delay_swaps_min_max():
    # hi < lo must be swapped, not raise (tiny values keep the test fast)
    asyncio.run(human_delay(0.002, 0.001))
