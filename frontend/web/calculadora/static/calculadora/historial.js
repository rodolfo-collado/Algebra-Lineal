(() => {
    "use strict";

    // Atrás y Adelante del header recorren el historial real del navegador (o de WebView2
    // en escritorio): no hay una pila propia. La Navigation API dice si hay adónde ir; sin
    // ella ambos quedan activos y el navegador ignora un salto imposible.
    const grupo = document.querySelector(".historial");
    const atras = document.getElementById("historial-atras");
    const adelante = document.getElementById("historial-adelante");
    const nav = window.navigation;

    function actualizar() {
        if (!nav || !("canGoBack" in nav)) return;
        atras.disabled = !nav.canGoBack;
        adelante.disabled = !nav.canGoForward;
        grupo.classList.toggle("con-adelante", nav.canGoForward);
    }

    if (grupo && atras && adelante) {
        atras.addEventListener("click", () => history.back());
        adelante.addEventListener("click", () => history.forward());
        nav?.addEventListener("currententrychange", actualizar);
        window.addEventListener("pageshow", actualizar);
        actualizar();
        grupo.hidden = false;
    }

    // «Retomar» en el inicio: la última herramienta abierta durante esta visita.
    const ULTIMA = "pygebra-ultima-herramienta";
    const actual = document.querySelector('.nav-tool .nav-link[aria-current="page"]');
    try {
        if (actual) sessionStorage.setItem(ULTIMA, JSON.stringify({ ruta: actual.getAttribute("href"), nombre: actual.textContent.trim() }));
        const retomar = document.getElementById("retomar");
        const ultima = JSON.parse(sessionStorage.getItem(ULTIMA));
        if (retomar && ultima?.ruta?.startsWith("/")) {
            retomar.href = ultima.ruta;
            retomar.textContent = `Retomar ${ultima.nombre}`;
            retomar.hidden = false;
        }
    } catch (_) {
        // Sin almacenamiento no hay nada que retomar.
    }
})();
