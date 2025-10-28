import React, { useEffect, useRef } from 'react';
import '../styles/square.css';
import { State } from "../utility";

export default function Square({ value, onClick }) {
    const buttonRef = useRef(null);

    const isHint= value === State.HINT;
    const isRed= value === State.LOSING_MINE;
    const isRevealed = value >= State.LOSING_MINE;
    const isFlagged = value === State.FLAG;
    const isMine = value === State.MINE || value === State.LOSING_MINE;
    const isStart = value === State.START_FIELD;

    const className = `square
     ${isRevealed ? "clicked" : "not-clicked"}
     ${value >= 1 && value <= 8 ? `number-${value}` : ""}
     ${isStart ? "start" : ""}
     ${isHint ? "hint" : ""}
     ${isRed ? "red-mine" : ""}
     }`;

    let content = " ";
    if (isFlagged) content = <img src="/flag.svg" alt="I"/>;
    else if (isMine) content = <img src="/mine.svg" alt="X"/>;
    else if (isStart) content = "X";
    else if (value > 0) content = value;


    useEffect(() => {
        const buttonElement = buttonRef.current;
        if (!buttonElement) return;

        const scaleContent = () => {
            const width = buttonElement.offsetWidth;
            const contentRatio = 0.69;
            const newFontSize = width * contentRatio;

            buttonElement.style.fontSize = `${newFontSize}px`;
        };

        const observer = new ResizeObserver(e => {
            scaleContent();
        });

        observer.observe(buttonElement);
        scaleContent();

        return () => {
            observer.unobserve(buttonElement);
        };
    }, []);

    return (
        <button
            ref={buttonRef}
            className={className}
            onMouseUp={onClick}
            onContextMenu={(e) => e.preventDefault()}
        >
            <span>
                {content}
            </span>
        </button>
    );
}