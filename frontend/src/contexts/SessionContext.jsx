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
    const { addMessageListener, removeMessageListener, lobby } = useGame();

    const [sessionId, setSessionId] = useState(null);
    const [round, setRound] = useState(null);
    const [startAt, setStartAt] = useState(null);
    const [leaveLobbyAt, setLeaveLobbyAt] = useState(null);
    const [endAt, setEndAt] = useState(null);
    const [startField, setStartField] = useState(null);
    const [status, setStatus] = useState("lobby");
    const [mines, setMines] = useState(null);
    const [boardData, setBoardData] = useState( null );

    const [send, setSend] = useState(null);
    const [socketRef, setSocketRef] = useState(null);

    const boardRef = useRef(null);
    const [gameState, setGameState] = useState(GameState.NOT_STARTED);

    const [scoreboard, setScoreboard] = useState([]);

    const boardDataRef = useRef(null);
    useEffect(() => {
        boardDataRef.current = boardData;
    }, [boardData]);


    useEffect(() => {
        if (!lobby?.users) return;

        const initialScoreboard = lobby.users.map(u => ({
            id: u.id,
            nickname: u.nickname,
            avatar_url: u.avatar_url,
            score: 0
        }));

        setScoreboard(initialScoreboard);
    }, [lobby?.users]);

    const handleGameServiceMessage = useCallback((msg) => {
        if (!msg ) return;
        console.log("[Session] (forwarded):", msg);

        switch (msg.type) {
            case "reset_session":
                setSessionId(null);
                break;

            case "round_ready":
                setSessionId(msg.session_id);
                setRound(msg.round ?? 1);
                setBoardData(msg.difficulty_level);
                break;
            case "round_countdown":
                setStartAt(msg.start_at ?? null);
                // setLeaveLobbyAt(msg.countdown_to ?? null)
                setStatus("game");

                break
            default:
                break;
        }

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
                setEndAt(msg.end_at);
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
                if (msg.scoreboard) {
                    updateScoreFromMessage(msg.scoreboard);
                }

                // opóźnienie 3 sekundy przed powrotem do lobby
                setTimeout(() => {
                    setStatus("lobby");
                }, 3000);
                break;

            case "session_over":
                setStatus("lobby");
                setSessionId(null);
                break;

            case "score_update":
                updateScore(msg);
                break;

            case "round_ready":
                setSessionId(msg.session_id);
                setRound(msg.round ?? 1);
                break;

            case "round_countdown":
                setStartAt(msg.start_at ?? null);
                setStatus("game");
                break;
            default:
                return false;
        }

        return true;
    }, []);

    const updateScore = (msg) => {
        if (!msg?.user_id) return;

        setScoreboard(prev => prev.map(player =>
            player.id === msg.user_id ? { ...player, score: Math.floor(msg.score) } : player
        ));
    };

    const updateScoreFromMessage = (msgScoreboard) => {
        setScoreboard(prev =>
            prev.map(player => {
                const updated = msgScoreboard.find(p => p.user_id === player.id);
                if (!updated) return player;
                return {
                    ...player,
                    score: Math.floor(updated.score) ?? Math.floor(player.score)
                };
            })
        );
    };


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
            mines,
            scoreboard
        }}>
            {children}
        </SessionContext.Provider>
    );
}

export const useSession = () => useContext(SessionContext);
