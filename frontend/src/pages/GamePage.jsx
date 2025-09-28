import React, { useState } from 'react';
import Board from '../components/Board';
import Controls from '../components/Controls';
import DifficultyMenu from '../components/DifficultyMenu';
import { GameState } from '../utility';
import VictoryScreen from "../components/VictoryScreen";
import PauseScreen from "../components/PauseScreen";


export default function GamePage() {
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

    const pauseGame = () => {
        console.log('gameState in Controls:', gameState);
        console.log('GameState.IN_PROGRESS:', GameState.IN_PROGRESS);
        if(gameState === GameState.IN_PROGRESS)
        setGameState(GameState.PAUSED);
    };

    const resumeGame = () => {
        setGameState(GameState.IN_PROGRESS);
    };
    const returnToMenu = () => {
        setData(null);
        setFirstClick(null);
        setMines(0);
        setView('menu');
        setGameState(GameState.NOT_STARTED);
    };

    return (
        <div className="game flex h-screen justify-evenly bg-bg-tertiary">
            {/* Sidebar */}
            <aside className="w-64 p-4 bg-bg-tertiary">
                <DifficultyMenu onSelect={startGame} />
            </aside>

            {/* Main game area */}
            <main className="p-4 overflow-auto">
                <Controls
                    onReset={handleReset}
                    onNewGame={handleNewGame}
                    onMenu={returnToMenu}
                    mines={mines}
                    onPause={pauseGame}
                    gameState={gameState}
                />

                <div className="game-board flex-1 mt-4 ">
                    {data === null ? (
                        <Board
                            board={null}
                            setBoard={setData}
                            rows={rows}
                            cols={cols}
                            mineCount={mineCount}
                            firstClick={firstClick}
                            setFirstClick={setFirstClick}
                            setMines={setMines}
                            gameState={gameState}
                            setGameState={setGameState}
                        />
                    ) : (
                        <Board
                            board={data}
                            setBoard={setData}
                            rows={rows}
                            cols={cols}
                            mineCount={mineCount}
                            firstClick={firstClick}
                            setFirstClick={setFirstClick}
                            mines={mines}
                            setMines={setMines}
                            key={boardKey}
                            gameState={gameState}
                            setGameState={setGameState}
                        />
                    )}
                </div>
            </main>

            {/* Overlay screens */}
            {gameState === GameState.WON && <VictoryScreen onPlayAgain={handleNewGame} />}
            {gameState === GameState.PAUSED && <PauseScreen resumeGame={resumeGame} />}
        </div>
    );
}