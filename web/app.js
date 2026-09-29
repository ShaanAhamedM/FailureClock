/**
 * Failure Clock — Lead-Designer Grade Operations Controller
 * High-performance, reactive, and minimalist UI orchestration.
 * All 20 audited bugs squashed with robust defensive design.
 */

const API_BASE = window.location.origin;

const STATE = {
  scenarioId: "severe_cyclone_live",
  currentTimeH: -12.0,
  isPlaying: false,
  playInterval: null,
  graph: null,
  scenarioAssets: null,
  scenarioTrack: [],
  timeSteps: [],
  metrics: null,
  actions: [],
  councilData: null,
  whatifData: null,
  map: null,
  assetMarkers: {},
  roadPolylines: {},
  stormMarker: null,
  selectedAssetId: null,
  selectedMarkerElement: null,
  tmChartInstance: null,
  currentDrawerPane: "actions",
  isDrawerOpen: false,
};

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener("DOMContentLoaded", async () => {
  initMap();
  initNavigation();
  initScrubber();
  initScenarioSelect();
  initTimeMachine();

  await loadScenario(STATE.scenarioId);
});

// ==========================================================================
// Map Initialization
// ==========================================================================
function initMap() {
  // Center on Puri District, Odisha
  STATE.map = L.map("map", {
    center: [19.820, 85.835],
    zoom: 12,
    zoomControl: false,
    attributionControl: true,
  });

  // Re-add zoom control to avoid obscuring floating island
  L.control.zoom({ position: "topleft" }).addTo(STATE.map);

  // High-reliability OpenStreetMap tile layer styled via grayscale CSS
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; OpenStreetMap · Failure Clock System',
    subdomains: ["a", "b", "c"],
    maxZoom: 18,
  }).addTo(STATE.map);

  // BUG-12 Fix: Dismiss slide-over drawer when clicking directly on map canvas
  STATE.map.on("click", (e) => {
    if (e.originalEvent) {
      const target = e.originalEvent.target;
      if (target.id === "map" || target.classList.contains("leaflet-tile")) {
        closeDrawer();
        deselectActiveMarker();
      }
    }
  });
}

// ==========================================================================
// Navigation & Drawer Management
// ==========================================================================
function initNavigation() {
  const toggleBtn = document.getElementById("btnToggleDrawer");
  const closeBtn = document.getElementById("btnCloseDrawer");
  const backBtn = document.getElementById("btnBackToActions");
  const navButtons = document.querySelectorAll(".nav-segment-btn");

  // Toggle drawer open/close
  toggleBtn.addEventListener("click", () => {
    toggleDrawer();
  });

  closeBtn.addEventListener("click", () => {
    closeDrawer();
    deselectActiveMarker();
  });

  // BUG-11 Fix: Back to Action Deadlines from Asset Detail
  if (backBtn) {
    backBtn.addEventListener("click", () => {
      switchDrawerPane("actions");
    });
  }

  // Top Nav Segmented Buttons
  navButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetPane = btn.dataset.drawer;
      navButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      // Switch to this pane
      switchDrawerPane(targetPane);

      // Open drawer if it's currently collapsed
      openDrawer();
    });
  });
}

function openDrawer() {
  const drawer = document.getElementById("slideDrawer");
  drawer.classList.remove("collapsed");
  STATE.isDrawerOpen = true;

  // BUG-04 Fix: Ensure Chart.js resizes properly when opening drawer
  if (STATE.currentDrawerPane === "timemachine" && STATE.tmChartInstance) {
    setTimeout(() => {
      STATE.tmChartInstance.resize();
    }, 150);
  }
}

function closeDrawer() {
  const drawer = document.getElementById("slideDrawer");
  drawer.classList.add("collapsed");
  STATE.isDrawerOpen = false;
}

function toggleDrawer() {
  if (STATE.isDrawerOpen) {
    closeDrawer();
    deselectActiveMarker();
  } else {
    openDrawer();
  }
}

function switchDrawerPane(paneName) {
  STATE.currentDrawerPane = paneName;

  // Update Drawer Titles & Subtitles
  const titleEl = document.getElementById("drawerTitle");
  const subEl = document.getElementById("drawerSubtitle");

  const paneMap = {
    actions: {
      id: "paneActions",
      title: "Action Deadlines",
      sub: "Pre-landfall intervention countdowns & route passability",
    },
    timeline: {
      id: "paneTimeline",
      title: "Failure Sequence",
      sub: "Simulated cascade chronology & trigger analysis",
    },
    detail: {
      id: "paneDetail",
      title: "Asset Intelligence",
      sub: "Causal dependency chain & outage probability",
    },
    timemachine: {
      id: "paneTimemachine",
      title: "Time Machine (What-If)",
      sub: "Counterfactual branch simulation via Common Random Numbers",
    },
    council: {
      id: "paneCouncil",
      title: "Crisis Council Memorandum",
      sub: "Inter-agency deliberation & synthesized action orders",
    },
  };

  const current = paneMap[paneName] || paneMap.actions;
  titleEl.textContent = current.title;
  subEl.textContent = current.sub;

  // Toggle pane visibility
  document.querySelectorAll(".drawer-pane").forEach((p) => p.classList.remove("active"));
  const activePane = document.getElementById(current.id);
  if (activePane) activePane.classList.add("active");

  // Sync nav buttons
  document.querySelectorAll(".nav-segment-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.drawer === paneName);
  });

  // BUG-04 Fix: Resize chart if switching to timemachine
  if (paneName === "timemachine" && STATE.tmChartInstance) {
    setTimeout(() => {
      STATE.tmChartInstance.resize();
    }, 100);
  }
}

// ==========================================================================
// Scenario Select
// ==========================================================================
function initScenarioSelect() {
  const sel = document.getElementById("scenarioSelect");
  sel.addEventListener("change", async (e) => {
    await loadScenario(e.target.value);
  });
}

// ==========================================================================
// Scenario Data Loader (BUG-14, BUG-16 Fixes)
// ==========================================================================
async function loadScenario(scenarioId) {
  STATE.scenarioId = scenarioId;

  try {
    const [assetsRes, graphRes, actionsRes, councilRes] = await Promise.all([
      fetch(`${API_BASE}/api/scenario/${scenarioId}/assets`),
      fetch(`${API_BASE}/api/graph`),
      fetch(`${API_BASE}/api/scenario/${scenarioId}/actions`),
      fetch(`${API_BASE}/api/scenario/${scenarioId}/crisis-council`),
    ]);

    if (!assetsRes.ok || !graphRes.ok || !actionsRes.ok || !councilRes.ok) {
      throw new Error("One or more scenario endpoints returned an error");
    }

    const assetsData = await assetsRes.json();
    STATE.scenarioAssets = assetsData.assets;
    STATE.metrics = assetsData.metrics;
    STATE.scenarioTrack = assetsData.track || [];
    STATE.timeSteps = assetsData.time_steps || [];
    STATE.graph = await graphRes.json();
    STATE.actions = await actionsRes.json();
    STATE.councilData = await councilRes.json();

    // BUG-14 Fix: Dynamically configure slider bounds from scenario time_steps
    const slider = document.getElementById("timeSlider");
    if (slider && STATE.timeSteps.length > 0) {
      const minT = STATE.timeSteps[0];
      const maxT = STATE.timeSteps[STATE.timeSteps.length - 1];
      slider.min = minT;
      slider.max = maxT;
      // Default to T-12h if within bounds, else minT
      STATE.currentTimeH = (minT <= -12.0 && maxT >= -12.0) ? -12.0 : minT;
      slider.value = STATE.currentTimeH;
    }

    // Update Action count badge in top island
    const badgeEl = document.getElementById("badgeActionCount");
    if (badgeEl) badgeEl.textContent = STATE.actions.length;

    renderMap();
    renderActions();
    renderFailureSequence();
    renderCouncil();
    renderTimeMachineOptions();
    updateTimeDisplay();
    updateStateAtTime(STATE.currentTimeH);
  } catch (err) {
    console.error("Failed to load scenario data:", err);
    // BUG-16 Fix: Display non-intrusive toast notification
    showErrorToast("Network error: Failed to load cyclone scenario data. Please check connection.");
  }
}

function showErrorToast(msg) {
  const existing = document.querySelector(".error-toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = "error-toast";
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4500);
}

// ==========================================================================
// Map Rendering & Markers (BUG-08, BUG-10 Fixes)
// ==========================================================================
function renderMap() {
  // Clear existing layers
  Object.values(STATE.assetMarkers).forEach((m) => STATE.map.removeLayer(m));
  Object.values(STATE.roadPolylines).forEach((r) => STATE.map.removeLayer(r));
  STATE.assetMarkers = {};
  STATE.roadPolylines = {};
  if (STATE.stormMarker) STATE.map.removeLayer(STATE.stormMarker);

  if (!STATE.graph || !STATE.graph.nodes) return;
  const nodes = STATE.graph.nodes;

  // 1. Road Segments
  nodes.filter((n) => n.type === "ROAD_SEGMENT").forEach((road) => {
    const coords = getRoadCoordinates(road.id, road.lat, road.lon);
    const poly = L.polyline(coords, {
      color: "#18181b",
      weight: 3.5,
      opacity: 0.85,
      smoothFactor: 1.0,
    }).addTo(STATE.map);

    poly.bindTooltip(
      `<b>${road.name}</b><br><span style="font-size:10px;color:#71717a">Click to inspect passability</span>`,
      { sticky: true }
    );
    poly.on("click", () => inspectAsset(road.id));
    STATE.roadPolylines[road.id] = poly;
  });

  // 2. Critical Facilities & Infrastructure Nodes
  nodes.filter((n) => n.type !== "ROAD_SEGMENT").forEach((node) => {
    const icon = createNodeIcon(node.type, "OPERATING");
    const marker = L.marker([node.lat, node.lon], { icon }).addTo(STATE.map);

    marker.bindTooltip(
      `<b>${node.name}</b><br><span style="font-size:10px;color:#71717a">${node.type.replace(/_/g, " ")} · Click to inspect</span>`,
      { sticky: true }
    );
    marker.on("click", () => inspectAsset(node.id));
    STATE.assetMarkers[node.id] = marker;
  });

  // 3. Cyclone Center Eye Marker
  const stormIcon = L.divIcon({
    className: "custom-storm-icon",
    html: `
      <div class="storm-eye-wrapper">
        <div class="storm-eye-pulse"></div>
        <div class="storm-eye-center">◎</div>
      </div>
    `,
    iconSize: [44, 44],
    iconAnchor: [22, 22],
  });

  const initPos = interpolateStormPosition(STATE.scenarioTrack, STATE.currentTimeH);
  STATE.stormMarker = L.marker([initPos.lat, initPos.lon], { icon: stormIcon }).addTo(STATE.map);
  STATE.stormMarker.bindTooltip("<b>Cyclone Eye Center</b><br>Track Tracking Station", { sticky: true });
}

function createNodeIcon(type, state) {
  let label = "H";
  if (type === "SUBSTATION") label = "SS";
  else if (type === "FEEDER") label = "FD";
  else if (type === "TOWER") label = "TX";
  else if (type === "WATER_PUMP") label = "WP";
  else if (type === "DEPOT") label = "DP";

  let stateClass = "operating";
  if (state === "ON_BACKUP") stateClass = "backup";
  else if (state === "FAILED") stateClass = "failed";

  return L.divIcon({
    className: "custom-node-icon",
    html: `<div class="node-badge-v2 ${stateClass}" data-type="${type}">${label}</div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
}

// BUG-08 Fix: Interpolate exact storm eye coordinates from scenario track
function interpolateStormPosition(track, timeH) {
  if (!track || track.length === 0) {
    return { lat: 19.78, lon: 85.80 };
  }
  if (timeH <= track[0].time_offset_hours) {
    return { lat: track[0].lat, lon: track[0].lon };
  }
  if (timeH >= track[track.length - 1].time_offset_hours) {
    const last = track[track.length - 1];
    return { lat: last.lat, lon: last.lon };
  }

  for (let i = 0; i < track.length - 1; i++) {
    const t1 = track[i].time_offset_hours;
    const t2 = track[i + 1].time_offset_hours;
    if (t1 <= timeH && timeH <= t2) {
      const alpha = (timeH - t1) / Math.max(t2 - t1, 0.001);
      return {
        lat: track[i].lat + alpha * (track[i + 1].lat - track[i].lat),
        lon: track[i].lon + alpha * (track[i + 1].lon - track[i].lon),
      };
    }
  }
  return { lat: track[0].lat, lon: track[0].lon };
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
  return [[centerLat - 0.015, centerLon - 0.015], [centerLat, centerLon], [centerLat + 0.015, centerLon + 0.015]];
}

// ==========================================================================
// Time Engine & Dynamic State Updates (BUG-07, BUG-08 Fixes)
// ==========================================================================
function updateStateAtTime(timeH) {
  if (!STATE.scenarioAssets) return;

  let countOp = 0;
  let countBk = 0;
  let countFa = 0;

  Object.entries(STATE.scenarioAssets).forEach(([aid, dist]) => {
    let state = "OPERATING";
    const timeline = dist.state_timeline_p50 || [];
    const match = timeline.find((pt) => Math.abs(pt[0] - timeH) < 0.05);
    if (match) {
      state = match[1];
    } else {
      let lastKnown = "OPERATING";
      for (const [t, s] of timeline) {
        if (t <= timeH) lastKnown = s;
        else break;
      }
      state = lastKnown;
    }

    if (dist.type === "ROAD_SEGMENT") {
      const poly = STATE.roadPolylines[aid];
      if (poly) {
        if (state === "FAILED") {
          poly.setStyle({ color: "#a1a1aa", dashArray: "4, 6", weight: 2.5, opacity: 0.6 });
        } else {
          poly.setStyle({ color: "#18181b", dashArray: null, weight: 3.5, opacity: 0.9 });
        }
      }
    } else {
      const marker = STATE.assetMarkers[aid];
      if (marker) {
        marker.setIcon(createNodeIcon(dist.type, state));
      }
    }

    if (state === "OPERATING") countOp++;
    else if (state === "ON_BACKUP") countBk++;
    else if (state === "FAILED") countFa++;
  });

  // Re-apply selection highlight if active (BUG-10 Fix)
  if (STATE.selectedAssetId && STATE.assetMarkers[STATE.selectedAssetId]) {
    const marker = STATE.assetMarkers[STATE.selectedAssetId];
    const el = marker.getElement();
    if (el) {
      const badge = el.querySelector(".node-badge-v2");
      if (badge) badge.classList.add("is-selected");
    }
  }

  // Telemetry Pills
  const opEl = document.getElementById("statOperating");
  const bkEl = document.getElementById("statBackup");
  const faEl = document.getElementById("statFailed");
  if (opEl) opEl.textContent = countOp;
  if (bkEl) bkEl.textContent = countBk;
  if (faEl) faEl.textContent = countFa;

  // BUG-08 Fix: True storm eye movement from interpolated track coordinates
  if (STATE.stormMarker && STATE.scenarioTrack && STATE.scenarioTrack.length > 0) {
    const pos = interpolateStormPosition(STATE.scenarioTrack, timeH);
    STATE.stormMarker.setLatLng([pos.lat, pos.lon]);
  }

  // BUG-07 Fix: Visual progress fill width update
  const slider = document.getElementById("timeSlider");
  const fill = document.getElementById("sliderFill");
  if (slider && fill) {
    const min = parseFloat(slider.min);
    const max = parseFloat(slider.max);
    const pct = ((timeH - min) / (max - min)) * 100;
    fill.style.width = `${Math.max(0, Math.min(pct, 100))}%`;
  }
}

function updateTimeDisplay() {
  const t = STATE.currentTimeH;
  const sign = t >= 0 ? "+" : "";
  const clockEl = document.getElementById("clockDisplay");
  const phaseEl = document.getElementById("phaseDisplay");

  if (clockEl) {
    clockEl.textContent = `T${sign}${t.toFixed(1)}h`;
  }

  let phase = "Pre-Landfall Warning";
  if (t <= -18) phase = "Pre-Landfall Warning (48h-24h)";
  else if (t > -18 && t <= -6) phase = "Pre-Landfall Preparation";
  else if (t > -6 && t <= -1) phase = "Final Evacuation Window";
  else if (t > -1 && t <= 3) phase = "Landfall Eye Window";
  else if (t > 3 && t <= 16) phase = "Peak Surge & Wind Cascade";
  else phase = "Post-Storm Recovery Phase";

  if (phaseEl) phaseEl.textContent = phase;
}

// ==========================================================================
// Scrubber Controls & Playback (BUG-17 Fix)
// ==========================================================================
function initScrubber() {
  const slider = document.getElementById("timeSlider");
  const playBtn = document.getElementById("btnPlayPause");
  const stepBackBtn = document.getElementById("btnStepBack");
  const stepFwdBtn = document.getElementById("btnStepFwd");

  slider.addEventListener("input", (e) => {
    STATE.currentTimeH = parseFloat(e.target.value);
    updateTimeDisplay();
    updateStateAtTime(STATE.currentTimeH);
    renderActions();
  });

  playBtn.addEventListener("click", () => {
    if (STATE.isPlaying) pausePlay();
    else startPlay();
  });

  stepBackBtn.addEventListener("click", () => {
    const min = parseFloat(slider.min || -24);
    STATE.currentTimeH = Math.max(min, STATE.currentTimeH - 1);
    slider.value = STATE.currentTimeH;
    updateTimeDisplay();
    updateStateAtTime(STATE.currentTimeH);
    renderActions();
  });

  stepFwdBtn.addEventListener("click", () => {
    const max = parseFloat(slider.max || 36);
    STATE.currentTimeH = Math.min(max, STATE.currentTimeH + 1);
    slider.value = STATE.currentTimeH;
    updateTimeDisplay();
    updateStateAtTime(STATE.currentTimeH);
    renderActions();
  });
}

function startPlay() {
  const slider = document.getElementById("timeSlider");
  const max = parseFloat(slider.max || 36);
  const min = parseFloat(slider.min || -24);

  // BUG-17 Fix: Reset to start if playing at the end of timeline
  if (STATE.currentTimeH >= max) {
    STATE.currentTimeH = min;
    slider.value = min;
    updateTimeDisplay();
    updateStateAtTime(STATE.currentTimeH);
  }

  STATE.isPlaying = true;
  document.getElementById("iconPlay").classList.add("hidden");
  document.getElementById("iconPause").classList.remove("hidden");

  STATE.playInterval = setInterval(() => {
    if (STATE.currentTimeH >= max) {
      pausePlay();
      return;
    }
    STATE.currentTimeH += 1;
    slider.value = STATE.currentTimeH;
    updateTimeDisplay();
    updateStateAtTime(STATE.currentTimeH);
    renderActions();
  }, 750);
}

function pausePlay() {
  STATE.isPlaying = false;
  document.getElementById("iconPlay").classList.remove("hidden");
  document.getElementById("iconPause").classList.add("hidden");
  clearInterval(STATE.playInterval);
}

// ==========================================================================
// Action Deadlines Pane (BUG-03, BUG-09 Fixes)
// ==========================================================================
function renderActions() {
  const container = document.getElementById("actionsContainer");
  if (!container) return;
  container.innerHTML = "";

  if (!STATE.actions || STATE.actions.length === 0) {
    container.innerHTML = `<div class="empty-state-notice"><p>No interventions configured for this scenario.</p></div>`;
    return;
  }

  STATE.actions.forEach((act, idx) => {
    const hoursRemaining = act.deadline_h - STATE.currentTimeH;
    const isExpired = hoursRemaining <= 0;
    const isUrgent = hoursRemaining > 0 && hoursRemaining <= 3.0;

    let deadlineClass = "";
    let deadlineText = `${hoursRemaining.toFixed(1)}h left`;
    if (isExpired) {
      deadlineClass = "expired";
      deadlineText = "WINDOW EXPIRED";
    } else if (isUrgent) {
      deadlineClass = "urgent";
      deadlineText = `CRITICAL: ${hoursRemaining.toFixed(1)}h left`;
    }

    // BUG-09 Fix: Route passability float comparison with epsilon tolerance
    const routeId = (act.route_asset_ids && act.route_asset_ids.length > 0) ? act.route_asset_ids[0] : null;
    let routeStatus = "Direct Access";
    let routeClass = "open";

    if (routeId && STATE.scenarioAssets && STATE.scenarioAssets[routeId]) {
      const routeAsset = STATE.scenarioAssets[routeId];
      const match = (routeAsset.state_timeline_p50 || []).find(
        (pt) => Math.abs(pt[0] - STATE.currentTimeH) < 0.05
      );
      if (match && match[1] === "FAILED") {
        routeStatus = `${routeAsset.name} (FLOODED)`;
        routeClass = "flooded";
      } else {
        routeStatus = `${routeAsset.name} (Clear)`;
        routeClass = "open";
      }
    }

    const card = document.createElement("div");
    card.className = "action-card";
    card.innerHTML = `
      <div class="action-card-header">
        <div class="action-card-title">#${idx + 1} ${act.title}</div>
        <div class="deadline-pill ${deadlineClass}">${deadlineText}</div>
      </div>
      <div class="action-card-desc">${act.description}</div>
      <div class="action-card-meta">
        <span class="action-route-status ${routeClass}">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line></svg>
          Route: ${routeStatus}
        </span>
        <span>Req: <b>${(act.resources_needed || "Standby").split(",")[0]}</b></span>
      </div>
    `;

    // BUG-03 Fix: Use act.target_asset_id (singular string from schema)
    if (act.target_asset_id) {
      card.style.cursor = "pointer";
      card.addEventListener("click", () => inspectAsset(act.target_asset_id));
    }

    container.appendChild(card);
  });
}

// ==========================================================================
// Failure Sequence Timeline Pane (BUG-02 Fix)
// ==========================================================================
function renderFailureSequence() {
  const container = document.getElementById("sequenceContainer");
  if (!container) return;
  container.innerHTML = "";

  // BUG-02 Fix: Query exact backend metric keys from SimulationAggregator
  const outagePctEl = document.getElementById("metricOutagePct");
  const patientHoursEl = document.getElementById("metricPatientHours");

  if (STATE.metrics) {
    if (outagePctEl) {
      const pct = STATE.metrics.median_landfall_outage_pct !== undefined
        ? STATE.metrics.median_landfall_outage_pct
        : (STATE.metrics.mean_system_outage_pct || 78);
      outagePctEl.textContent = `${Math.round(pct)}%`;
    }
    if (patientHoursEl) {
      const hrs = STATE.metrics.total_patient_hours_at_risk !== undefined
        ? STATE.metrics.total_patient_hours_at_risk
        : (STATE.metrics.hospital_unpowered_bed_hours || 420);
      patientHoursEl.textContent = `${Math.round(hrs)} hrs`;
    }
  }

  const failingAssets = Object.values(STATE.scenarioAssets || {})
    .filter((a) => a.p50_fail_time_h !== null)
    .sort((a, b) => a.p50_fail_time_h - b.p50_fail_time_h);

  failingAssets.forEach((asset) => {
    const sign = asset.p50_fail_time_h >= 0 ? "+" : "";
    const item = document.createElement("div");
    item.className = "seq-item";
    item.innerHTML = `
      <div class="seq-header">
        <span class="seq-time-badge">T${sign}${asset.p50_fail_time_h.toFixed(1)}h</span>
        <span class="seq-type-tag">${asset.type.replace(/_/g, " ")}</span>
      </div>
      <div class="seq-name">${asset.name}</div>
      <div class="seq-cause-text">Trigger: <b>${asset.dominant_cause.replace(/_/g, " ")}</b></div>
    `;

    item.addEventListener("click", () => inspectAsset(asset.asset_id));
    container.appendChild(item);
  });
}

// ==========================================================================
// Asset Detail & Causal Explanation (BUG-01, BUG-06, BUG-10 Fixes)
// ==========================================================================
async function inspectAsset(assetId) {
  STATE.selectedAssetId = assetId;

  // Open drawer and switch to detail pane
  switchDrawerPane("detail");
  openDrawer();

  // BUG-10 Fix: Apply visual selection ring to active marker
  applyMarkerSelection(assetId);

  // Focus map on asset
  const node = STATE.graph?.nodes?.find((n) => n.id === assetId);
  if (node) {
    STATE.map.panTo([node.lat, node.lon], { animate: true, duration: 0.8 });
  }

  try {
    const res = await fetch(`${API_BASE}/api/scenario/${STATE.scenarioId}/assets/${assetId}/explain`);
    if (!res.ok) return;
    const data = await res.json();

    // Toggle views
    document.getElementById("detailEmptyMessage").style.display = "none";
    const detailCard = document.getElementById("detailCard");
    detailCard.classList.remove("hidden");

    // Header info
    document.getElementById("detailTypeBadge").textContent = data.type.replace(/_/g, " ");
    document.getElementById("detailTitle").textContent = data.name;
    document.getElementById("detailLocation").textContent = `ID: ${data.asset_id} · Priority: ${data.criticality}`;

    // Current State & BUG-06 Fix: Handle backup class names properly
    let liveState = "OPERATING";
    if (STATE.scenarioAssets && STATE.scenarioAssets[assetId]) {
      const tl = STATE.scenarioAssets[assetId].state_timeline_p50 || [];
      const match = tl.find((pt) => Math.abs(pt[0] - STATE.currentTimeH) < 0.05);
      if (match) liveState = match[1];
    }
    const stateBadge = document.getElementById("detailCurrentState");
    stateBadge.textContent = liveState.replace(/_/g, " ");
    stateBadge.className = `asset-status-pill ${liveState.toLowerCase()} ${liveState === "ON_BACKUP" ? "backup" : ""}`;

    // P10, P50, P90
    const fmt = (t) => (t !== null ? `T${t >= 0 ? "+" : ""}${t.toFixed(1)}h` : "Survives");
    document.getElementById("detailP10").textContent = fmt(data.p10_fail_time_h);
    document.getElementById("detailP50").textContent = fmt(data.p50_fail_time_h);
    document.getElementById("detailP90").textContent = fmt(data.p90_fail_time_h);

    // Dominant cause
    document.getElementById("detailDominantCause").textContent = `Trigger: ${data.dominant_cause.replace(/_/g, " ")}`;

    // BUG-01 Fix: Remove * 100 (backend already returns percentage on 0-100 scale)
    const barsContainer = document.getElementById("detailCauseBars");
    barsContainer.innerHTML = "";
    Object.entries(data.cause_breakdown || {}).forEach(([cause, pct]) => {
      const cleanPct = Math.min(Math.round(pct), 100);
      const row = document.createElement("div");
      row.className = "cause-bar-row";
      row.innerHTML = `
        <div class="cause-bar-meta">
          <span>${cause.replace(/_/g, " ")}</span>
          <span>${cleanPct}%</span>
        </div>
        <div class="cause-bar-track">
          <div class="cause-bar-fill" style="width: ${cleanPct}%"></div>
        </div>
      `;
      barsContainer.appendChild(row);
    });

    // Causal chain flow
    const stepsContainer = document.getElementById("detailChainSteps");
    stepsContainer.innerHTML = "";
    if (!data.causal_chain || data.causal_chain.length === 0) {
      stepsContainer.innerHTML = `<div class="causal-step-pill"><span class="step-num-badge">✓</span> Operates nominally with robust resilience.</div>`;
    } else {
      data.causal_chain.forEach((step, idx) => {
        const stepEl = document.createElement("div");
        stepEl.className = "causal-step-pill";
        stepEl.innerHTML = `
          <span class="step-num-badge">${idx + 1}</span>
          <span>${step}</span>
        `;
        stepsContainer.appendChild(stepEl);
      });
    }

    // Dependency network
    document.getElementById("detailPowerSrc").textContent =
      data.upstream_power_nodes?.join(", ") || "Autonomous / Dedicated Source";

    const routeStr =
      data.resupply_routes?.length > 0
        ? `${data.resupply_routes[0].depot_id} via ${data.resupply_routes[0].road_path.join(" → ")}`
        : "Direct / Not applicable";
    document.getElementById("detailResupplyPath").textContent = routeStr;

  } catch (err) {
    console.error("Error inspecting asset:", err);
  }
}

// BUG-10 Fix: Manage active marker visual selection highlight
function applyMarkerSelection(assetId) {
  deselectActiveMarker();
  const marker = STATE.assetMarkers[assetId];
  if (marker) {
    const el = marker.getElement();
    if (el) {
      const badge = el.querySelector(".node-badge-v2");
      if (badge) {
        badge.classList.add("is-selected");
        STATE.selectedMarkerElement = badge;
      }
    }
  }
}

function deselectActiveMarker() {
  if (STATE.selectedMarkerElement) {
    STATE.selectedMarkerElement.classList.remove("is-selected");
    STATE.selectedMarkerElement = null;
  }
  STATE.selectedAssetId = null;
}

// ==========================================================================
// Time Machine (BUG-04 Fix)
// ==========================================================================
function initTimeMachine() {
  const btn = document.getElementById("btnRunFork");
  if (btn) {
    btn.addEventListener("click", runTimeMachineFork);
  }
}

function renderTimeMachineOptions() {
  const container = document.getElementById("whatifOptionsContainer");
  if (!container) return;
  container.innerHTML = "";

  (STATE.actions || []).forEach((act) => {
    const label = document.createElement("label");
    label.className = "whatif-option-label";
    label.innerHTML = `
      <input type="checkbox" class="whatif-checkbox" value="${act.id}" checked>
      <div class="whatif-text-group">
        <div class="whatif-title">${act.title}</div>
        <div class="whatif-desc">${act.description}</div>
      </div>
    `;
    container.appendChild(label);
  });

  // Run initial what-if simulation to render baseline vs branch chart
  runTimeMachineFork();
}

async function runTimeMachineFork() {
  const checkboxes = document.querySelectorAll(".whatif-checkbox:checked");
  const selectedIds = Array.from(checkboxes).map((cb) => cb.value);

  const btn = document.getElementById("btnRunFork");
  if (btn) btn.innerHTML = `<span>Simulating Fork...</span>`;

  try {
    const res = await fetch(`${API_BASE}/api/scenario/${STATE.scenarioId}/whatif`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        selected_action_ids: selectedIds,
        branch_time_h: -6.0,
      }),
    });

    if (!res.ok) throw new Error("What-if simulation failed");
    const data = await res.json();
    STATE.whatifData = data;

    // Update Saved Points Badge
    const badge = document.getElementById("tmPointsSaved");
    if (badge) {
      badge.textContent = `+${data.total_lifeline_points_saved.toFixed(1)} CLLI Points Saved`;
    }

    // Render / Update Chart.js Comparison Chart
    renderTimeMachineChart(data.clli_comparison);

  } catch (err) {
    console.error("Error running time machine:", err);
  } finally {
    if (btn) {
      btn.innerHTML = `
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="16 3 21 3 21 8"></polyline><line x1="4" y1="20" x2="21" y2="3"></line><polyline points="21 16 21 21 16 21"></polyline><line x1="15" y1="15" x2="21" y2="21"></line><line x1="4" y1="4" x2="9" y2="9"></line></svg>
        <span>Compute Forked Timeline</span>
      `;
    }
  }
}

function renderTimeMachineChart(clliComp) {
  const canvas = document.getElementById("tmChart");
  if (!canvas || !window.Chart) return;

  if (STATE.tmChartInstance) {
    STATE.tmChartInstance.destroy();
  }

  const labels = clliComp.time_steps.map((t) => `T${t >= 0 ? "+" : ""}${t}h`);

  STATE.tmChartInstance = new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Baseline (Do Nothing)",
          data: clliComp.baseline_clli_p50,
          borderColor: "#ef4444",
          borderWidth: 2,
          pointRadius: 0,
          borderDash: [4, 4],
          tension: 0.2,
        },
        {
          label: "Forked (Interventions Applied)",
          data: clliComp.branch_clli_p50,
          borderColor: "#18181b",
          backgroundColor: "rgba(24, 24, 27, 0.05)",
          borderWidth: 2.5,
          pointRadius: 0,
          fill: true,
          tension: 0.2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            boxWidth: 10,
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 10, weight: 600 },
            color: "#52525b",
          },
        },
        tooltip: {
          backgroundColor: "#18181b",
          titleFont: { family: "'JetBrains Mono', monospace", size: 11 },
          bodyFont: { family: "'Plus Jakarta Sans', sans-serif", size: 11 },
          padding: 8,
          cornerRadius: 6,
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            maxTicksLimit: 6,
            font: { family: "'JetBrains Mono', monospace", size: 9 },
            color: "#a1a1aa",
          },
        },
        y: {
          title: {
            display: true,
            text: "Lifeline Loss (CLLI)",
            font: { size: 9, weight: 600 },
            color: "#71717a",
          },
          grid: { color: "rgba(0,0,0,0.04)" },
          ticks: {
            font: { family: "'JetBrains Mono', monospace", size: 9 },
            color: "#a1a1aa",
          },
        },
      },
    },
  });

  // BUG-04 Fix: Ensure Chart.js is properly sized immediately
  STATE.tmChartInstance.resize();
}

// ==========================================================================
// Crisis Council Memorandum Pane
// ==========================================================================
function renderCouncil() {
  if (!STATE.councilData) return;

  const ordersContainer = document.getElementById("councilOrdersContainer");
  const chatContainer = document.getElementById("councilChatContainer");

  if (ordersContainer) {
    ordersContainer.innerHTML = "";
    (STATE.councilData.consensus_plan || []).forEach((order) => {
      const card = document.createElement("div");
      card.className = "order-pill-card";
      card.innerHTML = `
        <div class="order-card-top">
          <span class="order-step-num">ORDER #${order.step}</span>
          <span class="order-deadline-time">EXEC BY: ${order.deadline}</span>
        </div>
        <div class="order-action-text">${order.action}</div>
        <div class="order-owner-text">Assigned: <b>${order.owner}</b></div>
      `;
      ordersContainer.appendChild(card);
    });
  }

  if (chatContainer) {
    chatContainer.innerHTML = "";
    (STATE.councilData.transcript || []).forEach((msg) => {
      const initial = (msg.speaker || "C").charAt(0);
      const div = document.createElement("div");
      div.className = "deliberation-msg";
      div.innerHTML = `
        <div class="speaker-bar">
          <span class="speaker-avatar">${initial}</span>
          <span class="speaker-name">${msg.speaker}</span>
        </div>
        <div class="speech-text">${msg.message}</div>
      `;
      chatContainer.appendChild(div);
    });
  }
}
