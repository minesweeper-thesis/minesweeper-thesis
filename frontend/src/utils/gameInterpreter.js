import { GameState, State } from "../utility";

export default function gameInterpreter(msg) {
    if (!msg || typeof msg !== "object") return [];

    const cmds = [];

    // 1. HINT
    if (msg.type === "hint" && Array.isArray(msg.safe_cells)) {
        if (msg.safe_cells.length > 0) {
            const [x, y] = msg.safe_cells[0];
            cmds.push({
                type: "SET_CELL",
                x,
                y,
                value: State.HINT
            });
        }
        return cmds;
    }

    // 2. REVEAL
    if (msg.type === "reveal") {
        if (Array.isArray(msg.revealed_cells)) {
            cmds.push({
                type: "REVEAL_CELLS",
                cells: msg.revealed_cells
            });
        }

        if (msg.game_status === "in_progress") {
            cmds.push({ type: "SET_GAME_STATE", value: GameState.IN_PROGRESS });
        }

        if (msg.game_status === "not_started") {
            cmds.push({ type: "SET_GAME_STATE", value: GameState.NOT_STARTED });
        }

        if (msg.game_status === "finished") {
            cmds.push({ type: "SET_GAME_STATE", value: GameState.IN_PROGRESS });
        }

        return cmds;
    }

    // 3. GAME_STATE
    if (msg.type === "game_state") {
        if (msg.difficulty_level) {
            cmds.push({
                type: "RESET_BOARD",
                rows: msg.difficulty_level.rows,
                cols: msg.difficulty_level.columns,
                mineCount: msg.difficulty_level.mine_count
            });
        }

        if (msg.start_field) {
            cmds.push({
                type: "SET_CELL",
                x: msg.start_field[0],
                y: msg.start_field[1],
                value: State.START_FIELD
            });
        }

        if (Array.isArray(msg.board)) {
            cmds.push({
                type: "SET_BOARD",
                board: msg.board
            });
        }

        // Status
        let gs = GameState.NOT_STARTED;

        if (msg.status === "in_progress") gs = GameState.IN_PROGRESS;
        if (msg.status === "finished") {
            if (msg.result === "win") gs = GameState.WON;
            else if (msg.result === "loss") gs = GameState.LOST;
        }

        cmds.push({ type: "SET_GAME_STATE", value: gs });
        return cmds;
    }

    // 4. GAME_OVER
    if (msg.type === "game_over") {
        const isWin = msg.game_status === "win";

        if (isWin) {
            cmds.push({
                type: "SET_BOARD",
                board: msg.full_board
            });
            cmds.push({ type: "SET_GAME_STATE", value: GameState.WON });
        } else {
            cmds.push({
                type: "REVEAL_MINES",
                board: msg.full_board,
                losingCell: msg.loss_cause?.cell
            });
            cmds.push({ type: "SET_GAME_STATE", value: GameState.LOST });
        }

        return cmds;
    }

    // 5. FLAG / REMOVE_FLAG
    if (msg.type === "flag" || msg.type === "remove_flag") {
        if (msg.game_status === "in_progress") {
            cmds.push({ type: "SET_GAME_STATE", value: GameState.IN_PROGRESS });
        }
        return cmds;
    }

    console.warn("[gameInterpreter] unknown message:", msg);
    return cmds;
}
