import React from 'react';
import '../styles/controls.css';

export default function Controls({ onReset, onNewGame }) {
    return (
        <div className="controls">
            <button className="control-button" onClick={onReset}>Reset</button>
            <button className="control-button" onClick={onNewGame}>Nowa plansza</button>
        </div>
    );
}
