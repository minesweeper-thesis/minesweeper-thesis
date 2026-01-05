import { useCallback, useEffect, useRef, useState } from "react";
import Board from "../components/Board";
import useGameWebSocket from "../hooks/useGameWebSocket";
import boardInterpreter from "../utils/boardInterpreter";
import Controls from "../components/Controls";
import DifficultyMenu from "../components/DifficultyMenu";
import VictoryScreen from "../components/VictoryScreen";
import { GameState } from "../utility";

export default function GamePageSingle() {
    const [boardData, setBoardData] = useState({
        difficulty_level: {
            "rows": 10,
            "columns": 10,
            "mine_count": 15
        },
        mode: "normal" }
    );
    const [gameState, setGameState] = useState(GameState.NOT_STARTED);
    const [mines, setMines] = useState(0);
    const [gameplayId, setGameplayId] = useState(null);
    const [startField, setStartField] = useState(null);
    const boardRef = useRef(null);
    const [time, setTime] = useState(0);



    async function initGameRequest(storedId) {
        if (storedId) return { gameplay_id: storedId };

        console.log("Initializing game request...", boardData);

        const res = await fetch("/api/game/single", {
            method: "POST",
            headers: { "Content-Type": "application/json", accept: "application/json" },
            body: JSON.stringify(boardData),
        });
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return res.json();
    }


    const startNewGame = useCallback(async (storedId = null) => {
        setGameState(GameState.NOT_STARTED);
        try {
            const data = await initGameRequest(storedId);
            setGameplayId(data.gameplay_id);
            console.log("saving data:", data);
            localStorage.setItem("gameplayId", data.gameplay_id);
            setMines(data.mine_count ?? boardData.mineCount);
            setStartField(data.start_field ?? null);
        } catch (err) {
            console.error("Game init error:", err);
        }
    }, [boardData]);

    useEffect(() => {
        const stored = localStorage.getItem("gameplayId");
        startNewGame(stored);
    }, []);

    useEffect(() => {
        startNewGame(null);
    }, [boardData]);

    const onStart = useCallback(async () => {
        // await startNewGame(null);
    }, [startNewGame]);

    const onReset = useCallback(async (e) => {
        localStorage.removeItem("gameplayId");
        startNewGame(null);
    }, [startNewGame]);

    const socketUrl = gameplayId ? `api/game/single/${gameplayId}` : null;
    const { send, socketRef } = useGameWebSocket(socketUrl, boardInterpreter, boardRef, gameState, setTime);

    return (
        <div className="game flex min-h-screen justify-center bg-[linear-gradient(135deg,var(--bg-secondary)_0%,var(--bg-tertiary)_100%)] bg-fixed">
            <aside className="w-64 p-4">
                <DifficultyMenu setBoardData={setBoardData} onStart={onStart} />
            </aside>

            <main className="p-4 overflow-auto game-area relative w-full max-w-4xl">
                {gameState === GameState.WON && <VictoryScreen onPlayAgain={startNewGame} time={time} />}

                <Controls
                    onReset={onReset}
                    mines={mines}
                    gameState={gameState}
                    onHint={() => send({ type: "hint" })}
                />

                <div className="game-board flex-1 mt-4">
                        <Board
                            key={gameplayId}
                            ref={boardRef}
                            boardData={boardData}
                            sendCommand={send}
                            setGameState={setGameState}
                            setMines={setMines}
                            startField={startField}
                        />
                </div>
            </main>
        </div>
    );
}
