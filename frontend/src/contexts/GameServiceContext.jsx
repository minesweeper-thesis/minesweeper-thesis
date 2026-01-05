import React, {
    createContext,
    useContext,
    useEffect,
    useRef,
    useState
} from "react";
import { useAuth } from "./AuthContext";

export const GameServiceContext = createContext({
    socket: null,
    lastMessage: null,
});

export function GameServiceProvider({ children }) {
    const { user } = useAuth();

    const [notificationSocket, setNotificationSocket] = useState(null);
    const [isWsConnected, setIsWsConnected] = useState(false);

    const [lobbySocket, setLobbySocket] = useState(null);

    const [lastMessage, setLastMessage] = useState(null);
    const [lobby, setLobby] = useState(null);
    const [chatMessages, setChatMessages] = useState([]);
    const [gotLobby, setGotLobby] = useState(false);

    const creatingLobbyPromise = useRef(null);

    const notificationSocketRef = useRef(null);
    const lobbySocketRef = useRef(null);

    const reconnectTimeout = useRef(null);
    const isUnmounted = useRef(false);

    const msgListenersRef = useRef(new Set());


    const WS_NOTIFICATION_URL = "api/ws";
    const WS_GAME_BASE_URL = "api/game/multi";

    function safeJsonParse(str) {
        try {
            return JSON.parse(str);
        } catch (e) {
            console.error("WS JSON parse error:", e);
            return null;
        }
    }

    function addMessageListener(fn) {
        msgListenersRef.current.add(fn);
        return () => msgListenersRef.current.delete(fn);
    }

    function removeMessageListener(fn) {
        msgListenersRef.current.delete(fn);
    }

    function notifyListeners(msg) {
        for (const fn of Array.from(msgListenersRef.current)) {
            try {
                fn(msg);
            } catch (e) {
                console.error("msg listener error", e);
            }
        }
    }

    function connectNotificationSocket() {
        if (isUnmounted.current || notificationSocketRef.current) return;

        const ws = new WebSocket(WS_NOTIFICATION_URL);
        notificationSocketRef.current = ws;
        setNotificationSocket(ws);

        ws.onopen = () => {
            console.log("[WS /ws] connected");
            setIsWsConnected(true);
        }

        ws.onmessage = (event) => {
            const msg = safeJsonParse(event.data);

            if (!msg) return;
            console.log("[WS /ws] msg: ", msg);
            switch (msg.type) {
                case "current_lobby":
                    setGotLobby(true);
                    setLobby(applyInitialStatuses(msg.lobby));
                    break;
                case "invitation":
                case "friend_request":
                case "user_online_status":
                    setLastMessage(msg);
                    break;

                default:
                    forwardToLobbySocket(msg);
                    break;
            }
        };

        ws.onclose = () => {
            notificationSocketRef.current = null;
            setNotificationSocket(null);
            setIsWsConnected(false);
            if (!isUnmounted.current) {
                reconnectTimeout.current = setTimeout(
                    connectNotificationSocket,
                    2000
                );
            }
        };

        ws.onerror = (err) => {
            console.error("[WS /ws] error", err);
            setIsWsConnected(false);
        };
    }

    function connectLobbySocket(lobbyId, invitationId = null) {
        if (lobbySocketRef.current) return;

        const url = invitationId
            ? `${WS_GAME_BASE_URL}/${lobbyId}?invitation_id=${invitationId}`
            : `${WS_GAME_BASE_URL}/${lobbyId}`;

        const ws = new WebSocket(url);
        lobbySocketRef.current = ws;
        setLobbySocket(ws);

        ws.onopen = () =>
            console.log("[WS lobby] connected", lobbyId);

        ws.onmessage = (event) => {
            const msg = safeJsonParse(event.data);
            if (!msg) return;
            console.log("[WS lobby] msg: ", msg);

            switch (msg.type) {
                case "current_lobby":
                    setGotLobby(true);
                    setLobby(applyInitialStatuses(msg.lobby));
                    break;

                case "game_config_updated":
                    setLobby(prev =>
                        prev
                            ? { ...prev, game_config: msg.game_config }
                            : prev
                    );
                    break;

                case "user_ready":
                    handleUserReady(msg);
                    break;

                case "user_connection_status":
                    handleUserStatus(msg);
                    break;

                case "round_ready":
                case "round_countdown":
                    notifyListeners(msg);
                    break;

                case "session_state":
                    notifyListeners(msg);
                    break;
                case "lobby_chat_message":
                    addLobbyMessage(
                        msg.content,
                        msg.sender?.nickname,
                        msg.timestamp
                    );
                    break;

                default:
                    break;
            }
        };

        ws.onclose = () => {
            lobbySocketRef.current = null;
            setLobbySocket(null);
            setLobby(null);
            setChatMessages([]);
            setGotLobby(false);
        };
    }

    function forwardToLobbySocket(msg) {
        if (!lobbySocketRef.current) return;
        try {
            lobbySocketRef.current.send(JSON.stringify(msg));
        } catch (_) {}
    }

    useEffect(() => {
        if (!user) return;

        connectNotificationSocket();

        return () => {
            isUnmounted.current = true;
            notificationSocketRef.current?.close();
            lobbySocketRef.current?.close();
            if (reconnectTimeout.current)
                clearTimeout(reconnectTimeout.current);
        };
    }, [user]);

    useEffect(() => {
        if (!lobby) return;

        const fetchChatHistory = async () => {
            try {
                const res = await fetch(
                    `api/lobbies/${lobby.id}/chat-messages`,
                    { credentials: "include" }
                );
                if (!res.ok) return;

                const data = await res.json();
                const mapped = data.items
                    .map(msg => ({
                        id: crypto.randomUUID(),
                        system: false,
                        text: msg.content,
                        nick: msg.sender?.nickname ?? null,
                        timestamp: msg.timestamp,
                    }))
                    .reverse();

                setChatMessages(mapped);
            } catch (err) {
                console.error("Chat history error:", err);
            }
        };

        fetchChatHistory();
    }, [lobby?.id]);

    useEffect(() => {
        if (!lobby) return;

        if (!lobbySocketRef.current) {
            connectLobbySocket(lobby.id);
        }
    }, [lobby]);


    const applyInitialStatuses = (incomingLobby) => {
        if (!incomingLobby) return null;
        return {
            ...incomingLobby,
            users: incomingLobby.users.map(u => ({
                ...u,
                status: u.is_online ? "not_ready" : "offline"
            }))
        };
    };

    const resetReady = () => {
        setLobby(applyInitialStatuses(lobby));
    };

    const addLobbyMessage = (
        text,
        nick = null,
        timestamp = null,
        system = false
    ) => {
        setChatMessages(prev => [
            ...prev,
            {
                id: crypto.randomUUID(),
                system,
                text,
                nick,
                timestamp
            }
        ]);
    };

    const handleUserReady = (msg) => {
        setLobby(prev => {
            if (!prev) return prev;
            return {
                ...prev,
                users: prev.users.map(u =>
                    u.id === msg.user_id
                        ? {
                            ...u,
                            status: msg.value
                                ? "ready"
                                : "not_ready"
                        }
                        : u
                )
            };
        });
    };

    const handleUserStatus = (msg) => {
        if (!msg.user || !msg.status) return;

        setLobby(prev => {
            if (!prev || msg.lobby_id !== prev.id) return prev;

            if (msg.status === "connected") {
                if (prev.users.some(u => u.id === msg.user.id))
                    return prev;

                addLobbyMessage(
                    " joined the lobby.",
                    msg.user.nickname,
                    null,
                    true
                );

                return {
                    ...prev,
                    users: [...prev.users, msg.user]
                };
            }

            if (msg.status === "disconnected") {
                addLobbyMessage(
                    " left the lobby.",
                    msg.user.nickname,
                    null,
                    true
                );

                return {
                    ...prev,
                    users: prev.users.filter(
                        u => u.id !== msg.user.id
                    )
                };
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
            credentials: "include",
        });
        if (!res.ok) {
            const text = await res.text();
            throw new Error(text || res.statusText);
        }
        return res.json();
    };

    const createLobby = async () => {
        if (creatingLobbyPromise.current)
            return creatingLobbyPromise.current;

        creatingLobbyPromise.current = (async () => {
            try {
                const response = await authFetch("api/lobbies", {
                    method: "POST",
                });
                setLobby(response);
                return response;
            } finally {
                creatingLobbyPromise.current = null;
            }
        })();

        return creatingLobbyPromise.current;
    };

    const getLobby = async () => {
        if (gotLobby && lobby === null) {
            return await createLobby();
        }
        return lobby;
    };

    const sendLobbyInvitation = async (userId) => {
        const currentLobby = lobby || await createLobby();

        return authFetch(
            `api/lobbies/${currentLobby.id}/invitations`,
            {
                method: "POST",
                body: JSON.stringify({ user_id: userId })
            }
        );
    };

    const rejectGameInvite = async (invitationId) => {
        return authFetch(`api/invitations/${invitationId}`, {
            method: "DELETE",
        });
    };

    const acceptGameInvite = async (invitationId, lobbyId) => {
        connectLobbySocket(lobbyId, invitationId);
    };

    const updateLobbySettings = async (settings) => {
        if (!lobby) return null;

        return authFetch(`/api/lobbies/${lobby.id}`, {
            method: "PUT",
            body: JSON.stringify(settings)
        });
    };

    const leaveLobby = () => {
        lobbySocketRef.current?.close();
        lobbySocketRef.current = null;
        setLobby(null);
        setChatMessages([]);
        setGotLobby(false);
    };

    const isHost = () => {
        if (!lobby || !user) return false;
        return lobby.host?.id === user.id;
    };

    function sendToLobbySocket(payload) {
        const ws = lobbySocketRef.current;

        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.warn("[WS GAME] socket not connected");
            return false;
        }

        try {
            ws.send(JSON.stringify(payload));
            return true;
        } catch (err) {
            console.error("[WS GAME] send error", err);
            return false;
        }
    }


    return (
        <GameServiceContext.Provider value={{
            socket: notificationSocket,
            lastMessage,
            lobby,
            chatMessages,
            sendLobbyInvitation,
            createLobby,
            getLobby,
            acceptGameInvite,
            rejectGameInvite,
            leaveLobby,
            authFetch,
            addMessageListener,
            removeMessageListener,
            updateLobbySettings,
            isHost,
            resetReady,
            sendToLobbySocket,
            isWsConnected
        }}>
            {children}
        </GameServiceContext.Provider>
    );
}

export const useGame = () => useContext(GameServiceContext);
