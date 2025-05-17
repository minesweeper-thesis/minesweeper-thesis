import React, { useState } from 'react';
import Board from './components/Board';
import Controls from './components/Controls';
import MainMenu from './components/MainMenu';
import DifficultyMenu from './components/DifficultyMenu';
import { GameState } from './utility';
import './App.css';
import VictoryScreen from "./components/VictoryScreen";

export default function App() {
    const [view, setView] = useState('menu');
    const [data, setData] = useState(null);
    const [firstClick, setFirstClick] = useState(null);
    const [boardKey, setBoardKey] = useState(Date.now());
    const [mines, setMines] = useState(0);
    const [rows, setRows] = useState(9);
    const [cols, setCols] = useState(9);
    const [mineCount, setMineCount] = useState(10);
    const [gameState, setGameState] = useState(GameState.NOT_STARTED);

    const handleReset = () => {
        setBoardKey(Date.now());
        setGameState(GameState.NOT_STARTED);
    }

    const handleNewGame = () => {
        setData(null);
        setFirstClick(null);
        setMines(0);
        setGameState(GameState.NOT_STARTED);
    };

    const startGame = (r, c, m) => {
        setRows(r);
        setCols(c);
        setMineCount(m);
        setData(null);
        setView('game');
        setGameState(GameState.NOT_STARTED);
    };

    const returnToMenu = () => {
        setData(null);
        setFirstClick(null);
        setMines(0);
        setView('menu');
        setGameState(GameState.NOT_STARTED);
    };

    return (
        <div className="game">
            {view === 'menu' && <MainMenu onPlay={() => setView('difficulty')} />}
            {view === 'difficulty' && <DifficultyMenu onSelect={startGame} onBack={() => setView('menu')} />}
            {view === 'game' && (
                <>
                    <Controls onReset={handleReset} onNewGame={handleNewGame} onMenu={returnToMenu} mines={mines} />
                    <div className="game-board">
                        {data === null ? (
                            <Board board={null} setBoard={setData} rows={rows} cols={cols} mineCount={mineCount}
                                   firstClick={firstClick} setFirstClick={setFirstClick} setMines={setMines}
                                   gameState={gameState} setGameState={setGameState} />
                        ) : (
                            <Board board={data} setBoard={setData} rows={rows} cols={cols} mineCount={mineCount}
                                   firstClick={firstClick} setFirstClick={setFirstClick} mines={mines} setMines={setMines}
                                   key={boardKey} gameState={gameState} setGameState={setGameState}/>
                        )}
                    </div>
                </>
            )}
            {gameState === GameState.WON && <VictoryScreen onPlayAgain={handleNewGame} />}
        </div>
    );
}
