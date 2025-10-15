import { Routes, Route } from 'react-router-dom'
import SignIn from './components/SignIn.tsx'
import SignUp from './components/SignUp.tsx'
import ForgotPassword from './components/ForgotPassword.tsx'
import ResetPasswordConfirm from './components/ResetPasswordConfirm.tsx'
import VerifyEmail from './components/VerifyEmail.tsx'
import Dashboard from './pages/Dashboard.tsx'
import { AuthProvider } from './context/AuthContext'

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPasswordConfirm />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/" element={<SignIn />} />
      </Routes>
    </AuthProvider>
  )
}

export default App