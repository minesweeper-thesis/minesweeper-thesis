import { useCallback, useEffect, useRef, useState } from "react";
import Board from "../components/Board";
import useGameWebSocket from "../hooks/useGameWebSocket";
import gameInterpreter from "../utils/gameInterpreter";
import Controls from "../components/Controls";
import DifficultyMenu from "../components/DifficultyMenu";
import AdvancedOptions from "../components/AdvancedOptions";
import VictoryScreen from "../components/VictoryScreen";
import { GameState } from "../utility";

export default function GamePage() {
    const [boardData, setBoardData] = useState({ rows: 10, cols: 10, mineCount: 15, mode: "normal" });
    const [heuristicData, setHeuristicData] = useState({ classifier: "lightgbm", heuristic: "no", heuristic_args: [] });
    const [gameState, setGameState] = useState(GameState.NOT_STARTED);
    const [mines, setMines] = useState(0);
    const [gameplayId, setGameplayId] = useState(null);
    const boardRef = useRef(null);
    const [startField, setStartField] = useState(null);

    const REQUEST_BODY = {
        generator: { type: "random", settings: { ...heuristicData } },
        difficulty_level: { rows: boardData.rows, columns: boardData.cols, mine_count: boardData.mineCount },
        mode: boardData.mode,
    };

    async function initGameRequest() {
        try {
            const response = await fetch("api/game/single", {
                method: "POST",
                headers: { "accept": "application/json", "Content-Type": "application/json" },
                body: JSON.stringify(REQUEST_BODY),
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            const data = await response.json();
            return data;
        } catch (err) {
            console.error("Błąd inicjalizacji gry:", err);
            throw err;
        }
    }

    const startNewGame = useCallback(async () => {
        setGameState(GameState.NOT_STARTED);
        try {
            const res = await initGameRequest();
            setGameplayId(res.gameplay_id);
            setMines(res.mine_count ?? boardData.mineCount);
            setStartField(res.start_field);
            // if (res.start_field && boardRef.current?.dispatchCommand) {
            //     boardRef.current.dispatchCommand({ type: "SET_START_FIELD", start: res.start_field });
            // }
        } catch (err) {
            console.error("Game initialization error:", err);
        }
    }, [boardData, heuristicData]);

    const socketUrl = gameplayId ? `ws://localhost:8000/api/game/single/${gameplayId}` : null;
    const { send } = useGameWebSocket(socketUrl, gameInterpreter, boardRef);

    useEffect(() => {
        startNewGame();
    }, [boardData]);

    return (
        <div className="game flex h-screen justify-center bg-[linear-gradient(135deg,var(--bg-secondary)_0%,var(--bg-tertiary)_100%)] bg-fixed">
            <aside className="w-64 p-4">
                <DifficultyMenu setBoardData={setBoardData} />
                {/*<AdvancedOptions onSelect={(data) => setHeuristicData(data)} />*/}
            </aside>

            <main className="p-4 overflow-auto game-area relative w-full max-w-4xl">
                {gameState === GameState.WON && <VictoryScreen onPlayAgain={startNewGame} />}

                <Controls
                    onReset={startNewGame}
                    mines={mines}
                    gameState={gameState}
                    onHint={() => send({ type: "hint" })}
                />

                <div className="game-board flex-1 mt-4 ">
                    <Board
                        key={gameplayId}
                        ref={boardRef}
                        boardData={boardData}
                        sendCommand={(obj) => send(obj)}
                        setGameState={setGameState}
                        setMines={setMines}
                        startField={startField}
                    />
                </div>
            </main>
        </div>
    );
}
