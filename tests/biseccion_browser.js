/* Formularios reales, Plotly local y muestras del backend de producción. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const ok = (valor, mensaje) => { if (!valor) throw new Error(mensaje); };
    const esperar = async condicion => {
        const limite = Date.now() + 15000;
        while (!condicion()) {
            if (Date.now() > limite) throw new Error("Espera agotada");
            await new Promise(r => setTimeout(r, 40));
        }
    };
    const grafica = w => q(w, "#biseccion-grafica");
    const lista = w => JSON.parse(q(w, "#datos-biseccion").textContent).resultado.iteraciones;
    const valor = (w, nombre, texto) => {
        const campo = q(w, `[name="${nombre}"]`);
        campo.value = texto; campo.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const ejemplo = w => {
        valor(w, "funcion", "x^4 - 5x^3 + 0.5x^2 - 11x + 10");
        valor(w, "a", "0.55"); valor(w, "b", "1.1");
    };
    const post = frame => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout POST")), 15000);
        frame.onload = () => { clearTimeout(timer); resolve(frame.contentWindow); };
        q(frame.contentWindow, "[data-calculo]").click();
    });
    const listaGrafica = w => grafica(w)?.data?.[0]?.x?.length === 801 &&
        !q(w, "#grafica-estado").textContent.includes("Actualizando");
    const casos = [
        ["Inicio vacío y vista previa solo con datos completos", async w => {
            let peticiones = 0;
            const original = w.fetch; w.fetch = (...args) => { peticiones++; return original(...args); };
            for (const n of ["funcion", "a", "b"]) ok(q(w, `[name="${n}"]`).value === "", "Campo vacío");
            ok(!grafica(w).data && grafica(w).hidden, "Sin gráfica inventada");
            valor(w, "funcion", "x^2-2"); valor(w, "a", "1");
            await new Promise(r => setTimeout(r, 450));
            ok(peticiones === 0 && grafica(w).hidden, "Sin pedir muestras con campos incompletos");
            valor(w, "b", "2"); await esperar(() => listaGrafica(w));
            ok(!q(w, "#resultado"), "Vista previa sin resolver");
            valor(w, "funcion", "");
            ok(grafica(w).hidden && q(w, "#grafica-estado").textContent.includes("Introduce"), "Volver al estado vacío");
        }],
        ["Teclado contextual de funciones reales conserva foco y cursor", async w => {
            const f = q(w, '[name="funcion"]'); f.focus();
            await esperar(() => q(w, ".math-keyboard").hasAttribute("data-abierto"));
            q(w, '[data-insercion="x^2"]').click();
            ok(f.value === "x^2" && w.document.activeElement === f, "Cuadrado y foco");
            valor(w, "funcion", "x"); f.setSelectionRange(1, 1);
            q(w, '[data-insercion="^()"]')?.click();
            ok(f.value === "x^()" && f.selectionStart === 3, "Exponente general con cursor dentro");
            valor(w, "funcion", ""); f.setSelectionRange(0, 0);
            q(w, '[data-insercion="sqrt()"]')?.click();
            ok(f.value === "sqrt()" && f.selectionStart === 5, "Raíz y cursor");
            q(w, '[name="a"]').focus();
            ok(!q(w, ".math-keyboard").hasAttribute("data-abierto"), "No aparece en extremos numéricos");
        }],
        ["Una respuesta antigua no sobrescribe el estado vacío", async w => {
            ejemplo(w); await esperar(() => listaGrafica(w));
            const original = w.Plotly.restyle;
            let liberar;
            w.Plotly.restyle = (...args) => new Promise(resolve => {
                liberar = () => { w.Plotly.restyle = original; return original(...args).then(resolve); };
            });
            valor(w, "funcion", "x^2-3");
            await esperar(() => !!liberar);
            valor(w, "funcion", "");
            await liberar();
            await new Promise(r => w.requestAnimationFrame(r));
            ok(grafica(w).hidden && q(w, "#grafica-estado").textContent.includes("Introduce"), "Ignora respuesta obsoleta");
        }],
        ["Precisión pequeña mantiene distinguibles a, c y b", async (w, frame) => {
            valor(w, "funcion", "x^2-2"); valor(w, "a", "1"); valor(w, "b", "2");
            valor(w, "precision", "1e-10");
            w = await post(frame); await esperar(() => listaGrafica(w));
            const numeros = [...q(w, "#paso-valores").textContent.matchAll(/= ([\d,.-]+)/g)].map(m => m[1]);
            ok(numeros.length === 3 && new Set(numeros).size === 3, "No redondea los tres puntos al mismo número");
        }],
        ["Ejemplo del profesor: 13 filas y raíz verificada", async (w, frame) => {
            ejemplo(w);
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(lista(w).length === 13, "13 iteraciones");
            ok(lista(w)[12].c === .763970947265625, "Raíz del ejemplo");
            ok(grafica(w).layout.shapes.length === 3, "Dos extremos y una sola franja");
            ok(grafica(w).layout.shapes[2].x0 === lista(w)[12].a, "Franja de la última iteración");
            ok(!q(w, "#procedimiento-biseccion").open, "Detalle cerrado");
            ok(w.document.activeElement === q(w, "#resultado"), "Foco en el resultado");
        }],
        ["Cursor, foco y deslizador reutilizan pasos sin peticiones", async (w, frame) => {
            ejemplo(w);
            w = await post(frame); await esperar(() => listaGrafica(w));
            let peticiones = 0;
            const original = w.fetch; w.fetch = (...args) => { peticiones++; return original(...args); };
            q(w, "#procedimiento-biseccion").open = true;
            const fila = q(w, '[data-iteracion="2"]');
            fila.dispatchEvent(new w.PointerEvent("pointerenter"));
            await esperar(() => grafica(w).data[1].x[1] === lista(w)[1].c);
            ok(q(w, "#iteracion-biseccion").value === "2", "Cursor sincroniza el deslizador");
            ok(q(w, "#paso-decision").textContent.includes("derecha [c,b]"), "Segunda iteración conserva derecha");
            ok(q(w, "#paso-valores").textContent.includes("a (izquierdo)"), "Extremos identificados");
            q(w, '[data-iteracion="4"]').focus();
            await esperar(() => grafica(w).data[1].x[1] === lista(w)[3].c);
            ok(q(w, "#paso-decision").textContent.includes("izquierda [a,c]"), "Cuarta iteración conserva izquierda");
            const slider = q(w, "#iteracion-biseccion");
            slider.value = "7"; slider.dispatchEvent(new w.Event("input", { bubbles: true }));
            await esperar(() => grafica(w).data[1].x[1] === lista(w)[6].c);
            ok(grafica(w).layout.shapes[2].x0 === lista(w)[6].a, "Intervalo seleccionado");
            ok(peticiones === 0, "Sin nuevas peticiones al recorrer pasos");
            ok(grafica(w).layout.shapes.length === 3, "No se acumulan formas");
        }],
        ["Explorar y ajustar extremos conserva el resultado anterior", async (w, frame) => {
            ejemplo(w);
            w = await post(frame); await esperar(() => listaGrafica(w));
            await w.Plotly.relayout(grafica(w), { "xaxis.range": [-1, 6] });
            await esperar(() => grafica(w).data[0].x[0] === -1 && grafica(w).data[0].x[800] === 6);
            await w.Plotly.relayout(grafica(w), { "shapes[0].x0": .6, "shapes[0].x1": .6 });
            ok(Number(q(w, '[name="a"]').value) === .6, "Extremo conectado al formulario");
            ok(q(w, "#resultado").dataset.resultado === "desactualizado", "Aviso de resultado anterior");
            ok(lista(w).length === 13, "No vuelve a ejecutar la bisección");
        }],
        ["Dos intervalos de la segunda raíz: comparación de 13 y 10 pasos", async (w, frame) => {
            w.sessionStorage.removeItem("pygebra-biseccion-v1");
            ejemplo(w);
            valor(w, "a", "5"); valor(w, "b", "5.5");
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(lista(w).length === 13, "Primer intervalo: 13");
            ok(!q(w, "#biseccion-comparaciones table"), "Un solo cálculo sin tabla");
            ok(q(w, "#biseccion-comparaciones").textContent.includes("Ya tienes un cálculo"), "Orientación inicial");
            const funcion = q(w, '[name="funcion"]').value;
            ok(!funcion.includes("*"), "Función introducida con notación de clase");
            valor(w, "a", "5.2"); valor(w, "b", "5.3");
            valor(w, "funcion", "x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10");
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(lista(w).length === 10, "Segundo intervalo: 10");
            ok(q(w, '[name="funcion"]').value.replaceAll("*", "") === funcion, "Función equivalente conservada");
            ok(q(w, "#biseccion-comparaciones").textContent.includes("Compatible con la misma raíz"), "Misma raíz compatible");
            valor(w, "a", ".55"); valor(w, "b", "1.1");
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(q(w, "#biseccion-comparaciones").textContent.includes("Intervalos finales distintos"), "Raíces distintas");
            valor(w, "max_iteraciones", "1");
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(q(w, "#biseccion-comparaciones").textContent.includes("Actual · Sin convergencia verificada"), "Cálculo sin convergencia");
            ok(q(w, "#biseccion-comparaciones tbody").rows.length === 4, "Conserva los cuatro cálculos");
        }],
        ["Errores accesibles y raíz en extremo sin deslizador", async (w, frame) => {
            valor(w, "funcion", "1/x"); valor(w, "a", "-1"); valor(w, "b", "1");
            w = await post(frame);
            ok(!q(w, "#resultado"), "No declara raíz en una discontinuidad");
            ok(q(w, '[name="funcion"]').value === "1/x", "Conserva la entrada inválida");
            valor(w, "funcion", "x"); valor(w, "a", "0"); valor(w, "b", "1");
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(lista(w).length === 0 && !q(w, "#iteracion-biseccion"), "Raíz en extremo, sin iteraciones");
            valor(w, "a", "-1");
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(q(w, "#paso-decision").textContent.includes("f(c) = 0"), "Explica raíz exacta en punto medio");
        }],
        ["Conjuntos bloqueado en producción y marcado Próximamente", async w => {
            const respuesta = await w.fetch("/conjuntos/relaciones/");
            ok(respuesta.status === 404, "GET directo bloqueado");
            const html = await (await w.fetch("/?q=pertenencia")).text();
            ok(!html.includes('href="/conjuntos/relaciones/"') && html.includes("Próximamente"), "Sin enlace público");
        }],
    ];
    let aprobados = 0;
    for (const [nombre, probar] of casos) {
        const item = document.createElement("li"); document.getElementById("resultados").append(item);
        const frame = document.createElement("iframe"); frame.title = nombre; frame.style.cssText = "width:100%;height:700px";
        document.body.append(frame);
        try {
            await new Promise(resolve => { frame.onload = resolve; frame.src = "/metodos-numericos/biseccion/"; });
            await esperar(() => !!q(frame.contentWindow, "#biseccion-form"));
            await probar(frame.contentWindow, frame);
            item.textContent = `OK: ${nombre}`; aprobados++;
        } catch (e) { item.textContent = `FALLO: ${nombre}: ${e.message}`; }
        frame.remove();
    }
    document.getElementById("total").textContent = `${aprobados}/${casos.length} aprobados`;
})();
