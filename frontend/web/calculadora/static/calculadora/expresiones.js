(() => {
    "use strict";

    const root = document.querySelector("[data-expresiones]");
    if (!root) return;
    const lista = root.querySelector("[data-simbolos]");
    const cantidad = root.querySelector('[name="cantidad"]');
    const plantilla = document.getElementById("symbol-template");
    const celda = document.getElementById("expression-cell-template");
    const agregar = root.querySelector("[data-agregar]");
    const maximo = 8;

    function tarjeta(nodo) {
        return nodo.closest("[data-simbolo]");
    }

    function campo(card, nombre) {
        return card.querySelector(`[data-campo="${nombre}"]`);
    }

    function entero(input) {
        const valor = Number(input && !input.disabled ? input.value : "");
        return Number.isInteger(valor) && valor >= 1 && valor <= 10 ? valor : null;
    }

    function memoria(card) {
        const valores = new Map();
        card.querySelectorAll("[data-campo=celda]").forEach(input => {
            valores.set(`${input.dataset.fila}_${input.dataset.columna}`, input.value);
        });
        return valores;
    }

    function ocultar(card, nombre) {
        const input = campo(card, nombre);
        if (!input) return;
        input.disabled = true;
        const caja = input.closest("[data-dimension]");
        if (caja) caja.hidden = true;
    }

    function mostrar(card, nombre, etiqueta) {
        let input = campo(card, nombre);
        if (!input) {
            const caja = document.createElement("div");
            caja.className = "dimension-field";
            caja.dataset.dimension = nombre;
            caja.innerHTML = `<label>${etiqueta}</label><div class="stepper"><button type="button" class="stepper-btn" data-paso="-1" aria-label="Quitar">−</button><input type="number" class="field-input" min="1" max="10" value="2" data-campo="${nombre}" inputmode="numeric" aria-label="${etiqueta}"><button type="button" class="stepper-btn" data-paso="1" aria-label="Agregar">+</button></div>`;
            card.querySelector("[data-eliminar]").before(caja);
            input = campo(card, nombre);
        }
        input.disabled = false;
        input.setAttribute("aria-label", etiqueta);
        const caja = input.closest("[data-dimension]");
        caja.hidden = false;
        const label = caja.querySelector("label");
        if (label) label.childNodes[0].textContent = etiqueta;
        return input;
    }

    function reconstruir(card) {
        const tipo = campo(card, "tipo").value;
        const guardado = memoria(card);
        let filas = 1;
        let columnas = 1;
        if (tipo === "escalar") {
            ocultar(card, "filas");
            ocultar(card, "columnas");
        } else {
            const entradaFilas = mostrar(card, "filas", tipo === "vector" ? "Componentes" : "Filas");
            filas = entero(entradaFilas);
            if (filas === null) return;
            if (tipo === "vector") {
                ocultar(card, "columnas");
            } else {
                const entradaColumnas = mostrar(card, "columnas", "Columnas");
                columnas = entero(entradaColumnas);
                if (columnas === null) return;
            }
        }
        const cuerpo = card.querySelector("tbody");
        cuerpo.replaceChildren();
        const nombre = campo(card, "nombre").value || "símbolo";
        for (let i = 0; i < filas; i += 1) {
            const fila = document.createElement("tr");
            for (let j = 0; j < columnas; j += 1) {
                const copia = celda.content.cloneNode(true);
                const input = copia.querySelector("input");
                const label = copia.querySelector("label");
                input.dataset.fila = String(i);
                input.dataset.columna = String(j);
                input.value = guardado.get(`${i}_${j}`) || "";
                label.textContent = tipo === "escalar"
                    ? `Valor del escalar ${nombre}`
                    : tipo === "vector"
                        ? `Vector ${nombre}, componente ${i + 1}`
                        : `Matriz ${nombre}, fila ${i + 1}, columna ${j + 1}`;
                fila.append(copia);
            }
            cuerpo.append(fila);
        }
        reindex();
    }

    function reindex() {
        const cards = [...lista.querySelectorAll("[data-simbolo]")];
        cards.forEach((card, i) => {
            const nombre = campo(card, "nombre");
            const tipo = campo(card, "tipo");
            nombre.name = `nombre_${i}`;
            nombre.id = `id_nombre_${i}`;
            tipo.name = `tipo_${i}`;
            tipo.id = `id_tipo_${i}`;
            for (const clave of ["filas", "columnas"]) {
                const input = campo(card, clave);
                if (!input) continue;
                input.name = `${clave}_${i}`;
                input.id = `id_${clave}_${i}`;
            }
            card.querySelector("[data-eliminar]").value = String(i);
            card.querySelectorAll("[data-campo=celda]").forEach(input => {
                input.name = `celda_${i}_${input.dataset.fila}_${input.dataset.columna}`;
                input.id = `id_${input.name}`;
                const label = input.closest("td").querySelector("label");
                if (label) label.htmlFor = input.id;
            });
        });
        cantidad.value = String(cards.length);
        if (agregar) agregar.disabled = cards.length >= maximo;
        const vacio = lista.querySelector("[data-vacio]");
        if (vacio) vacio.hidden = cards.length > 0;
    }

    root.addEventListener("click", (event) => {
        const paso = event.target.closest("[data-paso]");
        if (paso && root.contains(paso)) {
            const input = paso.closest(".stepper").querySelector("input");
            const siguiente = Math.min(10, Math.max(1, (entero(input) || 1) + Number(paso.dataset.paso)));
            input.value = String(siguiente);
            reconstruir(tarjeta(paso));
            return;
        }
        const quitar = event.target.closest("[data-eliminar]");
        if (quitar && lista.contains(quitar)) {
            event.preventDefault();
            tarjeta(quitar).remove();
            reindex();
            return;
        }
        if (event.target.closest("[data-agregar]")) {
            event.preventDefault();
            if (lista.querySelectorAll("[data-simbolo]").length >= maximo) return;
            lista.append(plantilla.content.cloneNode(true));
            const nueva = lista.querySelector("[data-simbolo]:last-child");
            const usados = new Set([...lista.querySelectorAll("[data-campo=nombre]")].slice(0, -1).map(input => input.value));
            const letra = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").find(candidata => !usados.has(candidata)) || "S";
            campo(nueva, "nombre").value = letra;
            reconstruir(nueva);
        }
    });

    lista.addEventListener("change", (event) => {
        if (event.target.dataset.campo === "tipo") reconstruir(tarjeta(event.target));
    });
    lista.addEventListener("input", (event) => {
        if (event.target.dataset.campo === "filas" || event.target.dataset.campo === "columnas") {
            reconstruir(tarjeta(event.target));
        }
    });

    root.querySelectorAll(".stepper [data-paso]").forEach(boton => { boton.hidden = false; });
    reindex();
})();
