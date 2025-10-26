import React from 'react';
import '../styles/square.css';
import {State} from "../utility";

export default function Square({ value, onClick }) {

    const isRevealed = value >= State.MINE;
    const isFlagged = value === State.FLAG;
    const isMine = value === State.MINE;
    const isStart = value === State.START_FIELD;

    const className = `square ${isRevealed ? "clicked" : "not-clicked"} ${
        value >= 1 && value <= 8 ? `number-${value}` : ""
    } ${isStart ? "start" : ""}`;


    let content = " ";
    if (isFlagged) content = <img src="/flag.svg" alt="I" className="flag-icon" />;
    else if (isMine) content = <img src="/mine.svg" alt="X" className="mine-icon" />;
    else if (isStart) content = "X";
    else if (value > 0) content = value;

    return (
        <button
            className={className}
            onMouseUp={onClick}
            onContextMenu={(e) => e.preventDefault()}
        >
            {content}
        </button>
    );
}
