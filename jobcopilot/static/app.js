const jobList = document.getElementById("jobList");
const detail = document.getElementById("detail");
const statsEl = document.getElementById("stats");
const filter = document.getElementById("statusFilter");
const search = document.getElementById("search");
const banner = document.getElementById("banner");
const overlay = document.getElementById("overlay");
const overlayText = document.getElementById("overlayText");
const drawer = document.getElementById("drawer");
let jobs = [];
let selectedId = null;
let tab = "jd";

const STATUS_LABEL = {
  queued: "Queue",
  ready: "Approved",
  applied: "Applied",
  snoozed: "Snoozed",
  skipped: "Skipped",
  new: "Unscored",
};

function showBanner(text) {
  banner.hidden = !text;
  banner.textContent = text || "";
}

function setBusy(on, text) {
  overlay.hidden = !on;
  overlay.setAttribute("aria-hidden", on ? "false" : "true");
  overlayText.textContent = text || "Working…";
}

async function api(path, opts) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function scoreClass(n) {
  if (n == null) return "";
  if (n >= 70) return "high";
  if (n >= 55) return "mid";
  return "low";
}

async function loadMe() {
  try {
    const me = await api("/api/me");
    const who = document.getElementById("who");
    if (me.name) who.textContent = me.name;
    if (me.headline) document.querySelector(".sub").textContent = me.headline;
  } catch {
    /* ignore */
  }
}

async function loadStats() {
  const counts = await api("/api/stats");
  const current = filter.value;
  statsEl.innerHTML = Object.entries(counts)
    .map(
      ([k, v]) =>
        `<button type="button" class="stat ${k === current ? "active" : ""}" data-status="${k}">${STATUS_LABEL[k] || k}: ${v}</button>`
    )
    .join("");
}

async function loadJobs() {
  const status = filter.value;
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  jobs = await api("/api/jobs" + q);
  renderList();
  if (selectedId) {
    const still = visibleJobs().find((j) => j.id === selectedId);
    if (still) await showJob(selectedId);
    else {
      const first = visibleJobs()[0];
      selectedId = first?.id ?? null;
      if (selectedId) await showJob(selectedId);
      else {
        detail.classList.add("empty");
        detail.textContent = "Nothing in this view. Paste a listing or refresh jobs.";
      }
    }
  } else if (visibleJobs()[0]) {
    await showJob(visibleJobs()[0].id);
  }
}

function visibleJobs() {
  const q = search.value.trim().toLowerCase();
  if (!q) return jobs;
  return jobs.filter(
    (j) =>
      (j.title || "").toLowerCase().includes(q) ||
      (j.company || "").toLowerCase().includes(q) ||
      (j.location || "").toLowerCase().includes(q)
  );
}

function renderList() {
  const list = visibleJobs();
  jobList.innerHTML = list
    .map(
      (j) => `<li data-id="${j.id}" class="${j.id === selectedId ? "active" : ""}">
        <div class="title">${escapeHtml(j.title)}</div>
        <div class="meta">${escapeHtml(j.company)} · ${escapeHtml(j.location || "—")} · <span class="score ${scoreClass(j.score)}">${j.score ?? "–"}</span></div>
      </li>`
    )
    .join("");
}

function escapeHtml(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function setTab(name) {
  tab = name;
  detail.querySelectorAll(".tab").forEach((el) => el.classList.toggle("on", el.dataset.tab === name));
  detail.querySelectorAll(".panel").forEach((el) => el.classList.toggle("on", el.dataset.panel === name));
}

async function showJob(id) {
  selectedId = id;
  renderList();
  const job = await api(`/api/jobs/${id}`);
  const draft = job.draft || {};
  const bullets = Array.isArray(draft.resume_bullets) ? draft.resume_bullets : [];
  const screening = draft.screening_answers || {};
  const why = job.score_json || {};
  const mode = why.mode || "";
  detail.classList.remove("empty");
  detail.innerHTML = `
    <h2>${escapeHtml(job.title)}</h2>
    <p class="muted">${escapeHtml(job.company)} · ${escapeHtml(job.location || "—")}</p>
    <p>
      <span class="chip">${escapeHtml(job.provider)}</span>
      <span class="chip">${escapeHtml(job.status)}</span>
      <span class="chip" title="Fit for your Bangalore search: 0–100. 55+ stays in Queue; below that is Skipped. Color: green ≥70, gold ≥55, red below.">score ${job.score ?? "–"}${mode ? ` · ${escapeHtml(mode)}` : ""}</span>
      ${job.applied_at ? `<span class="chip">applied ${escapeHtml(job.applied_at)}</span>` : ""}
    </p>
    <p class="why">${escapeHtml(why.why_apply || why.why_skip || "")}</p>
    <div class="row">
      ${job.url ? `<a href="${escapeHtml(job.url)}" target="_blank" rel="noopener">Open original listing</a>` : "<span class='muted'>No URL</span>"}
    </div>
    <div class="tabs">
      <button type="button" class="tab ${tab === "packet" ? "on" : ""}" data-tab="packet">Packet</button>
      <button type="button" class="tab ${tab === "jd" ? "on" : ""}" data-tab="jd">Job description</button>
      <button type="button" class="tab ${tab === "screen" ? "on" : ""}" data-tab="screen">Screening</button>
    </div>
    <div class="panel ${tab === "packet" ? "on" : ""}" data-panel="packet">
      <h3>Cover note</h3>
      <textarea id="cover" class="packet" rows="9">${escapeHtml(draft.cover_letter || "")}</textarea>
      <div class="row"><button type="button" id="copyCover" class="secondary">Copy cover</button></div>
      <h3>Resume bullets</h3>
      <textarea id="bullets" class="packet" rows="7">${escapeHtml(bullets.join("\n"))}</textarea>
      <h3>Referral message</h3>
      <textarea id="referral" class="packet" rows="5">${escapeHtml(draft.referral_message || "")}</textarea>
      <div class="row"><button type="button" id="copyReferral" class="secondary">Copy referral</button></div>
    </div>
    <div class="panel ${tab === "jd" ? "on" : ""}" data-panel="jd">
      <div class="jd">${escapeHtml((job.description || "").slice(0, 12000))}</div>
    </div>
    <div class="panel ${tab === "screen" ? "on" : ""}" data-panel="screen">
      <p>Notice: ${escapeHtml(screening.notice_period || "—")}</p>
      <p>Location: ${escapeHtml(screening.location || "—")}</p>
      <p>Comp: ${escapeHtml(screening.salary_band || "—")}</p>
    </div>
    <div class="row">
      <button type="button" id="saveBtn" class="secondary">Save edits</button>
      <button type="button" id="approveBtn">Approve packet</button>
      <button type="button" id="appliedBtn" class="secondary">Mark applied</button>
      <button type="button" id="snoozeBtn" class="secondary">Snooze 3 days</button>
      <button type="button" id="skipBtn" class="danger">Skip</button>
    </div>
  `;
  detail.querySelectorAll(".tab").forEach((el) => {
    el.onclick = () => setTab(el.dataset.tab);
  });
  document.getElementById("saveBtn").onclick = () => saveDraft(job.id);
  document.getElementById("approveBtn").onclick = () => act(job.id, "approve");
  document.getElementById("appliedBtn").onclick = () => act(job.id, "applied");
  document.getElementById("snoozeBtn").onclick = () => act(job.id, "snooze");
  document.getElementById("skipBtn").onclick = () => act(job.id, "skip");
  document.getElementById("copyCover").onclick = () => copyText(document.getElementById("cover").value, "Cover copied");
  document.getElementById("copyReferral").onclick = () => copyText(document.getElementById("referral").value, "Referral copied");
}

async function copyText(text, ok) {
  try {
    await navigator.clipboard.writeText(text || "");
    showBanner(ok);
  } catch {
    showBanner("Could not copy");
  }
}

async function saveDraft(id) {
  const bullets = document
    .getElementById("bullets")
    .value.split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
  await api(`/api/jobs/${id}/draft`, {
    method: "PATCH",
    body: JSON.stringify({
      cover_letter: document.getElementById("cover").value,
      resume_bullets: bullets,
      referral_message: document.getElementById("referral").value,
    }),
  });
  showBanner("Draft saved. Nothing was submitted.");
}

async function act(id, action) {
  if (action === "approve") await saveDraft(id);
  await api(`/api/jobs/${id}/${action}`, { method: "POST" });
  await loadStats();
  await loadJobs();
  showBanner(
    action === "approve"
      ? "Packet approved. Open the original listing and apply yourself."
      : action === "applied"
        ? "Saved to applied history. This listing will not be queued again."
        : `Marked ${action}.`
  );
}

function moveSelection(delta) {
  const list = visibleJobs();
  if (!list.length) return;
  const idx = Math.max(0, list.findIndex((j) => j.id === selectedId));
  const next = list[Math.min(list.length - 1, Math.max(0, idx + delta))];
  if (next) showJob(next.id);
}

jobList.addEventListener("click", (e) => {
  const li = e.target.closest("li[data-id]");
  if (li) showJob(Number(li.dataset.id));
});
statsEl.addEventListener("click", (e) => {
  const btn = e.target.closest(".stat");
  if (!btn) return;
  filter.value = btn.dataset.status;
  loadStats().then(loadJobs);
});
filter.onchange = () => loadStats().then(loadJobs);
search.oninput = renderList;

document.getElementById("runBtn").onclick = async () => {
  setBusy(true, "Fetching jobs and scoring new listings…");
  try {
    const result = await api("/api/run", { method: "POST" });
    const ats = result.ats || {};
    const scored = result.scored || {};
    showBanner(
      `Run finished. Fetched ${ats.fetched ?? 0}, new ${ats.inserted ?? 0}, already applied ${ats.already_applied ?? 0}, scored ${scored.processed ?? 0}.`
    );
    filter.value = "queued";
    await loadStats();
    await loadJobs();
  } catch (err) {
    showBanner(String(err));
  } finally {
    setBusy(false);
  }
};

function openDrawer() {
  drawer.hidden = false;
  document.getElementById("pasteText").focus();
}
function closeDrawer() {
  drawer.hidden = true;
}
document.getElementById("pasteOpen").onclick = openDrawer;
document.getElementById("pasteClose").onclick = closeDrawer;
drawer.addEventListener("click", (e) => {
  if (e.target === drawer) closeDrawer();
});

document.getElementById("pasteBtn").onclick = async () => {
  const text = document.getElementById("pasteText").value.trim();
  const url = document.getElementById("pasteUrl").value.trim() || null;
  if (text.length < 20) return showBanner("Paste a fuller job description first.");
  setBusy(true, "Scoring with your profile…");
  try {
    const result = await api("/api/inbox", { method: "POST", body: JSON.stringify({ text, url }) });
    document.getElementById("pasteText").value = "";
    closeDrawer();
    if (result.ingest.already_applied) {
      showBanner(`Already applied: ${result.ingest.title} at ${result.ingest.company}. Not queued again.`);
      filter.value = "applied";
    } else {
      showBanner(`Ingested: ${result.ingest.title} at ${result.ingest.company}`);
      filter.value = "queued";
    }
    await loadStats();
    await loadJobs();
    if (result.job) await showJob(result.job.id);
  } catch (err) {
    showBanner(String(err));
  } finally {
    setBusy(false);
  }
};

document.addEventListener("keydown", (e) => {
  const typing = ["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName);
  if (e.key === "Escape") closeDrawer();
  if (typing) return;
  if (e.key === "j") moveSelection(1);
  if (e.key === "k") moveSelection(-1);
  if (e.key === "a" && selectedId) act(selectedId, "approve");
  if (e.key === "x" && selectedId) act(selectedId, "skip");
  if (e.key === "c") {
    const cover = document.getElementById("cover");
    if (cover) copyText(cover.value, "Cover copied");
  }
  if (e.key === "p") openDrawer();
});

loadMe()
  .then(loadStats)
  .then(loadJobs)
  .catch((err) => showBanner(String(err)));
