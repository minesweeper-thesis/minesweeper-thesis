import React, { useState } from 'react';
import Board from './components/Board';
import Controls from './components/Controls';
import './App.css';

export default function Game() {
    const [data, setData] = useState(null);

    const rows = 9;
    const cols = 9;
    const mineCount = 10;

    const handleReset = () => setData(null);

    const handleNewGame = () => setData(null);

    return (
        <div className="game">
            <Controls onReset={handleReset} onNewGame={handleNewGame} />
            <div className="game-board">
                {data === null ? (
                    <div></div>
                ) : (
                    <Board board={data} setBoard={setData} rows={rows} cols={cols} mineCount={mineCount} />
                )}
                {data === null && (
                    <Board board={null} setBoard={setData} rows={rows} cols={cols} mineCount={mineCount} />
                )}
            </div>
        </div>
    );
}
