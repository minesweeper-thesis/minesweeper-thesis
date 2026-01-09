import React, { useState } from "react";
import GeneratorSettings from "./GeneratorSettings";
import ModeSwitch from "./ModeSwitch";
import { Settings, Zap, Target, Flame } from 'lucide-react';

const DifficultyMenu = ({ setBoardData, onStart }) => {
    const [selected, setSelected] = useState('easy');
    const [customRows, setCustomRows] = useState(9);
    const [customCols, setCustomCols] = useState(9);
    const [customMines, setCustomMines] = useState(10);
    const [selectedMode, setSelectedMode] = useState(false);
    const [showGenerator, setShowGenerator] = useState(false);

    const [localData, setLocalData] = useState({
        difficulty: selected,
        mode: selectedMode ? "hardcore" : "normal",
        generator: {
            type: "random",
            settings: {
                heuristic: "random",
                heuristic_args: [],
                classifier: "lightgbm"
            }
        }
    });

    const difficultyInfo = {
        easy: { icon: Zap, label: 'Easy', description: '10×10 grid, 15 mines', color: 'var(--success)' },
        medium: { icon: Target, label: 'Medium', description: '16×16 grid, 40 mines', color: 'var(--warning)' },
        hard: { icon: Flame, label: 'Hard', description: '16×30 grid, 99 mines', color: 'var(--error)' },
        custom: { icon: Settings, label: 'Custom', description: 'Your settings', color: 'var(--accent-primary)' },
    };

    const handleAccept = () => {
        let rows, cols, mines;
        if (selected === 'easy') { rows=10; cols=10; mines=15; }
        else if (selected === 'medium') { rows=16; cols=16; mines=40; }
        else if (selected === 'hard') { rows=16; cols=30; mines=99; }
        else { rows=customRows; cols=customCols; mines=customMines; }

        const updatedData = {
            ...localData,
            difficulty_level: {
                "rows": rows,
                "columns": cols,
                "mine_count": mines
            },
            mode: selectedMode ? "hardcore" : "normal"
        };

        setBoardData(updatedData);
        onStart();
    };

    return (
        <div className="difficulty-selector card p-4 bg-bg-primary rounded-lg shadow-md">
            <h3 className="text-text-primary text-lg font-semibold mb-5">Difficulty</h3>

            <div className="difficulty-options text-text-secondary flex flex-col gap-2 mb-5 lg:flex-row lg:flex-wrap">
                {Object.entries(difficultyInfo).map(([key, info]) => {
                    const Icon = info.icon;
                    const isSelected = selected === key;
                    return (
                        <button
                            key={key}
                            className={`flex items-center gap-3 p-3 border-2 rounded-lg w-full text-left transition-all ${
                                isSelected
                                    ? 'bg-accent-primary border-accent-primary text-bg-primary'
                                    : 'bg-bg-tertiary border-border-primary hover:bg-cell-hover hover:translate-x-1'
                            }`}
                            onClick={() => setSelected(key)}
                        >
                            <Icon size={20} style={{ color: info.color }} />
                            <div className="flex flex-col gap-[2px]">
                                <span className="font-semibold text-sm">{info.label}</span>
                                <span className="text-xs opacity-80">{info.description}</span>
                            </div>
                        </button>
                    );
                })}
            </div>

            {selected === 'custom' && (
                <div className="custom-settings border-t border-border-primary pt-5 mt-5">
                    <h4 className="text-text-primary text-base font-semibold mb-4">Custom Settings</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        <div className="flex flex-col gap-1">
                            <label className="text-xs font-semibold text-text-primary">Rows</label>
                            <input
                                type="number"
                                min="5"
                                max="30"
                                value={customRows}
                                onChange={(e) =>
                                    setCustomRows(Math.max(1, parseInt(e.target.value) || 1))}
                                className="p-2 text-sm border rounded text-text-secondary bg-bg-tertiary"
                            />
                        </div>

                        <div className="flex flex-col gap-1">
                            <label className="text-xs font-semibold text-text-primary">Columns</label>
                            <input
                                type="number"
                                min="5"
                                max="50"
                                value={customCols}
                                onChange={(e) =>
                                    setCustomCols(Math.max(1, parseInt(e.target.value) || 1))}
                                className="p-2 text-sm border rounded text-text-secondary bg-bg-tertiary"
                            />
                        </div>

                        <div className="flex flex-col gap-1 md:col-span-2">
                            <label className="text-xs font-semibold text-text-primary">Mines</label>
                            <input
                                type="number"
                                min="1"
                                max={Math.floor(customRows * customCols * 0.8)} value={customMines}
                                onChange={(e) =>
                                    setCustomMines(Math.max(1, parseInt(e.target.value) || 1))}
                                className="p-2 text-sm border rounded text-text-secondary bg-bg-tertiary"
                            />
                        </div>
                    </div>
                </div>
            )}

            <ModeSwitch
                checked={selectedMode}
                onChange={() => {
                    setSelectedMode(prev => !prev);
                }}
            />

            {/* Generator settings */}
            <button
                className="mb-2 text-sm text-accent-primary underline"
                onClick={() => setShowGenerator(prev => !prev)}
            >
                Generator options
            </button>
            <br/>
            {showGenerator && (
                <GeneratorSettings boardData={localData} setBoardData={setLocalData} />
            )}

            <button
                onClick={handleAccept}
                className="px-4 py-2 bg-accent-primary text-bg-primary rounded-lg font-semibold hover:opacity-90 transition mt-4"
            >
                Start
            </button>
        </div>
    );
};

export default DifficultyMenu;
