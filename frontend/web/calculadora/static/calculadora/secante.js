/* Geometría y lectura del método de la secante; el controlador compartido gestiona Plotly y el recorrido.
   La iteración n une Pₙ₋₁ = (xₙ₋₁, f(xₙ₋₁)) y Pₙ = (xₙ, f(xₙ)); su corte con el eje x es xₙ₊₁.
   Como en la diapositiva 19: los dos puntos, la recta secante y su corte; nunca un intervalo. */
"use strict";
(() => {
    const { subindice, menos, operando, relacion, fraccion, bloque, valores, comprobacion, linea, nueva } = window.metodosAbiertos;
    // Recta por Pₙ₋₁ y Pₙ hasta su corte con el eje x, ordenada en x y prolongada un poco por cada lado.
    function recta(p) {
        const pendiente = (p.factual - p.fanterior) / (p.actual - p.anterior);
        const y = x => p.factual + pendiente * (x - p.actual);
        const puntos = [[p.anterior, p.fanterior, 0], [p.actual, p.factual, 0], [p.siguiente, 0, 13]].sort((a, b) => a[0] - b[0]);
        const margen = (puntos[2][0] - puntos[0][0]) * .08;
        const todos = [[puntos[0][0] - margen], ...puntos, [puntos[2][0] + margen]].map(([x, alto, tamano = 0]) => [x, alto ?? y(x), tamano]);
        return { x: todos.map(t => t[0]), y: todos.map(t => t[1]), size: todos.map(t => t[2]) };
    }
    (window.metodosRaices ||= {}).secante = {
        extremos: ["x0", "x1"],
        indicacion: "Introduce una función para explorar su gráfica y elegir x₀ y x₁.",
        comprobacion: "Gráfica muestreada. La secante no exige cambio de signo: x₀ y x₁ solo deben ser distintos.",
        resumen: r => ({ nombre: "x", x: r.x, fx: r.fx }),
        historial: { metrica: "Error absoluto", tolerancia: "Tolerancia", valor: r => r.error_absoluto,
            criterio: "El criterio se cumple si el error absoluto y el residuo no superan la tolerancia, o si f(x) = 0." },
        vista(p) {
            const xs = [p.anterior, p.actual, p.siguiente];
            const a = Math.min(...xs), b = Math.max(...xs);
            const margen = Math.max((b - a) / 4, Math.abs(a) * 1e-8, 1e-8);
            return [a - margen, b + margen];
        },
        paso(p, { formato }, { ultimo, resultado }) {
            const tolerancia = resultado.tolerancia;
            const lectura = formato([p.anterior, p.actual, p.siguiente, p.fanterior, p.factual,
                p.numerador ?? 0, p.denominador, p.residuo, p.error_absoluto, tolerancia]);
            const { n, r } = lectura, v = x => menos(n(x));
            const k0 = subindice(p.i - 1), k1 = subindice(p.i), m = subindice(p.i + 1);
            // «=» solo si todas las cifras sustituidas son exactamente las almacenadas.
            const exacta = (...xs) => xs.every(x => relacion(n, x) === "=") ? "=" : "≈";
            const operaciones = p.numerador === null ? [] : [linea(
                `x${m} ${exacta(p.actual, p.numerador, p.denominador)} ${v(p.actual)} − `, ...fraccion(v(p.numerador), v(p.denominador)))];
            const secante = recta(p);
            return {
                titulo: `Iteración ${p.i} de ${resultado.iteraciones.length}: x${m}`,
                aria: `x${k0} ${n(p.anterior)}, x${k1} ${n(p.actual)}, x${m} ${n(p.siguiente)}`,
                breve: [
                    bloque(`Puntos P${k0} y P${k1}`, valores([[`x${k0}`, p.anterior], [`f(x${k0})`, p.fanterior],
                        [`x${k1}`, p.actual], [`f(x${k1})`, p.factual]], lectura)),
                    bloque("Sustitución",
                        linea(`x${m} = x${k1} − `,
                            ...fraccion(`f(x${k1}) · (x${k1} − x${k0})`, `f(x${k1}) − f(x${k0})`)),
                        linea(`x${m} ${exacta(p.actual, p.anterior, p.factual, p.fanterior)} ${v(p.actual)} − `,
                            ...fraccion(`${operando(v(p.factual))} · (${v(p.actual)} − ${operando(v(p.anterior))})`,
                                `${v(p.factual)} − ${operando(v(p.fanterior))}`))),
                    bloque("Operaciones", ...operaciones, nueva(`x${m}`, p.siguiente, lectura)),
                    bloque(`Comprobación con tolerancia ${n(tolerancia)}`, comprobacion(
                        [[`Error absoluto |x${m} − x${k1}|`, p.error_absoluto], [`Residuo |f(x${m})|`, p.residuo]], tolerancia, lectura)),
                    ultimo ? `Se detiene: ${resultado.mensaje}`
                        : `Continúa: se desplazan los puntos (xₙ₋₁ ← x${k1}, xₙ ← x${m}); la siguiente secante une P${k1} y P${m}.`,
                ],
                valores: [`x${k0} ${r(p.anterior)}`, `f(x${k0}) ${r(p.fanterior)}`, `x${k1} ${r(p.actual)}`, `f(x${k1}) ${r(p.factual)}`],
                decision: [
                    `x${m} = ${v(p.actual)} − [${operando(v(p.factual))} · (${v(p.actual)} − ${operando(v(p.anterior))})] / [${v(p.factual)} − ${operando(v(p.fanterior))}] ${r(p.siguiente)}`,
                    ...(p.numerador === null ? [] : [`Numerador ${r(p.numerador)}; denominador f(x${k1}) − f(x${k0}) ${r(p.denominador)}.`]),
                    `El corte de la recta secante que une P${k0} y P${k1} con el eje x es la siguiente aproximación.`],
                error: [`Error absoluto |x${m} − x${k1}| ${r(p.error_absoluto)}`, `Residuo |f(x${m})| ${r(p.residuo)}`,
                    `Tolerancia ${n(tolerancia)}: deben cumplirla ambos.`],
                parada: [ultimo ? resultado.mensaje : `Continúa con x${k1} y x${m}: todavía no se cumplen las dos condiciones de parada.`],
                puntos: { x: [p.anterior, p.actual, p.siguiente], y: [p.fanterior, p.factual, p.fsiguiente],
                    text: [`P${k0} = (x${k0}, f(x${k0}))`, `P${k1} = (x${k1}, f(x${k1}))`, `(x${m}, f(x${m}))`],
                    size: [11, 11, 9], symbol: ["circle", "circle", "circle-open"] },
                // Traza auxiliar: recta secante, etiquetas P y corte xₙ₊₁ con su altura f(xₙ₊₁).
                trazo: { x: [...secante.x, null, p.siguiente, p.siguiente], y: [...secante.y, null, 0, p.fsiguiente],
                    size: [...secante.size, 0, 0, 0], text: secante.x.map(() => "").concat(["", "", ""]) },
                rotulos: [{ x: p.anterior, y: p.fanterior, text: `P${k0}` }, { x: p.actual, y: p.factual, text: `P${k1}` },
                    { x: p.siguiente, y: 0, text: `x${m}` }],
            };
        },
    };
})();
