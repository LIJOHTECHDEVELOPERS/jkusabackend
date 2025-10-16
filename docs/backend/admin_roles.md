# Admin Roles

Prefix: `/admin/roles`

## POST /admin/roles
Create a role. Requires `manage_roles`.
- Body: `AdminRoleCreate`

## GET /admin/roles
List roles with pagination and search.

## GET /admin/roles/{role_id}
Get role by ID.

## PUT /admin/roles/{role_id}
Update role. Super-admin checks enforced.

## DELETE /admin/roles/{role_id}
Delete role (cannot delete `super_admin`).

## GET /admin/roles/permissions/available
List available permissions and descriptions.
