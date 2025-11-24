import {GameState} from "../utility";
import {useCallback, useEffect, useRef} from "react";

export default function useGameWebSocket(url, interpreter, boardRef, gameState) {
    const socketRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const closedByEffectRef = useRef(false);
    const retryAttemptRef = useRef(0);
    const MAX_RETRIES = 10;

    const send = useCallback((msg) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify(msg));
        }
    }, []);

    const connect = useCallback(() => {
        if (!url) return;

        if (socketRef.current) {
            socketRef.current.close(1000, "Switching connection");
        }

        closedByEffectRef.current = false;
        const ws = new WebSocket(url);
        socketRef.current = ws;

        ws.onopen = () => {
            retryAttemptRef.current = 0;
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log(data);
                const commands = interpreter(data) || [];
                if (Array.isArray(commands) && boardRef?.current?.dispatchCommand) {
                    boardRef.current.dispatchCommand(commands);
                }
            } catch (err) {
                console.error("[WebSocket] parse error", err);
            }
        };

        ws.onclose = () => {

            if (gameState === GameState.WON || gameState === GameState.LOST) return;

            if (closedByEffectRef.current) return;
            if (url !== ws.url) return;

            if (retryAttemptRef.current < MAX_RETRIES) {
                const delay = Math.min(1000 * 2 ** retryAttemptRef.current, 10000);
                reconnectTimeoutRef.current = setTimeout(() => {
                    retryAttemptRef.current += 1;
                    connect();
                }, delay);
            }
        };
    }, [url, interpreter, boardRef, gameState]);

    useEffect(() => {
        if (url) connect();

        return () => {
            closedByEffectRef.current = true;
            clearTimeout(reconnectTimeoutRef.current);

            if (socketRef.current) {
                socketRef.current.onclose = null;
                socketRef.current.close(1000, "Unmount / URL change");
            }
        };
    }, [url]);

    return { send, socketRef };
}
