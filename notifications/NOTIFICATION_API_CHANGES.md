# Notification API Changes

## Added paginated notification list API

A new endpoint was added to return all notifications for a farm using pagination.

### Endpoint

`GET /api/notifications/list/`

### Query params

- `farm_uuid` (required): UUID of the farm
- `page` (optional): page number, default depends on DRF pagination behavior
- `page_size` (optional): number of items per page, default `10`, max `100`

### Behavior

- Requires authenticated user
- Returns notifications only if the farm belongs to the authenticated user
- Orders notifications by newest first using `created_at DESC, id DESC`
- Returns paginated response
- Returns `404` if the farm is not found or does not belong to the user

### Response shape

```json
{
  "count": 12,
  "next": "http://localhost:8000/api/notifications/list/?farm_uuid=<uuid>&page=2&page_size=5",
  "previous": null,
  "results": {
    "code": 200,
    "msg": "success",
    "data": [
      {
        "uuid": "...",
        "farm_uuid": "...",
        "since_id": 12,
        "title": "Alert",
        "message": "Check sensor",
        "level": "info",
        "is_read": false,
        "metadata": {},
        "created_at": "2025-01-01T10:00:00Z"
      }
    ]
  }
}
```

## Long-poll behavior update

The `long-poll` notification logic was updated to prioritize unread notifications.

### Updated behavior

- Returns unread notifications first
- If unread notifications are fewer than `5`, fills the remaining slots with read notifications
- If unread notifications are `5` or more, returns only the first `5` unread notifications

### Notes

This behavior was implemented in the notification service layer so the existing long-poll endpoint automatically uses it.

## Files changed

- `notifications/views.py`
- `notifications/urls.py`
- `notifications/services.py`
- `notifications/tests.py`

## Tests added

Added tests for:

- paginated notification list for owned farm
- `404` for unowned farm on list API
- unread-first ordering in long-poll
- long-poll fallback with read notifications when unread count is below `5`
