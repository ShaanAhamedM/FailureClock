/**
 * Failure Clock Web Dashboard
 * Cyclone Impact & Infrastructure Vulnerability Forecaster
 */

const API_BASE = window.location.origin;

const STATE = {
  scenarioId: "severe_cyclone_live",
  currentTimeH: -12.0,
  isPlaying: false,
  playSpeed: 1,
  playInterval: null,
  graph: null,
  scenarioAssets: null,
  clliTimeline: [],
  metrics: {},
  actions: [],
  map: null,
  assetMarkers: {},
  roadPolylines: {},
  stormMarker: null,
  stormConeLayer: null,
  clliChart: null,
  whatifChart: null,
};

// --- INITIALIZATION ---
document.addEventListener("DOMContentLoaded", async () => {
  initTabs();
  initMap();
  initPlaybackControls();
  initEventListeners();
  await loadScenario(STATE.scenarioId);
});

// --- TABS ---
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.dataset.tab;
      document.getElementById(targetId).classList.add("active");

      // Invalidate map size if switching back to map
      if (targetId === "tab-map" && STATE.map) {
        setTimeout(() => STATE.map.invalidateSize(), 100);
      }
      // Load tab-specific dynamic content
      if (targetId === "tab-doomsday") loadDoomsdayBoard();
      if (targetId === "tab-timemachine") loadTimeMachineList();
      if (targetId === "tab-keystones") loadKeystonesAndShapley();
      if (targetId === "tab-council") loadCrisisCouncil();
      if (targetId === "tab-redteam") loadRedTeamDefault();
    });
  });
}

// --- EVENT LISTENERS ---
function initEventListeners() {
  document.getElementById("scenarioSelect").addEventListener("change", (e) => {
    loadScenario(e.target.value);
  });

  document.getElementById("btnRunSim").addEventListener("click", () => {
    loadScenario(STATE.scenarioId, true);
  });

  document.getElementById("modalCloseBtn").addEventListener("click", closeModal);
  document.getElementById("modalBackdrop").addEventListener("click", closeModal);

  document.getElementById("btnRunWhatIf").addEventListener("click", executeWhatIf);
  document.getElementById("btnReconveneCouncil").addEventListener("click", loadCrisisCouncil);
  document.getElementById("btnRunRedTeam").addEventListener("click", runRedTeam);
}

// --- MAP & LAYERS ---
function initMap() {
  // Center on Puri District, Odisha
  STATE.map = L.map("map", {
    center: [19.825, 85.845],
    zoom: 12,
    zoomControl: true,
  });

  // OpenStreetMap with grayscale CSS filter (no API keys, zero 403 errors)
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | Failure Clock',
    subdomains: ['a', 'b', 'c'],
    maxZoom: 18,
  }).addTo(STATE.map);
}

// --- SCENARIO LOADER ---
async function loadScenario(scenarioId, forceRefresh = false) {
  STATE.scenarioId = scenarioId;
  try {
    const url = `${API_BASE}/api/scenario/${scenarioId}/assets${forceRefresh ? "?force_refresh=true" : ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch scenario assets");
    const data = await res.json();

    STATE.scenarioAssets = data.assets;
    STATE.clliTimeline = data.clli_timeline;
    STATE.metrics = data.metrics;

    // Load graph & actions
    const [graphRes, actionsRes] = await Promise.all([
      fetch(`${API_BASE}/api/graph`),
      fetch(`${API_BASE}/api/scenario/${scenarioId}/actions`),
    ]);
    STATE.graph = await graphRes.json();
    STATE.actions = await actionsRes.json();

    updateHeaderMetrics();
    renderMapElements();
    renderCLLIChart();
    renderQuickActions();
    updateTimeDisplay();
  } catch (err) {
    console.error("Error loading scenario:", err);
  }
}

// --- HEADER METRICS ---
function updateHeaderMetrics() {
  document.getElementById("metricPeakCLLI").textContent = (STATE.metrics.peak_clli_p50 || 0).toFixed(1);
  document.getElementById("metricPatientHours").textContent = Number(STATE.metrics.total_patient_hours_at_risk || 0).toLocaleString();
  document.getElementById("metricOutagePct").textContent = (STATE.metrics.median_landfall_outage_pct || 0) + "%";
}

// --- RENDER MAP ELEMENTS ---
function renderMapElements() {
  // Clear existing
  Object.values(STATE.assetMarkers).forEach((m) => STATE.map.removeLayer(m));
  Object.values(STATE.roadPolylines).forEach((r) => STATE.map.removeLayer(r));
  STATE.assetMarkers = {};
  STATE.roadPolylines = {};

  if (STATE.stormMarker) STATE.map.removeLayer(STATE.stormMarker);

  const nodes = STATE.graph.nodes;

  // Render Road Segments (Minimalist white solid / dashed lines)
  const roadNodes = nodes.filter((n) => n.type === "ROAD_SEGMENT");
  roadNodes.forEach((road) => {
    const coords = getRoadCoordinates(road.id, road.lat, road.lon);
    const poly = L.polyline(coords, {
      color: "#ffffff",
      weight: 3.5,
      opacity: 0.9,
    }).addTo(STATE.map);

    poly.bindTooltip(`<b>${road.name}</b><br>Lifeline Corridor (Passable)`, { sticky: true });
    poly.on("click", () => openAssetModal(road.id));
    STATE.roadPolylines[road.id] = poly;
  });

  // Render Infrastructure Nodes (Minimalist monochrome badges)
  nodes.filter((n) => n.type !== "ROAD_SEGMENT").forEach((node) => {
    const icon = getAssetCustomIcon(node.type, "OPERATING");
    const marker = L.marker([node.lat, node.lon], { icon }).addTo(STATE.map);

    marker.bindTooltip(`<b>${node.name}</b><br><span style="color:#a3a3a3">${node.type}</span>`, {
      sticky: true,
    });
    marker.on("click", () => openAssetModal(node.id));
    STATE.assetMarkers[node.id] = marker;
  });

  // Render Storm Eye Marker (Minimalist rotating target glyph)
  const stormIcon = L.divIcon({
    className: "custom-storm-icon",
    html: `<div class="storm-eye-marker">◎</div>`,
    iconSize: [40, 40],
    iconAnchor: [20, 20],
  });
  STATE.stormMarker = L.marker([19.78, 85.80], { icon: stormIcon }).addTo(STATE.map);
  STATE.stormMarker.bindTooltip("<b>Cyclone Core / Eye</b><br>Max Sustained Winds: 115 knots", { sticky: true });

  updateMapStateAtTime(STATE.currentTimeH);
}

function getRoadCoordinates(roadId, centerLat, centerLon) {
  // Return realistic coordinate traces for Puri roads
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

function getAssetCustomIcon(type, state) {
  let label = "H";
  if (type === "SUBSTATION") label = "SS";
  if (type === "FEEDER") label = "FD";
  if (type === "TOWER") label = "TX";
  if (type === "WATER_PUMP") label = "WP";
  if (type === "DEPOT") label = "DP";

  let stateClass = "operating";
  if (state === "ON_BACKUP") stateClass = "backup";
  else if (state === "FAILED") stateClass = "failed";

  const html = `
    <div class="node-badge ${stateClass}" title="${type}: ${state}">
      ${label}
    </div>
  `;

  return L.divIcon({
    className: "custom-asset-icon",
    html,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
}

// --- UPDATE STATE AT TIME T ---
function updateMapStateAtTime(timeH) {
  if (!STATE.scenarioAssets) return;

  let operatingCount = 0;
  let backupCount = 0;
  let failedCount = 0;

  Object.entries(STATE.scenarioAssets).forEach(([assetId, dist]) => {
    // Find state at timeH in state_timeline_p50
    let currentState = "OPERATING";
    const timeline = dist.state_timeline_p50 || [];
    const match = timeline.find((pt) => pt[0] === timeH);
    if (match) currentState = match[1];

    if (dist.type === "ROAD_SEGMENT") {
      const poly = STATE.roadPolylines[assetId];
      if (poly) {
        if (currentState === "FAILED") {
          poly.setStyle({ color: "#525252", dashArray: "4, 6", weight: 2.5 });
          poly.setTooltipContent(`<b>${dist.name}</b><br><span style="color:#a3a3a3">IMPASSABLE / SUBMERGED</span>`);
        } else {
          poly.setStyle({ color: "#ffffff", dashArray: null, weight: 3.5 });
          poly.setTooltipContent(`<b>${dist.name}</b><br><span style="color:#ffffff">PASSABLE</span>`);
        }
      }
    } else {
      const marker = STATE.assetMarkers[assetId];
      if (marker) {
        const icon = getAssetCustomIcon(dist.type, currentState);
        marker.setIcon(icon);
      }
    }

    if (currentState === "OPERATING") operatingCount++;
    else if (currentState === "ON_BACKUP") backupCount++;
    else if (currentState === "FAILED") failedCount++;
  });

  document.getElementById("countOperating").textContent = operatingCount;
  document.getElementById("countBackup").textContent = backupCount;
  document.getElementById("countFailed").textContent = failedCount;
  document.getElementById("sidebarTimeVal").textContent = `T${timeH >= 0 ? "+" : ""}${timeH.toFixed(1)}h`;

  // Update Storm Position
  updateStormPosition(timeH);
}

function updateStormPosition(timeH) {
  if (!STATE.stormMarker) return;
  // Move storm along track approaching Puri (landfall near 19.78, 85.80 at T=0)
  // Simple parametric track interpolation for visual feedback
  const lat = 19.78 + timeH * 0.055;
  const lon = 85.80 + timeH * 0.050;
  STATE.stormMarker.setLatLng([lat, lon]);
}

// --- PLAYBACK CONTROLS ---
function initPlaybackControls() {
  const slider = document.getElementById("timeSlider");
  const playBtn = document.getElementById("btnPlayPause");
  const stepBackBtn = document.getElementById("btnStepBack");
  const stepFwdBtn = document.getElementById("btnStepFwd");

  slider.addEventListener("input", (e) => {
    STATE.currentTimeH = parseFloat(e.target.value);
    updateTimeDisplay();
    updateMapStateAtTime(STATE.currentTimeH);
  });

  playBtn.addEventListener("click", () => {
    if (STATE.isPlaying) pausePlayback();
    else startPlayback();
  });

  stepBackBtn.addEventListener("click", () => {
    STATE.currentTimeH = Math.max(-24, STATE.currentTimeH - 1);
    slider.value = STATE.currentTimeH;
    updateTimeDisplay();
    updateMapStateAtTime(STATE.currentTimeH);
  });

  stepFwdBtn.addEventListener("click", () => {
    STATE.currentTimeH = Math.min(36, STATE.currentTimeH + 1);
    slider.value = STATE.currentTimeH;
    updateTimeDisplay();
    updateMapStateAtTime(STATE.currentTimeH);
  });

  document.querySelectorAll(".speed-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".speed-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      STATE.playSpeed = parseInt(btn.dataset.speed, 10);
      if (STATE.isPlaying) {
        pausePlayback();
        startPlayback();
      }
    });
  });
}

function startPlayback() {
  STATE.isPlaying = true;
  document.getElementById("btnPlayPause").textContent = "Pause";
  STATE.playInterval = setInterval(() => {
    if (STATE.currentTimeH >= 36) {
      pausePlayback();
      return;
    }
    STATE.currentTimeH += 1;
    document.getElementById("timeSlider").value = STATE.currentTimeH;
    updateTimeDisplay();
    updateMapStateAtTime(STATE.currentTimeH);
  }, 1000 / STATE.playSpeed);
}

function pausePlayback() {
  STATE.isPlaying = false;
  document.getElementById("btnPlayPause").textContent = "Play";
  clearInterval(STATE.playInterval);
}

function updateTimeDisplay() {
  const t = STATE.currentTimeH;
  const sign = t >= 0 ? "+" : "";
  const text = `T${sign}${t.toFixed(1)}h`;
  document.getElementById("scrubClockDisplay").textContent = text;
  document.getElementById("doomsdaySimTime").textContent = text;

  let phase = "PRE-LANDFALL WARNING (T-24h to T-12h)";
  if (t >= -12 && t < -2) phase = "PRE-LANDFALL PREPARATION (T-12h to T-2h)";
  else if (t >= -2 && t <= 4) phase = "EYEWALL LANDFALL WINDOW (T-2h to T+4h)";
  else if (t > 4 && t <= 20) phase = "POST-LANDFALL CASCADE (T+4h to T+20h)";
  else if (t > 20) phase = "RECOVERY & RESTORATION (T+24h+)";

  document.getElementById("phaseIndicator").textContent = phase;
}

// --- CHARTS ---
function renderCLLIChart() {
  const ctx = document.getElementById("clliChart").getContext("2d");
  if (STATE.clliChart) STATE.clliChart.destroy();

  const labels = STATE.clliTimeline.map((pt) => `T${pt[0] >= 0 ? "+" : ""}${pt[0]}h`);
  const dataP50 = STATE.clliTimeline.map((pt) => pt[2]);
  const dataP90 = STATE.clliTimeline.map((pt) => pt[3]);

  STATE.clliChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "P50 CLLI (Median)",
          data: dataP50,
          borderColor: "#ffffff",
          backgroundColor: "rgba(255, 255, 255, 0.05)",
          fill: true,
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: "P90 CLLI (Severe)",
          data: dataP90,
          borderColor: "#737373",
          borderDash: [4, 4],
          fill: false,
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 1.5,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { mode: "index", intersect: false },
      },
      scales: {
        x: { ticks: { maxTicksLimit: 6, color: "#737373", font: { size: 9, family: "'JetBrains Mono', monospace" } }, grid: { display: false } },
        y: { ticks: { color: "#737373", font: { size: 9, family: "'JetBrains Mono', monospace" } }, grid: { color: "#262626" } },
      },
    },
  });
}

// --- QUICK ACTIONS SIDEBAR ---
function renderQuickActions() {
  const container = document.getElementById("quickActionList");
  container.innerHTML = "";
  document.getElementById("actionCountBadge").textContent = STATE.actions.length;

  STATE.actions.slice(0, 4).forEach((act) => {
    const card = document.createElement("div");
    card.className = "action-card";
    const hoursLeft = Math.max(act.deadline_h - STATE.currentTimeH, 0);
    const urgency = hoursLeft <= 2 ? "critical" : hoursLeft <= 6 ? "high" : "medium";

    card.innerHTML = `
      <div class="action-header">
        <div class="action-title">${act.title}</div>
        <span class="countdown-pill ${urgency}">${hoursLeft.toFixed(1)}h left</span>
      </div>
      <div class="action-benefit">${act.benefit_summary}</div>
      <div class="action-footer">
        <span>Route: ${act.route_asset_ids[0] || "Direct"}</span>
        <span>${act.resources_needed.split(",")[0]}</span>
      </div>
    `;
    container.appendChild(card);
  });
}

// --- ASSET DEEP-DIVE MODAL ---
async function openAssetModal(assetId) {
  try {
    const res = await fetch(`${API_BASE}/api/scenario/${STATE.scenarioId}/assets/${assetId}/explain`);
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("modalAssetName").textContent = data.name;
    document.getElementById("modalAssetType").textContent = data.type;
    document.getElementById("modalAssetMeta").textContent = `Asset ID: ${data.asset_id} | Criticality Weight: ${data.criticality}`;

    document.getElementById("modalP10").textContent = data.p10_fail_time_h !== null ? `T${data.p10_fail_time_h >= 0 ? "+" : ""}${data.p10_fail_time_h}h` : "Survived";
    document.getElementById("modalP50").textContent = data.p50_fail_time_h !== null ? `T${data.p50_fail_time_h >= 0 ? "+" : ""}${data.p50_fail_time_h}h` : "Survived";
    document.getElementById("modalP90").textContent = data.p90_fail_time_h !== null ? `T${data.p90_fail_time_h >= 0 ? "+" : ""}${data.p90_fail_time_h}h` : "Survived";

    document.getElementById("modalDominantCause").textContent = `${data.dominant_cause} (Primary trigger across simulations)`;

    // Cause bars
    const barsContainer = document.getElementById("modalCauseBars");
    barsContainer.innerHTML = "";
    Object.entries(data.cause_breakdown).forEach(([cause, pct]) => {
      const row = document.createElement("div");
      row.style.marginBottom = "6px";
      row.innerHTML = `
        <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:2px;">
          <span>${cause}</span>
          <span style="font-family:var(--font-mono); font-weight:700;">${pct}%</span>
        </div>
        <div style="height:6px; background:#262626; border-radius:3px; overflow:hidden;">
          <div style="height:100%; width:${pct}%; background:#ffffff; border-radius:3px;"></div>
        </div>
      `;
      barsContainer.appendChild(row);
    });

    // Causal chain
    const chainContainer = document.getElementById("modalCausalChain");
    chainContainer.innerHTML = "";
    if (data.causal_chain.length === 0) {
      chainContainer.innerHTML = `<div class="chain-step" style="border-left-color:#ffffff">Asset operates normally without cascade failure.</div>`;
    } else {
      data.causal_chain.forEach((step) => {
        const item = document.createElement("div");
        item.className = "chain-step";
        item.textContent = step;
        chainContainer.appendChild(item);
      });
    }

    // Dependency links
    document.getElementById("modalPowerSource").textContent = data.upstream_power_nodes.join(", ") || "Self-powered / Off-grid";
    document.getElementById("modalResupplyRoute").textContent = data.resupply_routes.length > 0 ? `${data.resupply_routes[0].depot_id} via ${data.resupply_routes[0].road_path.join(" -> ")}` : "No external resupply route required";

    document.getElementById("assetModal").classList.remove("hidden");
  } catch (err) {
    console.error("Error opening modal:", err);
  }
}

function closeModal() {
  document.getElementById("assetModal").classList.add("hidden");
}

// --- TAB 2: LAST SAFE MINUTE (DOOMSDAY BOARD) ---
async function loadDoomsdayBoard() {
  const container = document.getElementById("doomsdayBoardGrid");
  container.innerHTML = `<div style="color:var(--text-muted)">Computing route closure thresholds...</div>`;
  try {
    const res = await fetch(`${API_BASE}/api/scenario/${STATE.scenarioId}/doomsday?current_time_h=${STATE.currentTimeH}`);
    const data = await res.json();
    container.innerHTML = "";

    data.actions_board.forEach((item) => {
      const card = document.createElement("div");
      card.className = `doomsday-card ${item.urgency}`;
      card.innerHTML = `
        <div class="doomsday-card-top">
          <div>
            <div style="font-size:13px; font-weight:700; color:#fff; margin-bottom:4px;">${item.title}</div>
            <div class="doomsday-subtext">Target: <b>${item.target_asset_id}</b></div>
          </div>
          <span class="countdown-pill ${item.urgency}">${item.status}</span>
        </div>

        <div style="display:flex; align-items:baseline; gap:8px;">
          <div class="doomsday-time-left">${item.hours_remaining.toFixed(1)}h</div>
          <span style="font-size:11px; color:var(--text-muted)">Remaining to Safe Departure</span>
        </div>

        <div class="route-bottleneck-box">
          <b>Route Corridor:</b> ${item.bottleneck_routes.join(", ") || "Direct Access"}<br>
          <b>Closure P50:</b> T${item.confidence_interval.expected_p50_h >= 0 ? "+" : ""}${item.confidence_interval.expected_p50_h.toFixed(1)}h
          (P10: T${item.confidence_interval.conservative_p10_h.toFixed(1)}h)
        </div>

        <div style="font-size:11px; color:var(--text-secondary);">${item.benefit_summary}</div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Error loading doomsday board:", err);
  }
}

// --- TAB 3: TIME MACHINE / WHAT-IF ---
function loadTimeMachineList() {
  const container = document.getElementById("whatifCheckboxList");
  container.innerHTML = "";

  STATE.actions.forEach((act) => {
    const div = document.createElement("div");
    div.className = "whatif-item";
    div.innerHTML = `
      <input type="checkbox" id="whatif_${act.id}" value="${act.id}">
      <div>
        <label for="whatif_${act.id}" class="whatif-item-title">${act.title}</label>
        <div class="whatif-item-desc">${act.description}</div>
      </div>
    `;
    container.appendChild(div);
  });
}

async function executeWhatIf() {
  const checkedBoxes = document.querySelectorAll("#whatifCheckboxList input:checked");
  const selectedIds = Array.from(checkedBoxes).map((cb) => cb.value);

  if (selectedIds.length === 0) {
    alert("Please select at least one intervention to fork the timeline.");
    return;
  }

  document.getElementById("btnRunWhatIf").textContent = "Computing...";

  try {
    const res = await fetch(`${API_BASE}/api/scenario/${STATE.scenarioId}/whatif`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selected_action_ids: selectedIds, branch_time_h: -6.0 }),
    });
    const data = await res.json();

    document.getElementById("whatifSavedPoints").textContent = data.total_lifeline_points_saved.toFixed(1);
    document.getElementById("whatifDesc").textContent =
      `Applied ${data.applied_actions.length} interventions. Cascade delayed across district assets using Common Random Numbers.`;

    renderWhatIfChart(data.clli_comparison);
  } catch (err) {
    console.error("Error running what-if:", err);
  } finally {
    document.getElementById("btnRunWhatIf").textContent = "Compute Forked Timeline";
  }
}

function renderWhatIfChart(comp) {
  const ctx = document.getElementById("whatifChart").getContext("2d");
  if (STATE.whatifChart) STATE.whatifChart.destroy();

  const labels = comp.time_steps.map((t) => `T${t >= 0 ? "+" : ""}${t}h`);

  STATE.whatifChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Baseline Loss (No Action)",
          data: comp.baseline_clli_p50,
          borderColor: "#737373",
          borderDash: [4, 4],
          backgroundColor: "transparent",
          tension: 0.3,
          borderWidth: 1.5,
          pointRadius: 0,
        },
        {
          label: "Forked Timeline (With Interventions)",
          data: comp.branch_clli_p50,
          borderColor: "#ffffff",
          backgroundColor: "rgba(255, 255, 255, 0.08)",
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#ffffff", font: { family: "'JetBrains Mono', monospace", size: 11 } } },
      },
      scales: {
        x: { ticks: { color: "#737373", font: { family: "'JetBrains Mono', monospace" } }, grid: { color: "#1e1e1e" } },
        y: { ticks: { color: "#737373", font: { family: "'JetBrains Mono', monospace" } }, grid: { color: "#1e1e1e" } },
      },
    },
  });
}

// --- TAB 4: KEYSTONES & SHAPLEY ---
async function loadKeystonesAndShapley() {
  try {
    const res = await fetch(`${API_BASE}/api/scenario/${STATE.scenarioId}/keystones`);
    const data = await res.json();

    const table = document.getElementById("keystoneTable");
    table.innerHTML = "";
    data.top_keystones.forEach((k, idx) => {
      const item = document.createElement("div");
      item.className = "keystone-item";
      item.innerHTML = `
        <div>
          <div style="font-size:13px; font-weight:700; color:#fff;">#${idx + 1}: ${k.name}</div>
          <div style="font-size:11px; color:var(--text-muted);">${k.type} | Protects ${k.downstream_dependent_count} Downstream Assets</div>
        </div>
        <div style="text-align:right">
          <div class="keystone-score-badge">${k.keystone_score}%</div>
          <div style="font-size:10px; color:var(--text-dim)">Cascade Mitigation Leverage</div>
        </div>
      `;
      table.appendChild(item);
    });

    const shapley = document.getElementById("shapleyBreakdown");
    shapley.innerHTML = "";
    data.shapley_blame.attributions.forEach((attr) => {
      const row = document.createElement("div");
      row.className = "shapley-bar-row";
      row.innerHTML = `
        <div class="shapley-bar-header">
          <span>${attr.cause}</span>
          <span style="font-family:var(--font-mono); color:var(--accent-blue);">${attr.shapley_pct}%</span>
        </div>
        <div class="shapley-progress-bg">
          <div class="shapley-progress-fill" style="width:${attr.shapley_pct}%"></div>
        </div>
        <div class="shapley-bar-desc">${attr.explanation}</div>
      `;
      shapley.appendChild(row);
    });
  } catch (err) {
    console.error("Error loading keystones:", err);
  }
}

// --- TAB 5: CRISIS COUNCIL ---
async function loadCrisisCouncil() {
  try {
    const res = await fetch(`${API_BASE}/api/scenario/${STATE.scenarioId}/crisis-council`);
    const data = await res.json();

    const feed = document.getElementById("councilTranscript");
    feed.innerHTML = "";

    data.transcript.forEach((msg) => {
      const card = document.createElement("div");
      card.className = "transcript-msg";
      card.innerHTML = `
        <div class="msg-header">
          <div class="msg-speaker">${msg.speaker}</div>
          <div class="msg-role">${msg.role}</div>
        </div>
        <div class="msg-body">${msg.message}</div>
        ${
          msg.tool_citation
            ? `<div class="tool-tag" title="Verified Simulation Metric">${msg.tool_citation.tag}: ${msg.tool_citation.value}</div>`
            : ""
        }
      `;
      feed.appendChild(card);
    });

    const orders = document.getElementById("councilOrders");
    orders.innerHTML = "";
    data.consensus_plan.forEach((o) => {
      const div = document.createElement("div");
      div.className = "order-card";
      div.innerHTML = `
        <div style="font-weight:700; color:#fff;">Step ${o.step}: ${o.action}</div>
        <div style="display:flex; justify-content:space-between; margin-top:4px; color:var(--text-muted); font-size:11px;">
          <span>Agency: <b>${o.owner}</b></span>
          <span style="font-family:var(--font-mono); color:#ffffff;">Deadline: ${o.deadline}</span>
        </div>
      `;
      orders.appendChild(div);
    });

    const dissent = document.getElementById("councilDissent");
    if (data.dissent_log && data.dissent_log.length > 0) {
      dissent.innerHTML = `
        <b>Dissent Log:</b> ${data.dissent_log[0].stakeholder} - ${data.dissent_log[0].conflict}<br>
        <span style="color:var(--text-dim)">Resolution: ${data.dissent_log[0].resolution}</span>
      `;
    }
  } catch (err) {
    console.error("Error loading crisis council:", err);
  }
}

// --- TAB 6: RED TEAM ---
function loadRedTeamDefault() {
  // If already run, no need
}

async function runRedTeam() {
  document.getElementById("btnRunRedTeam").textContent = "Running Stress Test...";
  try {
    const res = await fetch(`${API_BASE}/api/scenario/${STATE.scenarioId}/redteam`, { method: "POST" });
    const data = await res.json();

    document.getElementById("redTeamScore").textContent = `${data.plan_robustness_score}%`;
    document.getElementById("redTeamScoreDesc").textContent =
      `${data.survived_facilities} of ${data.facilities_evaluated} critical facilities survived Category 5 stress test`;

    const list = document.getElementById("redteamFacilityList");
    list.innerHTML = "";
    data.facility_breakdown.forEach((fac) => {
      const row = document.createElement("div");
      row.className = "facility-row";
      row.innerHTML = `
        <span>${fac.name}</span>
        <span style="font-family:var(--font-mono); color:${fac.robust ? "#ffffff" : "#737373"}">
          ${fac.robust ? "[ROBUST]" : "[AT RISK]"} (${fac.fail_risk_under_redteam_pct}% Fail Risk)
        </span>
      `;
      list.appendChild(row);
    });

    const findings = document.getElementById("redteamFindings");
    findings.innerHTML = "<b>Stress Test Vulnerability Findings:</b><br>" + data.adversarial_findings.map((f) => `• ${f}`).join("<br>");
  } catch (err) {
    console.error("Error running red team:", err);
  } finally {
    document.getElementById("btnRunRedTeam").textContent = "Run Adversarial Test";
  }
}
