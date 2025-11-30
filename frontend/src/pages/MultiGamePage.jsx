import React, { useEffect, useRef, useState } from "react";
import Board from "../components/Board";
import { useSession } from "../contexts/SessionContext";
import boardInterpreter from "../utils/boardInterpreter";
import useGameWebSocket from "../hooks/useGameWebSocket";
import { GameState } from "../utility";
import {useNavigate} from "react-router-dom";

export default function MultiGamePage() {
    const {
        sessionId,
        round,
        startAt,
        endAt,
        startField,
        status,
        boardData,
        send,
        boardRef,
        gameState,
        setMines,
        setGameState,
    } = useSession();




    const navigate = useNavigate();


    useEffect(() => {
        if (status === "lobby") {
            navigate("/lobby");
        }
    }, [status]);

    const timeLeft = endAt ? Math.max(0, endAt - Math.floor(Date.now() / 1000)) : null;

    if (!sessionId) {
        return <div className="p-6 text-text-primary">Waiting for session...</div>;
    }

    return (
        <div className="game flex h-screen justify-center bg-[linear-gradient(135deg,var(--bg-secondary)_0%,var(--bg-tertiary)_100%)] bg-fixed">
            <aside className="w-64 p-4">
                <div className="bg-bg-secondary p-4 rounded shadow">
                    <div>Round: {round}</div>
                    <div>Session: {sessionId}</div>
                    <div>Time left: {timeLeft !== null ? `${timeLeft}s` : "n/a"}</div>
                </div>
            </aside>

            <main className="p-4 overflow-auto game-area relative w-full max-w-4xl">
                <div className="game-board flex-1 mt-4">
                    <Board
                        key={`${sessionId}-${round}`}
                        ref={boardRef}
                        boardData={boardData}
                        sendCommand={send}
                        setGameState={setGameState}
                        setMines={setMines}
                    />
                </div>
            </main>
        </div>
    );
}
