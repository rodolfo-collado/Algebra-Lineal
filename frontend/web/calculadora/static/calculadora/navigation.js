(() => {
    "use strict";

    const STORAGE_MENU = "algebra-lineal-menu";
    const STORAGE_SECCIONES = "algebra-lineal-menu-secciones";
    const root = document.documentElement;
    const button = document.getElementById("navigation-toggle");
    const sidebar = document.getElementById("navegacion-principal");
    const backdrop = document.getElementById("sidebar-backdrop");
    const closeButton = document.getElementById("sidebar-close");
    const main = document.getElementById("contenido");
    if (!button || !sidebar) return;

    const compact = window.matchMedia("(max-width: 880px)");
    let drawerOpen = false;

    function leer(clave) {
        try {
            return localStorage.getItem(clave);
        } catch (error) {
            return null;
        }
    }

    function guardar(clave, valor) {
        try {
            localStorage.setItem(clave, valor);
        } catch (error) {
            // Sin almacenamiento disponible el menú sigue funcionando; solo no recuerda.
        }
    }

    function desktopOculto() {
        return root.getAttribute("data-menu") === "oculto";
    }

    // En escritorio la sidebar es una columna que se puede ocultar; en pantallas
    // estrechas es un cajón sobre el contenido. Un solo botón controla ambos.
    function aplicar() {
        button.hidden = false;
        if (compact.matches) {
            root.toggleAttribute("data-drawer", drawerOpen);
            sidebar.hidden = !drawerOpen;
            if (backdrop) backdrop.hidden = !drawerOpen;
            if (closeButton) closeButton.hidden = false;
            if (main) main.inert = drawerOpen;
            button.setAttribute("aria-expanded", String(drawerOpen));
            return;
        }

        drawerOpen = false;
        root.removeAttribute("data-drawer");
        if (backdrop) backdrop.hidden = true;
        if (closeButton) closeButton.hidden = true;
        if (main) main.inert = false;
        sidebar.hidden = desktopOculto();
        button.setAttribute("aria-expanded", String(!desktopOculto()));
    }

    function abrirCajon() {
        drawerOpen = true;
        aplicar();
        const primero = sidebar.querySelector("input, a, button, summary");
        if (primero) primero.focus();
    }

    function cerrarCajon() {
        if (!drawerOpen) return;
        drawerOpen = false;
        aplicar();
        button.focus();
    }

    button.addEventListener("click", () => {
        if (compact.matches) {
            if (drawerOpen) cerrarCajon();
            else abrirCajon();
            return;
        }
        const ocultar = !desktopOculto();
        if (ocultar) root.setAttribute("data-menu", "oculto");
        else root.removeAttribute("data-menu");
        guardar(STORAGE_MENU, ocultar ? "oculto" : "visible");
        aplicar();
    });

    if (closeButton) closeButton.addEventListener("click", cerrarCajon);
    if (backdrop) backdrop.addEventListener("click", cerrarCajon);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && compact.matches && drawerOpen) cerrarCajon();
    });
    compact.addEventListener("change", aplicar);

    // Las categorías abiertas por el usuario se recuerdan; la categoría activa
    // siempre llega abierta desde el servidor.
    const categorias = Array.from(sidebar.querySelectorAll("details[data-categoria]"));
    let abiertas = new Set();
    try {
        abiertas = new Set(JSON.parse(leer(STORAGE_SECCIONES) || "[]"));
    } catch (error) {
        abiertas = new Set();
    }
    categorias.forEach((categoria) => {
        if (abiertas.has(categoria.dataset.categoria)) categoria.open = true;
        categoria.addEventListener("toggle", () => {
            // El filtro del buscador abre categorías por su cuenta; eso no se guarda.
            if (sidebar.querySelector("[data-filtrando]")) return;
            if (categoria.open) abiertas.add(categoria.dataset.categoria);
            else abiertas.delete(categoria.dataset.categoria);
            guardar(STORAGE_SECCIONES, JSON.stringify(Array.from(abiertas)));
        });
    });

    aplicar();
})();
