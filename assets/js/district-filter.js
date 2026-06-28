/* =========================================================================
   district-filter.js ── 地区ページ 歴史的コンテンツのテーマ別絞り込み
   方針:
   - JavaScript 無効時は、HTML に静的出力されたカードが全件表示される。
   - JS 有効時のみ、テーマ別絞り込み・件数表示・新着固定＋日替わりランダム整列・出現アニメを行う。
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
    var STAGGER = 40;    // 出現アニメーションの時間差(ms)
    var STAGGER_CAP = 12; // 時間差を頭打ちにするカード数（全体が間延びしないように）

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

    /* --- 日替わりシード付き乱数（その日のうちは同じ並び、日付が変わると変わる） --- */
    function hashStr(s) {
      var h = 2166136261;
      for (var i = 0; i < s.length; i++) {
        h ^= s.charCodeAt(i);
        h = Math.imul(h, 16777619);
      }
      return h >>> 0;
    }
    function mulberry32(a) {
      return function () {
        a = (a + 0x6d2b79f5) | 0;
        var t = Math.imul(a ^ (a >>> 15), 1 | a);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      };
    }
    var now = new Date();
    var rng = mulberry32(hashStr(now.getFullYear() + "-" + (now.getMonth() + 1) + "-" + now.getDate()));

    /* --- Fisher–Yates シャッフル（日替わりシードを使用） --- */
    function shuffle(arr) {
      for (var i = arr.length - 1; i > 0; i--) {
        var j = Math.floor(rng() * (i + 1));
        var t = arr[i];
        arr[i] = arr[j];
        arr[j] = t;
      }
      return arr;
    }

    /* --- 表示順は一度だけ確定：新着 PIN_COUNT 件を上に固定し、残りを日替わりでシャッフル --- */
    var displayOrder = byDate.slice(0, PIN_COUNT).concat(shuffle(byDate.slice(PIN_COUNT)));

    /* --- 絞り込み：確定済みの並びを保ったまま該当カードを出し、順番に出現させる --- */
    function apply(theme) {
      var visible = [];
      displayOrder.forEach(function (card) {
        var themes = (card.getAttribute("data-theme") || "").split(/\s+/);
        var ok = theme === "all" || themes.indexOf(theme) !== -1;
        card.hidden = !ok;
        if (ok) visible.push(card);
      });

      // DOM順を確定済みの並びに合わせ、アニメーションを一旦リセット
      displayOrder.forEach(function (card) {
        card.classList.remove("is-enter");
        card.style.animationDelay = "";
        list.appendChild(card);
      });

      // 一度だけリフローして、付け直したアニメーションを確実に再生させる
      void list.offsetWidth;

      visible.forEach(function (card, i) {
        card.style.animationDelay = Math.min(i, STAGGER_CAP) * STAGGER + "ms";
        card.classList.add("is-enter");
      });

      if (countEl) countEl.textContent = "表示中：" + visible.length + "件 / 全" + cards.length + "件";
      if (emptyEl) emptyEl.hidden = visible.length !== 0;
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
