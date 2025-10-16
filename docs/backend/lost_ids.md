# Lost & Found IDs

Prefix: `/api/lost-ids`

## POST /
Post a found ID.
- Body: `PostIDRequest`
- Response: `LostIDResponse`

## GET /
List IDs with filters and pagination.
- Query: `status`, `station`, `id_type`, `limit`, `offset`
- Response: `LostIDResponse[]`

## GET /search
Search by name or ID number.
- Query: `q`, optional `status`, `station`, `limit`

## GET /{id_record}
Get a record by ID.

## PUT /{id_record}/collect
Mark as collected.
- Body: `MarkCollectedRequest`

## GET /stats/info
System info and counters.
- Response: `SystemInfoResponse`

## GET /stats/detailed
Detailed statistics.
- Response: `DetailedStatisticsResponse`

## DELETE /{id_record}
Delete a record.

## GET /by-station/{station}
IDs by station.

## GET /recent/available
Recent available IDs.

## PATCH /{id_record}
Update details (if not collected).

## GET /health/check
Health check.
