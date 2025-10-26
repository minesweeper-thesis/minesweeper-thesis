import React, {useEffect, useState} from 'react';
import Board from '../components/Board';
import Controls from '../components/Controls';
import DifficultyMenu from '../components/DifficultyMenu';
import { GameState } from '../utility';
import VictoryScreen from "../components/VictoryScreen";
import PauseScreen from "../components/PauseScreen";
import AdvancedOptions from "../components/AdvancedOptions";


export default function GamePage() {

    // const [data, setData] = useState(null);
    const [firstClick, setFirstClick] = useState(null);
    // const [boardKey, setBoardKey] = useState(Date.now());
    const [mines, setMines] = useState(0);
    const [rows, setRows] = useState(9);
    const [cols, setCols] = useState(9);
    const [mineCount, setMineCount] = useState(10);
    const [heuristicData, setHeuristicData] = useState({
        classifier: "lightgbm",
        heuristic: "no",
        heuristic_args: [0]
    });
    const [boardData, setBoardData] = useState({
        rows: 9,
        cols: 9,
        mineCount: 10,
        startField: null
    })

    // const [gameState, setGameState] = useState(GameState.NOT_STARTED);
    const [socket, setSocket] = useState(null);

    // const handleReset = () => {
    //     setBoardKey(Date.now());
    //     setGameState(GameState.NOT_STARTED);
    // }
    //
    // const handleNewGame = () => {
    //     setData(null);
    //     setFirstClick(null);
    //     setMines(0);
    //     setGameState(GameState.NOT_STARTED);
    // };
    //
    // const startGame = (r, c, m) => {
    //     setRows(r);
    //     setCols(c);
    //     setMineCount(m);
    //     setData(null);
    //     setGameState(GameState.NOT_STARTED);
    // };
    //
    // const pauseGame = () => {
    //     console.log('gameState in Controls:', gameState);
    //     console.log('GameState.IN_PROGRESS:', GameState.IN_PROGRESS);
    //     if(gameState === GameState.IN_PROGRESS)
    //     setGameState(GameState.PAUSED);
    // };
    //
    // const resumeGame = () => {
    //     setGameState(GameState.IN_PROGRESS);
    // };


    const REQUEST_BODY = {
        generator: {
            type: "random",
            settings: {
                ...heuristicData
            },
        },
        difficulty_level: {
            rows: rows,
            columns: cols,
            mine_count: mineCount,
        },
        mode: "normal",
    };

    async function initGameRequest() {
        try {
            const response = await fetch("api/game/single/init", {
                method: "POST",
                headers: {
                    "accept": "application/json",
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(REQUEST_BODY),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            // console.log(data);
            return data;
        } catch (error) {
            console.error("Błąd inicjalizacji gry:", error);
            throw error;
        }
    }

    function connectToGameWebSocket(gameplay_id, onMessage, onClose) {
        const socketUrl = `game_api/game/${gameplay_id}/ws`;
        const socket = new WebSocket(socketUrl);

        socket.onopen = () => {
            console.log("WebSocket connected:", socketUrl);
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                // onMessage?.(data);
            } catch (err) {
                console.warn("Niepoprawny JSON z serwera:", event.data);
            }
        };

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        socket.onclose = (event) => {
            console.log("WebSocket closed:", event);
            // onClose?.(event);
        };

        return socket;
    }

    useEffect(() => {
        let ws;

        async function init() {
            try {
                const res = await initGameRequest();
                setBoardData(prevData => ({
                    ...prevData,
                    startField: res.start_field
                }));
                ws = connectToGameWebSocket(res.gameplay_id);
                setSocket(ws);

            } catch (err) {
                console.error("Game initialization error:", err);
            }
        }

        init();

        return () => {
            if (ws) {
                ws.close();
            }
        };
    }, []);



    return (
        <div className="game flex h-screen bg-bg-tertiary justify-center">
            {/* Sidebar */}
            <aside className="w-64 p-4 bg-bg-tertiary">
                {/*<DifficultyMenu onSelect={startGame} />*/}
                <AdvancedOptions onSelect={(data) => setHeuristicData(data)} />
            </aside>

            {/* Main game area */}
            <main className="p-4 overflow-auto game-area relative w-full max-w-4xl">
                {/* Overlay screens */}
                {/*{gameState === GameState.WON && <VictoryScreen onPlayAgain={handleNewGame} />}*/}
                {/*{gameState === GameState.PAUSED && <PauseScreen resumeGame={resumeGame} />}*/}

                {/*<Controls*/}
                {/*    onReset={handleReset}*/}
                {/*    onNewGame={handleNewGame}*/}
                {/*    mines={mines}*/}
                {/*    onPause={pauseGame}*/}
                {/*    gameState={gameState}*/}
                {/*/>*/}

                <div className="game-board flex-1 mt-4 ">
                    {socket != null ? (
                        <Board
                            boardData = {boardData}
                            socket = {socket}
                        />
                    ) :
                        <div>Conecting...</div>
                    }
                </div>
            </main>


        </div>
    );
}