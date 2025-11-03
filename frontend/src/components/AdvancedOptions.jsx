import React, { useState } from "react";
import { Cpu, Brain, ChevronDown, ChevronUp } from "lucide-react";
import "../styles/advancedOptions.css";

const AdvancedOptions = ({ onSelect }) => {
    const [openSection, setOpenSection] = useState("classifier");
    const [classifier, setClassifier] = useState("lightgbm");
    const [heuristic, setHeuristic] = useState("no");

    const classifiers = [
        "lightgbm",
        "catboost",
        "gaussiannb",
        "mlp",
        "xgboost",
        "gradientboosting",
    ];

    const heuristics = ["no", "naive", "GA", "MCTS", "PSO", "SA"];

    const handleToggle = (section) => {
        setOpenSection((prev) => (prev === section ? null : section));
    };

    React.useEffect(() => {
        onSelect({ classifier, heuristic });
    }, [classifier, heuristic, onSelect]);

    return (
        <div className="advanced-options card p-4 mt-4 bg-bg-primary rounded-lg shadow-md w-full">
            <h3 className="text-text-primary text-lg font-semibold mb-4">
                Generator Settings
            </h3>

            {/* CLASSIFIER */}
            <div className="accordion-section mb-3">
                <button
                    onClick={() => handleToggle("classifier")}
                    className="accordion-header bg-bg-secondary flex justify-between items-center w-full text-left p-2 rounded-lg border border-border-primary hover:bg-cell-hover transition"
                >
                    <div className="flex flex-col text-text-primary font-semibold">
                        <div className="flex items-center gap-2">
                            <span>Classifier</span>
                        </div>
                        {/* Wybrany element */}
                        <span className="text-xs opacity-70 capitalize">
                            {classifier}
                        </span>
                    </div>
                    {openSection === "classifier" ? (
                        <ChevronUp className="text-text-primary transition-transform duration-300 rotate-180" size={18} />
                    ) : (
                        <ChevronDown className="text-text-primary transition-transform duration-300" size={18} />
                    )}
                </button>

                <div
                    className={`accordion-content ${
                        openSection === "classifier" ? "open" : ""
                    }`}
                >
                    <div className="accordion-inner mt-3 flex flex-col gap-2">
                        {classifiers.map((c) => (
                            <button
                                key={c}
                                onClick={() => setClassifier(c)}
                                className={`w-full text-left px-3 py-2 rounded-lg border-2 capitalize transition-all ${
                                    classifier === c
                                        ? "bg-accent-primary border-accent-primary text-bg-primary font-semibold"
                                        : "bg-bg-tertiary border-border-primary text-text-secondary hover:bg-cell-hover"
                                }`}
                            >
                                {c}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* HEURISTIC */}
            <div className="accordion-section mb-3">
                <button
                    onClick={() => handleToggle("heuristic")}
                    className="accordion-header flex justify-between items-center bg-bg-secondary w-full text-left p-2 rounded-lg border border-border-primary hover:bg-cell-hover transition"
                >
                    <div className="flex flex-col text-text-primary font-semibold">
                        <div className="flex items-center gap-2">
                            <span>Heuristic</span>
                        </div>
                        {/* Wybrany element */}
                        <span className="text-xs opacity-70">
                            {heuristic}
                        </span>
                    </div>
                    {openSection === "heuristic" ? (
                        <ChevronUp className="text-text-primary transition-transform duration-300 rotate-180" size={18} />
                    ) : (
                        <ChevronDown className="text-text-primary transition-transform duration-300" size={18} />
                    )}
                </button>

                <div
                    className={`accordion-content ${
                        openSection === "heuristic" ? "open" : ""
                    }`}
                >
                    <div className="accordion-inner mt-3 flex flex-col gap-2">
                        {heuristics.map((h) => (
                            <button
                                key={h}
                                onClick={() => setHeuristic(h)}
                                className={`w-full text-left px-3 py-2 rounded-lg border-2 uppercase transition-all ${
                                    heuristic === h
                                        ? "bg-accent-primary border-accent-primary text-bg-primary font-semibold"
                                        : "bg-bg-tertiary border-border-primary text-text-secondary hover:bg-cell-hover"
                                }`}
                            >
                                {h}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
            
        </div>
    );
};

export default AdvancedOptions;
