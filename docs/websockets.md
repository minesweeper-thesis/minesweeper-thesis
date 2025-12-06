## 1. Notifications — `GET /ws` (WebSocket)

Real-time updates on lobby state, invitations, and player connections.

### Server → Client Messages

#### `current_lobby`

**Purpose:** Sync current lobby membership.
**Triggered:** On connect, when lobby state changes (user joins/leaves/config updated).

```typescript
{
  type: "current_lobby",
  lobby: null | {
    id: "550e8400-e29b-41d4-a716-446655440000",
    host: {
      id: "550e8400-e29b-41d4-a716-446655440001",
      nickname: "alice",
      email: "alice@example.com",
      avatar_url: "url" | null
    },
    users: [{ id: "uuid", nickname: "string", email: "string", avatar_url: "url" | null }],
    game_config: {
      generator: {
        type: "random" | "ml",
        settings: {} | null
      },
      difficulty_level: { rows: 10, columns: 10, mine_count: 15 },
      game_mode: "normal" | "hardcore"
    }
  }
}
```

#### `pending_invitations`

**Purpose:** List active pending invitations for current user.
**Triggered:** On client request or when invitations list changes.

```typescript
{
  type: "pending_invitations",
  invitations: [
    {
      type: "invitation",
      id: "550e8400-e29b-41d4-a716-446655440000",
      lobby: {
        id: "550e8400-e29b-41d4-a716-446655440000",
        host: { id: "uuid", nickname: "alice", email: "alice@example.com", avatar_url: "url" | null },
        game_config: {
          generator: {
            type: "random" | "ml",
            settings: {} | null
          },
          difficulty_level: { rows: 10, columns: 10, mine_count: 15 },
          game_mode: "normal" | "hardcore"
        }
      }
    }
  ]
}
```

#### `invitation_response`

**Purpose:** Notify about acceptance/rejection of an invitation.
**Triggered:** When someone accepts or rejects an invitation.

```typescript
{
  type: "invitation_response",
  invitation: {
    type: "invitation",
    id: "550e8400-e29b-41d4-a716-446655440000",
    lobby: {
      id: "550e8400-e29b-41d4-a716-446655440000",
      host: { id: "uuid", nickname: "alice", email: "alice@example.com", avatar_url: "url" | null },
      game_config: {
        generator: {
          type: "random" | "ml",
          settings: {} | null
        },
        difficulty_level: { rows: 10, columns: 10, mine_count: 15 },
        game_mode: "normal" | "hardcore"
      }
    }
  },
  response: "accepted" | "rejected"
}
```

#### `user_connection_status`

**Purpose:** Notify when a player connects/disconnects from lobby.
**Triggered:** User joins or leaves a lobby.

```typescript
{
  type: "user_connection_status",
  lobby_id: "550e8400-e29b-41d4-a716-446655440000",
  user: { id: "uuid", nickname: "bob", email: "bob@example.com", avatar_url: "url" | null },
  status: "connected" | "disconnected"
}
```

### Client → Server Messages

#### `pending_invitations` (request)

**Purpose:** Request refresh of pending invitations list.
**Response:** `pending_invitations` message (server → client).

```typescript
{
  type: "pending_invitations";
}
```

---

## 2. Singleplayer Game — `GET /game/single/{gameplay_id}` (WebSocket)

Real-time game session for single player.

### Client → Server Messages

#### `reveal_one`

**Purpose:** Reveal a single cell.
**Response:** `reveal` message with updated cell state.

```typescript
{
  type: "reveal_one",
  cell: [3, 5]
}
```

#### `reveal_many`

**Purpose:** Reveal cluster of cells adjacent to numbered cell.
**Response:** `reveal` message with updated cell states.

```typescript
{
  type: "reveal_many",
  cell: [3, 5]
}
```

#### `flag`

**Purpose:** Mark cell as flagged (suspected mine).
**Response:** `flag` message with current game status.

```typescript
{
  type: "flag",
  cell: [3, 5]
}
```

#### `remove_flag`

**Purpose:** Unmark cell.
**Response:** `remove_flag` message with current game status.

```typescript
{
  type: "remove_flag",
  cell: [3, 5]
}
```

#### `hint`

**Purpose:** Request AI-computed list of safe cells.
**Response:** `hint` message with safe cell list.

```typescript
{
  type: "hint";
}
```

#### `get_state`

**Purpose:** Fetch current game board state (e.g., after reconnect).
**Response:** `game_state` message with full board snapshot.

```typescript
{
  type: "get_state";
}
```

### Server → Client Messages

#### `reveal`

**Purpose:** Confirm cell reveal; return newly revealed cells and current game status.
**Triggered:** After `reveal_one` or `reveal_many`.

```typescript
{
  type: "reveal",
  revealed_cells: [[3, 5, 0], [3, 6, 2], [4, 5, 1]],
  game_status: "not_started" | "in_progress" | "finished"
}
```

Note: cell value is `0` to `8` (safe), `-2` (LOSING_MINE), `-3` (NOT_REVEALED), `-4` (FLAG), `-5` (START_FIELD).

#### `game_state`

**Purpose:** Full game state snapshot.
**Triggered:** After `get_state` request, on initial board send, or on state change.

```typescript
{
  type: "game_state",
  board_id: "550e8400-e29b-41d4-a716-446655440000",
  status: "not_started" | "in_progress" | "finished",
  result: "win" | "loss" | null,
  board: null | [[0, 1, 2], [3, -4, 5]],
  difficulty_level: { rows: 10, columns: 10, mine_count: 15 },
  elapsed_time: 12.34,
  loss_cause: null | { type: "mine_clicked" | "unsafe_move", cell: [5, 7] },
  start_field: [3, 3]
}
```

#### `flag`

**Purpose:** Confirm flag action.
**Triggered:** After `flag` request.

```typescript
{
  type: "flag",
  game_status: "not_started" | "in_progress" | "finished"
}
```

#### `remove_flag`

**Purpose:** Confirm unflag action.
**Triggered:** After `remove_flag` request.

```typescript
{
  type: "remove_flag",
  game_status: "not_started" | "in_progress" | "finished"
}
```

#### `game_over`

**Purpose:** Notify game end (win or loss).
**Triggered:** Once when game concludes.

```typescript
{
  type: "game_over",
  game_status: "finished",
  result: "win" | "loss",
  full_board: [[0, 1, 2], [1, 2, 1]],
  elapsed_time: 120.45,
  loss_cause: null | { type: "mine_clicked" | "unsafe_move" | "hardcore", cell: [5, 7] }
}
```

#### `hint`

**Purpose:** Return list of safe cells to reveal.
**Triggered:** After `hint` request.

```typescript
{
  type: "hint",
  safe_cells: [[3, 4], [3, 5], [4, 4]]
}
```
