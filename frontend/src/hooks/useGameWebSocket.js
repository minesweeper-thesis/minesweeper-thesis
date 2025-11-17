import { useEffect, useRef } from "react";


export default function useGameWebSocket(socketUrl, interpreter, boardRef) {
    const socketRef = useRef(null);
    const pendingRef = useRef([]);

    useEffect(() => {
        if (!socketUrl) return;

        const ws = new WebSocket(socketUrl);
        socketRef.current = ws;

        ws.onopen = () => {
            console.log("[useGameWebSocket] connected:", socketUrl);
            flushPending();
        };

        ws.onerror = (e) => {
            console.error("[useGameWebSocket] error", e);
        };

        ws.onclose = (e) => {
            console.log("[useGameWebSocket] closed", e);
        };

        ws.onmessage = (ev) => {
            try {
                const data = JSON.parse(ev.data);
                const commands = interpreter(data) || [];
                if (!Array.isArray(commands)) return;

                if (boardRef && boardRef.current && typeof boardRef.current.dispatchCommand === "function") {
                    boardRef.current.dispatchCommand(commands);
                } else {
                    pendingRef.current.push(...commands);
                }
            } catch (err) {
                console.error("[useGameWebSocket] onmessage parse error", err);
            }
        };

        function flushPending() {
            if (pendingRef.current.length === 0) return;
            if (boardRef && boardRef.current && typeof boardRef.current.dispatchCommand === "function") {
                boardRef.current.dispatchCommand(pendingRef.current);
                pendingRef.current = [];
            }
        }

        const flushInterval = setInterval(flushPending, 200);

        return () => {
            clearInterval(flushInterval);
            try { ws.close(); } catch (e) {}
            socketRef.current = null;
            pendingRef.current = [];
        };
    }, [socketUrl, interpreter, boardRef]);

    const send = (obj) => {
        if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) return false;
        socketRef.current.send(JSON.stringify(obj));
        return true;
    };

    return { send, socketRef };
}
