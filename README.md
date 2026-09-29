# Failure Clock ⏳
### Cyclone Impact & Infrastructure Vulnerability Forecaster (Track 5)

> *"Weather forecasts tell you the storm is coming. Failure Clock tells you which lifeline breaks first, and when to act to stop it."*

Failure Clock is a decision-support and cascade simulation system for district-level cyclone response. Instead of stopping at weather hazard heatmaps, it forecasts **which critical lifelines (power, telecom, hospitals, water pumping, road corridors) break, in what order, and with what uncertainty ($P_{10}/P_{50}/P_{90}$)**. It then translates those timelines into a **ranked list of pre-landfall interventions with route-dependent departure deadlines ("Last Safe Minute")**.

---

## 🌟 Signature Features ("Wow Layer")

1. **🗺️ Interactive Cascade Command Map:**
   - Real-time Leaflet map of Puri District, Odisha infrastructure (Substations, Feeders, Hospitals, Towers, Water Works, Depots, Lifeline Road Corridors).
   - Dynamic time scrub slider from $T-24h$ to $T+36h$ with animated storm eye and changing asset failure states.
   - Comprehensive asset deep-dive drawer with $P_{10}/P_{50}/P_{90}$ distributions, cause breakdown bars, and step-by-step causal chain audits.

2. **⏳ Last Safe Minute (Doomsday Board - F2):**
   - Live countdown clocks showing the latest feasible departure time for every emergency dispatch (fuel bowsers, mobile generators) before the transit road corridor is cut off by flood water ($\ge 0.3m$) or fallen tree debris.

3. **🔀 Time Machine (Branching Timelines - F1):**
   - Drag or toggle pre-landfall interventions onto the timeline to fork an alternative future.
   - Uses **Common Random Numbers (CRN)** so differences in outcomes are strictly due to the intervention, comparing baseline vs branched Critical Lifeline Loss Index (CLLI).

4. **💎 Keystone Finder & Shapley Blame Graph (F6):**
   - Automatically discovers high-leverage keystone assets whose protection averts massive downstream cascades.
   - Applies game-theoretic **Shapley value decomposition** to attribute responsibility for hospital outages across upstream triggers (grid trip, road cut, fuel capacity, telecom loss).

5. **🏛️ Grounded AI Crisis Council (F4):**
   - Multi-stakeholder deliberation between role-playing AI agents: District Collector (Chair), Chief Medical Officer (Health), Power Utility DISCOM Engineer, Telecom NOC Director, and PWD Roads Engineer.
   - Every numeric claim is tagged and verified against simulation call IDs (`#SIM-...`).
   - Produces a signed, coordinated multi-agency consensus action plan.

6. **🔴 Red Team Storm (Adversarial Stress Test - F3):**
   - Adversarially stress-tests your disaster plan against worst-case plausible cyclone tracks and speeds, computing a **Plan Robustness Score**.

---

## 🔬 Core Engine Architecture

```
failure-clock/
  ├── api/              # FastAPI REST server & static file host (main.py)
  ├── graph/            # Schema, NetworkX dependency manager, parameters.yaml
  ├── hazard/           # Holland (1980) wind model, surge inundation, pluvial flood, track ensembles
  ├── sim/              # Monte Carlo cascade simulator, resupply routing, aggregation
  ├── actions/          # Candidate catalogue, CRN action ranker, Part II Wow Layer
  ├── data/             # Pilot district seed data (Puri, Odisha) & Cyclone Fani tracks
  ├── web/              # Web dashboard UI (Leaflet, Chart.js, Mission Control dark theme)
  ├── validation/       # Cyclone Fani (2019) ground truth comparison & evaluation script
  └── tests/            # Automated test suite (core engine & REST API endpoints)
```

---

## 🚀 Quickstart & Setup

### 1. Requirements
- Python 3.11+
- Virtual environment (`.venv`)

### 2. Installation
```bash
# Clone repository
cd FailureClock

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (already satisfied in .venv)
pip install -r requirements.txt
```

### 3. Run Test Suite
```bash
PYTHONPATH=. .venv/bin/pytest -v
```

### 4. Launch the Web Dashboard & API
```bash
PYTHONPATH=. .venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000/`**

---

## 📊 Historical Replay Validation (Cyclone Fani 2019)

We validated Failure Clock against curated post-disaster ground truth from the Odisha State Disaster Management Authority (OSDMA), OPTCL, and NDMA for Extremely Severe Cyclone Fani (May 3, 2019):

```bash
PYTHONPATH=. .venv/bin/python3 validation/replay_fani.py
```

### Results:
- **Failure Detection Recall:** **100.0%** (9 of 9 documented failures correctly detected with $P(\text{fail}) > 0.5$)
- **Spearman Sequence Correlation:** **0.80** (Target > 0.70; correctly predicts early road and grid collapse prior to hospital battery exhaustion)
- **CLLI Reduction with Top 3 Actions:** **142.5 point-hours** saved.

---

## 📜 Transparent Engineering Assumptions
In accordance with ethical guidelines and Section 8.4:
- All parameter defaults (generator fuel burn rates, battery hours, road passability depths, wind fragility medians) are explicitly catalogued in `graph/parameters.yaml` and visible in the **Parameters & Fragility** dashboard tab.
