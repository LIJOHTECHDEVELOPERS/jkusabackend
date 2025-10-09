import { FC, useState, useEffect } from 'react'
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
  AcademicCapIcon,
  ShieldCheckIcon,
  CheckIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline'

// Logo Component
const JKUSALogo = ({ className = "w-16 h-16" }: { className?: string }) => (
  <div className={`bg-blue-600 rounded-full flex items-center justify-center ${className}`}>
    <AcademicCapIcon className="w-8 h-8 text-white" />
  </div>
)

// OTP Input Component
const OTPInput = ({ 
  otp, 
  setOtp, 
  error 
}: { 
  otp: string[]
  setOtp: (otp: string[]) => void
  error?: string 
}) => {
  return (
    <div className="space-y-2">
      <div className="flex justify-center space-x-2">
        {[0, 1, 2, 3, 4, 5].map((index) => (
          <input
            key={index}
            type="text"
            maxLength={1}
            value={otp[index] || ''}
            onChange={(e) => {
              const value = e.target.value
              if (!/^\d*$/.test(value)) return
              const newOtp = [...otp]
              newOtp[index] = value
              setOtp(newOtp)
              if (value && index < 5) {
                const nextInput = document.querySelector(`input[data-index="${index + 1}"]`) as HTMLInputElement
                if (nextInput) nextInput.focus()
              }
            }}
            onKeyDown={(e) => {
              if (e.key === 'Backspace' && !otp[index] && index > 0) {
                const prevInput = document.querySelector(`input[data-index="${index - 1}"]`) as HTMLInputElement
                if (prevInput) prevInput.focus()
              }
            }}
            onPaste={(e) => {
              e.preventDefault()
              const paste = e.clipboardData.getData('text')
              if (/^\d{6}$/.test(paste)) {
                setOtp(paste.split(''))
              }
            }}
            data-index={index}
            className={`w-12 h-12 text-center text-lg font-semibold border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${
              error ? 'border-red-300 bg-red-50' : 'border-gray-300 hover:border-gray-400'
            }`}
          />
        ))}
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
    setLoading(true)

    try {
      await login(formData.login_id, formData.password)
      
      // Check if email verification is required
      // If verification required, switch to verify step
      // Otherwise navigate to dashboard
      navigate('/dashboard')
    } catch (err: any) {
      // Check if error is due to unverified email
      if (err.code === 'EMAIL_NOT_VERIFIED' || 
          err.message?.toLowerCase().includes('verify your email')) {
        setCurrentStep('verify')
        setResendCooldown(60)
        setError('Your email is not verified. We\'ve sent a verification code to your email.')
      } else {
        setError(err.message || 'Login failed')
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
      // Call your verify email API here
      // await verifyEmail(formData.login_id, otpString)
      
      setSuccessMessage('Email verified successfully!')
      setTimeout(() => {
        navigate('/dashboard')
      }, 2000)
    } catch (err: any) {
      if (err.code === 'INVALID_OTP') {
        setVerificationAttempts(prev => prev + 1)
      }
      setError(err.message || 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  const handleResendOTP = async () => {
    if (resendCooldown > 0) return

    setLoading(true)
    setError('')

    try {
      // Call your resend verification API here
      // await resendVerification(formData.login_id)
      
      setResendCooldown(60)
      setOtp(['', '', '', '', '', ''])
      setVerificationAttempts(0)
      setSuccessMessage('New verification code sent to your email!')
    } catch (err: any) {
      setError('Failed to resend verification code. Please try again.')
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
  }

  // Sign-In Step
  if (currentStep === 'signin') {
    return (
      <div className="font-sans min-h-screen flex flex-col lg:flex-row">
        {/* Left Side - Form */}
        <div className="flex-1 flex items-center justify-center p-4 sm:p-8 bg-gradient-to-br from-gray-50 to-white">
          <div className="w-full max-w-md space-y-6">
            {/* Special Flow Banner */}
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

            {/* Header */}
            <div className="text-center space-y-2">
              <div className="flex items-center justify-center space-x-3 mb-4">
                <JKUSALogo />
                <div>
                  <h1 className="text-xl font-bold text-gray-900">JKUSA Portal</h1>
                  <p className="text-xs text-gray-600">Student Management System</p>
                </div>
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Welcome back</h2>
              <p className="text-gray-600 text-sm">
                Sign in to your account to continue
              </p>
            </div>

            {/* Error Alert */}
            {error && (
              <Alert type="error" onClose={() => setError('')}>
                {error}
              </Alert>
            )}

            {/* Success Message */}
            {successMessage && (
              <Alert type="success" onClose={() => setSuccessMessage('')}>
                {successMessage}
              </Alert>
            )}

            {/* Sign-In Form */}
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
                }}
                required
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
                  }}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-11 text-gray-400 hover:text-gray-600 transition-colors"
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
                  />
                  <span className="ml-2 text-sm text-gray-600">Remember me</span>
                </label>
                <button 
                  type="button" 
                  onClick={() => navigate('/forgot-password')} 
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
                >
                  Forgot password?
                </button>
              </div>

              <Button loading={loading} className="w-full">
                Sign In
              </Button>
            </form>

            {/* Sign-Up Link */}
            <div className="text-center">
              <p className="text-gray-600 text-sm">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => navigate('/signup')}
                  className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
                >
                  Register here
                </button>
              </p>
            </div>
          </div>
        </div>

        {/* Right Side - Info Panel */}
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
                  <span className="text-sm">Two-factor authentication</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckIcon className="h-5 w-5 text-green-400 flex-shrink-0" />
                  <span className="text-sm">SSL encrypted connections</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckIcon className="h-5 w-5 text-green-400 flex-shrink-0" />
                  <span className="text-sm">24/7 account monitoring</span>
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
      {/* Left Side - Verification Form */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-8 bg-gradient-to-br from-gray-50 to-white">
        <div className="w-full max-w-md space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <button
              onClick={handleBackToSignin}
              className="inline-flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-4 text-sm transition-colors"
            >
              <ArrowLeftIcon className="h-4 w-4" />
              <span>Back to sign in</span>
            </button>

            <div className="flex items-center justify-center space-x-3 mb-4">
              <JKUSALogo />
              <div>
                <h1 className="text-xl font-bold text-gray-900">JKUSA Portal</h1>
                <p className="text-xs text-gray-600">Student Management System</p>
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Verify your email</h2>
            <p className="text-gray-600 text-sm">
              Enter the 6-digit code sent to <span className="font-medium text-gray-900">{formData.login_id}</span>
            </p>
          </div>

          {/* Success Message */}
          {successMessage && (
            <Alert type="success" onClose={() => setSuccessMessage('')}>
              {successMessage}
            </Alert>
          )}

          {/* Error Alert */}
          {error && (
            <Alert type="error" onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          {/* OTP Form */}
          <form onSubmit={handleVerifyOTP} className="space-y-6">
            <div className="space-y-4">
              <label className="block text-sm font-medium text-gray-700 text-center">
                Verification Code
              </label>
              <OTPInput otp={otp} setOtp={setOtp} error={error} />
            </div>

            <Button
              loading={loading}
              disabled={otp.join('').length !== 6}
              className="w-full"
            >
              Verify & Sign In
            </Button>
          </form>

          {/* Resend Section */}
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
                  className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center space-x-1 transition-colors"
                >
                  <span>Resend Code</span>
                </button>
              )}
            </div>

            {verificationAttempts > 0 && verificationAttempts < 5 && (
              <div className="text-xs text-orange-600 bg-orange-50 p-2 rounded border border-orange-200">
                {5 - verificationAttempts} attempts remaining
              </div>
            )}

            {verificationAttempts >= 5 && (
              <div className="text-xs text-red-600 bg-red-50 p-2 rounded border border-red-200">
                Too many failed attempts. Please try signing in again.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Side - Info Panel */}
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
            <div className="text-sm text-blue-100 opacity-90">
              <p>Tip: Check your spam folder if you don't see the email</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SignIn