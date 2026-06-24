/* =========================================================================
   district-filter.js ── 地区ページ 歴史的コンテンツのテーマ別絞り込み
   方針:
   - JavaScript 無効時は、HTML に静的出力されたカードが全件表示される。
   - JS 有効時のみ、テーマ別絞り込み・件数表示・新着順整列を行う。
   - 絞り込みボタンは aria-pressed を切り替える。
   - 複数の絞り込みブロックが1ページにあっても動作する（data-filter-scope 単位）。
   ========================================================================= */
(function () {
  "use strict";

  function initScope(scope) {
    var filterBar = scope.querySelector(".district-filter");
    var list = scope.querySelector(".content-cards");
    if (!list) return;

    var cards = Array.prototype.slice.call(list.querySelectorAll(".content-card"));
    var countEl = scope.querySelector(".district-filter-count");
    var emptyEl = scope.querySelector(".district-empty");

    /* --- 新着順に整列（data-published の降順、同日は元の順序を維持） --- */
    cards
      .map(function (card, i) {
        return { card: card, i: i, d: card.getAttribute("data-published") || "" };
      })
      .sort(function (a, b) {
        if (a.d === b.d) return a.i - b.i;
        return a.d < b.d ? 1 : -1; // 新しい日付を上に
      })
      .forEach(function (o) {
        list.appendChild(o.card);
      });

    function apply(theme) {
      var shown = 0;
      cards.forEach(function (card) {
        var themes = (card.getAttribute("data-theme") || "").split(/\s+/);
        var match = theme === "all" || themes.indexOf(theme) !== -1;
        if (match) {
          card.hidden = false;
          shown++;
        } else {
          card.hidden = true;
        }
      });
      if (countEl) countEl.textContent = "表示中：" + shown + "件 / 全" + cards.length + "件";
      if (emptyEl) emptyEl.hidden = shown !== 0;
    }

    if (filterBar) {
      var buttons = Array.prototype.slice.call(filterBar.querySelectorAll("button[data-filter]"));
      filterBar.addEventListener("click", function (e) {
        var btn = e.target.closest("button[data-filter]");
        if (!btn) return;
        buttons.forEach(function (b) {
          b.setAttribute("aria-pressed", b === btn ? "true" : "false");
        });
        apply(btn.getAttribute("data-filter"));
      });
    }

    apply("all");
  }

  function init() {
    var scopes = document.querySelectorAll("[data-filter-scope]");
    if (!scopes.length) return;
    Array.prototype.forEach.call(scopes, initScope);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
