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

// Create axios instance with interceptor for 401 errors
const axiosInstance = axios.create({
  withCredentials: true
})

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
      console.log('Checking authentication...')
      const response = await axiosInstance.get(`${API_BASE_URL}/me`)
      
      if (response.status === 200 && response.data) {
        console.log('User authenticated:', response.data.first_name)
        setUser(response.data)
        setLoading(false)
        return
      }
    } catch (error: any) {
      console.error('Auth check error:', error.response?.status, error.message)
      
      // 401 means user is not authenticated - this is expected when not logged in
      if (error.response?.status === 401) {
        console.log('User not authenticated (401) - redirecting to signin if needed')
        setUser(null)
        
        // Only redirect if not on a public route
        if (!publicRoutes.includes(location.pathname)) {
          navigate('/signin', { replace: true })
        }
      } else {
        // Other errors - keep user logged out but don't redirect if already on public route
        setUser(null)
        if (!publicRoutes.includes(location.pathname)) {
          navigate('/signin', { replace: true })
        }
      }
    } finally {
      setLoading(false)
    }
  }

  const login = async (loginId: string, password: string) => {
    try {
      console.log('Attempting login...')
      const response = await axiosInstance.post(`${API_BASE_URL}/login`, { 
        login_id: loginId, 
        password 
      })
      
      if (response.status === 200) {
        console.log('Login successful')
        setUser(response.data.student)
        setLoading(false)
        return response.data
      } else {
        throw new Error(response.data?.detail || 'Login failed')
      }
    } catch (error: any) {
      console.error('Login error:', error.response?.data || error.message)
      throw new Error(error.response?.data?.detail || 'Login failed. Please try again.')
    }
  }

  const logout = async (): Promise<void> => {
    try {
      console.log('Logging out...')
      await axiosInstance.post(`${API_BASE_URL}/logout`, {})
      console.log('Logout successful')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setUser(null)
      setLoading(false)
      navigate('/signin', { replace: true })
    }
  }

  const register = async (formData: RegistrationData) => {
    try {
      console.log('Registering user...')
      const response = await axiosInstance.post(`${API_BASE_URL}/register`, formData)
      
      if (response.status === 201) {
        console.log('Registration successful')
        return response.data
      } else {
        throw new Error(response.data?.detail || 'Registration failed')
      }
    } catch (error: any) {
      console.error('Registration error:', error.response?.data || error.message)
      throw new Error(error.response?.data?.detail || 'Registration failed. Please try again.')
    }
  }

  const verifyEmail = async (token: string) => {
    try {
      const response = await axiosInstance.get(`${API_BASE_URL}/verify?token=${token}`)
      if (response.status === 200) {
        return response.data
      } else {
        throw new Error(response.data?.detail || 'Verification failed')
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Verification failed')
    }
  }

  const resendVerification = async (email: string) => {
    try {
      const response = await axiosInstance.post(`${API_BASE_URL}/resend-verification`, { email })
      if (response.status === 200) {
        return response.data
      } else {
        throw new Error(response.data?.detail || 'Failed to resend verification')
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to resend verification')
    }
  }

  const requestPasswordReset = async (email: string) => {
    try {
      const response = await axiosInstance.post(`${API_BASE_URL}/password-reset-request`, { email })
      if (response.status === 200) {
        return response.data
      } else {
        throw new Error(response.data?.detail || 'Failed to request password reset')
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to request password reset')
    }
  }

  const confirmPasswordReset = async (token: string, newPassword: string, confirmPassword: string) => {
    try {
      const response = await axiosInstance.post(`${API_BASE_URL}/password-reset-confirm`, { 
        token, 
        new_password: newPassword, 
        confirm_password: confirmPassword 
      })
      if (response.status === 200) {
        return response.data
      } else {
        throw new Error(response.data?.detail || 'Password reset failed')
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Password reset failed')
    }
  }

  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      login, 
      logout, 
      register, 
      checkAuth, 
      verifyEmail, 
      resendVerification, 
      requestPasswordReset, 
      confirmPasswordReset 
    }}>
      {children}
    </AuthContext.Provider>
  )
}