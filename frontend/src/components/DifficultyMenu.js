import React, { useState } from 'react';
import '../styles/difficultyMenu.css';

export default function DifficultyMenu({ onSelect, onBack }) {
    const [selected, setSelected] = useState(null);
    const [customRows, setCustomRows] = useState(9);
    const [customCols, setCustomCols] = useState(9);
    const [customMines, setCustomMines] = useState(10);

    const handleAccept = () => {
        if (selected === 'easy') onSelect(9, 9, 10);
        else if (selected === 'medium') onSelect(16, 16, 40);
        else if (selected === 'hard') onSelect(16, 30, 99);
        else if (selected === 'custom') onSelect(customRows, customCols, customMines);
    };

    return (
        <div className="menu">
            <h2>Select Difficulty</h2>
            <div className="difficulty-buttons">
                <button
                    className={`menu-button ${selected === 'easy' ? 'selected' : ''}`}
                    onClick={() => setSelected('easy')}
                >
                    Easy
                </button>
                <button
                    className={`menu-button ${selected === 'medium' ? 'selected' : ''}`}
                    onClick={() => setSelected('medium')}
                >
                    Medium
                </button>
                <button
                    className={`menu-button ${selected === 'hard' ? 'selected' : ''}`}
                    onClick={() => setSelected('hard')}
                >
                    Hard
                </button>
                <button
                    className={`menu-button ${selected === 'custom' ? 'selected' : ''}`}
                    onClick={() => setSelected('custom')}
                >
                    Custom
                </button>
            </div>

            {selected === 'custom' && (
                <div className="custom-params">
                    <label>
                        Rows:
                        <input
                            type="number"
                            value={customRows}
                            onChange={(e) => setCustomRows(parseInt(e.target.value))}
                            min={5}
                            max={50}
                        />
                    </label>
                    <label>
                        Columns:
                        <input
                            type="number"
                            value={customCols}
                            onChange={(e) => setCustomCols(parseInt(e.target.value))}
                            min={5}
                            max={50}
                        />
                    </label>
                    <label>
                        Mines:
                        <input
                            type="number"
                            value={customMines}
                            onChange={(e) => setCustomMines(parseInt(e.target.value))}
                            min={1}
                            max={customRows * customCols - 1}
                        />
                    </label>
                </div>
            )}

            <div className="menu-actions">
                <button className="back-button" onClick={onBack}>Back</button>
                <button className="accept-button" onClick={handleAccept} disabled={!selected}>Accept</button>
            </div>
        </div>
    );
}
