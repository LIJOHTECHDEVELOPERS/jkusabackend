# Students Authentication & SSO

Prefix: `/students/auth`

## POST /students/auth/register (201)
Registers a new student.
- Body: `studentCreate`
- Responses: `{ success, message, code, email, email_sent }`
- Notes: Validates password strength, JKUAT student email, phone format; creates verification token; sends verification email.

Example:
```bash
curl -X POST $BASE/students/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name":"John","last_name":"Doe",
    "email":"john.doe@students.jkuat.ac.ke",
    "phone_number":"+254712345678",
    "registration_number":"SCT211-0001/2021",
    "college_id":1,"school_id":1,
    "course":"Computer Science","year_of_study":3,
    "password":"SecurePass123!"
  }'
```

## GET /students/auth/verify
Verifies email via token.
- Query: `token`
- Responses: success or token errors; may send welcome email.

## POST /students/auth/login
Login with email or registration number.
- Body: `{ login_id, password }`
- Sets cookies: `access_token`, `refresh_token`
- Responses: `{ success, message, code, student, access_token, token_type }`
- Errors: ACCOUNT_LOCKED, EMAIL_NOT_VERIFIED (resends verification), RATE_LIMIT_EXCEEDED.

## POST /students/auth/refresh
Refresh access token from refresh cookie.
- Returns new access token and sets cookie.

## POST /students/auth/logout
Clears auth cookies.

## GET /students/auth/me
Returns current authenticated student.
- Auth: Bearer access token
- Response: `studentResponse`

## POST /students/auth/password-reset-request
Send password reset email.
- Body: `{ email }`

## POST /students/auth/password-reset-confirm
Confirm password reset.
- Body: `{ token, new_password, confirm_password }`

## POST /students/auth/change-password
Change password while logged in.
- Body: form or JSON fields: `old_password, new_password, confirm_password`

## GET /students/auth/colleges
List colleges.

## GET /students/auth/colleges/{college_id}/schools
List schools in a college.

## GET /students/auth/health
Health check.

## POST /students/auth/resend-verification
Resend email verification.
- Body: `{ email }`
