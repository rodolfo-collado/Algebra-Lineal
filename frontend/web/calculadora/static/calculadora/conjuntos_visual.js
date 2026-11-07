/* Solo dibuja datos del motor; las operaciones y selección de regiones llegan calculadas. */
(() => {
    'use strict';
    const ajuste = document.querySelector('[data-ajuste-cardinalidades]');
    if (ajuste) for (const nombre of ['numero','modo']) ajuste.form.elements[nombre].addEventListener('change', () => ajuste.form.requestSubmit(ajuste));
    const datos = document.getElementById('conjuntos-resultado-datos');
    if (!datos) return;
    const resultado = JSON.parse(datos.textContent);
    const ns = 'http://www.w3.org/2000/svg';
    const svg = (tipo, attrs = {}, texto) => {
        const nodo = document.createElementNS(ns,tipo);
        for (const [k,v] of Object.entries(attrs)) nodo.setAttribute(k,v);
        if (texto !== undefined) nodo.textContent = texto;
        return nodo;
    };
    const boton = (texto, accion) => {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'btn btn-secondary';
        b.textContent = texto; b.addEventListener('click',accion); return b;
    };
    const recta = document.querySelector('[data-recta]');
    if (recta && resultado.recta) {
        const grafica = svg('svg',{viewBox:'0 0 100 32',width:'100%',role:'img','aria-label':'Intervalos del resultado en la recta real',style:'max-height:300px'});
        grafica.append(svg('line',{x1:0,y1:14,x2:100,y2:14,stroke:'currentColor','stroke-width':0.3}));
        const detalle = document.createElement('p'); detalle.setAttribute('aria-live','polite');
        for (const [indice,t] of resultado.recta.tramos.entries()) {
            const grupo = svg('g',{'data-tramo':indice});
            grupo.append(svg('line',{x1:t.x1,y1:14,x2:t.x2,y2:14,stroke:'#16758a','stroke-width':1.2}));
            for (const [x,valor,cerrado,lado] of [[t.x1,t.inferior,t.cerrado_inferior,-1],[t.x2,t.superior,t.cerrado_superior,1]]) {
                if (valor === null) grupo.append(svg('path',{d:`M ${x-lado*2} 12 L ${x} 14 L ${x-lado*2} 16`,fill:'none',stroke:'currentColor','stroke-width':0.5}));
                else grupo.append(svg('circle',{cx:x,cy:14,r:1,fill:cerrado?'#16758a':'white',stroke:'#16758a','stroke-width':0.4}));
                grupo.append(svg('text',{x,y:23,'font-size':3,'text-anchor':'middle'},valor ?? (lado < 0 ? '−∞' : '+∞')));
            }
            grafica.append(grupo);
            recta.append(boton(`Tramo ${indice+1}`,() => {detalle.textContent = `${t.cerrado_inferior?'[':'('}${t.inferior ?? '−∞'}, ${t.superior ?? '+∞'}${t.cerrado_superior?']':')'}`; grupo.setAttribute('stroke-width','2');}));
        }
        if (!resultado.recta.tramos.length) detalle.textContent = 'El resultado es vacío: no hay puntos en la recta.';
        let ancho = 100, inicio = 0;
        const actualizar = () => grafica.setAttribute('viewBox',`${inicio} 0 ${ancho} 32`);
        recta.prepend(grafica);
        recta.append(boton('Acercar',() => {if(ancho>12){inicio+=ancho/4;ancho/=2;actualizar();}}),
            boton('Alejar',() => {inicio-=ancho/2;ancho=Math.min(200,ancho*2);actualizar();}),
            boton('←',() => {inicio-=ancho/4;actualizar();}), boton('→',() => {inicio+=ancho/4;actualizar();}),
            boton('Restablecer',() => {inicio=0;ancho=100;actualizar();}),detalle);
    }
    const venn = document.querySelector('[data-venn]');
    if (venn && resultado.venn) {
        const {nombres,regiones} = resultado.venn;
        const tres = nombres.length === 3;
        const centros = tres ? [[42,35],[66,35],[54,56]] : [[42,43],[67,43]];
        const radio = tres ? 23 : 25;
        const grafica = svg('svg',{viewBox:'0 0 110 90',width:'100%',role:'img','aria-label':`Diagrama de Venn de ${nombres.join(', ')}`,style:'max-height:460px'});
        const defs = svg('defs'); grafica.append(defs);
        const detalle = document.createElement('p'); detalle.setAttribute('aria-live','polite');
        const anchors = tres ? [[7,85],[25,32],[83,32],[54,22],[54,76],[38,55],[70,55],[54,44]] : [[7,82],[28,43],[80,43],[54,43]];
        const etiquetas = [];
        for (const r of regiones) {
            const id = `conjuntos-region-${r.mascara}`;
            const mask = svg('mask',{id,x:0,y:0,width:110,height:90,maskUnits:'userSpaceOnUse'});
            mask.append(svg('rect',{width:110,height:90,fill:'white'}));
            let grupo = svg('g'); const principal = grupo;
            centros.forEach(([cx,cy],i) => {
                if (r.pertenece[i]) {
                    const clipId = `${id}-incluye-${i}`;
                    const clip = svg('clipPath',{id:clipId}); clip.append(svg('circle',{cx,cy,r:radio})); defs.append(clip);
                    const hijo = svg('g',{'clip-path':`url(#${clipId})`}); grupo.append(hijo); grupo=hijo;
                } else mask.append(svg('circle',{cx,cy,r:radio,fill:'black'}));
            });
            defs.append(mask);
            grupo.append(svg('rect',{x:1,y:1,width:108,height:87,fill:r.seleccionada?'#73c5bd':'#f5f1e7',mask:`url(#${id})`,'data-region':r.mascara}));
            grafica.append(principal);
            const nombre = nombres.map((n,i) => r.pertenece[i]?n:`${n}ᶜ`).join(' ∩ ');
            etiquetas.push({r,nombre});
        }
        grafica.append(svg('rect',{x:1,y:1,width:108,height:87,fill:'none',stroke:'currentColor','stroke-width':0.4}));
        centros.forEach(([cx,cy],i) => {grafica.append(svg('circle',{cx,cy,r:radio,fill:'none',stroke:'currentColor','stroke-width':0.4}));grafica.append(svg('text',{x:cx,y:cy-radio-2,'text-anchor':'middle','font-size':4},nombres[i]));});
        for (const {r,nombre} of etiquetas) {
            const [x,y] = anchors[r.mascara];
            grafica.append(svg('text',{x,y,'text-anchor':'middle','font-size':3},r.cantidad ?? '?'));
            venn.append(boton(nombre,() => {detalle.textContent = `${nombre}: ${r.cantidad ?? 'cardinalidad desconocida'}${r.etiquetas.length?'; '+r.etiquetas.join(', '):''}. ${r.seleccionada?'Región seleccionada por la expresión.':'Región no seleccionada por la expresión.'}`;}));
        }
        venn.prepend(grafica); venn.append(detalle);
    }
})();
