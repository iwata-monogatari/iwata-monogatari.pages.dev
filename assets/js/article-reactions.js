// 記事末尾の反応ボタン（3種）と非公開の一言。部品は partials/article-reactions.html。
(function () {
  "use strict";
  var root = document.querySelector(".im-react");
  if (!root || root.dataset.ready) return;
  root.dataset.ready = "1";

  var path = location.pathname.replace(/\/index\.html$/, "/").replace(/\.html$/, "");
  if (path.length > 1) path = path.replace(/\/+$/, "");
  var title = (document.title || "").slice(0, 200);
  var btns = root.querySelectorAll(".im-react-btns button");
  var after = root.querySelector(".im-react-after");
  var thanks = root.querySelector(".im-react-thanks");
  var ta = root.querySelector("textarea");
  var send = root.querySelector(".im-react-send");
  var count = root.querySelector(".im-react-count");

  function store(k, v) {
    try {
      if (v === undefined) return localStorage.getItem(k);
      localStorage.setItem(k, v);
    } catch (e) { return null; }
  }

  // 端末ごとの匿名ID
  var vid = store("imReactVid");
  if (!vid) {
    var a = new Uint8Array(12);
    (window.crypto || window.msCrypto).getRandomValues(a);
    vid = Array.prototype.map.call(a, function (b) { return ("0" + b.toString(16)).slice(-2); }).join("");
    store("imReactVid", vid);
  }

  // 運営者のアクセス（アクセス解析と同じ判定）は internal として記録し、集計から除く
  function isInternal() {
    var q = new URLSearchParams(location.search);
    var v = q.get("fga_internal") || q.get("atawi_internal");
    if (v === "1" || v === "true") return true;
    return store("fujigaokaAnalyticsInternal") === "1" || store("fujigaokaAnalyticsIgnore") === "1";
  }

  var key = "imReact:" + path;
  var current = store(key);

  function paint() {
    Array.prototype.forEach.call(btns, function (b) {
      b.setAttribute("aria-pressed", b.dataset.r === current ? "true" : "false");
    });
    if (current) after.hidden = false;
  }

  function post(url, data) {
    data.path = path; data.title = title; data.vid = vid; data.internal = isInternal();
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      keepalive: true
    }).then(function (r) { return r.json(); });
  }

  Array.prototype.forEach.call(btns, function (b) {
    b.addEventListener("click", function () {
      if (current === b.dataset.r) return;
      current = b.dataset.r;
      store(key, current);
      paint();
      post("/api/reactions/react", { reaction: current }).catch(function () {});
    });
  });

  ta.addEventListener("input", function () { count.textContent = ta.value.length + " / 200"; });

  send.addEventListener("click", function () {
    var note = ta.value.trim();
    if (!note) { ta.focus(); return; }
    send.disabled = true;
    post("/api/reactions/note", { note: note, reaction: current })
      .then(function (d) {
        if (d && d.ok) {
          ta.value = ""; ta.hidden = true; send.hidden = true; count.hidden = true;
          thanks.textContent = "届きました。ありがとうございました。";
        } else {
          thanks.textContent = (d && d.error) || "送信できませんでした。";
          send.disabled = false;
        }
      })
      .catch(function () { thanks.textContent = "送信できませんでした。"; send.disabled = false; });
  });

  paint();
})();
