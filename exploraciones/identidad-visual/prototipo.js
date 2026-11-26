/* Estudio independiente: no importa ni llama al motor matemático de PyGebra. */
(() => {
  'use strict';
  const concept = document.body.dataset.concept;
  const concepts = {
    patio: {name:'Patio', title:'Las ideas tienen un lugar.', lead:'Entra, elige un tema y descubre lo que pasa entre una pregunta y su respuesta.', action:'Entrar a PyGebra', menu:'¿Qué exploramos hoy?', tool:'Una suma, cuatro pequeños encuentros.'},
    trama: {name:'Trama', title:'Pensar deja huella.', lead:'Una expresión. Un hilo de razonamiento. Un espacio para entender cómo llegaste hasta aquí.', action:'Abrir el cuaderno', menu:'Tu índice de posibilidades.', tool:'El razonamiento, a la vista.'},
    prisma: {name:'Prisma', title:'Mira las relaciones.', lead:'Las matemáticas cobran sentido cuando conectas lo que conoces con lo que estás por descubrir.', action:'Entrar al laboratorio', menu:'Elige un punto de partida.', tool:'De los datos a la estructura.'}
  };
  const c = concepts[concept];
  const mark = '<svg class="mark" viewBox="0 0 64 64" aria-hidden="true"><path fill="currentColor" d="M2 12H62V34H22V42H40V40L56 46L40 52V50H14V26H54V20H2Z"/></svg>';
  const miniMatrix = (values, label) => `<span class="matrix" role="img" aria-label="${label}: ${values.join(', ')}">${values.map(v=>`<span>${v}</span>`).join('')}</span>`;
  const areas = [
    {id:'algebra',name:'Álgebra lineal',symbol:'[aᵢⱼ]',description:'Las piezas y sus transformaciones.', topics:'Matrices · Vectores · Sistemas',tools:['Operaciones con matrices','Determinantes','Reducción por filas','Resolver Ax = b']},
    {id:'numeros',name:'Sistemas numéricos',symbol:'101₂',description:'Un número, distintas maneras de verlo.',topics:'Bases numéricas · Numeración romana',tools:['Conversión de bases','Numeración romana']},
    {id:'conjuntos',name:'Conjuntos',symbol:'{a, b}',description:'Pertenecer. Incluir. Relacionar.',topics:'Conjuntos finitos · Relaciones',tools:['Relaciones entre conjuntos']}
  ];
  // shortcut: ejemplos precalculados y de solo lectura; conectar al backend solo tras elegir una dirección.
  const examples = [
    {name:'Suma de matrices',expression:'A + B',a:['1','2','3','4'],b:['5','6','7','8'],result:['6','8','10','12'],decimal:['6','8','10','12'],rule:'Misma posición, misma pareja. Sumamos cada entrada de A con la entrada correspondiente de B.',steps:['1 + 5 = 6','2 + 6 = 8','3 + 7 = 10','4 + 8 = 12']},
    {name:'Suma con fracciones',expression:'A + B',a:['1/2','0','1','3/4'],b:['1/4','2','−1','1/4'],result:['3/4','2','0','1'],decimal:['0.75','2','0','1'],rule:'Conservamos el valor exacto. En la primera entrada usamos denominador común: 1/2 = 2/4.',steps:['1/2 + 1/4 = 3/4','0 + 2 = 2','1 + (−1) = 0','3/4 + 1/4 = 1']},
    {name:'Producto de matrices',expression:'AB',a:['1','2','3','4'],b:['2','0','1','2'],result:['4','4','10','8'],decimal:['4','4','10','8'],rule:'Fila por columna. Cada entrada del producto suma los productos de una fila de A y una columna de B.',steps:['1 × 2 + 2 × 1 = 4','1 × 0 + 2 × 2 = 4','3 × 2 + 4 × 1 = 10','3 × 0 + 4 × 2 = 8']}
  ];
  let exampleIndex = 0, step = 0, decimal = false, soundOn = false, audio;
  const tones = {patio:[523.25,659.25,783.99],trama:[440,550,660],prisma:[392,587.33,784]};
  async function sound(kind) {
    if (!soundOn) return;
    try {
      audio ||= new AudioContext();
      await audio.resume();
      if (!soundOn || document.hidden) return;
      const now=audio.currentTime, frequencies=tones[concept];
      const notes=kind==='confirm' ? frequencies.slice(1) : [frequencies[kind==='step'?1:0]];
      notes.forEach((frequency,i)=>{
        const osc=audio.createOscillator(),gain=audio.createGain(),start=now+i*0.055;
        osc.type=concept==='trama'?'triangle':'sine'; osc.frequency.value=frequency;
        gain.gain.setValueAtTime(0,start); gain.gain.linearRampToValueAtTime(0.035,start+0.008);
        gain.gain.exponentialRampToValueAtTime(0.0001,start+0.12);
        osc.connect(gain);gain.connect(audio.destination);osc.start(start);osc.stop(start+0.13);
        osc.onended=()=>{osc.disconnect();gain.disconnect();};
      });
    } catch {
      soundOn=false;syncSound();document.querySelector('#status').textContent='No se pudo activar el audio. Puedes continuar en silencio.';
    }
  }
  const art = concept==='patio' ? `<div class="patio-art" aria-hidden="true"><div class="art-channel one">${miniMatrix(['1','2','3','4'],'')}</div><div class="art-channel two">∈</div><div class="art-channel three">x + y</div><div class="art-channel four">${mark}</div><span class="art-caption">Cada paso cuenta.</span></div>` : concept==='trama' ? `<div class="trama-art" aria-hidden="true"><span class="pencil-note">Todo empieza con una pregunta.</span><div class="written-formula">A + B</div><div class="thread"></div><div class="written-answer">Entender<br>también es<br>un resultado.</div><span class="paper-tab">PyGebra / Cuaderno de ideas</span></div>` : `<div class="prisma-art" aria-hidden="true"><svg viewBox="0 0 500 430"><g fill="none" stroke="currentColor" stroke-width="1"><path d="M70 300 250 75 440 285 250 390Z M70 300 440 285 M250 75V390 M70 300 250 185 440 285 M250 185 250 390"/><ellipse cx="250" cy="270" rx="190" ry="100"/></g><g fill="currentColor"><circle cx="250" cy="75" r="7"/><circle cx="70" cy="300" r="7"/><circle cx="440" cy="285" r="7"/></g></svg><span class="node node-a">A</span><span class="node node-b">B</span><span class="node node-c">A + B</span><span class="art-caption">Una operación conecta las piezas.</span></div>`;
  const areaCards = areas.map(a=>`<a class="area-card area-${a.id}" href="#menu/${a.id}"><span class="area-art" aria-hidden="true">${a.symbol}</span><div class="area-copy"><h2>${a.name}</h2><p>${a.description}</p><small>${a.topics}</small></div><span class="area-open" aria-hidden="true">↗</span></a>`).join('');
  document.body.innerHTML = `
    <a class="skip" href="#main">Saltar al contenido</a>
    <div class="study-bar"><a href="index.html">Comparar propuestas</a><span>Estudio visual / ${c.name}</span><span>Prototipo independiente</span></div>
    <header class="topbar"><a class="brand" href="#bienvenida" aria-label="PyGebra, bienvenida">${mark}<span translate="no">PyGebra</span></a><nav aria-label="Navegación principal"><a href="#menu" data-nav="menu">Áreas</a><a href="#herramienta" data-nav="herramienta">Matrices</a><button id="sound" type="button" aria-pressed="false">Sonido: apagado</button></nav></header>
    <main id="main" tabindex="-1">
      <section class="screen welcome" data-screen="bienvenida"><div class="welcome-copy"><h1 tabindex="-1">${c.title}</h1><p class="lead">${c.lead}</p><a class="primary" href="#menu">${c.action}</a><p class="welcome-note">Aprende resolviendo, paso a paso.</p></div>${art}<div class="welcome-footer"><span>Precisión para resolver.</span><span>Espacio para comprender.</span></div></section>
      <section class="screen menu-screen" data-screen="menu" hidden><div class="menu-heading"><h1 tabindex="-1">${c.menu}</h1><p class="lead">Elige un área o busca por lo que quieres resolver.</p></div><form id="search-form" role="search"><label for="search">Buscar una herramienta</label><div class="search-line"><input id="search" name="q" type="search" autocomplete="off" placeholder="Por ejemplo: matrices…"><button type="submit">Buscar</button></div></form><div class="areas">${areaCards}<div class="upcoming"><span aria-hidden="true">∫</span><div><strong>Cálculo</strong><small>Próximamente en PyGebra</small></div></div></div><section id="area-detail" class="area-detail" aria-label="Herramientas del área" hidden></section><p class="menu-foot">Este estudio permite recorrer Matrices. Las demás herramientas se muestran como referencia de navegación.</p></section>
      <section class="screen tool-screen" data-screen="herramienta" hidden><nav class="breadcrumbs" aria-label="Ruta de navegación"><a href="#menu">Áreas</a><span aria-hidden="true">/</span><a href="#menu/algebra">Álgebra lineal</a><span aria-hidden="true">/</span><span aria-current="page">Matrices</span></nav><div class="tool-heading"><div><h1 tabindex="-1">Operaciones con matrices</h1><p class="lead">${c.tool}</p></div><span class="demo-label">Ejemplos guiados · solo lectura</span></div><div class="workbench"><section class="input-panel" aria-labelledby="input-title"><h2 id="input-title">Las piezas</h2><label for="example">Ejemplo</label><select id="example" name="example">${examples.map((e,i)=>`<option value="${i}">${e.name}</option>`).join('')}</select><p class="help">Elige un ejemplo precalculado. Estas celdas no se editan.</p><div id="operands" class="operands"></div><div class="expression"><label for="expression">Expresión</label><input id="expression" name="expression" readonly autocomplete="off" spellcheck="false"></div><button class="primary" id="show" type="button">Mostrar procedimiento</button><details class="help-details"><summary>¿Por qué estas dimensiones?</summary><p>La suma necesita matrices de la misma forma. Para AB, las columnas de A deben coincidir con las filas de B. Los ejemplos son de 2 × 2.</p></details></section><section class="reasoning" aria-labelledby="reason-title"><h2 id="reason-title">El hilo del cálculo</h2><div id="reason-empty"><span class="empty-symbol" aria-hidden="true">${concept==='prisma'?'A ⟷ B':concept==='trama'?'A + B = ?':'[ ? ]'}</span><p>Las piezas están listas.<br>Abre el procedimiento para ver cómo se relacionan.</p></div><div id="procedure" hidden><p id="rule"></p><ol class="step-track" aria-label="Entradas del resultado">${[1,2,3,4].map((n,i)=>`<li><button type="button" data-step="${i}" aria-label="Ver fila ${Math.floor(i/2)+1}, columna ${i%2+1}">${n}</button></li>`).join('')}</ol><div class="step-view"><p id="step-location"></p><p id="step-equation" class="equation"></p><p id="step-explanation"></p></div><div class="step-actions"><button id="previous" type="button">Anterior</button><span id="step-count"></span><button id="next" type="button">Siguiente</button></div><details id="all-steps"><summary>Ver el procedimiento completo</summary><ol id="all-equations"></ol></details></div></section><section class="result-panel" aria-labelledby="result-title"><h2 id="result-title">El resultado</h2><p id="result-empty">Aparecerá junto al razonamiento.</p><div id="result" hidden><div class="format-options" role="group" aria-label="Formato del resultado"><button id="exact" type="button" aria-pressed="true">Exacto</button><button id="decimal" type="button" aria-pressed="false">Decimal</button></div><div id="result-matrix"></div><p class="result-caption">Una matriz de 2 × 2.<br>Cada entrada tiene su explicación.</p></div></section></div><p class="prototype-note">Demostración de experiencia. Sin conexión con las calculadoras ni con el motor de PyGebra.</p></section>
    </main><p id="status" class="sr-only" role="status" aria-live="polite" aria-atomic="true"></p><noscript>Activa JavaScript para recorrer este prototipo. La calculadora de producción conserva su funcionamiento independiente.</noscript>`;
  const $ = s=>document.querySelector(s);
  function syncSound() { $('#sound').setAttribute('aria-pressed',String(soundOn)); $('#sound').textContent=`Sonido: ${soundOn?'activado':'apagado'}`; }
  $('#sound').addEventListener('click',()=>{soundOn=!soundOn;syncSound();if(soundOn)sound('confirm');else if(audio)audio.suspend();});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&audio)audio.suspend();});
  function operands() {
    const e=examples[exampleIndex];
    $('#operands').innerHTML=['a','b'].map(key=>`<fieldset class="operand"><legend>${key.toUpperCase()} <small>2 × 2</small></legend><div class="input-matrix">${e[key].map((v,i)=>`<input name="${key}${i}" aria-label="Matriz ${key.toUpperCase()}, fila ${Math.floor(i/2)+1}, columna ${i%2+1}" value="${v}" readonly autocomplete="off" spellcheck="false">`).join('')}</div></fieldset>`).join('');
    $('#expression').value=e.expression;
  }
  function updateStep() {
    const e=examples[exampleIndex],row=Math.floor(step/2)+1,col=step%2+1;
    $('#step-location').textContent=`Fila ${row}, columna ${col}`;
    $('#step-equation').textContent=e.steps[step];
    $('#step-explanation').textContent=exampleIndex===2?`Multiplica la fila ${row} de A por la columna ${col} de B y suma los productos.`:`Combina la entrada de la fila ${row}, columna ${col} de cada matriz.`;
    $('#step-count').textContent=`${step+1} de 4`;
    $('#previous').disabled=step===0;$('#next').disabled=step===3;
    document.querySelectorAll('[data-step]').forEach((b,i)=>{if(i===step)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');});
    $('#result-matrix').innerHTML=miniMatrix(decimal?e.decimal:e.result,'Resultado por filas');
    $('#result-matrix .matrix').children[step].classList.add('selected-cell');
  }
  function setStep(n) { step=Math.max(0,Math.min(3,n));updateStep();$('#status').textContent=`Paso ${step+1} de 4. ${examples[exampleIndex].steps[step]}`;sound('step'); }
  $('#show').addEventListener('click',()=>{
    step=0;$('#reason-empty').hidden=true;$('#procedure').hidden=false;$('#result-empty').hidden=true;$('#result').hidden=false;
    $('#rule').textContent=examples[exampleIndex].rule;
    $('#all-equations').innerHTML=examples[exampleIndex].steps.map(s=>`<li>${s}</li>`).join('');
    updateStep();$('#reason-title').tabIndex=-1;$('#reason-title').focus();$('#status').textContent='Procedimiento y resultado disponibles. Paso 1 de 4.';sound('confirm');
  });
  $('#example').addEventListener('change',()=>{
    exampleIndex=Number($('#example').value);decimal=false;step=0;operands();
    $('#procedure').hidden=true;$('#result').hidden=true;$('#reason-empty').hidden=false;$('#result-empty').hidden=false;
    $('#all-steps').open=false;$('#exact').setAttribute('aria-pressed','true');$('#decimal').setAttribute('aria-pressed','false');
    $('#status').textContent='Ejemplo cambiado. Abre su procedimiento para ver el nuevo resultado.';sound('step');
  });
  document.querySelectorAll('[data-step]').forEach(b=>b.addEventListener('click',()=>setStep(Number(b.dataset.step))));
  $('#previous').addEventListener('click',()=>setStep(step-1));$('#next').addEventListener('click',()=>setStep(step+1));
  for(const mode of ['exact','decimal'])$('#'+mode).addEventListener('click',()=>{
    decimal=mode==='decimal';$('#exact').setAttribute('aria-pressed',String(!decimal));$('#decimal').setAttribute('aria-pressed',String(decimal));updateStep();$('#status').textContent=`Resultado en formato ${decimal?'decimal':'exacto'}.`;sound('step');
  });
  function renderArea(id) {
    const a=areas.find(a=>a.id===id),panel=$('#area-detail');panel.hidden=!a;if(!a)return;
    panel.innerHTML=`<h2>${a.name}</h2><ul class="tool-list">${a.tools.map((t,i)=>`<li>${id==='algebra'&&i===0?`<a class="tool-launch" href="#herramienta">${t}<span>Abrir ejemplo guiado</span></a>`:`<span>${t}<small>Fuera de este prototipo</small></span>`}</li>`).join('')}</ul>`;
  }
  function route(initial=false) {
    const [requested,id]=location.hash.slice(1).split('/'),screen=['bienvenida','menu','herramienta'].includes(requested)?requested:'bienvenida';
    document.body.dataset.view=screen;
    document.querySelectorAll('[data-screen]').forEach(s=>s.hidden=s.dataset.screen!==screen);
    document.querySelectorAll('[data-nav]').forEach(a=>{if(a.dataset.nav===screen)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
    document.title=`${screen==='bienvenida'?'Bienvenida':screen==='menu'?'Áreas':'Matrices'} · ${c.name} · PyGebra`;
    if(screen==='menu')renderArea(id);
    if(!initial){const target=screen==='menu'&&id?$('#area-detail h2'):$(`[data-screen="${screen}"] h1`);if(target){target.tabIndex=-1;target.focus();}sound('navigate');}
  }
  $('#search-form').addEventListener('submit',event=>{
    event.preventDefault();const q=$('#search').value.trim().normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
    const a=areas.find(a=>[a.name,...a.tools].join(' ').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().includes(q));
    if(!q){$('#status').textContent='Escribe el nombre de un área o una herramienta.';$('#search').focus();return;}
    if(a){if(location.hash===`#menu/${a.id}`)renderArea(a.id);else location.hash=`menu/${a.id}`;$('#status').textContent=`Herramientas de ${a.name}.`;}
    else{$('#area-detail').hidden=false;$('#area-detail').innerHTML='<h2>Sin coincidencias</h2><p>Prueba con matrices, bases o conjuntos.</p>';$('#status').textContent='Sin coincidencias. Prueba con matrices, bases o conjuntos.';}
  });
  window.addEventListener('hashchange',()=>route());operands();route(true);
})();
