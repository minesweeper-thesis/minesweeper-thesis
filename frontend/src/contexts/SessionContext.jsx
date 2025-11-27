import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useGame } from "./GameServiceContext";

export const SessionContext = createContext(null);

/*
{
  sessionId: string | null,
  round: number | null,
  startAt: number | null,
  endAt: number | null,
  startField: [x,y] | null,
  status: "lobby | game"
}
*/

export function SessionProvider({ children }) {
    const { addMessageListener, removeMessageListener } = useGame();

    const [sessionId, setSessionId] = useState(null);
    const [round, setRound] = useState(null);
    const [startAt, setStartAt] = useState(null);
    const [endAt, setEndAt] = useState(null);
    const [startField, setStartField] = useState(null);
    const [status, setStatus] = useState("lobby");
    const [lastGameOver, setLastGameOver] = useState(null);

    const handleIncoming = useCallback((msg) => {
        console.log("[Session] msg: ", msg);
        if (!msg || typeof msg !== "object") return;

        switch (msg.type) {
            case "ready":
                // server tells when next round will start and provides session_id
                setSessionId(msg.session_id ?? null);
                setRound(msg.round ?? 0);
                setStartAt(msg.start_at ?? null);
                setStatus("game");
                break;

            case "round_start":
                // round has started in session socket too, but handle if arrives on global ws
                setSessionId(msg.session_id ?? sessionId);
                setRound(msg.round ?? round);
                setStartAt(msg.start_at ?? startAt);
                setEndAt(msg.end_at ?? null);
                setStartField(msg.start_field ?? null);
                break;

            case "round_end":
                setStatus("loby");
                break;

            case "game_over":
                // could be sent either on global ws or session ws; record result
                setLastGameOver(msg);
                break;

            case "session_over":
                setStatus("lobby");
                break;

            default:
                // ignore other messages here
                break;
        }
    }, [sessionId, round, startAt, status]);

    useEffect(() => {
        if (!addMessageListener) return;
        console.log("podpinam listenera")
        addMessageListener(handleIncoming);
        return () => removeMessageListener(handleIncoming);
    }, [addMessageListener, removeMessageListener, handleIncoming]);

    const resetSession = () => {
        setSessionId(null);
        setRound(null);
        setStartAt(null);
        setEndAt(null);
        setStartField(null);
        setStatus("lobby");
        setLastGameOver(null);
    };

    return (
        <SessionContext.Provider value={{
            sessionId,
            round,
            startAt,
            endAt,
            startField,
            status,
            lastGameOver,
            setSessionId,
            setRound,
            setStartAt,
            setEndAt,
            setStartField,
            setStatus,
            resetSession,
        }}>
            {children}
        </SessionContext.Provider>
    );
}

export const useSession = () => useContext(SessionContext);
