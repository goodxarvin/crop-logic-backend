# Requested Endpoint Usage Audit

This file is the backend-facing API status matrix reconciled against current code.

Status vocabulary:

- `implemented`
- `partially_implemented`
- `stub/contract-only`
- `deprecated`
- `missing`

## Endpoint Matrix

| Endpoint | Backend route | AI route | Status | Notes |
|---|---|---|---:|---|
| `POST /api/weather/farm-card/` | yes | yes | `implemented` | Current backend public weather card route. |
| `POST /api/economy/overview/` | yes | yes | `implemented` | End-to-end route is live. |
| `GET /api/irrigation/` | yes | yes | `implemented` | Method list route is live. |
| `POST /api/irrigation/recommend/` | yes | yes | `implemented` | Recommendation route is live. |
| `POST /api/irrigation/water-stress/` | yes | yes | `implemented` | Backend route proxies to AI-backed water stress flow. |
| `POST /api/fertilization/recommend/` | yes | yes | `implemented` | Live route. |
| `POST /api/pest-disease/detect/` | yes | yes | `implemented` | Canonical current public alias. |
| `POST /api/pest-disease/risk/` | yes | yes | `implemented` | Canonical current public alias. |
| `POST /api/pest-disease/risk-summary/` | yes | no separate AI route | `implemented` | Backend route derives risk summary from the same AI risk integration. |
| `POST /api/farm-alerts/tracker/` | yes | yes | `partially_implemented` | Backend serves snapshot-backed tracker response; not a direct request-time AI invocation. |
| `POST /api/farm-alerts/timeline/` | no | no | `missing` | Was documented, but no route exists. |
| `POST /api/soil/summary/` | yes | n/a | `implemented` | Backend public summary route. |
| `POST /api/soil/anomalies/` | yes | via `POST /api/soile/anomaly-detection/` | `implemented` | Backend canonical route. |
| `POST /api/soil/moisture-heatmap/` | yes | via `POST /api/soile/moisture-heatmap/` | `implemented` | Backend canonical route. |
| `POST /api/crop-health/ndvi-health/` | yes | via `POST /api/soil-data/ndvi-health/` | `implemented` | Backend canonical route. |
| `POST /api/yield-harvest/current-farm-chart/` | yes | via `/api/crop-simulation/current-farm-chart/` | `implemented` | Backend canonical route. |
| `POST /api/yield-harvest/harvest-prediction/` | yes | via `/api/crop-simulation/harvest-prediction/` | `implemented` | Backend canonical route. |
| `POST /api/yield-harvest/yield-prediction/` | yes | via `/api/crop-simulation/yield-prediction/` | `implemented` | Backend canonical route. |
| `POST /api/yield-harvest/growth/` | yes | via `/api/crop-simulation/growth/` | `implemented` | Backend canonical route. |
| `GET /api/yield-harvest/growth/{task_id}/status/` | yes | via `/api/crop-simulation/growth/{task_id}/status/` | `implemented` | Backend canonical route. |
| `GET /api/yield-harvest/summary/` | yes | no | `implemented` | Summary route exists. |
| `GET /api/yield-harvest/yield-harvest-summary/` | yes | via AI summary service | `implemented` | Compatibility alias remains live. |

## Internal AI Contracts Not To Present As Backend Public APIs

| Endpoint | Status | Notes |
|---|---:|---|
| `POST /api/rag/chat/` | `implemented` | AI service route only. |
| `GET|POST /api/soil-data/` | `implemented` | AI service route only. |
| `GET /api/soil-data/tasks/{task_id}/status/` | `implemented` | AI service route only. |
| `POST /api/soile/*` | `implemented` | AI service routes; backend public aliases are under `soil/*`. |
| `POST /api/farm-data/` | `implemented` | AI service route used for integration and sync. |
| `GET /api/farm-data/{farm_uuid}/detail/` | `implemented` | AI service route. |
| `POST /api/farm-data/parameters/` | `implemented` | AI service route. |
| `POST /api/weather/water-need-prediction/` | `implemented` | AI service route; backend public contract is under `water/*`. |
| `POST /api/crop-simulation/*` | `implemented` | AI service routes; backend public contract is under `yield-harvest/*`. |

## Contract-Only / Stale Spec Entries

| Endpoint | Status | Notes |
|---|---:|---|
| `GET /api/irrigation/recommend/{task_id}/status/` | `stub/contract-only` | Present in mock spec, no real route registration found. |
| `GET /api/fertilization/recommend/{task_id}/status/` | `stub/contract-only` | Present in mock spec, no real route registration found. |
| `PUT|PATCH|DELETE /api/irrigation/{pk}/` | `stub/contract-only` | Spec exists, but no backend public route is registered. |

## Deprecated Path Decisions

| Old path | Replacement |
|---|---|
| `/api/soil-data/ndvi-health/` | `/api/crop-health/ndvi-health/` |
| `/api/crop-simulation/*` as backend public routes | `/api/yield-harvest/*` |
| `/api/soile/*` as backend public routes | `/api/soil/*` |
