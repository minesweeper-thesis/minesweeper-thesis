import { useCallback, useEffect, useRef, useState } from "react";
import Board from "../components/Board";
import useGameWebSocket from "../hooks/useGameWebSocket";
import gameInterpreter from "../utils/gameInterpreter";
import Controls from "../components/Controls";
import DifficultyMenu from "../components/DifficultyMenu";
import VictoryScreen from "../components/VictoryScreen";
import { GameState } from "../utility";

export default function GamePageSingle() {
    const [boardData, setBoardData] = useState({ rows: 10, cols: 10, mineCount: 15, mode: "normal" });
    const [heuristicData, setHeuristicData] = useState({ classifier: "lightgbm", heuristic: "no", heuristic_args: [] });
    const [gameState, setGameState] = useState(GameState.NOT_STARTED);
    const [mines, setMines] = useState(0);
    const [gameplayId, setGameplayId] = useState(null);
    const [startField, setStartField] = useState(null);
    const boardRef = useRef(null);

    const firstRenderRef = useRef(true);

    async function initGameRequest(storedId) {
        if (storedId) return { gameplay_id: storedId };

        let REQUEST_BODY = {
            generator: { type: "ml", settings: { ...heuristicData } },
            difficulty_level: { rows: boardData.rows, columns: boardData.cols, mine_count: boardData.mineCount },
            mode: boardData.mode,
        };
        console.log(REQUEST_BODY);

        const res = await fetch("/api/game/single", {
            method: "POST",
            headers: { "Content-Type": "application/json", accept: "application/json" },
            body: JSON.stringify(REQUEST_BODY),
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
    }, [boardData, heuristicData]);

    useEffect(() => {
        const stored = localStorage.getItem("gameplayId");
        startNewGame(stored);
    }, []);

    useEffect(() => {
        if (firstRenderRef.current) {
            firstRenderRef.current = false;
            return;
        }
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
    const { send, socketRef } = useGameWebSocket(socketUrl, gameInterpreter, boardRef, gameState );

    return (
        <div className="game flex h-screen justify-center bg-[linear-gradient(135deg,var(--bg-secondary)_0%,var(--bg-tertiary)_100%)] bg-fixed">
            <aside className="w-64 p-4">
                <DifficultyMenu setBoardData={setBoardData} onStart={onStart} />
            </aside>

            <main className="p-4 overflow-auto game-area relative w-full max-w-4xl">
                {gameState === GameState.WON && <VictoryScreen onPlayAgain={startNewGame} />}

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
