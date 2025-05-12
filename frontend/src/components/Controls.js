import React from 'react';
import '../styles/controls.css';

export default function Controls({ onReset, onNewGame,onMenu, mines }) {
    return (
        <div className="controls">
            <button className="control-button" onClick={onMenu}>Menu</button>
            <button className="control-button" onClick={onReset}>Reset</button>
            <p className="mine-counter">{mines}</p>
            <button className="control-button" onClick={onNewGame}>Nowa plansza</button>
        </div>
    );
}
