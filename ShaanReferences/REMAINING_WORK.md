# Remaining Work & Future Roadmap — Failure Clock

This document outlines the next stages of development, architectural extensions, and operational enhancements planned for **Failure Clock**.

---

## 1. Live Weather & IMD Feed Ingestion
- **Automated Real-Time RSS / API Ingestion**:
  - Connect directly to the India Meteorological Department (IMD) Tropical Cyclone Bulletins API / RSMC New Delhi bulletin feeds.
  - Automatically parse official IMD forecast track coordinates, estimated central pressure, and radii of maximum winds.
- **Ensemble Track Cone Visualization**:
  - Render IMD probability cones of uncertainty on the map canvas as transparent contour polygons.

---

## 2. Multi-District Scaling & Regional Graph Expansion
- **Beyond Puri District**:
  - Expand the infrastructure graph to neighboring coastal districts: **Khordha** (Bhubaneswar state capital), **Ganjam** (Berhampur), **Kendrapara**, and **Jagatsinghpur** (Paradip Port).
  - Model inter-district high-voltage transmission lines (400kV / 220kV OPTCL grid corridors) and inter-district diesel tanker logistics.
- **OpenStreetMap Automated Ingestion Script**:
  - Create an automated parser (`data/osm_ingest.py`) using Overpass API to query hospitals, power substations, cell towers, and highway networks directly from OpenStreetMap data.

---

## 3. Printable Situation Room Memorandum (PDF Export)
- **1-Click Executive PDF Brief**:
  - Add an "Export Situation Report" button in the top navigation island.
  - Generates a formatted single-page PDF containing:
    - Official District Collectorate header with timestamp and storm classification.
    - Top 3 urgent interventions with execution deadlines and assigned agencies.
    - High-risk hospital outage predictions.
    - Road corridor closure timetable.

---

## 4. Real-Time Collaboration & WebSockets
- **Live Multi-User Situation Room**:
  - Integrate FastAPI WebSockets (`/ws/situation-room`) so multiple departmental officers (Police, PWD, Health, DISCOM) can view the same interactive timeline simultaneously.
  - Live cursor and action acknowledgment sync across connected terminals.

---

## 5. Offline Field PWA & Mobile Touch Optimization
- **Offline Progressive Web App (PWA)**:
  - Cache map tiles and the latest simulation state in IndexedDB / Service Workers so incident commanders can access the Failure Clock even after cellular towers go dark during landfall.
- **Mobile Touch Controls**:
  - Fine-tune scrubber slider touch targets and swipe gestures to dismiss the slide-over drawer on iOS Safari and Android Chrome.

---

## 6. Dockerization & Production Deployment
- **Containerization**:
  - Add `Dockerfile` and `docker-compose.yml` for 1-command deployment.
  - Production-ready Gunicorn/Uvicorn configuration with Nginx reverse proxy.
