# Email Service

Module: `app/services/email_service.py`

## Functions
- `send_verification_email(email, user_name, token) -> bool`
- `send_password_reset_email(email, user_name, token) -> bool`
- `send_welcome_email(email, user_name) -> bool`

All functions return True/False based on SMTP send success.

Environment:
- `SMTP_SERVER`, `SMTP_PORT` (465 or 587), `SMTP_USERNAME`, `SMTP_PASSWORD`
- `EMAIL_FROM`, `EMAIL_FROM_NAME`, `FRONTEND_URL`

## Templates
- Verification, Password Reset, Welcome emails with branded HTML + plain text fallbacks.

Example:
```python
from app.services.email_service import send_verification_email
send_verification_email("john@students.jkuat.ac.ke", "John Doe", token)
```
