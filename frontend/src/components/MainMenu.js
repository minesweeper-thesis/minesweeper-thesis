import React from 'react';

export default function MainMenu({ onPlay }) {
    return (
        <div className="menu">
            <h1>Main Menu</h1>
            <button className="menu-button" onClick={onPlay}>Play</button>
            <button className="menu-button" disabled>Option 2</button>
            <button className="menu-button" disabled>Option 3</button>
        </div>
    );
}
