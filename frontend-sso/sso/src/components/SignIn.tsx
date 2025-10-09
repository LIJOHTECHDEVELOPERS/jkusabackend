import { FC, useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Input from './ui/Input'
import Button from './ui/Button'
import Alert from './ui/Alert'
import {
  EnvelopeIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ShieldCheckIcon,
  CheckIcon,
  ArrowLeftIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

// Logo Component
const JKUSALogo = ({ className = "w-16 h-16" }: { className?: string }) => (
  <img
    src="images/logo.jpg"
    alt="JKUSA Logo"
    className={className}
  />
)

// OTP Input Component - FIXED
const OTPInput = ({
  otp,
  setOtp,
  error
}: {
  otp: string[]
  setOtp: (otp: string[]) => void
  error?: string
}) => {
  const inputRefs = [
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null)
  ]

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return
    
    const newOtp = [...otp]
    newOtp[index] = value
    setOtp(newOtp)
    
    if (value && index < 5 && inputRefs[index + 1].current) {
      inputRefs[index + 1].current?.focus()
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs[index - 1].current?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const paste = e.clipboardData.getData('text')
    if (/^\d{6}$/.test(paste)) {
      setOtp(paste.split(''))
    }
  }

  const inputClass = (hasError: boolean) => 
    `w-12 h-12 text-center text-lg font-semibold border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
      hasError ? 'border-red-300 bg-red-50' : 'border-gray-300 hover:border-gray-400'
    }`

  return (
    <div className="space-y-2">
      <div className="flex justify-center space-x-2">
        <input
          ref={inputRefs[0]}
          type="text"
          maxLength={1}
          value={otp[0] || ''}
          onChange={(e) => handleChange(0, e.target.value)}
          onKeyDown={(e) => handleKeyDown(0, e)}
          onPaste={handlePaste}
          className={inputClass(!!error)}
          autoFocus
        />
        <input
          ref={inputRefs[1]}
          type="text"
          maxLength={1}
          value={otp[1] || ''}
          onChange={(e) => handleChange(1, e.target.value)}
          onKeyDown={(e) => handleKeyDown(1, e)}
          onPaste={handlePaste}
          className={inputClass(!!error)}
        />
        <input
          ref={inputRefs[2]}
          type="text"
          maxLength={1}
          value={otp[2] || ''}
          onChange={(e) => handleChange(2, e.target.value)}
          onKeyDown={(e) => handleKeyDown(2, e)}
          onPaste={handlePaste}
          className={inputClass(!!error)}
        />
        <input
          ref={inputRefs[3]}
          type="text"
          maxLength={1}
          value={otp[3] || ''}
          onChange={(e) => handleChange(3, e.target.value)}
          onKeyDown={(e) => handleKeyDown(3, e)}
          onPaste={handlePaste}
          className={inputClass(!!error)}
        />
        <input
          ref={inputRefs[4]}
          type="text"
          maxLength={1}
          value={otp[4] || ''}
          onChange={(e) => handleChange(4, e.target.value)}
          onKeyDown={(e) => handleKeyDown(4, e)}
          onPaste={handlePaste}
          className={inputClass(!!error)}
        />
        <input
          ref={inputRefs[5]}
          type="text"
          maxLength={1}
          value={otp[5] || ''}
          onChange={(e) => handleChange(5, e.target.value)}
          onKeyDown={(e) => handleKeyDown(5, e)}
          onPaste={handlePaste}
          className={inputClass(!!error)}
        />
      </div>
      {error && (
        <div className="flex items-center justify-center space-x-1 text-red-600 text-sm">
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}

const SignIn: FC = () => {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // Form state
  const [currentStep, setCurrentStep] = useState<'signin' | 'verify'>('signin')
  const [formData, setFormData] = useState({ login_id: '', password: '' })
  const [otp, setOtp] = useState<string[]>(['', '', '', '', '', ''])
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [resendCooldown, setResendCooldown] = useState(0)
  const [verificationAttempts, setVerificationAttempts] = useState(0)
  const [studentInfo, setStudentInfo] = useState<{ email: string; name: string } | null>(null)
  const [attemptsRemaining, setAttemptsRemaining] = useState<number | null>(null)

  // Extract URL parameters
  const returnType = searchParams.get('return')
  const isSpecialFlow = returnType === 'dashboard' || returnType === 'profile'

  // Cooldown timer effect
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [resendCooldown])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')
    setAttemptsRemaining(null)
    setLoading(true)
    
    try {
      await login(formData.login_id, formData.password)
      setSuccessMessage('Login successful! Redirecting to dashboard...')
      setTimeout(() => {
        navigate('/dashboard')
      }, 1000)
    } catch (err: any) {
      const errorData = err.response?.data?.detail || err.response?.data || {}
      
      if (typeof errorData === 'object') {
        const { code, message, email, student_name, email_sent, attempts_remaining, minutes_remaining } = errorData
        
        switch (code) {
          case 'EMAIL_NOT_VERIFIED':
            setStudentInfo({
              email: email || formData.login_id,
              name: student_name || 'Student'
            })
            setCurrentStep('verify')
            setResendCooldown(60)
            if (email_sent) {
              setSuccessMessage('A verification code has been sent to your email. Please check your inbox.')
            } else {
              setError('Could not send verification email. Please try again or contact support.')
            }
            break
            
          case 'INVALID_CREDENTIALS':
            if (attempts_remaining !== undefined) {
              setAttemptsRemaining(attempts_remaining)
              setError(message || `Invalid credentials. ${attempts_remaining} attempt${attempts_remaining !== 1 ? 's' : ''} remaining.`)
            } else {
              setError(message || 'Invalid email/registration number or password.')
            }
            break
            
          case 'ACCOUNT_LOCKED':
            if (minutes_remaining) {
              setError(message || `Account temporarily locked. Try again in ${minutes_remaining} minute${minutes_remaining !== 1 ? 's' : ''}.`)
            } else {
              setError(message || 'Account is temporarily locked. Please try again later.')
            }
            break
            
          case 'RATE_LIMIT_EXCEEDED':
            setError(message || 'Too many login attempts. Please wait a moment and try again.')
            break
            
          default:
            setError(message || 'Login failed. Please check your credentials and try again.')
        }
      } else {
        setError(typeof errorData === 'string' ? errorData : 'Login failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault()
    const otpString = otp.join('')
    
    if (otpString.length !== 6) {
      setError('Please enter the complete 6-digit verification code')
      return
    }
    
    if (!/^\d{6}$/.test(otpString)) {
      setError('Verification code must contain only numbers')
      return
    }
    
    setLoading(true)
    setError('')
    
    try {
      // Call your verification endpoint here
      // const response = await verifyEmail(otpString)
      
      setSuccessMessage('Email verified successfully! Redirecting...')
      setTimeout(() => {
        handleSubmit(e)
      }, 2000)
    } catch (err: any) {
      const errorData = err.response?.data?.detail || err.response?.data || {}
      
      if (typeof errorData === 'object') {
        const { code, message } = errorData
        
        switch (code) {
          case 'INVALID_OTP':
            setVerificationAttempts(prev => prev + 1)
            setError(message || 'Invalid verification code. Please try again.')
            break
            
          case 'TOKEN_EXPIRED':
            setError(message || 'Verification code has expired. Please request a new one.')
            break
            
          default:
            setError(message || 'Verification failed. Please try again.')
        }
      } else {
        setError('Verification failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleResendOTP = async () => {
    if (resendCooldown > 0) return
    
    setLoading(true)
    setError('')
    setSuccessMessage('')
    
    try {
      // Call your resend verification endpoint here
      // const response = await resendVerification(studentInfo?.email || formData.login_id)
      
      setResendCooldown(60)
      setOtp(['', '', '', '', '', ''])
      setVerificationAttempts(0)
      setSuccessMessage('New verification code sent to your email!')
      
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err: any) {
      const errorData = err.response?.data?.detail || err.response?.data || {}
      
      if (typeof errorData === 'object') {
        setError(errorData.message || 'Failed to resend verification code. Please try again.')
      } else {
        setError('Failed to resend verification code. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleBackToSignin = () => {
    setCurrentStep('signin')
    setError('')
    setSuccessMessage('')
    setOtp(['', '', '', '', '', ''])
    setVerificationAttempts(0)
    setResendCooldown(0)
    setStudentInfo(null)
    setAttemptsRemaining(null)
  }

  // Sign-In Step
  if (currentStep === 'signin') {
    return (
      <div className="font-sans min-h-screen flex flex-col lg:flex-row">
        <div className="flex-1 flex items-center justify-center p-4 sm:p-8 bg-gradient-to-br from-gray-50 to-white">
          <div className="w-full max-w-md space-y-6">
            {isSpecialFlow && (
              <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <div>
                    <h3 className="font-semibold text-green-900">Quick Access Required</h3>
                    <p className="text-sm text-green-700">
                      Sign in to continue to your {returnType}
                    </p>
                  </div>
                </div>
              </div>
            )}

            <div className="text-center space-y-2">
              <div className="flex items-center justify-center space-x-3 mb-4">
                <JKUSALogo />
                <div>
                  <h1 className="text-xl font-bold text-gray-900">JKUSA Portal</h1>
                  <p className="text-xs text-gray-600">Jkuat Student's Network</p>
                </div>
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Welcome back</h2>
              <p className="text-gray-600 text-sm">
                Sign in to your account to continue
              </p>
            </div>

            {error && (
              <Alert type="error" onClose={() => setError('')}>
                <div className="flex items-start space-x-2">
                  <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p>{error}</p>
                    {attemptsRemaining !== null && attemptsRemaining > 0 && (
                      <div className="mt-2 text-xs bg-orange-100 text-orange-800 px-3 py-2 rounded">
                        <strong>Security Alert:</strong> {attemptsRemaining} attempt{attemptsRemaining !== 1 ? 's' : ''} remaining before account lockout
                      </div>
                    )}
                  </div>
                </div>
              </Alert>
            )}

            {successMessage && (
              <Alert type="success" onClose={() => setSuccessMessage('')}>
                {successMessage}
              </Alert>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Email or Registration Number"
                type="text"
                icon={EnvelopeIcon}
                placeholder="Enter your email or reg number"
                value={formData.login_id}
                onChange={(e) => {
                  setFormData({ ...formData, login_id: e.target.value })
                  setError('')
                  setAttemptsRemaining(null)
                }}
                required
                disabled={loading}
              />

              <div className="relative">
                <Input
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  icon={LockClosedIcon}
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={(e) => {
                    setFormData({ ...formData, password: e.target.value })
                    setError('')
                    setAttemptsRemaining(null)
                  }}
                  required
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-11 text-gray-400 hover:text-gray-600 transition-colors"
                  disabled={loading}
                >
                  {showPassword ? (
                    <EyeSlashIcon className="w-5 h-5" />
                  ) : (
                    <EyeIcon className="w-5 h-5" />
                  )}
                </button>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    disabled={loading}
                  />
                  <span className="ml-2 text-sm text-gray-600">Remember me</span>
                </label>
                <button
                  type="button"
                  onClick={() => navigate('/forgot-password')}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
                  disabled={loading}
                >
                  Forgot password?
                </button>
              </div>

              <Button loading={loading} className="w-full" disabled={loading}>
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>

            <div className="text-center">
              <p className="text-gray-600 text-sm">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => navigate('/signup')}
                  className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
                  disabled={loading}
                >
                  Register here
                </button>
              </p>
            </div>

            <div className="text-center mt-6">
              <div className="inline-flex items-center space-x-2 text-xs text-gray-500">
                <ShieldCheckIcon className="h-4 w-4" />
                <span>Secured with enterprise-grade encryption</span>
              </div>
            </div>
          </div>
        </div>

        <div className="hidden lg:flex flex-1 bg-gradient-to-br from-blue-600 to-blue-800 relative overflow-hidden">
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="relative z-10 flex items-center justify-center p-8 text-white">
            <div className="text-center space-y-6 max-w-md">
              <div className="w-16 h-16 mx-auto bg-white/20 rounded-full flex items-center justify-center">
                <ShieldCheckIcon className="h-8 w-8" />
              </div>
              <h3 className="text-2xl font-bold">Secure & Fast</h3>
              <p className="text-blue-100 text-base leading-relaxed">
                Access your student portal with enterprise-grade security and fast performance.
              </p>
              <div className="grid grid-cols-1 gap-4 text-left">
                <div className="flex items-center space-x-3">
                  <CheckIcon className="h-5 w-5 text-green-400 flex-shrink-0" />
                  <span className="text-sm">Email verification system</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckIcon className="h-5 w-5 text-green-400 flex-shrink-0" />
                  <span className="text-sm">SSL encrypted connections</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckIcon className="h-5 w-5 text-green-400 flex-shrink-0" />
                  <span className="text-sm">Account lockout protection</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // OTP Verification Step
  return (
    <div className="font-sans min-h-screen flex flex-col lg:flex-row">
      <div className="flex-1 flex items-center justify-center p-4 sm:p-8 bg-gradient-to-br from-gray-50 to-white">
        <div className="w-full max-w-md space-y-6">
          <button
            onClick={handleBackToSignin}
            className="inline-flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-4 text-sm transition-colors"
            disabled={loading}
          >
            <ArrowLeftIcon className="h-4 w-4" />
            <span>Back to sign in</span>
          </button>

          <div className="text-center space-y-2">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <JKUSALogo />
              <div>
                <h1 className="text-xl font-bold text-gray-900">JKUSA Portal</h1>
                <p className="text-xs text-gray-600">The Jkuat Student's Community</p>
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Verify your email</h2>
            <p className="text-gray-600 text-sm">
              We've sent a verification code to{' '}
              <span className="font-medium text-gray-900">
                {studentInfo?.email || formData.login_id}
              </span>
            </p>
            {studentInfo?.name && (
              <p className="text-sm text-blue-600">
                Welcome, {studentInfo.name}!
              </p>
            )}
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <EnvelopeIcon className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 text-sm text-blue-800">
                <p className="font-medium">Email verification required</p>
                <p className="mt-1 text-blue-700">
                  Your account needs to be verified before you can sign in. Check your inbox for the verification code.
                </p>
              </div>
            </div>
          </div>

          {successMessage && (
            <Alert type="success" onClose={() => setSuccessMessage('')}>
              {successMessage}
            </Alert>
          )}

          {error && (
            <Alert type="error" onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleVerifyOTP} className="space-y-6">
            <div className="space-y-4">
              <label className="block text-sm font-medium text-gray-700 text-center">
                Verification Code
              </label>
              <OTPInput otp={otp} setOtp={setOtp} error={error} />
            </div>

            <Button
              loading={loading}
              disabled={otp.join('').length !== 6 || loading}
              className="w-full"
            >
              {loading ? 'Verifying...' : 'Verify & Sign In'}
            </Button>
          </form>

          <div className="text-center space-y-4">
            <div className="text-sm text-gray-600">
              Didn't receive the code?{' '}
              {resendCooldown > 0 ? (
                <span className="text-gray-400">
                  Resend in {resendCooldown}s
                </span>
              ) : (
                <button
                  type="button"
                  onClick={handleResendOTP}
                  disabled={loading}
                  className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center space-x-1 transition-colors disabled:opacity-50"
                >
                  <span>Resend Code</span>
                </button>
              )}
            </div>

            {verificationAttempts > 0 && verificationAttempts < 5 && (
              <div className="text-xs text-orange-600 bg-orange-50 p-3 rounded-lg border border-orange-200">
                <div className="flex items-center justify-center space-x-2">
                  <ExclamationTriangleIcon className="h-4 w-4" />
                  <span>{5 - verificationAttempts} attempts remaining</span>
                </div>
              </div>
            )}

            {verificationAttempts >= 5 && (
              <div className="text-xs text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">
                <div className="flex items-center justify-center space-x-2">
                  <ExclamationTriangleIcon className="h-4 w-4" />
                  <span>Too many failed attempts. Please try signing in again.</span>
                </div>
              </div>
            )}
          </div>

          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <p className="font-medium text-gray-900 mb-2">Need help?</p>
            <ul className="space-y-1 text-xs">
              <li>• Check your spam or junk folder</li>
              <li>• Make sure you're checking the correct email</li>
              <li>• Wait a minute and try resending the code</li>
              <li>• Contact support if the issue persists</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-blue-600 to-blue-800 relative overflow-hidden">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative z-10 flex items-center justify-center p-8 text-white">
          <div className="text-center space-y-6 max-w-md">
            <div className="w-16 h-16 mx-auto bg-white/20 rounded-full flex items-center justify-center">
              <EnvelopeIcon className="h-8 w-8" />
            </div>
            <h3 className="text-2xl font-bold">Almost There!</h3>
            <p className="text-blue-100 text-base leading-relaxed">
              Please verify your email address to complete the sign-in process and access your account.
            </p>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-sm space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-green-400 rounded-full flex-shrink-0"></div>
                  <span>Check your inbox</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-green-400 rounded-full flex-shrink-0"></div>
                  <span>Enter the 6-digit code</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-gray-400 rounded-full flex-shrink-0"></div>
                  <span>Access your dashboard</span>
                </div>
              </div>
            </div>
            <div className="text-sm text-blue-100 opacity-90 bg-white/5 rounded-lg p-3">
              <p className="font-medium mb-1">Pro Tip:</p>
              <p>Add no-reply@jkusa.ac.ke to your contacts to ensure you receive future notifications.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SignIn