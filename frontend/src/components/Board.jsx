import { useEffect, useState } from "react";
import "../styles/board.css";
import { GameState, State } from "../utility";
import Square from "./Square";

export default function Board({ socket, boardData, setGameState, setMines, startField }) {
    const [board, setBoard] = useState(
        Array.from({ length: boardData.rows }, () =>
            Array(boardData.cols).fill(State.NOT_REVEALED)
        )
    );

    useEffect(() => {
        setBoard(
            Array.from({ length: boardData.rows }, () =>
                Array(boardData.cols).fill(State.NOT_REVEALED)
            )
        );
        setMines(boardData.mineCount);
    }, []);


    useEffect(() => {
        if (startField && startField[0]) {
            setBoard(prevBoard => {
                const newBoard = prevBoard.map(row => [...row]);
                newBoard[startField[0]][startField[1]]  = State.START_FIELD;
                return newBoard;
            });
        }

    }, []);

    useEffect(() => {
        if (!socket) return;

        socket.onmessage = (event) => {
            try {
                requestAnimationFrame(() => {
                    const data = JSON.parse(event.data);
                    console.log(data);
                    if (data.game_status === "in_progress") {
                        setGameState(GameState.IN_PROGRESS);
                    } else if (data.game_status === "loss") {
                        revealMines(data.full_board, data.loss_cause.cell);
                        setGameState(GameState.LOST);
                    } else if (data.game_status === "win") {
                        revealBoard(data.full_board);
                        setGameState(GameState.WON);
                    }

                    if (data.safe_cells && data.safe_cells.length > 0) {
                        setCell(data.safe_cells[0][0], data.safe_cells[0][1], State.HINT);
                        return;
                    }

                    if (!data.revealed_cells || data.game_status != "in_progress"){
                        return
                    }

                    setBoard(prevBoard => {
                        const newBoard = prevBoard.map(row => [...row]);


                        data.revealed_cells.forEach(([x, y, state]) => {
                            if (newBoard[x] && newBoard[x][y] !== undefined) {
                                newBoard[x][y] = state;
                            }
                        });
                        if(newBoard[startField[0]][startField[1]] === State.START_FIELD){
                            newBoard[startField[0]][startField[1]] = State.NOT_REVEALED
                        }

                        return newBoard;
                    });
                });
            } catch (err) {
                console.error("Error onmessage:", err);
            }
        };


        return () => {
            socket.onmessage = null;
        };
    }, [socket]);

    const handleClick = (e, x, y) => {
        e.preventDefault();
        if (!socket) return;


        if ((e.buttons === 2 && e.button === 0) || (e.buttons === 1 && e.button === 2)) {
            handleMultiClick(x, y);
        } else if (e.button === 0) {
            handleLeftClick(x, y);
        } else if (e.button === 2) {
            handleRightClick(x, y);
        }
    };

    const handleLeftClick = (x, y) => {
        if (!socket || socket.readyState !== WebSocket.OPEN) return;
        if(board[x][y] === State.START_FIELD || board[x][y] === State.NOT_REVEALED || board[x][y] === State.HINT) {
            let msg = JSON.stringify({
                type: "reveal_one",
                cell: [ x, y ]
            })
            console.log("wyslano:");
            console.log(msg);
            socket.send(msg);
        }

    };

    const handleRightClick = (x, y) => {
        if (!socket || socket.readyState !== WebSocket.OPEN) return;

        setBoard((prev) => {
            const newBoard = prev.map((row) => [...row]);
            const current = newBoard[x][y];

            if (current === State.NOT_REVEALED) {
                newBoard[x][y] = State.FLAG;
                setMines(prev => prev - 1)
                socket.send(JSON.stringify({ type: "flag", cell: [ x, y ] }));
            } else if (current === State.FLAG) {
                newBoard[x][y] = State.NOT_REVEALED;
                setMines(prev => prev + 1)
                socket.send(JSON.stringify({ type: "remove_flag", cell: [ x, y ] }));
            }

            return newBoard;
        });
    };

    const handleMultiClick = (x, y) => {
        if (!socket || socket.readyState !== WebSocket.OPEN || !isValidMultiClick(x, y)) return;

        const msg = {
            type: "reveal_many",
            cell: [ x, y ]
        };
        console.log("wyslano:", msg);
        socket.send(JSON.stringify(msg));
    };

    const setCell = (x, y, newValue) => {
        setBoard(prevBoard => {
            const newBoard = prevBoard.map(row => [...row]);
            newBoard[x][y] = newValue;
            return newBoard;
        });
    }

    const isValidMultiClick = (x, y) => {

        const value = board[x][y];

        if (value < State._0 || value > State._8) return false;

        let flagCount = 0;
        for (let dy = -1; dy <= 1; dy++) {
            for (let dx = -1; dx <= 1; dx++) {

                if (dx === 0 && dy === 0) continue;
                const nx = x + dx;
                const ny = y + dy;
                if (ny >= 0 && ny < boardData.cols && nx >= 0 && nx < boardData.rows) {
                    if (board[nx][ny] === State.FLAG) flagCount++;
                }
            }
        }
        return flagCount === value;
    };

    function revealMines(revealed_board, red_mine) {
        setBoard(prevBoard => {
            const newBoard = prevBoard.map(row => [...row]);

            for (let i = 0; i < revealed_board.length; i++) {
                for (let j = 0; j < revealed_board[i].length; j++) {
                    if (i === red_mine[0] && j === red_mine[1]) {
                        newBoard[i][j] = State.LOSING_MINE;
                    }else if (revealed_board[i][j] === State.MINE && board[i][j] !== State.FLAG) {
                        newBoard[i][j] = State.MINE;
                    }
                }
            }

            return newBoard;
        });
    }

    function revealBoard(revealed_board) {
        setBoard(prevBoard => {
            const newBoard = prevBoard.map(row => [...row]);

            for (let i = 0; i < revealed_board.length; i++) {
                for (let j = 0; j < revealed_board[i].length; j++) {
                    if (revealed_board[i][j] !== -1) {
                        newBoard[i][j] = revealed_board[i][j];
                    }
                }
            }

            return newBoard;
        });
    }

    return (
        <div className="board" onContextMenu={(e) => e.preventDefault()}>
                {board != null ? (
                        Array.from({ length: board.length}).map((_, i) => (
                                <div key={i} className="board-row">
                                    {Array.from({ length: board[0].length }).map((_, j) => (
                                        <Square
                                            key={`${i}-${j}`}
                                            value={board[i][j]}
                                            onClick={(e) => handleClick(e, i, j)}
                                        />
                                    ))}
                                </div>
                            ))
                    ) :
                    <div>Conecting...</div>
                }

        </div>
    );
}
