/* Lectura de una iteración de regla falsa: secante, corte con el eje x y extremo sustituido. */
"use strict";
(window.metodosRaices ||= {}).regla_falsa = {
    distintas: "Raíces confirmadas en tramos distintos",
    // Solo un cambio de signo confirmado deja un tramo que contiene la raíz.
    resumen: r => ({ nombre: "xr", x: r.xr, fx: r.fxr,
        certeza: r.cota === null ? [r.xr, r.xr] : [Math.min(r.xr, r.prueba), Math.max(r.xr, r.prueba)] }),
    paso(p, { formato, signo }, { ultimo, resultado }) {
        const { n, r } = formato([p.a, p.b, p.xr, p.nuevo_a, p.nuevo_b]);
        const tolerancia = resultado.tolerancia;
        const fijo = p.sustituido === "a" ? "b" : "a";
        let parada;
        if (p.fxr === 0) parada = "El residuo f(xr) es cero: nos detenemos.";
        else if (p.error_absoluto === null) parada = "Ea no disponible: es la primera aproximación y aún no hay una anterior con la cual compararla. Continuamos.";
        else {
            // Dos cifras bastan para leer Ea, salvo que se confunda con la tolerancia.
            const e = formato([p.error_absoluto, tolerancia], 2);
            const cambio = `La aproximación cambió ${e.n(p.error_absoluto)} unidades respecto a la anterior`;
            if (!p.cumple_tolerancia) parada = `${cambio}: Ea supera la tolerancia (${e.n(tolerancia)}). Continuamos.`;
            else {
                const cumple = `${cambio}, ${p.error_absoluto < tolerancia ? "por debajo de" : "igual a"} la tolerancia establecida (${e.n(tolerancia)}). Eso solo indica que xr casi no se movió`;
                const prueba = formato([p.xr, p.prueba]).n(p.prueba);
                parada = p.confirmada
                    ? `${cumple}; para declarar convergencia comprobamos además el punto ${prueba}, a no más de una tolerancia de xr: allí f ${p.f_prueba === 0 ? "vale cero" : `es ${signo(p.f_prueba)}, de signo contrario a f(xr)`}. Hay una raíz entre ambos, a no más de ${e.n(tolerancia)} de xr. Nos detenemos.`
                    : `${cumple}; en ${prueba}, a no más de una tolerancia de xr, f sigue siendo ${signo(p.f_prueba)}, igual que f(xr). No se confirmó una raíz cercana: ese mismo signo tampoco descarta raíces entre ambos puntos. Continuamos.`;
            }
        }
        const cierre = { maquina: "La siguiente secante ya no da un punto nuevo con los números de máquina: el cálculo termina sin convergencia." }[resultado.estado]
            || "Se alcanzó el máximo de iteraciones: el cálculo termina sin convergencia.";
        if (ultimo && !resultado.convergio) parada = parada.replace(/Continuamos\.$/, cierre);
        return {
            aria: `xr ${formato([p.xr], 12).r(p.xr)}`,
            valores: `Antes de sustituir: a ${r(p.a)} · b ${r(p.b)}. La recta secante que une (a, f(a)) y (b, f(b)) corta al eje x en xr ${r(p.xr)}.`,
            signos: `f(a) ${r(p.fa)} (${signo(p.fa)}) · f(xr) ${r(p.fxr)} (${signo(p.fxr)}) · f(b) ${r(p.fb)} (${signo(p.fb)}).`,
            decision: p.fxr === 0
                ? "f(xr) = 0 en aritmética de máquina: xr es una raíz calculada. No hace falta sustituir ningún extremo."
                : `Como f(${p.sustituido}) y f(xr) tienen el mismo signo (${signo(p.fxr)}), xr sustituye al extremo ${p.sustituido}: el nuevo ${p.sustituido} es ${n(p.xr)} y ${fijo} permanece en ${n(p[fijo])}. Así el intervalo conserva el cambio de signo.`,
            intervalo: `Intervalo anterior: [${n(p.a)}; ${n(p.b)}]. Nuevo intervalo: [${n(p.nuevo_a)}; ${n(p.nuevo_b)}].`
                + (p.veces_fijo >= 3 ? ` El extremo ${p.extremo_fijo} lleva ${p.veces_fijo} iteraciones sin moverse: el método avanza por un solo lado.` : ""),
            parada,
            puntos: { x: [p.a, p.xr, p.b], y: [p.fa, p.fxr, p.fb], text: ["(a, f(a))", "(xr, f(xr))", "(b, f(b))"],
                size: [9, 9, 9], symbol: ["circle", "circle", "circle"] },
            // Secante de (a, f(a)) a (b, f(b)), su corte xr con el eje x y la subida hasta f(xr).
            trazo: { x: [p.a, p.b, null, p.xr, p.xr], y: [p.fa, p.fb, null, 0, p.fxr], size: [0, 0, 0, 13, 0],
                text: ["", "", "", "xr", ""], posicion: p.fxr < 0 ? "top center" : "bottom center" },
        };
    },
};
