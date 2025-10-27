import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './pages/ProtectedRoute'
import Layout from './components/Layout'

// Auth Pages (No Layout)
import SignIn from './components/SignIn'
import SignUp from './components/SignUp'
import ForgotPassword from './components/ForgotPassword'
import ResetPasswordConfirm from './components/ResetPasswordConfirm'
import VerifyEmail from './components/VerifyEmail'

// Protected Pages (With Layout)
import Dashboard from './pages/Dashboard'
import StudentFormsPage from './pages/StudentsFormsPage'

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Routes>
        {/* ==================== PUBLIC ROUTES (No Layout) ==================== */}
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPasswordConfirm />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        
        {/* ==================== PROTECTED ROUTES (With Layout) ==================== */}
        
        {/* Dashboard */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Layout title="Dashboard">
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        {/* Forms List */}
        <Route 
          path="/forms" 
          element={
            <ProtectedRoute>
              <Layout title="Forms">
                <StudentFormsPage />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        {/* Form Detail */}
        <Route 
          path="/forms/:formId" 
          element={
            <ProtectedRoute>
              <Layout title="Form Submission">
                <StudentFormsPage />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        {/* Events (Example - add when ready) */}
        {/* 
        <Route 
          path="/events" 
          element={
            <ProtectedRoute>
              <Layout title="Events">
                <EventsPage />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/events/:eventId" 
          element={
            <ProtectedRoute>
              <Layout title="Event Details">
                <EventDetailsPage />
              </Layout>
            </ProtectedRoute>
          } 
        />
        */}
        
        {/* Calendar (Example - add when ready) */}
        {/* 
        <Route 
          path="/calendar" 
          element={
            <ProtectedRoute>
              <Layout title="Calendar">
                <CalendarPage />
              </Layout>
            </ProtectedRoute>
          } 
        />
        */}
        
        {/* Profile (Example - add when ready) */}
        {/* 
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <Layout title="My Profile">
                <ProfilePage />
              </Layout>
            </ProtectedRoute>
          } 
        />
        */}
        
        {/* Settings (Example - add when ready) */}
        {/* 
        <Route 
          path="/settings" 
          element={
            <ProtectedRoute>
              <Layout title="Settings">
                <SettingsPage />
              </Layout>
            </ProtectedRoute>
          } 
        />
        */}
        
        {/* ==================== DEFAULT ROUTES ==================== */}
        
        {/* Root - redirects to dashboard (auto-redirects to signin if not authenticated) */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* 404 - Catch all unmatched routes */}
        <Route path="*" element={<Navigate to="/signin" replace />} />
      </Routes>
    </AuthProvider>
  )
}

export default App