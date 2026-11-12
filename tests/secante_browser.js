/* DOM, parser y Plotly reales en Métodos abiertos → Secante; los eventos sintéticos viven solo en las pruebas. */
(async () => {
    "use strict";
    const RUTA = "/metodos-numericos/metodos-abiertos/secante/";
    const NEWTON = "/metodos-numericos/metodos-abiertos/newton-raphson/";
    const q = (w,s) => w.document.querySelector(s);
    const qa = (w,s) => [...w.document.querySelectorAll(s)];
    const ok = (v,m) => { if (!v) throw new Error(m); };
    const esperar = async (f, m="Espera agotada") => { const fin=Date.now()+15000; while(!f()) {
        if(Date.now()>fin) throw new Error(m); await new Promise(r=>setTimeout(r,40)); } };
    const g = w => q(w,"#raices-grafica");
    const lista = w => g(w)?.data?.[0]?.x?.length === 801 && !g(w).hidden;
    const valor = (w,n,v) => { const c=q(w,`[name="${n}"]`); c.value=v; c.dispatchEvent(new w.Event("input",{bubbles:true})); };
    const navegar = (frame, accion) => new Promise(r=>{ frame.onload=r; accion(); });
    const resolver = async (frame,cambios={}) => {
        const w=frame.contentWindow;
        for(const [n,v] of Object.entries({funcion:"x³-x-2",x0:"1",x1:"2",...cambios})) valor(w,n,v);
        await navegar(frame, ()=>q(w,"[data-calculo]").click());
        await esperar(()=>lista(frame.contentWindow)); return frame.contentWindow;
    };
    const datos = w => JSON.parse(q(w,"#datos-raices").textContent).resultado;
    // Tres puntos alineados: los de la traza auxiliar están en la recta que une Pₙ₋₁ y Pₙ.
    const enRecta = (p, x, y) => Math.abs(p.factual + (p.factual-p.fanterior)/(p.actual-p.anterior)*(x-p.actual) - y) <= 1e-9*Math.max(1,Math.abs(y));
    const casos = [
        ["Gráfica antes de resolver y selección de x₀ y x₁ en la curva", async w=>{
            ok(q(w,'[aria-current="page"][data-metodo-abierto]').textContent.startsWith("Secante"),"Secante activa en el selector");
            valor(w,"funcion","x³-x-2"); await esperar(()=>lista(w));
            ok(!q(w,"#resultado"),"No calcula al explorar");
            q(w,'[data-elegir-extremo="x0"]').click();
            g(w).emit("plotly_click",{points:[{curveNumber:0,x:1}]});
            q(w,'[data-elegir-extremo="x1"]').click();
            g(w).emit("plotly_click",{points:[{curveNumber:0,x:2}]});
            ok(q(w,'[name="x0"]').value==="1"&&q(w,'[name="x1"]').value==="2","Dos puntos elegidos en la curva");
            await esperar(()=>g(w).layout.shapes[0].visible&&g(w).layout.shapes[1].visible,"Dos líneas");
            ok(g(w).layout.shapes[0].label.text==="x₀"&&g(w).layout.shapes[1].label.text==="x₁","Rótulos x₀ y x₁");
            ok(!g(w).layout.shapes[2].visible&&!g(w).layout.shapes[3].visible,"Sin franjas de intervalo");
            await new Promise(r=>setTimeout(r,100));
            await w.Plotly.relayout(g(w),{"shapes[1].x0":2.5,"shapes[1].x1":2.5});
            await esperar(()=>q(w,'[name="x1"]').value==="2.5","Arrastrar x₁");
            // Sin orden ni cambio de signo: x₁ < x₀ también se enfoca.
            valor(w,"x0","3");valor(w,"x1","2");q(w,"#grafica-enfocar").click();
            await esperar(()=>g(w).layout.xaxis.range[0]<2&&g(w).layout.xaxis.range[1]>3,"Enfoca los dos puntos");
        }],
        ["Secantes de la diapositiva 23 sincronizadas con tabla y gráfica, sin peticiones", async(w,frame)=>{
            w=await resolver(frame);const r=datos(w);let peticiones=0;
            ok(r.iteraciones.map(p=>p.siguiente.toFixed(6)).join()==="1.333333,1.462687,1.531169,1.520926,1.521376,1.521380","Diapositiva 23");
            ok(q(w,"#iteracion-raices").value==="1"&&q(w,"#paso-titulo").textContent==="Iteración 1 de 6: x₂","Abre en la iteración 1");
            ok(JSON.stringify(qa(w,".raices-tabla thead th").map(t=>t.textContent))===JSON.stringify(["n","xₙ₋₁ anterior","xₙ actual","xₙ₊₁ nueva","|xₙ₊₁ − xₙ| cambio","|f(xₙ₊₁)| residuo"]),"Columnas de clase y de parada");
            ok(q(w,"#iteracion-anterior").disabled,"No hay paso antes de la iteración 1");
            const original=w.fetch;w.fetch=(...a)=>{peticiones++;return original(...a);};
            q(w,"#procedimiento-raices").open=true;
            for(const p of r.iteraciones){
                q(w,`[data-iteracion="${p.i}"]`).focus();
                await esperar(()=>g(w).data[1].x.join()===[p.anterior,p.actual,p.siguiente].join(),"Puntos de la iteración "+p.i);
                const t=g(w).data[2],k=t.x.indexOf(p.siguiente),sub=j=>"₀₁₂₃₄₅₆₇₈₉"[j];
                ok(k>0&&t.y[k]===0&&t.marker.size[k]===13,"Corte con el eje x "+p.i);
                const rot=g(w).layout.annotations.map(a=>[a.text,a.x,a.y].join());
                ok(rot.join("|")===[["P"+sub(p.i-1),p.anterior,p.fanterior],["P"+sub(p.i),p.actual,p.factual],["x"+sub(p.i+1),p.siguiente,0]].map(a=>a.join()).join("|"),"Rótulos P y corte "+p.i);
                ok(qa(w,"#raices-grafica .annotation-text").length===3,"Rótulos dibujados "+p.i);
                const nulo=t.x.indexOf(null);
                ok(t.x.slice(0,nulo).every((x,j)=>enRecta(p,x,t.y[j])),"Recta secante por P y el corte "+p.i);
                ok(t.x.slice(0,nulo).every((x,j,a)=>j===0||a[j-1]<=x),"Recta ordenada en x "+p.i);
                ok(t.x[nulo+1]===p.siguiente&&t.y[nulo+2]===p.fsiguiente,"Altura f(xₙ₊₁) "+p.i);
                ok(q(w,`[data-iteracion="${p.i}"]`).hasAttribute("data-activa"),"Fila activa "+p.i);
                ok(q(w,"#paso-decision").textContent.includes("secante"),"Lectura completa");
            }
            q(w,"#iteracion-anterior").click();ok(q(w,"#iteracion-raices").value==="5","Retrocede");
            q(w,"#iteracion-siguiente").click();ok(q(w,"#iteracion-siguiente").disabled,"Último paso");
            ok(peticiones===0,"Recorrido sin recalcular ni pedir muestras");
            q(w,"#grafica-enfocar").click();await esperar(()=>peticiones>0);
            const p=r.iteraciones.at(-1),vista=w.metodosRaices.secante.vista(p);
            await esperar(()=>g(w).layout.xaxis.range[0]===vista[0],"Enfoca la secante del paso activo");
        }],
        ["Fórmula, sustitución y operaciones de la diapositiva 22", async(w,frame)=>{
            w=await resolver(frame);const r=datos(w);
            const formula=q(w,".abierto-formula");
            ok(formula.textContent.includes("f(x) = x³ − x − 2")&&!formula.textContent.includes("f′"),"Función sin derivada");
            ok(q(w,".abierto-formula .raices-fraccion").textContent==="f(xₙ) · (xₙ − xₙ₋₁)f(xₙ) − f(xₙ₋₁)","Fracción completa apilada");
            const breve=q(w,"#paso-breve"),texto=breve.textContent;
            ok(qa(w,"#paso-breve dd").map(d=>d.textContent).join("|")==="= 1|= −2|= 2|= 4","x₀, f(x₀), x₁ y f(x₁)");
            const fr=qa(w,"#paso-breve .raices-fraccion").map(f=>[...f.children].map(c=>c.textContent).join(" / "));
            ok(fr[0]==="f(x₁) · (x₁ − x₀) / f(x₁) − f(x₀)","Sustitución simbólica");
            ok(fr[1]==="4 · (2 − 1) / 4 − (−2)","Sustitución numérica con paréntesis");
            ok(fr[2]==="4 / 6","Operaciones: numerador y denominador");
            ok(q(w,".abierto-nueva").textContent==="x₂ ≈ 1.333333","Primera aproximación");
            ok(texto.includes("x₂ = 2 − ")&&texto.includes("xₙ₋₁ ← x₁, xₙ ← x₂"),"Actualización de los puntos");
            ok(q(w,"#paso-breve .sr-only").textContent==="(f(x₁) · (x₁ − x₀))/(f(x₁) − f(x₀))","Lectura lineal");
            ok(qa(w,".abierto-comprobacion li").map(li=>li.dataset.cumple).join()==="false,false","Primera iteración no cumple");
            const s=q(w,"#raices-decimales");s.value="completa";s.dispatchEvent(new w.Event("change"));
            for(const p of r.iteraciones){
                q(w,`[data-iteracion="${p.i}"]`).click();
                ok(qa(w,"#paso-breve dd").map(d=>Number(d.textContent.slice(2).replace("−","-"))).join()===[p.anterior,p.fanterior,p.actual,p.factual].join(),"Valores almacenados "+p.i);
                ok(Number(q(w,".abierto-nueva strong").textContent)===p.siguiente,"Nueva aproximación almacenada "+p.i);
                ok(qa(w,".abierto-comprobacion li").map(li=>li.dataset.cumple).join()===[p.error_absoluto<=r.tolerancia,p.residuo<=r.tolerancia].join(),"Comprobación "+p.i);
            }
            ok(q(w,"#paso-breve").textContent.includes("Se detiene"),"El último paso explica la parada");
            s.value="4";s.dispatchEvent(new w.Event("change"));q(w,'[data-iteracion="1"]').click();
            ok(q(w,".abierto-nueva").textContent==="x₂ ≈ 1.3333","4 decimales en la explicación");
            ok(!/\de[-+]?\d/.test(q(w,"#resultado").textContent)&&!q(w,"#resultado").textContent.includes("= ≈"),"Sin exponentes ni igualdad falsa");
        }],
        ["Ejemplos precargados y práctica integradora con tolerancia 10⁻⁶", async(w,frame)=>{
            q(w,"#ejemplos-secante").open=true;q(w,'[data-ejemplo*="x³-2x-5"]').click();
            ok(q(w,'[name="funcion"]').value==="x³-2x-5"&&q(w,'[name="x0"]').value==="2"&&q(w,'[name="x1"]').value==="3"&&q(w,'[name="precision"]').value==="0.000001","Práctica completa");
            w=await navegar(frame,()=>q(w,"[data-calculo]").click()).then(()=>frame.contentWindow);
            await esperar(()=>lista(w));
            const r=datos(w);
            ok(r.convergio&&r.tolerancia===1e-6&&Math.abs(r.x-2.0945514815)<1e-9,"Raíz con tolerancia 10⁻⁶");
            q(w,"#ejemplos-secante").open=true;q(w,'[data-ejemplo*="x³-x-2"]').click();
            ok(q(w,'[name="precision"]').value==="0.0001","Otro ejemplo restablece la tolerancia");
        }],
        ["Cambiar de método conserva la función y nunca el resultado", async(w,frame)=>{
            w.sessionStorage.clear();
            w=await resolver(frame);
            const enlace=q(w,`[data-metodo-abierto][href^="${NEWTON}"]`);
            ok(new URL(enlace.href).searchParams.get("funcion")==="x³-x-2","El enlace lleva la función");
            await navegar(frame,()=>enlace.click());w=frame.contentWindow;
            ok(w.location.pathname===NEWTON&&q(w,'[name="funcion"]').value==="x³-x-2","Newton recibe la función");
            ok(!q(w,"#resultado")&&!q(w,"#iteracion-raices"),"Newton empieza sin resultado");
            ok(q(w,'[aria-current="page"][data-metodo-abierto]').textContent.startsWith("Newton"),"Newton activo");
            await esperar(()=>lista(w)&&q(w,"#raices-derivada").textContent==="f′(x) = 3x² − 1","Gráfica y derivada de Newton");
            ok(!g(w).layout.shapes[1].visible,"Newton solo tiene x₀");
            valor(w,"funcion","cos(x) - x");
            await navegar(frame,()=>q(w,`[data-metodo-abierto][href^="${RUTA}"]`).click());w=frame.contentWindow;
            ok(q(w,'[name="funcion"]').value==="cos(x) - x"&&q(w,'[name="x0"]').value===""&&!q(w,"#resultado"),"Secante recibe la función sin puntos ni resultado");
            await esperar(()=>lista(w));
            ok(w.sessionStorage.getItem("pygebra-raices-historial-secante")&&!w.sessionStorage.getItem("pygebra-raices-historial-newton_raphson"),"Historiales separados por método");
        }],
        ["Historial compara pares de puntos iniciales", async(w,frame)=>{
            w.sessionStorage.removeItem("pygebra-raices-historial-secante");
            w=await resolver(frame);ok(q(w,"#raices-historial").hidden,"Oculto con una ejecución");
            w=await resolver(frame,{x0:"0",x1:"3"});
            const h=q(w,"#raices-historial"),filas=[...h.querySelectorAll("tbody tr:not(:first-child)")];
            ok(!h.hidden&&filas.length===2,"Dos ejecuciones en un grupo");
            ok(qa(w,"#raices-historial thead th").map(t=>t.textContent).join("|")==="x₀, x₁|Aproximación|Iteraciones|Criterio de parada|Error absoluto|Residuo|Tolerancia|","Columnas");
            ok(filas.map(f=>[...f.cells[0].querySelectorAll("span")].map(s=>Number(s.dataset.raicesNumero)).join(";")).join()==="1;2,0;3","Puntos iniciales");
            ok(filas[0].querySelector("button").getAttribute("aria-label")==="Ver la ejecución con x₀ = 1, x₁ = 2","Etiqueta accesible");
            await navegar(frame,()=>filas[0].querySelector("button").click());w=frame.contentWindow;
            await esperar(()=>lista(w));
            ok(datos(w).x0===1&&datos(w).x1===2,"«Ver» recupera la ejecución");
        }],
        ["Denominador nulo y raíz inicial: explicación sin pasos inventados", async(w,frame)=>{
            w=await resolver(frame,{funcion:"x^2-4",x0:"-1",x1:"1"});
            ok(datos(w).estado==="denominador"&&q(w,"#results-title").textContent==="Método no aplicable","Secante horizontal");
            ok(!q(w,"#iteracion-raices")&&q(w,"#resultado").textContent.includes("la secante es horizontal"),"Explica el denominador nulo");
            w=await resolver(frame,{funcion:"x^2+1",x0:"0",x1:"1"});
            ok(datos(w).estado==="denominador"&&q(w,"#iteracion-raices").max==="1","Se detiene tras una iteración");
            ok(q(w,"#paso-breve").textContent.includes("Se detiene"),"Explica la parada");
            w=await resolver(frame,{funcion:"x^2-4",x0:"3",x1:"2"});
            ok(!q(w,"#iteracion-raices")&&g(w).data[1].x[0]===2,"Raíz inicial marcada sin pasos");
        }],
        ["Teclado matemático solo en la función", async w=>{
            const c=q(w,'[name="funcion"]');c.focus();
            await esperar(()=>q(w,".math-keyboard").hasAttribute("data-abierto"));
            q(w,'[data-insercion="x²"]').click();
            ok(c.value==="x²"&&w.document.activeElement===c,"Inserción y foco en la función");
            q(w,'[name="x1"]').focus();ok(!q(w,".math-keyboard").hasAttribute("data-abierto"),"Oculto en x₁");
        }],
        ["Estilos, temas y responsive con geometría real", async(w,frame)=>{
            w=await resolver(frame);const raiz=w.document.documentElement;
            for(const estilo of ["estudio","minimalista"]) for(const tema of ["light","dark"]) for(const ancho of [1280,744,390]){
                raiz.dataset.estilo=estilo;raiz.dataset.theme=tema;frame.style.width=ancho+"px";
                await w.Plotly.Plots.resize(g(w));
                await esperar(()=>g(w).layout.paper_bgcolor===w.getComputedStyle(raiz).getPropertyValue("--color-surface").trim());
                ok(raiz.scrollWidth<=raiz.clientWidth+1,"Sin desborde "+estilo+tema+ancho);
                ok(g(w).getBoundingClientRect().width>200,"Gráfica visible");
                const caja=s=>q(w,s).getBoundingClientRect(),l=caja(".raices-lienzo"),e=caja(".raices-recorrido"),t=caja("#raices-tabla-marco");
                if(ancho===1280) ok(t.top>=l.bottom&&t.right<=e.left&&Math.abs(t.left-l.left)<1,"Tabla bajo la gráfica "+estilo+tema);
                else ok(t.top>=e.bottom&&e.top>=l.bottom,"Columna única "+estilo+tema+ancho);
                const sel=caja(".metodos-abiertos");ok(sel.right<=raiz.clientWidth+1,"Selector visible "+estilo+ancho);
            }
        }],
        ["Precisión de lectura conserva cálculos", async(w,frame)=>{
            w=await resolver(frame);const original=q(w,"#datos-raices").textContent;
            const s=q(w,"#raices-decimales");s.value="completa";s.dispatchEvent(new w.Event("change"));
            ok(q(w,"#datos-raices").textContent===original,"JSON intacto");
            ok(qa(w,"[data-raices-numero]").every(n=>Number(n.textContent)===Number(n.dataset.raicesNumero)),"Valor almacenado");
        }],
    ];
    let aprobados=0;
    for(const [nombre,probar] of casos){
        const item=document.createElement("li");document.getElementById("resultados").append(item);(window.preferencias ? window.preferencias.guardar("pygebra-raices-decimales", "6") : localStorage.setItem("pygebra-raices-decimales", "6"));
        const frame=document.createElement("iframe");frame.title=nombre;frame.style.cssText="width:100%;height:700px";document.body.append(frame);
        try{await new Promise(r=>{frame.onload=r;frame.src=RUTA;});await probar(frame.contentWindow,frame);item.textContent="OK: "+nombre;aprobados++;}
        catch(e){item.textContent="FALLO: "+nombre+": "+e.message;}frame.remove();
    }
    document.getElementById("total").textContent=`${aprobados}/${casos.length} aprobados`;
})();
