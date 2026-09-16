(() => {
    "use strict";

    const STORAGE_KEY = "algebra-lineal-tema";
    const root = document.documentElement;
    const button = document.getElementById("theme-toggle");
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    function storedTheme() {
        const value = localStorage.getItem(STORAGE_KEY);
        return value === "light" || value === "dark" ? value : null;
    }

    function systemTheme() {
        return media.matches ? "dark" : "light";
    }

    function currentTheme() {
        return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
    }

    function applyTheme(theme) {
        root.setAttribute("data-theme", theme);
        root.style.colorScheme = theme;
        if (!button) {
            return;
        }

        const siguiente = theme === "dark" ? "claro" : "oscuro";
        button.setAttribute("aria-label", `Cambiar a tema ${siguiente}`);
        button.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
        const label = button.querySelector(".theme-toggle-text");
        if (label) {
            label.textContent = theme === "dark" ? "Oscuro" : "Claro";
        }
    }

    applyTheme(storedTheme() || currentTheme() || systemTheme());

    if (button) {
        button.addEventListener("click", () => {
            const next = currentTheme() === "dark" ? "light" : "dark";
            localStorage.setItem(STORAGE_KEY, next);
            applyTheme(next);
        });
    }

    media.addEventListener("change", () => {
        if (storedTheme()) {
            return;
        }
        applyTheme(systemTheme());
    });
})();
