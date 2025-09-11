import React from 'react';
import '../styles/victoryScreen.css';

export default function VictoryScreen({ onPlayAgain }) {
    return (
        <div className="victory-popup">
                <h2>You Win!</h2>
                <button className="menu-button" onClick={onPlayAgain}>
                    Play Again
                </button>
        </div>
    );
}