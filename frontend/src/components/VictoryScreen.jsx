import React from 'react';
import '../styles/victoryScreen.css';

export default function VictoryScreen({ onPlayAgain }) {
    return (
        <div className="victory-popup">
            <div className="victory-content">
                <h2>You Win!</h2>
                <h4>tu bedzie kilka rzeczy jeszcze</h4>
                <button className="menu-button" onClick={onPlayAgain}>
                    Play Again
                </button>
            </div>
        </div>
    );
}