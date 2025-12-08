import React, { useState, useEffect } from "react";

export default function LobbySettingsPopup({ onClose, config, onSave }) {
    const [rounds, setRounds] = useState(config.rounds || 1);
    const [maxTime, setMaxTime] = useState(config.max_round_time || 60);
    const [difficulty, setDifficulty] = useState("custom");
    const [difficultyValue, setDifficultyValue] = useState(config.difficulty_level);

    const [gameMode, setGameMode] = useState(config.game_mode || "normal");
    const [generatorType, setGeneratorType] = useState(config.generator?.settings?.heuristic || "random");
    const [classifier, setClassifier] = useState(config.generator?.settings?.classifier || "lightgbm");
    const [generatorSettings, setGeneratorSettings] = useState(config.generator?.settings || {});

    const [showAdvanced, setShowAdvanced] = useState(false);

    const presets = {
        easy: { rows: 10, columns: 10, mine_count: 15 },
        medium: { rows: 16, columns: 16, mine_count: 40 },
        hard: { rows: 16, columns: 30, mine_count: 99 },
    };

    const isPresetActive = (presetKey) => {
        const preset = presets[presetKey];
        return (
            difficultyValue?.rows === preset.rows &&
            difficultyValue?.columns === preset.columns &&
            difficultyValue?.mine_count === preset.mine_count
        );
    };


    const generatorOptions = {
        GA: [
            { name: "generations", type: "integer", min: 1, max: 100 },
            { name: "population_size", type: "integer", min: 1, max: 100 },
            { name: "parents_size", type: "integer", min: 1, max: 100 },
            { name: "random_specimen_rate", type: "float", min: 0.0, max: 1.0 },
        ],
        PSO: [
            { name: "iterations", type: "integer", min: 1, max: 100 },
            { name: "particle_count", type: "integer", min: 1, max: 100 },
            { name: "random_specimen_rate1", type: "float", min: 0.4, max: 0.9 },
            { name: "random_specimen_rate2", type: "float", min: 1.0, max: 2.5 },
            { name: "random_specimen_rate3", type: "float", min: 1.0, max: 2.5 },
        ],
        SA: [
            { name: "iterations", type: "integer", min: 1, max: 100 },
            { name: "fields_changed", type: "integer", min: 1, max: 50 },
            { name: "T_MAX", type: "float", min: 1.0, max: 100 },
            { name: "T_MIN", type: "float", min: 0.1, max: 1.0 },
        ],
        naive: [
            { name: "tries", type: "integer", min: 1, max: 1000 },
        ],
    };

    const classifierOptions = ["lightgbm", "catboost", "xgboost", "gaussiannb", "mlp"];

    const applyPreset = (key) => {
        setDifficulty(key);
        setDifficultyValue(presets[key]);
    };

    const setDefaultGeneratorSettings = (type) => {
        let defaults = {};
        if (type in generatorOptions) {
            generatorOptions[type].forEach(opt => {
                // wpiszemy wartość w środku zakresu
                if (opt.type === "integer") {
                    defaults[opt.name] = Math.floor((opt.min + opt.max) / 2);
                } else {
                    defaults[opt.name] = (opt.min + opt.max) / 2;
                }
            });
            // dodatkowy warunek GA
            if (type === "GA") {
                if (defaults.parents_size >= defaults.population_size) {
                    defaults.parents_size = Math.max(1, defaults.population_size - 1);
                }
            }
        }
        setGeneratorSettings(defaults);
    };

    // resetujemy ustawienia gdy zmieni się generator
    useEffect(() => {
        setDefaultGeneratorSettings(generatorType);
    }, [generatorType]);

    const handleGeneratorSettingChange = (name, value) => {
        setGeneratorSettings(prev => {
            const updated = { ...prev, [name]: value };
            // dodatkowy warunek dla GA
            if (generatorType === "GA" && name === "population_size") {
                if (updated.parents_size >= updated.population_size) {
                    updated.parents_size = Math.max(1, updated.population_size - 1);
                }
            }
            return updated;
        });
    };

    const handleSave = async () => {
        const heuristicArgs = generatorOptions[generatorType].map(opt => generatorSettings[opt.name]);

        const body = {
            rounds,
            max_round_time: maxTime,
            difficulty_level: difficultyValue,
            game_mode: gameMode,
            generator: {
                type: "ml",
                settings: {
                    heuristic: generatorType,
                    heuristic_args: heuristicArgs,
                    classifier: classifier,
                }

            },
        };

        await onSave(body);
        onClose();
    };


    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
            <div className="bg-bg-secondary border border-border-primary rounded-xl p-6 w-full max-w-lg overflow-y-auto max-h-[90vh]">
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
                                isPresetActive(key)
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

                {/* Classifier */}
                <label className="text-sm font-semibold">Classifier</label>
                <select
                    className="w-full bg-bg-tertiary border border-border-primary rounded-lg p-2 mb-4"
                    value={classifier}
                    onChange={(e) => setClassifier(e.target.value)}
                >
                    {classifierOptions.map(c => (
                        <option key={c} value={c}>{c}</option>
                    ))}
                </select>

                {/* Generator */}
                <label className="text-sm font-semibold">Heuristic</label>
                <select
                    className="w-full bg-bg-tertiary border border-border-primary rounded-lg p-2 mb-2"
                    value={generatorType}
                    onChange={(e) => setGeneratorType(e.target.value)}
                >
                    {Object.keys(generatorOptions).map(g => (
                        <option key={g} value={g}>{g}</option>
                    ))}
                </select>

                <button
                    className="mb-2 text-sm text-accent-primary underline"
                    onClick={() => setShowAdvanced(prev => !prev)}
                >
                    Advanced heuristic options
                </button>

                {/* Generator dynamic settings – rozwijane */}
                {showAdvanced && generatorType in generatorOptions && (
                    <div className="mb-4 space-y-2 border-t border-border-primary pt-2">
                        {generatorOptions[generatorType].map(setting => (
                            <div key={setting.name}>
                                <label className="text-sm font-semibold">{setting.name}</label>
                                <input
                                    type={setting.type === "integer" ? "number" : "number"}
                                    step={setting.type === "integer" ? 1 : 0.01}
                                    min={setting.min}
                                    max={setting.max}
                                    value={generatorSettings[setting.name] ?? setting.min}
                                    onChange={(e) => handleGeneratorSettingChange(setting.name, setting.type === "integer" ? parseInt(e.target.value) : parseFloat(e.target.value))}
                                    className="w-full bg-bg-tertiary border border-border-primary rounded-lg p-2"
                                />
                            </div>
                        ))}
                    </div>
                )}

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