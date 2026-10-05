# Adaptive Carbon-Aware Workload Scheduling

> **Faculty Demo Prototype** — Academic PBL project, Semester 5

---

## Purpose

A working prototype that demonstrates how a VM workload scheduler can reduce
carbon emissions by predicting near-future CPU demand with a trained GRU model
and deciding whether to **run a job now** or **delay it** based on the current
grid carbon intensity fetched from the Electricity Maps API.

This is a **faculty-facing demo**, not a production system.  
The goal is to make carbon-aware scheduling decisions tangible and inspectable
through a simple React dashboard.

---

## Locked Architecture

```
Bitbrains VM 846 CPU history
        │
        ▼
  Existing trained GRU          ← models/saved/gru_model.pt
        │                           data/processed/scaler.pkl
        ▼
  Next-5-minute CPU prediction
        │
        ▼
  Electricity Maps carbon intensity  ← legacy_carbon/api_client.py
        │
        ▼
  Deadline-aware scheduling decision
  (RUN NOW  vs  DELAY)
        │
        ▼
  Estimated CO₂ comparison
        │
        ▼
  React dashboard
```

**Do NOT extend with:** Prophet, Contextual Bandits, Reinforcement Learning,
Gurobi, ILP, Kubernetes, C++, complex optimisation, or additional ML models.

---

## Existing Artifacts Being Reused

| Artifact | Path | Role |
|----------|------|------|
| GRU checkpoint | `models/saved/gru_model.pt` | Pre-trained workload predictor |
| MinMaxScaler | `data/processed/scaler.pkl` | CPU-% normalisation (feature range 0–1, data range 7.87–58.93 %) |
| Workload data | `data/workload/846.csv` | Bitbrains VM 846 — 8 635 rows, 5-minute intervals, semicolon-delimited |
| Carbon client | `legacy_carbon/api_client.py` | Validated Electricity Maps v3 API wrapper |
| GRU definition | `legacy_model/gru_model.py` | `GRUWorkloadPredictor` class (input_dim=1, hidden_dim=64, num_layers=1) |

---

## Project Layout

```
.
├── backend/                 # FastAPI application (to be implemented)
│   ├── api/                 # Route handlers / endpoints
│   ├── services/            # Prediction, scheduling, carbon logic
│   └── tests/               # Pytest unit tests
│
├── frontend/                # React + Vite dashboard (to be implemented)
│
├── scripts/                 # One-off utility / verification scripts
│
├── data/
│   ├── workload/846.csv     # Raw Bitbrains VM trace
│   └── processed/scaler.pkl # Fitted MinMaxScaler
│
├── models/
│   └── saved/gru_model.pt   # Trained GRU state dict
│
├── legacy_model/
│   └── gru_model.py         # GRUWorkloadPredictor definition (do not modify)
│
└── legacy_carbon/
    └── api_client.py        # Electricity Maps client (do not modify)
```

---

## Key Technical Notes

- **CSV separator**: The workload file uses **semicolon (`;`)** as delimiter.  
  Parse with `pd.read_csv("data/workload/846.csv", sep=";")` and strip whitespace from column names.
- **Target column**: `CPU usage [%]` (values roughly 8 – 59 %).
- **Scaler**: `sklearn.preprocessing.MinMaxScaler`, fitted on `CPU usage [%]`.
  `data_min_=7.87`, `data_max_=58.93`, `feature_range=(0, 1)`.
- **GRU checkpoint**: plain `state_dict` (`collections.OrderedDict`), 12 929 parameters.  
  Load with `model.load_state_dict(torch.load(..., map_location="cpu"))`.
- **Carbon API**: requires `ELECTRICITY_MAPS_API_KEY` environment variable.

---

## Status

- [x] Existing artifacts inspected and verified readable  
- [ ] Backend (FastAPI) — Prompt 2  
- [ ] Prediction service — Prompt 2  
- [ ] Scheduler logic — Prompt 3  
- [ ] React dashboard — Prompt 4  
