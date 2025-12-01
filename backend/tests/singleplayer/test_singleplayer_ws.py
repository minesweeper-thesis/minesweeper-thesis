import asyncio
import json
import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.tests.utils.auth_helpers import register_and_login


def _create_board_in_db(minefields, start_field, rows=5, columns=5):
    """Create a Board in the test DB using repository inside an asyncio run.

    Returns the board id (as str).
    """
    from backend.core.board import Board, DifficultyLevel, GenerationSettings
    from backend.db.db import async_session_maker
    from backend.repositories.board_repo import BoardRepository

    async def _add():
        async with async_session_maker() as session:
            repo = BoardRepository(session)
            # Try to reuse an existing board with the same difficulty and
            # minefields to avoid UNIQUE constraint violations when the
            # same board is created multiple times across the test suite.
            difficulty = DifficultyLevel(
                rows=rows, columns=columns, mine_count=len(minefields)
            )
            try:
                existing = await repo.get_board(
                    difficulty_level=difficulty, minefields=minefields
                )
                return str(existing.id)
            except Exception:
                # Board not found -> create it
                board = Board(
                    id=uuid.uuid4(),
                    difficulty_level=difficulty,
                    minefields=minefields,
                    start_field=start_field,
                    generation_settings=GenerationSettings(
                        type="random", settings=None, difficulty_level=difficulty
                    ),
                )
                await repo.add_board(board)
                return str(board.id)

    return asyncio.run(_add())


def receive_json(ws):
    return json.loads(ws.receive_text())


def test_singleplayer_all_ws_messages():
    # Build a known 5x5 board that is solvable and deterministic
    # Mines chosen so start_field is safe
    mines = [(0, 0), (2, 2), (4, 4)]
    start = (0, 1)

    # Create a fresh client and user
    with TestClient(app, base_url="https://testserver") as client:
        user = register_and_login(
            client, f"sp+{uuid.uuid4().hex}@example.com", nickname="sp"
        )

        # Add board to DB
        board_id = _create_board_in_db(mines, start, rows=5, columns=5)

        # Start gameplay specifying board_id
        payload = {"board_id": board_id, "mode": "normal"}
        r = client.post("/api/game/single", json=payload)
        assert r.status_code == 200
        gameplay_id = r.json()["gameplay_id"]

        seen = set()

        # Connect to singleplayer websocket and exercise actions
        with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
            # initial game_state should be sent on load
            msg = receive_json(ws)
            assert msg.get("type") == "game_state"
            seen.add("game_state")

            # Request a hint
            ws.send_json({"type": "hint"})
            msg = receive_json(ws)
            assert msg.get("type") == "hint"
            seen.add("hint")

            # pick a safe cell from hint
            safe_cells = msg.get("safe_cells") or []
            assert len(safe_cells) > 0
            safe = safe_cells[0]

            # Flag a known mine to get flag response
            mine = mines[0]
            ws.send_json({"type": "flag", "cell": [mine[0], mine[1]]})
            msg = receive_json(ws)
            assert msg.get("type") == "flag"
            seen.add("flag")

            # Remove the flag
            ws.send_json({"type": "remove_flag", "cell": [mine[0], mine[1]]})
            msg = receive_json(ws)
            assert msg.get("type") == "remove_flag"
            seen.add("remove_flag")

            # Reveal a safe cell (expect reveal or possibly game_over if board trivial)
            ws.send_json({"type": "reveal_one", "cell": [safe[0], safe[1]]})
            msg = receive_json(ws)
            mtype = msg.get("type")
            assert mtype in ("reveal", "game_over")
            seen.add(mtype)

            # If we got only reveal so far, trigger a loss by revealing a mine
            if "game_over" not in seen:
                ws.send_json({"type": "reveal_one", "cell": [mines[1][0], mines[1][1]]})
                msg = receive_json(ws)
                assert msg.get("type") == "game_over"
                seen.add("game_over")

        # Verify we observed all expected message types
        expected = {"game_state", "hint", "flag", "remove_flag", "reveal", "game_over"}

        # It's acceptable if both 'reveal' and 'game_over' were observed, but the test
        # should at least have seen each message type at least once across the flow.
        assert expected.issubset(seen) or ("reveal" in seen and "game_over" in seen)
