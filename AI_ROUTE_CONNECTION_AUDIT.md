# Backend ↔ AI Route Connection Audit

Last reconciled against current route registrations and view implementations in:

- `Backend/config/urls.py`
- `Backend/*/urls.py`
- `Backend/*/views.py`
- `Ai/config/urls.py`
- `Ai/*/urls.py`
- `Backend/external_api_adapter/json/ai/index.json`

## Status Vocabulary

- `implemented`: route exists and the corresponding backend ↔ AI integration is implemented now
- `partially_implemented`: route exists, but behavior/readiness is limited or alias-based
- `contract_only`: mock/spec exists, but no real client-facing implementation is registered
- `deprecated`: kept for compatibility or aliasing, but not the preferred canonical route
- `missing`: documented previously, but no route/implementation exists now
- `disabled`: intentionally not exposed for current developer/public use
- `transitional`: works now, but still reflects temporary architecture boundaries or compatibility layers

## Runtime vs Seed Rule

- seed/bootstrap data stays allowed for local/dev/test/bootstrap flows
- runtime application code must not silently return mock/sample/demo data
- if real data is missing, the contract must surface an explicit empty state or structured failure

## Ownership Boundaries

- Backend owns canonical plant catalog records exposed in `Backend/plants`
- AI `farm_data` owns the derived farm read-model and canonical AI-side farm ↔ plant assignment path
- Backend farm-alert tracker route is cached snapshot delivery, not live AI on request
- AI crop-simulation routes own live or derived simulation outputs

## Source-Of-Truth Matrix

| Backend/API contract | Actual route or AI path | Status | Notes |
|---|---|---:|---|
| `POST /api/rag/chat/` | AI only: `Ai/rag/urls.py` | `implemented` | Real AI route; not a backend client route |
| `POST /api/farm-alerts/tracker/` | `Backend/farm_alerts/views.py` → cached snapshot response | `transitional` | Backend route is production-valid, but semantics are `cached_snapshot`, not live AI inference |
| `POST /api/farm-alerts/timeline/` | no backend route | `missing` | Previously documented incorrectly |
| `GET /api/soil-data/` | AI only: `Ai/location_data/urls.py` | `implemented` | Exists on AI service, not on backend public routes |
| `POST /api/soil-data/` | AI only: `Ai/location_data/urls.py` | `implemented` | Exists on AI service, not on backend public routes |
| `GET /api/soil-data/tasks/{task_id}/status/` | AI only: `Ai/location_data/urls.py` | `implemented` | Exists on AI service, not on backend public routes |
| `POST /api/soil-data/ndvi-health/` | real backend route is `POST /api/crop-health/ndvi-health/` | `deprecated` | Old path should not be presented as current |
| `POST /api/soile/moisture-heatmap/` | AI route; backend canonical alias is `POST /api/soil/moisture-heatmap/` | `implemented` | `soile/*` is AI-facing, `soil/*` is backend-facing |
| `POST /api/soile/health-summary/` | AI route; backend canonical alias is `POST /api/soil/summary/` | `implemented` | Same as above |
| `POST /api/soile/anomaly-detection/` | AI route; backend canonical alias is `POST /api/soil/anomalies/` | `implemented` | Same as above |
| `POST /api/farm-data/` | AI route exists; backend uses it for sync | `implemented` | Internal AI contract; not a backend public endpoint |
| `GET /api/farm-data/{farm_uuid}/detail/` | AI route exists: `Ai/farm_data/urls.py` | `implemented` | Internal AI service contract |
| `POST /api/farm-data/parameters/` | AI route exists: `Ai/farm_data/urls.py` | `implemented` | Internal AI service contract |
| `POST /api/weather/farm-card/` | backend route exists; AI canonical route also exists | `implemented` | Backend proxies to weather functionality |
| `POST /api/weather/water-need-prediction/` | AI route exists; backend public contract differs | `partially_implemented` | AI path is real; backend public path is different |
| `POST /api/economy/overview/` | backend + AI route exist | `implemented` | End-to-end connected |
| `GET /api/plants/` | AI route exists as `Ai/plant/urls.py` and backend route exists as `GET /api/plants/` | `implemented` | Different services, both real |
| `POST /api/plants/` | AI + backend real | `implemented` | Different services, both real |
| `GET /api/plants/{pk}/` | AI + backend real | `implemented` | Backend is canonical catalog; AI is its own service/snapshot consumer |
| `PUT /api/plants/{pk}/` | AI route real; backend route not exposed with PUT | `partially_implemented` | Real on AI, not mirrored on backend public app |
| `PATCH /api/plants/{pk}/` | AI route real; backend route not exposed with PATCH | `partially_implemented` | Same limitation |
| `DELETE /api/plants/{pk}/` | AI route real; backend route not exposed with DELETE | `partially_implemented` | Same limitation |
| `POST /api/plants/fetch-info/` | AI route real | `implemented` | AI route exists; backend public equivalent is absent |
| `POST /api/pest-disease/detect/` | backend alias + AI route real | `implemented` | Canonical current path |
| `POST /api/pest-disease/risk/` | backend alias + AI route real | `implemented` | Canonical current path |
| `POST /api/pest-disease/risk-summary/` | backend alias route exists | `implemented` | Implemented in backend alias layer |
| `GET /api/irrigation/` | backend + AI real | `implemented` | Canonical list route |
| `POST /api/irrigation/` | AI route real; backend route currently list/create mismatch | `partially_implemented` | Backend public create contract is not yet cleanly reconciled |
| `GET /api/irrigation/{pk}/` | AI route real; backend route missing | `partially_implemented` | Real in AI only |
| `PUT /api/irrigation/{pk}/` | AI route real; backend route missing | `contract_only` | Present in mock/spec and AI service, not a backend public route |
| `PATCH /api/irrigation/{pk}/` | AI route real; backend route missing | `contract_only` | Same |
| `DELETE /api/irrigation/{pk}/` | AI route real; backend route missing | `contract_only` | Same |
| `POST /api/irrigation/recommend/` | backend + AI real | `implemented` | Canonical route |
| `GET /api/irrigation/recommend/{task_id}/status/` | mock/spec only | `contract_only` | No current backend or AI route registration found |
| `POST /api/fertilization/recommend/` | backend + AI real | `implemented` | Canonical route |
| `GET /api/fertilization/recommend/{task_id}/status/` | mock/spec only | `contract_only` | No current route registration found |
| `POST /api/crop-simulation/growth/` | AI route real; backend canonical client route is `/api/yield-harvest/growth/` | `deprecated` | Real AI route, but backend public source-of-truth remains under `yield-harvest/*` |
| `GET /api/crop-simulation/growth/{task_id}/status/` | AI route real; backend canonical client route is `/api/yield-harvest/growth/{task_id}/status/` | `deprecated` | Same |
| `POST /api/crop-simulation/current-farm-chart/` | AI route real; backend canonical client route is `/api/yield-harvest/current-farm-chart/` | `deprecated` | Same |
| `POST /api/crop-simulation/harvest-prediction/` | AI route real; backend canonical client route is `/api/yield-harvest/harvest-prediction/` | `deprecated` | Same |
| `POST /api/crop-simulation/yield-prediction/` | AI route real; backend canonical client route is `/api/yield-harvest/yield-prediction/` | `deprecated` | Same |

## Response Semantics

- `farm-alerts/tracker` backend route → `cached snapshot`
- `irrigation/*` backend routes → mostly `proxy` or `backend-owned data with AI enrichment`
- `yield-harvest/*` backend routes → `proxy` to AI plus persisted backend logs for some summaries
- `farm-data/*` AI routes → `AI-owned derived read/write model`

## Reconciliation Notes

- `pest-disease/*` is now the real backend alias and AI contract. Older references to `pest-detection/analyze` as the “real” path are stale.
- `farm-alerts/timeline` is not a registered backend route and must not be documented as implemented.
- `soil-data/*`, `farm-data/*`, and several `plants/*` routes are real on the AI service, but not backend public routes; docs must distinguish internal AI contracts from backend client APIs.
- `crop-simulation/*` remains real on AI, while backend public endpoints are exposed under `yield-harvest/*`.
- task status endpoints for fertilization and irrigation recommendation remain mock/spec-only in `Backend/external_api_adapter/json/ai/index.json`.
- schema UI endpoints are intentionally disabled in AI; developers should rely on version-controlled audit docs until schema publishing is intentionally re-enabled.

## Known Gaps / Follow-up

- Some backend docs still use historical “AI route” wording where “internal AI contract” would be more precise.
- Some dashboard-era docs still need cleanup where old mock fallback language remains.
