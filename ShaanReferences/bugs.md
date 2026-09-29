# Known Bugs & Issues Tracker — Failure Clock

This document tracks all known bugs, edge cases, visual quirks, and technical debt across the frontend and backend of **Failure Clock**. Each item includes the exact file location, impact level, and proposed fix.

---

## 1. High Priority Bugs

### BUG-01: Chart.js Canvas Zero-Dimension Render Bug
- **Location:** [`web/app.js`](file:///Users/shaanm/Projects/FailureClock/web/app.js) (`renderTimeMachineChart`) / [`web/index.html`](file:///Users/shaanm/Projects/FailureClock/web/index.html) (`#tmChart`)
- **Severity:** High
- **Description:**  
  When `loadScenario()` runs on initial page load, it automatically calls `renderTimeMachineOptions()` and `runTimeMachineFork()`. At this time, the parent container `#paneTimemachine` is styled with `display: none` because the default active pane is `paneActions`. Chart.js computes the canvas width and height as `0px × 0px`. When the user later clicks the "Time Machine" button in the top navigation, the chart may render squished or invisible until the browser window is manually resized.
- **Proposed Fix:**  
  1. Defer chart initialization until `#paneTimemachine` becomes visible.
  2. Inside `switchDrawerPane("timemachine")`, explicitly call `STATE.tmChartInstance.resize()` or re-trigger `runTimeMachineFork()`.

---

### BUG-02: Storm Eye Marker Track Interpolation Discrepancy
- **Location:** [`web/app.js`](file:///Users/shaanm/Projects/FailureClock/web/app.js#L273-L277) (`updateStateAtTime`)
- **Severity:** Medium-High
- **Description:**  
  The storm center position on the map is currently calculated using a simple linear approximation:
  ```javascript
  const stormLat = 19.78 + timeH * 0.052;
  const stormLon = 85.80 + timeH * 0.048;
  ```
  However, each scenario in `data/seed_data.py` (e.g. Cyclone Fani vs Severe Cyclone Live vs Red Team Storm) has its own distinct curved trajectory. As a result, the storm eye icon on the map does not follow the true scenario trajectory defined in the backend.
- **Proposed Fix:**  
  1. Return the scenario's `track` array in `GET /api/scenario/{scenario_id}/assets` or a dedicated endpoint.
  2. In `app.js`, linearly interpolate latitude and longitude between the two bounding track points `(t1, t2)` for the given `currentTimeH`.

---

## 2. Medium Priority Bugs & Edge Cases

### BUG-03: Missing Visual Selection Aura for Clicked Map Marker
- **Location:** [`web/app.js`](file:///Users/shaanm/Projects/FailureClock/web/app.js) (`inspectAsset`) & [`web/style.css`](file:///Users/shaanm/Projects/FailureClock/web/style.css)
- **Severity:** Medium
- **Description:**  
  When a user clicks an infrastructure marker (e.g. DHH Puri) or road polyline on the map, the camera pans to the location and the slide-over drawer opens. However, the clicked marker has no distinct "selected" visual state (like a highlighted halo, white outline, or animated ring). If there are multiple adjacent nodes, the user cannot easily tell which one is currently active.
- **Proposed Fix:**  
  Add an `.is-selected` CSS class to the active marker DOM element that applies a high-contrast double-ring pulse (`box-shadow: 0 0 0 4px #09090b`).

---

### BUG-04: Time Slider Range Mismatch with Early Warning Scenarios
- **Location:** [`web/index.html`](file:///Users/shaanm/Projects/FailureClock/web/index.html#L84) (`#timeSlider`)
- **Severity:** Medium
- **Description:**  
  The timeline slider HTML element is hardcoded to `min="-24" max="36"`:
  ```html
  <input type="range" id="timeSlider" min="-24" max="36" step="1" value="-12">
  ```
  However, the `severe_cyclone_live` scenario track begins at `T-36.0h` (36 hours before landfall). The user cannot scrub back to inspect the earliest warning phase between T-36h and T-24h.
- **Proposed Fix:**  
  Dynamically set `slider.min` and `slider.max` based on `time_steps[0]` and `time_steps[n-1]` returned by the scenario API.

---

### BUG-05: Missing "Back to List" Button in Asset Detail Drawer
- **Location:** [`web/index.html`](file:///Users/shaanm/Projects/FailureClock/web/index.html#L177) (`#paneDetail`)
- **Severity:** Medium
- **Description:**  
  When clicking a marker on the map, the drawer switches to `#paneDetail`. If the user wants to return to the **Action Deadlines** or **Failure Sequence** list, they have to click the top segmented buttons. If they don't notice the top buttons, they feel "trapped" in the asset detail screen.
- **Proposed Fix:**  
  Add a clean "← Back to Deadlines" link at the top of `#paneDetail`.

---

## 3. Low Priority & Technical Debt

### BUG-06: Starlette Deprecation Warning on Test Suite
- **Location:** [`tests/test_api.py`](file:///Users/shaanm/Projects/FailureClock/tests/test_api.py)
- **Severity:** Low
- **Description:**  
  Running `pytest` triggers the following warning:
  ```
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  ```
- **Proposed Fix:**  
  Ensure pytest configuration ignores this external Starlette deprecation warning, or update dependencies when Starlette updates its official test client interface.

---

### BUG-07: Road Polyline Visibility on Flooded State
- **Location:** [`web/style.css`](file:///Users/shaanm/Projects/FailureClock/web/style.css) & [`web/app.js`](file:///Users/shaanm/Projects/FailureClock/web/app.js)
- **Severity:** Low
- **Description:**  
  When a road fails (floods), its polyline style changes to:
  ```javascript
  poly.setStyle({ color: "#a1a1aa", dashArray: "4, 6", weight: 2.5, opacity: 0.6 });
  ```
  On certain high-contrast display monitors, this light gray dashed line can partially blend into the grayscale background map tiles, making it hard to see where the flooded road cuts off.
- **Proposed Fix:**  
  Use a distinct pattern such as `#ef4444` (subtle red dash) or a darker dashed black line `#52525b` with a noticeable gap and red alert symbol.

---

### BUG-08: Drawer Outside-Click Dismissal
- **Location:** [`web/app.js`](file:///Users/shaanm/Projects/FailureClock/web/app.js)
- **Severity:** Low
- **Description:**  
  Clicking on the map background does not automatically collapse the slide-over drawer. The user must manually click the `×` button or the top toggle icon to dismiss the panel.
- **Proposed Fix:**  
  Add a Leaflet map click listener that collapses the drawer if `STATE.isDrawerOpen === true` and the click target was not a marker or control element.
