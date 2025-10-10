import { FC, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Input from './ui/Input'
import Button from './ui/Button'
import Alert from './ui/Alert'
import { 
  UserIcon, 
  EnvelopeIcon, 
  PhoneIcon, 
  BookOpenIcon, 
  LockClosedIcon, 
  EyeIcon, 
  EyeSlashIcon, 
  CheckCircleIcon,
  ShieldCheckIcon,
  CheckIcon,
  ArrowLeftIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline'
import axios from 'axios'

interface College {
  id: number
  name: string
}

interface School {
  id: number
  name: string
  college_id: number
}

// Logo Component - Updated to use actual JKUSA logo
const JKUSALogo = ({ className = "w-16 h-16" }: { className?: string }) => (
  <img
    src="images/logo.jpg"
    alt="JKUSA Logo"
    className={className}
  />
)

const SignUp: FC = () => {
  const { register, resendVerification } = useAuth()
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [colleges, setColleges] = useState<College[]>([])
  const [schools, setSchools] = useState<School[]>([])
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    registration_number: '',
    college_id: '',
    school_id: '',
    course: '',
    year_of_study: '1',
    password: '',
    confirm_password: ''
  })
  const [phoneInput, setPhoneInput] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [collegesLoading, setCollegesLoading] = useState(false)
  const [schoolsLoading, setSchoolsLoading] = useState(false)

  useEffect(() => {
    fetchColleges()
  }, [])

  useEffect(() => {
    if (formData.college_id) {
      fetchSchools(formData.college_id)
    } else {
      setSchools([])
    }
  }, [formData.college_id])

  const fetchColleges = async () => {
    setCollegesLoading(true)
    try {
      const response = await axios.get('https://backend.jkusa.org/students/auth/colleges')
      // Ensure we always set an array
      if (Array.isArray(response.data)) {
        setColleges(response.data)
      } else {
        console.error('Invalid colleges data format:', response.data)
        setColleges([])
      }
    } catch (err) {
      console.error('Failed to fetch colleges:', err)
      setColleges([]) // Ensure colleges is always an array
    } finally {
      setCollegesLoading(false)
    }
  }

  const fetchSchools = async (collegeId: string) => {
    setSchoolsLoading(true)
    try {
      const response = await axios.get(`https://backend.jkusa.org/students/auth/colleges/${collegeId}/schools`)
      // Ensure we always set an array
      if (Array.isArray(response.data)) {
        setSchools(response.data)
      } else {
        console.error('Invalid schools data format:', response.data)
        setSchools([])
      }
    } catch (err) {
      console.error('Failed to fetch schools:', err)
      setSchools([]) // Ensure schools is always an array
    } finally {
      setSchoolsLoading(false)
    }
  }

  const formatPhoneNumber = (input: string): string => {
    // Remove all non-digits
    const digits = input.replace(/\D/g, '')
    
    // If starts with 0, remove it
    const cleanDigits = digits.startsWith('0') ? digits.slice(1) : digits
    
    // Return with country code
    return `+254${cleanDigits}`
  }

  const handlePhoneChange = (value: string) => {
    // Only allow digits
    const digitsOnly = value.replace(/\D/g, '')
    
    // Limit to 10 digits (or 9 if they don't include the leading 0)
    const maxLength = digitsOnly.startsWith('0') ? 10 : 9
    const limitedValue = digitsOnly.slice(0, maxLength)
    
    setPhoneInput(limitedValue)
    
    // Update formData with formatted number
    if (limitedValue.length >= 9) {
      setFormData({ ...formData, phone_number: formatPhoneNumber(limitedValue) })
    } else {
      setFormData({ ...formData, phone_number: '' })
    }
  }

  const validateStep = (): boolean => {
    if (step === 1) {
      if (!formData.first_name || !formData.last_name || !formData.email || !formData.phone_number) {
        setError('Please fill in all personal information fields')
        return false
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        setError('Please enter a valid email address')
        return false
      }
      if (phoneInput.length < 9) {
        setError('Please enter a valid phone number')
        return false
      }
    } else if (step === 2) {
      if (!formData.registration_number || !formData.college_id || !formData.school_id || !formData.course) {
        setError('Please fill in all academic information fields')
        return false
      }
    } else if (step === 3) {
      if (formData.password !== formData.confirm_password) {
        setError('Passwords do not match')
        return false
      }
      if (formData.password.length < 8) {
        setError('Password must be at least 8 characters long')
        return false
      }
    }
    setError('')
    return true
  }

  const handleNext = () => {
    if (validateStep()) {
      setStep(step + 1)
    }
  }

  const handleSubmit = async () => {
    if (!validateStep()) return
    setLoading(true)
    setError('')

    try {
      const { confirm_password, ...registrationData } = formData
      const result = await register({
        ...registrationData,
        college_id: parseInt(registrationData.college_id),
        school_id: parseInt(registrationData.school_id),
        year_of_study: parseInt(registrationData.year_of_study)
      })
      setSuccess(result.detail)
    } catch (err: any) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const handleResendVerification = async () => {
    try {
      await resendVerification(formData.email)
      setSuccess('Verification email resent. Please check your inbox.')
    } catch (err: any) {
      setError(err.message || 'Failed to resend verification email')
    }
  }

  // Success State
  if (success) {
    return (
      <div className="font-sans min-h-screen flex flex-col lg:flex-row">
        {/* Left Side - Success Message */}
        <div className="flex-1 flex items-center justify-center p-4 sm:p-8 bg-gradient-to-br from-gray-50 to-white">
          <div className="w-full max-w-md space-y-6">
            <div className="text-center space-y-4">
              <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto">
                <CheckCircleIcon className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-3xl font-bold text-gray-900">Registration Successful!</h2>
              <p className="text-gray-600 text-base leading-relaxed">
                {success}
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div className="space-y-3 text-sm">
                <div className="flex items-center space-x-3">
                  <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0" />
                  <span className="text-gray-700">Account created successfully</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0" />
                  <span className="text-gray-700">Verification email sent</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-5 h-5 border-2 border-gray-300 rounded-full flex-shrink-0"></div>
                  <span className="text-gray-500">Verify your email to continue</span>
                </div>
              </div>
            </div>

            <Button onClick={() => navigate('/signin')} className="w-full">
              Go to Sign In
            </Button>

            <div className="text-center">
              <button 
                onClick={handleResendVerification} 
                className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                Resend Verification Email
              </button>
            </div>
          </div>
        </div>

        {/* Right Side - Info Panel */}
        <div className="hidden lg:flex flex-1 bg-gradient-to-br from-green-600 to-green-800 relative overflow-hidden">
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="relative z-10 flex items-center justify-center p-8 text-white">
            <div className="text-center space-y-6 max-w-md">
              <div className="w-16 h-16 mx-auto bg-white/20 rounded-full flex items-center justify-center">
                <CheckCircleIcon className="h-8 w-8" />
              </div>
              <h3 className="text-2xl font-bold">Welcome to JKUSA!</h3>
              <p className="text-green-100 text-base leading-relaxed">
                You're one step away from accessing your student portal. Please verify your email to get started.
              </p>
              <div className="bg-white/10 rounded-lg p-4">
                <div className="text-sm space-y-3 text-left">
                  <p className="font-semibold mb-2">Next Steps:</p>
                  <div className="flex items-center space-x-3">
                    <div className="w-6 h-6 bg-white text-green-700 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">1</div>
                    <span>Check your email inbox</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-6 h-6 bg-white text-green-700 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">2</div>
                    <span>Click the verification link</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-6 h-6 bg-white text-green-700 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">3</div>
                    <span>Sign in to your account</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Get step info for right panel
  const getStepInfo = () => {
    switch (step) {
      case 1:
        return {
          title: "Personal Information",
          description: "Let's start with your basic details. This information will be used to create your student profile.",
          icon: UserIcon,
          items: [
            "Full legal name",
            "Valid email address",
            "Contact phone number"
          ]
        }
      case 2:
        return {
          title: "Academic Details",
          description: "Tell us about your academic background. This helps us customize your portal experience.",
          icon: BookOpenIcon,
          items: [
            "Official registration number",
            "College and school information",
            "Course and year of study"
          ]
        }
      case 3:
        return {
          title: "Secure Your Account",
          description: "Create a strong password to protect your account and personal information.",
          icon: ShieldCheckIcon,
          items: [
            "Minimum 8 characters",
            "Mix of letters and numbers",
            "At least one special character"
          ]
        }
      default:
        return null
    }
  }

  const stepInfo = getStepInfo()

  return (
    <div className="font-sans min-h-screen flex flex-col lg:flex-row">
      {/* Left Side - Form */}
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
            <h2 className="text-2xl font-bold text-gray-900">Create Your Account</h2>
            <p className="text-gray-600 text-sm">
              Join the JKUSA community today
            </p>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center justify-center space-x-2">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all ${
                  s === step 
                    ? 'bg-blue-600 text-white ring-4 ring-blue-100' 
                    : s < step 
                    ? 'bg-green-500 text-white' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {s < step ? <CheckIcon className="w-5 h-5" /> : s}
                </div>
                {s < 3 && (
                  <div className={`w-12 h-1 transition-all ${
                    s < step ? 'bg-green-500' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>

          {/* Step Title */}
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900">
              Step {step} of 3: {stepInfo?.title}
            </h3>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert type="error" onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          {/* Form Content */}
          <div className="space-y-4">
            {step === 1 && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="First Name"
                    type="text"
                    icon={UserIcon}
                    placeholder="Enter first name"
                    value={formData.first_name}
                    onChange={(e) => {
                      setFormData({ ...formData, first_name: e.target.value })
                      setError('')
                    }}
                    required
                  />
                  <Input
                    label="Last Name"
                    type="text"
                    icon={UserIcon}
                    placeholder="Enter last name"
                    value={formData.last_name}
                    onChange={(e) => {
                      setFormData({ ...formData, last_name: e.target.value })
                      setError('')
                    }}
                    required
                  />
                </div>
                <Input
                  label="Email Address"
                  type="email"
                  icon={EnvelopeIcon}
                  placeholder="your.email@example.com"
                  value={formData.email}
                  onChange={(e) => {
                    setFormData({ ...formData, email: e.target.value })
                    setError('')
                  }}
                  required
                />
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Phone Number <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center space-x-2 pointer-events-none">
                      <PhoneIcon className="w-5 h-5 text-gray-400" />
                      <span className="text-gray-600 font-medium">+254</span>
                      <div className="w-px h-5 bg-gray-300"></div>
                    </div>
                    <input
                      type="tel"
                      placeholder="712345678 or 0712345678"
                      value={phoneInput}
                      onChange={(e) => {
                        handlePhoneChange(e.target.value)
                        setError('')
                      }}
                      className="w-full pl-28 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all hover:border-gray-400"
                      required
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Enter 9 digits (e.g., 706400432) or 10 digits starting with 0
                  </p>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <Input
                  label="Registration Number"
                  type="text"
                  icon={BookOpenIcon}
                  placeholder="Enter your reg number"
                  value={formData.registration_number}
                  onChange={(e) => {
                    setFormData({ ...formData, registration_number: e.target.value })
                    setError('')
                  }}
                  required
                />
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    College <span className="text-red-500">*</span>
                  </label>
                  <select
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white text-gray-900 transition-all hover:border-gray-400 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    value={formData.college_id}
                    onChange={(e) => {
                      setFormData({ ...formData, college_id: e.target.value, school_id: '' })
                      setError('')
                    }}
                    required
                    disabled={collegesLoading}
                  >
                    <option value="">
                      {collegesLoading ? 'Loading colleges...' : 'Select your college'}
                    </option>
                    {Array.isArray(colleges) && colleges.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                  {!collegesLoading && colleges.length === 0 && (
                    <p className="text-xs text-red-500 mt-1">Failed to load colleges. Please refresh the page.</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    School <span className="text-red-500">*</span>
                  </label>
                  <select
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white text-gray-900 transition-all hover:border-gray-400 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    value={formData.school_id}
                    onChange={(e) => {
                      setFormData({ ...formData, school_id: e.target.value })
                      setError('')
                    }}
                    required
                    disabled={!formData.college_id || schoolsLoading}
                  >
                    <option value="">
                      {schoolsLoading ? 'Loading schools...' : 'Select your school'}
                    </option>
                    {Array.isArray(schools) && schools.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                  {!formData.college_id && (
                    <p className="text-xs text-gray-500 mt-1">Please select a college first</p>
                  )}
                </div>
                <Input
                  label="Course/Program"
                  type="text"
                  icon={BookOpenIcon}
                  placeholder="e.g., Computer Science"
                  value={formData.course}
                  onChange={(e) => {
                    setFormData({ ...formData, course: e.target.value })
                    setError('')
                  }}
                  required
                />
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Year of Study <span className="text-red-500">*</span>
                  </label>
                  <select
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white text-gray-900 transition-all hover:border-gray-400"
                    value={formData.year_of_study}
                    onChange={(e) => {
                      setFormData({ ...formData, year_of_study: e.target.value })
                      setError('')
                    }}
                    required
                  >
                    {[1, 2, 3, 4, 5, 6].map((year) => (
                      <option key={year} value={year}>Year {year}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <div className="relative">
                  <Input
                    label="Password"
                    type={showPassword ? 'text' : 'password'}
                    icon={LockClosedIcon}
                    placeholder="Create a strong password"
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
                <div className="relative">
                  <Input
                    label="Confirm Password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    icon={LockClosedIcon}
                    placeholder="Re-enter your password"
                    value={formData.confirm_password}
                    onChange={(e) => {
                      setFormData({ ...formData, confirm_password: e.target.value })
                      setError('')
                    }}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-11 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    {showConfirmPassword ? (
                      <EyeSlashIcon className="w-5 h-5" />
                    ) : (
                      <EyeIcon className="w-5 h-5" />
                    )}
                  </button>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
                  <p className="font-semibold text-gray-900 mb-2">Password Requirements:</p>
                  <ul className="space-y-1 text-gray-700">
                    <li className="flex items-center space-x-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${formData.password.length >= 8 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                      <span>At least 8 characters long</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${/[A-Z]/.test(formData.password) && /[a-z]/.test(formData.password) ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                      <span>Contains uppercase and lowercase letters</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${/\d/.test(formData.password) ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                      <span>Contains at least one number</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${/[!@#$%^&*(),.?":{}|<>]/.test(formData.password) ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                      <span>Contains at least one special character</span>
                    </li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Navigation Buttons */}
          <div className="flex gap-3">
            {step > 1 && (
              <Button
                type="button"
                onClick={() => setStep(step - 1)}
                className="flex-1 bg-gray-100 text-gray-700 hover:bg-gray-200"
              >
                <div className="flex items-center justify-center space-x-2">
                  <ArrowLeftIcon className="w-4 h-4" />
                  <span>Back</span>
                </div>
              </Button>
            )}
            {step < 3 ? (
              <Button
                type="button"
                onClick={handleNext}
                className="flex-1"
              >
                <div className="flex items-center justify-center space-x-2">
                  <span>Next</span>
                  <ArrowRightIcon className="w-4 h-4" />
                </div>
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                loading={loading}
                className="flex-1"
              >
                Create Account
              </Button>
            )}
          </div>

          {/* Sign-In Link */}
          <div className="text-center">
            <p className="text-gray-600 text-sm">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => navigate('/signin')}
                className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
              >
                Sign in here
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
              {stepInfo && <stepInfo.icon className="h-8 w-8" />}
            </div>
            <h3 className="text-2xl font-bold">{stepInfo?.title}</h3>
            <p className="text-blue-100 text-base leading-relaxed">
              {stepInfo?.description}
            </p>
            <div className="grid grid-cols-1 gap-4 text-left">
              {stepInfo?.items.map((item, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <CheckIcon className="h-5 w-5 text-green-400 flex-shrink-0" />
                  <span className="text-sm">{item}</span>
                </div>
              ))}
            </div>
            <div className="bg-white/10 rounded-lg p-4 mt-6">
              <div className="flex items-center justify-center space-x-2 text-sm">
                <ShieldCheckIcon className="h-5 w-5 text-green-400" />
                <span>Your information is encrypted and secure</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SignUp