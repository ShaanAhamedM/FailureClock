/**
 * Failure Clock — Minimalist, Clean Dashboard Controller
 */

const API_BASE = window.location.origin;

const STATE = {
  scenarioId: "severe_cyclone_live",
  currentTimeH: -12.0,
  isPlaying: false,
  playInterval: null,
  graph: null,
  scenarioAssets: null,
  actions: [],
  map: null,
  assetMarkers: {},
  roadPolylines: {},
  stormMarker: null,
  selectedAssetId: null,
};

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", async () => {
  initTabs();
  initMap();
  initTimeControls();
  initScenarioSelect();
  await loadScenario(STATE.scenarioId);
});

// --- TABS ---
function initTabs() {
  const tabs = document.querySelectorAll(".panel-tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".panel-content").forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.dataset.view;
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");
    });
  });
}

function switchToTab(tabViewId) {
  document.querySelectorAll(".panel-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.view === tabViewId);
  });
  document.querySelectorAll(".panel-content").forEach((p) => {
    p.classList.toggle("active", p.id === tabViewId);
  });
}

// --- SCENARIO SELECT ---
function initScenarioSelect() {
  const sel = document.getElementById("scenarioSelect");
  sel.addEventListener("change", (e) => {
    loadScenario(e.target.value);
  });
}

// --- MAP INITIALIZATION ---
function initMap() {
  // Center on Puri District
  STATE.map = L.map("map", {
    center: [19.825, 85.845],
    zoom: 12,
    zoomControl: true,
  });

  // Free, standard OpenStreetMap tiles with dark grayscale CSS filter
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; OpenStreetMap | Failure Clock',
    subdomains: ['a', 'b', 'c'],
    maxZoom: 18,
  }).addTo(STATE.map);
}

// --- SCENARIO DATA LOADER ---
async function loadScenario(scenarioId) {
  STATE.scenarioId = scenarioId;
  try {
    const [assetsRes, graphRes, actionsRes, councilRes] = await Promise.all([
      fetch(`${API_BASE}/api/scenario/${scenarioId}/assets`),
      fetch(`${API_BASE}/api/graph`),
      fetch(`${API_BASE}/api/scenario/${scenarioId}/actions`),
      fetch(`${API_BASE}/api/scenario/${scenarioId}/crisis-council`),
    ]);

    const assetsData = await assetsRes.json();
    STATE.scenarioAssets = assetsData.assets;
    STATE.graph = await graphRes.json();
    STATE.actions = await actionsRes.json();
    const councilData = await councilRes.json();

    renderMap();
    renderActions();
    renderFailureSequence();
    renderCrisisPlan(councilData);
    updateTimeDisplay();
  } catch (err) {
    console.error("Error loading scenario:", err);
  }
}

// --- RENDER MAP ELEMENTS ---
function renderMap() {
  // Clear existing
  Object.values(STATE.assetMarkers).forEach((m) => STATE.map.removeLayer(m));
  Object.values(STATE.roadPolylines).forEach((r) => STATE.map.removeLayer(r));
  STATE.assetMarkers = {};
  STATE.roadPolylines = {};
  if (STATE.stormMarker) STATE.map.removeLayer(STATE.stormMarker);

  const nodes = STATE.graph.nodes;

  // Road Corridors
  nodes.filter((n) => n.type === "ROAD_SEGMENT").forEach((road) => {
    const coords = getRoadCoordinates(road.id, road.lat, road.lon);
    const poly = L.polyline(coords, {
      color: "#000000",
      weight: 3.5,
      opacity: 0.9,
    }).addTo(STATE.map);

    poly.bindTooltip(`<b>${road.name}</b>`, { sticky: true });
    poly.on("click", () => openAssetDetail(road.id));
    STATE.roadPolylines[road.id] = poly;
  });

  // Infrastructure Nodes
  nodes.filter((n) => n.type !== "ROAD_SEGMENT").forEach((node) => {
    const icon = createNodeIcon(node.type, "OPERATING");
    const marker = L.marker([node.lat, node.lon], { icon }).addTo(STATE.map);

    marker.bindTooltip(`<b>${node.name}</b><br><span style="color:#666">${node.type}</span>`, {
      sticky: true,
    });
    marker.on("click", () => openAssetDetail(node.id));
    STATE.assetMarkers[node.id] = marker;
  });

  // Storm Eye Marker
  const stormIcon = L.divIcon({
    className: "custom-storm-icon",
    html: `<div class="storm-eye-marker">◎</div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
  STATE.stormMarker = L.marker([19.78, 85.80], { icon: stormIcon }).addTo(STATE.map);
  STATE.stormMarker.bindTooltip("<b>Cyclone Center</b><br>Landfall Point", { sticky: true });

  updateStateAtTime(STATE.currentTimeH);
}

function createNodeIcon(type, state) {
  let label = "H";
  if (type === "SUBSTATION") label = "SS";
  if (type === "FEEDER") label = "FD";
  if (type === "TOWER") label = "TX";
  if (type === "WATER_PUMP") label = "WP";
  if (type === "DEPOT") label = "DP";

  let stateClass = "operating";
  if (state === "ON_BACKUP") stateClass = "backup";
  else if (state === "FAILED") stateClass = "failed";

  return L.divIcon({
    className: "custom-node-icon",
    html: `<div class="node-badge ${stateClass}">${label}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function getRoadCoordinates(roadId, centerLat, centerLon) {
  if (roadId === "RD-NH316-NORTH") {
    return [[19.825, 85.828], [19.855, 85.830], [19.920, 85.835]];
  }
  if (roadId === "RD-PURI-TOWN-LINK") {
    return [[19.825, 85.828], [19.818, 85.828], [19.814, 85.827]];
  }
  if (roadId === "RD-MARINE-DRIVE") {
    return [[19.814, 85.835], [19.851, 85.918], [19.889, 86.098]];
  }
  if (roadId === "RD-BRAHMAGIRI-LINK") {
    return [[19.814, 85.827], [19.805, 85.740], [19.799, 85.682]];
  }
  if (roadId === "RD-GOP-INLAND") {
    return [[19.825, 85.828], [19.920, 85.920], [19.995, 86.012]];
  }
  return [[centerLat - 0.02, centerLon - 0.02], [centerLat, centerLon], [centerLat + 0.02, centerLon + 0.02]];
}

// --- UPDATE STATE AT TIME T ---
function updateStateAtTime(timeH) {
  if (!STATE.scenarioAssets) return;

  let op = 0;
  let bk = 0;
  let fa = 0;

  Object.entries(STATE.scenarioAssets).forEach(([aid, dist]) => {
    let state = "OPERATING";
    const timeline = dist.state_timeline_p50 || [];
    const match = timeline.find((pt) => pt[0] === timeH);
    if (match) state = match[1];

    if (dist.type === "ROAD_SEGMENT") {
      const poly = STATE.roadPolylines[aid];
      if (poly) {
        if (state === "FAILED") {
          poly.setStyle({ color: "#999999", dashArray: "4, 6", weight: 2.5 });
        } else {
          poly.setStyle({ color: "#000000", dashArray: null, weight: 3.5 });
        }
      }
    } else {
      const marker = STATE.assetMarkers[aid];
      if (marker) {
        marker.setIcon(createNodeIcon(dist.type, state));
      }
    }

    if (state === "OPERATING") op++;
    else if (state === "ON_BACKUP") bk++;
    else if (state === "FAILED") fa++;
  });

  document.getElementById("countOperating").textContent = op;
  document.getElementById("countBackup").textContent = bk;
  document.getElementById("countFailed").textContent = fa;

  // Move storm
  if (STATE.stormMarker) {
    const lat = 19.78 + timeH * 0.055;
    const lon = 85.80 + timeH * 0.050;
    STATE.stormMarker.setLatLng([lat, lon]);
  }
}

// --- TIME CONTROLS ---
function initTimeControls() {
  const slider = document.getElementById("timeSlider");
  const playBtn = document.getElementById("btnPlayPause");
  const stepBackBtn = document.getElementById("btnStepBack");
  const stepFwdBtn = document.getElementById("btnStepFwd");

  slider.addEventListener("input", (e) => {
    STATE.currentTimeH = parseFloat(e.target.value);
    updateTimeDisplay();
    updateStateAtTime(STATE.currentTimeH);
    renderActions(); // update countdowns
  });

  playBtn.addEventListener("click", () => {
    if (STATE.isPlaying) pausePlay();
    else startPlay();
  });

  stepBackBtn.addEventListener("click", () => {
    STATE.currentTimeH = Math.max(-24, STATE.currentTimeH - 1);
    slider.value = STATE.currentTimeH;
    updateTimeDisplay();
    updateStateAtTime(STATE.currentTimeH);
    renderActions();
  });

  stepFwdBtn.addEventListener("click", () => {
    STATE.currentTimeH = Math.min(36, STATE.currentTimeH + 1);
    slider.value = STATE.currentTimeH;
    updateTimeDisplay();
    updateStateAtTime(STATE.currentTimeH);
    renderActions();
  });
}

function startPlay() {
  STATE.isPlaying = true;
  document.getElementById("btnPlayPause").textContent = "❚❚ Pause";
  STATE.playInterval = setInterval(() => {
    if (STATE.currentTimeH >= 36) {
      pausePlay();
      return;
    }
    STATE.currentTimeH += 1;
    document.getElementById("timeSlider").value = STATE.currentTimeH;
    updateTimeDisplay();
    updateStateAtTime(STATE.currentTimeH);
    renderActions();
  }, 900);
}

function pausePlay() {
  STATE.isPlaying = false;
  document.getElementById("btnPlayPause").textContent = "▶ Play";
  clearInterval(STATE.playInterval);
}

function updateTimeDisplay() {
  const t = STATE.currentTimeH;
  const sign = t >= 0 ? "+" : "";
  document.getElementById("scrubClockDisplay").textContent = `T${sign}${t.toFixed(1)}h`;

  let phase = "Pre-Landfall Warning";
  if (t >= -12 && t < -2) phase = "Pre-Landfall Preparation";
  else if (t >= -2 && t <= 4) phase = "Landfall Eye Window";
  else if (t > 4 && t <= 20) phase = "Post-Landfall Cascade";
  else if (t > 20) phase = "Recovery Phase";

  document.getElementById("phaseIndicator").textContent = phase;
}

// --- RENDER ACTIONS ---
function renderActions() {
  const list = document.getElementById("actionsList");
  list.innerHTML = "";

  STATE.actions.forEach((act) => {
    const hoursLeft = Math.max(act.deadline_h - STATE.currentTimeH, 0);
    const isUrgent = hoursLeft <= 3.0;

    const card = document.createElement("div");
    card.className = "simple-card";
    card.innerHTML = `
      <div class="card-top">
        <div class="card-title">${act.title}</div>
        <div class="deadline-badge ${isUrgent ? 'urgent' : ''}">
          ${hoursLeft <= 0 ? "EXPIRED" : `${hoursLeft.toFixed(1)}h left`}
        </div>
      </div>
      <div class="card-desc">${act.description}</div>
      <div class="card-meta">
        <span>Route: <b>${act.route_asset_ids[0] || "Direct"}</b></span>
        <span>${act.resources_needed.split(",")[0]}</span>
      </div>
    `;
    list.appendChild(card);
  });
}

// --- RENDER FAILURE SEQUENCE ---
function renderFailureSequence() {
  const container = document.getElementById("failureSequenceList");
  container.innerHTML = "";

  const items = Object.values(STATE.scenarioAssets || {})
    .filter((a) => a.p50_fail_time_h !== null)
    .sort((a, b) => a.p50_fail_time_h - b.p50_fail_time_h);

  items.forEach((item) => {
    const sign = item.p50_fail_time_h >= 0 ? "+" : "";
    const div = document.createElement("div");
    div.className = "sequence-item";
    div.style.cursor = "pointer";
    div.onclick = () => openAssetDetail(item.asset_id);

    div.innerHTML = `
      <div class="seq-time">T${sign}${item.p50_fail_time_h.toFixed(1)}h</div>
      <div class="seq-info">
        <div class="seq-name">${item.name}</div>
        <div class="seq-cause">Primary trigger: ${item.dominant_cause.replace(/_/g, " ")}</div>
      </div>
    `;
    container.appendChild(div);
  });
}

// --- ASSET DETAIL IN SIDE PANEL ---
async function openAssetDetail(assetId) {
  STATE.selectedAssetId = assetId;
  switchToTab("view-detail");

  try {
    const res = await fetch(`${API_BASE}/api/scenario/${STATE.scenarioId}/assets/${assetId}/explain`);
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("detailEmptyMessage").style.display = "none";
    const body = document.getElementById("detailContent");
    body.classList.remove("hidden");

    document.getElementById("detailType").textContent = data.type;
    document.getElementById("detailName").textContent = data.name;
    document.getElementById("detailMeta").textContent = `Asset ID: ${data.asset_id} | Criticality: ${data.criticality}`;

    document.getElementById("detailP10").textContent = data.p10_fail_time_h !== null ? `T${data.p10_fail_time_h >= 0 ? "+" : ""}${data.p10_fail_time_h}h` : "Survived";
    document.getElementById("detailP50").textContent = data.p50_fail_time_h !== null ? `T${data.p50_fail_time_h >= 0 ? "+" : ""}${data.p50_fail_time_h}h` : "Survived";
    document.getElementById("detailP90").textContent = data.p90_fail_time_h !== null ? `T${data.p90_fail_time_h >= 0 ? "+" : ""}${data.p90_fail_time_h}h` : "Survived";

    document.getElementById("detailCause").textContent = `${data.dominant_cause.replace(/_/g, " ")} (${data.cause_breakdown[data.dominant_cause] || 80}%)`;

    const chain = document.getElementById("detailChain");
    chain.innerHTML = "";
    if (data.causal_chain.length === 0) {
      chain.innerHTML = `<div class="chain-step">Asset operates normally without disruption.</div>`;
    } else {
      data.causal_chain.forEach((s) => {
        const stepDiv = document.createElement("div");
        stepDiv.className = "chain-step";
        stepDiv.textContent = s;
        chain.appendChild(stepDiv);
      });
    }

    const routeInfo = data.resupply_routes.length > 0 ? `${data.resupply_routes[0].depot_id} via ${data.resupply_routes[0].road_path.join(" → ")}` : "None";
    document.getElementById("detailDeps").innerHTML = `
      <b>Grid Power:</b> ${data.upstream_power_nodes.join(", ") || "Self-powered / Off-grid"}<br>
      <b>Resupply Route:</b> ${routeInfo}
    `;
  } catch (err) {
    console.error("Error opening asset detail:", err);
  }
}

// --- RENDER CRISIS PLAN ---
function renderCrisisPlan(councilData) {
  const ordersContainer = document.getElementById("councilOrdersList");
  ordersContainer.innerHTML = "";

  (councilData.consensus_plan || []).forEach((order) => {
    const div = document.createElement("div");
    div.className = "order-item";
    div.innerHTML = `
      <div class="order-item-title">Step ${order.step}: ${order.action}</div>
      <div class="order-item-meta">
        <span>Owner: <b>${order.owner}</b></span>
        <span>Deadline: <b>${order.deadline}</b></span>
      </div>
    `;
    ordersContainer.appendChild(div);
  });

  const notesContainer = document.getElementById("councilSummary");
  notesContainer.innerHTML = "";

  (councilData.transcript || []).slice(0, 4).forEach((msg) => {
    const note = document.createElement("div");
    note.className = "note-msg";
    note.innerHTML = `<b>${msg.speaker}:</b> ${msg.message}`;
    notesContainer.appendChild(note);
  });
}
