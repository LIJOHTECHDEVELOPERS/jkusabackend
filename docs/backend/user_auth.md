# User Auth (simple)

Prefix: `/auth`

## POST /auth/register
- Body: `UserCreate`
- Response: `Token`

## POST /auth/login
- Body: OAuth2 form (`username`, `password`)
- Response: `Token`
