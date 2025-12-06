
export function handleReady(msg) {
    return {
        type: "SESSION_READY",
        session_id: msg.session_id,
        round: msg.round,
        start_at: msg.start_at
    };
}

export function handleRoundStart(msg) {
    return {
        type: "SESSION_ROUND_START",
        session_id: msg.session_id,
        round: msg.round,
        start_at: msg.start_at,
        end_at: msg.end_at,
        start_field: msg.start_field
    };
}

export function handleRoundEnd(msg) {
    return {
        type: "SESSION_ROUND_END",
        session_id: msg.session_id,
        round: msg.round
    };
}

export function handleSessionOver(msg) {
    return {
        type: "SESSION_OVER",
        session_id: msg.session_id
    };
}
