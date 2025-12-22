import asyncio
import random
from typing import Any

import pytest


async def receive_json(ws, *, timeout_s: float = 1.0) -> dict[str, Any]:
    try:
        async with asyncio.timeout(timeout_s):
            return await ws.receive_json()
    except asyncio.TimeoutError:
        pytest.fail(f"Timeout {timeout_s}s waiting for json")


async def receive_type(
    ws, expected_type: str, *, timeout_s: float = 1.0
) -> dict[str, Any]:
    try:
        async with asyncio.timeout(timeout_s):
            msg = await ws.receive_json()
            print(msg["type"], expected_type)
            assert (
                msg.get("type") == expected_type
            ), f"expected type {expected_type}, got {msg}"
            return msg
    except asyncio.TimeoutError:
        pytest.fail(f"Timeout {timeout_s}s waiting for {expected_type}")


def random_cell(
    *, rows: int, cols: int, exclude: tuple[int, int] | None = None
) -> tuple[int, int]:
    cells = [(x, y) for x in range(rows) for y in range(cols)]
    if exclude is not None:
        cells = [c for c in cells if c != exclude]
    return random.choice(cells)
