/* Identidad sonora de PyGebra.
   Notas breves de «madera tibia»: un tono, un parcial inharmónico que se apaga antes
   y, a veces, un soplo de aire filtrado. Afinadas en la pentatónica de Re, así que
   cualquier combinación suena bien. Todo se sintetiza al momento: sin archivos ni red.
   Apagado por defecto. El sonido nunca es la única señal: cada efecto acompaña un
   cambio visible. */

window.Sonido = (() => {
    "use strict";

    const ESCALA = [587.33, 659.25, 739.99, 880, 987.77]; // Re5 Mi5 Fa#5 La5 Si5
    const preferencias = window.preferencias;
    let ctx = null, salida = null, ultimaSeleccion = 0;
    let activo = preferencias.leer("pygebra-sonido") === "on";
    let volumen = Number(preferencias.leer("pygebra-volumen") || 50) / 100;

    // También lo usa la música: un solo contexto de audio por página.
    function preparar() {
        if (!ctx) {
            const AC = window.AudioContext || window.webkitAudioContext;
            if (!AC) return false;
            ctx = new AC();
            salida = ctx.createGain();
            const suave = ctx.createBiquadFilter();
            suave.type = "lowpass";
            suave.frequency.value = 5200;
            salida.connect(suave).connect(ctx.destination);
        }
        // ponytail: volumen máximo fijo en 0.45; si alguien lo pide más alto, exponer el techo.
        salida.gain.value = volumen * 0.45;
        return true;
    }

    function nota(f, t, { dur = 0.32, vel = 0.3, brillo = 1 } = {}) {
        // Pequeñas variaciones de afinación e intensidad: el mismo gesto nunca suena idéntico.
        const desvio = 2 ** (((Math.random() - 0.5) * 16) / 1200);
        vel *= 0.9 + Math.random() * 0.2;
        const env = ctx.createGain();
        env.gain.setValueAtTime(0.0001, t);
        env.gain.exponentialRampToValueAtTime(vel, t + 0.006);
        env.gain.exponentialRampToValueAtTime(0.0001, t + dur);
        env.connect(salida);

        const tono = ctx.createOscillator();
        tono.frequency.value = f * desvio;
        tono.connect(env);

        const parcial = ctx.createOscillator();
        const gParcial = ctx.createGain();
        parcial.frequency.value = f * desvio * 3.9;
        gParcial.gain.setValueAtTime(0.35 * brillo + 0.0001, t);
        gParcial.gain.exponentialRampToValueAtTime(0.0001, t + dur * 0.35);
        parcial.connect(gParcial).connect(env);

        for (const o of [tono, parcial]) { o.start(t); o.stop(t + dur + 0.05); }
    }

    function soplo(t, { f = 1800, dur = 0.035, vel = 0.12 } = {}) {
        const n = Math.ceil(ctx.sampleRate * dur);
        const buffer = ctx.createBuffer(1, n, ctx.sampleRate);
        const datos = buffer.getChannelData(0);
        for (let i = 0; i < n; i++) datos[i] = (Math.random() * 2 - 1) * (1 - i / n) ** 2;
        const fuente = ctx.createBufferSource();
        fuente.buffer = buffer;
        const banda = ctx.createBiquadFilter();
        banda.type = "bandpass";
        banda.frequency.value = f;
        banda.Q.value = 1.4;
        const g = ctx.createGain();
        g.gain.value = vel;
        fuente.connect(banda).connect(g).connect(salida);
        fuente.start(t);
    }

    const EFECTOS = {
        // Recorrer opciones: una nota apenas audible cuya altura depende de la posición.
        seleccion(t, i = 0) { nota(ESCALA[i % ESCALA.length], t, { dur: 0.14, vel: 0.11, brillo: 0.6 }); },
        // Entrar sube; volver baja y es más suave.
        entrar(t) {
            soplo(t, { f: 2400, vel: 0.08 });
            nota(ESCALA[0], t, { vel: 0.2 });
            nota(ESCALA[3], t + 0.07, { vel: 0.24, dur: 0.42 });
        },
        volver(t) {
            nota(ESCALA[3], t, { vel: 0.16, brillo: 0.6 });
            nota(ESCALA[0], t + 0.07, { vel: 0.18, dur: 0.36, brillo: 0.4 });
        },
        // Un cálculo resuelto: arpegio corto que se queda sonando un instante.
        confirmar(t) {
            [0, 2, 3].forEach((k, j) => nota(ESCALA[k], t + j * 0.055, { vel: 0.2, dur: 0.3 }));
            nota(ESCALA[0] * 2, t + 0.17, { vel: 0.15, dur: 0.75, brillo: 0.3 });
        },
        // Algo que corregir: dos notas graves y opacas, nunca una alarma.
        aviso(t) {
            nota(ESCALA[1] / 2, t, { vel: 0.22, dur: 0.22, brillo: 0.15 });
            nota(ESCALA[0] / 2, t + 0.09, { vel: 0.22, dur: 0.3, brillo: 0.15 });
        },
        // El interruptor de la lámpara al cambiar entre día y noche.
        interruptor(t) {
            soplo(t, { f: 3200, dur: 0.02, vel: 0.22 });
            soplo(t + 0.05, { f: 2100, dur: 0.025, vel: 0.16 });
        },
        // Botones pequeños: un toque de lápiz.
        tic(t) {
            soplo(t, { f: 2600, dur: 0.018, vel: 0.1 });
            nota(ESCALA[4], t, { dur: 0.08, vel: 0.05, brillo: 0.3 });
        },
    };

    function tocar(nombre, ...args) {
        if (!activo || !preparar()) return;
        if (nombre === "seleccion") {
            const ahora = performance.now();
            if (ahora - ultimaSeleccion < 45) return; // recorrer rápido no debe sonar a ráfaga
            ultimaSeleccion = ahora;
        }
        if (ctx.state === "running") {
            EFECTOS[nombre](ctx.currentTime + 0.005, ...args);
            return;
        }
        // El navegador solo deja sonar tras una interacción: si el permiso llega tarde,
        // el efecto ya no corresponde a nada visible y se descarta.
        const pedido = performance.now();
        ctx.resume().then(() => {
            if (performance.now() - pedido < 250) EFECTOS[nombre](ctx.currentTime + 0.005, ...args);
        }, () => {});
    }

    // Al llegar desde otra página de PyGebra: entrar, volver, o el desenlace de un cálculo.
    if (activo && document.documentElement.hasAttribute("data-llegada")) {
        const llegada = document.querySelector("[data-error-general], .field-error") ? "aviso"
            : document.querySelector("[data-resultado]") ? "confirmar"
            : document.documentElement.dataset.dir === "atras" ? "volver" : "entrar";
        tocar(llegada);
    }

    // El interruptor del tema suena como el de la lámpara.
    document.getElementById("theme-toggle")?.addEventListener("click", () => tocar("interruptor"));
    document.querySelector(".nota")?.addEventListener("toggle", () => tocar("tic"));

    return {
        tocar,
        contexto: () => (preparar() ? ctx : null),
        configurar(opciones) {
            if ("activo" in opciones) activo = opciones.activo;
            if ("volumen" in opciones) volumen = opciones.volumen;
            if (salida) salida.gain.value = volumen * 0.45;
        },
    };
})();
