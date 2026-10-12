(() => {
    "use strict";

    // Solo la app de escritorio sirve esta página. Cada paso es un clic del usuario;
    // durante la descarga se consulta el estado local, nunca Internet desde aquí.
    const panel = document.querySelector("[data-actualizador]");
    if (!panel) return;

    const mensaje = panel.querySelector("[data-mensaje]");
    const progreso = panel.querySelector("[data-progreso]");
    const botones = {
        buscar: panel.querySelector('[data-accion="buscar"]'),
        descargar: panel.querySelector('[data-accion="descargar"]'),
        instalar: panel.querySelector('[data-accion="instalar"]')
    };
    // Qué botón ofrece cada estado; los estados en curso no ofrecen ninguno.
    const accionPorEstado = {
        inicial: "buscar",
        actualizado: "buscar",
        error_conexion: "buscar",
        checksum_invalido: "buscar",
        error: "buscar",
        disponible: "descargar",
        listo: "instalar"
    };
    const enCurso = new Set(["buscando", "descargando", "verificando"]);
    const token = document.querySelector('meta[name="csrf-token"]');
    let temporizador = null;

    function pintar(datos) {
        panel.dataset.estado = datos.estado;
        if (datos.mensaje && mensaje.textContent !== datos.mensaje) mensaje.textContent = datos.mensaje;
        const accion = accionPorEstado[datos.estado];
        for (const [nombre, boton] of Object.entries(botones)) {
            boton.hidden = nombre !== accion;
            boton.disabled = false;
        }
        if (datos.estado === "disponible") {
            botones.descargar.textContent = `Descargar PyGebra ${datos.version_disponible}`;
        }
        progreso.hidden = datos.estado !== "descargando";
        if (Number.isInteger(datos.progreso)) {
            progreso.value = datos.progreso;
            progreso.textContent = `${datos.progreso} %`;
        }
        clearTimeout(temporizador);
        if (enCurso.has(datos.estado)) temporizador = setTimeout(consultar, 500);
    }

    function fallo() {
        pintar({
            estado: "error",
            mensaje: "No se pudo completar la actualización. Inténtalo de nuevo más tarde."
        });
    }

    function consultar() {
        fetch("/actualizaciones/estado/", {cache: "no-store"})
            .then((respuesta) => respuesta.ok ? respuesta.json() : Promise.reject())
            .then(pintar, fallo);
    }

    function ejecutar(accion) {
        for (const boton of Object.values(botones)) boton.disabled = true;
        if (accion === "buscar") pintar({estado: "buscando", mensaje: "Buscando actualizaciones…"});
        fetch(`/actualizaciones/${accion}/`, {
            method: "POST",
            headers: {"X-CSRFToken": token ? token.content : ""}
        })
            .then((respuesta) => respuesta.ok ? respuesta.json() : Promise.reject())
            .then(pintar, fallo);
    }

    for (const [accion, boton] of Object.entries(botones)) {
        boton.addEventListener("click", () => ejecutar(accion));
    }
    pintar({estado: panel.dataset.estado, progreso: progreso.hasAttribute("value") ? progreso.value : null});
})();
