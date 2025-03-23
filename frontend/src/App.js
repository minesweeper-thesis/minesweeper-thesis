import React, { useState, useEffect } from 'react';

import './App.css'

export const State = {
    NOT_REVEALED: 0,
    REVEALED: 1,
    FLAGGED: 2,
};

function Square({ value, onClick}) {
    function isClicked(value){
        if( value === " " || value === -2){
            return " not-clicked"
        }
        return " clicked"
    }
  return (
      <button className={`square number-${value}` + isClicked(value)} onMouseUp={onClick} onContextMenu={(e) => e.preventDefault()}>
          {value === -1 ? (
              <img src="/mine.svg" alt=" " className="mine-icon" />
          ) : value === -2 ? (
              <img src="/flag.svg" alt=" " className="flag-icon" />
          ) : value === 0 ? (
              " "
          ) : (
              value
          )}
      </button>
  );
}

function Board({ board }) {

    const [clicked, setClicked] = useState(
        board.map(row => row.map(() => 0))
    );

    function cellState(x, y, newClicked) {
        if (x < 0 || y < 0 || x >= board.length || y >= board[0].length) {
            return State.REVEALED;
        }
        return newClicked[x][y];
    }

    function reveal(x, y, newClicked, revealFlags = true) {
        if (cellState(x, y,newClicked) === State.REVEALED) {
            return;
        }
        if (cellState(x, y, newClicked) === State.FLAGGED && revealFlags === false) {
            return
        }

        newClicked[x][y] = State.REVEALED;

        if (board[x][y] !== 0) {
            return;
        }

        const directions = [
            [-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]
        ];

        for (let [dx, dy] of directions) {
            let newX = x + dx;
            let newY = y + dy;

            if (newX >= 0 && newY >= 0 && newX < board.length && newY < board[0].length) {
                reveal(newX, newY, newClicked, revealFlags);
            }
        }
    }

    function fillSquare(i, j) {
        if (clicked[i][j] === State.NOT_REVEALED) {
            return " "
        }else if (clicked[i][j] === State.FLAGGED) {
            return -2
        }
        return board[i][j];
    }

    const handleClick = (e, i, j) => {
        if ((e.buttons === 2 && e.button === 0) || ( e.buttons === 1 && e.button === 2)) {
            handleMultiClick(i, j);
        }else if(e.button === 0) {
            handleLeftClick(i, j);
        }else if (e.button === 2) {
            handleRightClick(e, i, j);
        }

    };

    const handleLeftClick = (i, j) => {
        const newClicked = clicked.slice();
        reveal(i, j, newClicked);
        setClicked(newClicked);
    };

    const handleRightClick = (e, i, j) => {
        if (cellState(i, j, clicked) === State.REVEALED) {
            return
        }

        const newClicked = clicked.slice();

        if (cellState(i, j, clicked) === State.FLAGGED) {
            newClicked[i][j] = State.NOT_REVEALED;
        }else{
            newClicked[i][j] = State.FLAGGED;
        }

        setClicked(newClicked);
    };

    const handleMultiClick = (x, y) => {
        if(clicked[x][y] !== State.REVEALED) {
            return
        }

        const directions = [
            [-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]
        ];

        let flagged = 0
        const newClicked = clicked.slice();

        for (let [dx, dy] of directions) {
            if (cellState(dx + x,dy + y, newClicked) === State.FLAGGED) {
                flagged++;
            }
        }

        if (flagged === board[x][y]) {
            for (let [dx, dy] of directions) {
                reveal(dx + x,dy + y, newClicked, false);
            }
        }
        setClicked(newClicked);
    }
    return (
        <div className="board">
            {board.map((row, rowIndex) => (
                <div key={rowIndex} className="board-row">
                    {row.map((value, colIndex) => (
                        <Square key={colIndex} value={fillSquare(rowIndex, colIndex)}
                                onClick={e => handleClick(e, rowIndex, colIndex)}/>
                    ))}
                </div>
            ))}
        </div>
    );
}


export default function Game() {
    const [data, setData] = useState(null);



    useEffect(() => {
        fetch('http://localhost:8000/board?rows=9&cols=9&start_x=3&start_y=4&mine_count=9')
            .then(response => response.json())
            .then(data => setData(data))
            .catch(error => console.error('Błąd:', error));
    }, []);

    if(data === null){
        return <div>Ładowanie... (to musi być na 3000, a backend na 8000 i musi być włączony)</div>;
    }
  return (
      <div className="game">
        <div className="game-board">
          <Board  board={data}/>
        </div>
      </div>
  )
}

