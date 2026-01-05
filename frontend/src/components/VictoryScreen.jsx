import React from 'react';
import '../styles/victoryScreen.css';

export default function VictoryScreen({ onPlayAgain, time }) {
    return (
        <div className="victory-popup">
            <div className="victory-content">
                <h2>You Win!</h2>
                <h4>Time: {time}</h4>
                <button className="menu-button" onClick={_ => onPlayAgain()}>
                    Play Again
                </button>
            </div>
        </div>
    );
}