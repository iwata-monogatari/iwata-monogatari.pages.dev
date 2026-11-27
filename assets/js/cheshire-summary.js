async function loadCheshireSummary(days, isCurrent) {
  const box = document.getElementById('cheshire-results');
  const status = document.getElementById('status');
  box.replaceChildren();
  status.textContent = '読み込み中…';
  try {
    const response = await fetch('/api/reactions/cheshire?days=' + encodeURIComponent(days), {cache:'no-store'});
    if (!response.ok) throw Error();
    const data = await response.json();
    if (!data.ok) throw Error();
    if (!isCurrent()) return;
    for (const question of data.items) {
      const article = document.createElement('article');
      article.className = 'box';
      const heading = document.createElement('h3');
      const link = document.createElement('a');
      link.href = 'https://cheshire.atawi.link/philosophy/talk-back/' + question.id + '/';
      link.textContent = question.title;
      heading.append(link);
      const total = document.createElement('p');
      total.textContent = '回答 ' + question.total + ' 件';
      const list = document.createElement('ul');
      for (const answer of question.answers) {
        const item = document.createElement('li');
        const share = question.total ? '（' + Math.round(100 * answer.count / question.total) + '%）' : '';
        item.textContent = answer.label + '　' + answer.count + '件' + share;
        list.append(item);
      }
      article.append(heading,total,list);
      box.append(article);
    }
    status.textContent = '集計を更新しました。';
  } catch {
    if (isCurrent()) status.textContent = '集計を取得できませんでした。再読み込みしてください。';
  }
}
