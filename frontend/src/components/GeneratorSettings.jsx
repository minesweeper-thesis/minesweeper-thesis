import React, { useState, useEffect } from "react";

const generatorOptions = {
    GA: [
        { name: "Generations", type: "integer", min: 1, max: 100, default: 100 },
        { name: "Population size", type: "integer", min: 1, max: 100, default: 20 },
        { name: "Parents size", type: "integer", min: 1, max: 100, default: 1 },
        { name: "Random specimen rate", type: "float", min: 0.0, max: 1.0, default: 0.0 },
    ],
    PSO: [
        { name: "Iterations", type: "integer", min: 1, max: 100, default: 1 },
        { name: "Particle count", type: "integer", min: 1, max: 100, default: 40 },
        { name: "Random specimen rate 1", type: "float", min: 0.4, max: 0.9, default: 0.4 },
        { name: "Random specimen rate 2", type: "float", min: 1.0, max: 2.5, default: 2.5 },
        { name: "Random specimen rate 3", type: "float", min: 1.0, max: 2.5, default: 2.5 },
    ],
    SA: [
        { name: "Iterations", type: "integer", min: 1, max: 100, default: 82 },
        { name: "Fields Changed", type: "integer", min: 1, max: 50, default: 50 },
        { name: "T MAX", type: "float", min: 1.0, max: 100, default: 1.0 },
        { name: "T MIN", type: "float", min: 0.1, max: 1.0, default: 0.1 },
    ],
    naive: [
        { name: "Tries", type: "integer", min: 1, max: 1000, default: 503 },
    ],
};

const classifierOptions = ["lightgbm", "catboost", "xgboost", "gaussiannb", "mlp"];

const getDefaultGeneratorSettings = (type) => {
    if (!(type in generatorOptions)) return {};
    const defaults = {};
    generatorOptions[type].forEach(opt => {
        defaults[opt.name] = opt.default;
    });
    if (type === "GA" && defaults.parents_size >= defaults.population_size) {
        defaults.parents_size = Math.max(1, defaults.population_size - 1);
    }
    return defaults;
};

export default function GeneratorSettings({ boardData, setBoardData }) {
    const initialGeneratorType =
        boardData.generator?.settings?.heuristic in generatorOptions
            ? boardData.generator.settings.heuristic
            : "PSO";

    const initialClassifier = boardData.generator?.settings?.classifier || "xgboost";

    const initialSettings = boardData.generator?.settings?.heuristic_args && generatorOptions[initialGeneratorType]
        ? Object.fromEntries(
            generatorOptions[initialGeneratorType].map((opt, i) => [opt.name, boardData.generator.settings.heuristic_args[i]])
        )
        : getDefaultGeneratorSettings(initialGeneratorType);

    const [generatorType, setGeneratorType] = useState(initialGeneratorType);
    const [classifier, setClassifier] = useState(initialClassifier);
    const [generatorSettings, setGeneratorSettings] = useState(initialSettings);

    useEffect(() => {
        setBoardData(prev => ({
            ...prev,
            generator: {
                type: "ml",
                settings: {
                    heuristic: generatorType,
                    heuristic_args: Object.values(generatorSettings),
                    classifier: classifier
                }
            }
        }));
    }, [generatorType, classifier, generatorSettings]);

    useEffect(() => {
        const currentSettings = generatorSettings || {};
        let needDefault = false;

        if (!generatorOptions[generatorType]) return;

        generatorOptions[generatorType].forEach(opt => {
            if (currentSettings[opt.name] === undefined) {
                needDefault = true;
            }
        });

        if (needDefault) {
            setGeneratorSettings(getDefaultGeneratorSettings(generatorType));
        }
    }, []);


    const handleChange = (name, value) => {
        setGeneratorSettings(prev => {
            const updated = { ...prev, [name]: value };
            if (generatorType === "GA" && name === "population_size" && updated.parents_size >= updated.population_size) {
                updated.parents_size = Math.max(1, updated.population_size - 1);
            }
            return updated;
        });
    };

    const handleClassifierChange = (value) => setClassifier(value);

    const handleHeuristicChange = (value) => {
        setGeneratorType(value);
        setGeneratorSettings(getDefaultGeneratorSettings(value)); // tylko generatorSettings
    };

    return (
        <div className="mb-4 border-t border-border-primary pt-2">
            {/* Heuristic */}
            <label className="text-sm text-text-primary font-semibold">Heuristic</label>
            <select
                className="w-full bg-bg-tertiary text-text-secondary border border-border-primary rounded-lg p-2 mb-2"
                value={generatorType}
                onChange={(e) => handleHeuristicChange(e.target.value)}
            >
                {Object.keys(generatorOptions).map(g => (
                    <option key={g} value={g}>{g}</option>
                ))}
            </select>

            {/* Classifier */}
            <label className="text-sm text-text-primary font-semibold">Classifier</label>
            <select
                className="w-full text-text-secondary bg-bg-tertiary border border-border-primary rounded-lg p-2 mb-2"
                value={classifier}
                onChange={(e) => handleClassifierChange(e.target.value)}
            >
                {classifierOptions.map(c => (
                    <option key={c} value={c}>{c}</option>
                ))}
            </select>

            {/* Advanced Generator Options */}
            <div className="mt-2 space-y-2 border-t border-border-primary pt-2">
                <h3 className="text-sm text-text-primary font-semibold">Advanced generator options</h3>
                {generatorType in generatorOptions && generatorOptions[generatorType].map(opt => (
                    <div key={opt.name}>
                        <label className="text-sm text-text-primary font-semibold">{opt.name}</label>
                        <input
                            type={opt.type === "integer" ? "number" : "number"}
                            step={opt.type === "integer" ? 1 : 0.01}
                            min={opt.min}
                            max={opt.max}
                            value={generatorSettings[opt.name]}
                            onChange={(e) => handleChange(opt.name, opt.type === "integer" ? parseInt(e.target.value) : parseFloat(e.target.value))}
                            className="w-full bg-bg-tertiary text-text-secondary border border-border-primary rounded-lg p-2"
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}
