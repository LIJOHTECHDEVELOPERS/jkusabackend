import { type FC, useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {Input } from './ui/input'
import { Button } from './ui/button' // Assuming Button is a named export
import { Alert } from './ui/alert'
import {
  EnvelopeIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ShieldCheckIcon,
  CheckIcon,
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  PaperAirplaneIcon,
  InboxIcon
} from '@heroicons/react/24/outline'

// Logo Component
const JKUSALogo = ({ className = "w-16 h-16" }: { className?: string }) => (
  <img
    src="images/logo.jpg"
    alt="JKUSA Logo"
    className={className}
  />
)

const SignIn: FC = () => {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // Form state
  const [currentStep, setCurrentStep] = useState<'signin' | 'verify'>('signin')
  const [formData, setFormData] = useState({ login_id: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [resendCooldown, setResendCooldown] = useState(0)
  const [studentInfo, setStudentInfo] = useState<{ email: string; name: string } | null>(null)
  const [attemptsRemaining, setAttemptsRemaining] = useState<number | null>(null)
  const [checkingEmail, setCheckingEmail] = useState(false)

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

  // Auto-check for email verification status every 5 seconds
  useEffect(() => {
    let interval: NodeJS.Timeout
    
    if (currentStep === 'verify' && checkingEmail) {
      interval = setInterval(async () => {
        try {
          // Call your check verification status endpoint here
          // const response = await checkVerificationStatus(studentInfo?.email || formData.login_id)
          // if (response.verified) {
          //   setSuccessMessage('Email verified! Redirecting to dashboard...')
          //   setCheckingEmail(false)
          //   setTimeout(() => {
          //     navigate('/dashboard')
          //   }, 2000)
          // }
        } catch (err) {
          // Silent fail - just continue checking
        }
      }, 5000)
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [currentStep, checkingEmail, studentInfo, formData.login_id, navigate])

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
            setCheckingEmail(true)
            if (email_sent) {
              setSuccessMessage('A verification link has been sent to your email. Please check your inbox and click the link to verify your account.')
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

  const handleResendLink = async () => {
    if (resendCooldown > 0) return
    
    setLoading(true)
    setError('')
    setSuccessMessage('')
    
    try {
      // Call your resend verification endpoint here
      // const response = await resendVerification(studentInfo?.email || formData.login_id)
      
      setResendCooldown(60)
      setCheckingEmail(true)
      setSuccessMessage('New verification link sent to your email!')
      
      setTimeout(() => setSuccessMessage(''), 5000)
    } catch (err: any) {
      const errorData = err.response?.data?.detail || err.response?.data || {}
      
      if (typeof errorData === 'object') {
        setError(errorData.message || 'Failed to resend verification link. Please try again.')
      } else {
        setError('Failed to resend verification link. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleBackToSignin = () => {
    setCurrentStep('signin')
    setError('')
    setSuccessMessage('')
    setResendCooldown(0)
    setStudentInfo(null)
    setAttemptsRemaining(null)
    setCheckingEmail(false)
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

  // Email Verification Step
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
            <div className="w-20 h-20 mx-auto bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <InboxIcon className="h-10 w-10 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Check your email</h2>
            <p className="text-gray-600 text-sm">
              We've sent a verification link to{' '}
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
              <PaperAirplaneIcon className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 text-sm text-blue-800">
                <p className="font-medium">Email verification required</p>
                <p className="mt-1 text-blue-700">
                  Click the verification link in your email to activate your account and complete the sign-in process.
                </p>
              </div>
            </div>
          </div>

          {successMessage && (
            <Alert type="success" onClose={() => setSuccessMessage('')}>
              <div className="flex items-center space-x-2">
                <CheckIcon className="h-5 w-5" />
                <span>{successMessage}</span>
              </div>
            </Alert>
          )}

          {error && (
            <Alert type="error" onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          {checkingEmail && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <div className="flex-1 text-sm text-green-800">
                  <p className="font-medium">Waiting for verification...</p>
                  <p className="text-green-700 text-xs mt-1">
                    You'll be automatically redirected once you click the link in your email
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            <div className="text-center text-sm text-gray-600">
              Didn't receive the email?{' '}
              {resendCooldown > 0 ? (
                <span className="text-gray-400">
                  Resend in {resendCooldown}s
                </span>
              ) : (
                <button
                  type="button"
                  onClick={handleResendLink}
                  disabled={loading}
                  className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center space-x-1 transition-colors disabled:opacity-50"
                >
                  <span>Resend Link</span>
                  <PaperAirplaneIcon className="h-4 w-4" />
                </button>
              )}
            </div>

            <Button
              onClick={() => {
                setCheckingEmail(false)
                navigate('/dashboard')
              }}
              className="w-full"
              variant="primary"
            >
              I've verified my email
            </Button>
          </div>

          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
            <p className="font-medium text-gray-900 mb-2">Need help?</p>
            <ul className="space-y-1 text-xs">
              <li>• Check your spam or junk folder</li>
              <li>• Make sure you're checking the correct email address</li>
              <li>• The link expires in 24 hours</li>
              <li>• Wait a minute before requesting a new link</li>
              <li>• Contact support if the issue persists</li>
            </ul>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-xs text-yellow-800">
            <div className="flex items-start space-x-2">
              <ExclamationTriangleIcon className="h-4 w-4 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">Security Note</p>
                <p className="mt-1">
                  Don't share your verification link with anyone. It's unique to your account.
                </p>
              </div>
            </div>
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
            <h3 className="text-2xl font-bold">One Click Away!</h3>
            <p className="text-blue-100 text-base leading-relaxed">
              Simply click the verification link in your email to complete the sign-in process and access your account.
            </p>
            <div className="bg-white/10 rounded-lg p-4">
              <div className="text-sm space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-green-400 rounded-full flex-shrink-0"></div>
                  <span>Check your email inbox</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-green-400 rounded-full flex-shrink-0"></div>
                  <span>Click the verification link</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${checkingEmail ? 'bg-yellow-400 animate-pulse' : 'bg-gray-400'}`}></div>
                  <span>Automatic redirect to dashboard</span>
                </div>
              </div>
            </div>
            <div className="text-sm text-blue-100 opacity-90 bg-white/5 rounded-lg p-3">
              <p className="font-medium mb-1">Pro Tip:</p>
              <p>Add no-reply@jkusa.ac.ke to your contacts to ensure you receive future notifications and updates.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SignIn