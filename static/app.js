// Client-side filtering for the home page list (no framework).
(() => {
  const q = document.getElementById("q");
  const state = { county: "", status: "", text: "" };
  const cards = [...document.querySelectorAll(".county .card")];
  const sections = [...document.querySelectorAll("section.county")];
  const none = document.getElementById("none");

  function apply() {
    let shown = 0;
    for (const c of cards) {
      const ok = (!state.county || c.dataset.county === state.county) &&
                 (!state.status || c.dataset.status === state.status) &&
                 (!state.text || c.dataset.name.includes(state.text));
      c.hidden = !ok;
      if (ok) shown++;
    }
    for (const s of sections) s.hidden = !s.querySelector(".card:not([hidden])");
    none.hidden = shown > 0;
    const p = new URLSearchParams();
    if (state.county) p.set("county", state.county);
    if (state.status) p.set("status", state.status);
    history.replaceState(null, "", p.toString() ? "?" + p : location.pathname);
  }

  function wire(groupId, key) {
    const btns = [...document.querySelectorAll(`#${groupId} .chip`)];
    for (const b of btns) b.addEventListener("click", () => {
      state[key] = b.dataset[key];
      btns.forEach(x => x.classList.toggle("on", x === b));
      apply();
    });
    const init = new URLSearchParams(location.search).get(key);
    if (init) btns.find(b => b.dataset[key] === init)?.click();
  }

  wire("county-chips", "county");
  wire("status-chips", "status");
  q.addEventListener("input", () => { state.text = q.value.trim().toLowerCase(); apply(); });
})();
