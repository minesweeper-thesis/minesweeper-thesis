import React, {
    useEffect,
    useState,
    forwardRef,
    useImperativeHandle
} from "react";
import Square from "./Square";
import { GameState, State } from "../utility";
import "../styles/board.css";

const Board = forwardRef(function Board(
    { boardData, sendCommand, setGameState, setMines, startField, socket = null, mode = "single", countdownTime = 0 },
    ref
) {
    const [board, setBoard] = useState(null);
    const [timeLeft, setTimeLeft] = useState(countdownTime);

    // Countdown effect for multi mode
    useEffect(() => {
        if (mode !== "multi") return;

        setTimeLeft(countdownTime);
        const interval = setInterval(() => {
            setTimeLeft(prev => Math.max(prev - 1, 0));
        }, 1000);

        return () => clearInterval(interval);
    }, [countdownTime, mode]);

    // Initialize board and mines
    useEffect(() => {
        setBoard(null);
        if (boardData?.mineCount) setMines(boardData);
    }, [boardData?.rows, boardData?.cols, boardData?.mineCount, setMines]);

    // Set start field
    useEffect(() => {
        if (startField && startField[0] != null) {
            setBoard(prev => {
                const newB = prev?.map(r => [...r]) || [];
                newB[startField[0]][startField[1]] = State.START_FIELD;
                return newB;
            });
        }
    }, [startField]);

    // --- Existing Board Functions ---

    const setCell = (x, y, newValue) => {
        setBoard(prevBoard => {
            const newBoard = prevBoard.map(row => [...row]);
            if (newBoard[x] && typeof newBoard[x][y] !== "undefined") {
                newBoard[x][y] = newValue;
            }
            return newBoard;
        });
    };

    const revealMines = (revealed_board, red_mine) => {
        setBoard(prevBoard => {
            const newBoard = prevBoard.map(row => [...row]);
            for (let i = 0; i < revealed_board.length; i++) {
                for (let j = 0; j < revealed_board[i].length; j++) {
                    if (red_mine && i === red_mine[0] && j === red_mine[1]) {
                        newBoard[i][j] = State.LOSING_MINE;
                    } else if (revealed_board[i][j] === State.MINE && newBoard[i][j] !== State.FLAG) {
                        newBoard[i][j] = State.MINE;
                    }
                }
            }
            return newBoard;
        });
    };

    const revealBoard = (revealed_board) => {
        setBoard(prevBoard => {
            const newBoard = prevBoard.map(row => [...row]);
            for (let i = 0; i < revealed_board.length; i++) {
                for (let j = 0; j < revealed_board[i].length; j++) {
                    if (revealed_board[i][j] !== -1) {
                        newBoard[i][j] = revealed_board[i][j];
                    }
                }
            }

            if (startField) {
                for (let i = 0; i < newBoard.length; i++) {
                    for (let j = 0; j < newBoard[i].length; j++) {
                        if (newBoard[i][j] === State.START_FIELD && (i !== startField[0] || j !== startField[1])) {
                            newBoard[i][j] = State.NOT_REVEALED;
                        }
                    }
                }
            }

            return newBoard;
        });
    };

    const applyRevealCells = (cells) => {
        setBoard(prevBoard => {
            const newBoard = prevBoard.map(row => [...row]);
            cells.forEach(([x, y, state]) => {
                if (newBoard[x] && typeof newBoard[x][y] !== "undefined") {
                    newBoard[x][y] = state;
                }
            });

            if (startField && newBoard[startField[0]] && newBoard[startField[0]][startField[1]] === State.START_FIELD) {
                newBoard[startField[0]][startField[1]] = State.NOT_REVEALED;
            }

            return newBoard;
        });
    };

    const handleCommand = (cmd) => {
        if (!cmd || !cmd.type) return;

        switch (cmd.type) {
            case "REVEAL_CELLS":
                if (Array.isArray(cmd.cells)) applyRevealCells(cmd.cells);
                break;
            case "SET_CELL":
                setCell(cmd.x, cmd.y, cmd.value);
                break;
            case "REVEAL_MINES":
                revealMines(cmd.board, cmd.losingCell);
                break;
            case "REVEAL_FULL_BOARD":
                revealBoard(cmd.board);
                break;
            case "SET_GAME_STATE":
                setGameState(cmd.value);
                break;
            case "SET_BOARD":
                setBoard(cmd.board);
                break;
            case "RESET_BOARD":
                setBoard(Array.from({ length: cmd.rows }, () => Array(cmd.cols).fill(State.NOT_REVEALED)));
                setMines(cmd.mineCount ?? 0);
                break;
            default:
                console.warn("[Board] unknown command:", cmd.type);
        }
    };

    useImperativeHandle(ref, () => ({
        dispatchCommand: (cmdOrArray) => {
            if (!cmdOrArray) return;
            if (Array.isArray(cmdOrArray)) {
                cmdOrArray.forEach(c => handleCommand(c));
            } else {
                handleCommand(cmdOrArray);
            }
        }
    }), [board]);

    // Click handlers
    const handleClick = (e, x, y) => {
        e.preventDefault();
        if ((e.buttons === 2 && e.button === 0) || (e.buttons === 1 && e.button === 2)) {
            handleMultiClick(x, y);
        } else if (e.button === 0) {
            handleLeftClick(x, y);
        } else if (e.button === 2) {
            handleRightClick(x, y);
        }
    };

    const handleLeftClick = (x, y) => {
        if (socket && socket.readyState !== WebSocket.OPEN) return;
        const current = board[x][y];
        if ([State.START_FIELD, State.NOT_REVEALED, State.HINT].includes(current)) {
            sendCommand({ type: "reveal_one", cell: [x, y] });
        }
    };

    const handleRightClick = (x, y) => {
        if (socket && socket.readyState !== WebSocket.OPEN) return;

        setBoard(prev => {
            const newBoard = prev.map(row => [...row]);
            const current = newBoard[x][y];

            if (current === State.NOT_REVEALED) {
                newBoard[x][y] = State.FLAG;
                setMines(prev => prev - 1);
                sendCommand({ type: "flag", cell: [x, y] });
            } else if (current === State.FLAG) {
                newBoard[x][y] = State.NOT_REVEALED;
                setMines(prev => prev + 1);
                sendCommand({ type: "remove_flag", cell: [x, y] });
            }

            return newBoard;
        });
    };

    const handleMultiClick = (x, y) => {
        const value = board[x][y];
        if (value < State._0 || value > State._8) return;
        sendCommand({ type: "reveal_many", cell: [x, y] });
    };

    // --- Render ---
    return (
        <div className="board" onContextMenu={(e) => e.preventDefault()}>
            {mode === "multi" && !board ? (
                <div className="flex flex-col items-center justify-center h-full text-text-primary">
                    <div className="text-6xl font-bold animate-pulse text-accent-primary">{timeLeft}</div>
                    <div className="text-lg opacity-80">Game starting...</div>
                </div>
            ) : !board ? (
                <div className="flex flex-col items-center justify-center h-full text-text-primary">
                    <div className="relative w-10 h-10 mb-3 mt-20">
                        <div className="absolute inset-0 border-4 border-border-primary rounded-full opacity-20"></div>
                        <div className="absolute inset-0 border-4 border-accent-primary rounded-full border-t-transparent animate-spin"></div>
                    </div>
                    <p className="text-lg font-medium animate-pulse">
                        Generating Board<span className="dots"></span>
                    </p>
                </div>
            ) : (
                board.map((row, i) => (
                    <div key={i} className="board-row">
                        {row.map((val, j) => (
                            <Square key={`${i}-${j}`} value={val} onClick={(e) => handleClick(e, i, j)} />
                        ))}
                    </div>
                ))
            )}
        </div>
    );
});

export default Board;
