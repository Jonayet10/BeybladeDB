// Frontend logic for the BeybladeDB pages: session handling, API calls,
// table rendering, modal actions, and event binding.

const el = (id) => document.getElementById(id);

// Centralized API route definitions used by the frontend.
const ENDPOINTS = {
  login: "/api/login",
  beyblades: "/api/beyblades",
  leaderboard: "/api/leaderboard",
  userCollection: (username) => `/api/users/${encodeURIComponent(username)}/collection`,
  addToCollection: "/api/collection/add",
  deleteCollectionItem: (username, userBeybladeId) =>
    `/api/users/${encodeURIComponent(username)}/collection/${encodeURIComponent(userBeybladeId)}`,
  parts: "/api/parts",
  beybladeParts: (beybladeId) => `/api/beyblades/${encodeURIComponent(beybladeId)}/parts`,
  partById: (partId) => `/api/parts/${encodeURIComponent(partId)}`,
  heaviest: (type) => `/api/beyblades/heaviest?type=${encodeURIComponent(type)}`,
  tournaments: "/api/tournaments",
  locations: "/api/battles/locations",
  tournamentResults: (name) => `/api/tournaments/${encodeURIComponent(name)}/results`,
  tournamentsByLocation: (loc) => `/api/tournaments/by-location?location=${encodeURIComponent(loc)}`,
  updateCollectionCondition: (username, userBeybladeId) =>
  `/api/users/${encodeURIComponent(username)}/collection/${encodeURIComponent(userBeybladeId)}`,
};

const PAGE_LOGIN = "/login";
const PAGE_BEYBLADES = "/beyblades-page";
const PAGE_BATTLES = "/battles-page";

// Client-side session state and temporary modal state.
let CURRENT_USER = localStorage.getItem("beyblade_username");

let PENDING_ADD = {
  beybladeId: null,
  name: null,
};

const yesNo = (v) => (v === 1 || v === true || v === "1") ? "Yes" : "No";

const escapeHtml = (s) =>
  String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

function has(id) {
  return !!document.getElementById(id);
}

function safeSetText(id, text) {
  const node = document.getElementById(id);
  if (node) node.textContent = text;
}

function safeSetHtml(id, html) {
  const node = document.getElementById(id);
  if (node) node.innerHTML = html;
}

function bindClick(id, handler) {
  const node = document.getElementById(id);
  if (node) node.onclick = handler;
}

// Wrapper around fetch that parses JSON when possible and throws a
// readable error message for non-OK responses.
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });

  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }

  if (!res.ok) {
    const msg = data?.detail || data?.error || (typeof data === "string" ? data : JSON.stringify(data));
    throw new Error(msg);
  }

  return data;
}

function currentPath() {
  return window.location.pathname;
}

function onLoginPage() {
  return currentPath() === "/" || currentPath() === "/login";
}

function onBeybladesPage() {
  return currentPath() === PAGE_BEYBLADES;
}

function onBattlesPage() {
  return currentPath() === PAGE_BATTLES;
}

// Redirect unauthenticated users away from protected pages.
function requireLoginForProtectedPages() {
  if (!CURRENT_USER && (onBeybladesPage() || onBattlesPage())) {
    window.location.href = PAGE_LOGIN;
  }
}

function redirectLoggedInUserAwayFromLogin() {
  if (CURRENT_USER && onLoginPage()) {
    window.location.href = PAGE_BEYBLADES;
  }
}

// Sync in-memory session state, localStorage, and login-related UI elements.
function setSession(username) {
  CURRENT_USER = username || null;

  if (CURRENT_USER) {
    localStorage.setItem("beyblade_username", CURRENT_USER);
  } else {
    localStorage.removeItem("beyblade_username");
  }

  const pill = document.getElementById("sessionPill");
  if (pill) {
    pill.textContent = CURRENT_USER ? `Logged in: ${CURRENT_USER}` : "Not logged in";
  }

  const btnLogout = document.getElementById("btnLogout");
  if (btnLogout) {
    btnLogout.disabled = !CURRENT_USER;
  }

  const table = document.getElementById("beybladesTable");
  if (table && table.innerHTML.trim().length > 0) {
    const btns = table.querySelectorAll("button[data-beyblade-id]");
    btns.forEach((b) => {
      b.disabled = !CURRENT_USER;
    });
  }
}

// Table rendering helpers for API response data.
function renderTable(headers, rows) {
  const thead = `
    <thead>
      <tr>${headers.map((h) => `<th>${escapeHtml(h)}</th>`).join("")}</tr>
    </thead>
  `;

  const tbody = `
    <tbody>
      ${rows
        .map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`)
        .join("")}
    </tbody>
  `;

  return `<table class="table">${thead}${tbody}</table>`;
}

function renderBeyblades(items) {
  const headers = ["ID", "Name", "Type", "Series", "Custom", ""];
  const rows = items.map((b) => {
    const id = escapeHtml(b.beyblade_ID);
    const name = escapeHtml(b.name);
    const type = escapeHtml(b.type);
    const series = escapeHtml(b.series);
    const custom = escapeHtml(yesNo(b.is_custom));

    const btn = `
      <button class="btn-add" data-beyblade-id="${id}" data-beyblade-name="${name}" ${CURRENT_USER ? "" : "disabled"}>
        Add
      </button>
    `;

    return [id, name, type, series, custom, btn];
  });

  return renderTable(headers, rows);
}

function renderCollection(items) {
  const headers = ["User Beyblade ID", "Beyblade ID", "Name", "Custom", "Condition", "", ""];
  const rows = items.map((b) => {
    const userBeyId = escapeHtml(b.user_beyblade_ID ?? "");
    const beyId = escapeHtml(b.beyblade_ID ?? "");
    const name = escapeHtml(b.name ?? "");
    const custom = escapeHtml(yesNo(b.is_custom ?? 0));
    const cond = escapeHtml(b.bey_condition ?? "");

    const editBtn = `
      <button
        class="secondary btn-edit"
        data-edit-user-beyblade-id="${userBeyId}"
        data-current-condition="${cond}"
        ${CURRENT_USER ? "" : "disabled"}>
        Edit
      </button>
    `;

    const delBtn = `
      <button class="btn-del" data-user-beyblade-id="${userBeyId}" ${CURRENT_USER ? "" : "disabled"}>
        Delete
      </button>
    `;

    return [userBeyId, beyId, name, custom, cond, editBtn, delBtn];
  });

  return renderTable(headers, rows);
}

function renderLeaderboard(items) {
  const headers = ["Beyblade ID", "Name", "Type", "Wins"];
  const rows = items.map((x) => [
    escapeHtml(x.beyblade_ID ?? ""),
    escapeHtml(x.name ?? ""),
    escapeHtml(x.type ?? ""),
    escapeHtml(x.wins ?? ""),
  ]);

  return renderTable(headers, rows);
}

function renderParts(items) {
  const headers = ["Part ID", "Type", "Weight", "Description"];
  const rows = items.map((p) => [
    escapeHtml(p.part_ID ?? p.part_id ?? p.id ?? ""),
    escapeHtml(p.part_type ?? p.type ?? ""),
    escapeHtml(p.weight ?? p.part_weight ?? p.grams ?? p.weight_g ?? ""),
    escapeHtml(p.description ?? p.part_description ?? p.descr ?? p.desc ?? ""),
  ]);
  return renderTable(headers, rows);
}

function renderPartLookup(item) {
  const headers = ["Part ID", "Type", "Weight", "Description"];
  const rows = [[
    escapeHtml(item.part_ID ?? item.part_id ?? item.id ?? ""),
    escapeHtml(item.part_type ?? item.type ?? ""),
    escapeHtml(item.weight ?? item.part_weight ?? item.grams ?? item.weight_g ?? ""),
    escapeHtml(item.description ?? item.part_description ?? item.descr ?? item.desc ?? ""),
  ]];
  return renderTable(headers, rows);
}

function renderHeaviest(item) {
  const headers = ["Beyblade ID", "Name", "Type", "Series", "Total Weight"];
  const rows = [[
    escapeHtml(item.beyblade_ID ?? ""),
    escapeHtml(item.name ?? ""),
    escapeHtml(item.type ?? ""),
    escapeHtml(item.series ?? ""),
    escapeHtml(item.total_weight ?? ""),
  ]];
  return renderTable(headers, rows);
}

function renderTournaments(items) {
  const headers = ["Tournament Name"];
  const rows = items.map((t) => [escapeHtml(t.tournament_name ?? "")]);
  return renderTable(headers, rows);
}

function renderLocations(items) {
  const headers = ["Location"];
  const rows = items.map((x) => [escapeHtml(x.location ?? "")]);
  return renderTable(headers, rows);
}

function renderTournamentResults(items) {
  const headers = ["Battle ID", "Tournament", "Location", "Winner", "Loser"];
  const rows = items.map((b) => [
    escapeHtml(b.battle_ID ?? ""),
    escapeHtml(b.tournament_name ?? ""),
    escapeHtml(b.location ?? ""),
    escapeHtml(b.winner_beyblade_name ?? b.winner_ID ?? ""),
    escapeHtml(b.loser_beyblade_name ?? b.loser_ID ?? ""),
  ]);
  return renderTable(headers, rows);
}

function renderBeybladeParts(item) {
  const headers = ["Slot", "Part ID", "Weight", "Description"];
  const rows = [
    ["Face Bolt", item.face_bolt_id, item.face_bolt_weight, item.face_bolt_description],
    ["Energy Ring", item.energy_ring_id, item.energy_ring_weight, item.energy_ring_description],
    ["Fusion Wheel", item.fusion_wheel_id, item.fusion_wheel_weight, item.fusion_wheel_description],
    ["Spin Track", item.spin_track_id, item.spin_track_weight, item.spin_track_description],
    ["Performance Tip", item.performance_tip_id, item.performance_tip_weight, item.performance_tip_description],
  ].map((r) => r.map((c) => escapeHtml(c ?? "")));

  const title = `<div class="muted" style="margin-bottom:10px;">${escapeHtml(item.beyblade_ID)} • ${escapeHtml(item.beyblade_name ?? "")}</div>`;
  return title + renderTable(headers, rows);
}

// Build the beyblade filter query string from the current form inputs.
function buildBeybladeQuery() {
  const params = new URLSearchParams();

  const type = (document.getElementById("filterType")?.value || "").trim();
  const series = (document.getElementById("filterSeries")?.value || "").trim();

  if (type) params.set("type", type);
  if (series) params.set("series", series);

  const qs = params.toString();
  return qs ? `?${params.toString()}` : "";
}

async function loadBeyblades() {
  safeSetText("beybladesMsg", "");
  const data = await api(ENDPOINTS.beyblades + buildBeybladeQuery());
  const items = data.items || [];
  safeSetHtml("beybladesTable", renderBeyblades(items));
}

async function loadCollection() {
  safeSetText("collectionMsg", "");
  if (!CURRENT_USER) throw new Error("Login first.");
  const data = await api(ENDPOINTS.userCollection(CURRENT_USER));
  const items = data.items || data.collection || [];
  safeSetHtml("collectionTable", renderCollection(items));
}

async function loadLeaderboard() {
  safeSetText("leaderboardMsg", "");
  const data = await api(ENDPOINTS.leaderboard);
  const items = data.items || [];
  safeSetHtml("leaderboardTable", renderLeaderboard(items));
}

async function loadLocationSuggestions() {
  const data = await api(ENDPOINTS.locations);
  const items = data.items || [];

  const datalist = document.getElementById("locationSuggestions");
  if (!datalist) return;

  datalist.innerHTML = items
    .map((x) => `<option value="${escapeHtml(x.location ?? "")}"></option>`)
    .join("");
}

async function loadTournamentsByLocation() {
  const loc = el("locationForTournaments").value.trim();
  if (!loc) throw new Error("Enter a location");

  const data = await api(ENDPOINTS.tournamentsByLocation(loc));
  el("tournamentsTable").innerHTML = renderTournaments(data.items || []);
}

async function login(username, password) {
  safeSetText("loginMsg", "");
  const payload = { username, password };
  const data = await api(ENDPOINTS.login, { method: "POST", body: JSON.stringify(payload) });
  const u = data.username || username;
  setSession(u);
  window.location.href = PAGE_BEYBLADES;
}

function logout() {
  setSession(null);
  window.location.replace(PAGE_LOGIN);
}

// Store the selected beyblade and open the add-to-collection modal.
function openAddModal(beybladeId, beybladeName) {
  if (!CURRENT_USER) {
    safeSetText("beybladesMsg", "Login first.");
    return;
  }

  PENDING_ADD = { beybladeId, name: beybladeName };
  safeSetText("addModalMsg", "");
  safeSetText("addModalSubtitle", `${beybladeId}${beybladeName ? ` • ${beybladeName}` : ""}`);

  const backdrop = document.getElementById("addModalBackdrop");
  if (backdrop) {
    backdrop.classList.remove("hidden");
    backdrop.setAttribute("aria-hidden", "false");
  }

  document.getElementById("modalCondition")?.focus();
}

function closeAddModal() {
  const backdrop = document.getElementById("addModalBackdrop");
  if (backdrop) {
    backdrop.classList.add("hidden");
    backdrop.setAttribute("aria-hidden", "true");
  }

  const conditionInput = document.getElementById("modalCondition");
  if (conditionInput) {
    conditionInput.value = "Like New";
  }

  safeSetText("addModalMsg", "");
  PENDING_ADD = { beybladeId: null, name: null };
}

// Submit the pending add-to-collection request for the selected beyblade.
async function confirmAdd() {
  if (!CURRENT_USER) throw new Error("Login first.");
  if (!PENDING_ADD.beybladeId) throw new Error("No beyblade selected.");

  const condition = (document.getElementById("modalCondition")?.value || "Like New").trim();
  const payload = {
    username: CURRENT_USER,
    beyblade_id: PENDING_ADD.beybladeId,
    bey_condition: condition,
  };

  await api(ENDPOINTS.addToCollection, { method: "POST", body: JSON.stringify(payload) });

  safeSetText("beybladesMsg", `Added ${PENDING_ADD.beybladeId} to ${CURRENT_USER}'s collection.`);
  closeAddModal();
  if (has("collectionTable")) {
    await loadCollection().catch(() => {});
  }
}

async function deleteFromCollection(userBeybladeId) {
  if (!CURRENT_USER) throw new Error("Login first.");
  await api(ENDPOINTS.deleteCollectionItem(CURRENT_USER, userBeybladeId), { method: "DELETE" });
}

// Update the saved condition for a collection item.
async function updateCollectionCondition(userBeybladeId, newCondition) {
  if (!CURRENT_USER) throw new Error("Login first.");

  await api(ENDPOINTS.updateCollectionCondition(CURRENT_USER, userBeybladeId), {
    method: "PATCH",
    body: JSON.stringify({
      username: CURRENT_USER,
      user_beyblade_id: Number(userBeybladeId),
      bey_condition: newCondition,
    }),
  });
}

async function loadParts() {
  safeSetText("partsMsg", "");
  const params = new URLSearchParams();
  const pt = (document.getElementById("partsFilterType")?.value || "").trim();
  const q = (document.getElementById("partsSearch")?.value || "").trim();
  if (pt) params.set("part_type", pt);
  if (q) params.set("q", q);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const data = await api(ENDPOINTS.parts + qs);
  safeSetHtml("partsTable", renderParts(data.items || []));
}

async function loadBeybladeParts() {
  safeSetText("beyPartsMsg", "");
  const id = (document.getElementById("beybladeIdForParts")?.value || "").trim();
  if (!id) throw new Error("Enter a Beyblade ID.");
  const data = await api(ENDPOINTS.beybladeParts(id));
  safeSetHtml("beyPartsTable", renderBeybladeParts(data.item));
}

async function loadPartById() {
  safeSetText("partLookupMsg", "");
  safeSetHtml("partLookupTable", "");
  const id = (document.getElementById("partIdLookup")?.value || "").trim();
  if (!id) throw new Error("Enter a Part ID.");
  const data = await api(ENDPOINTS.partById(id));
  safeSetHtml("partLookupTable", renderPartLookup(data.item));
}

async function loadHeaviest() {
  safeSetText("heaviestMsg", "");
  const t = (document.getElementById("heaviestType")?.value || "").trim();
  if (!t) throw new Error("Enter a Beyblade type.");
  const data = await api(ENDPOINTS.heaviest(t));
  safeSetHtml("heaviestTable", renderHeaviest(data.item));
}

async function loadTournaments() {
  safeSetText("tournamentsMsg", "");
  const data = await api(ENDPOINTS.tournaments);
  safeSetHtml("tournamentsTable", renderTournaments(data.items || []));
}

async function loadLocations() {
  safeSetText("locationsMsg", "");
  const data = await api(ENDPOINTS.locations);
  safeSetHtml("locationsTable", renderLocations(data.items || []));
}

async function loadTournamentResults() {
  safeSetText("resultsMsg", "");
  const name = (document.getElementById("tournamentNameForResults")?.value || "").trim();
  if (!name) throw new Error("Enter a tournament name.");
  const data = await api(ENDPOINTS.tournamentResults(name));
  safeSetHtml("resultsTable", renderTournamentResults(data.items || []));
}

function toggleCollection() {
  const wrap = document.getElementById("collectionTableWrap");
  const btn = document.getElementById("btnToggleCollection");
  const msg = document.getElementById("collectionMsg");

  if (!wrap || !btn) return;

  const isHidden = wrap.classList.toggle("hidden-section");

  if (msg) {
    msg.classList.toggle("hidden-section", isHidden);
  }

  btn.textContent = isHidden ? "Show" : "Hide";
}

// Use event delegation for dynamically rendered table buttons.
function bindTableDelegates() {
  const beybladesTable = document.getElementById("beybladesTable");
  if (beybladesTable) {
    beybladesTable.addEventListener("click", (e) => {
      // Handle inline collection edits and deletes through delegated table clicks.
      const btn = e.target.closest("button[data-beyblade-id]");
      if (!btn) return;
      openAddModal(btn.dataset.beybladeId, btn.dataset.beybladeName);
    });
  }

  const collectionTable = document.getElementById("collectionTable");
  if (collectionTable) {
    collectionTable.addEventListener("click", async (e) => {
      const editBtn = e.target.closest("button[data-edit-user-beyblade-id]");
      if (editBtn) {
        try {
          const id = editBtn.dataset.editUserBeybladeId;
          const currentCondition = editBtn.dataset.currentCondition || "";
          const nextCondition = window.prompt("Enter new condition:", currentCondition);

          if (nextCondition === null) return;

          const cleaned = nextCondition.trim();
          if (!cleaned) {
            throw new Error("Condition cannot be empty.");
          }

          await updateCollectionCondition(id, cleaned);
          safeSetText("collectionMsg", `Updated condition for item ${id}.`);
          await loadCollection();
        } catch (err) {
          safeSetText("collectionMsg", err.message);
        }
        return;
      }

      const delBtn = e.target.closest("button[data-user-beyblade-id]");
      if (delBtn) {
        try {
          const id = delBtn.dataset.userBeybladeId;
          const ok = window.confirm(`Delete this beyblade from your collection?\n\nUser Beyblade ID: ${id}`);
          if (!ok) return;

          await deleteFromCollection(id);
          safeSetText("collectionMsg", `Deleted item ${id} from your collection.`);
          await loadCollection();
        } catch (err) {
          safeSetText("collectionMsg", err.message);
        }
      }
    });
  }
}

function bindEvents() {
  bindClick("btnLogin", async () => {
    try {
      const username = (document.getElementById("loginUsername")?.value || "").trim().toLowerCase();
      const password = (document.getElementById("loginPassword")?.value || "").trim();
      if (!username || !password) throw new Error("Enter username and password.");
      await login(username, password);
    } catch (e) {
      safeSetText("loginMsg", e.message);
    }
  });

  document.addEventListener("click", (e) => {
    const logoutLink = e.target.closest("#btnLogout");
    if (!logoutLink) return;

    e.preventDefault();
    logout();
  });

  bindClick("btnLoadBeyblades", async () => {
    try {
      await loadBeyblades();
    } catch (e) {
      safeSetText("beybladesMsg", e.message);
    }
  });

  bindClick("btnCloseAddModal", closeAddModal);
  bindClick("btnCancelAdd", closeAddModal);

  bindClick("btnConfirmAdd", async () => {
    try {
      safeSetText("addModalMsg", "");
      await confirmAdd();
    } catch (e) {
      safeSetText("addModalMsg", e.message);
    }
  });

  bindClick("btnToggleCollection", () => {
    toggleCollection();
  });

  const addModalBackdrop = document.getElementById("addModalBackdrop");
  if (addModalBackdrop) {
    addModalBackdrop.addEventListener("click", (e) => {
      if (e.target === addModalBackdrop) closeAddModal();
    });
  }

  document.addEventListener("keydown", (e) => {
    const backdrop = document.getElementById("addModalBackdrop");
    if (e.key === "Escape" && backdrop && !backdrop.classList.contains("hidden")) {
      closeAddModal();
    }
  });

  bindClick("btnLoadParts", async () => {
    try {
      await loadParts();
    } catch (e) {
      safeSetText("partsMsg", e.message);
    }
  });

  bindClick("btnLoadBeybladeParts", async () => {
    try {
      await loadBeybladeParts();
    } catch (e) {
      safeSetText("beyPartsMsg", e.message);
    }
  });

  bindClick("btnLoadPartById", async () => {
    try {
      await loadPartById();
    } catch (e) {
      safeSetText("partLookupMsg", e.message);
    }
  });

  bindClick("btnHeaviestByType", async () => {
    try {
      await loadHeaviest();
    } catch (e) {
      safeSetText("heaviestMsg", e.message);
    }
  });

  bindClick("btnLoadTournamentsByLocation", async () => {
    try {
      await loadTournamentsByLocation();
    } catch (e) {
      safeSetText("tournamentsMsg", e.message);
    }
  });

  bindClick("btnTournamentResults", async () => {
    try {
      await loadTournamentResults();
    } catch (e) {
      safeSetText("resultsMsg", e.message);
    }
  });

  bindTableDelegates();
}

// Initialize page state, bind UI events, and load page-specific data.
async function bootstrapPage() {
    setSession(CURRENT_USER);
    requireLoginForProtectedPages();
    redirectLoggedInUserAwayFromLogin();
    bindEvents();

    if (onBeybladesPage()) {
        await loadBeyblades().catch(() => {});
        await loadCollection().catch(() => {});
    }

    if (onBattlesPage()) {
    await loadLeaderboard().catch(() => {});
    await loadLocationSuggestions().catch(() => {});
    }
}

bootstrapPage();