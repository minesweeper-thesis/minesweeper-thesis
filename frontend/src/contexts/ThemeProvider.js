const THEME_KEY = "app-theme";

export function applyTheme(mode) {
    if (!["light", "dark", "system"].includes(mode)) {
        mode = "system";
    }

    localStorage.setItem(THEME_KEY, mode);

    if (mode === "system") {
        applySystemTheme();
    } else {
        document.documentElement.setAttribute("data-theme", mode);
    }
}

export function applySystemTheme() {
    const isDarkMode = window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.setAttribute("data-theme", isDarkMode ? "dark" : "light");

    window.matchMedia("(prefers-color-scheme: dark)").removeEventListener?.("change", handleSystemChange);
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", handleSystemChange);
}

function handleSystemChange(e) {
    const current = localStorage.getItem(THEME_KEY);
    if (current === "system") {
        document.documentElement.setAttribute("data-theme", e.matches ? "dark" : "light");
    }
}

export function initTheme() {
    const saved = localStorage.getItem(THEME_KEY) || "system";
    applyTheme(saved);
}
