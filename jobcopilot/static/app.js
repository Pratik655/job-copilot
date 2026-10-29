// ==============================================================================
// JOB COPILOT — MULTI-DOMAIN CAREER & APPLICATION WORKSPACE
// ==============================================================================

// View Stepper & Pages (Desktop & Mobile)
const navPref = document.getElementById("navPref");
const navJobs = document.getElementById("navJobs");
const navPacket = document.getElementById("navPacket");
const viewPref = document.getElementById("viewPreferences");
const viewJobs = document.getElementById("viewJobs");
const viewPacket = document.getElementById("viewPacket");
const navJobCount = document.getElementById("navJobCount");

// Android Mobile Bottom Navigation
const mobileNavPref = document.getElementById("mobileNavPref");
const mobileNavJobs = document.getElementById("mobileNavJobs");
const mobileNavPacket = document.getElementById("mobileNavPacket");
const mobileNavJobCount = document.getElementById("mobileNavJobCount");

// Notifications & Overlays
const banner = document.getElementById("banner");
const overlay = document.getElementById("overlay");
const overlayText = document.getElementById("overlayText");
const scanStepList = document.getElementById("scanStepList");

// Strictly force hide overlay on initial script load
if (overlay) {
  overlay.setAttribute("hidden", "");
  overlay.classList.remove("active");
  overlay.style.setProperty("display", "none", "important");
}

// Autosync elements
const syncDot = document.getElementById("syncDot");
const syncStatusLabel = document.getElementById("syncStatusLabel");
const toggleAutoSyncBtn = document.getElementById("toggleAutoSyncBtn");

// Feed & Filters
const jobList = document.getElementById("jobList");
const statusTabs = document.getElementById("statusTabs");
const domainFilter = document.getElementById("domainFilter");
const cityFilter = document.getElementById("cityFilter");
const search = document.getElementById("search");
const onlySelectedCitiesToggle = document.getElementById("onlySelectedCitiesToggle");
const jobsCountLabel = document.getElementById("jobsCountLabel");
const quickPreviewPane = document.getElementById("quickPreviewPane");
const emptyPreview = document.getElementById("emptyPreview");
const previewContent = document.getElementById("previewContent");

// Profile / Preferences elements
const dropzone = document.getElementById("dropzone");
const resumeFileInput = document.getElementById("resumeFileInput");
const browseFileBtn = document.getElementById("browseFileBtn");
const existingResumeRow = document.getElementById("existingResumeRow");
const existingResumeName = document.getElementById("existingResumeName");
const scanExistingBtn = document.getElementById("scanExistingBtn");
const togglePasteResumeBtn = document.getElementById("togglePasteResumeBtn");
const pasteResumeArea = document.getElementById("pasteResumeArea");
const rawResumeText = document.getElementById("rawResumeText");
const scanRawTextBtn = document.getElementById("scanRawTextBtn");

const profName = document.getElementById("profName");
const profDegree = document.getElementById("profDegree");
const profYear = document.getElementById("profYear");
const profUniversity = document.getElementById("profUniversity");
const profCurrentLoc = document.getElementById("profCurrentLoc");
const skillsChips = document.getElementById("skillsChips");
const newSkillInput = document.getElementById("newSkillInput");
const addSkillBtn = document.getElementById("addSkillBtn");

const cityPillsGrid = document.getElementById("cityPillsGrid");
const customCityInput = document.getElementById("customCityInput");
const addCustomCityBtn = document.getElementById("addCustomCityBtn");
const selectAllCitiesBtn = document.getElementById("selectAllCitiesBtn");
const selectTopCitiesBtn = document.getElementById("selectTopCitiesBtn");
const clearCitiesBtn = document.getElementById("clearCitiesBtn");

const domainCardsGrid = document.getElementById("domainCardsGrid");
const customDomainInput = document.getElementById("customDomainInput");
const addCustomDomainBtn = document.getElementById("addCustomDomainBtn");
const selectAllDomainsBtn = document.getElementById("selectAllDomainsBtn");
const clearDomainsBtn = document.getElementById("clearDomainsBtn");
const saveAndContinueBtn = document.getElementById("saveAndContinueBtn");

// Packet & Review elements
const backToJobsBtn = document.getElementById("backToJobsBtn");
const packetTitle = document.getElementById("packetTitle");
const packetScoreBadge = document.getElementById("packetScoreBadge");
const packetCompany = document.getElementById("packetCompany");
const packetCity = document.getElementById("packetCity");
const packetDomain = document.getElementById("packetDomain");
const packetExp = document.getElementById("packetExp");
const btnPacketApply = document.getElementById("btnPacketApply");
const btnPacketApprove = document.getElementById("btnPacketApprove");
const btnPacketMarkApplied = document.getElementById("btnPacketMarkApplied");
const btnPacketSkip = document.getElementById("btnPacketSkip");
const btnPacketGenerateAi = document.getElementById("btnPacketGenerateAi");
const fitPillsRow = document.getElementById("fitPillsRow");
const matchedSkillsRow = document.getElementById("matchedSkillsRow");

const packetTabs = document.getElementById("packetTabs");
const coverLetterText = document.getElementById("coverLetterText");
const copyCoverBtn = document.getElementById("copyCoverBtn");
const resumeBulletsList = document.getElementById("resumeBulletsList");
const copyBulletsBtn = document.getElementById("copyBulletsBtn");
const referralText = document.getElementById("referralText");
const copyReferralBtn = document.getElementById("copyReferralBtn");
const screeningQaList = document.getElementById("screeningQaList");
const fullJdContent = document.getElementById("fullJdContent");
const originalLinkAnchor = document.getElementById("originalLinkAnchor");

const appliedTableBody = document.getElementById("appliedTableBody");
const exportHistoryCsvBtn = document.getElementById("exportHistoryCsvBtn");

// Modals & Menu
const moreBtn = document.getElementById("moreBtn");
const moreMenu = document.getElementById("moreMenu");
const pasteModal = document.getElementById("pasteModal");
const pasteOpen = document.getElementById("pasteOpen");
const openPasteBtn = document.getElementById("openPasteBtn");
const pasteCloseBtn = document.getElementById("pasteCloseBtn");
const pasteCancelBtn = document.getElementById("pasteCancelBtn");
const pasteSubmitBtn = document.getElementById("pasteSubmitBtn");
const pasteUrl = document.getElementById("pasteUrl");
const pasteText = document.getElementById("pasteText");

const runBtn = document.getElementById("runBtn");
const fetchSyncBtn = document.getElementById("fetchSyncBtn");
const rescoreBtn = document.getElementById("rescoreBtn");
const exportCsvBtn = document.getElementById("exportCsvBtn");
const exportAllBtn = document.getElementById("exportAllBtn");

const clearProfileBtn = document.getElementById("clearProfileBtn");
const resetResumeBtn = document.getElementById("resetResumeBtn");

// State
let currentView = "preferences";
let jobs = [];
let selectedJobId = null;
let currentStatus = "queued";
let activePacketTab = "cover";
let profileData = {};
let availableCities = [];
let availableDomains = [];
let currentSkills = [];
let hasUploadedResume = sessionStorage.getItem("jobcopilot_has_resume") === "true";

// ==============================================================================
// UTILITIES & API
// ==============================================================================

function showToast(text, isError = false) {
  if (!text) {
    banner.hidden = true;
    return;
  }
  banner.hidden = false;
  banner.textContent = text;
  banner.style.borderColor = isError ? "#f85149" : "var(--accent)";
  setTimeout(() => {
    banner.hidden = true;
  }, 4500);
}

function setBusy(on, text = "Working…", showSteps = false) {
  if (!overlay) return;
  if (on) {
    overlay.removeAttribute("hidden");
    overlay.classList.add("active");
    overlay.style.setProperty("display", "flex", "important");
  } else {
    overlay.setAttribute("hidden", "");
    overlay.classList.remove("active");
    overlay.style.setProperty("display", "none", "important");
  }
  if (overlayText) overlayText.textContent = text;
  if (scanStepList) {
    scanStepList.hidden = !showSteps;
    scanStepList.style.display = showSteps ? "block" : "none";
  }
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: opts.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(errText || res.statusText);
  }
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return res.json();
  }
  return res.text();
}

function escapeHtml(s) {
  if (s == null) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function scoreClass(n) {
  if (n == null) return "mid";
  if (n >= 70) return "high";
  if (n >= 50) return "mid";
  return "low";
}

// ==============================================================================
// VIEW SWITCHING
// ==============================================================================

function switchView(viewName) {
  currentView = viewName;
  // Clear active states on desktop stepper & mobile bottom bar
  [navPref, navJobs, navPacket].forEach((btn) => btn && btn.classList.remove("active"));
  [mobileNavPref, mobileNavJobs, mobileNavPacket].forEach((btn) => btn && btn.classList.remove("active"));
  [viewPref, viewJobs, viewPacket].forEach((page) => page && page.classList.remove("active"));

  if (viewName === "preferences") {
    if (navPref) navPref.classList.add("active");
    if (mobileNavPref) mobileNavPref.classList.add("active");
    if (viewPref) viewPref.classList.add("active");
    window.scrollTo({ top: 0, behavior: "smooth" });
  } else if (viewName === "jobs") {
    if (navJobs) navJobs.classList.add("active");
    if (mobileNavJobs) mobileNavJobs.classList.add("active");
    if (viewJobs) viewJobs.classList.add("active");
    loadStats();
    loadJobs();
    window.scrollTo({ top: 0, behavior: "smooth" });
  } else if (viewName === "packet") {
    if (navPacket) navPacket.classList.add("active");
    if (mobileNavPacket) mobileNavPacket.classList.add("active");
    if (viewPacket) viewPacket.classList.add("active");
    if (selectedJobId) {
      loadPacketDetail(selectedJobId);
    }
    loadApplyHistory();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

if (navPref) navPref.addEventListener("click", () => switchView("preferences"));
if (navJobs) navJobs.addEventListener("click", () => switchView("jobs"));
if (navPacket) navPacket.addEventListener("click", () => switchView("packet"));

if (mobileNavPref) mobileNavPref.addEventListener("click", () => switchView("preferences"));
if (mobileNavJobs) mobileNavJobs.addEventListener("click", () => switchView("jobs"));
if (mobileNavPacket) mobileNavPacket.addEventListener("click", () => switchView("packet"));

if (backToJobsBtn) backToJobsBtn.addEventListener("click", () => switchView("jobs"));

// ==============================================================================
// PAGE 1: PREFERENCES & RESUME SCANNER
// ==============================================================================

async function loadPreferences() {
  try {
    const data = await api("/api/preferences");
    profileData = data.profile || {};
    availableCities = data.all_cities || [];
    availableDomains = data.all_domains || [];

    const tag = document.getElementById("scanStatusTag");
    if (hasUploadedResume) {
      profName.value = profileData.name || "";
      profDegree.value = profileData.degree || "";
      profYear.value = profileData.graduating_year || 2026;
      profUniversity.value = profileData.university || "";
      profCurrentLoc.value = profileData.current_location || "";
      currentSkills = Array.isArray(profileData.stack) ? [...profileData.stack] : [];
      if (tag) {
        tag.textContent = "Active Profile";
        tag.className = "tag-status";
      }
    } else {
      profName.value = "";
      profDegree.value = "";
      profYear.value = "";
      profUniversity.value = "";
      profCurrentLoc.value = "";
      currentSkills = [];
      if (tag) {
        tag.textContent = "Awaiting Resume";
        tag.className = "tag-status tag-status-awaiting";
      }
    }

    renderSkillsChips();
    renderCityPills();
    renderDomainCards();
  } catch (err) {
    console.error("Preferences load error:", err);
  }
}

function renderSkillsChips() {
  if (!currentSkills || !currentSkills.length) {
    skillsChips.innerHTML = `<span class="skills-empty-hint">Drop your resume above to auto-extract technical skills.</span>`;
    return;
  }
  skillsChips.innerHTML = currentSkills
    .map(
      (sk) => `
      <span class="chip">
        ${escapeHtml(sk)}
        <button type="button" class="chip-remove" data-skill="${escapeHtml(sk)}" aria-label="Remove skill">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="pointer-events: none;">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </span>
    `
    )
    .join("");

  skillsChips.querySelectorAll(".chip-remove").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sk = btn.getAttribute("data-skill");
      currentSkills = currentSkills.filter((s) => s !== sk);
      renderSkillsChips();
    });
  });
}

function addSkill(sk) {
  const clean = (sk || "").trim();
  if (clean && !currentSkills.includes(clean)) {
    currentSkills.push(clean);
    renderSkillsChips();
  }
  newSkillInput.value = "";
}

addSkillBtn.addEventListener("click", () => addSkill(newSkillInput.value));
newSkillInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    addSkill(newSkillInput.value);
  }
});

function renderCityPills() {
  const selected = new Set(profileData.open_to || []);
  
  // Combine all_cities and any custom ones from profile
  const allUnique = Array.from(new Set([...availableCities, ...(profileData.open_to || [])]));

  cityPillsGrid.innerHTML = allUnique
    .map((city) => {
      const isChecked = selected.has(city);
      return `
        <label class="pill-check-item ${isChecked ? "checked" : ""}">
          <input type="checkbox" value="${escapeHtml(city)}" ${isChecked ? "checked" : ""} />
          <span class="pill-check-label">${escapeHtml(city)}</span>
        </label>
      `;
    })
    .join("");

  cityPillsGrid.querySelectorAll("input[type='checkbox']").forEach((cb) => {
    cb.addEventListener("change", (e) => {
      const parent = cb.closest(".pill-check-item");
      if (cb.checked) {
        parent.classList.add("checked");
      } else {
        parent.classList.remove("checked");
      }
    });
  });
}

function getSelectedCities() {
  const checked = [];
  cityPillsGrid.querySelectorAll("input[type='checkbox']:checked").forEach((cb) => {
    checked.push(cb.value);
  });
  return checked;
}

selectAllCitiesBtn.addEventListener("click", () => {
  cityPillsGrid.querySelectorAll(".pill-check-item").forEach((el) => {
    el.classList.add("checked");
    el.querySelector("input").checked = true;
  });
});

selectTopCitiesBtn.addEventListener("click", () => {
  const topSet = new Set(["Bangalore", "Hyderabad", "Pune", "Delhi-NCR", "Remote India", "Mumbai", "Chennai"]);
  cityPillsGrid.querySelectorAll(".pill-check-item").forEach((el) => {
    const val = el.querySelector("input").value;
    const isTop = topSet.has(val);
    el.classList.toggle("checked", isTop);
    el.querySelector("input").checked = isTop;
  });
});

clearCitiesBtn.addEventListener("click", () => {
  cityPillsGrid.querySelectorAll(".pill-check-item").forEach((el) => {
    el.classList.remove("checked");
    el.querySelector("input").checked = false;
  });
});

addCustomCityBtn.addEventListener("click", () => {
  const val = (customCityInput.value || "").trim();
  if (!val) return;
  if (!availableCities.includes(val)) {
    availableCities.push(val);
  }
  if (!profileData.open_to) profileData.open_to = [];
  if (!profileData.open_to.includes(val)) profileData.open_to.push(val);
  renderCityPills();
  customCityInput.value = "";
  showToast(`Added "${val}" to target locations`);
});

customCityInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    addCustomCityBtn.click();
  }
});

function renderDomainCards() {
  const selected = new Set(profileData.target_domains || []);

  domainCardsGrid.innerHTML = availableDomains
    .map((dom) => {
      const isChecked = selected.has(dom.key);
      return `
        <label class="domain-card-item ${isChecked ? "checked" : ""}">
          <input type="checkbox" value="${escapeHtml(dom.key)}" ${isChecked ? "checked" : ""} />
          <div class="domain-info">
            <div class="domain-title">${escapeHtml(dom.label)}</div>
            <div class="domain-desc">${escapeHtml(dom.desc)}</div>
          </div>
        </label>
      `;
    })
    .join("");

  domainCardsGrid.querySelectorAll("input[type='checkbox']").forEach((cb) => {
    cb.addEventListener("change", (e) => {
      const parent = cb.closest(".domain-card-item");
      if (cb.checked) {
        parent.classList.add("checked");
      } else {
        parent.classList.remove("checked");
      }
    });
  });
}

function getSelectedDomains() {
  const checked = [];
  domainCardsGrid.querySelectorAll("input[type='checkbox']:checked").forEach((cb) => {
    checked.push(cb.value);
  });
  return checked;
}

selectAllDomainsBtn.addEventListener("click", () => {
  domainCardsGrid.querySelectorAll(".domain-card-item").forEach((el) => {
    el.classList.add("checked");
    el.querySelector("input").checked = true;
  });
});

clearDomainsBtn.addEventListener("click", () => {
  domainCardsGrid.querySelectorAll(".domain-card-item").forEach((el) => {
    el.classList.remove("checked");
    el.querySelector("input").checked = false;
  });
});

addCustomDomainBtn.addEventListener("click", () => {
  const val = (customDomainInput.value || "").trim();
  if (!val) return;
  const key = val.toLowerCase().replace(/[^a-z0-9]/g, "_");
  availableDomains.push({
    key: key,
    label: val,
    desc: "Custom added target field",
  });
  if (!profileData.target_domains) profileData.target_domains = [];
  profileData.target_domains.push(key);
  renderDomainCards();
  customDomainInput.value = "";
  showToast(`Added "${val}" to target fields`);
});

// Resume Upload & Scanning Flow
browseFileBtn.addEventListener("click", () => resumeFileInput.click());
dropzone.addEventListener("click", (e) => {
  if (e.target !== browseFileBtn) resumeFileInput.click();
});

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files && e.dataTransfer.files.length) {
    handleFileUpload(e.dataTransfer.files[0]);
  }
});

resumeFileInput.addEventListener("change", (e) => {
  if (e.target.files && e.target.files.length) {
    handleFileUpload(e.target.files[0]);
  }
});

async function simulateScanSteps() {
  setBusy(true, "Scanning resume with AI extraction…", true);
  const steps = ["step1", "step2", "step3", "step4"];
  for (let i = 0; i < steps.length; i++) {
    const el = document.getElementById(steps[i]);
    if (el) el.classList.add("active");
    await new Promise((r) => setTimeout(r, 250));
    if (el) {
      el.classList.remove("active");
      el.classList.add("done");
    }
  }
}

async function autoProcessParsedResume(res, sourceLabel) {
  hasUploadedResume = true;
  sessionStorage.setItem("jobcopilot_has_resume", "true");
  applyParsedData(res.parsed);
  setBusy(true, "Auto-saving profile, searching & scoring matching jobs in background…");
  try {
    await api("/api/resume/save", {
      method: "POST",
      body: JSON.stringify({
        parsed: res.parsed,
        raw_text: res.raw_text,
        rescore: true,
        trigger_sync: true,
      }),
    });
    await loadStats();
    await loadJobs();
    setBusy(false);
    showToast(`✓ ${sourceLabel}: Found ${res.parsed.skills_count} skills. Live jobs scored & matched!`);
    switchView("jobs");
  } catch (saveErr) {
    console.error("Auto save & match error:", saveErr);
    setBusy(false);
    showToast(`✓ Resume scanned! Switched to job matches.`);
    switchView("jobs");
  }
}

async function handleFileUpload(file) {
  try {
    await simulateScanSteps();
    const formData = new FormData();
    formData.append("file", file);

    const res = await api("/api/resume/upload", {
      method: "POST",
      body: formData,
    });

    await autoProcessParsedResume(res, `Scanned "${file.name}"`);
  } catch (err) {
    setBusy(false);
    showToast(`Failed to parse resume: ${err.message}`, true);
  }
}

if (scanExistingBtn) {
  scanExistingBtn.addEventListener("click", async () => {
    try {
      await simulateScanSteps();
      const res = await api("/api/resume/scan-existing", { method: "POST" });
      await autoProcessParsedResume(res, `Scanned existing resume`);
    } catch (err) {
      setBusy(false);
      showToast(`Scan error: ${err.message}`, true);
    }
  });
}

togglePasteResumeBtn.addEventListener("click", () => {
  pasteResumeArea.hidden = !pasteResumeArea.hidden;
});

scanRawTextBtn.addEventListener("click", async () => {
  const text = rawResumeText.value.trim();
  if (text.length < 10) {
    showToast("Please paste your resume text first", true);
    return;
  }
  try {
    await simulateScanSteps();
    const res = await api("/api/resume/scan-text", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    await autoProcessParsedResume(res, `Parsed resume text`);
  } catch (err) {
    setBusy(false);
    showToast(`Scan error: ${err.message}`, true);
  }
});

function applyParsedData(parsed) {
  if (!parsed) return;
  if (parsed.name) profName.value = parsed.name;
  if (parsed.degree) profDegree.value = parsed.degree;
  if (parsed.graduating_year) profYear.value = parsed.graduating_year;
  if (parsed.university) profUniversity.value = parsed.university;
  if (parsed.skills && Array.isArray(parsed.skills)) {
    currentSkills = Array.from(new Set([...currentSkills, ...parsed.skills]));
    renderSkillsChips();
  }
  if (parsed.recommended_domains && Array.isArray(parsed.recommended_domains)) {
    profileData.target_domains = Array.from(
      new Set([...(profileData.target_domains || []), ...parsed.recommended_domains])
    );
    renderDomainCards();
  }
  const tag = document.getElementById("scanStatusTag");
  if (tag) {
    tag.textContent = "AI Parsed & Updated";
    tag.style.background = "var(--blue-soft)";
    tag.style.color = "var(--blue)";
  }
}

saveAndContinueBtn.addEventListener("click", async () => {
  const payload = {
    name: profName.value.trim(),
    degree: profDegree.value.trim(),
    graduating_year: parseInt(profYear.value, 10) || 2026,
    university: profUniversity.value.trim(),
    current_location: profCurrentLoc.value.trim(),
    stack: currentSkills,
    open_to: getSelectedCities(),
    target_domains: getSelectedDomains(),
  };

  try {
    setBusy(true, "Saving preferences & re-scoring jobs…");
    await api("/api/preferences", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    await api("/api/rescore", { method: "POST" });
    hasUploadedResume = true;
    sessionStorage.setItem("jobcopilot_has_resume", "true");
    setBusy(false);
    showToast("Preferences saved! Re-scored matching opportunities.");
    switchView("jobs");
  } catch (err) {
    setBusy(false);
    showToast(`Save error: ${err.message}`, true);
  }
});

// ==============================================================================
// PAGE 2: LIVE JOB FEED & SPLIT PREVIEW
// ==============================================================================

async function loadStats() {
  const qEl = document.getElementById("countQueued");
  const rEl = document.getElementById("countReady");
  const aEl = document.getElementById("countApplied");
  const sEl = document.getElementById("countSkipped");
  const tEl = document.getElementById("countTotal");

  if (!hasUploadedResume) {
    if (navJobCount) navJobCount.textContent = "0";
    if (mobileNavJobCount) mobileNavJobCount.textContent = "0";
    if (qEl) qEl.textContent = "0";
    if (rEl) rEl.textContent = "0";
    if (aEl) aEl.textContent = "0";
    if (sEl) sEl.textContent = "0";
    if (tEl) tEl.textContent = "0";
    return;
  }

  try {
    const counts = await api("/api/stats");
    const totalAll = Object.values(counts).reduce((a, b) => a + b, 0);

    if (qEl) qEl.textContent = counts.queued ?? 0;
    if (rEl) rEl.textContent = counts.ready ?? 0;
    if (aEl) aEl.textContent = counts.applied ?? 0;
    if (sEl) sEl.textContent = counts.skipped ?? 0;
    if (tEl) tEl.textContent = totalAll;

    const queuedCount = counts.queued ?? 0;
    if (navJobCount) navJobCount.textContent = queuedCount;
    if (mobileNavJobCount) mobileNavJobCount.textContent = queuedCount;
  } catch (err) {
    console.error("Stats load failed:", err);
  }
}

async function loadCityFilterOptions() {
  try {
    const data = await api("/api/filters");
    if (data.cities && data.cities.length) {
      const cur = cityFilter.value;
      const opts = [
        '<option value="">All Locations</option>',
        ...data.cities.slice(0, 20).map(
          (c) => `<option value="${escapeHtml(c.city)}">${escapeHtml(c.city)} (${c.count})</option>`
        ),
      ];
      cityFilter.innerHTML = opts.join("");
      cityFilter.value = cur;
    }
  } catch (err) {
    console.warn("City filter options failed:", err);
  }
}

function renderNoResumeState() {
  jobs = [];
  jobsCountLabel.textContent = "0 roles matched";
  jobList.innerHTML = `
    <li class="empty-matches-prompt">
      <div class="empty-prompt-icon">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="12" y1="18" x2="12" y2="12"></line>
          <line x1="9" y1="15" x2="15" y2="15"></line>
        </svg>
      </div>
      <h3>No Resume Uploaded Yet</h3>
      <p>To view matching jobs and calculate fit scores, please upload your resume in Step 1. Job Copilot will extract your technical stack and rank 580+ live openings.</p>
      <button type="button" class="btn-accent btn-sm" id="emptyGoToUploadBtn">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 5px;">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        Upload Resume in Step 1
      </button>
    </li>
  `;
  const btn = document.getElementById("emptyGoToUploadBtn");
  if (btn) btn.addEventListener("click", () => switchView("preferences"));

  renderEmptyPreview(true);
}

async function loadJobs() {
  if (!hasUploadedResume) {
    renderNoResumeState();
    return;
  }

  const params = new URLSearchParams();
  if (currentStatus) params.set("status", currentStatus);
  if (cityFilter.value) params.set("city", cityFilter.value);
  if (domainFilter.value) params.set("domain", domainFilter.value);
  if (search.value.trim()) params.set("search", search.value.trim());

  const q = params.toString() ? `?${params.toString()}` : "";
  jobs = await api("/api/jobs" + q);

  // If "only selected cities" toggle is ON, filter client-side against profile.open_to
  if (onlySelectedCitiesToggle.checked && profileData.open_to && profileData.open_to.length) {
    const selSet = new Set(profileData.open_to.map((c) => c.toLowerCase()));
    jobs = jobs.filter((j) => {
      const c = (j.city || j.location || "").toLowerCase();
      return Array.from(selSet).some((s) => c.includes(s));
    });
  }

  renderJobList();

  if (selectedJobId) {
    const still = jobs.find((j) => j.id === selectedJobId);
    if (still) renderQuickPreview(still);
    else if (jobs.length > 0) renderQuickPreview(jobs[0]);
    else renderEmptyPreview();
  } else if (jobs.length > 0) {
    renderQuickPreview(jobs[0]);
  } else {
    renderEmptyPreview();
  }
}

function renderJobList() {
  jobsCountLabel.textContent = `${jobs.length} ${jobs.length === 1 ? "role" : "roles"}`;
  const mobileJobsCount = document.getElementById("mobileJobsCount");
  if (mobileJobsCount) {
    mobileJobsCount.textContent = jobs.length;
  }
  if (!jobs.length) {
    jobList.innerHTML = `<li style="padding: 2.5rem 1rem; text-align: center; color: var(--text-dim); font-size: 13px;">No opportunities found matching criteria.</li>`;
    return;
  }

  jobList.innerHTML = jobs
    .map((j) => {
      const city = j.city || j.location || "Flexible";
      const domain = j.domain || "Opportunity";
      const score = j.score ?? "–";
      const sCls = scoreClass(j.score);
      const isAct = j.id === selectedJobId ? "active" : "";

      return `
        <li data-id="${j.id}" class="job-card ${isAct}">
          <div class="card-top">
            <span class="card-title">${escapeHtml(j.title)}</span>
            <span class="score-pill ${sCls}">${score}</span>
          </div>
          <div class="card-sub">${escapeHtml(j.company)} · ${escapeHtml(city)}</div>
          <div class="card-meta">
            <span class="tag-subtle">${escapeHtml(domain)}</span>
            <span class="tag-subtle">${escapeHtml(j.experience_level || "Fresher")}</span>
          </div>
        </li>
      `;
    })
    .join("");

  jobList.querySelectorAll(".job-card").forEach((card) => {
    card.addEventListener("click", () => {
      const id = parseInt(card.getAttribute("data-id"), 10);
      selectJob(id);
    });
    card.addEventListener("dblclick", () => {
      const id = parseInt(card.getAttribute("data-id"), 10);
      selectJob(id);
      switchView("packet");
    });
  });
}

function selectJob(id) {
  selectedJobId = id;
  jobList.querySelectorAll(".job-card").forEach((c) => {
    c.classList.toggle("active", parseInt(c.getAttribute("data-id"), 10) === id);
  });
  const found = jobs.find((j) => j.id === id);
  if (found) {
    renderQuickPreview(found);
    const mDetailTabLabel = document.getElementById("mDetailTabLabel");
    if (mDetailTabLabel) {
      mDetailTabLabel.textContent = `${found.company} (${found.score ?? "–"})`;
    }
  }

  // Mobile viewport automatic drawer / tab switch
  if (window.innerWidth <= 900) {
    const feedLayout = document.querySelector(".feed-layout");
    if (feedLayout) {
      feedLayout.classList.remove("show-list");
      feedLayout.classList.add("show-detail");
    }
    const mToggleListBtn = document.getElementById("mToggleListBtn");
    const mToggleDetailBtn = document.getElementById("mToggleDetailBtn");
    if (mToggleListBtn && mToggleDetailBtn) {
      mToggleListBtn.classList.remove("active");
      mToggleDetailBtn.classList.add("active");
    }
    window.scrollTo({ top: 110, behavior: "smooth" });
  }
}

function renderEmptyPreview(awaitingResume = false) {
  emptyPreview.hidden = false;
  previewContent.hidden = true;
  if (awaitingResume) {
    emptyPreview.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon-wrap">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
          </svg>
        </div>
        <h2>Awaiting Resume Upload</h2>
        <p>Drop your resume in Step 1 to unlock personalized matching, fit scores, and tailored application packets.</p>
      </div>
    `;
  } else {
    emptyPreview.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon-wrap">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
        </div>
        <h2>Select a Role to Preview</h2>
        <p>Choose any job card on the left to see full match breakdown, tech stack overlap, and application materials.</p>
      </div>
    `;
  }
}

function renderQuickPreview(job) {
  emptyPreview.hidden = true;
  previewContent.hidden = false;
  selectedJobId = job.id;

  const score = job.score ?? "–";
  const sCls = scoreClass(job.score);
  const city = job.city || job.location || "Flexible";
  const domain = job.domain || "Role";
  const breakdown = job.match_breakdown || {};
  const skills = job.skills_matched || [];
  const coverLetter = (job.draft && job.draft.cover_letter) || "";
  const wordCount = coverLetter ? coverLetter.split(/\s+/).filter(Boolean).length : 220;

  previewContent.innerHTML = `
    <button type="button" class="btn-ghost btn-xs mobile-back-btn" id="mBackToListBtn" style="margin-bottom: 0.85rem; width: 100%; justify-content: flex-start; padding: 0.45rem 0.75rem; display: none;">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 5px;"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
      ← Back to Job Roles List
    </button>

    <div class="preview-header">
      <div class="preview-title-row">
        <h2>${escapeHtml(job.title)}</h2>
        <span class="score-pill-lg ${sCls}">${score}</span>
      </div>
      <div class="preview-sub">${escapeHtml(job.company)} · ${escapeHtml(city)} · ${escapeHtml(domain)}</div>
      
      <div class="preview-actions-row">
        <button type="button" class="btn-accent btn-sm" id="openFullPacketBtn">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 5px; vertical-align: middle;">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
          </svg>
          Open Application Packet
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-left: 5px; vertical-align: middle;">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </button>
        <a href="/open/${job.id}" target="_blank" rel="noopener" class="btn-ghost btn-sm">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 5px; vertical-align: middle;">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
            <polyline points="15 3 21 3 21 9"></polyline>
            <line x1="10" y1="14" x2="21" y2="3"></line>
          </svg>
          Official Apply
        </a>
      </div>
    </div>

    <div class="fit-breakdown-card" style="margin-bottom: 1rem; padding: 1rem;">
      <h3>Match Breakdown</h3>
      <div class="fit-pills-row" style="grid-template-columns: repeat(2, 1fr); margin-bottom: 0.5rem;">
        <div class="fit-pillar-box">
          <div class="fit-pillar-label">Degree &amp; Batch Fit</div>
          <div class="fit-pillar-val">${breakdown.degree_fit ? breakdown.degree_fit.rating : "Pass"} (${breakdown.degree_fit ? breakdown.degree_fit.score : "25"}/25)</div>
        </div>
        <div class="fit-pillar-box">
          <div class="fit-pillar-label">Role &amp; Seniority</div>
          <div class="fit-pillar-val">${breakdown.seniority_fit ? breakdown.seniority_fit.rating : "Pass"} (${breakdown.seniority_fit ? breakdown.seniority_fit.score : "25"}/25)</div>
        </div>
        <div class="fit-pillar-box">
          <div class="fit-pillar-label">Tech &amp; Skills Fit</div>
          <div class="fit-pillar-val">${breakdown.skills_overlap ? breakdown.skills_overlap.rating : "Good"} (${breakdown.skills_overlap ? breakdown.skills_overlap.score : "20"}/30)</div>
        </div>
        <div class="fit-pillar-box">
          <div class="fit-pillar-label">Location Fit</div>
          <div class="fit-pillar-val">${breakdown.location_fit ? breakdown.location_fit.rating : "Match"} (${breakdown.location_fit ? breakdown.location_fit.score : "20"}/20)</div>
        </div>
      </div>

      <div class="matched-skills-row">
        ${skills.map((s) => `<span class="skill-tag-matched">✓ ${escapeHtml(s)}</span>`).join("")}
      </div>
    </div>

    <div class="field" style="margin-top: 1rem;">
      <label style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
        <span>Tailored Executive Cover Letter</span>
        <span style="font-size: 11px; color: var(--blue); font-weight: normal;">Personalized for ${escapeHtml(job.company)}</span>
      </label>
      <div class="mini-cl-box">
        <div class="mini-cl-top">
          <span class="mini-cl-badge">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
            Executive Letter Preview
          </span>
          <span class="mini-cl-words">${wordCount} words</span>
        </div>
        <div class="mini-cl-body">${escapeHtml(coverLetter || "Tailored executive application letter generated automatically in Packet View.")}</div>
        <div class="mini-cl-actions">
          <button type="button" class="btn-ghost btn-xs" id="quickCopyCoverBtn">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            <span>Quick Copy</span>
          </button>
          <button type="button" class="btn-accent btn-xs" id="quickOpenCoverDocBtn">
            <span>Open Executive Letter &amp; Print PDF →</span>
          </button>
        </div>
      </div>
    </div>
  `;

  // Mobile Back Button visibility check
  const mBackBtn = document.getElementById("mBackToListBtn");
  if (mBackBtn) {
    if (window.innerWidth <= 900) {
      mBackBtn.style.display = "inline-flex";
    }
    mBackBtn.addEventListener("click", () => {
      const feedLayout = document.querySelector(".feed-layout");
      if (feedLayout) {
        feedLayout.classList.remove("show-detail");
        feedLayout.classList.add("show-list");
      }
      const mToggleListBtn = document.getElementById("mToggleListBtn");
      const mToggleDetailBtn = document.getElementById("mToggleDetailBtn");
      if (mToggleListBtn && mToggleDetailBtn) {
        mToggleListBtn.classList.add("active");
        mToggleDetailBtn.classList.remove("active");
      }
      window.scrollTo({ top: 110, behavior: "smooth" });
    });
  }

  const openPktBtn = document.getElementById("openFullPacketBtn");
  if (openPktBtn) {
    openPktBtn.addEventListener("click", () => switchView("packet"));
  }

  const quickCopyCoverBtn = document.getElementById("quickCopyCoverBtn");
  if (quickCopyCoverBtn) {
    quickCopyCoverBtn.addEventListener("click", () => {
      copyToClipboard(coverLetter, quickCopyCoverBtn, "✓ Copied!");
    });
  }

  const quickOpenCoverDocBtn = document.getElementById("quickOpenCoverDocBtn");
  if (quickOpenCoverDocBtn) {
    quickOpenCoverDocBtn.addEventListener("click", () => {
      activePacketTab = "cover";
      switchView("packet");
    });
  }
}

// Status Switcher Pills
statusTabs.addEventListener("click", (e) => {
  const pill = e.target.closest(".tab-pill");
  if (!pill) return;
  statusTabs.querySelectorAll(".tab-pill").forEach((p) => p.classList.remove("active"));
  pill.classList.add("active");
  currentStatus = pill.getAttribute("data-status");
  loadJobs();
});

// Filter events
let debounceTimer;
search.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(loadJobs, 200);
});
domainFilter.addEventListener("change", loadJobs);
cityFilter.addEventListener("change", loadJobs);
onlySelectedCitiesToggle.addEventListener("change", loadJobs);

// Keyboard navigation (j/k)
window.addEventListener("keydown", (e) => {
  if (currentView !== "jobs" || ["INPUT", "TEXTAREA"].includes(e.target.tagName)) return;
  if (e.key === "j" || e.key === "ArrowDown") {
    e.preventDefault();
    stepJob(1);
  } else if (e.key === "k" || e.key === "ArrowUp") {
    e.preventDefault();
    stepJob(-1);
  } else if (e.key === "Enter") {
    if (selectedJobId) switchView("packet");
  }
});

function stepJob(delta) {
  if (!jobs.length) return;
  const idx = jobs.findIndex((j) => j.id === selectedJobId);
  const nextIdx = Math.max(0, Math.min(jobs.length - 1, (idx === -1 ? 0 : idx) + delta));
  selectJob(jobs[nextIdx].id);
  const card = jobList.querySelector(`li[data-id="${jobs[nextIdx].id}"]`);
  if (card) card.scrollIntoView({ block: "nearest" });
}

// ==============================================================================
// PAGE 3: APPLICATION COPILOT & PACKET
// ==============================================================================

async function loadPacketDetail(jobId) {
  try {
    const job = await api(`/api/jobs/${jobId}`);
    renderPacketView(job);
  } catch (err) {
    console.error("Load packet error:", err);
  }
}

function renderPacketView(job) {
  selectedJobId = job.id;
  const score = job.score ?? "–";
  const sCls = scoreClass(job.score);

  packetTitle.textContent = job.title;
  packetScoreBadge.textContent = score;
  packetScoreBadge.className = `score-pill-lg ${sCls}`;
  packetCompany.textContent = job.company;
  packetCity.textContent = job.city || job.location || "Flexible";
  packetDomain.textContent = job.domain || "Career Field";
  packetExp.textContent = job.experience_level || "Fresher";

  // Fit Breakdown
  const breakdown = job.match_breakdown || {};
  const skills = job.skills_matched || [];

  fitPillsRow.innerHTML = `
    <div class="fit-pillar-box">
      <div class="fit-pillar-label">Degree &amp; Batch</div>
      <div class="fit-pillar-val">${breakdown.degree_fit ? breakdown.degree_fit.rating : "Pass"} (${breakdown.degree_fit ? breakdown.degree_fit.score : "25"}/25)</div>
    </div>
    <div class="fit-pillar-box">
      <div class="fit-pillar-label">Role &amp; Seniority</div>
      <div class="fit-pillar-val">${breakdown.seniority_fit ? breakdown.seniority_fit.rating : "Pass"} (${breakdown.seniority_fit ? breakdown.seniority_fit.score : "25"}/25)</div>
    </div>
    <div class="fit-pillar-box">
      <div class="fit-pillar-label">Tech &amp; Skills Overlap</div>
      <div class="fit-pillar-val">${breakdown.skills_overlap ? breakdown.skills_overlap.rating : "Good"} (${breakdown.skills_overlap ? breakdown.skills_overlap.score : "20"}/30)</div>
    </div>
    <div class="fit-pillar-box">
      <div class="fit-pillar-label">Location Fit</div>
      <div class="fit-pillar-val">${breakdown.location_fit ? breakdown.location_fit.rating : "Match"} (${breakdown.location_fit ? breakdown.location_fit.score : "20"}/20)</div>
    </div>
  `;

  matchedSkillsRow.innerHTML = skills.length
    ? skills.map((s) => `<span class="skill-tag-matched">✓ ${escapeHtml(s)}</span>`).join("")
    : `<span style="font-size: 11px; color: var(--text-dim);">No specific skills keyword match recorded</span>`;

  // Application Packet Tab Bodies
  currentPacketJob = job;
  const draft = job.draft || {};
  coverLetterText.value = draft.cover_letter || "";
  referralText.value = draft.referral_message || "";
  renderExecutiveCoverLetter(draft.cover_letter || "", job);

  // Resume Bullets
  const bullets = Array.isArray(draft.resume_bullets) ? draft.resume_bullets : [];
  resumeBulletsList.innerHTML = bullets.length
    ? bullets.map((b) => `<div class="bullet-item">• ${escapeHtml(b)}</div>`).join("")
    : `<div class="bullet-item text-dim">No specific bullets generated for this role.</div>`;

  // Screening Q&A
  const qa = draft.screening_answers || {};
  const qaEntries = Object.entries(qa);
  screeningQaList.innerHTML = qaEntries.length
    ? qaEntries
        .map(
          ([q, a]) => `
        <div class="qa-item">
          <div class="qa-q">${escapeHtml(q)}</div>
          <div class="qa-a">${escapeHtml(a)}</div>
        </div>
      `
        )
        .join("")
    : `<div class="bullet-item text-dim">No screening questions recorded.</div>`;

  // Job Description
  fullJdContent.textContent = job.description || "No description provided.";
  originalLinkAnchor.href = job.url || "#";

  // Actions
  if (btnPacketGenerateAi) {
    btnPacketGenerateAi.onclick = async () => {
      const origHtml = btnPacketGenerateAi.innerHTML;
      btnPacketGenerateAi.disabled = true;
      btnPacketGenerateAi.innerHTML = `<span>Generating AI Packet…</span>`;
      showToast("Generating tailored packet with AI API… Please wait.");
      try {
        const updatedJob = await api(`/api/jobs/${job.id}/generate-ai`, { method: "POST" });
        renderPacketView(updatedJob);
        showToast("Application materials generated successfully with AI!");
      } catch (err) {
        showToast("AI Generation failed: " + (err.message || "Network error"));
      } finally {
        btnPacketGenerateAi.disabled = false;
        btnPacketGenerateAi.innerHTML = origHtml;
      }
    };
  }

  btnPacketApply.onclick = () => {
    window.open(`/open/${job.id}`, "_blank");
  };

  btnPacketApprove.onclick = async () => {
    await api(`/api/jobs/${job.id}/approve`, { method: "POST" });
    showToast("Role approved and moved to Ready!");
    loadStats();
  };

  btnPacketMarkApplied.onclick = async () => {
    await api(`/api/jobs/${job.id}/applied`, { method: "POST" });
    showToast("Marked as Applied! Added to Tracker.");
    loadStats();
    loadApplyHistory();
  };

  btnPacketSkip.onclick = async () => {
    await api(`/api/jobs/${job.id}/skip`, { method: "POST" });
    showToast("Role skipped.");
    loadStats();
    switchView("jobs");
  };
}

// ==============================================================================
// EXECUTIVE COVER LETTER RENDERING & FORMATTING SYSTEM
// ==============================================================================

let currentPacketJob = null;
let currentCoverTone = "standard";

function renderExecutiveCoverLetter(rawText, job) {
  currentPacketJob = job || currentPacketJob;
  const name = profName?.value?.trim() || profileData?.name || "Candidate Name";
  const degree = profDegree?.value?.trim() || profileData?.degree || "Degree / Program";
  const year = profYear?.value?.trim() || profileData?.graduating_year || new Date().getFullYear().toString();
  const univ = profUniversity?.value?.trim() || profileData?.university || "";
  const location = profCurrentLoc?.value?.trim() || profileData?.current_location || "";
  const email = profileData?.email || "";
  const phone = profileData?.phone || "";

  const clDocSenderName = document.getElementById("clDocSenderName");
  const clDocSenderTitle = document.getElementById("clDocSenderTitle");
  const clDocEmailText = document.getElementById("clDocEmailText");
  const clDocPhoneText = document.getElementById("clDocPhoneText");
  const clDocLocationText = document.getElementById("clDocLocationText");
  const clDocDate = document.getElementById("clDocDate");
  const clDocRecipientCompany = document.getElementById("clDocRecipientCompany");
  const clDocRecipientLocation = document.getElementById("clDocRecipientLocation");
  const clDocSubjectText = document.getElementById("clDocSubjectText");
  const clDocSalutation = document.getElementById("clDocSalutation");
  const clDocBodyContent = document.getElementById("clDocBodyContent");
  const clDocSignatureScript = document.getElementById("clDocSignatureScript");
  const clDocSignName = document.getElementById("clDocSignName");
  const clDocSignSub = document.getElementById("clDocSignSub");
  const clWordCount = document.getElementById("clWordCount");

  const company = currentPacketJob?.company || "Hiring Organization";
  const title = currentPacketJob?.title || "Software Engineering Role";
  const jobCity = currentPacketJob?.city || currentPacketJob?.location || "Flexible / Remote";

  if (clDocSenderName) clDocSenderName.textContent = name.toUpperCase();
  if (clDocSenderTitle) clDocSenderTitle.textContent = `${degree} · Class of ${year}`;
  if (clDocEmailText) clDocEmailText.textContent = email;
  if (clDocPhoneText) clDocPhoneText.textContent = phone;
  if (clDocLocationText) clDocLocationText.textContent = location;

  const todayStr = new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric", year: "numeric" }).format(new Date());
  if (clDocDate) clDocDate.textContent = todayStr;
  if (clDocRecipientCompany) clDocRecipientCompany.textContent = company;
  if (clDocRecipientLocation) clDocRecipientLocation.textContent = jobCity;
  if (clDocSubjectText) clDocSubjectText.textContent = `Application for ${title} — ${name}`;
  if (clDocSalutation) clDocSalutation.textContent = `Dear ${company} Hiring Team,`;

  if (clDocSignatureScript) clDocSignatureScript.textContent = name;
  if (clDocSignName) clDocSignName.textContent = name;
  if (clDocSignSub) clDocSignSub.textContent = `Candidate for ${title} · ${univ}`;

  // Process raw text into structured paragraphs
  let bodyText = (rawText || "").trim();
  if (!bodyText) {
    bodyText = generateCoverLetterByTone(currentCoverTone, currentPacketJob);
  }

  // Split into clean paragraphs
  let cleanLines = bodyText.split(/\n\s*\n/).map((l) => l.trim()).filter(Boolean);
  if (cleanLines.length && cleanLines[0].toLowerCase().startsWith("dear")) {
    cleanLines.shift();
  }

  // Strip trailing signoffs if present to prevent duplication in document
  while (cleanLines.length) {
    const last = cleanLines[cleanLines.length - 1].toLowerCase();
    if (
      last.startsWith("sincerely") ||
      last.startsWith("thank you") ||
      last.startsWith("warm regards") ||
      last.startsWith("email:") ||
      last.startsWith("phone:") ||
      last.startsWith("github:") ||
      last.startsWith("linkedin:") ||
      last === name.toLowerCase()
    ) {
      cleanLines.pop();
    } else {
      break;
    }
  }

  if (clDocBodyContent) {
    clDocBodyContent.innerHTML = cleanLines
      .map((para) => `<p class="cl-para">${escapeHtml(para)}</p>`)
      .join("");
  }

  // Word count & read time indicator
  const words = bodyText.split(/\s+/).filter(Boolean).length;
  const readMin = Math.max(1, Math.round((words / 200) * 10) / 10);
  if (clWordCount) {
    clWordCount.textContent = `${words} words · ~${readMin} min read`;
  }
}

function generateCoverLetterByTone(tone, job) {
  const name = profName?.value?.trim() || profileData?.name || "Candidate Name";
  const degree = profDegree?.value?.trim() || profileData?.degree || "Degree Program";
  const year = profYear?.value?.trim() || profileData?.graduating_year || new Date().getFullYear().toString();
  const univ = profUniversity?.value?.trim() || profileData?.university || "University";
  const company = job?.company || "the company";
  const title = job?.title || "Software Engineering Role";
  const skills = (job?.skills_matched && job.skills_matched.length)
    ? job.skills_matched.slice(0, 4).join(", ")
    : "full-stack development, modern JavaScript, and Python data analysis";

  if (tone === "tech") {
    return (
      `Dear ${company} Hiring Team,\n\n` +
      `I am writing to submit my application for the ${title} position at ${company}. As a ${degree} student graduating in ${year} from ${univ}, my core technical engineering focuses on ${skills}.\n\n` +
      `My hands-on experience includes developing and deploying full-stack web architectures utilizing Node.js, Express, and MongoDB with complete RESTful API integration, as well as building data preprocessing pipelines with Python, Pandas, and NumPy. I prioritize clean component architecture, scalable design patterns, and test-driven reliability.\n\n` +
      `I am eager to bring this solid engineering foundation to ${company} and actively contribute to your technical roadmap. I look forward to discussing how my skills and problem-solving mindset align with your engineering priorities.\n\n` +
      `Thank you for your time and consideration,\n${name}`
    );
  } else if (tone === "enthusiastic") {
    return (
      `Dear ${company} Hiring Team,\n\n` +
      `I am thrilled to apply for the ${title} opportunity at ${company}! As a final-year ${degree} graduate from ${univ} (Class of ${year}), I have been closely following ${company}'s impressive growth and high-impact engineering culture.\n\n` +
      `I bring an energetic work ethic and practical experience across full-stack web applications and data analysis. I love tackling complex technical challenges, quickly learning new frameworks, and shipping high-quality software that creates real user value.\n\n` +
      `Joining ${company} would be an incredible opportunity to contribute with energy and precision. I would love the chance to connect and discuss how my enthusiasm and skill set can help propel your team forward!\n\n` +
      `Warm regards,\n${name}`
    );
  } else if (tone === "concise") {
    return (
      `Dear ${company} Hiring Team,\n\n` +
      `Please accept my application for the ${title} position at ${company}. I am a ${degree} candidate from ${univ} graduating in ${year}, specializing in ${skills}.\n\n` +
      `Key qualifications include:\n` +
      `• Full-stack web application engineering (Node.js, Express, MongoDB, REST APIs)\n` +
      `• Python data preprocessing, exploratory analysis (EDA), and scripting\n` +
      `• Fast domain comprehension, disciplined Git workflows, and production-first focus\n\n` +
      `I would welcome an interview to discuss how I can deliver immediate value to ${company}.\n\n` +
      `Sincerely,\n${name}`
    );
  } else {
    // Standard formal
    return (
      `Dear Hiring Team,\n\n` +
      `I am ${name}, a final-year ${degree} student graduating in ${year} from ${univ}, actively seeking early-career engineering opportunities. I am excited to submit my application for the ${title} role at ${company}.\n\n` +
      `My technical background centers on full-stack web engineering and Python data analysis, aligning with your work around ${skills}. My hands-on projects include architecting full-stack Node.js and Express web services with MongoDB and building scalable end-to-end data pipelines.\n\n` +
      `I am adaptable, fast at learning new technologies, and passionate about creating tangible impact. I would welcome the opportunity to discuss how my skill set can support ${company}'s goals.\n\n` +
      `Thank you for your time and consideration,\n${name}`
    );
  }
}

// Cover Letter Mode Toggle (Formatted vs Raw)
const clModeFormattedBtn = document.getElementById("clModeFormattedBtn");
const clModeRawBtn = document.getElementById("clModeRawBtn");
const clFormattedDoc = document.getElementById("clFormattedDoc");
const clRawEditorWrap = document.getElementById("clRawEditorWrap");
const clToneSelector = document.getElementById("clToneSelector");
const printCoverBtn = document.getElementById("printCoverBtn");

if (clModeFormattedBtn && clModeRawBtn) {
  clModeFormattedBtn.addEventListener("click", () => {
    clModeFormattedBtn.classList.add("active");
    clModeRawBtn.classList.remove("active");
    if (clFormattedDoc) clFormattedDoc.style.display = "block";
    if (clRawEditorWrap) clRawEditorWrap.style.display = "none";
    if (currentPacketJob) {
      renderExecutiveCoverLetter(coverLetterText.value, currentPacketJob);
    }
  });

  clModeRawBtn.addEventListener("click", () => {
    clModeRawBtn.classList.add("active");
    clModeFormattedBtn.classList.remove("active");
    if (clFormattedDoc) clFormattedDoc.style.display = "none";
    if (clRawEditorWrap) clRawEditorWrap.style.display = "block";
    coverLetterText.focus();
  });
}

if (clToneSelector) {
  clToneSelector.addEventListener("change", (e) => {
    currentCoverTone = e.target.value;
    if (currentPacketJob) {
      const newLetter = generateCoverLetterByTone(currentCoverTone, currentPacketJob);
      coverLetterText.value = newLetter;
      renderExecutiveCoverLetter(newLetter, currentPacketJob);
      showToast(`Cover letter updated with ${clToneSelector.options[clToneSelector.selectedIndex].text} tone!`);
    }
  });
}

if (printCoverBtn) {
  printCoverBtn.addEventListener("click", () => {
    if (clModeFormattedBtn && clFormattedDoc) {
      clModeFormattedBtn.click();
    }
    setTimeout(() => {
      window.print();
    }, 150);
  });
}

if (coverLetterText) {
  coverLetterText.addEventListener("input", () => {
    if (currentPacketJob) {
      renderExecutiveCoverLetter(coverLetterText.value, currentPacketJob);
    }
  });
}

// Mobile Feed Toggle
const mToggleListBtn = document.getElementById("mToggleListBtn");
const mToggleDetailBtn = document.getElementById("mToggleDetailBtn");
const feedLayout = document.querySelector(".feed-layout");

if (feedLayout) {
  feedLayout.classList.add("show-list");
}

if (mToggleListBtn && mToggleDetailBtn) {
  mToggleListBtn.addEventListener("click", () => {
    mToggleListBtn.classList.add("active");
    mToggleDetailBtn.classList.remove("active");
    if (feedLayout) {
      feedLayout.classList.remove("show-detail");
      feedLayout.classList.add("show-list");
    }
    window.scrollTo({ top: 110, behavior: "smooth" });
  });

  mToggleDetailBtn.addEventListener("click", () => {
    mToggleDetailBtn.classList.add("active");
    mToggleListBtn.classList.remove("active");
    if (feedLayout) {
      feedLayout.classList.remove("show-list");
      feedLayout.classList.add("show-detail");
    }
    window.scrollTo({ top: 110, behavior: "smooth" });
  });
}

// Packet Tabs navigation
packetTabs.addEventListener("click", (e) => {
  const btn = e.target.closest(".pkt-tab-btn");
  if (!btn) return;
  packetTabs.querySelectorAll(".pkt-tab-btn").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  activePacketTab = btn.getAttribute("data-tab");

  const tabMap = {
    cover: "tabCover",
    bullets: "tabBullets",
    referral: "tabReferral",
    qa: "tabQa",
    jd: "tabJd",
  };

  document.querySelectorAll(".pkt-tab-panel").forEach((p) => p.classList.remove("active"));
  const activePanel = document.getElementById(tabMap[activePacketTab]);
  if (activePanel) activePanel.classList.add("active");
});

// Copy to Clipboard Helpers
async function copyToClipboard(text, btnElement, successLabel = "✓ Copied!") {
  try {
    await navigator.clipboard.writeText(text);
    const orig = btnElement.textContent;
    btnElement.textContent = successLabel;
    setTimeout(() => {
      btnElement.textContent = orig;
    }, 2000);
  } catch (err) {
    showToast("Clipboard copy failed", true);
  }
}

copyCoverBtn.addEventListener("click", () => {
  copyToClipboard(coverLetterText.value, copyCoverBtn);
});

copyBulletsBtn.addEventListener("click", () => {
  const bullets = Array.from(resumeBulletsList.querySelectorAll(".bullet-item")).map(
    (el) => el.textContent
  );
  copyToClipboard(bullets.join("\n"), copyBulletsBtn);
});

copyReferralBtn.addEventListener("click", () => {
  copyToClipboard(referralText.value, copyReferralBtn);
});

async function loadApplyHistory() {
  try {
    const list = await api("/api/history");
    if (!list.length) {
      appliedTableBody.innerHTML = `<tr><td colspan="4" class="text-center text-dim">No applied roles recorded yet.</td></tr>`;
      return;
    }
    appliedTableBody.innerHTML = list
      .map(
        (app) => `
        <tr>
          <td><strong>${escapeHtml(app.company)}</strong></td>
          <td>${escapeHtml(app.title)}</td>
          <td>${escapeHtml((app.applied_at || "").split("T")[0])}</td>
          <td><a href="${escapeHtml(app.url)}" target="_blank" rel="noopener" class="btn-link">View Listing ↗</a></td>
        </tr>
      `
      )
      .join("");
  } catch (err) {
    console.error("Apply history load error:", err);
  }
}

// ==============================================================================
// AUTOSYNC & MANUAL FETCHING
// ==============================================================================

async function checkAutoSyncStatus() {
  try {
    const status = await api("/api/autosync");
    if (status.enabled) {
      syncDot.classList.add("active");
      syncStatusLabel.textContent = `Auto-Sync: Active (${status.interval_minutes}m)`;
      toggleAutoSyncBtn.textContent = "Disable";
    } else {
      syncDot.classList.remove("active");
      syncStatusLabel.textContent = "Auto-Sync: Off";
      toggleAutoSyncBtn.textContent = "Enable";
    }
  } catch (err) {
    console.warn("Autosync status check failed:", err);
  }
}

toggleAutoSyncBtn.addEventListener("click", async () => {
  const isCurrentlyActive = syncDot.classList.contains("active");
  try {
    const res = await api("/api/autosync/toggle", {
      method: "POST",
      body: JSON.stringify({ enabled: !isCurrentlyActive, interval_minutes: 30 }),
    });
    checkAutoSyncStatus();
    showToast(res.enabled ? "Auto-Sync enabled! Polling ATS boards every 30m." : "Auto-Sync disabled.");
  } catch (err) {
    showToast(`Autosync error: ${err.message}`, true);
  }
});

async function triggerFetchPipeline() {
  try {
    setBusy(true, "Pulling latest jobs from Greenhouse, Lever & Ashby watchlist…");
    const res = await api("/api/autosync/trigger", { method: "POST" });
    setBusy(false);
    showToast("Fetch & Score complete! Synced opportunities.");
    loadStats();
    loadJobs();
  } catch (err) {
    setBusy(false);
    showToast(`Fetch error: ${err.message}`, true);
  }
}

runBtn.addEventListener("click", triggerFetchPipeline);
fetchSyncBtn.addEventListener("click", triggerFetchPipeline);

// Dropdown More Actions
moreBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  moreMenu.hidden = !moreMenu.hidden;
});

document.addEventListener("click", () => {
  moreMenu.hidden = true;
});

rescoreBtn.addEventListener("click", async () => {
  try {
    setBusy(true, "Re-scoring all jobs against current profile & open filters…");
    await api("/api/rescore", { method: "POST" });
    setBusy(false);
    showToast("Re-score completed for all 376 roles!");
    loadStats();
    loadJobs();
  } catch (err) {
    setBusy(false);
    showToast(`Re-score error: ${err.message}`, true);
  }
});

exportCsvBtn.addEventListener("click", () => {
  window.location.href = "/api/export?format=csv&status=queued";
});

exportAllBtn.addEventListener("click", () => {
  window.location.href = "/api/export?format=json";
});

exportHistoryCsvBtn.addEventListener("click", () => {
  window.location.href = "/api/export?format=csv&status=applied";
});

// Paste Role Modal (Optional / Secondary)
function openPasteModal() {
  if (pasteModal) {
    pasteModal.hidden = false;
    pasteModal.style.setProperty("display", "flex", "important");
    if (pasteUrl) pasteUrl.value = "";
    if (pasteText) {
      pasteText.value = "";
      pasteText.focus();
    }
  }
}

function closePasteModal() {
  if (pasteModal) {
    pasteModal.hidden = true;
    pasteModal.style.setProperty("display", "none", "important");
  }
}

if (pasteOpen) pasteOpen.addEventListener("click", openPasteModal);
if (openPasteBtn) openPasteBtn.addEventListener("click", openPasteModal);
if (pasteCloseBtn) pasteCloseBtn.addEventListener("click", closePasteModal);
if (pasteCancelBtn) pasteCancelBtn.addEventListener("click", closePasteModal);

pasteSubmitBtn.addEventListener("click", async () => {
  const text = pasteText.value.trim();
  const url = pasteUrl.value.trim();
  if (text.length < 20) {
    showToast("Please paste a job description (at least 20 characters)", true);
    return;
  }
  try {
    setBusy(true, "Ingesting and evaluating job listing…");
    const res = await api("/api/inbox", {
      method: "POST",
      body: JSON.stringify({ text, url: url || null }),
    });
    setBusy(false);
    closePasteModal();
    showToast("Role ingested and scored successfully!");
    loadStats();
    await loadJobs();
    if (res.job && res.job.id) {
      selectJob(res.job.id);
      switchView("packet");
    }
  } catch (err) {
    setBusy(false);
    showToast(`Ingest error: ${err.message}`, true);
  }
});

function resetResume() {
  hasUploadedResume = false;
  sessionStorage.removeItem("jobcopilot_has_resume");
  selectedJobId = null;
  jobs = [];
  loadPreferences();
  loadStats();
  switchView("preferences");
  showToast("Workspace reset. Please upload your resume to match jobs.");
}

if (clearProfileBtn) clearProfileBtn.addEventListener("click", resetResume);
if (resetResumeBtn) resetResumeBtn.addEventListener("click", resetResume);

// ==============================================================================
// INITIALIZATION
// ==============================================================================

async function init() {
  await loadPreferences();
  await loadCityFilterOptions();
  await loadStats();
  await checkAutoSyncStatus();
}

init();
