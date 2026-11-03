(() => {
    "use strict";

    const root = document.documentElement;
    const sonar = (nombre, ...args) => window.Sonido?.tocar(nombre, ...args);
    const AREA = "pygebra-area-elegida";
    const leer = (clave) => { try { return JSON.parse(sessionStorage.getItem(clave)) || {}; } catch (_) { return {}; } };
    const guardar = (clave, valor) => { try { sessionStorage.setItem(clave, JSON.stringify(valor)); } catch (_) {} };

    /* —— Inicio: canales de áreas —— */

    const canales = document.querySelector(".canales");
    if (canales) {
        const lista = [...canales.querySelectorAll(".canal")];
        let sonado = null;
        const sonarCanal = (event) => {
            const canal = event.target.closest?.(".canal:not(.es-pronto)");
            if (canal && canal !== sonado) sonar("seleccion", lista.indexOf(canal));
            sonado = canal;
        };
        canales.addEventListener("pointerover", sonarCanal);
        canales.addEventListener("focusin", sonarCanal);
        // Solo una escena puede viajar entre páginas: la del canal que se abre.
        canales.addEventListener("click", (event) => {
            const canal = event.target.closest(".canal:not(.es-pronto)");
            if (!canal) return;
            canales.querySelectorAll(".canal-escena").forEach((e) => { e.style.viewTransitionName = ""; });
            canal.querySelector(".canal-escena").style.viewTransitionName = "diorama";
        });
        // Al volver de un área, su escena regresa a su canal.
        const previa = leer(AREA).ultima;
        const canal = root.dataset.dir === "atras" && previa ? document.getElementById(previa) : null;
        if (canal?.matches(".canal")) canal.querySelector(".canal-escena").style.viewTransitionName = "diorama";

        // La cámara de la habitación se acerca cuando el visitante deja atrás la bienvenida.
        const bienvenida = document.querySelector(".home-hero");
        if (bienvenida && "IntersectionObserver" in window) {
            new IntersectionObserver(([entrada]) => {
                document.body.dataset.vista = entrada.intersectionRatio < 0.85 ? "areas" : "inicio";
            }, { threshold: 0.85 }).observe(bienvenida);
        }
    }

    /* —— Área: índice y panel destacado ——
       Recorrer el índice con cursor, teclado o un primer toque cambia el panel; abrir es un
       segundo paso explícito. En pantallas estrechas el panel se despliega bajo la opción. */

    const explorador = document.querySelector("[data-explorador]");
    if (!explorador) return;
    const area = explorador.dataset.explorador;
    const items = [...explorador.querySelectorAll("a.indice-item")];
    const destacado = explorador.querySelector(".destacado");
    const escena = destacado.querySelector(".destacado-escena");
    const cuerpos = new Map([...destacado.querySelectorAll(".destacado-cuerpo")].map((c) => [c.dataset.id, c]));
    const estrecho = window.matchMedia("(max-width: 760px)");
    let elegida = null;

    function colocar() {
        const destino = estrecho.matches ? elegida.parentElement : explorador;
        if (destacado.parentElement !== destino) destino.append(destacado);
    }

    function seleccionar(item, { inicial = false } = {}) {
        if (!item || item === elegida) return;
        const anterior = elegida;
        elegida = item;
        for (const a of items) {
            a.classList.toggle("elegida", a === item);
            a.tabIndex = a === item ? 0 : -1; // una sola parada de Tab; las flechas recorren el resto
        }
        const cuerpo = cuerpos.get(item.dataset.id);
        cuerpos.forEach((c) => { c.hidden = c !== cuerpo; });
        const cambiaTema = escena.dataset.tema !== cuerpo.dataset.tema;
        escena.dataset.tema = cuerpo.dataset.tema;
        if (!inicial) {
            // El gesto del diorama se repite al cambiar de tema; el texto entra desde el lado
            // hacia el que se movió la selección.
            if (cambiaTema) { escena.classList.remove("gesto"); void escena.offsetWidth; }
            cuerpo.dataset.dir = anterior && items.indexOf(item) < items.indexOf(anterior) ? "arriba" : "abajo";
            cuerpo.classList.remove("cambia"); void cuerpo.offsetWidth; cuerpo.classList.add("cambia");
            sonar("seleccion", items.indexOf(item));
        }
        escena.classList.add("gesto");
        colocar();
        guardar(AREA, { ...leer(AREA), ultima: area, [area]: item.dataset.id });
    }

    // Lo último que se miró en esta área queda elegido al volver; un ancla de categoría
    // (las migas de una herramienta) elige la primera herramienta de esa categoría.
    const porId = (id) => items.find((a) => a.dataset.id === id);
    function inicial() {
        const tema = decodeURIComponent(location.hash.slice(1));
        const recordada = porId(leer(AREA)[area]);
        const delTema = tema && document.getElementById(tema)?.nextElementSibling?.querySelector("a.indice-item");
        if (delTema && recordada?.closest("ul") !== delTema.closest("ul")) return delTema;
        return recordada || items[0];
    }
    seleccionar(inicial(), { inicial: true });
    window.addEventListener("hashchange", () => seleccionar(inicial()));
    estrecho.addEventListener("change", colocar);

    let intencion = null;
    let puntero = "mouse";
    explorador.addEventListener("pointerdown", (event) => { puntero = event.pointerType; });
    explorador.addEventListener("pointerover", (event) => {
        const item = event.target.closest("a.indice-item");
        clearTimeout(intencion);
        // Un instante de intención: cruzar el índice hacia el panel no cambia la selección.
        if (item && event.pointerType === "mouse") intencion = setTimeout(() => seleccionar(item), 90);
    });
    explorador.addEventListener("focusin", (event) => seleccionar(event.target.closest("a.indice-item")));
    explorador.addEventListener("click", (event) => {
        const item = event.target.closest("a.indice-item");
        // Al tocar, el primer toque muestra la herramienta y el segundo la abre.
        if (item && puntero !== "mouse" && item !== elegida) {
            event.preventDefault();
            item.focus({ preventScroll: true });
        }
    });
    explorador.addEventListener("keydown", (event) => {
        if (event.altKey || event.ctrlKey || event.metaKey) return;
        const item = event.target.closest("a.indice-item");
        if (item) {
            const i = items.indexOf(item);
            const destino = { ArrowDown: items[i + 1], ArrowUp: items[i - 1], Home: items[0], End: items.at(-1) }[event.key];
            if (destino) { event.preventDefault(); destino.focus(); return; }
            if (event.key === "ArrowRight" && !estrecho.matches) {
                event.preventDefault();
                cuerpos.get(item.dataset.id).querySelector(".destacado-abrir").focus();
            }
        } else if (event.key === "ArrowLeft" && event.target.matches(".destacado-abrir") && !estrecho.matches) {
            event.preventDefault();
            elegida.focus();
        }
    });
})();
