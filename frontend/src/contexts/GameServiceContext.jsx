import React, {createContext, useContext, useEffect, useRef, useState} from "react";

export const GameServiceContext = createContext({
    socket: null,
    lastMessage: null,
});

export function GameServiceProvider({ children }) {
    const [socket, setSocket] = useState(null);
    const [lastMessage, setLastMessage] = useState(null);
    const [lobby, setLobby] = useState(null);
    const [chatMessages, setChatMessages] = useState([]);
    let creatingLobbyPromise = null;

    const reconnectTimeout = useRef(null);
    const isUnmounted = useRef(false);

    const WS_URL = "api/ws";

    const socketRef = useRef(null);

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

        ws.onopen = () => console.log("[NotificationWS] ✔ Połączono");

        ws.onmessage = (event) => {
            const msg = safeJsonParse(event.data);
            if (!msg) return;

            console.log("[WS] Received:", msg);

            switch (msg.type) {
                case "current_lobby":
                    console.log("[WS] Ustawiam current lobby:", msg.lobby);
                    setLobby(msg.lobby);
                    break;

                case "invitation":
                case "friend_request":
                    setLastMessage(msg);
                    break;


                case "user_connection_status":
                    handleUserStatus(msg);
                    break;

                default:
                    console.warn("[WS] Nieznany typ wiadomości:", msg.type);
            }
        };
        ws.onerror = (err) => console.error("[NotificationWS] Błąd websocketu:", err);

        ws.onclose = () => {
            console.warn("[NotificationWS] Rozłączono. Próba ponownego połączenia w 2 sek...");
            socketRef.current = null;
            if (!isUnmounted.current) {
                reconnectTimeout.current = setTimeout(connectWebSocket, 2000);
            }
        };
    }

    useEffect(() => {
        connectWebSocket();

        return () => {
            isUnmounted.current = true;
            if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
            if (socketRef.current) socketRef.current.close();
        };
    }, []);

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

            const user = msg.user;

            if (msg.status === "connected") {
                const exists = prev.users.some(u => u.id === user.id);
                if (exists) return prev;

                const updated = {
                    ...prev,
                    users: [...prev.users, user]
                };

                addLobbyMessage(`${user.nickname} joined the lobby.`);
                return updated;
            }

            if (msg.status === "disconnected") {
                const updated = {
                    ...prev,
                    users: prev.users.filter(u => u.id !== user.id),
                };

                addLobbyMessage(`${user.nickname} left the lobby.`);
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
                    body: JSON.stringify({ user_id: userId }) // <-- dane w body
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

            return response;
        } catch (err) {
            console.error("Error accepting invitation:", err);
            throw err;
        }
    };


    const getLobby = async () => {
        return lobby || await createLobby();
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
        }}>
            {children}
        </GameServiceContext.Provider>
    );
}

export const useGame = () => useContext(GameServiceContext);
