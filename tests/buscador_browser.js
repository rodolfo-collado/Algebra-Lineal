/* P27.5: catálogo Django y scripts de producción; la tabla de orden viene de Python. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const todos = (w, s) => Array.from(w.document.querySelectorAll(s));
    const igual = (a, b) => {
        if (a?.nodeType || b?.nodeType) {
            if (a !== b) throw new Error(`${a?.nodeName} != ${b?.nodeName}`);
        } else if (JSON.stringify(a) !== JSON.stringify(b)) {
            throw new Error(`${JSON.stringify(a)} != ${JSON.stringify(b)}`);
        }
    };
    const turno = w => new Promise(r => w.requestAnimationFrame(() => w.requestAnimationFrame(r)));
    const valor = (w, texto, lateral = false) => {
        const input = q(w, lateral ? "#buscador-lateral" : "#buscador-inicio");
        input.value = texto;
        input.dispatchEvent(new w.Event("input", { bubbles: true }));
    };
    const ids = w => todos(w, "#catalogo-inicio [data-herramienta]:not([hidden])")
        .filter(n => n.getClientRects().length).map(n => n.dataset.herramienta);
    const menu = w => q(w, "#navigation-toggle").click();
    // El universo es el catálogo publicado por Django, no un número fijo de herramientas.
    const universo = w => JSON.parse(q(w, "#datos-buscador").textContent).herramientas.length;
    const escape = w => q(w, "#buscador-lateral").dispatchEvent(new w.KeyboardEvent(
        "keydown", { key: "Escape", bubbles: true, cancelable: true }));
    const casos = [
        ["GET tiene todo el universo, solo Gauss visible y un recuento estático", "/?q=gauss", w => {
            igual(todos(w, "#catalogo-inicio [data-herramienta]").length, universo(w));
            igual(ids(w), ["reduccion-filas"]);
            igual(q(w, "[data-busqueda-servidor]").hidden, false);
            todos(w, ".search-status").forEach(n => igual(n.textContent, ""));
            todos(w, "form[data-buscador]").forEach(n => igual(n.querySelectorAll('[aria-live="polite"]').length, 1));
        }],
        ["gauss → inversa → vectores → límites no envía GET ni duplica filas", "/?q=gauss", w => {
            const documento = w.document;
            for (const [texto, esperado] of [["inversa", ["matriz-inversa"]],
                ["vectores", ["operaciones-vectores", "operaciones-matrices"]], ["límites", ["limites-funciones"]]]) {
                valor(w, texto); igual(ids(w), esperado);
                igual(w.document, documento); igual(w.location.search, "?q=gauss");
                igual(q(w, "[data-busqueda-servidor]").hidden, true);
                igual(todos(w, "#catalogo-inicio [data-herramienta]").length, universo(w));
            }
            igual(q(w, '#catalogo-inicio [data-herramienta="limites-funciones"] .badge').textContent, "Próximamente");
        }],
        ["Editar y volver al GET restaura heading y vacía live", "/?q=gauss", w => {
            valor(w, "inversa"); igual(q(w, "#buscador-inicio-estado").textContent.includes("inversa"), true);
            valor(w, "gauss"); igual(ids(w), ["reduccion-filas"]);
            igual(q(w, "[data-busqueda-servidor]").hidden, false);
            igual(q(w, "#buscador-inicio-estado").textContent, "");
            valor(w, " gauss"); igual(q(w, "[data-busqueda-servidor]").hidden, true);
        }],
        ["Limpiar GET y volver a buscar no limita el universo", "/?q=gauss", w => {
            valor(w, ""); igual(ids(w).length, universo(w));
            valor(w, "invertir matriz"); igual(ids(w), ["matriz-inversa"]);
        }],
        ["GET vacío sin heading huérfano tiene sugerencias funcionales", "/?q=zzz", async (w, frame) => {
            igual(q(w, "#resultados-title"), null); igual(ids(w), []);
            const link = q(w, '#resultados-busqueda [data-busqueda-sugerencias] a');
            igual(link.getClientRects().length > 0, true);
            const carga = new Promise(r => { frame.onload = () => r(frame.contentWindow); });
            link.click(); w = await carga; await turno(w);
            igual(w.location.search, "?q=gauss"); igual(ids(w), ["reduccion-filas"]);
        }],
        ["Live vacío oculta heading, anuncia una vez y ofrece enlaces", "/?q=gauss", w => {
            valor(w, "zzz"); igual(ids(w), []);
            igual(q(w, "[data-busqueda-servidor]").hidden, true);
            igual(q(w, "#buscador-inicio-estado").textContent, "Sin coincidencias para «zzz».");
            igual(q(w, "#resultados-busqueda [data-busqueda-sugerencias]").hidden, false);
            valor(w, "calcular la"); igual(ids(w), []);
        }],
        ["GET sin coincidencias también permite buscar y restaurar el vacío", "/?q=zzz", w => {
            valor(w, "inversa"); igual(ids(w), ["matriz-inversa"]);
            valor(w, "zzz"); igual(ids(w), []);
            igual(q(w, "#buscador-inicio-estado").textContent, "");
            igual(q(w, "[data-busqueda-servidor]").hidden, false);
            igual(q(w, "#resultados-busqueda [data-busqueda-sugerencias]").hidden, false);
        }],
        ["GET con búsqueda enfoca resultados con contorno visible", "/?q=inversa", w => {
            const destino = q(w, "#resultados-busqueda");
            igual(w.document.activeElement, destino);
            igual(w.getComputedStyle(destino).outlineStyle, "solid");
            // El escalado de pantalla puede resolver 3px como 2.66667px: importa que el contorno exista.
            igual(parseFloat(w.getComputedStyle(destino).outlineWidth) > 0, true);
        }],
        ["GET normal conserva foco; live no provoca salto de foco", "/", w => {
            igual(w.document.activeElement, w.document.body);
            const input = q(w, "#buscador-inicio"); input.focus();
            valor(w, "inversa"); igual(w.document.activeElement, input);
        }],
        ["Inicio conserva mismas filas y canales al buscar y limpiar", "/", w => {
            const filas = todos(w, "#catalogo-inicio [data-herramienta]");
            valor(w, "límites"); igual(ids(w), ["limites-funciones"]);
            igual(todos(w, "#catalogo-inicio .canal").every(c => c.hidden), true);
            valor(w, ""); igual(ids(w), []);
            igual(todos(w, "#catalogo-inicio .canal").some(c => c.hidden), false);
            igual(q(w, "#calculo").classList.contains("es-pronto"), true);
            todos(w, "#catalogo-inicio [data-herramienta]").forEach((n, i) => {
                igual(n, filas[i]); igual(n.closest(".canal-herramientas").hidden, true);
            });
        }],
        ["Menú: Cálculo próximo, límites abre área y categoría", "/", w => {
            menu(w); valor(w, "límites", true);
            const area = q(w, "#nav-area-calculo").parentElement;
            igual(area.hidden, false); igual(area.open, true);
            igual(q(w, '[data-categoria="limites"]').open, true);
            igual(q(w, "#nav-area-calculo .nav-badge").textContent, "Próximamente");
            igual(q(w, '#arbol-herramientas [data-herramienta="limites-funciones"] .nav-badge').textContent, "Próximamente");
            igual(q(w, "#nav-area-algebra-lineal .nav-badge"), null);
            igual(q(w, "#nav-area-sistemas-numericos .nav-badge"), null);
        }],
        ["Escape con texto limpia sin cerrar, Escape vacío cierra", "/", w => {
            menu(w); valor(w, "inversa", true); q(w, "#buscador-lateral").focus();
            escape(w); igual(q(w, "#buscador-lateral").value, "");
            igual(q(w, "#navegacion-principal").hidden, false);
            igual(q(w, "#buscador-lateral-estado").textContent, "");
            escape(w); igual(q(w, "#navegacion-principal").hidden, true);
            igual(w.document.activeElement, q(w, "#navigation-toggle"));
        }],
        ["Menú restaura grupos y memoria sin guardar aperturas de filtro", "/matrices/inversa/", async w => {
            menu(w); const categoria = q(w, '[data-categoria="vectores"]'); categoria.open = true;
            const area = q(w, "#nav-area-calculo").parentElement; area.open = false;
            await turno(w);
            const memoria = w.sessionStorage.getItem("algebra-lineal-menu-secciones");
            igual(JSON.parse(memoria).includes("vectores"), true); igual(w.localStorage.getItem("algebra-lineal-menu-secciones"), null);
            const abiertos = todos(w, "#arbol-herramientas details").map(n => n.open);
            valor(w, "límites", true); await turno(w);
            igual(w.sessionStorage.getItem("algebra-lineal-menu-secciones"), memoria);
            valor(w, "", true); await turno(w);
            igual(todos(w, "#arbol-herramientas details").map(n => n.open), abiertos);
            igual(w.sessionStorage.getItem("algebra-lineal-menu-secciones"), memoria);
        }],
        ["Explorador del área: una parada de Tab, flechas y panel sin guardar nada", "/areas/algebra-lineal/", w => {
            const items = todos(w, "a.indice-item");
            const claves = Object.keys(w.localStorage).sort();
            const tecla = key => w.document.activeElement.dispatchEvent(new w.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true }));
            const visible = () => todos(w, ".destacado-cuerpo").filter(c => !c.hidden).map(c => c.dataset.id);
            igual(items.filter(a => a.tabIndex === 0).length, 1);
            items[0].focus(); tecla("End"); igual(w.document.activeElement, items.at(-1));
            igual(visible(), ["determinantes"]);
            tecla("ArrowUp"); igual(visible(), ["matriz-inversa"]);
            tecla("ArrowRight"); igual(w.document.activeElement.matches(".destacado-abrir"), true);
            igual(w.document.activeElement.getAttribute("href"), "/matrices/inversa/");
            tecla("ArrowLeft"); igual(w.document.activeElement, items[4]);
            igual(items.map(a => a.tabIndex), [-1, -1, -1, -1, 0, -1]);
            igual(Object.keys(w.localStorage).sort(), claves);
        }],
        ["Panel destacado: contexto del tema y lema solo si hay varias herramientas", "/areas/sistemas-numericos/", w => {
            const panel = () => w.document.querySelector(".destacado-cuerpo:not([hidden])");
            igual(panel().querySelector(".destacado-contexto").textContent, "Conversión entre binario, octal, decimal y hexadecimal.");
            igual(panel().querySelector(".destacado-lema"), null);
            w.document.querySelector('a.indice-item[data-id="conversion-romanos"]').focus();
            igual(panel().querySelector(".destacado-contexto").textContent, "Conversión entre números arábigos y romanos.");
        }],
        ["«Para curiosos» nace plegada, abre sin tapar el cálculo en ambos estilos", "/matrices/determinantes/", w => {
            const nota = w.document.querySelector(".tool-header > details.nota");
            const entrada = w.document.querySelector(".tool-header").nextElementSibling;
            igual(nota.open, false);
            for (const estilo of ["estudio", "minimalista"]) {
                w.document.documentElement.setAttribute("data-estilo", estilo);
                nota.open = false;
                if (nota.getBoundingClientRect().height > 60) throw new Error(`Plegada ocupa demasiado en ${estilo}`);
                nota.querySelector("summary").click();
                igual(nota.open, true);
                if (nota.getBoundingClientRect().bottom > entrada.getBoundingClientRect().top + 4) throw new Error(`Tapa el cálculo en ${estilo}`);
            }
        }],
        ["Música: apagada, voluntaria, con reproductor, y su volumen no toca el de los efectos", "/", async w => {
            const limpiar = almacen => ["pygebra-musica", "pygebra-musica-marca", "pygebra-musica-pieza", "pygebra-musica-volumen"].forEach(k => almacen.removeItem(k));
            limpiar(w.sessionStorage); limpiar(w.localStorage);
            const abrirMarco = () => new Promise(r => { const n = document.createElement("iframe"); n.onload = () => r(n); n.src = "/"; document.body.append(n); });
            const f = await abrirMarco();
            let g = null;
            const v = f.contentWindow, d = v.document;
            const boton = d.getElementById("musica-toggle"), lista = d.getElementById("musica-pieza");
            const elegir = id => { lista.value = id; lista.dispatchEvent(new v.Event("change", { bubbles: true })); };
            try {
                igual(d.getElementById("musica-grupo").hidden, false);
                igual(boton.textContent, "Reproducir");
                igual(v.Musica.pedida(), false);
                igual([...lista.options].map(o => o.value).join(), "continua,rincon,cafe,orbita,lluvia");
                igual(lista.value, "cafe");
                const efectos = v.localStorage.getItem("pygebra-volumen");
                const volumen = d.getElementById("musica-volumen");
                volumen.value = 70; volumen.dispatchEvent(new v.Event("input", { bubbles: true })); volumen.dispatchEvent(new v.Event("change", { bubbles: true }));
                igual(v.localStorage.getItem("pygebra-musica-volumen"), "70");
                igual(v.localStorage.getItem("pygebra-volumen"), efectos);
                boton.click();
                igual(boton.textContent, "Pausar"); igual(v.sessionStorage.getItem("pygebra-musica"), "on");
                igual(v.localStorage.getItem("pygebra-musica"), null);
                // Anterior y siguiente cambian lo elegido y lo recuerdan.
                d.getElementById("musica-siguiente").click();
                igual(lista.value, "orbita"); igual(v.localStorage.getItem("pygebra-musica-pieza"), "orbita");
                d.getElementById("musica-anterior").click(); d.getElementById("musica-anterior").click();
                igual(lista.value, "rincon");
                d.getElementById("musica-anterior").click();
                igual(lista.value, "lluvia");
                igual(d.getElementById("musica-ahora").textContent, `${v.Musica.actual().descripcion}.`);
                // En continua, saltar no sale del modo y una línea dice qué toca.
                elegir("continua");
                igual(v.localStorage.getItem("pygebra-musica-pieza"), "continua");
                igual(v.Musica.actual().id, "lluvia");
                d.getElementById("musica-siguiente").click();
                igual(lista.value, "continua"); igual(v.Musica.actual().id, "rincon");
                if (!d.getElementById("musica-ahora").textContent.startsWith("Ahora: Rincón tranquilo.")) throw new Error("Falta qué suena en continua");
                boton.click();
                igual(boton.textContent, "Reproducir"); igual(v.sessionStorage.getItem("pygebra-musica"), null);
                // Otra visita: en silencio, con lo elegido y el volumen; una preferencia inválida no rompe nada.
                f.remove();
                g = await abrirMarco();
                igual(g.contentWindow.Musica.pedida(), false);
                igual(g.contentDocument.getElementById("musica-pieza").value, "continua");
                igual(g.contentDocument.getElementById("musica-volumen").value, "70");
                g.remove();
                w.localStorage.setItem("pygebra-musica-pieza", "inexistente");
                g = await abrirMarco();
                igual(g.contentDocument.getElementById("musica-pieza").value, "cafe");
                // Ensayo sin altavoces: las cuatro suenan, no saturan y un compás siempre suena igual.
                const piezas = g.contentWindow.Musica.PIEZAS;
                for (const p of piezas) {
                    const ensayar = async () => {
                        const c = new g.contentWindow.OfflineAudioContext(2, 8000 * 12, 8000);
                        const sala = p.armar(c, c.destination);
                        sala.bus.gain.value = 0.5;
                        p.componer(sala, 8, 0);
                        return (await c.startRendering()).getChannelData(0);
                    };
                    const [a, b] = [await ensayar(), await ensayar()];
                    let pico = 0, diferencia = 0;
                    a.forEach((x, i) => { pico = Math.max(pico, Math.abs(x)); diferencia = Math.max(diferencia, Math.abs(x - b[i])); });
                    if (!(pico > 0.01 && pico < 0.7)) throw new Error(`${p.id}: nivel inesperado ${pico}`);
                    // El eco realimentado de Órbita puede moverse un bloque de audio entre ensayos: no es una nota.
                    if (diferencia > 0.1 * pico) throw new Error(`${p.id}: el mismo compás suena distinto: ${diferencia}`);
                    if (!p.notasDe) continue;
                    // La partitura, también al dar la vuelta: nada a un semitono ni a una novena menor.
                    const eventos = [];
                    for (let k = 0; k < p.LARGO + 8; k++) for (const n of p.notasDe(k)) {
                        if (n.midi) eventos.push({ ...n, k, a: k * 4 + n.pulso, z: k * 4 + n.pulso + n.dur });
                    }
                    eventos.forEach((x, i) => eventos.slice(i + 1).forEach(y => {
                        const distancia = Math.abs(x.midi - y.midi);
                        if (x.a < y.z && y.a < x.z && [1, 13, 25].includes(distancia)) throw new Error(`${p.id}: choque en el compás ${x.k}: ${x.voz} ${x.midi} y ${y.voz} ${y.midi}`);
                    }));
                }
                // Cuatro piezas que se distinguen: ni el mismo pulso ni los mismos instrumentos.
                igual(new Set(piezas.map(p => p.COMPAS)).size, 4);
                const voces = p => [...new Set(Array.from({ length: p.LARGO }, (_, k) => p.notasDe(k).map(n => n.voz)).flat())].sort().join();
                igual(new Set(piezas.filter(p => p.notasDe).map(voces)).size, 3);
            } finally {
                f.remove(); g?.remove();
                limpiar(w.sessionStorage); limpiar(w.localStorage);
            }
        }],
        ["Grupos y herramientas ocultos no se pueden enfocar", "/", w => {
            menu(w); valor(w, "inversa", true); const input = q(w, "#buscador-lateral"); input.focus();
            const oculto = q(w, '#arbol-herramientas [data-herramienta="conversion-bases"] a');
            igual(oculto.getClientRects().length, 0); oculto.focus(); igual(w.document.activeElement, input);
        }],
    ];
    const tabla = await (await fetch("/__pruebas/contrato.json")).json();
    for (const ruta of ["/", "/?q=gauss"]) {
        casos.push([`Orden/semántica Python = JS: ${tabla.length} consultas desde ${ruta}`, ruta, w => {
            for (const { consulta, ids: esperados } of tabla) {
                valor(w, consulta); igual(ids(w), esperados);
            }
        }]);
    }
    let aprobados = 0;
    for (const [nombre, ruta, probar] of casos) {
        const fila = document.createElement("li");
        document.getElementById("resultados").append(fila);
        const frame = document.createElement("iframe"); frame.style.cssText = "width:100%;height:600px";
        const errores = [];
        const carga = new Promise(r => { frame.onload = () => r(frame.contentWindow); });
        frame.src = ruta; document.body.append(frame);
        try {
            const w = await carga;
            w.addEventListener("error", e => errores.push(e.message)); await turno(w);
            await probar(w, frame); igual(errores, []);
            fila.textContent = `OK: ${nombre}`; fila.dataset.resultado = "ok"; aprobados++;
        } catch (error) {
            fila.textContent = `FALLO: ${nombre}: ${error.message}`; fila.dataset.resultado = "fallo";
        } finally { frame.remove(); }
    }
    document.getElementById("total").textContent = `${aprobados}/${casos.length} pruebas DOM correctas.`;
})();
