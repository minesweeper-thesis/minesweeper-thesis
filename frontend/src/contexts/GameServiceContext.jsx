import React, {createContext, useContext, useEffect, useRef, useState} from "react";

export const GameServiceContext = createContext({
    socket: null,
    lastMessage: null,
});

export function GameServiceProvider({ children }) {
    const [socket, setSocket] = useState(null);
    const [lastMessage, setLastMessage] = useState(null);
    const [lobby, setLobby] = useState(null);
    let creatingLobbyPromise = null;

    const reconnectTimeout = useRef(null);
    const isUnmounted = useRef(false);

    //potem cos z tym zrobie jesli bedzie trzeba
    const WS_URL = "ws://localhost:8000/api/ws";

    const socketRef = useRef(null);

    function connectWebSocket() {
        if (isUnmounted.current || socketRef.current) return;

        console.log("[NotificationWS] Próba połączenia...");

        const ws = new WebSocket(WS_URL);
        socketRef.current = ws;

        ws.onopen = () => console.log("[NotificationWS] ✔ Połączono");

        ws.onmessage = (event) => {
            console.log("[NotificationWS] Otrzymano wiadomość:", event);
            setLastMessage(event.data);
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
        }}>
            {children}
        </GameServiceContext.Provider>
    );
}

export const useGame = () => useContext(GameServiceContext);
