/* 磐田物語 みんなの掲示板 / フロントエンド
   - ページ読み込み時に /api/bbs/list から一覧取得
   - フォーム送信時に /api/bbs/post へ POST
   - 投稿成功後に一覧を再取得し、メッセージ表示
   本文の表示は textContent / createElement で行い、HTML は実行しない。 */

(function () {
  "use strict";

  var form = document.getElementById("bbs-form");
  var submitBtn = document.getElementById("bbs-submit");
  var msgEl = document.getElementById("bbs-message");
  var postsEl = document.getElementById("bbs-posts");
  var postsStatus = document.getElementById("bbs-posts-status");
  var bodyField = form ? form.querySelector('textarea[name="body"]') : null;
  var counter = document.getElementById("bbs-counter");

  // ---- 文字数カウンター ----
  if (bodyField && counter) {
    var updateCounter = function () {
      counter.textContent = (bodyField.value.length) + " / 800";
    };
    bodyField.addEventListener("input", updateCounter);
    updateCounter();
  }

  // ---- 日時の整形 ----
  function formatDate(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return iso || "";
    var y = d.getFullYear();
    var m = d.getMonth() + 1;
    var day = d.getDate();
    var hh = ("0" + d.getHours()).slice(-2);
    var mm = ("0" + d.getMinutes()).slice(-2);
    return y + "年" + m + "月" + day + "日 " + hh + ":" + mm;
  }

  function pad5(n) {
    return "No." + ("00000" + n).slice(-5);
  }

  // ---- 投稿1件を描画（DOM生成のみ。innerHTMLは使わない） ----
  function renderPost(post) {
    var article = document.createElement("article");
    article.className = "bbs-post";

    var header = document.createElement("header");
    header.className = "bbs-post-header";

    var no = document.createElement("span");
    no.className = "bbs-no";
    no.textContent = pad5(post.id);
    header.appendChild(no);

    var time = document.createElement("time");
    time.setAttribute("datetime", post.created_at || "");
    time.textContent = formatDate(post.created_at);
    header.appendChild(time);

    var name = document.createElement("span");
    name.className = "bbs-name";
    name.textContent = (post.name && post.name.trim()) ? post.name : "匿名";
    name.textContent += " さん";
    header.appendChild(name);

    if (post.area && post.area.trim()) {
      var area = document.createElement("span");
      area.className = "bbs-area";
      area.textContent = post.area;
      header.appendChild(area);
    }

    article.appendChild(header);

    var body = document.createElement("p");
    body.className = "bbs-body";
    body.textContent = post.body || "";
    article.appendChild(body);

    // 関連URLは同一サイト内のリンクのみ表示（外部リンク混入対策）
    if (post.related_url && /^https?:\/\//i.test(post.related_url)) {
      var safe = isAllowedUrl(post.related_url);
      if (safe) {
        var rel = document.createElement("p");
        rel.className = "bbs-related";
        var label = document.createTextNode("関連ページ: ");
        var a = document.createElement("a");
        a.href = post.related_url;
        a.textContent = post.related_url;
        a.rel = "nofollow noopener";
        rel.appendChild(label);
        rel.appendChild(a);
        article.appendChild(rel);
      }
    }

    return article;
  }

  function isAllowedUrl(url) {
    try {
      var u = new URL(url);
      // 自サイト内のみリンク化（必要に応じてドメインを追加）
      return /(^|\.)iwata-monogatari\.pages\.dev$/i.test(u.hostname);
    } catch (e) {
      return false;
    }
  }

  // ---- 一覧取得 ----
  function loadBbsPosts() {
    if (!postsEl) return Promise.resolve();
    if (postsStatus) postsStatus.textContent = "読み込み中…";
    return fetch("/api/bbs/list", { headers: { "Accept": "application/json" } })
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then(function (data) {
        var posts = (data && data.posts) || [];
        postsEl.textContent = "";
        if (posts.length === 0) {
          if (postsStatus) postsStatus.textContent = "まだ書き込みはありません。最初のひとことをどうぞ。";
          return;
        }
        if (postsStatus) postsStatus.textContent = posts.length + " 件の書き込み";
        var frag = document.createDocumentFragment();
        posts.forEach(function (p) { frag.appendChild(renderPost(p)); });
        postsEl.appendChild(frag);
      })
      .catch(function (err) {
        if (postsStatus) postsStatus.textContent = "投稿の読み込みに失敗しました。時間をおいて再読み込みしてください。";
        console.error("[bbs] list error:", err);
      });
  }

  function showMessage(text, type) {
    if (!msgEl) return;
    msgEl.textContent = text;
    msgEl.className = "bbs-message" + (type ? " " + type : "");
  }

  // ---- 投稿送信 ----
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      showMessage("", "");

      var body = bodyField ? bodyField.value.trim() : "";
      if (body.length < 10) {
        showMessage("投稿内容は10文字以上でご記入ください。", "err");
        return;
      }
      if (body.length > 800) {
        showMessage("投稿内容は800文字以内でご記入ください。", "err");
        return;
      }
      var agree = form.querySelector('input[name="agree"]');
      if (agree && !agree.checked) {
        showMessage("注意事項への同意が必要です。", "err");
        return;
      }

      var payload = {
        name: getVal("name"),
        area: getVal("area"),
        body: body,
        related_url: getVal("related_url"),
        website: getVal("website"), // honeypot
        agree: !!(agree && agree.checked)
      };

      // Turnstile トークン（読み込まれていれば付与）
      var tsField = form.querySelector('[name="cf-turnstile-response"]');
      if (tsField) payload["cf-turnstile-response"] = tsField.value;

      if (submitBtn) { submitBtn.disabled = true; }
      showMessage("送信中…", "");

      fetch("/api/bbs/post", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify(payload)
      })
        .then(function (res) {
          return res.json().then(function (data) { return { ok: res.ok, data: data }; });
        })
        .then(function (r) {
          if (!r.ok || !r.data || r.data.ok === false) {
            var m = (r.data && r.data.error) || "投稿に失敗しました。時間をおいて再度お試しください。";
            showMessage(m, "err");
            return;
          }
          form.reset();
          if (counter) counter.textContent = "0 / 800";
          // Turnstile をリセット
          if (window.turnstile && typeof window.turnstile.reset === "function") {
            try { window.turnstile.reset(); } catch (e) {}
          }
          showMessage("ご投稿ありがとうございます。掲示板に反映しました。不適切な内容が含まれる場合、管理者の判断で非表示または削除することがあります。", "ok");
          return loadBbsPosts();
        })
        .catch(function (err) {
          console.error("[bbs] post error:", err);
          showMessage("通信エラーが発生しました。時間をおいて再度お試しください。", "err");
        })
        .then(function () {
          if (submitBtn) submitBtn.disabled = false;
        });
    });
  }

  function getVal(name) {
    var el = form.querySelector('[name="' + name + '"]');
    return el ? el.value.trim() : "";
  }

  // 初期ロード
  loadBbsPosts();
})();
