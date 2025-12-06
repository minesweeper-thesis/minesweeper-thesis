import React, {useEffect, useRef, useState} from "react";
import { useGame } from "../contexts/GameServiceContext";
import { Crown } from "lucide-react";
import InvitePopup from "../components/InvitePopup";
import {useSession} from "../contexts/SessionContext";
import {useNavigate} from "react-router-dom";
import LobbySettingsPopup from "../components/LobbySettingsPopup";

export default function MultiplayerLobby() {
    const { lobby, chatMessages, leaveLobby, getLobby, addLobbyMessage, updateLobbySettings, isHost } = useGame();
    const { sessionId, send, round } = useSession();
    const navigate = useNavigate();
    const { status } = useSession();
    const [inputMessage, setInputMessage] = useState("");
    const [showInvitePopup, setShowInvitePopup] = useState(false);
    const [showSettingsPopup, setShowSettingsPopup] = useState(false);
    const chatRef = useRef(null);

    useEffect(() => {
        if (!lobby) {
            getLobby().catch(err => console.error(err));
        }
    }, [lobby, getLobby]);

    useEffect(() => {
        console.log("lobby status", status);
        if (status === "game"){
            navigate("/game");
        }
    }, [status]);

    useEffect(() => {
        if (!chatRef.current) return;

        chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }, [chatMessages]);


    if (!lobby) {
        return (
            <div className="w-full flex justify-center items-center h-full text-text-primary">
                Loading lobby...
            </div>
        );
    }

    const players = lobby?.users?.map(u => ({
        id: u.id,
        name: u.nickname,
        online: true,
        ready: false,
        score: 0,
    })) || [];

    const ownerId = lobby.host.id;


    const sendReady = async () => {
        if (sessionId){
            send({ type: "ready"});
            return;
        }

        try {
            const res = await fetch(`api/lobbies/${lobby.id}/ready`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
            });

            if (!res.ok) {
                const txt = await res.text();
                console.log(`${txt}`);
                throw new Error(txt || res.statusText);
            }

            addLobbyMessage("You marked ready.");
        } catch (err) {
            console.error("Ready error:", err);
            addLobbyMessage("Ready request failed.");
        }
    };

    const sendChatMessage = async () => {
        if (!inputMessage.trim()) return;

        try {
            const res = await fetch(`api/lobbies/${lobby.id}/chat-messages`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ content: inputMessage }),
            });

            if (!res.ok) {
                const txt = await res.text();
                console.error(txt);
                return;
            }

            setInputMessage("");
        } catch (err) {
            console.error("Chat send error:", err);
        }
    };


    return (
        <div className="w-full flex justify-center">
            <div className="w-full max-w-6xl flex flex-col md:flex-row gap-6 p-6 text-text-primary">
                {/* LEFT SIDE */}
                <div className="flex-1 flex flex-col gap-6">
                    {/* ROUND HEADER */}
                    <div className="bg-bg-secondary border border-border-primary rounded-xl shadow p-4 flex items-center justify-between">
                        <span className="text-lg font-semibold">Round {round ?? "-"} / {lobby.game_config?.rounds}</span>

                        <button
                            onClick={async () => {
                                const ok = await leaveLobby();
                                if (ok) {
                                    navigate("/");
                                }
                            }}
                            className="px-4 py-1 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
                        >
                            Leave
                        </button>
                    </div>

                    {/* PLAYER LIST */}
                    <div className="bg-bg-secondary border border-border-primary rounded-xl shadow p-4 flex flex-col flex-1">
                        <div className="flex items-center justify-between mb-3 pr-[140px]">
                            <div className="flex items-center justify-between gap-3">
                                <h2 className="text-lg font-semibold">Players</h2>

                                <button
                                    className="px-4 py-1 bg-accent-primary text-white rounded-lg hover:bg-accent-secondary transition"
                                    onClick={() => setShowInvitePopup(true)}
                                >
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

                                    <div className="flex items-center gap-6">
                                        <div className="text-sm font-semibold text-accent-primary w-[20px] text-right">
                                            {player.score}
                                        </div>
                                        <div className="w-px h-8 bg-border-primary"></div>
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

                            <div className="h-50"></div>
                        </div>

                        <button
                            onClick={sendReady}
                            className="mt-2 w-full py-2 rounded-lg bg-accent-primary text-white font-semibold hover:bg-accent-secondary transition"
                        >
                            Ready Up
                        </button>
                    </div>

                    {/* LOBBY SETTINGS */}
                    <div className="bg-bg-secondary border border-border-primary rounded-xl shadow p-4">
                        <h2 className="text-lg font-semibold mb-3">Lobby Settings</h2>

                        {/* Dwie kolumny – responsywne */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mb-4">

                            <div className="space-y-2">
                                <p>
                                    <span className="text-text-muted">Board size:</span>{" "}
                                    <span className="font-semibold">
                                        {lobby.game_config?.difficulty_level?.rows} × {lobby.game_config?.difficulty_level?.columns}
                                    </span>
                                                    </p>

                                                    <p>
                                                        <span className="text-text-muted">Mines:</span>{" "}
                                                        <span className="font-semibold">
                                        {lobby.game_config?.difficulty_level?.mine_count}
                                    </span>
                                </p>

                                <p>
                                    <span className="text-text-muted">Rounds:</span>{" "}
                                    <span className="font-semibold">{lobby.game_config?.rounds}</span>
                                </p>

                                <p>
                                    <span className="text-text-muted">Max round time:</span>{" "}
                                    <span className="font-semibold">{lobby.game_config?.max_round_time}s</span>
                                </p>
                            </div>

                            <div className="space-y-2">
                                <p>
                                    <span className="text-text-muted">Mode:</span>{" "}
                                    <span className="font-semibold capitalize">{lobby.game_config?.game_mode}</span>
                                </p>

                                <p>
                                    <span className="text-text-muted">Generator:</span>{" "}
                                    <span className="font-semibold">{lobby.game_config?.generator_type}</span>
                                </p>

                                <p>
                                    <span className="text-text-muted">Classifier:</span>{" "}
                                    <span className="font-semibold">{lobby.game_config?.generator_settings?.classifier}</span>
                                </p>

                                <p>
                                    <span className="text-text-muted">Heuristic:</span>{" "}
                                    <span className="font-semibold">{lobby.game_config?.generator_settings?.heuristic}</span>
                                </p>
                            </div>

                        </div>

                        {isHost() && sessionId === null && (
                            <button
                                onClick={() => setShowSettingsPopup(true)}
                                className="px-3 py-2 bg-accent-primary text-white rounded-lg w-full md:w-auto"
                            >
                                Edit Settings
                            </button>
                        )}
                    </div>


                </div>

                {/* CHAT */}
                <div className="w-full md:w-1/3 flex flex-col bg-bg-secondary border border-border-primary rounded-xl shadow overflow-hidden max-h-[60vh]">
                <div className="border-b border-border-primary p-4">
                        <h2 className="text-lg font-semibold">Chat</h2>
                    </div>

                    <div
                        ref={chatRef}
                        className="flex-1 h-0 overflow-y-auto p-4 space-y-3"
                    >

                        {chatMessages.length === 0 ? (
                            <div className="text-center text-xs text-text-secondary italic">
                                No messages yet
                            </div>
                        ) : (
                            chatMessages.map(m => (
                                <div key={m.id} className="text-sm">
                                    <span className="text-text-secondary">
                                        [{m.timestamp ? new Date(m.timestamp * 1000).toLocaleTimeString() : "--:--"}]
                                    </span>{" "}

                                    {m.nick ? (
                                        <span>
                                            <span className="font-bold">{m.nick}</span>: {m.text}
                                        </span>
                                    ) : (
                                        <span className="italic text-text-secondary">{m.text}</span>
                                    )}
                                </div>

                            ))
                        )}
                    </div>

                    <div className="p-3 border-t border-border-primary flex gap-2">
                        <input
                            type="text"
                            placeholder="Write a message..."
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    sendChatMessage();
                                }
                            }}
                            className="flex-1 bg-bg-tertiary border border-border-primary rounded-lg px-3 py-1 text-sm outline-none"
                        />

                        <button
                            onClick={sendChatMessage}
                            className="px-4 py-1 bg-accent-primary text-white rounded-lg hover:bg-accent-secondary transition"
                        >
                            Send
                        </button>
                    </div>

                </div>
                {showInvitePopup && <InvitePopup onClose={() => setShowInvitePopup(false)} />}
                {showSettingsPopup && (
                    <LobbySettingsPopup
                        onClose={() => setShowSettingsPopup(false)}
                        config={lobby.game_config}
                        onSave={updateLobbySettings}
                    />
                )}

            </div>
        </div>
    );
}
