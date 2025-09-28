
export function applySystemTheme() {
    const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
    });
}


applySystemTheme();
