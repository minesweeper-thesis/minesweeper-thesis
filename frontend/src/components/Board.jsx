import React, {useEffect, useState} from "react";
import Square from "./Square";
import { State } from "../utility";
import "../styles/board.css";

export default function Board({ socket, boardData }) {
    const [board, setBoard] = useState(
        Array.from({ length: boardData.rows }, () =>
            Array(boardData.cols).fill(State.NOT_REVEALED)
        )
    );

    useEffect(() => {
        if (boardData.startField != null) {
            const newBoard = board.map(row => row.slice());
            newBoard[boardData.startField[0]][boardData.startField[1]] = State.START_FIELD;
            setBoard(newBoard);
            console.log("komponent: ", boardData.startField);
        }

    }, []);

    useEffect(() => {
        if (!socket) return;

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log("Odebrano:", data);

                if (!data.revealed_cells || data.game_status != "in_progress"){
                    return
                }

                setBoard(prevBoard => {
                    const newBoard = prevBoard.map(row => [...row]);


                    data.revealed_cells.forEach(([x, y, state]) => {
                        if (newBoard[y] && newBoard[x][y] !== undefined) {
                            newBoard[x][y] = state;
                        }
                    });

                    return newBoard;
                });

            } catch (err) {
                console.error("Error onmessage:", err);
            }
        };

        socket.onclose = (event) => {
            console.log("Error onclose:", event);
        };

        socket.onerror = (err) => {
            console.error("Error onerror:", err);
        };

        return () => {
            socket.onmessage = null;
            socket.onclose = null;
            socket.onerror = null;
        };
    }, [socket]);

    const handleClick = (e, x, y) => {
        e.preventDefault();
        if (!socket) return;


        if ((e.buttons === 3) || (e.button === 0 && e.buttons === 2)) {
            handleMultiClick(x, y);
        } else if (e.button === 0) {
            handleLeftClick(x, y);
        } else if (e.button === 2) {
            handleRightClick(x, y);
        }
    };

    const handleLeftClick = (x, y) => {
        if (!socket || socket.readyState !== WebSocket.OPEN) return;
        let msg = JSON.stringify({
            type: "reveal_one",
            cell: [ x, y ]
        })
        console.log("wyslano:");
        console.log(msg);
        socket.send(JSON.stringify({
            type: "reveal_one",
            cell: [ y, x ]
        }));
    };

    const handleRightClick = (x, y) => {
        if (!socket || socket.readyState !== WebSocket.OPEN) return;

        setBoard((prev) => {
            const newBoard = prev.map((row) => [...row]);
            const current = newBoard[x][y];

            if (current === State.NOT_REVEALED) {
                newBoard[x][y] = State.FLAG;
                socket.send(JSON.stringify({ type: "flag", cell: [ y, x ] }));
            } else if (current === State.FLAG) {
                newBoard[x][y] = State.NOT_REVEALED;
                socket.send(JSON.stringify({ type: "remove_flag", cell: [ y, x ] }));
            }

            return newBoard;
        });
    };

    const handleMultiClick = (x, y) => {
        if (!socket || socket.readyState !== WebSocket.OPEN) return;

        const action = {
            type: "reveal_many",
            cell: [ y, x ]
        };
        socket.send(JSON.stringify(action));
    };

    return (
        <div className="board" onContextMenu={(e) => e.preventDefault()}>
            {Array.from({ length: boardData.rows }).map((_, i) => (
                <div key={i} className="board-row">
                    {Array.from({ length: boardData.cols }).map((_, j) => (
                        <Square
                            key={`${i}-${j}`}
                            value={board[i][j]}
                            onClick={(e) => handleClick(e, i, j)}
                        />
                    ))}
                </div>
            ))}
        </div>
    );
}
