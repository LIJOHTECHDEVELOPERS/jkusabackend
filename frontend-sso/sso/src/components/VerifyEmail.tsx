import { FC, useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {Input } from './ui/input'
import { Button } from './ui/button' // Assuming Button is a named export
import { Alert } from './ui/alert'
import { 
  EnvelopeIcon, 
  ArrowPathIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  ShieldCheckIcon,
  CheckIcon
} from '@heroicons/react/24/outline'

// Logo Component - Updated to use actual JKUSA logo
const JKUSALogo = ({ className = "w-16 h-16" }: { className?: string }) => (
  <img
    src="images/logo.jpg"
    alt="JKUSA Logo"
    className={className}
  />
)

const VerifyEmail: FC = () => {
  const { verifyEmail } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const token = searchParams.get('token') || ''

  useEffect(() => {
    const verify = async () => {
      try {
        const result = await verifyEmail(token)
        setSuccess(result.detail)
        setTimeout(() => navigate('/signin'), 3000)
      } catch (err: any) {
        setError(err.message || 'Verification failed')
      } finally {
        setLoading(false)
      }
    }
    verify()
  }, [token, verifyEmail, navigate])

  return (
    <div className="font-sans min-h-screen flex flex-col lg:flex-row">
      {/* Left Side - Verification Content */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-8 bg-gradient-to-br from-gray-50 to-white">
        <div className="w-full max-w-md space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <JKUSALogo />
              <div>
                <h1 className="text-xl font-bold text-gray-900">JKUSA Portal</h1>
                <p className="text-xs text-gray-600">The Jkuat Student's Community</p>
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Email Verification</h2>
            <p className="text-gray-600 text-sm">
              {loading ? 'Verifying your email address...' : success ? 'Verification complete!' : 'Verification status'}
            </p>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="text-center space-y-4">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                <ArrowPathIcon className="w-10 h-10 text-blue-600 animate-spin" />
              </div>
              <div className="space-y-2">
                <p className="text-gray-700 font-medium">Please wait...</p>
                <p className="text-sm text-gray-500">We're verifying your email address</p>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-center space-x-2 text-sm text-blue-700">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <span>This should only take a moment</span>
                </div>
              </div>
            </div>
          )}

          {/* Success State */}
          {!loading && success && (
            <div className="text-center space-y-4">
              <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto">
                <CheckCircleIcon className="w-10 h-10 text-white" />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-gray-900">Verification Successful!</h3>
                <p className="text-gray-600">{success}</p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                <div className="space-y-3 text-sm">
                  <div className="flex items-center space-x-3">
                    <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0" />
                    <span className="text-gray-700">Email verified successfully</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0" />
                    <span className="text-gray-700">Account activated</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse flex-shrink-0"></div>
                    <span className="text-gray-600">Redirecting to sign in...</span>
                  </div>
                </div>
              </div>

              <Alert type="success" onClose={() => setSuccess('')}>
                {success}
              </Alert>

              <Button 
                onClick={() => navigate('/signin')} 
                className="w-full"
              >
                Continue to Sign In
              </Button>
            </div>
          )}

          {/* Error State */}
          {!loading && error && (
            <div className="text-center space-y-4">
              <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto">
                <XCircleIcon className="w-10 h-10 text-red-600" />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-gray-900">Verification Failed</h3>
                <p className="text-gray-600">We couldn't verify your email address</p>
              </div>

              <Alert type="error" onClose={() => setError('')}>
                {error}
              </Alert>

              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-left">
                <p className="text-sm font-semibold text-gray-900 mb-2">Common issues:</p>
                <ul className="text-sm text-gray-700 space-y-1">
                  <li className="flex items-start space-x-2">
                    <span className="text-red-500 mt-0.5">•</span>
                    <span>The verification link may have expired</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-red-500 mt-0.5">•</span>
                    <span>The link may have already been used</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-red-500 mt-0.5">•</span>
                    <span>The verification token is invalid</span>
                  </li>
                </ul>
              </div>

              <div className="space-y-3">
                <Button 
                  onClick={() => navigate('/signin')} 
                  className="w-full"
                >
                  Go to Sign In
                </Button>
                <button 
                  onClick={() => navigate('/signup')} 
                  className="w-full text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
                >
                  Need to register again?
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Side - Info Panel */}
      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-blue-600 to-blue-800 relative overflow-hidden">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative z-10 flex items-center justify-center p-8 text-white">
          <div className="text-center space-y-6 max-w-md">
            {loading ? (
              <>
                <div className="w-16 h-16 mx-auto bg-white/20 rounded-full flex items-center justify-center">
                  <ArrowPathIcon className="h-8 w-8 animate-spin" />
                </div>
                <h3 className="text-2xl font-bold">Verifying Your Email</h3>
                <p className="text-blue-100 text-base leading-relaxed">
                  We're confirming your email address to ensure the security of your account.
                </p>
              </>
            ) : success ? (
              <>
                <div className="w-16 h-16 mx-auto bg-white/20 rounded-full flex items-center justify-center">
                  <CheckCircleIcon className="h-8 w-8" />
                </div>
                <h3 className="text-2xl font-bold">Welcome to JKUSA!</h3>
                <p className="text-blue-100 text-base leading-relaxed">
                  Your email has been verified successfully. You can now access all features of the student portal.
                </p>
                <div className="grid grid-cols-1 gap-4 text-left">
                  <div className="flex items-center space-x-3">
                    <CheckIcon className="h-5 w-5 text-green-400 flex-shrink-0" />
                    <span className="text-sm">Access your dashboard</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <CheckIcon className="h-5 w-5 text-green-400 flex-shrink-0" />
                    <span className="text-sm">View academic records</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <CheckIcon className="h-5 w-5 text-green-400 flex-shrink-0" />
                    <span className="text-sm">Manage your profile</span>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="w-16 h-16 mx-auto bg-white/20 rounded-full flex items-center justify-center">
                  <ShieldCheckIcon className="h-8 w-8" />
                </div>
                <h3 className="text-2xl font-bold">Email Verification</h3>
                <p className="text-blue-100 text-base leading-relaxed">
                  Email verification helps us ensure the security of your account and protect your personal information.
                </p>
                <div className="bg-white/10 rounded-lg p-4">
                  <div className="text-sm space-y-3 text-left">
                    <p className="font-semibold mb-2">Need help?</p>
                    <div className="flex items-start space-x-3">
                      <EnvelopeIcon className="h-5 w-5 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="font-medium">Check your email</p>
                        <p className="text-blue-200 text-xs">Request a new verification link from sign in</p>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default VerifyEmail