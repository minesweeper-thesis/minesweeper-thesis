import React, {useEffect, useRef, useState} from 'react';
import '../styles/controls.css';
import {GameState} from "../utility";

export default function Controls({ onReset, onNewGame,onMenu, mines, onPause , gameState }) {

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
                    setSeconds(prev => prev + 1);
                }, 1000);
            }
        } else {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }

        return () => {
            clearInterval(intervalRef.current);
        };
    }, [gameState]);

    return (
        <div className="controls">
            <button className="control-button" onClick={onReset}>Restart level</button>
            <button disabled={gameState !== GameState.IN_PROGRESS} className="control-button" onClick={onPause}>Pause</button>
            <p className="mine-counter">{seconds}</p>
            <p className="mine-counter">{mines}</p>
            <button className="control-button" onClick={onNewGame}>New game</button>
        </div>
    );
}
