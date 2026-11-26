/* Smoke repetible del controlador real, con las mismas aserciones en cada concepto. */
document.querySelector('#run').addEventListener('click', async () => {
  const run = document.querySelector('#run');
  const frame = document.querySelector('#subject');
  const summary = document.querySelector('#summary');
  const checks = document.querySelector('#checks');
  run.disabled = true;
  checks.replaceChildren();
  frame.hidden = false;
  let passed = 0;
  const check = (condition, description) => {
    if (!condition) throw new Error(description);
    const li = document.createElement('li');
    li.textContent = `PASS — ${description}`;
    checks.append(li);
    passed++;
  };
  try {
    for (const concept of ['patio', 'trama', 'prisma']) {
      summary.textContent = `Comprobando ${concept}…`;
      await new Promise((resolve, reject) => {
        frame.onload = resolve;
        frame.onerror = () => reject(new Error(`No se pudo cargar ${concept}.`));
        frame.src = `${concept}.html`;
      });
      const d = frame.contentDocument;
      if (!d) throw new Error('Usa el servidor HTTP local para permitir la prueba entre páginas.');
      const $ = selector => d.querySelector(selector);
      const navigate = async selector => {
        const changed = new Promise(resolve => frame.contentWindow.addEventListener('hashchange', resolve, {once:true}));
        $(selector).click();
        await changed;
      };
      check($('#sound').getAttribute('aria-pressed') === 'false', `${concept}: audio inicialmente apagado`);
      await navigate('a[data-nav="menu"]');
      check(d.activeElement.tagName === 'H1', `${concept}: foco al navegar`);
      $('#search').value = 'matrices';
      const changed = new Promise(resolve => frame.contentWindow.addEventListener('hashchange', resolve, {once:true}));
      $('#search-form').requestSubmit();
      await changed;
      check(Boolean($('.tool-launch')), `${concept}: búsqueda y acceso al ejemplo`);
      await navigate('.tool-launch');
      for (const [index, expected] of [['0','6, 8, 10, 12'], ['1','3/4, 2, 0, 1'], ['2','4, 4, 10, 8']]) {
        $('#example').value = index;
        $('#example').dispatchEvent(new Event('change'));
        check($('#result').hidden, `${concept}: cambio de ejemplo ${index} retira resultado anterior`);
        $('#show').click();
        check($('#result-matrix .matrix').getAttribute('aria-label').includes(expected), `${concept}: resultado ${index}`);
        check(d.activeElement.id === 'reason-title', `${concept}: foco en procedimiento ${index}`);
      }
      check($('#previous').disabled, `${concept}: límite inicial`);
      $('[data-step="3"]').click();
      check($('#next').disabled && $('#step-count').textContent === '4 de 4', `${concept}: límite final`);
      check($('#step-equation').textContent === '3 × 0 + 4 × 2 = 8', `${concept}: producto fila por columna`);
      $('#example').value = '1';
      $('#example').dispatchEvent(new Event('change'));
      $('#show').click();
      $('#decimal').click();
      check($('#result-matrix .matrix').getAttribute('aria-label').includes('0.75, 2, 0, 1'), `${concept}: decimal`);
      $('#exact').click();
      check($('#result-matrix .matrix').getAttribute('aria-label').includes('3/4, 2, 0, 1'), `${concept}: vuelta al valor exacto`);
      check($('input[readonly]') && [...d.querySelectorAll('.input-matrix input')].every(i=>i.readOnly), `${concept}: datos de demostración de solo lectura`);
    }
    summary.textContent = `${passed}/${passed} PASS. Sin errores en las comprobaciones.`;
  } catch (error) {
    summary.textContent = `FAIL después de ${passed} comprobaciones: ${error.message}`;
  } finally {
    frame.onload = null;
    frame.onerror = null;
    run.disabled = false;
  }
});
