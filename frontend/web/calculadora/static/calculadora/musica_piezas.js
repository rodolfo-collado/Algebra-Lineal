/* La pequeña banda sonora de PyGebra: cuatro piezas originales e instrumentales para
   acompañar sesiones largas. Las une la tonalidad (Re mayor y su relativa, Si menor); las tres
   últimas comparten además habitación, timbres solo con armónicos y un motivo: la – fa♯ – mi.
   Todo se sintetiza al momento: sin archivos ni red, y cada pieza suena siempre igual, sin
   notas al azar. musica.js decide cuál suena y cuándo. */

window.MusicaPiezas = (() => {
    "use strict";

    const hz = (midi) => 440 * 2 ** ((midi - 69) / 12);
    const modulo = (k, largo) => ((k % largo) + largo) % largo;

    function azar(semilla) { // mulberry32: el mismo sonido en cada sesión
        let s = semilla >>> 0;
        return () => {
            s = (s + 0x6d2b79f5) >>> 0;
            let t = Math.imul(s ^ (s >>> 15), 1 | s);
            t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        };
    }

    /* —— Rincón tranquilo ——
       La primera composición, tal cual: acordes lentos de 50 pulsos por minuto y, de vez en
       cuando, unas notas de la misma «madera tibia» que los efectos. */
    const rincon = (() => {
        const PERIODO = 9.6; // un acorde: dos compases de 4/4 a 50 pulsos por minuto
        const PULSO = PERIODO / 8;
        const ATAQUE = 3, CAIDA = 4;

        // Bajo y tres voces (MIDI), enlazadas para que cada acorde se mueva lo mínimo.
        const ACORDES = [
            [50, 57, 64, 66], [47, 57, 62, 66], [43, 59, 62, 66], [45, 57, 59, 64],
            [42, 57, 62, 64], [43, 59, 62, 69], [40, 59, 62, 67], [45, 55, 62, 64],
            [47, 54, 62, 66], [43, 55, 62, 66], [50, 57, 62, 66], [45, 57, 61, 64],
            [50, 57, 64, 66], [47, 57, 62, 66], [43, 59, 62, 66], [45, 57, 59, 64],
        ];
        const ESCALA = [62, 64, 66, 69, 71, 74, 76]; // pentatónica de Re, como los efectos
        const DENSIDAD = [0.4, 0.65, 0.5, 0.15]; // cuántas frases hay en cada bloque de cuatro acordes

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
                    realimentacion.disconnect();
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

        return {
            id: "rincon",
            nombre: "Rincón tranquilo",
            descripcion: "Acordes lentos y teclas sueltas",
            COMPAS: PERIODO,
            LARGO: ACORDES.length,
            vueltas: 2,
            atras: 0,
            ganancia: 1.05,
            armar,
            componer,
        };
    })();

    /* —— Lo que comparten las otras tres: instrumentos y habitación —— */

    function vivo(sala, fuente, inicio, fin) {
        sala.vivos.add(fuente);
        fuente.onended = () => sala.vivos.delete(fuente);
        fuente.start(inicio);
        if (fin !== undefined) fuente.stop(fin);
    }

    function tono(sala, nombre, midi, inicio, fin, nivel, ataque, sostén, caida, destino) {
        const { c } = sala;
        const g = c.createGain();
        g.gain.setValueAtTime(0, inicio);
        g.gain.linearRampToValueAtTime(nivel, inicio + ataque);
        g.gain.exponentialRampToValueAtTime(Math.max(nivel * sostén, 0.0001), fin);
        g.gain.linearRampToValueAtTime(0, fin + caida);
        g.connect(destino);
        const o = c.createOscillator();
        o.setPeriodicWave(sala.ondas[nombre]);
        o.frequency.value = hz(midi);
        o.connect(g);
        vivo(sala, o, inicio, fin + caida + 0.02);
    }

    function golpe(sala, nombre, inicio, nivel, destino = sala.canales.bateria) {
        const { c } = sala;
        const g = c.createGain();
        g.gain.value = nivel;
        g.connect(destino);
        const s = c.createBufferSource();
        s.buffer = sala.banco[nombre];
        s.connect(g);
        vivo(sala, s, inicio);
    }

    function crearBuffer(c, segundos, canales, llenar) {
        const buffer = c.createBuffer(canales, Math.ceil(segundos * c.sampleRate), c.sampleRate);
        for (let canal = 0; canal < canales; canal++) llenar(buffer.getChannelData(canal));
        return buffer;
    }

    const pasoBajo = (c, corte) => 1 - Math.exp((-2 * Math.PI * corte) / c.sampleRate);

    // Percusión y disco se calculan una vez y luego solo se reproducen: casi no gastan.
    function muestras(c) {
        const r = azar(7);
        const sr = c.sampleRate;
        const crear = (segundos, canales, llenar) => crearBuffer(c, segundos, canales, llenar);
        const paso = (corte) => pasoBajo(c, corte);
        return {
            bombo: crear(0.3, 1, (d) => {
                let fase = 0;
                for (let i = 0; i < d.length; i++) {
                    const t = i / sr;
                    fase += (2 * Math.PI * (46 + 62 * Math.exp(-t / 0.03))) / sr;
                    d[i] = Math.sin(fase) * Math.exp(-t / 0.1) * (1 - Math.exp(-t / 0.002));
                }
            }),
            caja: crear(0.24, 1, (d) => {
                let ruido = 0;
                const a = paso(2400);
                for (let i = 0; i < d.length; i++) {
                    const t = i / sr;
                    ruido += a * (r() * 2 - 1 - ruido);
                    const sonido = Math.sin(2 * Math.PI * 180 * t) * Math.exp(-t / 0.035) * 0.4;
                    d[i] = (ruido * 1.6 * Math.exp(-t / 0.055) + sonido) * (1 - Math.exp(-t / 0.003));
                }
            }),
            shaker: crear(0.08, 1, (d) => {
                let previo = 0;
                for (let i = 0; i < d.length; i++) {
                    const t = i / sr;
                    const n = r() * 2 - 1;
                    d[i] = (n - previo) * (1 - Math.exp(-t / 0.006)) * Math.exp(-t / 0.018);
                    previo = n;
                }
            }),
            disco: crear(3.7, 1, (d) => {
                let ruido = 0;
                const a = paso(900);
                for (let i = 0; i < d.length; i++) {
                    ruido += a * (r() * 2 - 1 - ruido);
                    d[i] = ruido * 0.5;
                }
                for (let n = 0; n < 11; n++) { // algún chasquido suelto del vinilo
                    const inicio = Math.floor(r() * (d.length - 80));
                    const fuerza = 0.5 + r();
                    for (let i = 0; i < 60 && inicio + i < d.length; i++) d[inicio + i] += fuerza * (r() - 0.5) * Math.exp(-i / 12);
                }
            }),
            sala: crear(0.9, 1, (d) => { // una habitación pequeña, oscura y sin metales
                let ruido = 0;
                const a = paso(1600);
                for (let i = 0; i < d.length; i++) {
                    ruido += a * (r() * 2 - 1 - ruido);
                    d[i] = ruido * Math.exp(-(i / sr) / 0.28);
                }
            }),
        };
    }

    // Lo común: la habitación, la mezcla con menos brillo (como una cinta) y lo que no para.
    function escenario(c, destino, { brillo, timbres, niveles }) {
        const vivos = new Set();
        const fijos = [];
        const bus = c.createGain();
        bus.connect(destino);
        const cinta = c.createBiquadFilter();
        cinta.type = "lowpass";
        cinta.frequency.value = brillo;
        cinta.connect(bus);
        const banco = muestras(c);
        const eco = c.createConvolver();
        eco.buffer = banco.sala;
        const ecoNivel = c.createGain();
        ecoNivel.gain.value = 0.32;
        eco.connect(ecoNivel).connect(cinta);
        const canales = {};
        for (const [nombre, nivel] of Object.entries(niveles)) {
            canales[nombre] = c.createGain();
            canales[nombre].gain.value = nivel;
        }
        const ondas = {};
        for (const [nombre, reales] of Object.entries(timbres)) {
            ondas[nombre] = c.createPeriodicWave(new Float32Array(reales.length), Float32Array.from(reales));
        }
        const alParar = [];
        return {
            c, vivos, bus, cinta, banco, canales, ondas, fijos, alParar,
            envio(canal, cantidad) {
                const g = c.createGain();
                g.gain.value = cantidad;
                canal.connect(g).connect(eco);
            },
            // Un filtro o un paneo que se mueve muy despacio.
            vaiven(frecuencia, profundidad, destinoLento) {
                const lento = c.createOscillator();
                const cuanto = c.createGain();
                lento.frequency.value = frecuencia;
                cuanto.gain.value = profundidad;
                lento.connect(cuanto).connect(destinoLento);
                fijos.push(lento);
            },
            arrancar() {
                fijos.forEach((fijo) => fijo.start());
            },
            parar() {
                fijos.forEach((fijo) => fijo.stop());
                vivos.forEach((o) => o.stop());
                alParar.forEach((accion) => accion());
                bus.disconnect();
            },
        };
    }

    function filtro(c, tipo, frecuencia) {
        const f = c.createBiquadFilter();
        f.type = tipo;
        f.frequency.value = frecuencia;
        return f;
    }

    function paneo(c, valor) {
        const p = c.createStereoPanner();
        p.pan.value = valor;
        return p;
    }

    // Un soplo de ruido que se repite sin costura: la última parte se funde con la primera.
    function soplo(c, segundos, corte, semilla, grave = 0) {
        const r = azar(semilla);
        const a = pasoBajo(c, corte);
        const b = grave ? pasoBajo(c, grave) : 0;
        const fundido = Math.floor(0.4 * c.sampleRate);
        const crudo = new Float32Array(Math.ceil(segundos * c.sampleRate) + fundido);
        let agudo = 0, cuerpo = 0;
        for (let i = 0; i < crudo.length; i++) {
            agudo += a * (r() * 2 - 1 - agudo);
            cuerpo += b * (agudo - cuerpo);
            crudo[i] = agudo - cuerpo;
        }
        return crearBuffer(c, segundos, 1, (d) => {
            for (let i = 0; i < d.length; i++) {
                const peso = Math.min(1, i / fundido);
                d[i] = crudo[i] * peso + (i < fundido ? crudo[d.length + i] * (1 - peso) : 0);
            }
        });
    }

    function enBucle(sala, buffer, nivel, destino) {
        const { c } = sala;
        const s = c.createBufferSource();
        s.buffer = buffer;
        s.loop = true;
        const g = c.createGain();
        g.gain.value = nivel;
        s.connect(g).connect(destino);
        sala.fijos.push(s);
    }

    /* —— Café de medianoche ——
       Lo-fi con un toque de jazz: 64 compases a unos 70 pulsos por minuto, con bajo cálido,
       percusión discreta y teclas de fondo. */
    const cafe = (() => {
        const COMPAS = 3.4; // cuatro pulsos, unos 70 por minuto
        const PULSO = COMPAS / 4;
        const COLUMPIO = 0.6; // la corchea de contratiempo llega tarde: de ahí el vaivén

        /* Re mayor. Tres voces abiertas por acorde, medidas por su aspereza: juntas en el grave
           suenan turbias. Se mueven lo mínimo y nunca quedan a un semitono ni a una novena menor;
           tests.buscador_browser lo comprueba en toda la pieza. */
        const ACORDES = {
            D: { voces: [57, 66, 73], raiz: 38, quinta: 33 }, // Dmaj7
            Bm: { voces: [57, 66, 74], raiz: 35, quinta: 42 }, // Bm7
            Em: { voces: [59, 67, 74], raiz: 40, quinta: 35 }, // Em7
            Asus: { voces: [59, 67, 74], raiz: 33, quinta: 40 }, // A9sus
            A13: { voces: [59, 67, 73], raiz: 33, quinta: 40 }, // A7(9)
            G: { voces: [59, 66, 74], raiz: 43, quinta: 38 }, // Gmaj7
            Fsm: { voces: [57, 64, 73], raiz: 42, quinta: 37 }, // F#m7
        };
        const SECCIONES = {
            A: ["D", "D", "Bm", "Bm", "Em", "Em", "Asus", "A13"],
            B: ["G", "G", "Fsm", "Fsm", "Em", "Em", "Asus", "A13"],
        };
        const FORMA = ["A", "A", "B", "A", "A", "B", "A", "A"]; // cada sección, ocho compases
        const LARGO = FORMA.length * 8;
        // Nota de paso del bajo hacia cada raíz.
        const PASO = { 38: 37, 35: 37, 40: 38, 33: 35, 43: 45, 42: 45 };

        // Frases de la voz, por encima de las teclas: [compás de la sección, pulso, nota, duración].
        // Pocas notas, nunca cruzan un cambio de acorde y descansan antes de que llegue.
        const FRASES = {
            A: [[0, 1.5, 81, 1], [0, 2.5, 78, 1.4],
                [2, 1.5, 78, 1], [2, 2.5, 81, 0.9], [3, 0, 78, 2],
                [4, 1.5, 78, 1], [4, 2.5, 76, 1.4],
                [6, 1.5, 76, 1], [6, 2.5, 78, 1.2]],
            B: [[0, 1.5, 78, 1], [0, 2.5, 81, 1.4],
                [2, 1.5, 81, 1], [2, 2.5, 76, 1.4],
                [4, 1.5, 78, 1], [4, 2.5, 81, 1.2],
                [6, 2.5, 78, 1.2], [7, 0, 76, 2]],
        };
        // Qué suena en cada sección de la forma; las partes sin percusión dejan respirar.
        const ARREGLO = [
            { voz: false, bajoDesde: 4, caja: 4, bombo: 4, shaker: 2 },
            { voz: true },
            { voz: true },
            { voz: false },
            { voz: true },
            { voz: true, sinCaja: true },
            { voz: false },
            { voz: false, respiro: 4 },
        ];

        function acordeEn(k) {
            const compas = modulo(k, LARGO);
            return SECCIONES[FORMA[Math.floor(compas / 8)]][compas % 8];
        }

        // Todo lo que suena en el compás k, sin instrumentos: una lista que también se puede verificar.
        function notasDe(k) {
            const compas = modulo(k, LARGO);
            const seccion = Math.floor(compas / 8);
            const enSeccion = compas % 8;
            const arreglo = ARREGLO[seccion];
            const nombre = acordeEn(k);
            const acorde = ACORDES[nombre];
            const par = compas % 2 === 0;
            const notas = [];
            const anadir = (voz, midi, pulso, dur, vel = 1) => notas.push({ voz, midi, pulso, dur, vel });

            // Fondo: un acorde sostenido hasta que cambie.
            if (nombre !== acordeEn(k - 1)) {
                const compases = nombre === acordeEn(k + 1) ? 2 : 1;
                acorde.voces.forEach((midi) => anadir("fondo", midi, 0, compases * 4));
            }
            // Teclas: pocos toques suaves, siempre dentro del compás.
            const toques = par ? [[0, 2.4, 0.85], [2.5, 1.2, 0.55]] : [[1.5, 1.6, 0.65]];
            for (const [pulso, dur, vel] of toques) {
                acorde.voces.forEach((midi) => anadir("teclas", midi, pulso, dur, vel));
            }

            const respira = arreglo.respiro !== undefined && enSeccion >= arreglo.respiro;
            // Bajo: la raíz manda, la quinta contesta y un paso lleva al acorde siguiente.
            if (enSeccion >= (arreglo.bajoDesde ?? 0)) {
                anadir("bajo", acorde.raiz, 0, 1.4);
                if (par) {
                    anadir("bajo", acorde.quinta, 2.5, 0.9, 0.8);
                } else {
                    anadir("bajo", acorde.raiz, 2, 0.8, 0.75);
                    if (!respira) anadir("bajo", PASO[ACORDES[acordeEn(k + 1)].raiz], 3.5, 0.45, 0.7);
                }
            }
            // Percusión muy discreta.
            if (!respira) {
                if (enSeccion >= (arreglo.bombo ?? 0)) {
                    (par ? [0, 2.5] : [0, 1.75, 2.5]).forEach((p, i) => anadir("bombo", 0, p, 0, i === 0 ? 1 : 0.7));
                }
                if (!arreglo.sinCaja && enSeccion >= (arreglo.caja ?? 0)) {
                    anadir("caja", 0, 1, 0, 0.85);
                    anadir("caja", 0, 3, 0, 1);
                }
                if (enSeccion >= (arreglo.shaker ?? 0)) {
                    for (let p = 0; p < 4; p += 0.5) anadir("shaker", 0, p, 0, p % 1 ? 1 : 0.6);
                }
            }
            // La voz, en las secciones que la tienen.
            if (arreglo.voz) {
                for (const [c, pulso, midi, dur] of FRASES[FORMA[seccion]]) {
                    if (c === enSeccion) anadir("voz", midi, pulso, dur);
                }
            }
            return notas;
        }

        // Cada instrumento se toca un pelín tarde o temprano respecto al pulso: es lo que lo relaja.
        const ATRASO = { bajo: 0.008, caja: 0.014, shaker: -0.004, teclas: 0.022, voz: 0.03, bombo: 0, fondo: 0 };
        // Espectros: solo armónicos, nada inarmónico que pueda chocar con el acorde.
        const TIMBRES = {
            fondo: [0, 1, 0.22, 0.08, 0.03],
            teclas: [0, 1, 0.3, 0.08, 0.04],
            voz: [0, 1, 0.1, 0.03],
            bajo: [0, 1, 0.5, 0.2, 0.08],
        };
        const NIVELES = { fondo: 0.5, teclas: 0.42, voz: 0.5, bajo: 1, bateria: 0.9, disco: 1 };

        function armar(c, destino) {
            const sala = escenario(c, destino, { brillo: 6500, timbres: TIMBRES, niveles: NIVELES });
            const { canales, cinta, banco } = sala;
            // Fondo: un filtro que se abre y cierra muy despacio.
            const calido = filtro(c, "lowpass", 850);
            canales.fondo.connect(calido).connect(cinta);
            sala.vaiven(0.05, 180, calido.frequency);
            // Teclas: redondas y con un leve vaivén de volumen, como un piano eléctrico.
            canales.teclas.connect(filtro(c, "lowpass", 1500)).connect(cinta);
            sala.vaiven(3.1, 0.05, canales.teclas.gain);
            // Bajo: cálido, sin ataque metálico.
            canales.bajo.connect(filtro(c, "lowpass", 480)).connect(cinta);
            canales.voz.connect(cinta);
            canales.bateria.connect(cinta);
            canales.disco.connect(cinta);
            // La habitación da profundidad; el bajo y el bombo quedan fuera para no emborronar.
            sala.envio(canales.fondo, 0.25);
            sala.envio(canales.teclas, 0.45);
            sala.envio(canales.voz, 0.7);
            // Disco: un soplo constante y casi inaudible.
            enBucle(sala, banco.disco, 0.012, canales.disco);
            // Paneo fijo por voz: la anchura no añade nodos por nota.
            const paneos = [-0.28, 0, 0.28].map((pan) => paneo(c, pan));
            sala.salidas = {
                fondo: paneos.map((p) => { const g = c.createGain(); g.connect(p).connect(canales.fondo); return g; }),
                teclas: paneos.map((p) => { const g = c.createGain(); p.connect(canales.teclas); g.connect(p); return g; }),
            };
            sala.arrancar();
            return sala;
        }

        // Empieza en t el compás k. Si la música entra a mitad, lo ya pasado no suena.
        function componer(sala, k, t) {
            const ahora = sala.c.currentTime;
            const voz = { fondo: 0, teclas: 0 };
            for (const n of notasDe(k)) {
                const fraccion = n.pulso % 1;
                const pulso = Math.floor(n.pulso) + (fraccion === 0.5 ? COLUMPIO : fraccion);
                let inicio = t + pulso * PULSO + ATRASO[n.voz];
                const fin = inicio + n.dur * PULSO;
                if (n.voz === "fondo") {
                    // El fondo es lo único sostenido: si ya empezó, entra ahora y suelta a su hora.
                    // Cambia de acorde con un fundido corto: nada del anterior queda sobre el nuevo.
                    inicio = Math.max(inicio, ahora);
                    if (fin > inicio + 1) tono(sala, "fondo", n.midi, inicio, fin - 0.1, 0.12, 0.45, 0.85, 0.3, sala.salidas.fondo[voz.fondo++ % 3]);
                    continue;
                }
                if (inicio < ahora) continue;
                if (n.voz === "teclas") {
                    const orden = voz.teclas++ % 3; // apenas rasgueado
                    tono(sala, "teclas", n.midi, inicio + orden * 0.011, fin, 0.09 * n.vel, 0.012, 0.25, 0.12, sala.salidas.teclas[orden]);
                } else if (n.voz === "voz") {
                    tono(sala, "voz", n.midi, inicio, fin, 0.12, 0.04, 0.3, 0.2, sala.canales.voz);
                } else if (n.voz === "bajo") {
                    tono(sala, "bajo", n.midi, inicio, fin, 0.3 * n.vel, 0.014, 0.45, 0.07, sala.canales.bajo);
                } else if (n.voz === "bombo") {
                    golpe(sala, "bombo", inicio, 0.3 * n.vel);
                } else if (n.voz === "caja") {
                    golpe(sala, "caja", inicio, 0.085 * n.vel);
                } else {
                    golpe(sala, "shaker", inicio, 0.035 * n.vel);
                }
            }
        }

        return {
            id: "cafe",
            nombre: "Café de medianoche",
            descripcion: "Lo-fi con bajo y percusión discreta",
            COMPAS,
            LARGO,
            vueltas: 1,
            atras: 1,
            ganancia: 0.6,
            armar,
            componer,
            notasDe,
        };
    })();

    /* —— Órbita lenta ——
       Sintetizadores cálidos a 40 pulsos por minuto y sin percusión. Una pila de quintas que
       casi no se mueve: cada acorde cambia una o dos voces y el resto queda ligado, mientras
       el bajo pasa por debajo. Encima, un arpegio de cinco notas sobre ocho corcheas que
       nunca cae igual en el compás y gira por el estéreo; a veces, el motivo en una campana. */
    const orbita = (() => {
        const COMPAS = 6;
        const PULSO = COMPAS / 4;
        const ACORDES = {
            D69: { voces: [57, 64, 71, 78], raiz: 38, giro: [69, 74, 76, 81, 78] },
            ED: { voces: [56, 64, 71, 78], raiz: 38, giro: [71, 76, 80, 78, 74] }, // el sol♯ flota: lidio
            Bm9: { voces: [57, 64, 73, 78], raiz: 35, giro: [69, 73, 78, 81, 76] },
            G: { voces: [57, 62, 71, 78], raiz: 43, giro: [71, 74, 78, 81, 69] },
            Em: { voces: [55, 62, 71, 76], raiz: 40, giro: [71, 74, 79, 76, 83] },
            Asus: { voces: [55, 62, 71, 76], raiz: 33, giro: [69, 74, 76, 79, 71] },
        };
        const SECCIONES = {
            A: ["D69", "D69", "ED", "ED", "Bm9", "Bm9", "G", "G"],
            B: ["Em", "Em", "Asus", "Asus", "Bm9", "Bm9", "G", "G"],
            C: ["D69", "D69", "D69", "D69", "ED", "ED", "D69", "D69"],
        };
        const FORMA = ["A", "A", "B", "A", "C"];
        const LARGO = FORMA.length * 8;
        const BAJO_DESDE = 2;
        const GIRO = [[8, 30, 0.7], [16, 32, 1], [32, 36, 0.6]]; // [desde, hasta, intensidad]
        const MOTIVO = [[0, 1, 81, 1.4], [0, 2.5, 78, 1.4], [1, 0, 76, 3]]; // la – fa♯ – mi
        const CAMPANA_EN = [6, 20, 30]; // siempre sobre sol o si menor, donde no choca
        const FINAL = [[38, 1, 81, 1.4], [38, 2.5, 78, 1.4], [39, 0, 76, 3.5]];

        const acordeEn = (compas) => ACORDES[SECCIONES[FORMA[Math.floor(compas / 8)]][compas % 8]];

        // Sostiene la nota mientras no cambie: lo que se repite queda ligado, sin volver a entrar.
        function ligada(alturaEn, compas) {
            const midi = alturaEn(compas);
            if (midi === null || (compas > 0 && alturaEn(compas - 1) === midi)) return null;
            let compases = 1;
            while (compas + compases < LARGO && alturaEn(compas + compases) === midi) compases++;
            return { midi, dur: compases * 4 };
        }

        function notasDe(k) {
            const compas = modulo(k, LARGO);
            const acorde = acordeEn(compas);
            const notas = [];
            const anadir = (voz, midi, pulso, dur, vel = 1, orden = 0) => notas.push({ voz, midi, pulso, dur, vel, orden });

            acorde.voces.forEach((_, i) => {
                const nota = ligada((c) => acordeEn(c).voces[i], compas);
                if (nota) anadir("almohada", nota.midi, 0, nota.dur, 1, i);
            });
            const sub = ligada((c) => (c < BAJO_DESDE ? null : acordeEn(c).raiz), compas);
            if (sub) anadir("sub", sub.midi, 0, sub.dur);

            const tramo = GIRO.find(([desde, hasta]) => compas >= desde && compas < hasta);
            if (tramo) {
                // Antes de un cambio de acorde el arpegio calla: su cola no pisa el siguiente.
                const cambia = compas + 1 < LARGO && acordeEn(compas + 1) !== acorde;
                for (let i = 0; i < (cambia ? 6 : 8); i++) {
                    const indice = (compas * 8 + i) % 5;
                    anadir("giro", acorde.giro[indice], i / 2, 1, tramo[2] * (indice === 0 ? 1 : 0.72));
                }
            }
            for (const desde of CAMPANA_EN) {
                for (const [c, pulso, midi, dur] of MOTIVO) if (compas === desde + c) anadir("campana", midi, pulso, dur);
            }
            for (const [c, pulso, midi, dur] of FINAL) if (compas === c) anadir("campana", midi, pulso, dur);
            return notas;
        }

        const TIMBRES = {
            almohada: [0, 1, 0.5, 0.28, 0.16, 0.09, 0.05],
            sub: [0, 1, 0.3, 0.08],
            giro: [0, 1, 0.14, 0.05],
            campana: [0, 1, 0.12, 0, 0.1],
        };
        const NIVELES = { almohada: 0.9, sub: 1, giro: 0.8, campana: 0.8, viento: 1 };

        function armar(c, destino) {
            const sala = escenario(c, destino, { brillo: 5200, timbres: TIMBRES, niveles: NIVELES });
            const { canales, cinta } = sala;
            const calido = filtro(c, "lowpass", 760);
            calido.Q.value = 0.6;
            canales.almohada.connect(calido).connect(cinta);
            sala.vaiven(0.025, 280, calido.frequency); // abre y cierra cada 40 segundos
            sala.voces = [-0.45, -0.15, 0.15, 0.45].map((pan) => {
                const p = paneo(c, pan);
                p.connect(canales.almohada);
                return p;
            });
            canales.sub.connect(filtro(c, "lowpass", 320)).connect(cinta);
            const rotor = paneo(c, 0); // el arpegio da la vuelta cada once segundos
            sala.vaiven(0.09, 0.55, rotor.pan);
            canales.giro.connect(rotor).connect(cinta);
            canales.campana.connect(cinta);
            canales.viento.connect(cinta);
            // Un eco que va de lado a lado: es lo que da la sensación de espacio, y gasta poco.
            const izquierda = c.createDelay(2);
            const derecha = c.createDelay(2);
            izquierda.delayTime.value = PULSO * 0.75;
            derecha.delayTime.value = PULSO * 0.75;
            const oscuro = filtro(c, "lowpass", 1700);
            const vuelta = c.createGain();
            vuelta.gain.value = 0.38;
            izquierda.connect(derecha).connect(oscuro).connect(vuelta).connect(izquierda);
            izquierda.connect(paneo(c, -0.6)).connect(cinta);
            derecha.connect(paneo(c, 0.6)).connect(cinta);
            sala.alParar.push(() => vuelta.disconnect());
            const alEco = (canal, cantidad) => {
                const g = c.createGain();
                g.gain.value = cantidad;
                canal.connect(g).connect(izquierda);
            };
            alEco(canales.giro, 0.22);
            alEco(canales.campana, 0.5);
            sala.envio(canales.almohada, 0.3);
            sala.envio(canales.giro, 0.3);
            sala.envio(canales.campana, 0.5);
            // Un viento muy lejano que sube y baja.
            const lejos = filtro(c, "lowpass", 1100);
            sala.vaiven(0.031, 500, lejos.frequency);
            lejos.connect(canales.viento);
            enBucle(sala, soplo(c, 5.3, 2600, 41, 180), 0.02, lejos);
            sala.arrancar();
            return sala;
        }

        // Una voz de la almohada: dos osciladores apenas desafinados, con entrada y salida lentas.
        function almohada(sala, midi, inicio, fin, orden) {
            const { c } = sala;
            const suelta = Math.max(fin - 1.2, inicio + 0.2);
            const g = c.createGain();
            g.gain.setValueAtTime(0, inicio);
            g.gain.linearRampToValueAtTime(0.0625, inicio + Math.min(3, (suelta - inicio) / 2));
            g.gain.setValueAtTime(0.0625, suelta);
            g.gain.linearRampToValueAtTime(0, fin + 0.4);
            g.connect(sala.voces[orden]);
            for (const signo of [-1, 1]) {
                const o = c.createOscillator();
                o.setPeriodicWave(sala.ondas.almohada);
                o.frequency.value = hz(midi);
                o.detune.value = signo * (3 - orden * 0.6);
                o.connect(g);
                vivo(sala, o, inicio, fin + 0.45);
            }
        }

        function componer(sala, k, t) {
            const ahora = sala.c.currentTime;
            for (const n of notasDe(k)) {
                const nace = t + n.pulso * PULSO;
                const fin = nace + n.dur * PULSO;
                if (n.voz === "almohada" || n.voz === "sub") {
                    // Lo sostenido entra ahora si ya había empezado y suelta a su hora.
                    const inicio = Math.max(nace, ahora);
                    if (fin <= inicio + 2) continue;
                    if (n.voz === "almohada") almohada(sala, n.midi, inicio, fin, n.orden);
                    else tono(sala, "sub", n.midi, inicio, fin - 0.6, 0.1, 1.2, 1, 0.9, sala.canales.sub);
                    continue;
                }
                if (nace < ahora) continue;
                if (n.voz === "giro") tono(sala, "giro", n.midi, nace, fin - 0.3, 0.16 * n.vel, 0.03, 0.2, 0.3, sala.canales.giro);
                else tono(sala, "campana", n.midi, nace, fin, 0.15, 0.012, 0.2, 0.5, sala.canales.campana);
            }
        }

        return {
            id: "orbita",
            nombre: "Órbita lenta",
            descripcion: "Sintetizadores cálidos y un eco espacial",
            COMPAS,
            LARGO,
            vueltas: 1,
            atras: 24, // una voz puede quedar ligada mucho tiempo
            ganancia: 0.71,
            armar,
            componer,
            notasDe,
        };
    })();

    /* —— Tarde de lluvia ——
       Un cuarteto de jazz tranquilo en Si menor, a 80 pulsos por minuto y con swing: guitarra
       de cuerda, contrabajo, vibráfono y escobillas, con lluvia detrás. Un tema AABA de 32
       compases; la segunda vuelta deja hablar al bajo, que camina, y guarda silencio el vibráfono. */
    const lluvia = (() => {
        const COMPAS = 3;
        const PULSO = COMPAS / 4;
        const COLUMPIO = 0.64;
        const ACORDES = {
            Bm: { guitarra: [57, 61, 66], raiz: 35, quinta: 42 }, // Bm9
            Em: { guitarra: [55, 59, 62], raiz: 40, quinta: 35 }, // Em7
            A: { guitarra: [55, 61, 66], raiz: 33, quinta: 40 }, // A13
            D: { guitarra: [54, 61, 64], raiz: 38, quinta: 45 }, // Dmaj9
            G: { guitarra: [54, 59, 62], raiz: 43, quinta: 38 }, // Gmaj7
            Cs: { guitarra: [55, 59, 64], raiz: 37, quinta: 43 }, // C#m7(b5)
            Fs: { guitarra: [58, 64, 68], raiz: 42, quinta: 37 }, // F#7(9)
            Fsm: { guitarra: [57, 61, 64], raiz: 42, quinta: 37 }, // F#m7
            Bm7: { guitarra: [57, 62, 66], raiz: 47, quinta: 42 }, // Bm7
        };
        const SECCIONES = {
            I: ["Bm", "Bm", "Em", "Fs"],
            A: ["Bm", "Bm", "Em", "A", "D", "G", "Cs", "Fs"],
            B: ["G", "Fsm", "Em", "A", "D", "Bm7", "Em", "Fs"],
            F: ["Em", "A", "D", "D"],
        };
        // Lo que camina el bajo en la segunda vuelta, nota por pulso.
        const ANDAR = {
            A: [[35, 38, 42, 45], [47, 45, 42, 38], [40, 43, 38, 35], [33, 37, 40, 43], [38, 42, 45, 42], [43, 42, 40, 38], [37, 35, 40, 43], [42, 46, 40, 37]],
            B: [[43, 45, 47, 43], [42, 40, 37, 38], [40, 43, 38, 35], [33, 37, 40, 43], [38, 40, 42, 45], [47, 45, 42, 38], [40, 43, 47, 45], [42, 46, 40, 37]],
        };
        // El tema: [compás de la sección, pulso, nota, duración]. Empieza con el motivo.
        const COMUN = [[0, 1.5, 81, 1], [0, 2.5, 78, 1.4], [1, 0, 76, 2.2],
            [2, 1, 74, 1], [2, 2, 78, 1.5], [3, 0, 76, 2.5],
            [4, 1.5, 81, 1], [4, 2.5, 78, 1.4], [5, 0, 74, 2]];
        const TEMA = {
            A1: [...COMUN, [6, 1, 76, 1], [6, 2, 71, 1.6], [7, 0, 70, 2]],
            A2: [...COMUN, [6, 0, 76, 1.5], [6, 2, 79, 1.2], [7, 0, 78, 2.5]],
            B: [[0, 1, 74, 1], [0, 2, 78, 1], [0, 3, 81, 0.9], [1, 0, 81, 2.5],
                [2, 1, 83, 1.2], [2, 2.5, 79, 1.2], [3, 0, 78, 2], [3, 2.5, 76, 1.2],
                [4, 0, 78, 1.4], [4, 1.5, 76, 1], [4, 2.5, 73, 1.2], [5, 0, 74, 2.5],
                [6, 1, 71, 1], [6, 2, 76, 1.5], [7, 0, 73, 2.5]],
            F: [[2, 1.5, 81, 1], [2, 2.5, 78, 1.4], [3, 0, 76, 3]],
        };
        // [desde, sección, tema del vibráfono, ¿camina el bajo?]
        const FORMA = [
            [0, "I", null, false],
            [4, "A", "A1", false], [12, "A", "A2", false], [20, "B", "B", false], [28, "A", "A1", false],
            [36, "A", null, true], [44, "A", null, true], [52, "B", "B", true], [60, "A", "A2", true],
            [68, "F", "F", false],
        ];
        const LARGO = 72;
        const COMPING = [ // la guitarra: pocas entradas, nunca las mismas dos veces seguidas
            [[0, 1.2, 0.85], [1.5, 0.9, 0.6]],
            [[2.5, 1.1, 0.7]],
            [[1, 1, 0.65], [2.5, 1, 0.7]],
            [[0, 1.4, 0.8]],
        ];

        function lugarDe(k) {
            const compas = modulo(k, LARGO);
            let parte = FORMA[0];
            for (const f of FORMA) if (f[0] <= compas) parte = f;
            const [desde, seccion, tema, camina] = parte;
            return { compas, seccion, tema, camina, enSeccion: compas - desde, acorde: SECCIONES[seccion][compas - desde] };
        }

        function notasDe(k) {
            const { compas, seccion, tema, camina, enSeccion, acorde: nombre } = lugarDe(k);
            const acorde = ACORDES[nombre];
            const notas = [];
            const anadir = (voz, midi, pulso, dur, vel = 1) => notas.push({ voz, midi, pulso, dur, vel });
            const ultimo = compas >= LARGO - 1;
            const final = compas >= LARGO - 2;

            if (ultimo) {
                acorde.guitarra.forEach((midi) => anadir("guitarra", midi, 0, 3.5, 0.7));
            } else {
                for (const [pulso, dur, vel] of COMPING[compas % COMPING.length]) {
                    acorde.guitarra.forEach((midi) => anadir("guitarra", midi, pulso, dur, vel));
                }
            }
            if (compas >= 2 && !ultimo) {
                if (camina) {
                    ANDAR[seccion][enSeccion].forEach((midi, pulso) => anadir("contrabajo", midi, pulso, 0.9, pulso % 2 ? 0.75 : 0.9));
                } else if (compas === LARGO - 2) {
                    anadir("contrabajo", acorde.raiz, 0, 3.6, 0.9);
                } else {
                    anadir("contrabajo", acorde.raiz, 0, 1.8, 0.95);
                    anadir("contrabajo", acorde.quinta, 2, 1.8, 0.8);
                }
            }
            if (compas >= 2 && !final) {
                anadir("barrido", 0, 0, 0, 1);
                anadir("barrido", 0, 2, 0, 0.8);
                anadir("toque", 0, 1, 0, 0.8);
                anadir("toque", 0, 3, 0, 1);
                anadir("bombo", 0, 0, 0, 1);
                if (compas >= 4) for (const p of [1, 1.5, 3, 3.5]) anadir("platillo", 0, p, 0, p % 1 ? 0.6 : 1);
            }
            if (tema) {
                for (const [c, pulso, midi, dur] of TEMA[tema]) if (c === enSeccion) anadir("vibrafono", midi, pulso, dur);
            }
            return notas;
        }

        const TIMBRES = { vibrafono: [0, 1, 0.04, 0, 0.16] };
        const NIVELES = { guitarra: 0.9, contrabajo: 1, vibrafono: 0.8, escobillas: 0.9, lluvia: 1 };
        const ATRASO = { contrabajo: 0.01, guitarra: 0.018, vibrafono: 0.028, barrido: 0, toque: 0.012, platillo: 0.004, bombo: 0 };

        // Una cuerda pulsada (Karplus-Strong): se calcula una vez y luego se reproduce a la altura pedida.
        function cuerda(c, f0, segundos, brillo, perdida, semilla) {
            const r = azar(semilla);
            const n = Math.round(c.sampleRate / f0);
            const linea = new Float32Array(n);
            const a = pasoBajo(c, brillo);
            let previo = 0, media = 0;
            for (let i = 0; i < n; i++) {
                previo += a * (r() * 2 - 1 - previo);
                linea[i] = previo;
                media += previo / n;
            }
            for (let i = 0; i < n; i++) linea[i] -= media;
            return {
                f: c.sampleRate / (n - 0.5), // el promedio con la muestra siguiente acorta medio periodo
                buffer: crearBuffer(c, segundos, 1, (d) => {
                    for (let i = 0; i < d.length; i++) {
                        const j = i % n;
                        d[i] = linea[j];
                        linea[j] = perdida * 0.5 * (linea[j] + linea[(j + 1) % n]);
                    }
                }),
            };
        }

        function armar(c, destino) {
            const sala = escenario(c, destino, { brillo: 7000, timbres: TIMBRES, niveles: NIVELES });
            const { canales, cinta, banco } = sala;
            const r = azar(23);
            const sr = c.sampleRate;
            const a = pasoBajo(c, 3200);
            banco.guitarra = cuerda(c, 220, 1.8, 1300, 0.998, 3);
            banco.contrabajo = cuerda(c, 55, 2.6, 500, 0.999, 5);
            banco.barrido = crearBuffer(c, 0.55, 1, (d) => { // la escobilla que barre el parche
                let ruido = 0;
                for (let i = 0; i < d.length; i++) {
                    const t = i / sr;
                    ruido += a * (r() * 2 - 1 - ruido);
                    d[i] = ruido * (1 - Math.exp(-t / 0.09)) * Math.exp(-t / 0.13);
                }
            });
            banco.toque = crearBuffer(c, 0.14, 1, (d) => {
                let ruido = 0;
                for (let i = 0; i < d.length; i++) {
                    const t = i / sr;
                    ruido += a * (r() * 2 - 1 - ruido);
                    d[i] = ruido * (1 - Math.exp(-t / 0.002)) * Math.exp(-t / 0.03);
                }
            });
            banco.platillo = crearBuffer(c, 0.16, 1, (d) => {
                let previo = 0;
                for (let i = 0; i < d.length; i++) {
                    const t = i / sr;
                    const n = r() * 2 - 1;
                    d[i] = (n - previo) * (1 - Math.exp(-t / 0.002)) * Math.exp(-t / 0.04);
                    previo = n;
                }
            });
            canales.guitarra.connect(filtro(c, "lowpass", 2400)).connect(paneo(c, 0.2)).connect(cinta);
            canales.contrabajo.connect(filtro(c, "lowpass", 620)).connect(cinta);
            canales.vibrafono.connect(paneo(c, -0.22)).connect(cinta);
            sala.vaiven(4.4, 0.08, canales.vibrafono.gain); // el motor del vibráfono, muy lento
            canales.escobillas.connect(cinta);
            canales.lluvia.connect(cinta);
            sala.envio(canales.guitarra, 0.3);
            sala.envio(canales.vibrafono, 0.55);
            sala.envio(canales.escobillas, 0.18);
            // La lluvia: dos soplos de distinto largo, uno a cada lado, para que no se note el bucle.
            const izquierda = paneo(c, -0.5);
            const derecha = paneo(c, 0.5);
            izquierda.connect(canales.lluvia);
            derecha.connect(canales.lluvia);
            enBucle(sala, soplo(c, 6.1, 3800, 11, 520), 0.02, izquierda);
            enBucle(sala, soplo(c, 7.3, 3800, 13, 520), 0.02, derecha);
            sala.arrancar();
            return sala;
        }

        function punteo(sala, nombre, midi, inicio, fin, nivel, destino) {
            const { c } = sala;
            const cuerdaUsada = sala.banco[nombre];
            const g = c.createGain();
            g.gain.setValueAtTime(0, inicio);
            g.gain.linearRampToValueAtTime(nivel, inicio + 0.006);
            g.gain.setValueAtTime(nivel, fin);
            g.gain.linearRampToValueAtTime(0, fin + 0.09);
            g.connect(destino);
            const s = c.createBufferSource();
            s.buffer = cuerdaUsada.buffer;
            s.playbackRate.value = hz(midi) / cuerdaUsada.f;
            s.connect(g);
            vivo(sala, s, inicio, fin + 0.1);
        }

        function componer(sala, k, t) {
            const ahora = sala.c.currentTime;
            let orden = 0;
            for (const n of notasDe(k)) {
                const fraccion = n.pulso % 1;
                const pulso = Math.floor(n.pulso) + (fraccion === 0.5 ? COLUMPIO : fraccion);
                const inicio = t + pulso * PULSO + ATRASO[n.voz];
                if (inicio < ahora) continue;
                const fin = inicio + n.dur * PULSO;
                if (n.voz === "guitarra") {
                    const rasgueo = (orden++ % 3) * 0.012;
                    punteo(sala, "guitarra", n.midi, inicio + rasgueo, fin, 0.3 * n.vel, sala.canales.guitarra);
                } else if (n.voz === "contrabajo") {
                    punteo(sala, "contrabajo", n.midi, inicio, fin, 0.8 * n.vel, sala.canales.contrabajo);
                } else if (n.voz === "vibrafono") {
                    tono(sala, "vibrafono", n.midi, inicio, fin, 0.14, 0.006, 0.3, 0.3, sala.canales.vibrafono);
                } else if (n.voz === "barrido") {
                    golpe(sala, "barrido", inicio, 0.05 * n.vel, sala.canales.escobillas);
                } else if (n.voz === "toque") {
                    golpe(sala, "toque", inicio, 0.06 * n.vel, sala.canales.escobillas);
                } else if (n.voz === "platillo") {
                    golpe(sala, "platillo", inicio, 0.012 * n.vel, sala.canales.escobillas);
                } else {
                    golpe(sala, "bombo", inicio, 0.13 * n.vel, sala.canales.escobillas);
                }
            }
        }

        return {
            id: "lluvia",
            nombre: "Tarde de lluvia",
            descripcion: "Jazz tranquilo con escobillas y lluvia",
            COMPAS,
            LARGO,
            vueltas: 1,
            atras: 0,
            ganancia: 0.9,
            armar,
            componer,
            notasDe,
        };
    })();

    return [rincon, cafe, orbita, lluvia];
})();
