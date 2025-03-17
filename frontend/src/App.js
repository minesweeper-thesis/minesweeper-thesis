import React, { useState, useEffect } from 'react';

import './App.css'

function Square({ value, onLeftClick, onRightClick }) {
  return (
      <button className="square" onClick={onLeftClick} onContextMenu={onRightClick}>
        {value}
      </button>
  );
}

function Board({ board }) {

    const [clicked, setClicked] = useState(
        board.map(row => row.map(() => 0))
    );

    function isClicked(x, y, newClicked) {
        if (x < 0 || y < 0 || x >= board.length || y >= board[0].length) {
            return false;
        }
        if (newClicked[x][y] === -1 || newClicked[x][y] === 1) {
            return true;
        }
        return false;
    }

    function reveal(x, y, newClicked) {
        if (isClicked(x, y,newClicked)) {
            return;
        }

        newClicked[x][y] = 1;

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
                reveal(newX, newY, newClicked);
            }
        }
    }

    function fillSquare(i, j) {
        if (clicked[i][j] === -1) {
            return "X"
        }else if (clicked[i][j] === 0) {
            return " "
        }
        return board[i][j];
    }

    const handleLeftClick = (i, j) => {
        const newClicked = clicked.slice();
        reveal(i, j, newClicked);
        setClicked(newClicked);
    };

    const handleRightClick = (e, i, j) => {
        e.preventDefault()
        if (isClicked(i, j, clicked)) {
            return
        }
        const newClicked = clicked.slice();
        newClicked[i][j] = -1;
        setClicked(newClicked);
    };

    return (
        <div className="board">
            {board.map((row, rowIndex) => (
                <div key={rowIndex} className="board-row">
                    {row.map((value, colIndex) => (
                        <Square key={colIndex} value={fillSquare(rowIndex, colIndex)}
                                onLeftClick={() => handleLeftClick(rowIndex, colIndex)}
                                onRightClick={e => handleRightClick(e, rowIndex, colIndex)}/>
                    ))}
                </div>
            ))}
        </div>
    );
}


export default function Game() {
    const [data, setData] = useState(null);



    useEffect(() => {
        fetch('http://localhost:8000/board?rows=10&cols=10&start_x=3&start_y=4&mine_count=8')
            .then(response => response.json())
            .then(data => setData(data))
            .catch(error => console.error('Błąd:', error));
    }, []);

    if(data === null){
        return <div>Ładowanie...</div>;
    }
  return (
      <div className="game">
        <div className="game-board">
          <Board  board={data}/>
        </div>
      </div>
  )
}

