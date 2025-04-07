import React, {useState, useEffect, useCallback} from 'react';
import Square from './Square';
import { State } from '../utility';
import '../styles/board.css';

export default function Board({ board, setBoard, rows, cols, mineCount ,firstClick, setFirstClick, mines, setMines }) {
    const [clicked, setClicked] = useState(
        Array.from({ length: rows }, () => Array(cols).fill(State.NOT_REVEALED))
    );
    const [started, setStarted] = useState(false)
    const [disableClicks, setDisableClicks] = useState(false)

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
        if (board[x][y] === -1){
           setDisableClicks(true);
        }
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
    }

    const fetchBoard = (x, y) => {
        fetch(`http://localhost:8000/board?rows=${rows}&cols=${cols}&start_x=${x}&start_y=${y}&mine_count=${mineCount}`)
            .then(res => res.json())
            .then(data => {
                setBoard(data)
            })
            .catch(err => console.error("Błąd:", err));
    }

    const handleClick = (e, x, y) => {
        if (disableClicks) return;
        if (!board && e.button === 0) {
            setFirstClick({x, y})
            fetchBoard(x, y)
        }else if(!board) {
            console.log("huh")
        }else if ((e.buttons === 2 && e.button === 0) || (e.buttons === 1 && e.button === 2)) {
            handleMultiClick(x, y)
        } else if (e.button === 0) {
            handleLeftClick(x, y)
        } else if (e.button === 2) {
            handleRightClick(e, x, y)
        }
    }

    const handleLeftClick = useCallback((i, j) => {
        if(clicked[i][j] === State.FLAGGED){return}
        const newClicked = clicked.map(row => row.slice());
        reveal(i, j, newClicked);
        setClicked(newClicked);
    }, [clicked, reveal]);


    const handleRightClick = (e, i, j) => {
        e.preventDefault();
        const newClicked = clicked.map(row => row.slice());
        const state = cellState(i, j, clicked);
        if (state === State.REVEALED){
            return
        }else if (state === State.FLAGGED){
            setMines(mines + 1)
        }else{
            setMines(mines - 1)
        }

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
        if (board && firstClick && !started) {
            handleLeftClick(firstClick.x, firstClick.y);
            setStarted(true);
            setMines(mineCount)
            setDisableClicks(false)
        }
    }, [board, firstClick, handleLeftClick, mineCount, setFirstClick, setMines, started]);

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
