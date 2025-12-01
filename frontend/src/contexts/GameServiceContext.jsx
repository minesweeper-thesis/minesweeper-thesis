import React, {createContext, useContext, useEffect, useRef, useState} from "react";
import {useAuth} from "./AuthContext";

export const GameServiceContext = createContext({
    socket: null,
    lastMessage: null,
});

export function GameServiceProvider({ children }) {
    const { user } = useAuth();
    const [socket, setSocket] = useState(null);
    const [lastMessage, setLastMessage] = useState(null);
    const [lobby, setLobby] = useState(null);
    const [chatMessages, setChatMessages] = useState([]);
    const [gotLobby, setGotLobby] = useState(false);
    let creatingLobbyPromise = null;

    const reconnectTimeout = useRef(null);
    const isUnmounted = useRef(false);

    const WS_URL = "api/ws";

    const socketRef = useRef(null);

    const msgListenersRef = useRef(new Set());

    function addMessageListener(fn) {
        msgListenersRef.current.add(fn);
        return () => msgListenersRef.current.delete(fn);
    }

    function removeMessageListener(fn) {
        msgListenersRef.current.delete(fn);
    }

    function notifyListeners(msg) {
        for (const fn of Array.from(msgListenersRef.current)) {
            try { fn(msg); } catch (e) { console.error("msg listener error", e); }
        }
    }

    function safeJsonParse(str) {
        try {
            return JSON.parse(str);
        } catch (e) {
            console.error("WS JSON parse error:", e);
            return null;
        }
    }


    function connectWebSocket() {
        if (isUnmounted.current || socketRef.current) return;

        console.log("[NotificationWS] Próba połączenia...");

        const ws = new WebSocket(WS_URL);
        socketRef.current = ws;
        setSocket(ws);

        ws.onopen = () => console.log("[NotificationWS] ✔ Połączono");

        ws.onmessage = (event) => {
            const msg = safeJsonParse(event.data);
            if (!msg) return;

            console.log("[WS] Received:", msg);

            switch (msg.type) {
                case "current_lobby":
                    if (!msg.lobby){
                        setGotLobby(false);
                        break;
                    }
                    console.log("[WS] Ustawiam current lobby:", msg.lobby);
                    setGotLobby(true);
                    setLobby(msg.lobby);
                    break;

                case "game_config_updated":
                    setLobby(prev => {
                        if (!prev) return prev;

                        return {
                            ...prev,
                            game_config: msg.game_config,
                        };
                    });
                    break;

                case "invitation":
                case "friend_request":
                    setLastMessage(msg);
                    break;

                case "user_connection_status":
                    handleUserStatus(msg);
                    break;


                case "ready":
                    notifyListeners(msg);
                    break;

                default:
                    break;
            }


        };
        ws.onerror = (err) => console.error("[NotificationWS] Błąd websocketu:", err);

        ws.onclose = () => {
            console.warn("[NotificationWS] Rozłączono. Próba ponownego połączenia w 2 sek...");
            socketRef.current = null;
            setSocket(null);
            if (!isUnmounted.current) {
                reconnectTimeout.current = setTimeout(connectWebSocket, 2000);
            }
        };
    }

    useEffect(() => {
        if (!user){
            return
        }
        connectWebSocket();

        return () => {
            isUnmounted.current = true;
            if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
            if (socketRef.current) socketRef.current.close();
        };
    }, [user]);

    const addLobbyMessage = (text) => {
        setChatMessages(prev => [
            ...prev,
            {
                id: crypto.randomUUID(),
                system: true,
                text,
                timestamp: new Date().toISOString(),
            }
        ]);
    };

    const leaveLobby = async () => {
        if (!lobby) return;

        try {
            await authFetch(`/api/lobbies/${lobby.id}/leave`, {
                method: "POST",
            });

            addLobbyMessage("You left the lobby.");

            setLobby(null);

            return true;
        } catch (err) {
            console.error("Error leaving lobby:", err);
            return false;
        }
    };


    const handleUserStatus = (msg) => {
        if (!msg.user || !msg.status) return;

        setLobby(prev => {
            if (!prev) return prev;

            if (msg.lobby_id !== prev.id) return prev;

            const user_ = msg.user;

            if (msg.status === "connected") {
                const exists = prev.users.some(u => u.id === user_.id);
                if (exists) return prev;

                const updated = {
                    ...prev,
                    users: [...prev.users, user_]
                };

                addLobbyMessage(`${user_.nickname} joined the lobby.`);
                return updated;
            }

            if (msg.status === "disconnected") {
                const updated = {
                    ...prev,
                    users: prev.users.filter(u => u.id !== user_.id),
                };

                addLobbyMessage(`${user_.nickname} left the lobby.`);
                return updated;
            }

            return prev;
        });
    };



    const authFetch = async (url, options = {}) => {
        const res = await fetch(url, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
            credentials: 'include',
        });
        if (!res.ok) {
            const text = await res.text();
            throw new Error(text || res.statusText);
        }
        return res.json();
    };



// CREATE LOBBY
    const createLobby = async () => {
        if (creatingLobbyPromise) {
            return creatingLobbyPromise;
        }

        creatingLobbyPromise = (async () => {
            try {
                const response = await authFetch("/api/lobbies", { method: "POST" });

                setLobby(response);
                return response;
            } catch (err) {
                console.error("Error creating lobby:", err);
                throw err;
            } finally {
                creatingLobbyPromise = null;
            }
        })();

        return creatingLobbyPromise;
    };

// SEND LOBBY INVITATION
    const sendLobbyInvitation = async (userId) => {
        const currentLobby = lobby || await createLobby();

        try {
            const response = await authFetch(
                `/api/lobbies/${currentLobby.id}/invitations`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ user_id: userId })
                }
            );

            console.log("Invitation sent:", response);
            return response;
        } catch (err) {
            console.error("Error sending invitation:", err);
            throw err;
        }
    };

    // REJECT INVITATION
    const rejectGameInvite = async (invitationId) => {
        try {
            const response = await authFetch(`api/invitations/${invitationId}`, {
                method: "DELETE",
            });
            console.log("Invitation rejected:", response);
            return response;
        } catch (err) {
            console.error("Error rejecting invitation:", err);
            throw err;
        }
    };

// ACCEPT INVITATION
    const acceptGameInvite = async (invitationId, lobbyId) => {
        try {
            const response = await authFetch(`/api/lobbies/${lobbyId}/join`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ invitation_id: invitationId })
            });
            console.log("Invitation accepted:", response);

            setLobby(response);

            return response;
        } catch (err) {
            console.error("Error accepting invitation:", err);
            throw err;
        }
    };

    // UPDATE LOBBY SETTINGS
    const updateLobbySettings = async (settings) => {
        if (!lobby) {
            console.warn("updateLobbySettings: No active lobby.");
            return null;
        }

        try {
            console.log("[Lobby] Updating settings:", settings);

            const response = await authFetch(
                `/api/lobbies/${lobby.id}`,
                {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(settings)
                }
            );


        } catch (err) {
            console.error("[Lobby] Error updating settings:", err);
            throw err;
        }
    };

    const isHost = () => {
        if (!lobby || !user) return false;
        if (!lobby.host || !lobby.host.id) return false;

        return lobby.host.id === user.id;
    };



    const getLobby = async () => {
        if (gotLobby && lobby === null) {
            console.log("Lobby:", lobby);
            return await createLobby();
        }

        return lobby;
    }


    return (
        <GameServiceContext.Provider value={{
            socket,
            lastMessage,
            sendLobbyInvitation,
            createLobby,
            getLobby,
            acceptGameInvite,
            rejectGameInvite,
            lobby,
            chatMessages,
            addLobbyMessage,
            leaveLobby,
            authFetch,
            addMessageListener,
            removeMessageListener,
            updateLobbySettings,
            isHost,
        }}>
            {children}
        </GameServiceContext.Provider>
    );
}

export const useGame = () => useContext(GameServiceContext);
