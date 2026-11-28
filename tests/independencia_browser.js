/* El formulario, las preferencias y el procedimiento se prueban sobre la aplicación real. */
(async () => {
    "use strict";

    const ruta = "/vectores/independencia/";
    const casos = [];
    const caso = (nombre, ejecutar) => casos.push([nombre, ejecutar]);
    const q = (w, s) => w.document.querySelector(s);
    const texto = (w, s) => q(w, s)?.textContent.trim();
    const igual = (actual, esperado) => {
        if (actual !== esperado) throw new Error(`Esperado ${esperado}, obtenido ${actual}`);
    };
    const esperar = async (condicion) => {
        const fin = Date.now() + 5000;
        while (!condicion()) {
            if (Date.now() > fin) throw new Error("Espera agotada");
            await new Promise(resolve => setTimeout(resolve, 30));
        }
    };
    const navegar = (frame, accion) => new Promise(resolve => {
        frame.onload = () => resolve(frame.contentWindow);
        accion();
    });
    const abrir = (frame, ejemplo) => navegar(frame, () => { frame.src = ruta + `?ejemplo=${ejemplo}`; });
    const resolver = (frame, w, selector = "[data-calculo]") => navegar(frame, () => q(w, selector).click());
    const celda = (w, vector, fila) => q(w, `#id_celda_v${vector}_${fila}_0`);
    const elegir = (w, selector, valor) => {
        const campo = q(w, selector);
        campo.value = valor;
        campo.dispatchEvent(new w.Event("change", { bubbles: true }));
    };

    caso("Caso de aceptación, planteamiento, operaciones y verificación", async frame => {
        let w = await navegar(frame, () => { frame.src = "/"; });
        w = await navegar(frame, () => q(w, `#algebra-lineal a.tool-link[href="${ruta}"]`).click());
        w = await navegar(frame, () => q(w, 'a[href="?ejemplo=dependiente"]').click());
        w = await resolver(frame, w);
        igual(texto(w, "#results-title"), "Conjunto linealmente dependiente");
        igual(texto(w, "[data-rango]"), "2");
        igual(texto(w, "[data-pivotes]"), "1, 2");
        igual(texto(w, "[data-libres]"), "α₃");
        igual(texto(w, "[data-relacion]"), "-2v₁ - v₂ + v₃ = 0");
        igual(texto(w, "[data-despeje]"), "v₃ = 2v₁ + v₂");
        igual(q(w, "#procedimiento").open, false);
        q(w, "#procedimiento > summary").click();
        igual(q(w, "#procedimiento").open, true);
        igual(w.document.querySelectorAll("#procedimiento .step").length > 0, true);
        igual(texto(w, "[data-verificacion]"), "-2(1, 2, 0) - (0, 1, 3) + (2, 5, 3) = (0, 0, 0)");
    });

    caso("Exacto y Decimal aplicados a la relación y al procedimiento", async frame => {
        let w = await abrir(frame, "independiente");
        for (const [fila, valor] of ["1/9", "1/3", "0"].entries()) celda(w, 2, fila).value = valor;
        w = await resolver(frame, w);
        elegir(w, "#numeric-mode", "exacto");
        igual(texto(w, "[data-relacion]"), "-1/3v₁ + v₂ = 0");
        elegir(w, "#numeric-mode", "decimal");
        igual(texto(w, "[data-relacion]"), "-0.3333v₁ + v₂ ≈ 0");
        igual(texto(w, "[data-verificacion]").includes("≈"), true);
        elegir(w, "#numeric-precision", "2");
        igual(texto(w, "[data-relacion]"), "-0.33v₁ + v₂ ≈ 0");
        elegir(w, "#numeric-mode", "exacto");
        igual(texto(w, "[data-relacion]"), "-1/3v₁ + v₂ = 0");
        elegir(w, "#numeric-precision", "4");
    });

    caso("Redimensionar conserva celdas y respeta las flechas y el teclado contextual", async frame => {
        const w = await abrir(frame, "dependiente");
        q(w, '[data-dimension="cantidad"] [data-paso="-1"]').click();
        igual(celda(w, 3, 2), null);
        q(w, '[data-dimension="cantidad"] [data-paso="1"]').click();
        igual(celda(w, 3, 2).value, "3");
        celda(w, 1, 0).focus();
        igual(q(w, ".math-keyboard").hidden, false);
        const diagonal = q(w, '[data-insercion="/"]');
        igual(Boolean(diagonal), true);
        celda(w, 1, 0).select();
        diagonal.click();
        igual(celda(w, 1, 0).value, "/");
        const campo = celda(w, 2, 0);
        campo.focus();
        campo.setSelectionRange(0, 0);
        campo.dispatchEvent(new w.KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true, cancelable: true }));
        igual(w.document.activeElement, celda(w, 2, 1));
    });

    caso("Varias variables libres y rechazo de un literal inválido", async frame => {
        let w = await abrir(frame, "varias-libres");
        w = await resolver(frame, w);
        igual(texto(w, "[data-libres]"), "α₃, α₄");
        igual(texto(w, "[data-rango]"), "2");
        const campo = celda(w, 3, 0);
        campo.value = "1/0";
        campo.dispatchEvent(new w.Event("input", { bubbles: true }));
        igual(q(w, "#resultado").dataset.resultado, "desactualizado");
        w = await resolver(frame, w);
        igual(q(w, "#resultado"), null);
        igual(texto(w, "#id_celda_v3_0_0_error").includes("no es un número válido"), true);
    });

    caso("Aplicar y resolver sin JavaScript", async frame => {
        frame.sandbox = "allow-same-origin allow-forms";
        let w = await abrir(frame, "dependiente");
        igual(q(w, "[data-aplicar]").hidden, false);
        q(w, "#id_cantidad").value = "2";
        w = await resolver(frame, w, "[data-aplicar]");
        igual(celda(w, 3, 0), null);
        igual(celda(w, 2, 2).value, "3");
        w = await resolver(frame, w);
        igual(texto(w, "#results-title"), "Conjunto linealmente independiente");
    });

    for (const estilo of ["estudio", "minimalista", "chocolab", "belugacalc", "heyalgb"]) {
        for (const tema of ["light", "dark"]) {
            caso(`Resultado y procedimiento a 390 px · ${estilo} · ${tema}`, async frame => {
                frame.style.width = "390px";
                let w = await abrir(frame, "independiente");
                const raiz = () => w.document.documentElement;
                q(w, "#opciones-toggle").click();
                q(w, `[name="estilo"][value="${estilo}"]`).click();
                await esperar(() => raiz().dataset.estilo === estilo);
                if (raiz().dataset.theme !== tema) q(w, "#theme-toggle").click();
                await esperar(() => raiz().dataset.theme === tema);
                w = await resolver(frame, w);
                igual(raiz().dataset.theme, tema);
                igual(raiz().dataset.estilo, estilo);
                igual(texto(w, "#results-title"), "Conjunto linealmente independiente");
                q(w, "#procedimiento > summary").click();
                igual(raiz().scrollWidth <= raiz().clientWidth + 1, true);
            });
        }
    }

    let correctos = 0;
    for (const [nombre, ejecutar] of casos) {
        const frame = document.createElement("iframe");
        frame.title = nombre;
        frame.style.cssText = "width: 1080px; height: 750px; border: 0;";
        document.body.append(frame);
        const fila = document.createElement("li");
        try {
            await ejecutar(frame);
            fila.textContent = `OK · ${nombre}`;
            correctos++;
        } catch (error) {
            fila.textContent = `FALLO · ${nombre}: ${error.message}`;
        } finally {
            frame.remove();
        }
        document.querySelector("#resultados").append(fila);
    }
    document.querySelector("#total").textContent = `${correctos}/${casos.length}`;
})();
