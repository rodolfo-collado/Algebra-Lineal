(() => {
    "use strict";

    let pendiente = false;
    const observados = new WeakSet();
    const observer = new ResizeObserver(programar);
    function programar() {
        if (pendiente) return;
        pendiente = true;
        requestAnimationFrame(actualizar);
    }
    function observar(nodo) {
        if (observados.has(nodo)) return;
        observados.add(nodo);
        observer.observe(nodo);
    }
    function actualizar() {
        pendiente = false;
        document.querySelectorAll(".matrix-pair").forEach(par => {
            const matrices = [...par.querySelectorAll(".matrix-content")];
            const flecha = par.querySelector(".matrix-pair-arrow");
            const gap = parseFloat(getComputedStyle(par).columnGap);
            const ancho = matrices.reduce((total, matriz) => total + matriz.getBoundingClientRect().width, 0);
            const simbolo = flecha.firstElementChild;
            const envuelto = ancho + parseFloat(getComputedStyle(simbolo).width) + 2 * gap > par.getBoundingClientRect().width;
            par.toggleAttribute("data-wrapped", envuelto);
            observar(par);
        });
        document.querySelectorAll(".matrix-scroll, .matrix-expression").forEach(scroll => {
            const overflow = scroll.clientWidth > 0 && scroll.scrollWidth > scroll.clientWidth + 1;
            scroll.toggleAttribute("data-overflow", overflow);
            // Las entradas ya tienen sus inputs en Tab; también se excluye x simbólico.
            if (overflow && !scroll.closest("form")) {
                scroll.tabIndex = 0;
                if (!scroll.hasAttribute("aria-label")) {
                    scroll.setAttribute("aria-label", "Expresión, desplazamiento horizontal");
                }
            } else scroll.removeAttribute("tabindex");
            observar(scroll);
            [...scroll.children].forEach(observar);
        });
    }
    new MutationObserver(programar).observe(document.body, { childList: true, subtree: true, characterData: true });
    document.addEventListener("toggle", programar, true);
    window.addEventListener("resize", programar);
    window.addEventListener("load", programar);
    document.querySelectorAll(".disclosure-procedure > summary").forEach(summary => {
        summary.addEventListener("click", () => {
            const detalle = summary.parentElement;
            if (detalle.open && detalle.getBoundingClientRect().top < summary.getBoundingClientRect().top - 1) {
                requestAnimationFrame(() => detalle.scrollIntoView({ block: "start", behavior: "instant" }));
            }
        });
    });
    programar();
})();
