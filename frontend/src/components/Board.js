import React, {useState, useRef, useEffect, useCallback} from 'react';
import Square from './Square';
import { State } from '../utility';
import '../styles/board.css';

export default function Board({ board, setBoard, rows, cols, mineCount }) {
    const [clicked, setClicked] = useState(
        Array.from({ length: rows }, () => Array(cols).fill(State.NOT_REVEALED))
    );
    const firstClick = useRef(null)

    useEffect(() => {
        setClicked(Array.from({ length: rows }, () => Array(cols).fill(State.NOT_REVEALED)));
    }, [board, rows, cols]);

    const cellState = useCallback((x, y, clickedState) => {
        if (x < 0 || y < 0 || x >= rows || y >= cols) return State.REVEALED;
        return clickedState[x][y];
    }, [rows, cols]);


    const reveal = useCallback((x, y, newClicked, revealFlags = true) => {
        if (cellState(x, y, newClicked) === State.REVEALED) return;
        if (cellState(x, y, newClicked) === State.FLAGGED && !revealFlags) return;

        newClicked[x][y] = State.REVEALED;
        if (board[x][y] !== 0) return;

        const directions = [
            [-1, -1], [-1, 0], [-1, 1],
            [0, -1],          [0, 1],
            [1, -1], [1, 0], [1, 1],
        ];

        for (let [dx, dy] of directions) {
            reveal(x + dx, y + dy, newClicked, revealFlags);
        }
    }, [cellState, board])


    const fillSquare = (i, j) => {
        const state = clicked[i][j];
        if (state === State.NOT_REVEALED) return " ";
        if (state === State.FLAGGED) return -2;
        return board[i][j];
    };

    const fetchBoard = (x, y) => {
        console.log("ustawiam first click", x, y)
        firstClick.current = {x, y}
        console.log(firstClick.current)
        fetch(`http://localhost:8000/board?rows=${rows}&cols=${cols}&start_x=${x}&start_y=${y}&mine_count=${mineCount}`)
            .then(res => res.json())
            .then(data => {
                setBoard(data)
            })
            .catch(err => console.error("Błąd:", err));
    };

    const handleClick = (e, i, j) => {
        console.log("handle click");
        if (!board && e.button === 0) {
            console.log("fetching board");
           fetchBoard(i, j);
        }else if(!board) {
            console.log("huh")
        }else if ((e.buttons === 2 && e.button === 0) || (e.buttons === 1 && e.button === 2)) {
            handleMultiClick(i, j);
        } else if (e.button === 0) {
            handleLeftClick(i, j);
        } else if (e.button === 2) {
            handleRightClick(e, i, j);
        }
    };

    const handleLeftClick = useCallback((i, j) => {
        console.log("left click");
        const newClicked = clicked.map(row => row.slice());
        reveal(i, j, newClicked);
        setClicked(newClicked);
    }, [clicked, reveal]);


    const handleRightClick = (e, i, j) => {
        e.preventDefault();
        const newClicked = clicked.map(row => row.slice());
        const state = cellState(i, j, clicked);
        if (state === State.REVEALED) return;
        newClicked[i][j] = state === State.FLAGGED ? State.NOT_REVEALED : State.FLAGGED;
        setClicked(newClicked);
    };

    const handleMultiClick = (x, y) => {
        if (clicked[x][y] !== State.REVEALED) return;

        const directions = [
            [-1, -1], [-1, 0], [-1, 1],
            [0, -1],          [0, 1],
            [1, -1], [1, 0], [1, 1],
        ];

        const newClicked = clicked.map(row => row.slice());
        let flagged = 0;

        for (let [dx, dy] of directions) {
            if (cellState(x + dx, y + dy, newClicked) === State.FLAGGED) flagged++;
        }

        if (flagged === board[x][y]) {
            for (let [dx, dy] of directions) {
                reveal(x + dx, y + dy, newClicked, false);
            }
        }

        setClicked(newClicked);
    };

    useEffect(() => {
        console.log("useEffect sprawdza...", firstClick.current );
    }, [firstClick, board]);

    // useEffect(() => {
    //     console.log("useEffect sprawdza...", { board, firstClick });
    //     if (board && firstClick) {
    //         console.log("firstClick");
    //         // handleLeftClick(firstClick[], lastClick);
    //         setFirstClick(null);
    //     }
    // }, [board, firstClick, handleLeftClick]);

    return (
        <div className="board">
            {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="board-row">
                    {Array.from({ length: cols }).map((_, j) => (
                        <Square
                            key={j}
                            value={board ? fillSquare(i, j) : " "}
                            onClick={(e) => handleClick(e, i, j)}
                        />
                    ))}
                </div>
            ))}
        </div>
    );
}
