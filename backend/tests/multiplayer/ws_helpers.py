import random
from typing import Any

import pytest
from httpx_ws import AsyncWebSocketSession


async def receive_type(
    ws: AsyncWebSocketSession, expected_type: str, *, timeout: float = 5.0
) -> dict[str, Any]:
    try:
        msg = await ws.receive_json(timeout=timeout)
        assert (
            msg.get("type") == expected_type
        ), f"expected type {expected_type}, got {msg}"
        return msg
    except TimeoutError:
        pytest.fail(f"Timeout {timeout}s waiting for {expected_type}")


def random_cell(
    *, rows: int, cols: int, exclude: tuple[int, int] | None = None
) -> tuple[int, int]:
    cells = [(x, y) for x in range(rows) for y in range(cols)]
    if exclude is not None:
        cells = [c for c in cells if c != exclude]
    return random.choice(cells)
