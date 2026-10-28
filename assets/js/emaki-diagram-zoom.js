/* Enlarge the actual explanatory diagram while preserving its page-local defs. */
(() => {
  'use strict';
  let opener;
  const dialog = document.createElement('dialog');
  dialog.className = 'im-diagram-dialog';
  dialog.setAttribute('aria-label', '説明図の拡大表示');
  dialog.innerHTML = '<div class="im-diagram-toolbar"><button type="button" data-action="out" aria-label="図を縮小">縮小</button><button type="button" data-action="in" aria-label="図を拡大">拡大</button><button type="button" data-action="close">閉じる</button></div><p>図は上下・左右にスクロールできます。文字情報は元のページでも読めます。</p><div class="im-diagram-scroll" tabindex="0" role="region" aria-label="拡大した説明図"></div>';
  document.body.append(dialog);
  const canvas = dialog.querySelector('.im-diagram-scroll');
  let width = 0, height = 0, scale = 1;
  function size() {
    const svg = canvas.querySelector('svg,img');
    if (svg) {
      svg.style.width = `${Math.round(width * scale)}px`;
      svg.style.height = `${Math.round(height * scale)}px`;
    }
  }
  function copiedDiagram(original) {
    const copy = original.cloneNode(true);
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const copied = new Set(Array.from(copy.querySelectorAll('[id]'), e => e.id));
    const pending = [copy];
    // Resolve markers, gradients and patterns defined elsewhere on this page.
    while (pending.length) {
      const root = pending.shift();
      for (const node of [root, ...root.querySelectorAll('*')]) {
        for (const attr of node.attributes || []) {
          const matches = Array.from(attr.value.matchAll(/url\(\s*["']?#([^\s)'";]+)["']?\s*\)/g), m => m[1]);
          if ((attr.name === 'href' || attr.name === 'xlink:href') && attr.value.startsWith('#')) matches.push(attr.value.slice(1));
          for (const id of matches) {
            if (copied.has(id)) continue;
            const dependency = document.getElementById(id);
            if (!dependency || dependency.namespaceURI !== 'http://www.w3.org/2000/svg') continue;
            copied.add(id);
            const addition = dependency.cloneNode(true);
            defs.append(addition); pending.push(addition);
          }
        }
      }
    }
    copy.prepend(defs);
    // Keep IDs unique so marker references cannot resolve back into the original.
    const ids = new Map(Array.from(copy.querySelectorAll('[id]'), e => [e.id, `im-zoom-${e.id}`]));
    if (copy.id) ids.set(copy.id, `im-zoom-${copy.id}`);
    for (const node of [copy, ...copy.querySelectorAll('*')]) {
      for (const attr of Array.from(node.attributes || [])) {
        let value = attr.value;
        if (attr.name === 'id') value = ids.get(value) || value;
        else {
          value = value.replace(/url\(\s*["']?#([^\s)'";]+)["']?\s*\)/g, (all, id) => ids.has(id) ? `url(#${ids.get(id)})` : all);
          if ((attr.name === 'href' || attr.name === 'xlink:href') && value.startsWith('#') && ids.has(value.slice(1))) value = `#${ids.get(value.slice(1))}`;
          if (attr.name === 'aria-labelledby' || attr.name === 'aria-describedby') value = value.split(/\s+/).map(id => ids.get(id) || id).join(' ');
        }
        node.setAttribute(attr.name, value);
      }
    }
    return copy;
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('button[data-emaki-zoom]');
    if (!button) return;
    const original = document.querySelector(`[data-emaki-zoom-target="${button.dataset.emakiZoom}"]`);
    if (!original) return;
    const view = original.viewBox?.baseVal;
    width = Number(original.dataset.emakiZoomWidth) || view?.width || original.naturalWidth || Number(original.getAttribute('width')) || 800;
    height = Number(original.dataset.emakiZoomHeight) || view?.height || original.naturalHeight || Number(original.getAttribute('height')) || 500;
    scale = 1.25;
    if (original.tagName.toLowerCase() === 'img') {
      const image = document.createElement('img');
      image.src = original.currentSrc || original.src;
      image.alt = original.alt;
      canvas.replaceChildren(image);
    } else canvas.replaceChildren(copiedDiagram(original));
    size();
    opener = button; dialog.showModal(); canvas.focus();
  });
  dialog.addEventListener('click', event => {
    const action = event.target.closest('[data-action]')?.dataset.action;
    if (action === 'close') dialog.close();
    if (action === 'in') { scale = Math.min(4, scale + .25); size(); }
    if (action === 'out') { scale = Math.max(.75, scale - .25); size(); }
  });
  dialog.addEventListener('close', () => { canvas.replaceChildren(); opener?.focus(); });
  document.documentElement.classList.add('im-diagram-zoom-ready');
})();
