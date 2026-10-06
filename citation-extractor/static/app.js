(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const els = {
    text: $("caseText"), chars: $("charCount"), file: $("fileInput"), sample: $("sampleBtn"),
    lookup: $("lookupToggle"), tokenRow: $("tokenRow"), token: $("tokenInput"), remember: $("rememberToken"),
    tokenHint: $("tokenHint"), extract: $("extractBtn"), error: $("errorBox"),
    empty: $("emptyState"), results: $("results"), stats: $("stats"), banner: $("lookupBanner"),
    list: $("authorityList"), filter: $("filterInput"), kind: $("kindFilter"), sort: $("sortSelect"),
    authView: $("authoritiesView"), annView: $("annotatedView"), annText: $("annotatedText"),
    exportBtn: $("exportBtn"), exportMenu: $("exportMenu"),
  };

  const KIND_LABELS = { case: "Cases", statute: "Statutes, Rules & Regulations", journal: "Secondary Sources" };
  const TYPE_LABELS = { full: "Full", short: "Short", id: "Id.", supra: "Supra", reference: "Ref." };
  const TOKEN_KEY = "citex.courtlistenerToken";
  let result = null;

  // ---------- helpers ----------
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch { /* storage unavailable */ } },
  };
  const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
  const bestLink = (a) => a.links.courtlistener || a.links.source || a.links.courtlistener_citation || "";

  function showError(msg) {
    els.error.textContent = msg || "";
    els.error.hidden = !msg;
  }

  function updateCount() {
    els.chars.textContent = `${els.text.value.length.toLocaleString()} characters`;
  }

  // ---------- input ----------
  els.text.addEventListener("input", updateCount);

  els.sample.addEventListener("click", async () => {
    const res = await fetch("/api/sample");
    els.text.value = await res.text();
    updateCount();
  });

  els.file.addEventListener("change", () => {
    const f = els.file.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => { els.text.value = reader.result; updateCount(); };
    reader.readAsText(f);
    els.file.value = "";
  });

  const savedToken = store.get(TOKEN_KEY);
  if (savedToken) { els.token.value = savedToken; els.remember.checked = true; }
  els.remember.addEventListener("change", () => store.set(TOKEN_KEY, els.remember.checked ? els.token.value : null));
  els.token.addEventListener("input", () => { if (els.remember.checked) store.set(TOKEN_KEY, els.token.value); });
  els.lookup.addEventListener("change", () => { els.tokenRow.hidden = !els.lookup.checked; });

  fetch("/api/config").then((r) => r.json()).then((cfg) => {
    if (cfg.server_token) {
      els.token.placeholder = "Using the server's CourtListener token (override optional)";
    }
  }).catch(() => {});

  els.extract.addEventListener("click", run);
  els.text.addEventListener("keydown", (e) => { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") run(); });

  async function run() {
    showError("");
    const text = els.text.value;
    if (!text.trim()) { showError("Paste the text of a case (or upload a file) first."); return; }
    els.extract.disabled = true;
    els.extract.textContent = els.lookup.checked ? "Extracting & looking up…" : "Extracting…";
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, lookup: els.lookup.checked, token: els.token.value.trim() || null }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
      result = data;
      render();
    } catch (err) {
      showError(err.message);
    } finally {
      els.extract.disabled = false;
      els.extract.textContent = "Extract citations";
    }
  }

  // ---------- results ----------
  function render() {
    els.empty.hidden = true;
    els.results.hidden = false;
    const s = result.stats;
    const stat = (n, label) => `<div class="stat"><b>${n}</b><span>${label}</span></div>`;
    els.stats.innerHTML = [
      stat(s.total_citations, "citations"),
      stat(s.unique_authorities, "authorities"),
      stat(s.cases, "cases"),
      stat(s.statutes, "statutes/rules"),
      stat(s.journals, "secondary"),
      result.lookup.performed ? stat(s.linked, "linked") : stat(s.short_form, "short forms"),
    ].join("");

    const lk = result.lookup;
    if (lk.performed) {
      els.banner.hidden = false;
      if (lk.error) {
        els.banner.className = "banner warn";
        els.banner.textContent = `CourtListener lookup failed: ${lk.error} Citation links below still work.`;
      } else {
        els.banner.className = "banner ok";
        const merged = lk.merged_parallel ? ` · ${plural(lk.merged_parallel, "parallel citation")} merged` : "";
        els.banner.textContent = `CourtListener: ${lk.found} linked · ${lk.ambiguous} ambiguous · ${lk.not_found} not found${merged}`;
      }
    } else {
      els.banner.hidden = true;
    }
    renderList();
    renderAnnotated();
  }

  function matches(a, q) {
    if (!q) return true;
    const hay = [a.case_name, a.full_citation, a.citation, ...a.parallel_citations, a.court_name, a.reporter_name,
      ...a.parentheticals].join(" ").toLowerCase();
    return hay.includes(q);
  }

  function renderList() {
    const q = els.filter.value.trim().toLowerCase();
    const kind = els.kind.value;
    const sort = els.sort.value;
    let html = "";

    if (kind === "unresolved") {
      html = result.unresolved.length
        ? result.unresolved.filter((o) => !q || (o.full_text || o.text).toLowerCase().includes(q)).map(unresolvedCard).join("")
        : `<p class="empty">No unresolved short-form citations.</p>`;
      els.list.innerHTML = html;
      return;
    }

    let items = result.authorities.filter((a) => (kind === "all" || a.kind === kind) && matches(a, q));
    if (sort === "appearance") items = [...items].sort((a, b) => a.first_position - b.first_position);
    if (sort === "count") items = [...items].sort((a, b) => b.occurrence_count - a.occurrence_count || a.first_position - b.first_position);

    if (sort === "toa") {
      for (const [k, label] of Object.entries(KIND_LABELS)) {
        const group = items.filter((a) => a.kind === k);
        if (group.length) html += `<h3 class="group-title">${label}</h3>` + group.map(card).join("");
      }
      if (kind === "all" && result.unresolved.length && !q) {
        html += `<h3 class="group-title">Unresolved short forms</h3>` + result.unresolved.map(unresolvedCard).join("");
      }
    } else {
      html = items.map(card).join("");
    }
    els.list.innerHTML = html || `<p class="empty">No citations match.</p>`;
  }

  function titleHtml(a) {
    let t = esc(a.full_citation);
    if (a.case_name) t = t.replace(esc(a.case_name), `<i>${esc(a.case_name)}</i>`);
    const link = bestLink(a);
    return link ? `<a href="${esc(link)}" target="_blank" rel="noopener">${t}</a>` : t;
  }

  function lookupChip(a) {
    const cl = a.courtlistener;
    if (!cl) return a.kind === "case" && a.links.courtlistener_citation ? `<span class="chip">CourtListener link (unverified)</span>` : "";
    if (cl.status === "found") return `<span class="chip ok">✓ on CourtListener</span>`;
    if (cl.status === "ambiguous") return `<span class="chip warn">ambiguous — ${cl.candidates.length} matches</span>`;
    if (cl.status === "not_found") return `<span class="chip bad">not found on CourtListener</span>`;
    return `<span class="chip warn">${esc(cl.status)}</span>`;
  }

  function card(a) {
    const sub = [a.court_name, a.reporter_name].filter(Boolean).map(esc).join(" · ");
    const counts = Object.entries(a.counts).map(([k, v]) => `${v} ${TYPE_LABELS[k] || k}`).join(", ");
    const chips = [
      lookupChip(a),
      a.pin_cites.length ? `<span class="chip">pin ${esc(a.pin_cites.join(", "))}</span>` : "",
      ...a.signals.map((s) => `<span class="chip"><i>${esc(s)}</i></span>`),
      a.links.source ? `<span class="chip">source text linked</span>` : "",
    ].join("");
    const cl = a.courtlistener;
    const clName = cl && cl.case_name && cl.case_name !== a.case_name
      ? `<div class="auth-sub">CourtListener: ${esc(cl.case_name)}${cl.date_filed ? ` (${esc(cl.date_filed)})` : ""}</div>` : "";
    const candidates = cl && cl.candidates && cl.candidates.length
      ? `<p class="candidates">Possible matches: ${cl.candidates.map((c) =>
          `<a href="${esc(c.url)}" target="_blank" rel="noopener">${esc(c.case_name || c.url)}${c.date_filed ? ` (${esc(c.date_filed.slice(0, 4))})` : ""}</a>`).join("")}</p>` : "";
    const parens = a.parentheticals.length
      ? `<ul class="parens">${a.parentheticals.map((p) => `<li>(${esc(p)})</li>`).join("")}</ul>` : "";

    return `
      <div class="auth" id="auth-${a.id}">
        <div class="auth-head" data-toggle="${a.id}">
          <span class="kind-dot kind-${a.kind}" title="${a.kind}"></span>
          <div class="auth-main">
            <div class="auth-title">${titleHtml(a)}</div>
            ${sub ? `<div class="auth-sub">${sub}</div>` : ""}
            ${clName}
            <div class="chips">${chips}</div>
          </div>
          <div class="count" title="${esc(counts)}"><b>${a.occurrence_count}</b><span>cited</span></div>
        </div>
        <div class="auth-body" hidden>
          ${candidates}${parens}
          ${a.occurrences.map(occurrenceHtml).join("")}
        </div>
      </div>`;
  }

  function occurrenceHtml(o) {
    const extra = [o.pin_cite ? `at ${esc(o.pin_cite)}` : "", o.signal ? `<i>${esc(o.signal)}</i>` : ""].filter(Boolean).join(" · ");
    return `<div class="occ">
      <div class="occ-type">${TYPE_LABELS[o.type] || o.type}${extra ? `<small>${extra}</small>` : ""}</div>
      <div class="occ-ctx">${esc(o.context.before)}<mark>${esc(o.context.match)}</mark>${esc(o.context.after)}
        <a href="#" class="jump" data-jump="${o.start}">show in text</a></div>
    </div>`;
  }

  function unresolvedCard(o) {
    return `<div class="auth">
      <div class="auth-head" data-toggle="u${o.start}">
        <span class="kind-dot kind-unresolved"></span>
        <div class="auth-main">
          <div class="auth-title">${esc(o.full_text || o.text)}</div>
          <div class="auth-sub">Short-form citation with no matching full citation in this text${o.antecedent_guess ? ` (refers to “${esc(o.antecedent_guess)}”)` : ""}</div>
        </div>
      </div>
      <div class="auth-body" hidden>${occurrenceHtml(o)}</div>
    </div>`;
  }

  els.list.addEventListener("click", (e) => {
    const jump = e.target.closest("[data-jump]");
    if (jump) { e.preventDefault(); showInText(Number(jump.dataset.jump)); return; }
    if (e.target.closest("a")) return;
    const head = e.target.closest("[data-toggle]");
    if (head) { const body = head.nextElementSibling; body.hidden = !body.hidden; }
  });

  [els.filter, els.kind, els.sort].forEach((el) => el.addEventListener("input", () => result && renderList()));

  // ---------- annotated view ----------
  function renderAnnotated() {
    const text = result.text;
    const marks = [];
    const byId = Object.fromEntries(result.authorities.map((a) => [a.id, a]));
    result.authorities.forEach((a) => a.occurrences.forEach((o) => marks.push([o.start, o.end, a.id])));
    result.unresolved.forEach((o) => marks.push([o.start, o.end, null]));
    marks.sort((x, y) => x[0] - y[0]);
    let out = "", pos = 0;
    for (const [start, end, id] of marks) {
      if (start < pos) continue;
      out += esc(text.slice(pos, start));
      const a = id && byId[id];
      const cls = a ? `c c-${a.kind}` : "c c-unresolved";
      const tip = a ? a.full_citation : "Unresolved short-form citation";
      out += `<span class="${cls}" data-auth="${id || ""}" data-start="${start}" title="${esc(tip)}">${esc(text.slice(start, end))}</span>`;
      pos = end;
    }
    out += esc(text.slice(pos));
    els.annText.innerHTML = out.split("\n\n").map((p) => `<p>${p.replace(/\n/g, "<br>")}</p>`).join("");
  }

  els.annText.addEventListener("click", (e) => {
    const span = e.target.closest("[data-auth]");
    if (!span || !span.dataset.auth) return;
    setView("authorities");
    els.kind.value = "all"; els.filter.value = ""; renderList();
    const card = $(`auth-${span.dataset.auth}`);
    if (!card) return;
    card.querySelector(".auth-body").hidden = false;
    card.scrollIntoView({ behavior: "smooth", block: "start" });
    flash(card);
  });

  function showInText(start) {
    setView("annotated");
    const span = els.annText.querySelector(`[data-start="${start}"]`);
    if (span) { span.scrollIntoView({ behavior: "smooth", block: "center" }); flash(span); }
  }

  function flash(el) {
    el.classList.add("flash");
    setTimeout(() => el.classList.remove("flash"), 1600);
  }

  function setView(view) {
    document.querySelectorAll(".tab").forEach((t) => {
      const on = t.dataset.view === view;
      t.classList.toggle("active", on);
      t.setAttribute("aria-selected", on);
    });
    els.authView.hidden = view !== "authorities";
    els.annView.hidden = view !== "annotated";
  }
  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => setView(t.dataset.view)));

  // ---------- exports ----------
  els.exportBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    els.exportMenu.hidden = !els.exportMenu.hidden;
    els.exportBtn.setAttribute("aria-expanded", !els.exportMenu.hidden);
  });
  document.addEventListener("click", () => { els.exportMenu.hidden = true; els.exportBtn.setAttribute("aria-expanded", "false"); });

  els.exportMenu.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-format]");
    if (!btn || !result) return;
    try {
      const res = await fetch(`/api/export/${btn.dataset.format}`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(result),
      });
      if (!res.ok) throw new Error((await res.json()).error || "Export failed");
      const name = (res.headers.get("Content-Disposition") || "").match(/filename="([^"]+)"/)?.[1] || "export";
      const url = URL.createObjectURL(await res.blob());
      const link = Object.assign(document.createElement("a"), { href: url, download: name });
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      showError(err.message);
    }
  });
})();
