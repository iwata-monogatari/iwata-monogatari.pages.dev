/* =========================================================================
   district-filter.js ── 地区ページ 歴史的コンテンツのテーマ別絞り込み
   方針:
   - JavaScript 無効時は、HTML に静的出力されたカードが全件表示される。
   - JS 有効時のみ、テーマ別絞り込み・件数表示・新着固定＋ランダム整列・出現アニメを行う。
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

    var PIN_COUNT = 3;   // 上部に固定する新着件数
    var STAGGER = 45;    // 出現アニメーションの時間差(ms)
    var STAGGER_CAP = 14; // 時間差を頭打ちにするカード数（全体が間延びしないように）

    /* --- 新着順（data-published 降順・同日は元の順序）を基準配列として保持 --- */
    var byDate = cards
      .map(function (card, i) {
        return { card: card, i: i, d: card.getAttribute("data-published") || "" };
      })
      .sort(function (a, b) {
        if (a.d === b.d) return a.i - b.i;
        return a.d < b.d ? 1 : -1; // 新しい日付を上に
      })
      .map(function (o) {
        return o.card;
      });

    /* --- Fisher–Yates シャッフル（毎回ランダムに並べ替える） --- */
    function shuffle(arr) {
      for (var i = arr.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var t = arr[i];
        arr[i] = arr[j];
        arr[j] = t;
      }
      return arr;
    }

    /* --- 表示：新着 PIN_COUNT 件を上に固定し、残りをランダムに並べて順番に出現させる --- */
    function apply(theme) {
      var matching = byDate.filter(function (card) {
        var themes = (card.getAttribute("data-theme") || "").split(/\s+/);
        return theme === "all" || themes.indexOf(theme) !== -1;
      });
      var order = matching.slice(0, PIN_COUNT).concat(shuffle(matching.slice(PIN_COUNT)));

      // 非該当カードを隠し、DOM順を新しい並びに合わせ、アニメーションを一旦リセット
      cards.forEach(function (card) {
        card.hidden = order.indexOf(card) === -1;
      });
      order.forEach(function (card) {
        card.classList.remove("is-enter");
        card.style.animationDelay = "";
        list.appendChild(card);
      });

      // 一度だけリフローして、付け直したアニメーションを確実に再生させる
      void list.offsetWidth;

      order.forEach(function (card, i) {
        card.style.animationDelay = Math.min(i, STAGGER_CAP) * STAGGER + "ms";
        card.classList.add("is-enter");
      });

      if (countEl) countEl.textContent = "表示中：" + order.length + "件 / 全" + cards.length + "件";
      if (emptyEl) emptyEl.hidden = order.length !== 0;
    }

    if (filterBar) {
      var buttons = Array.prototype.slice.call(filterBar.querySelectorAll("button[data-filter]"));

      /* --- 該当カードが0件のテーマボタンは表示しない（「すべて」は常に表示） --- */
      buttons.forEach(function (btn) {
        var theme = btn.getAttribute("data-filter");
        if (theme === "all") return;
        var hasMatch = cards.some(function (card) {
          var themes = (card.getAttribute("data-theme") || "").split(/\s+/);
          return themes.indexOf(theme) !== -1;
        });
        if (!hasMatch) btn.hidden = true;
      });

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
