import { useCallback, useEffect, useRef } from "react";
import { GameState } from "../utility";

export default function useMultiplayerWebSocket(interpreter, boardRef, gameState) {
    const socketRef = useRef(null);
    const reconnectTimer = useRef(null);
    const manualClose = useRef(false);

    const MAX_RETRIES = 8;
    const retryCount = useRef(0);

    const send = useCallback((msg) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify(msg));
        }
    }, []);

    const connect = useCallback((url) => {
        if (!url) return;

        manualClose.current = false;

        if (socketRef.current) {
            socketRef.current.close(1000, "Reconnect");
        }

        console.log("[WS] Connecting:", url);

        const ws = new WebSocket(url);
        socketRef.current = ws;

        ws.onopen = () => {
            console.log("[WS] OPEN", url);
            retryCount.current = 0;
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                const commands = interpreter(data);

                if (Array.isArray(commands) && commands.length > 0) {
                    boardRef?.current?.dispatchCommand(commands);
                }

            } catch (err) {
                console.error("[WS] parse error", err);
            }
        };

        ws.onclose = () => {
            if (manualClose.current) {
                console.log("[WS] manual close → no reconnect");
                return;
            }

            if (gameState === GameState.WON || gameState === GameState.LOST) {
                console.log("[WS] game over → no reconnect");
                return;
            }

            if (retryCount.current < MAX_RETRIES) {
                retryCount.current++;
                const delay = Math.min(2000 * retryCount.current, 8000);

                console.log(`[WS] reconnect in ${delay}ms`);

                reconnectTimer.current = setTimeout(() => connect(url), delay);
            }
        };
    }, [interpreter, boardRef, gameState]);
    
    const close = useCallback(() => {
        manualClose.current = true;

        clearTimeout(reconnectTimer.current);

        if (socketRef.current) {
            socketRef.current.close(1000, "manual close");
        }
    }, []);

    useEffect(() => {
        return () => {
            close();
        };
    }, []);

    return {
        open: connect,
        close,
        send,
        socketRef,
    };
}
