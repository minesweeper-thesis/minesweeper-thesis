import React, { useState } from 'react';
import Board from './components/Board';
import Controls from './components/Controls';
import './App.css';

export default function Game() {
    const [data, setData] = useState(null)
    const [firstClick, setFirstClick] = useState(null)
    const [boardKey, setBoardKey] = useState(Date.now())
    const [mines, setMines] = useState(0)

    const rows = 9
    const cols = 9
    const mineCount = 10

    const handleReset = () =>{
        setBoardKey(Date.now())
    }

    const handleNewGame = () => {
        setData(null)
        setFirstClick(null)
        setMines(0)
    }

    return (
        <div className="game">
            <Controls onReset={handleReset} onNewGame={handleNewGame} mines={mines} />
            <div className="game-board">
                {data === null ? (
                    <div></div>
                ) : (
                    <Board board={data} setBoard={setData} rows={rows} cols={cols} mineCount={mineCount}
                           firstClick={firstClick} setFirstClick={setFirstClick} mines={mines} setMines={setMines} key={boardKey} />
                )}
                {data === null && (
                    <Board board={null} setBoard={setData} rows={rows} cols={cols} mineCount={mineCount}
                           firstClick={firstClick} setFirstClick={setFirstClick} setMines={setMines}/>
                )}
            </div>
        </div>
    );
}
