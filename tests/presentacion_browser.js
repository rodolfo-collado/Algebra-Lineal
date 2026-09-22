/* DOM real y código de producción; almacenamiento aislado por caso. */
(async () => {
    const igual = (a, b) => {
        if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    };
    function seleccionar(w, selector, value) {
        const control = w.document.querySelector(selector);
        control.value = value;
        control.dispatchEvent(new w.Event("change", {bubbles:true}));
    }
    const decimal = w => seleccionar(w, "#numeric-mode", "decimal");
    const texto = (w, selector) => w.document.querySelector(selector).textContent;
    const casos = [
        ["Exacto inicial; precisión oculta y pasos cerrados", {}, w => {
            igual(texto(w, "#solucion"), "x1 = 1/3");
            igual(w.document.querySelector("#numeric-mode").value, "exacto");
            igual(w.document.querySelector("#numeric-precision").hidden, true);
            igual(w.document.querySelector("#pasos").open, false);
        }],
        ["Decimal coherente en soluciones, pasos, matriz y etiquetas", {}, w => {
            decimal(w);
            igual(texto(w, "#solucion"), "x1 ≈ 0.3333");
            igual(texto(w, "#mitad"), "x2 = 0.5");
            igual(texto(w, "#entero"), "x3 = 4");
            igual(texto(w, "#pasos code"), "F1 ≈ (0.3333)F1");
            igual([...w.document.querySelectorAll("td")].map(n => n.textContent), ["0.3333", "-0.3333"]);
            igual(w.document.querySelector("table").getAttribute("aria-label"), "Matriz con factor 0.3333");
            igual(w.document.querySelector("#entrada").value, "1/3");
        }],
        ["Las cuatro precisiones, sin peticiones ni apertura de pasos", {}, w => {
            decimal(w);
            for (const p of [2,4,6,8]) {
                seleccionar(w, "#numeric-precision", String(p));
                igual(texto(w, "#solucion"), "x1 ≈ 0." + "3".repeat(p));
                igual(texto(w, "[data-numeric-notice]").includes(`${p} decimales`), true);
            }
            igual(w.requests, 0);
            igual(w.document.querySelector("#pasos").open, false);
        }],
        ["Vuelta al exacto y limpieza de aviso", {}, w => {
            decimal(w); seleccionar(w,"#numeric-mode","exacto");
            igual(texto(w,"#solucion"),"x1 = 1/3");
            igual(texto(w,"[data-numeric-notice]"),"");
            igual(w.document.querySelector("table").getAttribute("aria-label"), "Matriz con factor 1/3");
        }],
        ["Preferencia decimal y precisión recuperadas", {values:{"pygebra-formato-numerico":"decimal","pygebra-precision-decimal":"6"}}, w => {
            igual(texto(w,"#solucion"),"x1 ≈ 0.333333");
            seleccionar(w,"#numeric-precision","8");
            igual(w.localStorage.getItem("pygebra-precision-decimal"),"8");
            igual(w.localStorage.getItem("pygebra-formato-numerico"),"decimal");
        }],
        ["Preferencias inválidas vuelven a los predeterminados", {values:{"pygebra-formato-numerico":"otro","pygebra-precision-decimal":"99"}}, w => {
            igual(w.document.querySelector("#numeric-mode").value,"exacto");
            igual(w.document.querySelector("#numeric-precision").value,"4");
        }],
        ["Sin localStorage: exacto inicial y cambios funcionales", {blocked:true}, w => {
            igual(texto(w,"#solucion"),"x1 = 1/3"); decimal(w);
            igual(texto(w,"#solucion"),"x1 ≈ 0.3333");
            w.document.querySelector("#theme-toggle").click();
            igual(w.document.documentElement.classList.contains("js"),true);
        }],
        ["Tema histórico migrado", {values:{"algebra-lineal-tema":"dark"}}, w => {
            igual(w.document.documentElement.dataset.theme,"dark");
            igual(w.localStorage.getItem("pygebra-tema"),"dark");
        }],
        ["Tema PyGebra tiene prioridad sobre el histórico", {values:{"pygebra-tema":"light","algebra-lineal-tema":"dark"}}, w => {
            igual(w.document.documentElement.dataset.theme,"light");
            w.document.querySelector("#theme-toggle").click();
            igual(w.localStorage.getItem("pygebra-tema"),"dark");
        }],
        ["Sin JavaScript: valores exactos y details nativos", {nojs:true}, w => {
            igual(texto(w,"#solucion"),"x1 = 1/3");
            igual(w.document.querySelector("[data-numeric-controls]").hidden,true);
            w.document.querySelector("summary").click();
            igual(w.document.querySelector("#pasos").open,true);
        }],
    ];
    let passed=0;
    for (const [name, seed, test] of casos) {
        window.seed=seed;
        const frame=document.createElement("iframe");
        if(seed.nojs) frame.setAttribute("sandbox","allow-same-origin");
        frame.src="/fixture";
        const loaded=new Promise(resolve => frame.onload=resolve);
        document.body.append(frame);
        await loaded;
        const item=document.createElement("li");
        try { await test(frame.contentWindow); passed++; item.textContent=`PASS · ${name}`; }
        catch(error) { item.textContent=`FAIL · ${name}: ${error.message}`; }
        document.querySelector("#resultados").append(item);
        frame.remove();
    }
    document.querySelector("#total").textContent=`${passed}/${casos.length} PASS`;
})();
