import glob
import json
import os
import uuid

import pytest

from backend.tests.singleplayer.helpers import (
    create_board_from_full_board_sync,
    create_game,
)

MESSAGES_DIR = os.path.join(os.path.dirname(__file__), "messages")
json_files = glob.glob(os.path.join(MESSAGES_DIR, "*.json"))


@pytest.mark.parametrize("json_file", json_files)
@pytest.mark.anyio
async def test_replay_game(client, auth, json_file):
    with open(json_file, "r") as f:
        messages = json.load(f)

    if not messages:
        pytest.skip("Empty messages file")

    full_board = None
    for msg in reversed(messages):
        if msg["type"] == "receive":
            data = json.loads(msg["data"])
            if "full_board" in data:
                full_board = data["full_board"]
                break

    if full_board is None:
        pytest.skip(f"No full_board found in {json_file}")

    first_message_data = json.loads(messages[0]["data"])
    if "start_field" not in first_message_data:
        pytest.skip("No start_field in first message")

    start_field = tuple(first_message_data["start_field"])

    board_id = create_board_from_full_board_sync(full_board, start_field)

    unique_id = uuid.uuid4().hex[:8]
    await auth(
        email=f"replay-{unique_id}@example.com",
        password="pw",
        nickname=f"replay_{unique_id}",
    )

    gameplay_id = await create_game(client, board_id=board_id)

    with client.websocket_connect(f"/api/game/single/{gameplay_id}") as ws:
        for i, message in enumerate(messages):
            msg_type = message["type"]
            msg_data = json.loads(message["data"])

            if msg_type == "send":
                ws.send_json(msg_data)
            elif msg_type == "receive":
                received_text = await ws.receive_text()
                received_data = json.loads(received_text)

                def clean_data(data):
                    d = data.copy()
                    if "board_id" in d:
                        del d["board_id"]
                    if "elapsed_time" in d:
                        del d["elapsed_time"]
                    return d

                cleaned_received = clean_data(received_data)
                cleaned_expected = clean_data(msg_data)

                assert (
                    cleaned_received == cleaned_expected
                ), f"Mismatch at message {i} in {os.path.basename(json_file)}:\nExpected: {cleaned_expected}\nGot:      {cleaned_received}"
