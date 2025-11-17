import React, { createContext, useEffect, useRef, useState } from "react";

export const NotificationContext = createContext({
    socket: null,
    lastMessage: null,
});

export function NotificationProvider({ children }) {
    const [socket, setSocket] = useState(null);
    const [lastMessage, setLastMessage] = useState(null);

    const reconnectTimeout = useRef(null);
    const isUnmounted = useRef(false);

    //potem cos z tym zrobie jesli bedzie trzeba
    const WS_URL = "ws://localhost:8000/api/ws";

    function connectWebSocket() {
        if (isUnmounted.current) return;

        console.log("[NotificationWS] Próba połączenia...");

        const ws = new WebSocket(WS_URL);
        setSocket(ws);

        ws.onopen = () => {
            console.log("[NotificationWS] ✔ Połączono");
        };

        ws.onmessage = (event) => {
            console.log("[NotificationWS] Otrzymano wiadomość:", event);
            setLastMessage(event.data);
        };

        ws.onerror = (err) => {
            console.error("[NotificationWS] Błąd websocketu:", err);
        };

        ws.onclose = () => {
            console.warn("[NotificationWS] Rozłączono. Próba ponownego połączenia w 2 sek...");
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
            if (socket) socket.close();
        };
    }, []);

    return (
        <NotificationContext.Provider value={{ socket, lastMessage }}>
            {children}
        </NotificationContext.Provider>
    );
}
