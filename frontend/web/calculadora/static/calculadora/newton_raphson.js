/* Geometría y lectura de Newton; el controlador compartido gestiona Plotly y el recorrido. */
"use strict";
(window.metodosRaices ||= {}).newton_raphson = {
    extremos: ["x0"],
    indicacion: "Introduce una función para explorar su gráfica y elegir x₀.",
    comprobacion: "Gráfica muestreada. Newton comprueba las evaluaciones de la función y la derivada en cada paso.",
    resumen: r => ({ nombre: "x", x: r.x, fx: r.fx }),
    vista(p) {
        const a = Math.min(p.xn, p.siguiente), b = Math.max(p.xn, p.siguiente);
        const margen = Math.max((b - a) / 4, Math.abs(a) * 1e-8, 1e-8);
        return [a - margen, b + margen];
    },
    paso(p, { formato }, { ultimo, resultado }) {
        const { n, r } = formato([p.xn, p.siguiente, p.fxn, p.dfxn, p.residuo, p.error_absoluto, resultado.tolerancia]);
        return {
            aria: `x actual ${n(p.xn)}, siguiente ${n(p.siguiente)}`,
            breve: [`Tangente en x ${r(p.xn)}, con pendiente f′ ${r(p.dfxn)}.`,
                `Corta el eje x en x siguiente ${r(p.siguiente)}; allí |f| ${r(p.residuo)}.`,
                ultimo ? `Se detiene: ${resultado.mensaje}` : `Continúa: cambio ${r(p.error_absoluto)}; aún no se cumplen ambas condiciones.`],
            valores: [`x actual ${r(p.xn)}`, `f(x actual) ${r(p.fxn)}; f′(x actual) ${r(p.dfxn)}`],
            decision: [`x siguiente = ${n(p.xn)} − (${n(p.fxn)})/(${n(p.dfxn)}) ≈ ${n(p.siguiente)}`,
                "El corte de la tangente con el eje x propone el siguiente punto."],
            error: [`Residuo siguiente |f(x siguiente)| ≈ ${n(p.residuo)}`,
                `Cambio |x siguiente − x actual| ≈ ${n(p.error_absoluto)}`,
                `Tolerancia: ${n(resultado.tolerancia)}. Deben cumplirla ambos.`],
            parada: [ultimo ? resultado.mensaje : "Continúa: todavía no se cumplen las dos condiciones de parada."],
            puntos: { x: [p.xn, p.siguiente], y: [p.fxn, p.fsiguiente],
                text: ["(x actual, f(x actual))", "(x siguiente, f(x siguiente))"], size: [11, 9], symbol: ["circle", "circle-open"] },
            trazo: { x: [p.xn, p.siguiente, null, p.siguiente, p.siguiente],
                y: [p.fxn, 0, null, 0, p.fsiguiente], size: [0, 13, 0, 0, 0],
                text: ["", "x siguiente", "", "", ""] },
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
