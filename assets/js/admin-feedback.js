(function () {
  "use strict";
  var status = document.getElementById("feedback-admin-status");
  var body = document.getElementById("feedback-admin-rows");
  var download = document.getElementById("feedback-csv");
  if (!status || !body || !download) return;
  var rows = [], requestId = 0;
  async function load() {
    var id = ++requestId;
    rows = []; body.replaceChildren(); download.disabled = true;
    status.textContent = "見せ方の希望を読み込んでいます…";
    var query = new URLSearchParams({ site: document.getElementById("site").value, days: document.getElementById("days").value });
    if (document.getElementById("internal").checked) query.set("internal", "1");
    try {
      var response = await fetch("/api/reactions/admin-feedback?" + query, { cache: "no-store", credentials: "same-origin" });
      if (id !== requestId) return;
      if (response.status === 401) { status.textContent = "下の管理者端末の登録後に、希望する見せ方を確認できます。"; return; }
      var data = await response.json();
      if (id !== requestId) return;
      if (!response.ok || !data.ok) throw new Error("load-failed");
      rows = data.rows;
      rows.forEach(function (row) {
        var tr = document.createElement("tr");
        var title = document.createElement("td"), link = document.createElement("a");
        link.href = row.path; link.textContent = row.title || row.path; link.target = "_blank"; link.rel = "noopener";
        title.appendChild(link); tr.appendChild(title);
        [row.question_id + " / " + row.question_version + " / " + row.ui_version,
          row.device === "mobile" ? "スマートフォン" : "PC",
          row.reactions, row.answers, row.list, row.diagram, row.qa].forEach(function (value, index) {
          var td = document.createElement("td"); td.textContent = String(value); if (index > 1) td.className = "num"; tr.appendChild(td);
        });
        body.appendChild(tr);
      });
      status.textContent = rows.length ? rows.length + "区分を表示しています。同じ質問の版ごとに比較してください。" : "この条件での回答はまだありません。";
      download.disabled = !rows.length;
    } catch (_) {
      if (id === requestId) status.textContent = "取得できませんでした。再読み込みしてください。";
    }
  }
  function csvCell(value) {
    var text = String(value == null ? "" : value);
    if (/^[\s]*[=+@-]/.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
  }
  download.addEventListener("click", function () {
    if (!rows.length) return;
    var columns = ["path", "title", "question_id", "question_version", "ui_version", "article_type", "device", "reactions", "answers", "list", "diagram", "qa", "last_at"];
    var csv = "\uFEFF" + [columns].concat(rows.map(function (row) { return columns.map(function (key) { return row[key]; }); }))
      .map(function (line) { return line.map(csvCell).join(","); }).join("\r\n");
    var url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    var link = document.createElement("a"); link.href = url; link.download = "article-feedback.csv"; link.click();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  });
  document.addEventListener("reaction-summary-loading", load);
  load();
})();
