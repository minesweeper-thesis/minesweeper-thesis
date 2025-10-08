import React, {useState, useEffect, useCallback} from 'react';
import Square from './Square';
import { State, GameState } from '../utility';
import '../styles/board.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function Board({ board, setBoard, rows, cols, mineCount ,firstClick, setFirstClick, mines, setMines, gameState, setGameState }) {
    const [clicked, setClicked] = useState(
        Array.from({ length: rows }, () => Array(cols).fill(State.NOT_REVEALED))
    );

    const [revealedCount, setRevealedCount] = useState(0);
    
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
           setGameState(GameState.LOST);
        }
        newClicked[x][y] = State.REVEALED;
        setRevealedCount(revealedCount+1);
        console.log(revealedCount);
        if (board[x][y] !== 0) return;

        const directions = [
            [-1, -1], [-1, 0], [-1, 1],
            [0, -1],          [0, 1],
            [1, -1], [1, 0], [1, 1],
        ];

        for (let [dx, dy] of directions) {
            reveal(x + dx, y + dy, newClicked, revealFlags);
        }
    }, [cellState, board, revealedCount, setGameState])


    const fillSquare = (i, j) => {
        const state = clicked[i][j];
        if (state === State.NOT_REVEALED) return " ";
        if (state === State.FLAGGED) return -2;
        return board[i][j];
    }

    const checkWin = useCallback(() => {
        console.log("checking...")
        for (let i = 0; i < rows; i++) {
            for (let j = 0; j < cols; j++) {
                if(board[i][j] !== -1 && clicked[i][j] !== State.REVEALED ){
                    console.log("game's still on");
                    return GameState.IN_PROGRESS;
                }
            }
        }
        console.log("Won!");
        return GameState.WON;
    }, [board, clicked, cols, rows])

    const fetchBoard = (x, y) => {
        const data = {
            rows,
            columns: cols,
            start_field: [x, y],
            mine_count: mineCount,
            classifier: "lightgbm",
            heuristic: "GA",
            heuristic_args: [10,50,10,0.05],
        };

        fetch(`${BACKEND_URL}/board`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
            .then(res => res.json())
            .then(data => {
                setBoard(data)
            })
            .catch(err => console.error("Błąd:", err));
    }

    const handleClick = (e, x, y) => {
        if (gameState === GameState.LOST || gameState === GameState.WON || gameState === GameState.PAUSED) return;
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
        if (board && firstClick && gameState === GameState.NOT_STARTED) {
            handleLeftClick(firstClick.x, firstClick.y);
            setMines(mineCount)
            setGameState(GameState.IN_PROGRESS)
        }
    }, [board, firstClick, gameState, handleLeftClick, mineCount, setGameState, setMines]);

    useEffect(() => {
    if(board && gameState === GameState.IN_PROGRESS){
        setGameState(checkWin())
    }
    }, [checkWin,board, setGameState, gameState]);
    
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
