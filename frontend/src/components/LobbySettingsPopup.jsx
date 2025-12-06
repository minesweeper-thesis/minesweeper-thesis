import React, { useState } from "react";

export default function LobbySettingsPopup({ onClose, config, onSave }) {
    const [rounds, setRounds] = useState(config.rounds || 1);
    const [maxTime, setMaxTime] = useState(config.max_round_time || 60);
    const [difficulty, setDifficulty] = useState("custom");
    const [difficultyValue, setDifficultyValue] = useState(config.difficulty_level);

    const [gameMode, setGameMode] = useState(config.game_mode || "normal");
    const [generatorType, setGeneratorType] = useState(config.generator_type || "random");

    const presets = {
        easy:   { rows: 10, columns: 10, mine_count: 15 },
        medium: { rows: 16, columns: 16, mine_count: 40 },
        hard:   { rows: 16, columns: 30, mine_count: 99 },
    };

    const applyPreset = (key) => {
        setDifficulty(key);
        setDifficultyValue(presets[key]);
    };

    const handleSave = async () => {
        const body = {
            rounds,
            max_round_time: maxTime,
            difficulty_level: difficultyValue,
            game_mode: gameMode,
            generator: {
                type: generatorType,
                settings: config.generator_settings // NIC NIE ZMIENIAMY
            }
        };

        await onSave(body);
        onClose();
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
            <div className="bg-bg-secondary border border-border-primary rounded-xl p-6 w-full max-w-lg">
                <h2 className="text-xl font-semibold mb-4">Edit Lobby Settings</h2>

                {/* Rounds */}
                <label className="text-sm font-semibold">Rounds</label>
                <input
                    type="number"
                    className="w-full bg-bg-tertiary border border-border-primary rounded-lg p-2 mb-4"
                    value={rounds}
                    min={1}
                    onChange={(e) => setRounds(Number(e.target.value))}
                />

                {/* Max time */}
                <label className="text-sm font-semibold">Max Round Time (sec)</label>
                <input
                    type="number"
                    className="w-full bg-bg-tertiary border border-border-primary rounded-lg p-2 mb-4"
                    value={maxTime}
                    min={10}
                    onChange={(e) => setMaxTime(Number(e.target.value))}
                />

                {/* Difficulty presets */}
                <label className="text-sm font-semibold">Difficulty</label>
                <div className="flex gap-2 mb-4">
                    {Object.keys(presets).map((key) => (
                        <button
                            key={key}
                            onClick={() => applyPreset(key)}
                            className={`px-3 py-2 rounded-lg border ${
                                difficulty === key
                                    ? "bg-accent-primary text-white"
                                    : "bg-bg-tertiary text-text-primary"
                            }`}
                        >
                            {key.charAt(0).toUpperCase() + key.slice(1)}
                        </button>
                    ))}
                </div>

                {/* Game Mode */}
                <label className="text-sm font-semibold">Game Mode</label>
                <select
                    className="w-full bg-bg-tertiary border border-border-primary rounded-lg p-2 mb-4"
                    value={gameMode}
                    onChange={(e) => setGameMode(e.target.value)}
                >
                    <option value="normal">Normal</option>
                    <option value="hardcore">Hardcore</option>
                </select>

                {/* Generator */}
                <label className="text-sm font-semibold">Generator</label>
                <select
                    className="w-full bg-bg-tertiary border border-border-primary rounded-lg p-2 mb-6"
                    value={generatorType}
                    onChange={(e) => setGeneratorType(e.target.value)}
                >
                    <option value="random">Random</option>
                    <option value="ml">ML</option>
                </select>

                {/* Buttons */}
                <div className="flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg bg-bg-tertiary border border-border-primary"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-4 py-2 rounded-lg bg-accent-primary text-white"
                    >
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
}
