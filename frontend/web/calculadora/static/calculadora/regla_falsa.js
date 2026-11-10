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
        const e = formato([p.error_absoluto ?? 0, tolerancia], 2);
        const error = [p.error_absoluto === null ? "Ea no disponible: primera aproximación." : `Ea ${e.r(p.error_absoluto)}`,
            `Tolerancia: ${e.n(tolerancia)}`];
        const parada = [];
        if (p.fxr === 0) parada.push("Se detiene: f(xr) = 0 en aritmética de máquina.");
        else {
            if (p.error_absoluto === null) parada.push("Aún no hay dos aproximaciones para comparar.");
            else if (!p.cumple_tolerancia) parada.push("Ea supera la tolerancia.");
            else {
                const prueba = formato([p.xr, p.prueba]).r(p.prueba);
                parada.push("Ea cumple la tolerancia.", `Punto de prueba ${prueba}: a no más de una tolerancia de xr.`);
                if (p.confirmada) parada.push(p.f_prueba === 0 ? "f(prueba) = 0." : "f(prueba) y f(xr) tienen signos opuestos.",
                    "Raíz confirmada entre xr y el punto de prueba.");
                else parada.push("f(prueba) y f(xr) tienen el mismo signo.",
                    "Sin confirmación de una raíz cercana.", "El mismo signo tampoco descarta raíces intermedias.");
            }
            parada.push(p.confirmada ? "Se detiene: convergencia verificada."
                : ultimo && !resultado.convergio
                    ? resultado.estado === "maquina" ? "Se detiene sin convergencia: límite de los números de máquina."
                        : "Se detiene sin convergencia: máximo de iteraciones."
                    : "Continúa.");
        }
        return {
            aria: `xr ${formato([p.xr], 12).r(p.xr)}`,
            valores: [`xr ${r(p.xr)}`, "Corte de la secante con el eje x."],
            signos: p.fxr === 0 ? ["f(xr) = 0 (cero)."]
                : [`f(${p.sustituido}) y f(xr) tienen el mismo signo (${signo(p.fxr)}).`,
                    `f(a) ${r(p.fa)} · f(b) ${r(p.fb)} · f(xr) ${r(p.fxr)}`],
            decision: p.fxr === 0 ? ["No hace falta sustituir ningún extremo."]
                : [`xr sustituye al extremo ${p.sustituido}.`, `${fijo} permanece en ${n(p[fijo])}.`],
            intervalo: [`Nuevo intervalo: [${n(p.nuevo_a)}; ${n(p.nuevo_b)}].`,
                ...(p.veces_fijo >= 3 ? [`${p.extremo_fijo} lleva ${p.veces_fijo} iteraciones sin moverse.`] : [])],
            error,
            parada,
            puntos: { x: [p.a, p.xr, p.b], y: [p.fa, p.fxr, p.fb], text: ["(a, f(a))", "(xr, f(xr))", "(b, f(b))"],
                size: [9, 9, 9], symbol: ["circle", "circle", "circle"] },
            // Secante de (a, f(a)) a (b, f(b)), su corte xr con el eje x y la subida hasta f(xr).
            trazo: { x: [p.a, p.b, null, p.xr, p.xr], y: [p.fa, p.fb, null, 0, p.fxr], size: [0, 0, 0, 13, 0],
                text: ["", "", "", "xr", ""], posicion: p.fxr < 0 ? "top center" : "bottom center" },
        };
    },
};
