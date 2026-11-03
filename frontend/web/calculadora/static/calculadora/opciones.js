(() => {
    "use strict";

    // Opciones de presentación: estilo y sonido. Se guardan con window.preferencias
    // (localStorage y, en escritorio, el archivo propio), igual que el tema.
    const root = document.documentElement;
    const boton = document.getElementById("opciones-toggle");
    const panel = document.getElementById("opciones");
    if (!boton || !panel) return;
    const preferencias = window.preferencias;
    const volumen = panel.querySelector("#volumen");
    const musica = panel.querySelector("#musica-toggle");
    const volumenMusica = panel.querySelector("#musica-volumen");

    function sincronizar() {
        const actuales = {
            estilo: root.getAttribute("data-estilo"),
            sonido: preferencias.leer("pygebra-sonido") === "on" ? "on" : "off",
        };
        panel.querySelectorAll('input[type="radio"]').forEach((radio) => {
            radio.checked = actuales[radio.name] === radio.value;
        });
        volumen.value = preferencias.leer("pygebra-volumen") || 50;
        volumen.disabled = actuales.sonido !== "on";
        musica.textContent = window.Musica.pedida() ? "Pausar música" : "Reproducir música";
        volumenMusica.value = preferencias.leer("pygebra-musica-volumen") || 40;
    }

    panel.querySelector("#musica-grupo").hidden = !window.Musica.disponible;
    musica.addEventListener("click", () => {
        window.Musica.alternar();
        sincronizar();
    });
    // El volumen de la música se oye al arrastrar y se guarda al soltar.
    volumenMusica.addEventListener("input", () => window.Musica.volumen(Number(volumenMusica.value)));

    panel.addEventListener("change", (event) => {
        const { name, value } = event.target;
        if (name === "musica-volumen") {
            preferencias.guardar("pygebra-musica-volumen", value);
            return;
        }
        if (name === "volumen") {
            preferencias.guardar("pygebra-volumen", value);
            window.Sonido.configurar({ volumen: value / 100 });
            window.Sonido.tocar("seleccion", 3); // muestra del volumen elegido
            return;
        }
        preferencias.guardar(`pygebra-${name}`, value);
        if (name === "estilo") {
            root.setAttribute("data-estilo", value);
            window.Sonido.tocar("tic");
        } else {
            window.Sonido.configurar({ activo: value === "on" });
            // Al activar se escucha cómo suena; al silenciar, nada.
            window.Sonido.tocar("confirmar");
        }
        sincronizar();
    });
    panel.addEventListener("toggle", (event) => {
        if (event.newState === "open") sincronizar();
    });
    // Una página restaurada del historial (bfcache) refleja lo elegido en otra página.
    window.addEventListener("pageshow", (event) => {
        if (!event.persisted) return;
        const estilo = preferencias.leer("pygebra-estilo") === "minimalista" ? "minimalista" : "estudio";
        root.setAttribute("data-estilo", estilo);
        window.Sonido.configurar({
            activo: preferencias.leer("pygebra-sonido") === "on",
            volumen: Number(preferencias.leer("pygebra-volumen") || 50) / 100,
        });
        sincronizar();
    });

    sincronizar();
    boton.hidden = false;
})();
