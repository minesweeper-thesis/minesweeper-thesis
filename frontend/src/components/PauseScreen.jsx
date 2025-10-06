import React from 'react';
import '../styles/pauseScreen.css';

export default function PauseScreen({ resumeGame }) {
    return (
        <div className="pause-popup">
            <div className="pause-content">
                <h2>Game Paused</h2>
                <button className="menu-button" onClick={resumeGame}>
                    Resume
                </button>
            </div>
        </div>
    );
}
