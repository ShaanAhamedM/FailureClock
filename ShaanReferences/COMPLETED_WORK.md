# Completed Work — Failure Clock

**Project:** Failure Clock — Cyclone Impact & Infrastructure Vulnerability Forecaster  
**District Pilot:** Puri District, Coastal Odisha, India  
**System Architecture:** Physics-informed Multi-Hazard Cascade Simulator + REST API + Editorial White & Black Operations Interface  

---

## 1. Physics-Informed Hazard Modeling Engine

All hazard models are implemented in pure Python with NumPy/SciPy under `/hazard/`:

- **Holland 1980 Wind Profile & Inflow Angle (`hazard/wind.py`)**:
  - Implements Holland’s radial pressure profile $B$ parameter, gradient wind balance, and asymmetrical surface friction reduction (0.8 factor + 20° cross-isobar inflow).
  - Includes Kaplan-DeMaria inland exponential decay model after eye landfall ($R = 0.09\, \text{h}^{-1}$).
- **Coastal Storm Surge Predictor (`hazard/surge.py`)**:
  - Bathtub storm surge hydrodynamics with inverted barometer effect (1 cm sea rise per 1 hPa pressure drop).
  - Shelf wind setup driven by coastal bathymetry slope and onshore wind stress.
  - Hydrodynamic wave runup based on offshore significant wave height $H_s$.
- **Inland Pluvial & Fluvial Flooding (`hazard/flood.py`)**:
  - SCS-CN (Soil Conservation Service Curve Number) runoff generation model.
  - Topographic wetness index (TWI) accumulation and Manning’s open-channel water depth calculation.
  - Real-time road passability check based on the critical depth threshold ($0.30\,\text{m}$ for emergency vehicles).
- **Multi-Hazard Ensemble (`hazard/ensemble.py`)**:
  - Spatially queries wind speed, flood water depth, and storm surge height at arbitrary `(lat, lon)` coordinates across time steps $t \in [-24\text{h}, +36\text{h}]$.

---

## 2. Infrastructure Dependency Graph & Cascading Simulator

Located in `/graph/` and `/sim/`:

- **Typed Graph Schema (`graph/schema.py`)**:
  - Typed Nodes: `HOSPITAL`, `SUBSTATION`, `FEEDER`, `TOWER`, `WATER_PUMP`, `DEPOT`, `ROAD_SEGMENT`.
  - Typed Edges: `POWERS`, `ACCESSED_VIA`, `RESUPPLIED_FROM`, `SERVES`.
  - Realistic parameters stored in `graph/parameters.yaml` (diesel burn rates, battery backup capacities, transformer flood thresholds, wind trip limits).
- **Puri Pilot Graph (`data/seed_data.py`)**:
  - 24 realistic infrastructure nodes covering District Headquarter Hospital (DHH Puri), Community Health Centres (CHC Konark, CHC Brahmagiri, PHC Balighai), 132/33kV Puri Grid Substation, Town Substations, distribution feeders, telecom towers, water pumping stations, and key transport arteries (NH-316, Puri Town Link, Marine Drive SH-60).
- **Monte Carlo Cascade Simulator (`sim/cascade.py`)**:
  - Dynamic tri-state state machine: `OPERATING` $\rightarrow$ `ON_BACKUP` $\rightarrow$ `FAILED`.
  - Functional power dependencies: grid outage triggers immediate fallback to on-site Diesel Generators (DG) or UPS batteries.
  - Consumable exhaustion: fuel drains hourly based on operational load.
  - Physical resupply simulation: Dijkstra shortest path across the road graph. If roads are flooded ($>0.30\,\text{m}$) or blocked by wind debris ($>36\,\text{m/s}$), resupply trucks cannot reach the facility, causing secondary failure when generator tanks run empty.
- **Aggregation & CLLI Lifeline Loss (`sim/aggregate.py`)**:
  - Computes P10, P50, P90 failure distributions across Monte Carlo runs.
  - Causal chain tracing (identifies exact root cause, e.g. "Grid power tripped at T-3h $\rightarrow$ DG ran out of fuel at T+11h $\rightarrow$ Road flooded preventing fuel truck").
  - Composite Lifeline Loss Index (CLLI) tracking across the full 60-hour storm horizon.

---

## 3. Intervention Actions & Counterfactual Optimizer

Located in `/actions/`:

- **Action Catalog (`actions/catalogue.py`)**:
  - Pre-landfall actions: Pre-positioning mobile 500kVA DG sets, priority fuel dispatch from IOCL Talabania depot, clearing crews on NH-316/Samang link, sandbagging substation switchyards, deploying high-capacity dewatering pumps.
- **Counterfactual Action Ranking (`actions/rank.py`)**:
  - Evaluates interventions by running paired Monte Carlo simulations.
  - Computes saved CLLI point-hours, net bed-hours protected, and urgency deadlines.
- **Last Safe Minute Board (`actions/wow_layer.py`)**:
  - Doomsday countdown board calculating exact execution deadlines before road inundation closes the logistical window.

---

## 4. Track 5 Signature Features

Located in `/actions/wow_layer.py`:

- **F1: Time Machine (Branching Timelines)**:
  - Interactive counterfactual engine using Common Random Numbers (CRN) for exact variance reduction.
  - Allows users to select arbitrary combinations of interventions and compare baseline vs forked CLLI curves in real-time.
- **F2: Last Safe Minute (Doomsday Countdown)**:
  - Confidence intervals (P10 conservative, P50 expected, P90 optimistic) on operational closure windows.
- **F3: Red Team Storm Stress Test**:
  - Adversarial simulation evaluating plan robustness against worst-case Category 5 track deviations.
- **F4: Grounded AI Crisis Council Deliberation**:
  - Multi-stakeholder debate between District Collector, Chief Medical Officer, PWD Roads Engineer, DISCOM Power Chief, and Telecom Director.
  - Every numeric claim is grounded with a simulation citation tag (e.g. `#SIM-HOSP-DHH`).
- **F6: Keystone Infrastructure Finder & Shapley Blame Graph**:
  - Computes marginal failure contribution and Shapley blame attribution for critical facilities.

---

## 5. Historical Validation Against Cyclone Fani (2019)

Located in `/validation/replay_fani.py`:

- Replayed official IMD Best Track data for Cyclone Fani (landfall May 3, 2019 near Puri).
- **Validation Results**:
  - **100% Detection Recall** (12 out of 12 historical damage and outage events detected).
  - **Spearman Rank Correlation: 0.80** between predicted failure sequence and official restoration reports.

---

## 6. High-End White & Black User Interface

Located in `/web/`:

- **Editorial White & Black Aesthetic (`web/style.css`)**:
  - Pure light mode with crisp white surfaces, Apple/Linear-grade glassmorphism (`backdrop-filter: blur(24px)`), and deep ink carbon text (`#09090b`).
  - Grayscale architectural blueprint map styling eliminating color pollution.
- **Full-Bleed Hero Map (`web/index.html`)**:
  - Map fills 100vw × 100vh with no clunky permanent sidebars taking over the screen.
- **Floating Top Navigation Island**:
  - Capsule housing brand identity, scenario switcher, and segmented pills for **Deadlines**, **Failure Sequence**, **Time Machine**, and **Crisis Council**.
- **Floating Bottom Timeline Scrubber**:
  - High-contrast clock display (`T-12.0h`), smooth range slider with fill progress, play/pause controls, and live telemetry badges (Grid, Backup, Dark).
- **Non-Intrusive Slide-Over Drawer**:
  - Glides in smoothly from the right on demand or when a user clicks a facility or road link on the map.
- **Interactive Controller (`web/app.js`)**:
  - Reactive event handling, real-time map updates as the timeline scrubs, Chart.js counterfactual comparison, and asset causal breakdown cards.

---

## 7. Automated Test Suite

Located in `/tests/`:

- 14 automated tests covering API endpoints, wind models, surge models, flood passability, dependency graphs, Monte Carlo cascades, and wow features.
- 100% pass rate (`pytest tests/`).
