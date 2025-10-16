# Admin Authentication

Prefix: `/admin/auth`

## POST /admin/auth/register-admin
Create admin (requires `manage_admins`).
- Body: `AdminCreate`
- Response: `TokenWithUser`

## POST /admin/auth/login
Login with JSON.
- Body: `{ username: string (or email), password: string }`
- Response: `TokenWithUser`

## GET /admin/auth/admins
Paginated list with filters.
- Query: `page, per_page, search, is_active, role_id, sort_by, sort_order`
- Response: `AdminListResponse`

## GET /admin/auth/admins/{id}
Admin by ID.

## PUT /admin/auth/admins/{id}
Update admin.

## DELETE /admin/auth/admins/{id}
Soft-delete (deactivate) admin.

## POST /admin/auth/admins/{id}/activate
Activate admin.

## GET /admin/auth/me
Current admin info.

## PUT /admin/auth/me
Update own profile (no role/status changes).

## POST /admin/auth/refresh-token | /refresh
Refresh token.

## POST /admin/auth/logout
Client should discard token.

## GET /admin/auth/verify-token
Validates token and returns admin info.
