import React from 'react';
import '../styles/square.css';

function isClicked(value) {
    return value === " " || value === -2 ? " not-clicked" : " clicked";
}

export default function Square({ value, onClick }) {
    return (
        <button
            className={`square number-${value}${isClicked(value)}`}
            onMouseUp={onClick}
            onContextMenu={(e) => e.preventDefault()}
        >
            {value === -1 ? (
                <img src="/mine.svg" alt=" " className="mine-icon" />
            ) : value === -2 ? (
                <img src="/flag.svg" alt=" " className="flag-icon" />
            ) : value === 0 ? " " : value}
        </button>
    );
}
