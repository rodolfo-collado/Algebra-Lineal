(() => {
    "use strict";

    const STORAGE_KEY = "pygebra-tema";
    const root = document.documentElement;
    const button = document.getElementById("theme-toggle");
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    function storedTheme() {
        let value = null;
        try {
            // La clave histórica sigue leyéndose; base.html la migra a la nueva.
            value = localStorage.getItem(STORAGE_KEY) ?? localStorage.getItem("algebra-lineal-tema");
        } catch (_) {
            // Sin persistencia se conserva el tema visible.
        }
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
        // El texto visible es siempre «Tema»: el icono y el aria-label indican el estado.
        button.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    }

    applyTheme(storedTheme() || currentTheme() || systemTheme());

    if (button) {
        button.addEventListener("click", () => {
            const next = currentTheme() === "dark" ? "light" : "dark";
            try {
                localStorage.setItem(STORAGE_KEY, next);
            } catch (_) {
                // Sin almacenamiento el cambio vale para esta visita.
            }
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
