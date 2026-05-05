# Backend ↔ AI Integration Flow Contract

## Ownership
- `Backend/plants` owns the canonical plant catalog stored in Backend DB.
- `Ai/farm_data` stores plant catalog snapshots and derived farm read-model data for AI workflows.
- `Backend/farm_alerts` returns persisted tracker snapshots; it does not expose live AI inference on the tracker endpoint.
- `Ai/crop_simulation` owns simulation-derived outputs and live inference tasks.

## Flow Types
- `direct_proxy`: Backend forwards request/response to AI without changing ownership.
- `backend_owned_data_with_ai_enrichment`: Backend owns the base record and augments it with AI output or AI sync.
- `cached_snapshot`: Response is served from persisted snapshot state.
- `live_ai_inference`: Response or task is generated from live AI execution.
- `ai_owned_derived_output`: AI returns computed or derived outputs from its own services/read-models.

## Response Metadata
Touched endpoints now expose a top-level `meta` object with:
- `flow_type`
- `source_type`
- `source_service`
- `ownership`
- `live`
- `cached`
- optional `generated_at`
- optional `snapshot_at`
- optional sync fields for Backend plant endpoints
