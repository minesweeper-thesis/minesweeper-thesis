export const State = {
    HINT: -6,
    START_FIELD: -5,
    FLAG: -4,
    NOT_REVEALED: -3,
    LOSING_MINE: -2,
    MINE: -1,
    _0: 0,
    _1: 1,
    _2 : 2,
    _3 : 3,
    _4 : 4,
    _5 : 5,
    _6 : 6,
    _7 : 7,
    _8 : 8
};

export const GameState = {
    LOST: 0,
    WON: 1,
    IN_PROGRESS: 2,
    NOT_STARTED: 3,
    PAUSED: 4,
};


export const BoardCommandRegistry = {
// reveal_many: cells = [[x,y,value], ...]
    reveal_many: ({ setBoard, payload }) => {
        setBoard(prev => {
            const newBoard = prev.map(r => [...r]);
            payload.cells.forEach(([x, y, val]) => {
                if (newBoard[x] && typeof newBoard[x][y] !== 'undefined') newBoard[x][y] = val;
            });
            return newBoard;
        });
    },


    reveal_one: ({ setBoard, payload }) => {
        const [x, y, val] = payload.cell || [];
        if (typeof x === 'undefined') return;
        setBoard(prev => {
            const newBoard = prev.map(r => [...r]);
            if (newBoard[x] && typeof newBoard[x][y] !== 'undefined') newBoard[x][y] = val;
            return newBoard;
        });
    },


// show_full_board: payload.board (2d array)
    show_full_board: ({ setBoard, payload }) => {
        setBoard(prev => {
// assume payload.board is correct shape
            return payload.board.map(r => r.map(c => c));
        });
    },


// highlight a cell (custom behaviour) -> we'll use a wrapper value object
    highlight_cell: ({ setBoard, payload }) => {
        const { x, y, meta } = payload;
        setBoard(prev => {
            const newBoard = prev.map(r => [...r]);
            if (newBoard[x] && typeof newBoard[x][y] !== 'undefined') {
// store highlight as object so UI can detect it (Square component can handle it)
                newBoard[x][y] = { __meta: 'HIGHLIGHT', meta };
            }
            return newBoard;
        });
    },


    set_cell: ({ setBoard, payload }) => {
        const { x, y, value } = payload;
        setBoard(prev => {
            const newBoard = prev.map(r => [...r]);
            if (newBoard[x] && typeof newBoard[x][y] !== 'undefined') newBoard[x][y] = value;
            return newBoard;
        });
    }
};


// fallback handler if command unknown
export function handleUnknownCommand({ command }) {
    console.warn('[Board] unknown command', command.type);
}