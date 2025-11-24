import { useEffect, useRef, useCallback } from "react";

export default function useGameWebSocket(url, interpreter, boardRef) {
    const socketRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const manuallyClosedRef = useRef(false);
    const retryAttemptRef = useRef(0);
    const MAX_RETRIES = 10;

    const send = useCallback((msg) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify(msg));
        }
    }, []);

    const connect = useCallback(() => {
        if (!url || manuallyClosedRef.current || socketRef.current) return;

        const ws = new WebSocket(url);
        socketRef.current = ws;

        ws.onopen = () => {
            retryAttemptRef.current = 0;
            // send({ type: "game_state"});
            console.log("[WebSocket] ConnectedL: ", url);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log("[WebSocket] Received message", data);
                const commands = interpreter(data) || [];
                if (Array.isArray(commands) && boardRef?.current?.dispatchCommand) {
                    boardRef.current.dispatchCommand(commands);
                }
            } catch (e) {
                console.error("[WebSocket] Error parsing message", e);
            }
        };

        ws.onerror = (err) => {
            console.error("[WebSocket] Error", err);
            // ws.close();
        };

        ws.onclose = () => {
            socketRef.current = null;
            if (manuallyClosedRef.current) return;

            if (retryAttemptRef.current < MAX_RETRIES) {
                const delay = Math.min(1000 * 2 ** retryAttemptRef.current, 10000);
                reconnectTimeoutRef.current = setTimeout(() => {
                    retryAttemptRef.current += 1;
                    connect();
                }, delay);
            }
        };
    }, [url, interpreter, boardRef]);

    useEffect(() => {
        manuallyClosedRef.current = false;
        connect();

        return () => {
            manuallyClosedRef.current = true;
            clearTimeout(reconnectTimeoutRef.current);
            socketRef.current?.close();
        };
    }, [connect]);

    return { send, socketRef };
}
