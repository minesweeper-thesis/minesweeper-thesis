import React, { useEffect, useState, useRef } from "react";
import Board from "../components/Board";
import Controls from "../components/Controls";
import { useSession } from "../contexts/SessionContext";
import { useNavigate } from "react-router-dom";
import { GameState } from "../utility";

export default function MultiGamePage() {
    const {
        sessionId,
        round,
        startAt,
        endAt,
        status,
        boardData,
        send,
        boardRef,
        gameState,
        setMines,
        setGameState,
        scoreboard
    } = useSession();

    const navigate = useNavigate();
    const [now, setNow] = useState(Math.floor(Date.now() / 1000));
    const [mines, setLocalMines] = useState(boardData?.mineCount ?? 0);

    useEffect(() => {
        const interval = setInterval(() => setNow(Math.floor(Date.now() / 1000)), 200);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (status === "lobby") navigate("/lobby");
    }, [status]);

    const timeToStart = startAt ? Math.max(0, startAt - Date.now()) : 0;
    const gameTimeLeft = endAt ? Math.max(0, endAt - now) : null;

    if (!sessionId) {
        return (
            <div className="w-full flex justify-center items-center h-full text-text-primary">
                Waiting for session...
            </div>
        );
    }

    return (
        <div className="w-full flex justify-center text-text-primary p-6">
            <div className="w-full max-w-6xl flex flex-col gap-6">
                {/* HEADER */}
                <div className="flex justify-between items-center mb-6 gap-4 flex-wrap">
                    <div className="flex gap-4 flex-wrap">
                        <div className="bg-bg-secondary border border-border-primary px-4 py-2 rounded-xl shadow text-sm md:text-base">
                            Round: {round}
                        </div>
                        <div className="bg-bg-secondary border border-border-primary px-4 py-2 rounded-xl shadow text-sm md:text-base">
                            Session: {sessionId}
                        </div>
                    </div>
                </div>

                {/* MAIN CONTENT */}
                <div className="flex flex-col md:flex-row gap-6">
                    {/* BOARD */}
                    <div className="flex-1">
                        <div className="rounded-xl p-4 relative">
                            {/* Controls in multi mode */}
                            <Controls
                                mode={"multi"}
                                mines={mines}
                                gameState={gameState}
                            />

                            {/* Board */}
                            <div className="mt-4">
                                <Board
                                    key={`${sessionId}-${round}`}
                                    ref={boardRef}
                                    boardData={boardData}
                                    sendCommand={send}
                                    setGameState={setGameState}
                                    setMines={setMines}
                                    mode={"multi"}
                                    countdownTime={Math.floor(timeToStart/1000)}
                                />
                            </div>
                        </div>
                    </div>

                    {/* LEADERBOARD */}
                    <div className="w-full md:w-1/3 bg-bg-secondary border border-border-primary p-4 rounded-xl shadow h-fit">
                        <h2 className="text-lg font-semibold mb-4">Leaderboard</h2>
                        <div className="flex flex-col gap-3">
                            {scoreboard.length === 0 ? (
                                <div className="text-text-secondary text-sm italic">No players yet</div>
                            ) : (
                                scoreboard.map(player => (
                                    <div
                                        key={player.id}
                                        className="flex items-center justify-between bg-bg-tertiary border border-border-primary p-3 rounded-lg"
                                    >
                                        <div className="flex items-center gap-3">
                                            <img
                                                src={player.avatar_url || "/avatar.svg"}
                                                alt="avatar"
                                                className="w-10 h-10 rounded-full bg-white border-2 border-border-primary object-cover"
                                            />
                                            <span className="font-medium text-text-primary">{player.nickname}</span>
                                        </div>
                                        <span className="text-accent-primary font-semibold">{player.score}</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
