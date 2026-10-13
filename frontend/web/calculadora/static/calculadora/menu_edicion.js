(() => {
    "use strict";

    // Menú de edición de PyGebra: clic derecho, Shift+F10 o la tecla Menú sobre una celda de matriz,
    // vector o escalar, o sobre el número de Números romanos. En el resto de la página, y cuando el
    // puntero lo abre con texto seleccionado dentro del campo, queda el menú del navegador.
    const plantilla = document.getElementById("menu-edicion-template");
    if (!plantilla) return;
    const menu = plantilla.content.firstElementChild.cloneNode(true);
    document.body.append(menu);
    const titulo = menu.querySelector("[data-edicion-titulo]");
    const { filasDeMatriz } = window.entradasSeguras;
    // Enteros pequeños: bastan para probar un procedimiento sin cuentas largas.
    const MINIMO = -9, MAXIMO = 9;
    const TIPOS_OPERANDO = { matriz: "Matriz", vector: "Vector", escalar: "Escalar" };
    let abierto = null;

    const celdas = n => n === 1 ? "1 celda" : `${n} celdas`;
    const aleatorio = (minimo, maximo) => minimo + Math.floor(Math.random() * (maximo - minimo + 1));
    const entero = () => String(aleatorio(MINIMO, MAXIMO));
    const editable = input => Boolean(input?.isConnected && input.matches('input[type="text"]') && !input.readOnly &&
        !input.matches(":disabled") && !input.closest("[hidden], [inert]"));
    // Solo el ítem y su grupo: el menú cerrado también tiene hidden mientras se prepara.
    const visibles = () => [...menu.querySelectorAll('[role="menuitem"]')]
        .filter(item => !item.hidden && !item.closest('[role="group"]')?.hidden);

    // La misma escritura que decimal_a_romano: la tabla canónica y el máximo llegan del backend.
    function romano(valor, tabla) {
        let texto = "";
        for (const [simbolos, cantidad] of tabla) {
            for (; valor >= cantidad; valor -= cantidad) texto += simbolos;
        }
        return texto;
    }

    function numeroRomano(input) {
        const datos = JSON.parse(document.getElementById("datos-numeracion-romana")?.textContent || "null");
        if (!datos) return null;
        const enRomano = input.form?.querySelector('[name="direccion"]:checked')?.value === "romano_a_decimal";
        return { titulo: enRomano ? "Número romano" : "Número arábigo", celdas: [input], generar() {
            const valor = aleatorio(1, datos.maximo);
            return enRomano ? romano(valor, datos.tabla) : String(valor);
        } };
    }

    // Qué se edita desde este campo. `cuadricula` permite deshacer como un pegado y `matriz`,
    // seleccionar; un campo suelto (k, el número romano) conserva el Ctrl+Z nativo.
    function entradaDe(input) {
        if (!editable(input)) return null;
        if (input.closest("[data-numeracion-romana]")) return numeroRomano(input);
        if (!input.matches("input.matrix-input")) return null;
        const fila = input.closest("#vector-list .vector-row");
        if (fila) {
            if (fila.hasAttribute("data-escalar")) return { titulo: "Escalar k", celdas: [input], generar: entero };
            return { titulo: `Vector ${fila.dataset.vector}`, celdas: [...fila.querySelectorAll("input.matrix-input")],
                cuadricula: fila.closest("#vector-list"), generar: entero };
        }
        const cuadricula = input.closest(".matrix-entry-table, #matrix-grid");
        if (!cuadricula) return null;
        const comun = { celdas: filasDeMatriz(cuadricula).flat(), cuadricula, generar: entero };
        if (cuadricula.id === "matrix-grid") return { ...comun, titulo: "Matriz aumentada [A | b]", matriz: cuadricula };
        const operando = cuadricula.closest("[data-simbolo]");
        if (operando) {
            const tipo = operando.querySelector('[data-campo="tipo"]').value;
            // Un vector lineal tiene expresiones en sus celdas: rellenarlas con números no tiene sentido.
            if (!TIPOS_OPERANDO[tipo]) return null;
            const nombre = operando.querySelector('[data-campo="nombre"]').value.trim();
            return { ...comun, titulo: `${TIPOS_OPERANDO[tipo]} ${nombre}`.trim(), matriz: tipo === "matriz" ? cuadricula : null };
        }
        const entrada = cuadricula.closest("[data-matriz]");
        const vector = Boolean(entrada?.hasAttribute("data-vector"));
        return { ...comun, titulo: `${vector ? "Vector" : "Matriz"} ${entrada?.dataset.matriz ?? ""}`.trim(),
            matriz: vector ? null : cuadricula };
    }

    // Solo lo que tiene sentido aquí: Limpiar si hay algo que vaciar y los comandos de selección posibles.
    function preparar(entrada) {
        const editables = entrada.celdas.every(editable);
        const seleccion = entrada.matriz ? window.seleccionMatricial?.obtener(entrada.matriz) : null;
        menu.querySelector('[data-accion="rellenar"]').hidden = !editables;
        menu.querySelector('[data-accion="limpiar"]').hidden = !editables || entrada.celdas.every(celda => !celda.value);
        menu.querySelectorAll("[data-seleccion-menu]").forEach(nodo => { nodo.hidden = !seleccion; });
        menu.querySelectorAll("[data-seleccionar]").forEach(item => {
            item.hidden = !seleccion?.comandos.includes(item.dataset.seleccionar);
        });
        menu.querySelector('[data-accion="deseleccionar"]').hidden = !seleccion?.celdas.length;
        menu.querySelector("[data-seleccion-aumentada]").hidden = !seleccion || entrada.cuadricula.id !== "matrix-grid";
        const ayudas = [...menu.querySelectorAll(".menu-edicion-ayuda")].filter(ayuda => !ayuda.hidden);
        if (ayudas.length) menu.setAttribute("aria-describedby", ayudas.map(ayuda => ayuda.id).join(" "));
        else menu.removeAttribute("aria-describedby");
        titulo.textContent = entrada.titulo;
        return visibles();
    }

    // Junto al puntero o, desde el teclado, bajo el campo; siempre dentro de la ventana.
    function colocar(input, punto) {
        menu.style.left = menu.style.top = "0px";
        menu.hidden = false;
        const margen = 8;
        const { clientWidth: ancho, clientHeight: alto } = document.documentElement;
        const caja = menu.getBoundingClientRect();
        const campo = input.getBoundingClientRect();
        const x = punto ? punto.x : campo.left;
        const debajo = punto ? punto.y : campo.bottom + 4;
        const encima = (punto ? punto.y : campo.top - 4) - caja.height;
        // Debajo si cabe; si no, encima; si tampoco, lo más abajo posible sin salir de la ventana.
        const y = debajo + caja.height <= alto - margen ? debajo : encima >= margen ? encima : alto - caja.height - margen;
        menu.style.left = `${Math.max(margen, Math.min(x, ancho - caja.width - margen))}px`;
        menu.style.top = `${Math.max(margen, y)}px`;
    }

    function cerrar(devolverFoco = false) {
        if (!abierto) return;
        const { input } = abierto;
        abierto = null;
        // Primero el foco: el teclado matemático no parpadea al volver al campo.
        if (devolverFoco && input.isConnected) input.focus();
        menu.hidden = true;
    }

    function escribir(entrada, input, valores, textos) {
        if (!entrada.celdas.every(editable)) return;
        if (entrada.cuadricula) {
            // Misma aplicación atómica que el pegado: un input por celda, aviso y un nivel de Deshacer.
            window.deshacerPegado.pegar(entrada.celdas.map((celda, i) => [celda, valores[i]]), entrada.cuadricula, input, textos);
            return;
        }
        // Un campo suelto se edita como al escribir, así Ctrl+Z lo deshace.
        const [campo] = entrada.celdas;
        const [valor] = valores;
        campo.focus();
        campo.select();
        const hecho = valor ? document.execCommand("insertText", false, valor) : document.execCommand("delete");
        if (!hecho || campo.value !== valor) {
            campo.value = valor;
            campo.dispatchEvent(new Event("input", { bubbles: true }));
        }
    }

    const ACCIONES = {
        rellenar(entrada, input) {
            const generar = () => entrada.celdas.map(() => entrada.generar());
            const iguales = valores => valores.every((valor, i) => valor === entrada.celdas[i].value);
            let valores = generar();
            // Al menos un valor distinto: la acción siempre se nota, también en una sola celda.
            for (let intento = 0; intento < 20 && iguales(valores); intento++) valores = generar();
            escribir(entrada, input, valores, {
                hecho: () => `${entrada.titulo}: ${celdas(entrada.celdas.length)} con enteros aleatorios.`,
                sinCambios: "Relleno sin cambios.",
                deshecho: n => `Relleno deshecho: ${celdas(n)} ${n === 1 ? "restaurada" : "restauradas"}.`,
                invalido: "El relleno ya no puede deshacerse porque la entrada cambió.",
            });
        },
        limpiar(entrada, input) {
            escribir(entrada, input, entrada.celdas.map(() => ""), {
                hecho: n => `${entrada.titulo}: ${celdas(n)} ${n === 1 ? "vaciada" : "vaciadas"}.`,
                sinCambios: "No había valores que limpiar.",
                deshecho: n => `Limpieza deshecha: ${celdas(n)} ${n === 1 ? "restaurada" : "restauradas"}.`,
                invalido: "La limpieza ya no puede deshacerse porque la entrada cambió.",
            });
        },
        deseleccionar(entrada) {
            window.seleccionMatricial.limpiar(entrada.matriz);
        },
    };

    document.addEventListener("contextmenu", event => {
        if (menu.contains(event.target)) {
            event.preventDefault();
            return;
        }
        cerrar();
        const input = event.target;
        const entrada = event.defaultPrevented ? null : entradaDe(input);
        // Shift+F10 y la tecla Menú llegan con button -1 (0 en Firefox), aunque Chromium diga pointerType «mouse».
        const teclado = event.button !== 2 && !["touch", "pen"].includes(event.pointerType);
        // Un puntero sobre texto seleccionado deja Cortar, Copiar y Pegar del navegador.
        if (!entrada || (!teclado && input.selectionStart !== input.selectionEnd) || !preparar(entrada).length) return;
        event.preventDefault();
        abierto = { input };
        colocar(input, teclado ? null : { x: event.clientX, y: event.clientY });
        visibles()[0].focus();
    });

    menu.addEventListener("click", event => {
        const item = event.target.closest('[role="menuitem"]');
        if (!item || !abierto) return;
        const { input } = abierto;
        cerrar(true);
        // Se vuelve a leer la entrada: su DOM pudo cambiar con el menú abierto.
        const entrada = entradaDe(input);
        if (!entrada) return;
        if (item.dataset.seleccionar) {
            window.seleccionMatricial.comando(entrada.matriz, item.dataset.seleccionar, item.textContent.trim());
        } else {
            ACCIONES[item.dataset.accion](entrada, input);
        }
    });

    // En captura: Escape cierra el menú sin limpiar la selección ni el teclado matemático.
    window.addEventListener("keydown", event => {
        if (!abierto || !menu.contains(event.target)) return;
        const items = visibles();
        const actual = items.indexOf(document.activeElement);
        const destino = { ArrowDown: actual + 1, ArrowUp: actual - 1, Home: 0, End: items.length - 1 }[event.key];
        if (destino !== undefined) {
            event.preventDefault();
            items[(destino + items.length) % items.length].focus();
        } else if (event.key === "Escape" || event.key === "Tab") {
            event.preventDefault();
            cerrar(true);
        }
    }, true);

    // Pulsar fuera cierra sin robar el foco a lo que se pulsó.
    document.addEventListener("pointerdown", event => {
        if (abierto && !menu.contains(event.target)) cerrar();
    }, true);
    menu.addEventListener("mousedown", event => {
        if (!event.target.closest('[role="menuitem"]')) event.preventDefault();
    });
    menu.addEventListener("focusout", event => {
        if (abierto && !menu.contains(event.relatedTarget)) cerrar(!event.relatedTarget);
    });
    window.addEventListener("pagehide", () => cerrar());
})();
