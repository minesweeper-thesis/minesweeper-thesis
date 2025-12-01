import React, {
    createContext,
    useContext,
    useEffect,
    useState,
    useCallback,
    useRef
} from "react";
import { useGame } from "./GameServiceContext";
import useMultiplayerWebSocket from "../hooks/useMultiplayerWebSocket";
import {GameState, State} from "../utility";
import boardInterpreter from "../utils/boardInterpreter";

export const SessionContext = createContext(null);

export function SessionProvider({ children }) {
    const { addMessageListener, removeMessageListener } = useGame();

    const [sessionId, setSessionId] = useState(null);
    const [round, setRound] = useState(null);
    const [startAt, setStartAt] = useState(null);
    const [endAt, setEndAt] = useState(null);
    const [startField, setStartField] = useState(null);
    const [status, setStatus] = useState("lobby");
    const [mines, setMines] = useState(null);
    const [boardData, setBoardData] = useState( null );

    const [send, setSend] = useState(null);
    const [socketRef, setSocketRef] = useState(null);

    const boardRef = useRef(null);
    const [gameState, setGameState] = useState(GameState.NOT_STARTED);

    const boardDataRef = useRef(null);
    useEffect(() => {
        boardDataRef.current = boardData;
    }, [boardData]);


    const handleGameServiceMessage = useCallback((msg) => {
        if (!msg || msg.type !== "ready") return;

        console.log("[Session] (forwarded):", msg);

        setSessionId(msg.session_id);
        setRound(msg.round ?? 0);
        setStartAt(msg.start_at ?? null);
        setStatus("game");
        console.log("->", msg.difficulty_level);
        setBoardData(msg.difficulty_level);

    }, []);

    useEffect( () => {
        console.log("boardData: ", boardData);
    }, [boardData])

    useEffect(() => {
        addMessageListener(handleGameServiceMessage);
        return () => removeMessageListener(handleGameServiceMessage);
    }, [addMessageListener, removeMessageListener, handleGameServiceMessage]);


    const handleSessionCommand = useCallback((msg) => {
        if (!msg?.type) return;

        console.log("[Session socket]: ", msg);

        switch (msg.type) {
            case "round_start":
                setRound(msg.round);
                setStartAt(msg.start_at);

                const difficulty = boardDataRef.current;


                boardRef.current?.dispatchCommand({
                    type: "RESET_BOARD",
                    rows: difficulty.rows,
                    cols: difficulty.columns,
                    mineCount: difficulty.mine_count
                });

                boardRef.current?.dispatchCommand({
                    type: "SET_CELL",
                    x: msg.start_field[0],
                    y: msg.start_field[1],
                    value: State.START_FIELD
                });

                break;

            case "round_end":
                setStatus("lobby");
                setEndAt(msg.end_at);
                break;

            case "session_over":
                setStatus("lobby");
                setSessionId(null);
                break;

            case "ready":
                setSessionId(msg.session_id);
                setRound(msg.round ?? 0);
                setStartAt(msg.start_at ?? null);
                setStatus("game");
                console.log("->", msg.difficulty_level);
                setBoardData(msg.difficulty_level);
                break
            default:
                return false;
        }

        return true;
    }, []);


    const ws = useMultiplayerWebSocket(
        (data) => {
            const handled = handleSessionCommand(data);
            if (handled) return [];
            return boardInterpreter(data);
        },
        boardRef,
        gameState
    );

    useEffect(() => {
        if (!sessionId) return;

        const socketUrl = `api/game/multi/${sessionId}`;
        ws.open(socketUrl);

        setSend(() => ws.send);
        setSocketRef(() => ws.socketRef);

    }, [sessionId]);


    const resetSession = () => {
        setSessionId(null);
        setRound(null);
        setStartAt(null);
        setEndAt(null);
        setStartField(null);
        setStatus("lobby");
    };

    return (
        <SessionContext.Provider value={{
            sessionId,
            round,
            startAt,
            endAt,
            startField,
            status,
            boardData,
            boardRef,
            gameState,
            send,
            resetSession,
            setGameState,
            setMines,
            mines
        }}>
            {children}
        </SessionContext.Provider>
    );
}

export const useSession = () => useContext(SessionContext);
