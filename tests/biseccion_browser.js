/* Formularios reales, Plotly local y muestras del backend de producción. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const ok = (valor, mensaje) => { if (!valor) throw new Error(mensaje); };
    const esperar = async (condicion, mensaje = "Espera agotada") => {
        const limite = Date.now() + 15000;
        while (!condicion()) {
            if (Date.now() > limite) throw new Error(mensaje);
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
        valor(w, "funcion", "x⁴ - 5x³ + 0.5x² - 11x + 10");
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
        ["Función sin extremos: exploración independiente y selección desde la curva", async w => {
            let peticiones = 0;
            const original = w.fetch; w.fetch = (...args) => { peticiones++; return original(...args); };
            for (const n of ["funcion", "a", "b"]) ok(q(w, `[name="${n}"]`).value === "", "Campo vacío");
            ok(!grafica(w).data && grafica(w).hidden, "Sin gráfica inventada");
            valor(w, "funcion", "x^2-2"); await esperar(() => listaGrafica(w), "Sin muestras iniciales");
            ok(peticiones === 1 && !grafica(w).hidden, "Solo función pide muestras");
            ok(grafica(w).data[0].x[0] === -10 && grafica(w).data[0].x[800] === 10, "Ventana inicial de exploración");
            ok(q(w, '[name="a"]').value === "" && q(w, '[name="b"]').value === "", "No inventa intervalo de cálculo");
            ok(!grafica(w).layout.shapes[0].visible && !grafica(w).layout.shapes[1].visible, "No muestra extremos inventados");
            q(w, '[data-elegir-extremo="a"]').click();
            grafica(w).emit("plotly_click", { points: [{ curveNumber: 0, x: 1 }] });
            await esperar(() => grafica(w).layout.shapes[0].visible, "No aparece a seleccionado");
            q(w, '[data-elegir-extremo="b"]').click();
            grafica(w).emit("plotly_click", { points: [{ curveNumber: 0, x: 2 }] });
            await esperar(() => grafica(w).layout.shapes[1].visible, "No aparece b seleccionado");
            ok(q(w, '[name="a"]').value === "1" && q(w, '[name="b"]').value === "2", "Selección reflejada en el formulario");
            valor(w, "a", "3");
            await esperar(() => grafica(w).layout.shapes[0].x0 === 3, "No se refleja la edición manual de a");
            ok(!grafica(w).hidden && grafica(w).layout.xaxis.range[0] === -10, "Extremos invertidos no ocultan ni desplazan la exploración");
            ok(!q(w, "#resultado"), "Vista previa sin resolver");
            valor(w, "funcion", "");
            ok(grafica(w).hidden && q(w, "#grafica-estado").textContent.includes("Introduce"), "Volver al estado vacío");
        }],
        ["La gráfica adopta los colores de cada estilo y tema sin perder la curva", async (w, frame) => {
            ejemplo(w);
            w = await post(frame); await esperar(() => listaGrafica(w));
            const raiz = w.document.documentElement;
            const token = nombre => w.getComputedStyle(raiz).getPropertyValue(nombre).trim();
            const fondos = new Set();
            for (const estilo of ["minimalista", "estudio"]) for (const tema of ["dark", "light"]) {
                raiz.setAttribute("data-estilo", estilo); raiz.setAttribute("data-theme", tema);
                await esperar(() => grafica(w).layout.paper_bgcolor === token("--color-surface")
                    && grafica(w).data[0].line.color === token("--color-brand")
                    && grafica(w).layout.font.color === token("--color-text"), `Colores de ${estilo}/${tema}`);
                fondos.add(grafica(w).layout.paper_bgcolor);
                ok(!/color-mix|var\(/.test(token("--color-surface") + token("--color-brand")), "Plotly recibe colores que entiende");
            }
            ok(fondos.size >= 2, "El fondo cambia de verdad");
            ok(grafica(w).data[0].x.length === 801 && grafica(w).layout.shapes.length === 3, "Conserva curva, extremos y franja");
            ok(lista(w).length === 13, "No recalcula");
        }],
        ["Teclado contextual de funciones reales conserva foco y cursor", async w => {
            const f = q(w, '[name="funcion"]'); f.focus();
            await esperar(() => q(w, ".math-keyboard").hasAttribute("data-abierto"));
            q(w, '[data-insercion="x²"]').click();
            ok(f.value === "x²" && w.document.activeElement === f, "Cuadrado y foco");
            valor(w, "funcion", "x"); f.setSelectionRange(1, 1);
            const modo = q(w, "[data-exponente-entero]");
            modo.click();
            ok(modo.getAttribute("aria-pressed") === "true", "Modo seleccionado");
            q(w, '[data-insercion="1"]').click(); q(w, '[data-insercion="2"]').click();
            ok(f.value === "x¹²", "Dígitos táctiles elevados");
            modo.click(); q(w, '[data-insercion="+"]').click(); q(w, '[data-insercion="3"]').click();
            ok(f.value === "x¹²+3", "Salida del modo");
            valor(w, "funcion", "(x+1)²"); f.setSelectionRange(5, 6); modo.click();
            q(w, '[data-insercion="-"]').click(); q(w, '[data-insercion="3"]').click();
            ok(f.value === "(x+1)⁻³", "Reemplaza exponente por negativo");
            valor(w, "funcion", ""); f.setSelectionRange(0, 0);
            q(w, '[data-insercion="√()"]')?.click();
            ok(f.value === "√()" && f.selectionStart === 2, "Raíz y cursor");
            valor(w, "funcion", ""); f.setSelectionRange(0, 0);
            q(w, '[data-insercion="sen()"]')?.click();
            ok(f.value === "sen()" && f.selectionStart === 4, "Seno en español");
            valor(w, "funcion", ""); f.setSelectionRange(0, 0);
            q(w, '[data-insercion="π"]').click();
            ok(f.value === "π", "Pi visible");
            valor(w, "funcion", ""); f.setSelectionRange(0, 0);
            q(w, '[data-insercion="e"]').click();
            ok(f.value === "e", "Constante e");
            valor(w, "funcion", ""); f.setSelectionRange(0, 0);
            q(w, '[data-insercion="log10()"]').click();
            ok(f.value === "log10()" && f.selectionStart === 6, "Logaritmo decimal y cursor");
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
        ["El estado listo espera a los extremos e ignora una entrada borrada durante la sincronización", async w => {
            const original = w.Plotly.relayout;
            let liberar;
            w.Plotly.relayout = (...args) => args[1]["shapes[0].visible"] === undefined ? original(...args) : new Promise(resolve => {
                liberar = () => { w.Plotly.relayout = original; return original(...args).then(resolve); };
            });
            valor(w, "funcion", "x²-2");
            await esperar(() => !!liberar);
            ok(q(w, "#grafica-estado").textContent.includes("Actualizando"), "No anuncia lista antes de sincronizar los extremos");
            valor(w, "funcion", ""); await liberar();
            await new Promise(r => w.requestAnimationFrame(r));
            ok(grafica(w).hidden && q(w, "#grafica-seleccion").hidden
                && q(w, "#grafica-estado").textContent.includes("Introduce"), "No muestra controles de una entrada borrada");
        }],
        ["Modo superíndice físico respeta edición y foco", async w => {
            const f = q(w, '[name="funcion"]'); f.focus();
            await esperar(() => !!q(w, "[data-exponente-entero]"));
            const escribir = texto => {
                const evento = new w.InputEvent("beforeinput", { inputType: "insertText", data: texto, bubbles: true, cancelable: true });
                if (f.dispatchEvent(evento)) w.document.execCommand("insertText", false, texto);
            };
            valor(w, "funcion", "x"); f.setSelectionRange(1, 1);
            q(w, "[data-exponente-entero]").click(); escribir("12");
            ok(f.value === "x¹²", "Escritura elevada");
            w.document.execCommand("undo");
            ok(f.value === "x", "Deshacer escritura elevada");
            valor(w, "funcion", "(x+1)²"); f.setSelectionRange(5, 6); escribir("-12");
            ok(f.value === "(x+1)⁻¹²", "Sustituye la selección");
            escribir("+3");
            ok(f.value === "(x+1)⁻¹²+3" && q(w, "[data-exponente-entero]").getAttribute("aria-pressed") === "false", "Operación sale del modo");
            q(w, "[data-exponente-entero]").click(); q(w, '[name="a"]').focus(); f.focus();
            await esperar(() => !!q(w, "[data-exponente-entero]"));
            ok(q(w, "[data-exponente-entero]").getAttribute("aria-pressed") === "false", "Otro foco desactiva el modo");
        }],
        ["Precisión pequeña mantiene distinguibles a, c y b", async (w, frame) => {
            valor(w, "funcion", "x^2-2"); valor(w, "a", "1"); valor(w, "b", "2");
            valor(w, "precision", "1e-10");
            w = await post(frame); await esperar(() => listaGrafica(w));
            const numeros = [...q(w, "#paso-valores").textContent.matchAll(/[=≈] ([\d,.-]+)/g)].map(m => m[1]);
            ok(numeros.length === 3 && new Set(numeros).size === 3, "No redondea los tres puntos al mismo número");
            const celdas = [...w.document.querySelectorAll(".biseccion-tabla tbody tr:last-child td [data-biseccion-numero]")].slice(0, 3);
            ok(new Set(celdas.map(n => n.textContent)).size === 3, "Tabla también distingue extremos");
        }],
        ["Decimales de lectura no recalculan ni crean ceros falsos", async (w, frame) => {
            valor(w, "funcion", "1e-20*(x²-2)"); valor(w, "a", "1"); valor(w, "b", "2");
            w = await post(frame); await esperar(() => listaGrafica(w));
            const original = q(w, "#datos-biseccion").textContent;
            let peticiones = 0; const fetch = w.fetch; w.fetch = (...args) => { peticiones++; return fetch(...args); };
            for (const precision of ["4", "16", "completa", "6"]) {
                const selector = q(w, "#biseccion-decimales"); selector.value = precision;
                selector.dispatchEvent(new w.Event("change", { bubbles: true }));
                for (const nodo of w.document.querySelectorAll("[data-biseccion-numero]")) {
                    const n = Number(nodo.textContent.replace("≈ ", ""));
                    ok(Number(nodo.dataset.biseccionNumero) === 0 || n !== 0, "No convierte valores en cero");
                    if (precision === "completa") ok(n === Number(nodo.dataset.biseccionNumero), "Valor de máquina accesible");
                }
            }
            ok(q(w, "#datos-biseccion").textContent === original && peticiones === 0, "Solo presentación");
            ok(!/≈\s*≈/.test(q(w, "#resultado").textContent), "No duplica aproximaciones");
        }],
        ["«=» para valores exactos y «≈» para redondeados, sin «= ≈», en ambos estilos", async (w, frame) => {
            const leer = w => q(w, "#resultado .results-heading .muted").textContent.replace(/\s+/g, " ");
            const decimales = (w, valor) => { const s = q(w, "#biseccion-decimales"); s.value = valor; s.dispatchEvent(new w.Event("change", { bubbles: true })); };
            for (const estilo of ["estudio", "minimalista"]) {
                w.document.documentElement.setAttribute("data-estilo", estilo);
                valor(w, "funcion", "x^2-2"); valor(w, "a", "1"); valor(w, "b", "2");
                w = await post(frame); await esperar(() => listaGrafica(w));
                w.document.documentElement.setAttribute("data-estilo", estilo);
                const fc = JSON.parse(q(w, "#datos-biseccion").textContent).resultado.fc;
                ok(fc !== 0, "El caso redondeado necesita f(c) ≠ 0");
                for (const precision of ["4", "6", "16"]) {
                    decimales(w, precision);
                    ok(/f\(c\) ≈ -?\d/.test(leer(w)), `${estilo}, ${precision}: f(c) redondeado usa ≈: ${leer(w)}`);
                }
                decimales(w, "completa");
                ok(/f\(c\) = -?\d/.test(leer(w)), `${estilo}: el valor completo vuelve a «=»: ${leer(w)}`);
                ok(!/=\s*≈|≈\s*=|≈\s*≈/.test(q(w, "#resultado").textContent + q(w, ".biseccion-recorrido").textContent), `${estilo}: sin símbolos dobles`);
                ok(/f\(c\) [=≈] /.test(q(w, "#paso-signos").textContent) && !/[=≈] [=≈]/.test(q(w, "#paso-signos").textContent), "El paso usa un solo símbolo");
                ok(/a \(izquierdo\) = 1 /.test(q(w, "#paso-valores").textContent.replace(/\s+/g, " ")) || q(w, "#iteracion-biseccion").value !== "1", "Un extremo exacto conserva «=»");
                // Una raíz exacta: f(c) = 0, nunca ≈ 0.
                valor(w, "funcion", "x-1.5"); valor(w, "a", "1"); valor(w, "b", "2");
                w = await post(frame); await esperar(() => listaGrafica(w));
                ok(JSON.parse(q(w, "#datos-biseccion").textContent).resultado.fc === 0, "El caso exacto necesita f(c) = 0");
                for (const precision of ["4", "completa"]) {
                    decimales(w, precision);
                    ok(leer(w).includes("f(c) = 0"), `${estilo}, ${precision}: igualdad exacta: ${leer(w)}`);
                }
                ok(q(w, "#paso-signos").textContent.includes("f(c) = 0 (cero)"), "El paso también escribe f(c) = 0");
            }
            w.document.documentElement.setAttribute("data-estilo", "estudio");
        }],
        ["Punto decimal en explicaciones y ejes, y «=» o «≈» en la gráfica según el redondeo", async (w, frame) => {
            for (const estilo of ["estudio", "minimalista"]) {
                w.document.documentElement.setAttribute("data-estilo", estilo);
                valor(w, "funcion", "x^2-2"); valor(w, "a", "1"); valor(w, "b", "2");
                w = await post(frame); await esperar(() => listaGrafica(w));
                w.document.documentElement.setAttribute("data-estilo", estilo);
                q(w, "#paso-detalles").open = true;
                const slider = q(w, "#iteracion-biseccion");
                for (const i of ["1", "7", slider.max]) {
                    slider.value = i; slider.dispatchEvent(new w.Event("input", { bubbles: true }));
                    const texto = ["#paso-valores", "#paso-signos", "#paso-decision", "#paso-intervalo"].map(s => q(w, s).textContent).join(" ") + slider.getAttribute("aria-valuetext");
                    ok(!/\d,\d/.test(texto), `${estilo}, iteración ${i}: sin coma decimal: ${texto}`);
                    ok(/\d\.\d/.test(texto), `${estilo}, iteración ${i}: con punto decimal`);
                }
                ok(grafica(w).layout.separators.startsWith("."), "Ejes con punto decimal");
                const comprobar = (traza, digitos) => {
                    const d = grafica(w).data[traza];
                    ok(!/= %\{[xy]/.test(d.hovertemplate), "Sin «=» fijo en la etiqueta");
                    ok(d.customdata?.length === d.x.length, "Una etiqueta por punto");
                    d.x.forEach((x, i) => [[x, d.customdata[i][0]], [d.y[i], d.customdata[i][1]]].forEach(([v, e]) => {
                        if (v === null) return;
                        const corto = Number(v.toPrecision(digitos));
                        ok(e === `${corto === v ? "=" : "≈"} ${corto}`, `${estilo}: etiqueta de ${v}: ${e}`);
                    }));
                    return d.customdata.flat();
                };
                const curva = comprobar(0, 10), puntos = comprobar(1, 12);
                ok(curva.some(e => e.startsWith("≈")) && curva.some(e => e.startsWith("=")), "La curva tiene valores exactos y redondeados");
                ok(puntos.some(e => e.startsWith("≈")), "Los puntos de la iteración redondeados usan ≈");
            }
            // Singular y plural: una raíz exacta tras una iteración.
            valor(w, "funcion", "x-1.5"); valor(w, "a", "1"); valor(w, "b", "2");
            w = await post(frame); await esperar(() => listaGrafica(w));
            ok(/^1 iteración ·/.test(q(w, "#resultado .results-heading .muted").textContent.trim()), "Una iteración, en singular");
            ok(grafica(w).data[1].customdata[1][0] === "= 1.5", "c exacto en la gráfica: = 1.5");
            w.document.documentElement.setAttribute("data-estilo", "estudio");
        }],
        ["Redondear no convierte una desigualdad estricta en igualdad", async (w, frame) => {
            valor(w, "funcion", "x-0.0001234567"); valor(w, "a", "0"); valor(w, "b", "0.00019999998");
            w = await post(frame); await esperar(() => listaGrafica(w));
            const selector = q(w, "#biseccion-decimales");
            for (const precision of ["4", "6", "8", "12", "16", "completa"]) {
                selector.value = precision; selector.dispatchEvent(new w.Event("change", { bubbles: true }));
                const valores = [...w.document.querySelectorAll(".biseccion-comprobacion [data-biseccion-numero]")];
                ok(valores.length === 2 && valores[0].textContent !== valores[1].textContent, "La longitud y la tolerancia siguen siendo distintas");
                ok(!/≈\s*≈/.test(q(w, "#resultado").textContent), "Sin doble aproximación");
            }
        }],
        ["Dominio explica raíz real y una corrección justificada", async (w, frame) => {
            valor(w, "funcion", "√(x)"); valor(w, "a", "-1"); valor(w, "b", "5");
            w = await post(frame);
            ok(!q(w, "#resultado"), "Mantiene el rechazo");
            ok(w.document.body.textContent.includes("valores negativos de x") && w.document.body.textContent.includes("a ≥ 0"), "Condición y corrección de raíz directa");
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
            q(w, "#iteracion-anterior").click();
            ok(slider.value === "6", "Retrocede una iteración");
            q(w, "#iteracion-siguiente").click();
            ok(slider.value === "7", "Avanza una iteración");
            slider.value = "1"; slider.dispatchEvent(new w.Event("input", { bubbles: true }));
            ok(q(w, "#iteracion-anterior").disabled, "No retrocede antes del primer paso");
            ok(q(w, "#paso-decision").textContent.includes("c pasa a ser el nuevo b") && q(w, "#paso-decision").textContent.includes("a permanece"), "Explica sustitución de b y extremo conservado");
            q(w, "#iteracion-siguiente").click();
            ok(q(w, "#paso-decision").textContent.includes("c pasa a ser el nuevo a") && q(w, "#paso-decision").textContent.includes("b permanece"), "Explica sustitución de a y extremo conservado");
            ok(q(w, "#paso-intervalo").textContent.includes("Nuevo intervalo"), "Nuevo intervalo separado");
            slider.value = String(lista(w).length); slider.dispatchEvent(new w.Event("input", { bubbles: true }));
            ok(q(w, "#iteracion-siguiente").disabled, "No avanza después del último paso");
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
        ["Vista inicial cancela el zoom pendiente y conserva ejes y muestras coherentes", async w => {
            valor(w, "funcion", "x²-2"); await esperar(() => listaGrafica(w));
            await w.Plotly.relayout(grafica(w), { "xaxis.range": [40, 60] });
            q(w, "#grafica-restablecer").click();
            await esperar(() => listaGrafica(w) && grafica(w).data[0].x[0] === -10);
            await new Promise(r => setTimeout(r, 400));
            ok(grafica(w).layout.xaxis.range[0] === -10 && grafica(w).data[0].x[0] === -10
                && grafica(w).data[0].x[800] === 10, "Descarta la vista anterior pendiente");
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
            ok(q(w, '[name="funcion"]').value.replaceAll("*", "").replaceAll("^4", "⁴").replaceAll("^3", "³").replaceAll("^2", "²") === funcion, "Función equivalente conservada");
            ok(q(w, "#biseccion-comparaciones").textContent.includes("Compatible con la misma raíz"), "Misma raíz compatible");
            const precision = q(w, "#biseccion-decimales"); precision.value = "4";
            precision.dispatchEvent(new w.Event("change", { bubbles: true }));
            const aproximaciones = [...w.document.querySelectorAll("#biseccion-comparaciones tbody tr td:nth-child(2) span")];
            ok(aproximaciones.length === 2 && aproximaciones[0].textContent !== aproximaciones[1].textContent, "Comparación distingue aproximaciones cercanas");
            precision.value = "completa"; precision.dispatchEvent(new w.Event("change", { bubbles: true }));
            ok(aproximaciones.every(n => Number(n.textContent) === Number(n.dataset.biseccionNumero)), "Comparación ofrece precisión completa");
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
