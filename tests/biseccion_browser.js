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
    const post = frame => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout POST")), 15000);
        frame.onload = () => { clearTimeout(timer); resolve(frame.contentWindow); };
        q(frame.contentWindow, "[data-calculo]").click();
    });
    const listaGrafica = w => grafica(w)?.data?.[0]?.x?.length === 801 &&
        !q(w, "#grafica-estado").textContent.includes("Actualizando");
    const casos = [
        ["Ejemplo del profesor: 13 filas y raíz verificada", async (w, frame) => {
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(lista(w).length === 13, "13 iteraciones");
            ok(lista(w)[12].c === .763970947265625, "Raíz del ejemplo");
            ok(grafica(w).layout.shapes.length === 3, "Dos extremos y una sola franja");
            ok(grafica(w).layout.shapes[2].x0 === lista(w)[12].a, "Franja de la última iteración");
            ok(!q(w, "#procedimiento-biseccion").open, "Detalle cerrado");
            ok(w.document.activeElement === q(w, "#resultado"), "Foco en el resultado");
        }],
        ["Cursor, foco y deslizador reutilizan pasos sin peticiones", async (w, frame) => {
            w = await post(frame); await esperar(() => listaGrafica(w));
            let peticiones = 0;
            const original = w.fetch; w.fetch = (...args) => { peticiones++; return original(...args); };
            q(w, "#procedimiento-biseccion").open = true;
            const fila = q(w, '[data-iteracion="2"]');
            fila.dispatchEvent(new w.PointerEvent("pointerenter"));
            await esperar(() => grafica(w).data[1].x[1] === lista(w)[1].c);
            ok(q(w, "#iteracion-biseccion").value === "2", "Cursor sincroniza el deslizador");
            q(w, '[data-iteracion="4"]').focus();
            await esperar(() => grafica(w).data[1].x[1] === lista(w)[3].c);
            const slider = q(w, "#iteracion-biseccion");
            slider.value = "7"; slider.dispatchEvent(new w.Event("input", { bubbles: true }));
            await esperar(() => grafica(w).data[1].x[1] === lista(w)[6].c);
            ok(grafica(w).layout.shapes[2].x0 === lista(w)[6].a, "Intervalo seleccionado");
            ok(peticiones === 0, "Sin nuevas peticiones al recorrer pasos");
            ok(grafica(w).layout.shapes.length === 3, "No se acumulan formas");
        }],
        ["Explorar y ajustar extremos conserva el resultado anterior", async (w, frame) => {
            w = await post(frame); await esperar(() => listaGrafica(w));
            await w.Plotly.relayout(grafica(w), { "xaxis.range": [-1, 6] });
            await esperar(() => grafica(w).data[0].x[0] === -1 && grafica(w).data[0].x[800] === 6);
            await w.Plotly.relayout(grafica(w), { "shapes[0].x0": .6, "shapes[0].x1": .6 });
            ok(Number(q(w, '[name="a"]').value) === .6, "Extremo conectado al formulario");
            ok(q(w, "#resultado").dataset.resultado === "desactualizado", "Aviso de resultado anterior");
            ok(lista(w).length === 13, "No vuelve a ejecutar la bisección");
        }],
        ["Dos intervalos de la segunda raíz: comparación de 13 y 10 pasos", async (w, frame) => {
            valor(w, "a", "5"); valor(w, "b", "5.5");
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(lista(w).length === 13, "Primer intervalo: 13");
            const funcion = q(w, '[name="funcion"]').value;
            valor(w, "a", "5.2"); valor(w, "b", "5.3");
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(lista(w).length === 10, "Segundo intervalo: 10");
            ok(q(w, '[name="funcion"]').value === funcion, "Función conservada");
            ok(q(w, "#biseccion-comparaciones").textContent.includes("Compatible con la misma raíz"), "Misma raíz compatible");
        }],
        ["Errores accesibles y raíz en extremo sin deslizador", async (w, frame) => {
            valor(w, "funcion", "1/x"); valor(w, "a", "-1"); valor(w, "b", "1");
            w = await post(frame);
            ok(!q(w, "#resultado"), "No declara raíz en una discontinuidad");
            ok(q(w, '[name="funcion"]').value === "1/x", "Conserva la entrada inválida");
            valor(w, "funcion", "x"); valor(w, "a", "0"); valor(w, "b", "1");
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(lista(w).length === 0 && !q(w, "#iteracion-biseccion"), "Raíz en extremo, sin iteraciones");
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
            await esperar(() => listaGrafica(frame.contentWindow));
            await probar(frame.contentWindow, frame);
            item.textContent = `OK: ${nombre}`; aprobados++;
        } catch (e) { item.textContent = `FALLO: ${nombre}: ${e.message}`; }
        frame.remove();
    }
    document.getElementById("total").textContent = `${aprobados}/${casos.length} aprobados`;
})();
