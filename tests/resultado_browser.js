/* P27.6: POST, eventos y geometría reales con los scripts de producción. */
(async () => {
    "use strict";
    const q = (w, s) => w.document.querySelector(s);
    const assert = (ok, mensaje) => { if (!ok) throw new Error(mensaje); };
    const turno = w => new Promise(resolve => w.requestAnimationFrame(() => w.requestAnimationFrame(resolve)));
    const valor = (w, campo, value, tipo = "input") => {
        campo.value = String(value);
        campo.dispatchEvent(new w.Event(tipo, { bubbles: true }));
    };
    const cargar = (frame, url) => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error(`Timeout: ${url}`)), 30000);
        frame.onload = async () => { clearTimeout(timer); await turno(frame.contentWindow); resolve(frame.contentWindow); };
        frame.src = url;
    });
    const post = frame => new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("Timeout POST")), 30000);
        frame.onload = async () => { clearTimeout(timer); await turno(frame.contentWindow); resolve(frame.contentWindow); };
        q(frame.contentWindow, "[data-calculo]").click();
    });
    const pagina = w => assert(w.document.documentElement.scrollWidth <= w.document.documentElement.clientWidth + 1,
        `Página desborda: ${w.document.documentElement.scrollWidth}/${w.document.documentElement.clientWidth}`);
    const casos = [];
    const entradas = {
        reduccion: '[name="matriz_0_0"]', axb: '[name="celda_A_0_0"]', inversa: '[name="celda_A_0_0"]',
        operaciones: '[name="celda_0_0_0"]', vectores: '[name="v1_0"]', bases: '[name="numero"]', romanos: '[name="numero"]',
    };
    for (const [nombre, selector] of Object.entries(entradas)) {
        casos.push([`${nombre}: vigente → entrada anterior → nuevo POST vigente`, nombre, async (w, frame) => {
            const resultado = q(w, "[data-resultado]");
            assert(resultado.dataset.resultado === "vigente", "POST inicial vigente");
            const controls = q(w, "[data-numeric-mode]");
            if (controls) { valor(w, controls, "decimal", "change"); valor(w, controls, "exacto", "change"); }
            q(w, "#procedimiento > summary").click(); q(w, "#procedimiento > summary").click();
            q(w, "#theme-toggle").click();
            assert(resultado.dataset.resultado === "vigente", "Presentación no invalida");
            const panel = q(w, ".panel-final"); const anterior = panel.textContent;
            const campo = q(w, selector); const inicial = Number(campo.value);
            valor(w, campo, inicial + 1);
            assert(!resultado.hidden && resultado.dataset.resultado === "desactualizado", "Resultado visible desactualizado");
            assert(panel.textContent === anterior && panel.getClientRects().length > 0, "Conserva el contenido");
            const aviso = q(w, ".result-notice"); let anuncios = 0;
            const observer = new w.MutationObserver(() => anuncios++);
            observer.observe(aviso, { subtree: true, childList: true, characterData: true });
            valor(w, campo, inicial + 2); await turno(w); observer.disconnect();
            assert(anuncios === 0 && w.document.querySelectorAll(".result-notice").length === 1, "Sin anuncio repetido");
            const range = w.document.createRange(); range.selectNodeContents(panel);
            w.getSelection().removeAllRanges(); w.getSelection().addRange(range);
            assert(w.getSelection().toString().trim().length > 0, "Resultado seleccionable y copiable");
            assert(!q(w, '[aria-busy="true"]'), "Editar no deja busy");
            w = await post(frame);
            assert(q(w, "[data-resultado]")?.dataset.resultado === "vigente", `Nuevo cálculo vigente: ${w.document.title}`);
            assert(q(w, ".result-notice").textContent === "", "Nuevo aviso vacío");
        }]);
    }
    for (const [ancho, alto] of [[1280, 650], [1084, 721], [744, 521], [640, 325], [390, 650]]) {
        for (const nombre of ["inversa-4", "inversa-6", "inversa-8", "inversa-10", "reduccion-8", "bases-largo", "rectangular", "axb"]) {
            casos.push([`${nombre}: geometría ${ancho}×${alto}`, nombre, async (w, frame) => {
                frame.style.width = `${ancho}px`; frame.style.height = `${alto}px`; await turno(w);
                q(w, "#procedimiento > summary").click(); await turno(w); pagina(w);
                const panel = q(w, ".panel-final").getBoundingClientRect();
                assert(panel.left >= 0 && panel.right <= w.innerWidth + 1, "Resultado dentro del viewport");
                for (const scroll of w.document.querySelectorAll(".matrix-scroll")) {
                    if (!scroll.clientWidth || scroll.closest("details:not([open])")) continue;
                    const overflow = scroll.scrollWidth > scroll.clientWidth + 1;
                    const entrada = scroll.closest("form");
                    assert(scroll.hasAttribute("tabindex") === (overflow && !entrada), "Tab solo en scroll real de salida");
                    if (overflow && !entrada) assert(scroll.getAttribute("aria-label")?.includes("desplazamiento horizontal"), "Scroll con nombre");
                    assert(scroll.querySelectorAll(".matrix-fence").length === 2, "Ambos corchetes dentro del scroll");
                    scroll.scrollLeft = scroll.scrollWidth; await turno(w);
                    const cierre = scroll.querySelector(".matrix-fence-end").getBoundingClientRect();
                    assert(cierre.right <= scroll.getBoundingClientRect().right + 1, "Cierre accesible al final");
                    const ultima = scroll.querySelector("tr td:last-child").getBoundingClientRect();
                    assert(ultima.right <= cierre.left + 1, "Última columna antes del cierre");
                    for (let padre = scroll.parentElement; padre; padre = padre.parentElement) {
                        const css = w.getComputedStyle(padre);
                        assert(!(["auto", "scroll"].includes(css.overflowX) && padre.scrollWidth > padre.clientWidth + 1), "Sin scroll horizontal anidado");
                    }
                }
                for (const par of w.document.querySelectorAll(".matrix-pair")) {
                    const items = par.querySelectorAll(".matrix-pair-item");
                    const envuelto = items[1].getBoundingClientRect().top > items[0].getBoundingClientRect().bottom;
                    assert(par.hasAttribute("data-wrapped") === envuelto, "Wrap medido y flecha coherente");
                    const transform = w.getComputedStyle(par.querySelector(".matrix-pair-arrow > span")).transform;
                    assert((transform !== "none") === envuelto, "Dirección de transición");
                    assert(w.getComputedStyle(par.querySelector(".matrix-pair-arrow")).transform === "none", "Sin giro responsive adicional");
                }
            }]);
        }
    }
    casos.push(["Resize: Tab aparece y desaparece al cambiar overflow", "inversa-8", async (w, frame) => {
        const scroll = q(w, ".panel-final .matrix-scroll");
        frame.style.width = "2500px";
        // La app limita el ancho a 1200; decimal corto permite que quepa.
        valor(w, q(w, "[data-numeric-mode]"), "decimal", "change");
        valor(w, q(w, "[data-numeric-precision]"), "2", "change"); await turno(w);
        assert(!scroll.hasAttribute("tabindex"), "Ancho grande sin parada muda");
        frame.style.width = "390px"; await turno(w);
        assert(scroll.tabIndex === 0 && scroll.scrollWidth > scroll.clientWidth, "Estrecho enfocable");
        scroll.focus(); assert(w.document.activeElement === scroll, "Scroll recibe foco");
        frame.style.width = "1280px"; await turno(w);
        assert(!scroll.hasAttribute("tabindex"), "Ancho restaurado retira Tab");
    }]);
    casos.push(["Procedimiento largo: sticky, cierre desde abajo y resultado alcanzable", "reduccion-8", async (w, frame) => {
        frame.style.width = "744px"; frame.style.height = "521px";
        const detalle = q(w, "#procedimiento"); const summary = q(w, "#procedimiento > summary");
        summary.click(); await turno(w);
        assert(detalle.getBoundingClientRect().height > 10000, "Procedimiento realmente largo");
        w.scrollTo(0, detalle.offsetTop + 6000); await turno(w);
        const rect = summary.getBoundingClientRect();
        const header = q(w, ".app-header").getBoundingClientRect();
        assert(w.getComputedStyle(summary).position === "sticky" && Math.abs(rect.top - header.bottom) <= 1, "Summary sigue bajo cabecera");
        assert(w.getComputedStyle(summary).backgroundColor !== "rgba(0, 0, 0, 0)", "Fondo sólido");
        summary.click(); await turno(w);
        const final = q(w, ".panel-final").getBoundingClientRect();
        assert(!detalle.open && final.top >= header.bottom && final.top < w.innerHeight, "Plegar acerca Resultado");
    }]);
    casos.push(["Cambios estructurales y opciones también desactualizan", "operaciones", async (w) => {
        q(w, "[data-agregar]").click(); await turno(w);
        assert(q(w, "[data-resultado]").dataset.resultado === "desactualizado", "Agregar símbolo invalida");
    }]);
    for (const [nombre, selector, value, tipo] of [
        ["reduccion", '[name="metodo"][value="gauss"]', null, "click"],
        ["reduccion", '[name="mostrar"]', null, "click"],
        ["axb", '[data-dimension="columnas"] [data-paso="1"]', null, "click"],
        ["inversa", '[name="verificar"]', null, "click"],
        ["inversa", '[data-dimension="orden"] [data-paso="1"]', null, "click"],
        ["operaciones", '[name="metodo"][value="columnas"]', null, "click"],
        ["operaciones", '[name="expresion"]', "A+B", "input"],
        ["vectores", '[data-agregar-vector]', null, "click"],
        ["vectores", '[name="operacion"][value="resta"]', null, "click"],
        ["bases", '[name="base_origen"]', "8", "change"],
        ["bases", '[name="bases_destino"][value="16"]', null, "click"],
        ["romanos", '[name="direccion"][value="romano_a_decimal"]', null, "click"],
    ]) {
        casos.push([`${nombre}: cambio relevante ${selector}`, nombre, async w => {
            const control = q(w, selector); assert(control, "Control existente");
            for (let padre = control.parentElement; padre; padre = padre.parentElement) {
                if (padre.tagName === "DETAILS") padre.open = true;
            }
            if (tipo === "click") control.click(); else valor(w, control, value, tipo);
            await turno(w);
            assert(q(w, "[data-resultado]").dataset.resultado === "desactualizado", "Opción o estructura invalida");
        }]);
    }
    casos.push(["Calcular desde stale mantiene busy y pageshow compartidos", "inversa", w => {
        valor(w, q(w, '[name="celda_A_0_0"]'), 4);
        const boton = q(w, '[data-calculo]');
        boton.form.dispatchEvent(new w.SubmitEvent('submit', {bubbles: true, cancelable: true, submitter: boton}));
        assert(boton.textContent === "Calculando…" && boton.form.getAttribute('aria-busy') === 'true', "Stale entra en busy");
        w.dispatchEvent(new w.PageTransitionEvent('pageshow', {persisted: true}));
        assert(!boton.form.hasAttribute('aria-busy') && !boton.hasAttribute('aria-busy'), "pageshow existente restaura");
    }]);
    casos.push(["Procedimiento 3×3 pequeño sin contenedores en Tab", "inversa-3", async w => {
        q(w, '#procedimiento > summary').click(); await turno(w);
        assert(!q(w, '#procedimiento .matrix-scroll[tabindex]'), "Sin overflow, sin paradas extra");
    }]);
    casos.push(["Sin JavaScript: no hay paradas mudas de matrices", "axb?sin-js", w => {
        assert(!q(w, '.matrix-scroll[tabindex], .matrix-equation[tabindex]'), "HTML sin tabindex=0");
    }]);
    casos.push(["POST inválido desde stale conserva foco P27.4", "romanos", async (w, frame) => {
        valor(w, q(w, '[name="numero"]'), 0); w = await post(frame);
        assert(!q(w, "[data-resultado]"), "Documento inválido manda");
        assert(w.document.activeElement === q(w, '[name="numero"]'), "Foco en campo inválido");
        assert(!q(w, '[aria-busy="true"]'), "Sin busy residual");
    }]);
    // Solo se simula el transporte del portapapeles; se ejecuta el botón de producción.
    const copiarResultado = (w, boton = q(w, "[data-copiar-resultado]"), preparar = () => {}) => {
        const original = w.document.execCommand;
        let data, impedido;
        w.document.execCommand = comando => {
            assert(comando === "copy", "Solo comando copy");
            data = new w.DataTransfer();
            const event = new w.ClipboardEvent("copy", { clipboardData: data, bubbles: true, cancelable: true });
            preparar(event); boton.dispatchEvent(event); impedido = event.defaultPrevented;
            return impedido;
        };
        try { boton.click(); } finally { w.document.execCommand = original; }
        return { data, impedido };
    };
    const formatos = (w, data) => [...data.types].map(tipo => [tipo, data.getData(tipo)]);
    const iguales = (a, b, mensaje) => assert(JSON.stringify(a) === JSON.stringify(b), mensaje);
    const exactos = matriz => [...matriz.querySelectorAll("tr")].map(tr => [...tr.cells].map(td => td.dataset.valorExacto));
    const comprobarResultado = (w, boton, esperado) => {
        const matriz = boton.closest("[data-matriz-copiable]");
        const antes = [...new w.FormData(q(w, "[data-entrada-calculo]"))];
        const foco = w.document.activeElement;
        const estado = q(w, "[data-resultado]").dataset.resultado;
        let cambios = 0; const contar = () => cambios++;
        q(w, "[data-entrada-calculo]").addEventListener("input", contar);
        const {data, impedido} = copiarResultado(w, boton);
        q(w, "[data-entrada-calculo]").removeEventListener("input", contar);
        assert(impedido, "Evento copy completado");
        iguales([...data.types], ["text/plain", "text/html", w.copiadoMatricial.TIPO], "Tres formatos P28.2");
        iguales(data.getData("text/plain"), esperado.map(f=>f.join("\t")).join("\n"), "TSV exacto completo");
        const celdas = esperado.flatMap((f,i)=>f.map((v,j)=>[i,j]));
        iguales(w.copiadoMatricial.parsear(data.getData(w.copiadoMatricial.TIPO), data.getData("text/plain")),
            {version:1, filas:esperado.length, columnas:esperado[0].length, forma:"rectangulo", celdas}, "Metadata v1 completa");
        const tabla = new w.DOMParser().parseFromString(data.getData("text/html"), "text/html");
        iguales([...tabla.querySelectorAll("tr")].map(tr=>[...tr.cells].map(td=>td.textContent)),
            esperado.map(f=>f.map(v=>v.includes("/")?`=${v}`:v)), "HTML y fracciones para Excel");
        assert(q(w,"[data-resultado]").dataset.resultado === estado && cambios === 0, "Copiar no marca stale ni emite input");
        iguales([...new w.FormData(q(w,"[data-entrada-calculo]"))], antes, "Inputs intactos");
        assert(w.document.activeElement === foco && !boton.disabled, "Foco y repetición conservados");
        const aviso = matriz.querySelector("[data-estado-copia]");
        assert(aviso.textContent === "Matriz copiada." && aviso.getAttribute("role") === "status" && aviso.getAttribute("aria-atomic") === "true", "Feedback accesible");
        assert(!q(w,"#procedimiento [data-copiar-resultado]"), "Procedimiento sin botones");
        assert(!matriz.querySelector("input, [data-celda-seleccionada]"), "Resultado sin selección ni inputs");
        return data;
    };
    const salidas = {
        "p28-suma": [[["1/3","-1","2"],["0","4","2"]]],
        "p28-resta": [[["1/3","-3","-2"],["10","3","-4"]]],
        "p28-producto": [[["1/3","-2"],["5","5/2"]]],
        "p28-expresion": [[["2/3","-5","-2"],["15","13/2","-5"]]],
        "p28-igualdad": [[["1/3","-2","0"],["5","7/2","-1"]], [["0","1","2"],["-5","1/2","3"]]],
        "p28-determinacion": [[["3","-2"],["1","4"],["0","1"]]],
        "p28-inversa": [[["1/3","0"],["0","-1/2"]]],
        "p28-gauss": [[["1","1","1/3"],["0","1","-2/3"]]],
        "p28-gauss_jordan": [[["1","0","1"],["0","1","-2/3"]]],
        "p28-comparar": [[["1","1","1/3"],["0","1","-2/3"]], [["1","0","1"],["0","1","-2/3"]]],
        "p28-inversa-inversa_inversa": [[["3","0"],["0","-2"]]],
        "p28-inversa-traspuesta": [[["1/3","0"],["0","-1/2"]]],
        "p28-inversa-producto": [[["1/3","0"],["0","-1/2"]]],
    };
    for (const [nombre, matrices] of Object.entries(salidas)) {
        casos.push([`P28.5 ${nombre}: exacto/decimal, formatos y vuelta a entrada`, nombre, w => {
            const botones = [...w.document.querySelectorAll("[data-copiar-resultado]")];
            assert(botones.length === matrices.length, "Un botón por matriz final");
            if(botones.length > 1) assert(new Set(botones.map(b=>b.getAttribute("aria-label"))).size === botones.length, "Nombres específicos distintos");
            botones.forEach((boton,i) => {
                boton.focus();
                const modo = q(w,"[data-numeric-mode]");
                valor(w,modo,"exacto","change");
                const exacto = comprobarResultado(w,boton,matrices[i]);
                valor(w,modo,"decimal","change");
                valor(w,q(w,"[data-numeric-precision]"),"2","change");
                const decimal = comprobarResultado(w,boton,matrices[i]);
                iguales(formatos(w,exacto),formatos(w,decimal),"Portapapeles Exacto === Decimal");
                valor(w,q(w,"[data-numeric-precision]"),"8","change");
                iguales(formatos(w,copiarResultado(w,boton).data),formatos(w,exacto),"Precisión 8 conserva exactitud");
                valor(w,modo,"exacto","change");
                iguales(formatos(w,copiarResultado(w,boton).data),formatos(w,exacto),"Decimal → Exacto idéntico");
                const tabla = q(w,"[data-entrada-calculo] table.matrix-entry-table") || q(w,"#matrix-grid");
                const input = tabla.querySelector("input.matrix-input");
                // Determinación usa una matriz simbólica sin inputs; su vuelta se cubre en Operaciones numéricas.
                if (input && nombre !== "p28-determinacion") {
                    input.focus(); w.seleccionMatricial.limpiar();
                    const event = new w.ClipboardEvent("paste",{clipboardData:decimal,bubbles:true,cancelable:true});
                    input.dispatchEvent(event);
                    assert(event.defaultPrevented,"P28.3 recibe metadata normal");
                    const filas = w.entradasSeguras.filasDeMatriz(tabla).map(fila=>fila.map(c=>c.value));
                    matrices[i].forEach((fila,j)=>iguales(filas[j].slice(0,fila.length),fila,"Round-trip exacto"));
                }
            });
        }]);
    }
    for (const [nombre,filas,columnas] of [["p28-operaciones-10",10,10],["inversa-10",10,10],["p28-reduccion-12",12,10],["p28-reduccion-13",9,13]]) {
        casos.push([`P28.5 límite ${filas}×${columnas}: datos completos fuera del viewport`,nombre,async(w,frame)=>{
            frame.style.width="320px"; await turno(w);
            const boton=q(w,"[data-copiar-resultado]"),matriz=boton.closest(".matrix");
            const valores=exactos(matriz); assert(valores.length===filas && valores[0].length===columnas,"Límite real");
            matriz.querySelector(".matrix-scroll").scrollLeft=10000;
            comprobarResultado(w,boton,valores); pagina(w);
        }]);
    }
    casos.push(["P28.5 calcular con preferencia Decimal inicial conserva el portapapeles", "p28-inversa", async(w,frame)=>{
        valor(w,q(w,"[data-numeric-mode]"),"exacto","change");
        const exacto=comprobarResultado(w,q(w,"[data-copiar-resultado]"),salidas["p28-inversa"][0]);
        valor(w,q(w,"[data-numeric-mode]"),"decimal","change");
        w=await post(frame);
        assert(q(w,"[data-numeric-mode]").value==="decimal","Nuevo cálculo inicia en Decimal");
        const decimal=comprobarResultado(w,q(w,"[data-copiar-resultado]"),salidas["p28-inversa"][0]);
        iguales(formatos(w,decimal),formatos(w,exacto),"Portapapeles idéntico tras POST en Decimal");
    }]);
    casos.push(["P28.5 stale y copiar conserva undo del pegado", "p28-inversa", w=>{
        const input=q(w,'[name="celda_A_0_0"]');
        const data=new w.DataTransfer(); data.setData("text/plain","1\t2\n3\t4");
        input.dispatchEvent(new w.ClipboardEvent("paste",{clipboardData:data,bubbles:true,cancelable:true}));
        assert(w.deshacerPegado.puedeDeshacer(),"Undo disponible");
        const aviso=q(w,"[data-estado-pegado]").textContent;
        assert(q(w,"[data-resultado]").dataset.resultado==="desactualizado" && q(w,".result-notice").textContent.includes("anterior"),"Stale comunica cálculo previo");
        comprobarResultado(w,q(w,"[data-copiar-resultado]"),salidas["p28-inversa"][0]);
        assert(w.deshacerPegado.puedeDeshacer() && !q(w,"[data-deshacer-pegado]").hidden,"Copiar conserva Deshacer");
        assert(q(w,"[data-estado-pegado]").textContent===aviso,"Feedback separado");
        q(w,"[data-deshacer-pegado]").click();
        iguales([...w.document.querySelectorAll('[data-matriz="A"] input.matrix-input')].map(c=>c.value),["3","0","0","-2"],"Undo todavía restaura");
    }]);
    casos.push(["P28.5 botón prevalece sobre selección de entrada/texto y anuncia una vez", "p28-inversa",async w=>{
        const input=q(w,'[name="celda_A_0_0"]'); input.focus();
        input.dispatchEvent(new w.MouseEvent("contextmenu",{bubbles:true,cancelable:true,button:2}));
        q(w,'[data-edicion-menu] [data-seleccionar="toda"]').click();
        input.focus(); input.select();
        const seleccion=w.seleccionMatricial.activa().celdas.map(c=>[c.fila,c.columna]);
        const mensaje=q(w,"[data-estado-seleccion]").textContent;
        const boton=q(w,"[data-copiar-resultado]"),aviso=boton.closest(".matrix").querySelector("[data-estado-copia]");
        let anuncios=0;const observer=new w.MutationObserver(()=>anuncios++);observer.observe(aviso,{childList:true});
        comprobarResultado(w,boton,salidas["p28-inversa"][0]);await turno(w);observer.disconnect();
        assert(anuncios===1 && q(w,"[data-estado-seleccion]").textContent===mensaje,"Una sola región actualizada");
        iguales(w.seleccionMatricial.activa().celdas.map(c=>[c.fila,c.columna]),seleccion,"Selección de entrada intacta");
    }]);
    for(const fallo of ["sin-evento","cancelado","escritura"]) casos.push([`P28.5 fallo ${fallo}: sin éxito parcial y recuperable`,"p28-inversa",w=>{
        const boton=q(w,"[data-copiar-resultado]"),aviso=q(w,"[data-estado-copia]");
        if(fallo==="sin-evento") {const original=w.document.execCommand;w.document.execCommand=()=>false;boton.click();w.document.execCommand=original;}
        else {const {data}=copiarResultado(w,boton,e=>{if(fallo==="cancelado")e.preventDefault();else dataFalla(e.clipboardData);});assert(data.types.length===0,"Sin formatos parciales");}
        assert(aviso.textContent.includes("No se pudo copiar"),"Fallo anunciado");
        comprobarResultado(w,boton,salidas["p28-inversa"][0]);
    }]);
    const dataFalla=data=>{const escribir=data.setData.bind(data);data.setData=(tipo,valor)=>{if(tipo==="text/html")throw new Error("QA");escribir(tipo,valor);};};
    casos.push(["P28.5 escape y límites comparten el núcleo P28.2","p28-inversa",w=>{
        const serializar=valor=>w.copiadoMatricial.serializarValores({celdas:[{fila:0,columna:0,valor}],rectangular:true,limites:{filaInicio:0,filaFin:0,columnaInicio:0,columnaFin:0}});
        const valor='&<>"\'';const datos=serializar(valor);
        assert(datos.html.includes("&amp;&lt;&gt;&quot;&#39;") && !datos.html.includes("<script"),"Escape compartido");
        assert(serializar("x".repeat(65537))===null && serializar("1\t2")===null,"Límites de texto P28.2");
        const boton=q(w,"[data-copiar-resultado]");q(w,"[data-valor-exacto]").dataset.valorExacto="x".repeat(65537);boton.click();
        assert(q(w,"[data-estado-copia]").textContent.includes("límites"),"Resultado excesivo rechazado");
    }]);
    for (const nombre of ["axb","p28-inversa-vector","vectores","bases","romanos"]) casos.push([`P28.5 ${nombre}: fuera del alcance`,nombre,w=>{
        assert(!q(w,"[data-copiar-resultado], [data-matriz-copiable]"),"Sin controles en vectores/texto");
    }]);
    for(const nombre of ["p28-suma","p28-comparar","p28-inversa"]) for(const tema of ["light","dark"]) for(const [ancho,alto] of [[1280,650],[744,521],[320,650]]) {
        casos.push([`P28.5 ${nombre} ${tema} ${ancho}×${alto}`,nombre,async(w,frame)=>{
            frame.style.width=`${ancho}px`;frame.style.height=`${alto}px`;
            if(w.document.documentElement.dataset.theme!==tema) q(w,"#theme-toggle").click(); await turno(w);
            pagina(w);
            const botones=[...w.document.querySelectorAll("[data-copiar-resultado]")];
            for(const boton of botones){boton.focus();comprobarResultado(w,boton,exactos(boton.closest(".matrix")));pagina(w);assert(w.getComputedStyle(boton).outlineStyle!=="none","Foco visible");}
        }]);
    }
    let fallos = 0;
    for (const [titulo, nombre, test] of casos) {
        const frame = document.createElement("iframe"); frame.title = titulo;
        frame.style.cssText = "display:block;width:1084px;height:721px;border:0";
        document.body.append(frame);
        const item = document.createElement("li");
        try {
            const w = await cargar(frame, `/__pruebas/casos/${nombre.replace('?sin-js', '/?sin-js')}`);
            await test(w, frame); item.textContent = `PASS: ${titulo}`;
        } catch (error) { fallos++; item.textContent = `FAIL: ${titulo}: ${error.message}`; }
        document.getElementById("resultados").append(item); frame.remove();
    }
    document.getElementById("total").textContent = `${casos.length - fallos}/${casos.length} correctas; ${fallos} fallos`;
})();
