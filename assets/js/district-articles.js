/* 地区別入口ページ「記事を探す」表＋フィルタ＋ページャ（全9地区共通）
   静的に全行出力済みのテーブルに対し、フィルタ・ページ送りだけを行う（プログレッシブ・エンハンスメント）。
   JS無効時はビルド時に埋め込まれる <noscript> の上書きスタイルで全行が見える。 */
(function () {
  var PER_PAGE = 50;

  document.querySelectorAll('.district-articles[data-district]').forEach(function (section) {
    var tbody = section.querySelector('.article-table tbody');
    if (!tbody) return;
    var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr[data-themes]'));
    if (!rows.length) return;

    var filterWrap = section.querySelector('.article-filter');
    var countEl = section.querySelector('[data-count]');
    var pager = section.querySelector('.article-pager');
    var pagerNums = pager ? pager.querySelector('.pager-nums') : null;
    var prevBtn = pager ? pager.querySelector('[data-page-prev]') : null;
    var nextBtn = pager ? pager.querySelector('[data-page-next]') : null;
    var statusEl = pager ? pager.querySelector('.pager-status') : null;
    var buttons = filterWrap
      ? Array.prototype.slice.call(filterWrap.querySelectorAll('button[data-theme]'))
      : [];

    var state = { theme: 'all', page: 1 };

    function paramPage() {
      var m = /[?&]page=(\d+)/.exec(window.location.search);
      var n = m ? parseInt(m[1], 10) : 1;
      return n > 0 ? n : 1;
    }

    // URL の theme パラメータ（日本語テーマ名。URLエンコード済みを想定）を読む。
    // 該当するフィルターボタンが無い／all／未指定なら 'all' 扱いにする
    // （共有URLの取り違えや語彙変更に強くする）。
    function paramTheme() {
      var raw = null;
      try {
        raw = new URLSearchParams(window.location.search).get('theme');
      } catch (e) {
        var m = /[?&]theme=([^&]*)/.exec(window.location.search);
        raw = m ? decodeURIComponent(m[1].replace(/\+/g, ' ')) : null;
      }
      if (!raw || raw === 'all') return 'all';
      var exists = buttons.some(function (b) { return b.getAttribute('data-theme') === raw; });
      return exists ? raw : 'all';
    }

    // フィルターボタンの見た目・aria 状態を state.theme に同期する。
    function syncButtons() {
      buttons.forEach(function (b) {
        var on = b.getAttribute('data-theme') === state.theme;
        b.classList.toggle('is-active', on);
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
    }

    state.page = paramPage();
    state.theme = paramTheme();
    syncButtons();

    function themesOf(row) {
      var raw = row.getAttribute('data-themes') || '';
      return raw.split(/\s+/).filter(Boolean);
    }

    function visibleForTheme(row) {
      return state.theme === 'all' || themesOf(row).indexOf(state.theme) !== -1;
    }

    function render() {
      var visible = rows.filter(visibleForTheme);
      var totalPages = Math.max(1, Math.ceil(visible.length / PER_PAGE));
      if (state.page > totalPages) state.page = totalPages;
      if (state.page < 1) state.page = 1;
      var start = (state.page - 1) * PER_PAGE;
      var end = start + PER_PAGE;

      rows.forEach(function (row) { row.hidden = true; });
      visible.slice(start, end).forEach(function (row) { row.hidden = false; });

      if (countEl) countEl.textContent = String(visible.length);

      if (pager) {
        if (totalPages <= 1) {
          pager.hidden = true;
        } else {
          pager.hidden = false;
          if (pagerNums) {
            pagerNums.innerHTML = '';
            for (var i = 1; i <= totalPages; i++) {
              var li = document.createElement('li');
              var btn = document.createElement('button');
              btn.type = 'button';
              btn.textContent = String(i);
              btn.setAttribute('data-page-to', String(i));
              if (i === state.page) {
                btn.className = 'is-current';
                btn.setAttribute('aria-current', 'page');
              }
              btn.addEventListener('click', function () {
                state.page = parseInt(this.getAttribute('data-page-to'), 10);
                syncUrl();
                render();
              });
              li.appendChild(btn);
              pagerNums.appendChild(li);
            }
          }
          if (prevBtn) prevBtn.disabled = state.page <= 1;
          if (nextBtn) nextBtn.disabled = state.page >= totalPages;
          if (statusEl) {
            var shownEnd = Math.min(end, visible.length);
            statusEl.textContent =
              (visible.length === 0 ? 0 : start + 1) + '〜' + shownEnd + '件目／全' +
              visible.length + '件（' + state.page + '／' + totalPages + 'ページ）';
          }
        }
      }
    }

    function syncUrl() {
      if (!window.history || !window.history.replaceState) return;
      var url = new URL(window.location.href);
      // テーマ絞り込み状態を共有・再訪できるよう URL に残す。all／未指定は消す。
      if (state.theme && state.theme !== 'all') {
        url.searchParams.set('theme', state.theme);
      } else {
        url.searchParams.delete('theme');
      }
      if (state.page > 1) {
        url.searchParams.set('page', String(state.page));
      } else {
        url.searchParams.delete('page');
      }
      window.history.replaceState(null, '', url.pathname + url.search + url.hash);
    }

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        state.theme = btn.getAttribute('data-theme');
        state.page = 1; // テーマ変更時はページを1に戻す
        syncButtons();
        syncUrl();
        render();
      });
    });

    if (prevBtn) {
      prevBtn.addEventListener('click', function () {
        state.page -= 1;
        syncUrl();
        render();
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener('click', function () {
        state.page += 1;
        syncUrl();
        render();
      });
    }

    render();
    // 初期表示後に URL を正規化する（無効な theme を除去し、絞り込みで
    // ページ数が減ってクランプされた page を実際の値に合わせる）。
    syncUrl();
  });
})();
