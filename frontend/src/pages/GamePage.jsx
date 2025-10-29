import React, {useEffect, useState} from 'react';
import Board from '../components/Board';
import Controls from '../components/Controls';
import DifficultyMenu from '../components/DifficultyMenu';
import { GameState } from '../utility';
import VictoryScreen from "../components/VictoryScreen";
import AdvancedOptions from "../components/AdvancedOptions";


export default function GamePage() {

    const [gameState, setGameState] = useState(GameState.NOT_STARTED);
    const [socket, setSocket] = useState(null);
    const [mines, setMines] = useState(0);
    const [startField, setStartField] = useState(null);
    const [heuristicData, setHeuristicData] = useState({
        classifier: "lightgbm",
        heuristic: "no",
        heuristic_args: []
    });
    const [boardData, setBoardData] = useState({
        rows: 9,
        cols: 9,
        mineCount: 10,
        mode: "normal",
    })



    const REQUEST_BODY = {
        generator: {
            type: "random",
            settings: {
                ...heuristicData
            },
        },
        difficulty_level: {
            rows: boardData.rows,
            columns: boardData.cols,
            mine_count: boardData.mineCount,
        },
        mode: boardData.mode,
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
            console.log(data);
            return data;
        } catch (error) {
            console.error("Błąd inicjalizacji gry:", error);
            throw error;
        }
    }

    function connectToGameWebSocket(gameplay_id) {
        const socketUrl = `game_api/game/${gameplay_id}/ws`;
        const socket = new WebSocket(socketUrl);

        socket.onopen = () => {
            console.log("WebSocket connected:", socketUrl);
        };

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        socket.onclose = (event) => {
            console.log("WebSocket closed:", event);
        };

        return socket;
    }

    async function startNewGame() {
        let ws;
        setGameState(GameState.NOT_STARTED);

        try {
            if (socket) {
                socket.close();
                setSocket(null);
            }
            const res = await initGameRequest();
            console.log("http response: ", res);
            setStartField(res.start_field);

            ws = connectToGameWebSocket(res.gameplay_id);
            setSocket(ws);
            return ws;
        } catch (err) {
            console.error("Game initialization error:", err);
        }
    }

    useEffect(() => {
        let ws;

        startNewGame().then(socket => {
            ws = socket;
        });

        return () => {
            if (ws) {
                ws.close();
            }
        };
    }, [boardData]);


    return (
        <div className="game flex h-screen bg-bg-tertiary justify-center">
            {/* Sidebar */}
            <aside className="w-64 p-4 bg-bg-tertiary">
                <DifficultyMenu setBoardData={setBoardData}/>
                <AdvancedOptions onSelect={(data) => setHeuristicData(data)} />
            </aside>

            {/* Main game area */}
            <main className="p-4 overflow-auto game-area relative w-full max-w-4xl">
                {/* Overlay screen */}
                {gameState === GameState.WON && <VictoryScreen onPlayAgain={startNewGame} />}

                <Controls
                    onReset={startNewGame}
                    mines={mines}
                    gameState={gameState}
                    onHint={() =>
                        {socket.send(JSON.stringify({
                            type: "hint"
                        }))}}
                />

                <div className="game-board flex-1 mt-4 ">
                    {socket != null ? (
                        <Board
                            boardData = {boardData}
                            socket = {socket}
                            setGameState = {setGameState}
                            setMines = {setMines}
                            startField = {startField}
                        />
                    ) :
                        <div>Conecting...</div>
                    }
                </div>
            </main>


        </div>
    );
}