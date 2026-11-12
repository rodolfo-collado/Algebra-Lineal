/* Geometría y lectura de Newton; el controlador compartido gestiona Plotly y el recorrido.
   Notación de clase: n = 0 es el punto inicial x₀; el paso n traza la tangente en xₙ₋₁ y obtiene xₙ. */
"use strict";
const subindiceNewton = k => String(k).replace(/\d/g, d => "₀₁₂₃₄₅₆₇₈₉"[d]);
(window.metodosRaices ||= {}).newton_raphson = {
    extremos: ["x0"],
    indicacion: "Introduce una función para explorar su gráfica y elegir x₀.",
    comprobacion: "Gráfica muestreada. Newton comprueba las evaluaciones de la función y la derivada en cada paso.",
    resumen: r => ({ nombre: "x", x: r.x, fx: r.fx }),
    historial: { metrica: "Error absoluto", tolerancia: "Tolerancia", valor: r => r.error_absoluto,
        criterio: "El criterio se cumple si el error absoluto y el residuo no superan la tolerancia, o si f(x) = 0." },
    vista(p) {
        const a = Math.min(p.xn, p.siguiente), b = Math.max(p.xn, p.siguiente);
        const margen = Math.max((b - a) / 4, Math.abs(a) * 1e-8, 1e-8);
        return [a - margen, b + margen];
    },
    pasoInicial(resultado, { formato }) {
        const x0 = resultado.x0, f0 = resultado.iteraciones[0]?.fxn ?? resultado.fx;
        const { n, r } = formato([x0, f0]);
        return {
            titulo: "Punto inicial (n = 0)",
            aria: `x₀ ${n(x0)}`,
            breve: [`x₀ ${r(x0)}; f(x₀) ${r(f0)}.`, "La primera tangente parte de este punto."],
            valores: [`x₀ ${r(x0)}`, `f(x₀) ${r(f0)}`],
            decision: ["Punto elegido para empezar; todavía no se aplica la fórmula."],
            error: ["Sin aproximación anterior: aún no hay error absoluto."],
            parada: ["Continúa con la primera tangente."],
            puntos: { x: [x0], y: [f0], text: ["(x₀, f(x₀))"], size: [11], symbol: ["circle"] },
        };
    },
    paso(p, { formato }, { ultimo, resultado }) {
        const { n, r } = formato([p.xn, p.siguiente, p.fxn, p.dfxn, p.residuo, p.error_absoluto, resultado.tolerancia]);
        const k = subindiceNewton(p.i - 1), m = subindiceNewton(p.i);
        return {
            titulo: `Iteración ${p.i} de ${resultado.iteraciones.length}: x${m}`,
            aria: `x${k} ${n(p.xn)}, x${m} ${n(p.siguiente)}`,
            breve: [`Tangente en x${k} ${r(p.xn)}, con pendiente f′(x${k}) ${r(p.dfxn)}.`,
                `Corta el eje x en x${m} = x${k} − f(x${k})/f′(x${k}) ${r(p.siguiente)}.`,
                ultimo ? `Se detiene: ${resultado.mensaje}`
                    : `Continúa: error absoluto ${r(p.error_absoluto)} y residuo ${r(p.residuo)}; tolerancia ${n(resultado.tolerancia)}.`],
            valores: [`x${k} ${r(p.xn)}`, `f(x${k}) ${r(p.fxn)}`, `f′(x${k}) ${r(p.dfxn)}`],
            decision: [`x${m} = ${n(p.xn)} − (${n(p.fxn)})/(${n(p.dfxn)}) ${r(p.siguiente)}`,
                "El corte de la tangente con el eje x es la siguiente aproximación."],
            error: [`Error absoluto |x${m} − x${k}| ${r(p.error_absoluto)}`, `Residuo |f(x${m})| ${r(p.residuo)}`,
                `Tolerancia ${n(resultado.tolerancia)}: deben cumplirla ambos.`],
            parada: [ultimo ? resultado.mensaje : "Continúa: todavía no se cumplen las dos condiciones de parada."],
            puntos: { x: [p.xn, p.siguiente], y: [p.fxn, p.fsiguiente],
                text: [`(x${k}, f(x${k}))`, `(x${m}, f(x${m}))`], size: [11, 9], symbol: ["circle", "circle-open"] },
            trazo: { x: [p.xn, p.siguiente, null, p.siguiente, p.siguiente],
                y: [p.fxn, 0, null, 0, p.fsiguiente], size: [0, 13, 0, 0, 0],
                text: ["", `x${m}`, "", "", ""] },
        };
    },
};
const ejemplosNewton = {
    cuadratica: ["x²-2", "1.5"], cubica: ["x³-x-2", "1.5"], ciclo: ["x³-2x+2", "0"],
};
document.querySelectorAll("[data-newton-ejemplo]").forEach(boton => boton.addEventListener("click", () => {
    ["funcion", "x0"].forEach((nombre, i) => {
        const campo = document.getElementById("raices-form").elements.namedItem(nombre);
        campo.value = ejemplosNewton[boton.dataset.newtonEjemplo][i];
        campo.dispatchEvent(new Event("input", { bubbles: true }));
    });
    document.getElementById("grafica-estado").textContent = "Ejemplo cargado. Puedes modificarlo o resolver.";
}));
