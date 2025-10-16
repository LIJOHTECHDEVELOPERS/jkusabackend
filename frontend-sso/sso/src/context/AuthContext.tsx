import React, { createContext, useState, useEffect, useContext } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import axios, { AxiosInstance } from 'axios'

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
  email_verified_at?: string
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

// Token management
class TokenManager {
  private static readonly TOKEN_KEY = 'auth_token'
  private static readonly TOKEN_TYPE_KEY = 'token_type'

  static setToken(token: string, tokenType: string = 'bearer') {
    try {
      sessionStorage.setItem(this.TOKEN_KEY, token)
      sessionStorage.setItem(this.TOKEN_TYPE_KEY, tokenType)
      console.log('✅ Token stored in sessionStorage')
    } catch (e) {
      console.error('Failed to store token:', e)
    }
  }

  static getToken(): string | null {
    try {
      return sessionStorage.getItem(this.TOKEN_KEY)
    } catch (e) {
      console.error('Failed to retrieve token:', e)
      return null
    }
  }

  static getTokenType(): string {
    try {
      return sessionStorage.getItem(this.TOKEN_TYPE_KEY) || 'bearer'
    } catch (e) {
      return 'bearer'
    }
  }

  static clearToken() {
    try {
      sessionStorage.removeItem(this.TOKEN_KEY)
      sessionStorage.removeItem(this.TOKEN_TYPE_KEY)
      console.log('✅ Token cleared from sessionStorage')
    } catch (e) {
      console.error('Failed to clear token:', e)
    }
  }

  static isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const expirationTime = payload.exp * 1000 // Convert to milliseconds
      return Date.now() >= expirationTime
    } catch (e) {
      console.error('Failed to decode token:', e)
      return true
    }
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<Student | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const location = useLocation()

  // Public routes that don't require authentication
  const publicRoutes = ['/signin', '/signup', '/forgot-password', '/reset-password', '/verify-email', '/']

  // Create axios instance with token interceptor
  const createAxiosInstance = (): AxiosInstance => {
    const instance = axios.create({
      withCredentials: true
    })

    // Request interceptor: Add token to headers
    instance.interceptors.request.use((config) => {
      const token = TokenManager.getToken()
      const tokenType = TokenManager.getTokenType()
      
      if (token) {
        config.headers.Authorization = `${tokenType} ${token}`
        console.log('📤 Token added to request header')
      }
      return config
    }, (error) => {
      return Promise.reject(error)
    })

    // Response interceptor: Handle 401 errors
    instance.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          console.error('❌ Unauthorized (401) - Token may be expired')
          TokenManager.clearToken()
          setUser(null)
          
          // Only redirect if not already on public route
          if (!publicRoutes.includes(location.pathname)) {
            navigate('/signin', { replace: true })
          }
        }
        return Promise.reject(error)
      }
    )

    return instance
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async (): Promise<void> => {
    try {
      console.log('🔍 Checking authentication...')
      const token = TokenManager.getToken()

      if (!token) {
        console.log('ℹ️ No token found - user not authenticated')
        setUser(null)
        setLoading(false)
        return
      }

      if (TokenManager.isTokenExpired(token)) {
        console.error('❌ Token expired')
        TokenManager.clearToken()
        setUser(null)
        setLoading(false)
        return
      }

      const axiosInstance = createAxiosInstance()
      const response = await axiosInstance.get(`${API_BASE_URL}/me`)

      if (response.status === 200 && response.data) {
        // Handle both wrapped and direct responses
        const userData = response.data.data || response.data
        console.log('✅ User authenticated:', userData.first_name)
        setUser(userData)
      }
    } catch (error: any) {
      console.error('❌ Auth check failed:', error.response?.status, error.message)
      TokenManager.clearToken()
      setUser(null)

      if (!publicRoutes.includes(location.pathname)) {
        navigate('/signin', { replace: true })
      }
    } finally {
      setLoading(false)
    }
  }

  const login = async (loginId: string, password: string) => {
    try {
      console.log('🔐 Attempting login...')
      const response = await axios.post(
        `${API_BASE_URL}/login`,
        { login_id: loginId, password },
        { withCredentials: true }
      )

      if (response.status === 200 && response.data.access_token) {
        console.log('✅ Login successful')
        
        // Store the token
        TokenManager.setToken(response.data.access_token, response.data.token_type)
        setUser(response.data.student)
        setLoading(false)
        
        return response.data
      } else {
        throw new Error(response.data?.message || 'Login failed')
      }
    } catch (error: any) {
      console.error('❌ Login error:', error.response?.data || error.message)
      setLoading(false)
      throw new Error(error.response?.data?.message || 'Login failed. Please try again.')
    }
  }

  const logout = async (): Promise<void> => {
    try {
      console.log('👋 Logging out...')
      const axiosInstance = createAxiosInstance()
      await axiosInstance.post(`${API_BASE_URL}/logout`, {})
      console.log('✅ Logout successful')
    } catch (error) {
      console.error('⚠️ Logout error (continuing anyway):', error)
    } finally {
      TokenManager.clearToken()
      setUser(null)
      setLoading(false)
      navigate('/signin', { replace: true })
    }
  }

  const register = async (formData: RegistrationData) => {
    try {
      console.log('📝 Registering user...')
      const response = await axios.post(
        `${API_BASE_URL}/register`,
        formData,
        { withCredentials: true }
      )

      if (response.status === 201) {
        console.log('✅ Registration successful')
        return response.data
      } else {
        throw new Error(response.data?.message || 'Registration failed')
      }
    } catch (error: any) {
      console.error('❌ Registration error:', error.response?.data || error.message)
      throw new Error(error.response?.data?.message || 'Registration failed. Please try again.')
    }
  }

  const verifyEmail = async (token: string) => {
    try {
      const axiosInstance = createAxiosInstance()
      const response = await axiosInstance.get(`${API_BASE_URL}/verify?token=${token}`)
      if (response.status === 200) {
        return response.data
      } else {
        throw new Error(response.data?.message || 'Verification failed')
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Verification failed')
    }
  }

  const resendVerification = async (email: string) => {
    try {
      const axiosInstance = createAxiosInstance()
      const response = await axiosInstance.post(`${API_BASE_URL}/resend-verification`, { email })
      if (response.status === 200) {
        return response.data
      } else {
        throw new Error(response.data?.message || 'Failed to resend verification')
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to resend verification')
    }
  }

  const requestPasswordReset = async (email: string) => {
    try {
      const axiosInstance = createAxiosInstance()
      const response = await axiosInstance.post(`${API_BASE_URL}/password-reset-request`, { email })
      if (response.status === 200) {
        return response.data
      } else {
        throw new Error(response.data?.message || 'Failed to request password reset')
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to request password reset')
    }
  }

  const confirmPasswordReset = async (token: string, newPassword: string, confirmPassword: string) => {
    try {
      const axiosInstance = createAxiosInstance()
      const response = await axiosInstance.post(
        `${API_BASE_URL}/password-reset-confirm`,
        {
          token,
          new_password: newPassword,
          confirm_password: confirmPassword
        }
      )
      if (response.status === 200) {
        return response.data
      } else {
        throw new Error(response.data?.message || 'Password reset failed')
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Password reset failed')
    }
  }

  return (
    <AuthContext.Provider
      value={{
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
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}