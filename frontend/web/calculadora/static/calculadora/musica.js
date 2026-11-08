/* El reproductor de la música ambiental: cuál de las piezas de musica_piezas.js suena y cuándo.
   Solo suena si se pide y cada visita empieza en silencio; se recuerdan la elección y el
   volumen. Calla con la ventana oculta.
   La página anota por dónde iba (solo durante la sesión) para seguir al cambiar de página.
   ponytail: cada página es un documento nuevo, así que al navegar la música baja y vuelve en
   1,5 s; para que no se interrumpa haría falta una aplicación de una sola página. */

window.Musica = (() => {
    "use strict";

    const PIEZAS = window.MusicaPiezas;
    const CONTINUA = "continua";
    const POR_DEFECTO = "cafe";
    const FUNDIDO = 4; // en reproducción continua, una pieza se apaga en estos segundos...
    const ENTRE_PIEZAS = 1.5; // ...y la siguiente espera a este silencio: nunca suenan juntas
    const SESION = "pygebra-musica";
    const MARCA = "pygebra-musica-marca";
    const VOLUMEN = "pygebra-musica-volumen";
    const ELECCION = "pygebra-musica-pieza";

    const porId = (id) => PIEZAS.find((pieza) => pieza.id === id);
    const vecina = (id, paso) => PIEZAS[(PIEZAS.findIndex((pieza) => pieza.id === id) + paso + PIEZAS.length) % PIEZAS.length].id;

    function eleccionGuardada() {
        const guardada = window.preferencias.leer(ELECCION);
        return guardada === CONTINUA || porId(guardada) ? guardada : POR_DEFECTO;
    }

    let eleccion = eleccionGuardada();
    let deseada = false, activa = null, reloj = null, esperando = false, reinicio = null, preparacion = null;
    let marca = { pieza: eleccion === CONTINUA ? PIEZAS[0].id : eleccion, segundos: 0 };
    try {
        deseada = sessionStorage.getItem(SESION) === "on";
        const anotada = JSON.parse(sessionStorage.getItem(MARCA));
        if (anotada && porId(anotada.pieza) && anotada.segundos >= 0 && (eleccion === CONTINUA || eleccion === anotada.pieza)) marca = anotada;
    } catch (_) { /* Solo esta página. */ }

    const avisar = () => document.dispatchEvent(new Event("musica:cambio"));

    function anotar() {
        try {
            sessionStorage.setItem(MARCA, JSON.stringify(marca));
        } catch (_) { /* Vale para esta página. */ }
    }

    const nivel = (pieza) => (Number(window.preferencias.leer(VOLUMEN)) || 40) / 100 * pieza.ganancia;

    function programar() {
        const { pieza, escena, c } = activa;
        const ahora = c.currentTime;
        // Lo que ya pasó (un temporizador retrasado) se salta en vez de sonar todo junto.
        while (activa.t < ahora + 1.5 && activa.k < activa.ultimo) {
            if (activa.t + (pieza.atras + 1) * pieza.COMPAS > ahora) pieza.componer(escena, activa.k, activa.t);
            activa.k++;
            activa.t += pieza.COMPAS;
        }
        if (ahora >= activa.fin + ENTRE_PIEZAS) pasarSola();
    }

    // En continua, la pieza termina al acabar una vuelta completa y se apaga antes de llegar.
    function fijarFinal() {
        const { pieza, fundido, c, origen } = activa;
        const ahora = c.currentTime;
        fundido.gain.cancelScheduledValues(ahora);
        fundido.gain.setValueAtTime(fundido.gain.value, ahora);
        if (eleccion !== CONTINUA) {
            fundido.gain.linearRampToValueAtTime(1, ahora + 1.5);
            activa.ultimo = Infinity;
            activa.fin = Infinity;
            return;
        }
        const vuelta = pieza.LARGO * pieza.vueltas * pieza.COMPAS;
        const fin = origen + Math.max(1, Math.ceil((ahora + 1 - origen) / vuelta)) * vuelta;
        activa.ultimo = Math.round((fin - origen) / pieza.COMPAS);
        // Si queda poco (al volver a mitad de un final), el fundido se acorta pero no desaparece.
        const hasta = Math.max(ahora + 1.5, fin - FUNDIDO);
        const apagada = Math.max(fin, hasta + 2);
        activa.fin = apagada;
        fundido.gain.linearRampToValueAtTime(1, ahora + 1.5);
        fundido.gain.setValueAtTime(1, hasta);
        fundido.gain.linearRampToValueAtTime(0, apagada);
    }

    function encender() {
        if (activa || preparacion !== null || !deseada || document.hidden) return;
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
        // Abrir el dispositivo y sintetizar las muestras no deben ser una sola tarea larga.
        preparacion = { c, reloj: setTimeout(() => {
            preparacion = null;
            if (deseada && !document.hidden) comenzar(c);
        }) };
    }

    function comenzar(c) {
        const pieza = porId(marca.pieza);
        const volumen = c.createGain();
        volumen.gain.value = nivel(pieza);
        volumen.connect(c.destination);
        const fundido = c.createGain();
        fundido.gain.value = 0;
        fundido.connect(volumen);
        const origen = c.currentTime - marca.segundos;
        const k = Math.max(0, Math.floor(marca.segundos / pieza.COMPAS) - pieza.atras);
        activa = { c, pieza, volumen, fundido, origen, k, t: origen + k * pieza.COMPAS, ultimo: Infinity, fin: Infinity, escena: pieza.armar(c, fundido) };
        fijarFinal();
        programar();
        reloj = setInterval(programar, 1000);
    }

    // Baja el volumen sin parar la música de golpe; el contexto se duerme si ya no hace falta.
    function apagar() {
        clearTimeout(reinicio);
        if (preparacion) {
            clearTimeout(preparacion.reloj);
            if (!deseada || document.hidden) preparacion.c.suspend();
            preparacion = null;
        }
        if (!activa) return;
        const { c, fundido, volumen, escena, origen, fin } = activa;
        // En el silencio entre dos piezas ya toca la siguiente.
        marca = c.currentTime >= fin ? { pieza: vecina(marca.pieza, 1), segundos: 0 } : { pieza: marca.pieza, segundos: Math.max(0, c.currentTime - origen) };
        anotar();
        activa = null;
        clearInterval(reloj);
        fundido.gain.cancelScheduledValues(c.currentTime);
        fundido.gain.setTargetAtTime(0, c.currentTime, 0.18);
        setTimeout(() => {
            escena.parar();
            volumen.disconnect();
            if (!activa && (!deseada || document.hidden)) c.suspend(); // en silencio no gasta nada
        }, 700);
    }

    // Otra pieza desde el principio, sin pisar la que suena: primero baja y luego entra.
    function ponerPieza(id) {
        const sonaba = Boolean(activa);
        apagar();
        marca = { pieza: id, segundos: 0 };
        anotar();
        if (sonaba || reinicio !== null) {
            clearTimeout(reinicio);
            reinicio = setTimeout(() => { reinicio = null; encender(); }, 750);
        } else {
            encender();
        }
        avisar();
    }

    // Se acabó la pieza y ya está en silencio: entra la siguiente, sin solaparse.
    function pasarSola() {
        const { escena, volumen } = activa;
        activa = null;
        clearInterval(reloj);
        escena.parar();
        volumen.disconnect();
        marca = { pieza: vecina(marca.pieza, 1), segundos: 0 };
        anotar();
        encender();
        avisar();
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

    function elegir(id) {
        if (id !== CONTINUA && !porId(id)) return;
        eleccion = id;
        window.preferencias.guardar(ELECCION, id);
        if (id === CONTINUA || id === marca.pieza) {
            // La pieza que suena sigue sonando; solo cambia lo que pasará al terminar.
            if (activa) fijarFinal();
            avisar();
        } else {
            ponerPieza(id);
        }
    }

    // Anterior o siguiente. En continua sigue en continua; si no, cambia lo elegido.
    function saltar(paso) {
        const id = vecina(marca.pieza, paso);
        if (eleccion !== CONTINUA) {
            eleccion = id;
            window.preferencias.guardar(ELECCION, id);
        }
        ponerPieza(id);
    }

    document.addEventListener("visibilitychange", () => (document.hidden ? apagar() : encender()));
    addEventListener("pagehide", apagar);
    addEventListener("pageshow", (event) => { if (event.persisted) encender(); });
    setTimeout(encender); // aparte: un fallo de audio no debe dejar sin Opciones a la página

    return {
        disponible: Boolean(window.AudioContext || window.webkitAudioContext),
        PIEZAS,
        CONTINUA,
        pedida: () => deseada,
        eleccion: () => eleccion,
        actual: () => porId(marca.pieza),
        alternar,
        elegir,
        saltar,
        volumen(valor) {
            if (activa) activa.volumen.gain.setTargetAtTime(valor / 100 * activa.pieza.ganancia, activa.c.currentTime, 0.1);
        },
    };
})();
