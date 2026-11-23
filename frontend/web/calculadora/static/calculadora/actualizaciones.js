(() => {
    "use strict";

    // Solo la app de escritorio sirve esta página. Cada paso es un clic del usuario;
    // durante la descarga se consulta el estado local, nunca Internet desde aquí.
    // Los textos de cada estado viven en la plantilla (data-para) y el CSS elige cuál se ve;
    // aquí solo se pinta lo que informa el servidor.
    const escena = document.querySelector("[data-actualizador]");
    if (!escena) return;

    const mensaje = escena.querySelector("[data-mensaje]");
    const progreso = escena.querySelector("[data-progreso]");
    const porcentaje = escena.querySelector("[data-porcentaje]");
    const boton = escena.querySelector("[data-accion]");
    const versiones = escena.querySelectorAll("[data-version-disponible]");
    const pasos = escena.querySelectorAll("[data-paso]");

    // Qué acción ofrece cada estado; los estados en curso no ofrecen ninguna.
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
    // Paso de la ruta (Buscar, Descargar, Verificar, Instalar) en el que está cada estado.
    const pasoPorEstado = {
        inicial: [0, "siguiente"],
        buscando: [0, "actual"],
        actualizado: [0, "hecho"],
        disponible: [1, "siguiente"],
        descargando: [1, "actual"],
        verificando: [2, "actual"],
        listo: [3, "siguiente"],
        instalando: [3, "actual"]
    };
    const errores = new Set(["error_conexion", "checksum_invalido", "error"]);
    const lecturas = {hecho: "completado", actual: "en curso", siguiente: "siguiente", fallo: "no se completó", pendiente: ""};
    const token = document.querySelector('meta[name="csrf-token"]');
    let temporizador = null;
    // El servidor no dice en qué paso falló algo: se marca el último paso visto en esta visita.
    let ultimoPaso = null;

    function marcarRuta(estado) {
        let [indice, avance] = pasoPorEstado[estado] || [null, "fallo"];
        if (indice !== null) ultimoPaso = indice;
        else if (errores.has(estado)) indice = ultimoPaso ?? (estado === "checksum_invalido" ? 2 : null);
        pasos.forEach((paso, i) => {
            const valor = indice === null || i > indice ? "pendiente" : i < indice ? "hecho" : avance;
            paso.dataset.avance = valor;
            paso.querySelector("[data-lectura]").textContent = lecturas[valor] ? `: ${lecturas[valor]}` : "";
            if (valor === "actual" || valor === "siguiente") paso.setAttribute("aria-current", "step");
            else paso.removeAttribute("aria-current");
        });
    }

    function pintar(datos) {
        const estado = datos.estado;
        escena.dataset.estado = estado;
        if (datos.mensaje && mensaje.textContent !== datos.mensaje) mensaje.textContent = datos.mensaje;
        if (datos.version_disponible) {
            for (const version of versiones) version.textContent = datos.version_disponible;
        }
        const accion = accionPorEstado[estado];
        boton.dataset.accion = accion || "";
        boton.setAttribute("aria-disabled", String(!accion));
        // La línea solo avanza con el porcentaje real; terminada la descarga queda completa.
        const descargado = estado === "descargando" ? (Number.isInteger(datos.progreso) ? datos.progreso : null)
            : ["verificando", "listo", "instalando"].includes(estado) ? 100 : 0;
        if (descargado !== null) escena.style.setProperty("--p", descargado / 100);
        progreso.hidden = estado !== "descargando";
        if (estado === "descargando" && descargado !== null) {
            progreso.value = descargado;
            progreso.textContent = `${descargado} %`;
            porcentaje.textContent = descargado;
        }
        marcarRuta(estado);
        clearTimeout(temporizador);
        if (enCurso.has(estado)) temporizador = setTimeout(consultar, 500);
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

    // Un solo botón: conserva el foco mientras su acción y su texto cambian con el estado.
    boton.addEventListener("click", () => {
        const accion = boton.dataset.accion;
        if (!accion || boton.getAttribute("aria-disabled") === "true") return;
        boton.setAttribute("aria-disabled", "true");
        if (accion === "buscar") pintar({estado: "buscando", mensaje: "Buscando actualizaciones…"});
        fetch(`/actualizaciones/${accion}/`, {
            method: "POST",
            headers: {"X-CSRFToken": token ? token.content : ""}
        })
            .then((respuesta) => respuesta.ok ? respuesta.json() : Promise.reject())
            .then(pintar, fallo);
    });

    pintar({estado: escena.dataset.estado, progreso: progreso.hasAttribute("value") ? progreso.value : null});
})();
