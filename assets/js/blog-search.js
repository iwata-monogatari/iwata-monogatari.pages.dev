(() => {
  "use strict";

  const panel = document.querySelector("[data-blog-search]");
  const items = [...document.querySelectorAll(".post-item[data-search]")];
  if (!panel || !items.length) return;

  const controls = {
    query: document.querySelector("#blog-search-query"),
    kind: document.querySelector("#blog-search-kind"),
    tag: document.querySelector("#blog-search-tag"),
    month: document.querySelector("#blog-search-month"),
  };
  const status = document.querySelector("#blog-search-status");
  const empty = document.querySelector("#blog-search-empty");
  const clear = document.querySelector("#blog-search-clear");
  const keys = Object.keys(controls);

  const normalize = (value) =>
    String(value || "").normalize("NFKC").toLocaleLowerCase("ja");

  const optionHasValue = (select, value) =>
    [...select.options].some((option) => option.value === value);

  const loadFromUrl = () => {
    const params = new URLSearchParams(window.location.search);
    controls.query.value = params.get("q") || "";
    for (const key of ["kind", "tag", "month"]) {
      const value = params.get(key) || "";
      controls[key].value = optionHasValue(controls[key], value) ? value : "";
    }
  };

  const updateUrl = () => {
    const url = new URL(window.location.href);
    for (const key of keys) {
      const param = key === "query" ? "q" : key;
      const value = controls[key].value.trim();
      if (value) url.searchParams.set(param, value);
      else url.searchParams.delete(param);
    }
    window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
  };

  const applyFilters = ({ syncUrl = true } = {}) => {
    const terms = normalize(controls.query.value).split(/\s+/).filter(Boolean);
    const kind = controls.kind.value;
    const tag = controls.tag.value;
    const month = controls.month.value;
    let visibleCount = 0;

    for (const item of items) {
      const haystack = normalize(item.dataset.search);
      const tags = (item.dataset.tags || "").split("|");
      const visible =
        terms.every((term) => haystack.includes(term)) &&
        (!kind || item.dataset.kind === kind) &&
        (!tag || tags.includes(tag)) &&
        (!month || item.dataset.month === month);
      item.hidden = !visible;
      if (visible) visibleCount += 1;
    }

    const hasFilters = keys.some((key) => controls[key].value.trim());
    status.textContent = hasFilters
      ? `${visibleCount}件見つかりました（全${items.length}件）`
      : `${items.length}件の記事`;
    empty.hidden = visibleCount !== 0;
    clear.hidden = !hasFilters;
    if (syncUrl) updateUrl();
  };

  controls.query.addEventListener("input", () => applyFilters());
  for (const key of ["kind", "tag", "month"]) {
    controls[key].addEventListener("change", () => applyFilters());
  }
  clear.addEventListener("click", () => {
    for (const key of keys) controls[key].value = "";
    applyFilters();
    controls.query.focus();
  });
  window.addEventListener("popstate", () => {
    loadFromUrl();
    applyFilters({ syncUrl: false });
  });

  loadFromUrl();
  applyFilters({ syncUrl: false });
})();
