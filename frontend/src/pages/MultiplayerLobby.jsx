import React, { useState } from "react";
import { Crown } from "lucide-react";
import {useAuth} from "../contexts/AuthContext";
import {useGame} from "../contexts/GameServiceContext";

export default function MultiplayerLobby() {

    // const { getLobby } = useGame();
    // console.log("lobby: ",  getLobby());

    const players = [
        { id: 1, name: "PlayerOne", online: true, ready: true, score: 12 },
        { id: 2, name: "PlayerTwo", online: true, ready: false, score: 7 },
        { id: 3, name: "GhostRider", online: false, ready: false, score: 3 },
    ];

    const ownerId = 1;

    const lobbySettings = {
        rows: 12,
        cols: 12,
        mines: 25,
        round: 2,
        totalRounds: 5,
    };

    const chatMessages = [
        { id: 1, system: true, message: "PlayerOne joined the lobby." },
        { id: 2, system: true, message: "GhostRider left the lobby." },
        { id: 3, system: false, from: "PlayerTwo", message: "Hi everyone!" },
        { id: 4, system: false, from: "PlayerOne", message: "Ready to play?" },
    ];

    const [inputMessage, setInputMessage] = useState("");

    return (
        <div className="w-full flex justify-center">
            <div className="w-full max-w-6xl flex flex-col md:flex-row gap-6 p-6 text-text-primary">

                {/* LEFT SIDE */}
                <div className="flex-1 flex flex-col gap-6">

                    {/* ROUND HEADER */}
                    <div className="bg-bg-secondary border border-border-primary rounded-xl shadow p-4 flex items-center justify-between">
            <span className="text-lg font-semibold">
              Round {lobbySettings.round} / {lobbySettings.totalRounds}
            </span>
                    </div>

                    {/* PLAYER LIST */}
                    <div className="bg-bg-secondary border border-border-primary rounded-xl shadow p-4 flex flex-col flex-1">
                        <div className="flex items-center justify-between mb-3 pr-[140px]">
                            <div className="flex items-center justify-between gap-3">
                                <h2 className="text-lg font-semibold">Players</h2>
                                <button className="px-4 py-1 bg-accent-primary text-white rounded-lg hover:bg-accent-secondary transition">
                                    Invite
                                </button>
                            </div>

                            <span className="text-sm text-text-secondary">Score</span>
                        </div>

                        <div className="flex flex-col gap-3 flex-1">

                            {players.map((player) => (
                                <div
                                    key={player.id}
                                    className="flex items-center justify-between bg-bg-tertiary p-3 rounded-lg border border-border-primary min-h-[56px]"
                                >
                                    {/* Name + status + crown */}
                                    <div className="flex items-center gap-3">
                    <span
                        className={`w-3 h-3 rounded-full ${
                            player.online ? "bg-green-500" : "bg-gray-500"
                        }`}
                    ></span>

                                        <span className="font-medium flex items-center gap-1">
                      {player.name}
                                            {player.id === ownerId && (
                                                <Crown className="w-4 h-4 text-yellow-400" />
                                            )}
                    </span>
                                    </div>

                                    {/* RIGHT SIDE: divider + ready + score */}
                                    <div className="flex items-center gap-6">





                                        {/* score */}
                                        <div className="text-sm font-semibold text-accent-primary w-[20px] text-right">
                                            {player.score}
                                        </div>

                                        {/* vertical line */}
                                        <div className="w-px h-8 bg-border-primary"></div>

                                        {/* ready button */}
                                        <button
                                            className={`px-2 py-1 rounded text-sm border border-border-primary transition w-[90px] text-center ${
                                                player.ready
                                                    ? "bg-green-600 text-white"
                                                    : "bg-bg-secondary text-text-secondary"
                                            }`}
                                        >
                                            {player.ready ? "Ready" : "Not Ready"}
                                        </button>

                                    </div>
                                </div>
                            ))}

                            {/* EXTRA SPACE ABOVE READY BUTTON */}
                            <div className="h-50"></div>
                        </div>

                        {/* BIG READY BUTTON */}
                        <button className="mt-2 w-full py-2 rounded-lg bg-accent-primary text-white font-semibold hover:bg-accent-secondary transition">
                            Ready Up
                        </button>
                    </div>

                    {/* LOBBY SETTINGS */}
                    <div className="bg-bg-secondary border border-border-primary rounded-xl shadow p-4">
                        <h2 className="text-lg font-semibold mb-3">Lobby Settings</h2>

                        <div className="space-y-2 text-sm">
                            <p>
                                Board size:{" "}
                                <span className="font-semibold">
                  {lobbySettings.rows} × {lobbySettings.cols}
                </span>
                            </p>
                            <p>
                                Mines: <span className="font-semibold">{lobbySettings.mines}</span>
                            </p>
                        </div>
                    </div>
                </div>

                {/* CHAT */}
                <div className="w-full md:w-1/3 flex flex-col bg-bg-secondary border border-border-primary rounded-xl shadow overflow-hidden">

                    <div className="border-b border-border-primary p-4">
                        <h2 className="text-lg font-semibold">Chat</h2>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                        {chatMessages.map((msg) => (
                            <div key={msg.id}>
                                {msg.system ? (
                                    <div className="text-center text-xs text-text-secondary italic">
                                        {msg.message}
                                    </div>
                                ) : (
                                    <div className="flex flex-col">
                    <span className="text-xs text-text-secondary mb-0.5">
                      {msg.from}
                    </span>
                                        <div className="bg-bg-tertiary border border-border-primary rounded-lg p-2 text-sm">
                                            {msg.message}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    <div className="p-3 border-t border-border-primary flex gap-2">
                        <input
                            type="text"
                            placeholder="Write a message..."
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            className="flex-1 bg-bg-tertiary border border-border-primary rounded-lg px-3 py-1 text-sm outline-none"
                        />

                        <button className="px-4 py-1 bg-accent-primary text-white rounded-lg hover:bg-accent-secondary transition">
                            Send
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
