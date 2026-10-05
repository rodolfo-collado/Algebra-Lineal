(() => {
    "use strict";

    const root = document.querySelector("[data-expresiones]");
    if (!root) return;
    const lista = root.querySelector("[data-simbolos]");
    const cantidad = root.querySelector('[name="cantidad"]');
    const plantilla = document.getElementById("symbol-template");
    const celda = document.getElementById("expression-cell-template");
    const agregar = root.querySelector("[data-agregar]");
    const aviso = root.querySelector("[data-presupuesto]");
    // Los mismos topes que aplica el servidor antes de construir el formulario.
    const maximos = {
        simbolos: Number(cantidad.dataset.operandosMaximos),
        celdas: Number(cantidad.dataset.celdasMaximas),
        campos: Number(cantidad.dataset.camposMaximos),
    };
    const DIMENSION = 2;
    const memorias = new WeakMap();
    const { dimensionValida, validarDimension } = window.entradasSeguras;

    function tarjeta(nodo) {
        return nodo.closest("[data-simbolo]");
    }

    function campo(card, nombre) {
        return card.querySelector(`[data-campo="${nombre}"]`);
    }

    function entero(input) {
        return input && !input.disabled && dimensionValida(input) ? Number(input.value) : null;
    }

    function memoria(card) {
        if (!memorias.has(card)) {
            memorias.set(card, { tipo: campo(card, "tipo").value, tipos: new Map(),
                filas: entero(campo(card, "filas")) || DIMENSION,
                columnas: entero(campo(card, "columnas")) || DIMENSION });
        }
        const estado = memorias.get(card);
        if (!estado.tipos.has(estado.tipo)) estado.tipos.set(estado.tipo, new Map());
        const valores = estado.tipos.get(estado.tipo);
        card.querySelectorAll("[data-campo=celda]").forEach(input => {
            valores.set(`${input.dataset.fila}_${input.dataset.columna}`, input.value);
        });
        return estado;
    }

    function ocultarResultado() {
        const resultado = document.getElementById("resultado");
        if (resultado) resultado.hidden = true;
        const confirmacion = root.querySelector("[data-confirmacion]");
        if (confirmacion) confirmacion.hidden = true;
        const firma = root.querySelector('input[name="confirmacion"]');
        if (firma) firma.value = "";
    }

    // Lo que cada símbolo dibuja y envía, con la misma regla que forms_expresiones.py.
    function forma(tipo, filas, columnas) {
        if (tipo === "matriz_desconocida" || tipo === "vector_simbolico") return [0, 0];
        if (tipo === "escalar") return [1, 1];
        if (tipo === "vector" || tipo === "vector_lineal") return [filas, 1];
        return [filas, columnas];
    }

    function camposEstructura(tipo) {
        return 2 + (tipo !== "escalar") + (tipo === "matriz" || tipo === "matriz_desconocida");
    }

    function estructura(card) {
        const guardado = memorias.get(card);
        return {
            tipo: campo(card, "tipo").value,
            filas: entero(campo(card, "filas")) || guardado?.filas || DIMENSION,
            columnas: entero(campo(card, "columnas")) || guardado?.columnas || DIMENSION,
        };
    }

    // Mensaje si la estructura no cabe en el formulario; "" si cabe.
    function presupuesto(estructuras) {
        let celdas = 0;
        let campos = 0;
        estructuras.forEach(({ tipo, filas, columnas }) => {
            const [alto, ancho] = forma(tipo, filas, columnas);
            celdas += alto * ancho;
            campos += alto * ancho + camposEstructura(tipo);
        });
        if (celdas > maximos.celdas) {
            return `Los ${estructuras.length} símbolos sumarían ${celdas} celdas y la interfaz admite hasta ${maximos.celdas}: quita símbolos o reduce sus dimensiones.`;
        }
        if (campos > maximos.campos) {
            return `Los ${estructuras.length} símbolos ocuparían ${campos} campos del formulario (nombre, tipo, dimensiones y celdas) y la interfaz admite hasta ${maximos.campos}: quita símbolos o reduce sus dimensiones.`;
        }
        return "";
    }

    function tarjetas() {
        return [...lista.querySelectorAll("[data-simbolo]")];
    }

    // ¿Cabe el formulario si `card` pasa a tener `cambio`? Avisa y responde false si no.
    function cabe(card, cambio) {
        const mensaje = presupuesto(tarjetas().map(otra => (otra === card ? { ...estructura(otra), ...cambio } : estructura(otra))));
        aviso.textContent = mensaje;
        return !mensaje;
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

    function esVector(tipo) {
        return tipo === "vector" || tipo === "vector_lineal" || tipo === "vector_simbolico";
    }

    function nota(card) {
        let texto = card.querySelector("[data-nota]");
        if (!texto) {
            texto = document.createElement("p");
            texto.className = "field-help";
            texto.dataset.nota = "";
            card.querySelector("[data-rejilla]").before(texto);
        }
        return texto;
    }

    function actualizarNota(card, tipo, filas) {
        const texto = nota(card);
        const rejilla = card.querySelector("[data-rejilla]");
        const nombre = campo(card, "nombre").value || "x";
        if (tipo === "matriz_desconocida") {
            texto.hidden = false;
            texto.textContent = "Matriz desconocida: indica filas y columnas. Las entradas no se escriben; se determinan al comparar coeficientes.";
            rejilla.hidden = true;
            return;
        }
        if (tipo === "vector_simbolico") {
            const componentes = Array.from({ length: filas }, (_, i) => `${nombre}${i + 1}`).join(", ");
            texto.hidden = false;
            texto.textContent = filas ? `Componentes independientes: ${componentes}.` : "Indica cuántas componentes independientes tiene.";
            rejilla.hidden = true;
            return;
        }
        if (tipo === "vector_lineal") {
            texto.hidden = false;
            texto.textContent = "Cada componente es una expresión lineal, como 3x1 - 2x2.";
            rejilla.hidden = false;
            return;
        }
        texto.hidden = true;
        rejilla.hidden = false;
    }

    function etiquetaCelda(tipo, nombre, i, j) {
        if (tipo === "escalar") return `Valor del escalar ${nombre}`;
        if (tipo === "vector_lineal") return `Vector lineal ${nombre}, componente ${i + 1}`;
        if (tipo === "vector") return `Vector ${nombre}, componente ${i + 1}`;
        return `Matriz ${nombre}, fila ${i + 1}, columna ${j + 1}`;
    }

    function reconstruir(card) {
        const tipo = campo(card, "tipo").value;
        const estado = memoria(card);
        const guardado = estado.tipos.get(tipo) || new Map();
        const vector = esVector(tipo);
        const conColumnas = tipo === "matriz" || tipo === "matriz_desconocida";
        const conCeldas = tipo !== "matriz_desconocida" && tipo !== "vector_simbolico";
        let filas = 1;
        let columnas = 1;
        if (tipo === "escalar") {
            ocultar(card, "filas");
            ocultar(card, "columnas");
        } else {
            const entradaFilas = mostrar(card, "filas", vector ? "Componentes" : "Filas");
            filas = entero(entradaFilas);
            if (!conColumnas) {
                ocultar(card, "columnas");
            } else {
                const entradaColumnas = mostrar(card, "columnas", "Columnas");
                columnas = entero(entradaColumnas);
            }
        }
        const validas = [...card.querySelectorAll('.dimension-field input')].map(input => validarDimension(input));
        if (filas === null || columnas === null || validas.includes(false)) return;
        estado.tipo = tipo;
        if (tipo !== "escalar") estado.filas = filas;
        if (conColumnas) estado.columnas = columnas;
        const cuerpo = card.querySelector("tbody");
        cuerpo.replaceChildren();
        if (conCeldas) {
            const nombre = campo(card, "nombre").value || "símbolo";
            const ancho = tipo === "matriz" ? columnas : 1;
            const alto = tipo === "escalar" ? 1 : filas;
            for (let i = 0; i < alto; i += 1) {
                const fila = document.createElement("tr");
                for (let j = 0; j < ancho; j += 1) {
                    const copia = celda.content.cloneNode(true);
                    const input = copia.querySelector("input");
                    input.dataset.fila = String(i);
                    input.dataset.columna = String(j);
                    input.value = guardado.get(`${i}_${j}`) ?? "";
                    input.classList.toggle("matrix-input-lineal", tipo === "vector_lineal");
                    input.placeholder = tipo === "vector_lineal" ? "3x1 - 2x2" : "";
                    copia.querySelector("label").textContent = etiquetaCelda(tipo, nombre, i, j);
                    fila.append(copia);
                }
                cuerpo.append(fila);
            }
        }
        actualizarNota(card, tipo, filas);
        reindex();
    }

    function reindex() {
        const cards = tarjetas();
        cards.forEach((card, i) => {
            const nombre = campo(card, "nombre");
            const tipo = campo(card, "tipo");
            nombre.name = `nombre_${i}`;
            nombre.id = `id_nombre_${i}`;
            tipo.name = `tipo_${i}`;
            tipo.id = `id_tipo_${i}`;
            tipo.dataset.anterior = tipo.value;
            for (const clave of ["filas", "columnas"]) {
                const input = campo(card, clave);
                if (!input) continue;
                input.name = `${clave}_${i}`;
                input.id = `id_${clave}_${i}`;
            }
            const eliminar = card.querySelector("[data-eliminar]");
            eliminar.value = String(i);
            eliminar.type = "button";
            card.querySelectorAll("[data-campo=celda]").forEach(input => {
                input.name = `celda_${i}_${input.dataset.fila}_${input.dataset.columna}`;
                input.id = `id_${input.name}`;
                const label = input.closest("td").querySelector("label");
                if (label) label.htmlFor = input.id;
            });
            card.querySelectorAll('.dimension-field input').forEach(input => validarDimension(input));
        });
        cantidad.value = String(cards.length);
        if (agregar) agregar.disabled = cards.length >= maximos.simbolos;
        const vacio = lista.querySelector("[data-vacio]");
        if (vacio) vacio.hidden = cards.length > 0;
    }

    // A … Z y después A1 … Z1: la misma regla que el servidor al agregar sin JavaScript.
    function nombreLibre(usados) {
        for (let sufijo = 0; ; sufijo += 1) {
            for (const letra of "ABCDEFGHIJKLMNOPQRSTUVWXYZ") {
                const nombre = letra + (sufijo ? String(sufijo) : "");
                if (!usados.has(nombre)) return nombre;
            }
        }
    }

    root.addEventListener("click", (event) => {
        const paso = event.target.closest("[data-paso]");
        if (paso && root.contains(paso)) {
            const card = tarjeta(paso);
            const input = paso.closest(".stepper").querySelector("input");
            const siguiente = Math.min(Number(input.max), Math.max(Number(input.min), Number(input.value) + Number(paso.dataset.paso)));
            // El paso es atómico: si no cabe, nada cambia y queda el aviso.
            if (!cabe(card, { [input.dataset.campo]: siguiente })) return;
            input.value = String(siguiente);
            reconstruir(card);
            ocultarResultado();
            return;
        }
        const quitar = event.target.closest("[data-eliminar]");
        if (quitar && lista.contains(quitar)) {
            event.preventDefault();
            tarjeta(quitar).remove();
            aviso.textContent = "";
            reindex();
            ocultarResultado();
            return;
        }
        if (event.target.closest("[data-agregar]")) {
            event.preventDefault();
            const actuales = tarjetas();
            if (actuales.length >= maximos.simbolos) {
                aviso.textContent = `La interfaz admite hasta ${maximos.simbolos} símbolos.`;
                return;
            }
            const mensaje = presupuesto([...actuales.map(estructura), { tipo: "matriz", filas: DIMENSION, columnas: DIMENSION }]);
            if (mensaje) {
                aviso.textContent = `No se puede agregar otro símbolo: una matriz 2×2 más no cabe. ${mensaje}`;
                return;
            }
            aviso.textContent = "";
            lista.append(plantilla.content.cloneNode(true));
            const nueva = lista.querySelector("[data-simbolo]:last-child");
            campo(nueva, "nombre").value = nombreLibre(new Set(actuales.map(card => campo(card, "nombre").value)));
            reconstruir(nueva);
            ocultarResultado();
        }
    });

    lista.addEventListener("change", (event) => {
        if (event.target.dataset.campo !== "tipo") return;
        const card = tarjeta(event.target);
        if (!cabe(card, {})) {
            // Otro tipo no cabe con estas dimensiones: se recupera el anterior.
            event.target.value = event.target.dataset.anterior;
            return;
        }
        reconstruir(card);
        ocultarResultado();
    });
    lista.addEventListener("input", (event) => {
        const card = tarjeta(event.target);
        if (!card) return;
        if (event.target.dataset.campo === "filas" || event.target.dataset.campo === "columnas") {
            // Mientras se escribe no se corrige el número: si no cabe, la cuadrícula espera.
            validarDimension(event.target);
            if (cabe(card, {})) reconstruir(card);
            else validarDimension(event.target, aviso.textContent);
        }
        if (event.target.dataset.campo === "nombre") {
            const tipo = campo(card, "tipo").value;
            const nombre = event.target.value || "símbolo";
            if (tipo === "vector_simbolico") {
                actualizarNota(card, "vector_simbolico", entero(campo(card, "filas")) || 0);
            }
            card.querySelectorAll("[data-campo=celda]").forEach(input => {
                const label = input.closest("td") && input.closest("td").querySelector("label");
                if (label) label.textContent = etiquetaCelda(tipo, nombre, Number(input.dataset.fila), Number(input.dataset.columna));
            });
        }
    });
    root.addEventListener("input", ocultarResultado);
    root.addEventListener("change", ocultarResultado);

    // Tab recorre todos los campos. Las flechas verticales cambian de fila dentro del
    // símbolo; las horizontales solo cambian de celda al llegar al extremo del texto.
    lista.addEventListener("keydown", (event) => {
        const input = event.target;
        if (input.dataset.campo !== "celda" || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
        const deltas = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
        const delta = deltas[event.key];
        if (!delta || input.selectionStart !== input.selectionEnd) return;
        if (event.key === "ArrowLeft" && input.selectionStart !== 0) return;
        if (event.key === "ArrowRight" && input.selectionEnd !== input.value.length) return;
        const fila = Number(input.dataset.fila) + delta[0];
        const columna = Number(input.dataset.columna) + delta[1];
        const destino = tarjeta(input).querySelector(`[data-campo="celda"][data-fila="${fila}"][data-columna="${columna}"]`);
        if (destino) {
            event.preventDefault();
            destino.focus();
        }
    });

    root.querySelectorAll(".stepper [data-paso]").forEach(boton => { boton.hidden = false; });
    agregar.type = "button";
    tarjetas().forEach(card => memoria(card));
    reindex();
    root.querySelector("form").addEventListener("submit", event => {
        const mensaje = presupuesto(tarjetas().map(estructura));
        if (mensaje) {
            event.preventDefault();
            aviso.textContent = mensaje;
        }
    });
})();
