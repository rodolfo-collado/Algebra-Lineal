/* DOM, parser y Plotly reales; los eventos sintéticos viven solo en las pruebas. */
(async () => {
    "use strict";
    const q = (w,s) => w.document.querySelector(s);
    const ok = (v,m) => { if (!v) throw new Error(m); };
    const esperar = async f => { const fin=Date.now()+15000; while(!f()) {
        if(Date.now()>fin) throw new Error("Espera agotada"); await new Promise(r=>setTimeout(r,40)); } };
    const g = w => q(w,"#raices-grafica");
    const lista = w => g(w)?.data?.[0]?.x?.length === 801 && !g(w).hidden;
    const valor = (w,n,v) => { const c=q(w,`[name="${n}"]`); c.value=v; c.dispatchEvent(new w.Event("input",{bubbles:true})); };
    const resolver = async (frame,cambios={}) => {
        const w=frame.contentWindow;
        for(const [n,v] of Object.entries({funcion:"x²-2",x0:"1.5",...cambios})) valor(w,n,v);
        await new Promise(r=>{frame.onload=r;q(w,"[data-calculo]").click();});
        await esperar(()=>lista(frame.contentWindow)); return frame.contentWindow;
    };
    const datos = w => JSON.parse(q(w,"#datos-raices").textContent).resultado;
    const casos = [
        ["Previsualización y selección de x₀ antes de resolver", async w=>{
            valor(w,"funcion","x²-2"); await esperar(()=>lista(w));
            ok(!q(w,"#resultado"),"No calcula al explorar");
            q(w,'[data-elegir-extremo="x0"]').click();
            g(w).emit("plotly_click",{points:[{curveNumber:0,x:1.5}]});
            ok(q(w,'[name="x0"]').value==="1.5","Selección en curva");
            await new Promise(r=>setTimeout(r,100));
            await w.Plotly.relayout(g(w),{"shapes[0].x0":1.6,"shapes[0].x1":1.6});
            await esperar(()=>q(w,'[name="x0"]').value==="1.6");
            ok(!g(w).layout.shapes[1].visible,"Sin segundo extremo");
        }],
        ["Tangente, residuo y recorrido coinciden con todas las filas", async (w,frame)=>{
            w=await resolver(frame, {funcion:"x³-x-2"});const r=datos(w);let peticiones=0;
            ok(q(w,"#raices-derivada").textContent==="f′(x) = 3 · x² − 1","Derivada automática visible");
            ok(!q(w,"#resultado").textContent.includes("f′(x) ="),"La derivada no se repite en el resultado");
            const primero=r.iteraciones[0];
            ok(primero.fxn===-0.125 && primero.dfxn===5.75 && primero.siguiente===1.5217391304347827,
               "Primera iteración de la diapositiva");
            ok(q(w,"#iteracion-raices").value==="1","Abre en la primera tangente");
            ok(!q(w,"#resultado").textContent.includes("= ≈"),"Sin igualdad falsa al redondear");
            const original=w.fetch;w.fetch=(...a)=>{peticiones++;return original(...a);};
            q(w,"#procedimiento-raices").open=true;
            for(const p of r.iteraciones){
                q(w,`[data-iteracion="${p.i}"]`).focus();
                await esperar(()=>g(w).data[1].x[0]===p.xn);
                ok(g(w).data[2].x[1]===p.siguiente && g(w).data[2].y[1]===0,"Corte con eje x");
                ok(g(w).data[2].y[0]===p.fxn,"Tangente parte del punto actual");
                ok(g(w).data[1].y[1]===p.fsiguiente,"Punto siguiente en curva");
                ok(q(w,"#paso-error").textContent.includes("Residuo"),"Residuo separado");
                ok(q(w,"#paso-decision").textContent.includes("−"),"Sustitución numérica");
            }
            q(w,"#iteracion-anterior").click();ok(q(w,"#iteracion-raices").value===String(r.iteraciones.length-1),"Retrocede");
            q(w,"#iteracion-siguiente").click();ok(q(w,"#iteracion-siguiente").disabled,"Último paso");
            ok(peticiones===0,"Recorrido sin recalcular ni pedir muestras");
            q(w,"#grafica-enfocar").click();await esperar(()=>peticiones>0);
            const p=r.iteraciones.at(-1),vista=w.metodosRaices.newton_raphson.vista(p);
            await esperar(()=>g(w).layout.xaxis.range[0]===vista[0],"Enfoca la tangente del paso activo");
            ok(vista[0]<Math.min(p.xn,p.siguiente)&&vista[1]>Math.max(p.xn,p.siguiente),"Tangente completa en el encuadre");
        }],
        ["Derivada reactiva sin resolver, sin ráfagas de peticiones y con mensajes discretos", async w=>{
            let peticiones=0;const original=w.fetch;w.fetch=(...a)=>{peticiones++;return original(...a);};
            for(const t of ["x","x^","x^3","x^3-","x^3-x"]) valor(w,"funcion",t);
            await esperar(()=>q(w,"#raices-derivada").textContent==="f′(x) = 3 · x² − 1");
            ok(peticiones===1,"Una sola petición tras escribir");
            ok(!q(w,"#resultado")&&!q(w,"#datos-raices").textContent.includes("iteraciones"),"Ningún cálculo de Newton");
            valor(w,"funcion","x^");
            await esperar(()=>q(w,"#raices-derivada").textContent.includes("aparecerá cuando f(x) esté completa"));
            ok(q(w,"#raices-derivada").hasAttribute("data-pendiente")&&!q(w,"[data-respuesta-errores]"),"Discreto, sin error de formulario");
            valor(w,"funcion","sen(x)/x");
            await esperar(()=>q(w,"#raices-derivada").textContent.startsWith("f′(x) = (cos(x)"));
            valor(w,"funcion","");
            ok(q(w,"#raices-derivada").textContent==="","Vacía sin función");
        }],
        ["Historial compara puntos iniciales de la misma función", async(w,frame)=>{
            w.sessionStorage.removeItem("pygebra-raices-historial-newton_raphson");
            w=await resolver(frame,{funcion:"x³-x-2",x0:"1.5"});
            ok(q(w,"#raices-historial").hidden,"Oculto con una ejecución");
            w=await resolver(frame,{funcion:"x³-x-2",x0:"0"});
            const h=q(w,"#raices-historial"),filas=[...h.querySelectorAll("tbody tr:not(:first-child)")];
            ok(!h.hidden&&h.querySelector("thead").textContent.includes("x₀")&&filas.length===2,"Dos x₀ en un grupo");
            ok(filas.map(f=>Number(f.cells[0].querySelector("span").dataset.raicesNumero)).join()==="1.5,0","Puntos iniciales");
            ok(filas[1].cells[3].textContent===String(datos(w).iteraciones.length),"Iteraciones de cada x₀");
        }],
        ["Teclado matemático en la función", async w=>{
            const c=q(w,'[name="funcion"]');c.focus();
            await esperar(()=>q(w,".math-keyboard").hasAttribute("data-abierto"));
            q(w,'[data-insercion="x²"]').click();
            ok(c.value==="x²" && w.document.activeElement===c,"Inserción y foco en la función");
            ok(!q(w,'[name="derivada"]'),"Sin entrada de derivada");
            q(w,'[name="x0"]').focus();ok(!q(w,".math-keyboard").hasAttribute("data-abierto"),"Oculto en x₀");
        }],
        ["Ejemplos, ciclos y raíz inicial", async(w,frame)=>{
            q(w,"#ejemplos-newton").open=true;q(w,'[data-newton-ejemplo="ciclo"]').click();
            ok(q(w,'[name="funcion"]').value==="x³-2x+2" && q(w,'[name="x0"]').value==="0","Ejemplo completo");
            w=await resolver(frame,{funcion:"x³-2x+2",x0:"0"});
            q(w,"#iteracion-siguiente").click();
            ok(datos(w).estado==="oscilacion" && q(w,"#paso-parada").textContent.includes("ciclo"),"Explica oscilación");
            w=await resolver(frame,{funcion:"x²",x0:"0"});
            ok(!q(w,"#iteracion-raices") && g(w).data[1].x[0]===0,"Raíz inicial sin pasos inventados");
        }],
        ["Estilos, temas y responsive con geometría real", async(w,frame)=>{
            w=await resolver(frame);const raiz=w.document.documentElement;
            for(const estilo of ["estudio","minimalista"]) for(const tema of ["light","dark"]) for(const ancho of [1280,744,390]){
                raiz.dataset.estilo=estilo;raiz.dataset.theme=tema;frame.style.width=ancho+"px";
                await w.Plotly.Plots.resize(g(w));
                await esperar(()=>g(w).layout.paper_bgcolor===w.getComputedStyle(raiz).getPropertyValue("--color-surface").trim());
                ok(raiz.scrollWidth<=raiz.clientWidth+1,"Sin desborde "+estilo+tema+ancho);
                ok(g(w).getBoundingClientRect().width>200,"Gráfica visible");
            }
        }],
        ["Precisión de lectura conserva cálculos",async(w,frame)=>{
            w=await resolver(frame);const original=q(w,"#datos-raices").textContent;
            const s=q(w,"#raices-decimales");s.value="completa";s.dispatchEvent(new w.Event("change"));
            ok(q(w,"#datos-raices").textContent===original,"JSON intacto");
            ok([...w.document.querySelectorAll("[data-raices-numero]")].every(n=>Number(n.textContent)===Number(n.dataset.raicesNumero)),"Valor almacenado");
        }],
    ];
    let aprobados=0;
    for(const [nombre,probar] of casos){
        const item=document.createElement("li");document.getElementById("resultados").append(item);
        const frame=document.createElement("iframe");frame.title=nombre;frame.style.cssText="width:100%;height:700px";document.body.append(frame);
        try{await new Promise(r=>{frame.onload=r;frame.src="/metodos-numericos/newton-raphson/";});await probar(frame.contentWindow,frame);item.textContent="OK: "+nombre;aprobados++;}
        catch(e){item.textContent="FALLO: "+nombre+": "+e.message;}frame.remove();
    }
    document.getElementById("total").textContent=`${aprobados}/${casos.length} aprobados`;
})();
