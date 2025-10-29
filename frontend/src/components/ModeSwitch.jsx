import React from "react";
import "../styles/modeSwitch.css";

export default function ModeSwitch({ checked, onChange }) {
    return (
        <label className="mode-switch">
            <span className="switch-label">Hardcore</span>
            <div className="info-icon" data-tooltip="Lose not only when hitting a mine, but also if you click a tile without logical certainty.">
                ?
            </div>
            <div className="switch">
                <input
                    type="checkbox"
                    checked={checked}
                    onChange={onChange}
                />
                <span className="slider"></span>
            </div>
        </label>
    );
}
