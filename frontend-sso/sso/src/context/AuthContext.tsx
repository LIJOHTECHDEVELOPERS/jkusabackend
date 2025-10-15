import React, { createContext, useState, useEffect, useContext } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import axios from 'axios'

const API_BASE_URL = 'https://backend.jkusa.org/students/auth'

interface Student {
  id: number
  first_name: string
  last_name: string
  email: string
  phone_number: string
  registration_number: string
  college_id: number
  school_id: number
  course: string
  year_of_study: number
  is_active: boolean
  created_at: string
  last_login?: string
}

interface RegistrationData {
  first_name: string
  last_name: string
  email: string
  phone_number: string
  registration_number: string
  college_id: number
  school_id: number
  course: string
  year_of_study: number
  password: string
}

interface AuthContextType {
  user: Student | null
  loading: boolean
  login: (loginId: string, password: string) => Promise<any>
  logout: () => Promise<void>
  register: (formData: RegistrationData) => Promise<any>
  checkAuth: () => Promise<void>
  verifyEmail: (token: string) => Promise<any>
  resendVerification: (email: string) => Promise<any>
  requestPasswordReset: (email: string) => Promise<any>
  confirmPasswordReset: (token: string, newPassword: string, confirmPassword: string) => Promise<any>
}

const AuthContext = createContext<AuthContextType | null>(null)

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<Student | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const location = useLocation()

  // Public routes that don't require authentication
  const publicRoutes = ['/signin', '/signup', '/forgot-password', '/reset-password', '/verify-email', '/']

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async (): Promise<void> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/me`, { withCredentials: true })
      if (response.status === 200) {
        setUser(response.data)
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      setUser(null)
      
      // Redirect to signin if not on a public route
      if (!publicRoutes.includes(location.pathname)) {
        navigate('/signin', { replace: true })
      }
    } finally {
      setLoading(false)
    }
  }

  const login = async (loginId: string, password: string) => {
    const response = await axios.post(`${API_BASE_URL}/login`, { login_id: loginId, password }, { withCredentials: true })
    if (response.status !== 200) {
      throw new Error(response.data.detail || 'Login failed')
    }
    setUser(response.data.student)
    return response.data
  }

  const logout = async (): Promise<void> => {
    try {
      await axios.post(`${API_BASE_URL}/logout`, {}, { withCredentials: true })
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setUser(null)
      navigate('/signin', { replace: true })
    }
  }

  const register = async (formData: RegistrationData) => {
    const response = await axios.post(`${API_BASE_URL}/register`, formData, { withCredentials: true })
    if (response.status !== 201) {
      throw new Error(response.data.detail || 'Registration failed')
    }
    return response.data
  }

  const verifyEmail = async (token: string) => {
    const response = await axios.get(`${API_BASE_URL}/verify?token=${token}`, { withCredentials: true })
    if (response.status !== 200) {
      throw new Error(response.data.detail || 'Verification failed')
    }
    return response.data
  }

  const resendVerification = async (email: string) => {
    const response = await axios.post(`${API_BASE_URL}/resend-verification`, { email }, { withCredentials: true })
    if (response.status !== 200) {
      throw new Error(response.data.detail || 'Failed to resend verification')
    }
    return response.data
  }

  const requestPasswordReset = async (email: string) => {
    const response = await axios.post(`${API_BASE_URL}/password-reset-request`, { email }, { withCredentials: true })
    if (response.status !== 200) {
      throw new Error(response.data.detail || 'Failed to request password reset')
    }
    return response.data
  }

  const confirmPasswordReset = async (token: string, newPassword: string, confirmPassword: string) => {
    const response = await axios.post(`${API_BASE_URL}/password-reset-confirm`, { token, new_password: newPassword, confirm_password: confirmPassword }, { withCredentials: true })
    if (response.status !== 200) {
      throw new Error(response.data.detail || 'Password reset failed')
    }
    return response.data
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, checkAuth, verifyEmail, resendVerification, requestPasswordReset, confirmPasswordReset }}>
      {children}
    </AuthContext.Provider>
  )
}