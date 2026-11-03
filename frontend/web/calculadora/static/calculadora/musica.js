/* Música ambiental de PyGebra: una pieza original, instrumental y discreta para estudiar.
   Acordes lentos de Re mayor con su respiración y, de vez en cuando, unas notas de la misma
   «madera tibia» que los efectos. Todo se sintetiza al momento: sin archivos ni red.
   Solo suena si se pide, cada visita empieza en silencio y calla con la ventana oculta.
   La posición en la pieza se deriva del reloj: al cambiar de página continúa por donde iba.
   ponytail: cada página es un documento nuevo, así que al navegar la música baja y vuelve en
   1,5 s; para que no se interrumpa haría falta una aplicación de una sola página. */

window.Musica = (() => {
    "use strict";

    const PERIODO = 9.6; // un acorde: dos compases de 4/4 a 50 pulsos por minuto
    const PULSO = PERIODO / 8;
    const ATAQUE = 3, CAIDA = 4;
    const GANANCIA = 0.7; // con el 40 % por defecto, de fondo: muy por debajo de los efectos en energía
    const SESION = "pygebra-musica";
    const VOLUMEN = "pygebra-musica-volumen";

    // Bajo y tres voces (MIDI), enlazadas para que cada acorde se mueva lo mínimo.
    const ACORDES = [
        [50, 57, 64, 66], [47, 57, 62, 66], [43, 59, 62, 66], [45, 57, 59, 64],
        [42, 57, 62, 64], [43, 59, 62, 69], [40, 59, 62, 67], [45, 55, 62, 64],
        [47, 54, 62, 66], [43, 55, 62, 66], [50, 57, 62, 66], [45, 57, 61, 64],
        [50, 57, 64, 66], [47, 57, 62, 66], [43, 59, 62, 66], [45, 57, 59, 64],
    ];
    const ESCALA = [62, 64, 66, 69, 71, 74, 76]; // pentatónica de Re, como los efectos
    const DENSIDAD = [0.4, 0.65, 0.5, 0.15]; // cuántas frases hay en cada bloque de cuatro acordes
    const hz = (midi) => 440 * 2 ** ((midi - 69) / 12);

    // Azar con semilla (mulberry32): cada periodo suena siempre igual y nunca se repite la pieza.
    function azar(semilla) {
        let s = semilla >>> 0;
        return () => {
            s = (s + 0x6d2b79f5) >>> 0;
            let t = Math.imul(s ^ (s >>> 15), 1 | s);
            t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        };
    }

    // La sala: filtro cálido que respira despacio y un eco corto. Devuelve dónde conectar.
    function armar(c, destino) {
        const vivos = new Set();
        const bus = c.createGain();
        bus.connect(destino);
        const calido = c.createBiquadFilter();
        calido.type = "lowpass";
        calido.frequency.value = 950;
        calido.connect(bus);
        const respiracion = c.createOscillator();
        const profundidad = c.createGain();
        respiracion.frequency.value = 0.04;
        profundidad.gain.value = 220;
        respiracion.connect(profundidad).connect(calido.frequency);
        respiracion.start();
        const eco = c.createDelay(1);
        const realimentacion = c.createGain();
        const sombra = c.createBiquadFilter();
        eco.delayTime.value = PULSO * 0.6;
        realimentacion.gain.value = 0.3;
        sombra.type = "lowpass";
        sombra.frequency.value = 1500;
        eco.connect(sombra).connect(realimentacion).connect(eco);
        sombra.connect(bus);
        return {
            c, vivos, bus, calido, eco,
            parar() {
                respiracion.stop();
                vivos.forEach((o) => o.stop());
                bus.disconnect();
            },
        };
    }

    function oscilador(sala, f, tipo, t, fin, destino) {
        const o = sala.c.createOscillator();
        o.type = tipo;
        o.frequency.value = f;
        o.connect(destino);
        o.start(t);
        o.stop(fin);
        sala.vivos.add(o);
        o.onended = () => sala.vivos.delete(o);
        return o;
    }

    function acorde(sala, notas, t, r) {
        const { c, calido, eco } = sala;
        // Al entrar a mitad de un acorde (t en el pasado) este nace ahora y suelta a su hora.
        const desde = Math.max(t, c.currentTime);
        const suelta = Math.max(t + PERIODO, desde + ATAQUE);
        const fin = suelta + CAIDA;
        notas.forEach((midi, voz) => {
            const nivel = voz === 0 ? 0.11 : 0.055;
            const g = c.createGain();
            g.gain.setValueAtTime(0, desde);
            g.gain.linearRampToValueAtTime(nivel, desde + ATAQUE);
            g.gain.setValueAtTime(nivel, suelta);
            g.gain.linearRampToValueAtTime(0, fin);
            const panorama = c.createStereoPanner();
            panorama.pan.value = voz === 0 ? 0 : (voz - 2) * 0.35;
            g.connect(panorama).connect(calido);
            if (voz === 0) {
                oscilador(sala, hz(midi), "sine", desde, fin + 0.05, g);
                return;
            }
            // Dos osciladores apenas desafinados: el batido lento evita que suene a órgano.
            const envio = c.createGain();
            envio.gain.value = 0.12;
            g.connect(envio).connect(eco);
            for (const signo of [-1, 1]) {
                oscilador(sala, hz(midi), "triangle", desde, fin + 0.05, g).detune.value = signo * (2.5 + r() * 2);
            }
        });
    }

    function nota(sala, midi, t, vel, pan) {
        const { c, bus, eco } = sala;
        const f = hz(midi);
        const dur = 3.2;
        const env = c.createGain();
        env.gain.setValueAtTime(0.0001, t);
        env.gain.linearRampToValueAtTime(vel, t + 0.015);
        env.gain.exponentialRampToValueAtTime(0.0001, t + dur);
        const panorama = c.createStereoPanner();
        panorama.pan.value = pan;
        env.connect(panorama).connect(bus);
        const envio = c.createGain();
        envio.gain.value = 0.35;
        env.connect(envio).connect(eco);
        oscilador(sala, f, "sine", t, t + dur + 0.05, env);
        const madera = c.createGain();
        madera.gain.setValueAtTime(0.1, t);
        madera.gain.exponentialRampToValueAtTime(0.0001, t + 0.5);
        madera.connect(env);
        oscilador(sala, f * 3.9, "sine", t, t + 0.55, madera);
        const octava = c.createGain();
        octava.gain.setValueAtTime(0.18, t);
        octava.gain.exponentialRampToValueAtTime(0.0001, t + 1.4);
        octava.connect(env);
        oscilador(sala, f * 2, "sine", t, t + 1.45, octava);
    }

    // Una frase de pocas notas por la escala que descansa en una nota del acorde.
    function frase(sala, notas, t, r) {
        const clases = new Set(notas.map((m) => m % 12));
        let i = 1 + Math.floor(r() * 4);
        let pulso = 1 + Math.floor(r() * 3);
        const cuantas = 2 + Math.floor(r() * 3);
        for (let n = 0; n < cuantas && pulso < 8; n++) {
            const siguiente = pulso + [1, 1, 2, 2, 3][Math.floor(r() * 5)];
            const ultima = n === cuantas - 1 || siguiente >= 8;
            if (ultima && !clases.has(ESCALA[i] % 12)) {
                const candidatas = ESCALA.map((_, k) => k).filter((k) => clases.has(ESCALA[k] % 12));
                if (candidatas.length) i = candidatas.reduce((a, b) => (Math.abs(b - i) < Math.abs(a - i) ? b : a));
            }
            const momento = t + pulso * PULSO;
            const vel = 0.1 + r() * 0.06;
            const pan = (r() - 0.5) * 0.5;
            if (momento >= sala.c.currentTime) nota(sala, ESCALA[i], momento, vel, pan);
            pulso = siguiente;
            i = Math.min(ESCALA.length - 1, Math.max(0, i + [-2, -1, -1, 1, 1, 2][Math.floor(r() * 6)]));
        }
    }

    // Lo que suena en el periodo k, empezando en el instante t del contexto.
    function componer(sala, k, t) {
        const notas = ACORDES[k % ACORDES.length];
        const r = azar(Math.imul(k, 2654435761));
        acorde(sala, notas, t, r);
        if (r() < DENSIDAD[Math.floor((k % ACORDES.length) / 4)]) frase(sala, notas, t, r);
    }

    /* —— Encender y apagar —— */

    let deseada = false, sala = null, reloj = null, esperando = false;
    try { deseada = sessionStorage.getItem(SESION) === "on"; } catch (_) { /* Solo esta página. */ }

    const nivel = () => (Number(window.preferencias.leer(VOLUMEN)) || 40) / 100 * GANANCIA;

    function programar(activa, k, t) {
        // Lo que ya pasó (un temporizador retrasado) se salta en vez de sonar todo junto.
        while (t < activa.c.currentTime + 1.5) {
            if (t + PERIODO > activa.c.currentTime) componer(activa, k, t);
            k++;
            t += PERIODO;
        }
        return [k, t];
    }

    function encender() {
        if (sala || !deseada || document.hidden) return;
        const c = window.Sonido.contexto();
        if (!c) return;
        if (c.state !== "running") {
            // El navegador pide un gesto antes de sonar; se atiende al primero que llegue.
            c.resume().then(encender, () => {});
            if (!esperando) {
                esperando = true;
                const gesto = () => {
                    esperando = false;
                    removeEventListener("pointerdown", gesto, true);
                    removeEventListener("keydown", gesto, true);
                    if (deseada) c.resume();
                };
                addEventListener("pointerdown", gesto, true);
                addEventListener("keydown", gesto, true);
            }
            return;
        }
        sala = armar(c, c.destination);
        sala.bus.gain.setValueAtTime(0, c.currentTime);
        sala.bus.gain.linearRampToValueAtTime(nivel(), c.currentTime + 1.5);
        const ahora = Date.now() / 1000;
        let k = Math.floor(ahora / PERIODO);
        let t = c.currentTime - (ahora % PERIODO);
        const activa = sala;
        [k, t] = programar(activa, k, t);
        reloj = setInterval(() => { [k, t] = programar(activa, k, t); }, 2000);
    }

    function apagar() {
        if (!sala) return;
        const anterior = sala;
        sala = null;
        clearInterval(reloj);
        const { c, bus } = anterior;
        bus.gain.cancelScheduledValues(c.currentTime);
        bus.gain.setTargetAtTime(0, c.currentTime, 0.18);
        setTimeout(() => {
            anterior.parar();
            if (!sala) c.suspend(); // en silencio el contexto no gasta nada
        }, 700);
    }

    function alternar() {
        deseada = !deseada;
        try {
            if (deseada) sessionStorage.setItem(SESION, "on");
            else sessionStorage.removeItem(SESION);
        } catch (_) { /* Vale para esta página. */ }
        if (deseada) encender();
        else apagar();
        return deseada;
    }

    document.addEventListener("visibilitychange", () => (document.hidden ? apagar() : encender()));
    addEventListener("pagehide", apagar);
    addEventListener("pageshow", (event) => { if (event.persisted) encender(); });
    setTimeout(encender); // aparte: un fallo de audio no debe dejar sin Opciones a la página

    return {
        disponible: Boolean(window.AudioContext || window.webkitAudioContext),
        pedida: () => deseada,
        alternar,
        volumen(valor) {
            if (sala) sala.bus.gain.setTargetAtTime(valor / 100 * GANANCIA, sala.c.currentTime, 0.1);
        },
        // Para ensayar la pieza sin altavoces (OfflineAudioContext) en las pruebas.
        armar,
        componer,
        PERIODO,
    };
})();
