import React, { useEffect, useRef, useState } from 'react';
import { GameState } from "../utility";
import { Lightbulb, RotateCcw } from "lucide-react";
import '../styles/controls.css';

export default function Controls({ onReset, mines, gameState, onHint }) {
    const [seconds, setSeconds] = useState(0);
    const intervalRef = useRef(null);

    useEffect(() => {
        if (gameState === GameState.NOT_STARTED) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
            setSeconds(0);
        }

        if (gameState === GameState.IN_PROGRESS) {
            if (!intervalRef.current) {
                intervalRef.current = setInterval(() => {
                    setSeconds(prev => Math.min(prev + 1, 999));
                }, 1000);
            }
        } else {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }

        return () => clearInterval(intervalRef.current);
    }, [gameState]);

    return (
        <div className="controls-container">
            <div className="counter-display">
                {seconds.toString().padStart(3, '0')}
            </div>

            <button className="control-btn reset" onClick={onReset} title="Restart">
                <RotateCcw size={22} />
            </button>

            <button className="control-btn hint-button" onClick={onHint} title="Hint">
                <Lightbulb size={22} />
            </button>

            <div className="counter-display">
                {mines.toString().padStart(2, '0')}
            </div>
        </div>
    );
}
