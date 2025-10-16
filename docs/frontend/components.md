# Frontend Components

Project: `frontend-sso/sso`

## Context
- `useAuth()` and `AuthProvider` (`src/context/AuthContext.tsx`)
  - Methods: `login(loginId, password)`, `logout()`, `register(formData)`, `checkAuth()`, `verifyEmail(token)`, `resendVerification(email)`, `requestPasswordReset(email)`, `confirmPasswordReset(token, newPassword, confirmPassword)`
  - Stores token in sessionStorage; axios interceptors add Authorization header; uses cookie-based refresh.

## UI Components (`src/components/ui`)
- `Input`
  - Props: `{ label?, error?, icon?, ...InputHTMLAttributes }`
  - Example:
```tsx
<Input label="Email" type="email" placeholder="you@students.jkuat.ac.ke" />
```
- `Button`
  - Props: `{ loading?, variant?: 'primary'|'secondary'|'danger', ...ButtonHTMLAttributes }`
  - Example:
```tsx
<Button loading>Submitting...</Button>
```
- `Alert`
  - Props: `{ type?: 'info'|'success'|'error'|'warning', onClose?, children }`

## Auth Pages
- `SignIn` (`src/components/SignIn.tsx`)
  - Uses `useAuth().login` and guides verification flow on `EMAIL_NOT_VERIFIED`.
- `ProtectedRoute` (`src/pages/ProtectedRoute.tsx`)
  - Redirects unauthenticated users to `/signin`.
- `Layout` (`src/components/Layout.tsx`)
  - Composes `SideBar` and `TopBar`, responsive sidebar.
