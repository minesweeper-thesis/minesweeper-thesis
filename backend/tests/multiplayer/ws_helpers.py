import random
from typing import Any, Iterable

import anyio


async def ws_receive_json(ws, *, timeout_s: float = 10.0) -> dict[str, Any]:
    with anyio.fail_after(timeout_s):
        return await ws.receive_json()


async def recv_until(
    ws,
    expected_types: set[str] | Iterable[str],
    *,
    max_messages: int = 50,
    timeout_s: float = 10.0,
) -> dict[str, Any]:
    expected = set(expected_types)
    seen: list[dict[str, Any]] = []

    for _ in range(max_messages):
        msg = await ws_receive_json(ws, timeout_s=timeout_s)
        seen.append(msg)
        if msg.get("type") in expected:
            return msg

    raise AssertionError(
        f"Did not receive one of {sorted(expected)} in {max_messages} messages. "
        f"Last message types: {[m.get('type') for m in seen[-10:]]}"
    )


async def recv_until_all(
    ws,
    expected_types: set[str] | Iterable[str],
    *,
    max_messages: int = 50,
    timeout_s: float = 10.0,
) -> list[dict[str, Any]]:
    expected = set(expected_types)
    remaining = set(expected)
    seen: list[dict[str, Any]] = []

    for _ in range(max_messages):
        msg = await ws_receive_json(ws, timeout_s=timeout_s)
        seen.append(msg)
        msg_type = msg.get("type")
        if msg_type in remaining:
            remaining.discard(msg_type)
            if not remaining:
                return seen

    raise AssertionError(
        f"Did not receive all of {sorted(expected)} in {max_messages} messages. "
        f"Missing: {sorted(remaining)}. "
        f"Last message types: {[m.get('type') for m in seen[-10:]]}"
    )


async def drain_ws(ws, *, max_messages: int = 50) -> None:
    for _ in range(max_messages):
        try:
            await ws_receive_json(ws, timeout_s=0.01)
        except TimeoutError:
            return


async def recv_round_ready(*, notif_ws, game_ws) -> None:
    try:
        await recv_until(notif_ws, {"round_ready"}, timeout_s=1.0)
    except TimeoutError:
        await recv_until(game_ws, {"round_ready"}, timeout_s=5.0)


def random_cell(
    *, rows: int, cols: int, exclude: tuple[int, int] | None = None
) -> tuple[int, int]:
    cells = [(x, y) for x in range(rows) for y in range(cols)]
    if exclude is not None:
        cells = [c for c in cells if c != exclude]
    return random.choice(cells)
