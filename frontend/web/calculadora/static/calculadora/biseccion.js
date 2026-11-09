/* Lectura de una iteración de bisección: punto medio y mitad descartada. */
"use strict";
(window.metodosRaices ||= {}).biseccion = {
    distintas: "Intervalos finales distintos",
    // c queda dentro del intervalo final, cuya longitud acota su distancia a la raíz.
    resumen: r => ({ nombre: "c", x: r.c, fx: r.fc, certeza: [r.a, r.b] }),
    paso(p, { formato, signo }) {
        // Mostrar los puntos distintos como distintos, incluso con tolerancias muy pequeñas.
        const { n, r } = formato([p.a, p.c, p.b, p.nuevo_a, p.nuevo_b]);
        const cambiaA = (p.fa < 0) === (p.fc < 0);
        const decision = cambiaA
            ? `f(a) y f(c) tienen el mismo signo (${signo(p.fa)}). Descartamos la mitad izquierda [a,c]: c pasa a ser el nuevo a ${r(p.c)}; b permanece en ${n(p.b)}. Conservamos la mitad derecha [c,b].`
            : `f(c) y f(b) tienen el mismo signo (${signo(p.fb)}). Descartamos la mitad derecha [c,b]: c pasa a ser el nuevo b ${r(p.c)}; a permanece en ${n(p.a)}. Conservamos la mitad izquierda [a,c].`;
        return {
            aria: `c ${formato([p.c], 12).r(p.c)}`,
            valores: `Antes de dividir: a (izquierdo) ${r(p.a)} · c (punto medio) ${r(p.c)} · b (derecho) ${r(p.b)}.`,
            signos: `f(a) ${r(p.fa)} (${signo(p.fa)}) · f(c) ${r(p.fc)} (${signo(p.fc)}) · f(b) ${r(p.fb)} (${signo(p.fb)}).`,
            decision: p.fc === 0
                ? `f(c) = 0 en aritmética de máquina: encontramos una raíz calculada. Ambos extremos pasan a c; no descartamos otra mitad ni seguimos dividiendo.`
                : decision,
            intervalo: `Nuevo intervalo: [${n(p.nuevo_a)}; ${n(p.nuevo_b)}], longitud ${n(p.longitud)}.`,
            puntos: { x: [p.a, p.c, p.b], y: [p.fa, p.fc, p.fb], text: ["a", "c (punto medio)", "b"],
                size: [9, 13, 9], symbol: ["circle", "diamond", "circle"] },
        };
    },
};
