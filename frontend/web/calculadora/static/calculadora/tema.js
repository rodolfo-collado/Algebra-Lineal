(() => {
    "use strict";

    const STORAGE_KEY = "pygebra-tema";
    const root = document.documentElement;
    const button = document.getElementById("theme-toggle");
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    // El script inicial del <head> (tema_inicial.html) publica el acceso a las preferencias.
    const preferencias = window.preferencias;

    function storedTheme() {
        let value = preferencias.leer(STORAGE_KEY);
        if (value === null) {
            try {
                // La clave histórica sigue leyéndose; tema_inicial.html la migra a la nueva.
                value = localStorage.getItem("algebra-lineal-tema");
            } catch (_) {
                // Sin persistencia se conserva el tema visible.
            }
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
            preferencias.guardar(STORAGE_KEY, next);
            applyTheme(next);
        });
    }

    media.addEventListener("change", () => {
        if (storedTheme()) {
            return;
        }
        applyTheme(systemTheme());
    });

    // Una página restaurada del historial (bfcache) conserva el tema con que se dejó.
    window.addEventListener("pageshow", (event) => {
        if (event.persisted) applyTheme(storedTheme() || systemTheme());
    });
})();
