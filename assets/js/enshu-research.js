(() => {
  'use strict';
  const source = document.getElementById('research-records');
  if (!source) return;
  const rows = JSON.parse(source.textContent);
  const scope = document.getElementById('lab-scope');
  const region = document.getElementById('lab-region');
  const body = document.getElementById('lab-table');
  const frequencies = new Map();
  const regionCounts = new Map();
  for (const row of rows) {
    frequencies.set(row.form, (frequencies.get(row.form) || 0) + 1);
    regionCounts.set(row.village, (regionCounts.get(row.village) || 0) + 1);
  }
  const largest = new Set([...regionCounts].sort((a, b) => b[1] - a[1]).slice(0, 3).map(([name]) => name));
  function render() {
    const selected = rows.filter(row =>
      (!region.value || row.village === region.value) &&
      (scope.value !== 'repeated' || frequencies.get(row.form) > 1) &&
      (scope.value !== 'outside' || !largest.has(row.village)));
    const grouped = new Map();
    for (const row of selected) {
      if (!grouped.has(row.village)) grouped.set(row.village, { count: 0, forms: new Set() });
      const group = grouped.get(row.village);
      group.count += 1;
      group.forms.add(row.form);
    }
    document.getElementById('lab-status').textContent = `${selected.length}記録 ／ ${new Set(selected.map(row => row.form)).size}原表記 ／ ${grouped.size}地域名ラベル`;
    document.getElementById('lab-rule').textContent = scope.value === 'repeated'
      ? '同形の判定は元の380行に対して行います。地域を絞って1行になっても、この条件は変えません。'
      : scope.value === 'outside'
        ? '福島村・袋井町・於保村を除外した感度確認です。偏りを補正した標本や地域の使用率ではありません。'
        : '原表記は完全一致で数えます。旧仮名・大きな仮名を統合しません。';
    const groups = [...grouped].sort((a, b) => b[1].count - a[1].count);
    const max = Math.max(1, ...groups.map(([, group]) => group.count));
    body.replaceChildren();
    for (const [name, group] of groups) {
      const tr = document.createElement('tr');
      const label = document.createElement('th'); label.scope = 'row'; label.textContent = name;
      const count = document.createElement('td');
      const bar = document.createElement('span'); bar.className = 'research-bar'; bar.style.setProperty('--share', `${group.count / max * 100}%`);
      const value = document.createElement('b'); value.textContent = group.count;
      count.append(bar, value, ' 行');
      const forms = document.createElement('td'); forms.textContent = `${group.forms.size} 種類`;
      tr.append(label, count, forms); body.append(tr);
    }
    if (!groups.length) {
      const tr = document.createElement('tr'); const td = document.createElement('td');
      td.colSpan = 3; td.textContent = 'この組合せに該当する記録はありません。「条件を戻す」で全件へ戻れます。';
      tr.append(td); body.append(tr);
    }
  }
  scope.addEventListener('change', render);
  region.addEventListener('change', render);
  document.getElementById('lab-reset').addEventListener('click', () => { scope.value = 'all'; region.value = ''; render(); });
  document.getElementById('lab-controls').hidden = false;
})();
