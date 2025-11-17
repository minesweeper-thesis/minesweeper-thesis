import { GameState, State } from "../utility";

export default function gameInterpreter(msg) {
    if (!msg || typeof msg !== "object") return [];

    const cmds = [];


    // LOSS
    if (msg.game_status === "loss") {
        if (msg.full_board) {
            cmds.push({
                type: "REVEAL_MINES",
                board: msg.full_board,
                losingCell: msg.loss_cause?.cell
            });
        }
        cmds.push({ type: "SET_GAME_STATE", value: GameState.LOST });
        return cmds;
    }

    // WIN
    if (msg.game_status === "win") {
        if (msg.full_board) {
            cmds.push({ type: "REVEAL_FULL_BOARD", board: msg.full_board });
        }
        cmds.push({ type: "SET_GAME_STATE", value: GameState.WON });
        return cmds;
    }

    // HINT
    if (Array.isArray(msg.safe_cells) && msg.safe_cells.length > 0) {
            cmds.push({
                type: "SET_CELL",
                x: msg.safe_cells[0][0],
                y: msg.safe_cells[0][1],
                value: State.HINT
            });

        return cmds;
    }

    // NORMAL MOVE
    if (msg.game_status === "in_progress" && Array.isArray(msg.revealed_cells) && msg.revealed_cells.length > 0) {
        cmds.push({
            type: "REVEAL_CELLS",
            cells: msg.revealed_cells
        });
        cmds.push({
            type: "SET_GAME_STATE",
            value: GameState.IN_PROGRESS
        });
        return cmds;
    }

    if (msg.full_board && Array.isArray(msg.full_board)) {
        cmds.push({ type: "REVEAL_FULL_BOARD", board: msg.full_board });
    }

    return cmds;
}
