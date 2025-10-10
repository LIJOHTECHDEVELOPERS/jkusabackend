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
  ArrowRightIcon,
  ExclamationTriangleIcon
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

interface SuccessData {
  message: string
  email: string
  emailSent: boolean
}

const JKUSALogo = ({ className = "w-16 h-16" }: { className?: string }) => (
  <img src="images/logo.jpg" alt="JKUSA Logo" className={className} />
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
  const [successData, setSuccessData] = useState<SuccessData | null>(null)
  const [collegesLoading, setCollegesLoading] = useState(false)
  const [schoolsLoading, setSchoolsLoading] = useState(false)
  const [resendLoading, setResendLoading] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)

  useEffect(() => {
    fetchColleges()
  }, [])

  useEffect(() => {
    if (formData.college_id) {
      fetchSchools(formData.college_id)
    } else {
      setSchools([])
      setFormData(prev => ({ ...prev, school_id: '' }))
    }
  }, [formData.college_id])

  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [resendCooldown])

  const fetchColleges = async () => {
    setCollegesLoading(true)
    try {
      const response = await axios.get('https://backend.jkusa.org/students/auth/colleges')
      const collegesData = response.data?.data || response.data
      setColleges(Array.isArray(collegesData) ? collegesData : [])
    } catch (err) {
      console.error('Failed to fetch colleges:', err)
      setColleges([])
    } finally {
      setCollegesLoading(false)
    }
  }

  const fetchSchools = async (collegeId: string) => {
    setSchoolsLoading(true)
    try {
      const response = await axios.get(`https://backend.jkusa.org/students/auth/colleges/${collegeId}/schools`)
      const schoolsData = response.data?.data || response.data
      setSchools(Array.isArray(schoolsData) ? schoolsData : [])
    } catch (err) {
      console.error('Failed to fetch schools:', err)
      setSchools([])
    } finally {
      setSchoolsLoading(false)
    }
  }

  const formatPhoneNumber = (input: string): string => {
    const digits = input.replace(/\D/g, '')
    const cleanDigits = digits.startsWith('0') ? digits.slice(1) : digits
    return `+254${cleanDigits}`
  }

  const handlePhoneChange = (value: string) => {
    const digitsOnly = value.replace(/\D/g, '')
    const maxLength = digitsOnly.startsWith('0') ? 10 : 9
    const limitedValue = digitsOnly.slice(0, maxLength)
    
    setPhoneInput(limitedValue)
    setFormData(prev => ({
      ...prev,
      phone_number: limitedValue.length >= 9 ? formatPhoneNumber(limitedValue) : ''
    }))
  }

  const validateStep = (): boolean => {
    setError('')

    if (step === 1) {
      if (!formData.first_name.trim()) {
        setError('Please enter your first name')
        return false
      }
      if (!formData.last_name.trim()) {
        setError('Please enter your last name')
        return false
      }
      if (!formData.email.trim()) {
        setError('Please enter your email address')
        return false
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        setError('Please enter a valid email address')
        return false
      }
      if (phoneInput.length < 9) {
        setError('Please enter a valid phone number (at least 9 digits)')
        return false
      }
      return true
    }

    if (step === 2) {
      if (!formData.registration_number.trim()) {
        setError('Please enter your registration number')
        return false
      }
      if (!formData.college_id) {
        setError('Please select your college')
        return false
      }
      if (!formData.school_id) {
        setError('Please select your school')
        return false
      }
      if (!formData.course.trim()) {
        setError('Please enter your course/program')
        return false
      }
      return true
    }

    if (step === 3) {
      if (!formData.password) {
        setError('Please enter a password')
        return false
      }
      if (formData.password.length < 8) {
        setError('Password must be at least 8 characters long')
        return false
      }
      if (!/[A-Z]/.test(formData.password)) {
        setError('Password must contain at least one uppercase letter')
        return false
      }
      if (!/[a-z]/.test(formData.password)) {
        setError('Password must contain at least one lowercase letter')
        return false
      }
      if (!/\d/.test(formData.password)) {
        setError('Password must contain at least one number')
        return false
      }
      if (!/[!@#$%^&*(),.?":{}|<>]/.test(formData.password)) {
        setError('Password must contain at least one special character')
        return false
      }
      if (formData.password !== formData.confirm_password) {
        setError('Passwords do not match')
        return false
      }
      return true
    }

    return true
  }

  const handleNext = () => {
    if (validateStep()) {
      setStep(step + 1)
      window.scrollTo(0, 0)
    }
  }

  const handleBack = () => {
    setStep(step - 1)
    setError('')
    window.scrollTo(0, 0)
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

      if (result?.success) {
        setSuccessData({
          message: result.message || 'Registration successful! Please check your email to verify your account.',
          email: result.email || formData.email,
          emailSent: result.email_sent !== false
        })
        setResendCooldown(60)
        window.scrollTo(0, 0)
      } else {
        setError(result?.message || 'Registration failed. Please try again.')
      }
    } catch (err: any) {
      console.error('Registration error:', err)
      
      const errorData = err.response?.data?.detail || err.response?.data || {}
      
      if (typeof errorData === 'object' && errorData.code) {
        const { code, message } = errorData
        
        switch (code) {
          case 'EMAIL_EXISTS':
            setError(message || 'This email is already registered. Please sign in or use a different email.')
            setStep(1)
            break
          case 'REG_NUMBER_EXISTS':
            setError(message || 'This registration number is already in use. Please contact support.')
            setStep(2)
            break
          case 'WEAK_PASSWORD':
            setError(message || 'Password does not meet security requirements.')
            setStep(3)
            break
          case 'INVALID_EMAIL':
            setError(message || 'Please enter a valid email address.')
            setStep(1)
            break
          case 'INVALID_PHONE':
            setError(message || 'Invalid phone number format.')
            setStep(1)
            break
          case 'INVALID_COLLEGE':
            setError(message || 'Please select a valid college.')
            setStep(2)
            break
          case 'INVALID_SCHOOL':
            setError(message || 'Please select a valid school.')
            setStep(2)
            break
          case 'RATE_LIMIT_EXCEEDED':
            setError(message || 'Too many registration attempts. Please wait a minute and try again.')
            break
          case 'MISSING_FIELDS':
            setError(message || 'Please fill in all required fields.')
            break
          default:
            setError(message || 'Registration failed. Please try again.')
        }
      } else {
        setError(err.message || 'An unexpected error occurred. Please try again.')
      }
      
      window.scrollTo(0, 0)
    } finally {
      setLoading(false)
    }
  }

  const handleResendVerification = async () => {
    if (!successData?.email || resendCooldown > 0 || resendLoading) return
    
    setResendLoading(true)
    setError('')
    
    try {
      const result = await resendVerification(successData.email)
      
      if (result?.success) {
        setSuccessData({
          ...successData,
          message: result.message || 'Verification email sent! Please check your inbox.',
          emailSent: result.email_sent !== false
        })
        setResendCooldown(60)
        setError('')
      } else {
        setError(result?.message || 'Failed to resend verification email.')
      }
    } catch (err: any) {
      console.error('Resend verification error:', err)
      const errorData = err.response?.data?.detail || err.response?.data || {}
      setError(errorData.message || 'Failed to resend verification email. Please try again.')
    } finally {
      setResendLoading(false)
    }
  }

  if (successData) {
    return (
      <div className="font-sans min-h-screen flex flex-col lg:flex-row">
        <div className="flex-1 flex items-center justify-center p-4 sm:p-8 bg-gradient-to-br from-gray-50 to-white">
          <div className="w-full max-w-md space-y-6">
            <div className="text-center space-y-4">
              <div className={`w-20 h-20 ${successData.emailSent ? 'bg-green-500' : 'bg-yellow-500'} rounded-full flex items-center justify-center mx-auto shadow-lg`}>
                {successData.emailSent ? (
                  <CheckCircleIcon className="w-10 h-10 text-white" />
                ) : (
                  <ExclamationTriangleIcon className="w-10 h-10 text-white" />
                )}
              </div>
              <h2 className="text-3xl font-bold text-gray-900">
                {successData.emailSent ? 'Registration Successful!' : 'Account Created'}
              </h2>
              <p className="text-gray-600 text-base leading-relaxed">
                {successData.message}
              </p>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <p className="text-sm text-gray-500">Verification email sent to:</p>
                <p className="font-medium text-gray-900">{successData.email}</p>
              </div>
            </div>

            {error && (
              <Alert type="error" onClose={() => setError('')}>
                {error}
              </Alert>
            )}

            <div className={`${successData.emailSent ? 'bg-blue-50 border-blue-200' : 'bg-yellow-50 border-yellow-200'} border rounded-xl p-4`}>
              <div className="space-y-3 text-sm">
                <div className="flex items-center space-x-3">
                  <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0" />
                  <span className="text-gray-700">Account created successfully</span>
                </div>
                <div className="flex items-center space-x-3">
                  {successData.emailSent ? (
                    <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0" />
                  ) : (
                    <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 flex-shrink-0" />
                  )}
                  <span className="text-gray-700">
                    {successData.emailSent ? 'Verification email sent' : 'Email delivery issue - Please resend'}
                  </span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-5 h-5 border-2 border-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
                    <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
                  </div>
                  <span className="text-gray-500">Verify your email to continue</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-xl p-4 text-sm text-gray-600 border border-gray-200">
              <p className="font-medium text-gray-900 mb-3 flex items-center">
                <span className="bg-blue-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs mr-2">!</span>
                Next Steps:
              </p>
              <ul className="space-y-2">
                <li className="flex items-start space-x-2">
                  <span className="text-blue-600 font-bold min-w-[20px]">1.</span>
                  <span>Check your email inbox (and spam/junk folder)</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-blue-600 font-bold min-w-[20px]">2.</span>
                  <span>Click the verification link in the email</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-blue-600 font-bold min-w-[20px]">3.</span>
                  <span>Return to sign in with your credentials</span>
                </li>
              </ul>
            </div>

            <div className="space-y-3">
              <Button onClick={() => navigate('/signin')} className="w-full">
                <div className="flex items-center justify-center space-x-2">
                  <span>Go to Sign In</span>
                  <ArrowRightIcon className="w-4 h-4" />
                </div>
              </Button>

              <div className="text-center">
                <button 
                  onClick={handleResendVerification} 
                  disabled={resendLoading || resendCooldown > 0}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center space-x-1"
                >
                  <EnvelopeIcon className="w-4 h-4" />
                  <span>
                    {resendLoading ? 'Sending...' : resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend Verification Email'}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="hidden lg:flex flex-1 bg-gradient-to-br from-green-600 to-green-800 relative overflow-hidden">
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="relative z-10 flex items-center justify-center p-8 text-white">
            <div className="text-center space-y-6 max-w-md">
              <div className="w-20 h-20 mx-auto bg-white/20 rounded-full flex items-center justify-center shadow-xl">
                <EnvelopeIcon className="h-10 w-10" />
              </div>
              <h3 className="text-3xl font-bold">Welcome to JKUSA!</h3>
              <p className="text-green-100 text-lg leading-relaxed">
                You're one step away from accessing your student portal. Please verify your email to get started.
              </p>
              <div className="bg-white/10 rounded-xl p-5 backdrop-blur-sm">
                <p className="font-semibold mb-3 text-lg">Why verify your email?</p>
                <div className="space-y-3 text-left">
                  <div className="flex items-center space-x-3">
                    <CheckIcon className="h-5 w-5 flex-shrink-0" />
                    <span>Secure your account</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <CheckIcon className="h-5 w-5 flex-shrink-0" />
                    <span>Receive important notifications</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <CheckIcon className="h-5 w-5 flex-shrink-0" />
                    <span>Access all portal features</span>
                  </div>
                </div>
              </div>
              <div className="text-sm text-green-100 bg-white/5 rounded-lg p-4">
                <p className="font-medium mb-1">Need help?</p>
                <p>Contact support if you don't receive the email within 5 minutes.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const getStepInfo = () => {
    const steps = {
      1: {
        title: "Personal Information",
        description: "Let's start with your basic details. This information will be used to create your student profile.",
        icon: UserIcon,
        items: ["Full legal name", "Valid email address", "Contact phone number"]
      },
      2: {
        title: "Academic Details",
        description: "Tell us about your academic background. This helps us customize your portal experience.",
        icon: BookOpenIcon,
        items: ["Official registration number", "College and school information", "Course and year of study"]
      },
      3: {
        title: "Secure Your Account",
        description: "Create a strong password to protect your account and personal information.",
        icon: ShieldCheckIcon,
        items: ["Minimum 8 characters", "Mix of letters and numbers", "At least one special character"]
      }
    }
    return steps[step as keyof typeof steps]
  }

  const stepInfo = getStepInfo()

  return (
    <div className="font-sans min-h-screen flex flex-col lg:flex-row">
      <div className="flex-1 flex items-center justify-center p-4 sm:p-8 bg-gradient-to-br from-gray-50 to-white">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center space-y-2">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <JKUSALogo />
              <div className="text-left">
                <h1 className="text-xl font-bold text-gray-900">JKUSA Portal</h1>
                <p className="text-xs text-gray-600">The Jkuat Student's Community</p>
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Create Your Account</h2>
            <p className="text-gray-600 text-sm">Join the JKUSA community today</p>
          </div>

          <div className="flex items-center justify-center space-x-2">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all ${
                  s === step 
                    ? 'bg-blue-600 text-white ring-4 ring-blue-100 shadow-md' 
                    : s < step 
                    ? 'bg-green-500 text-white shadow' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {s < step ? <CheckIcon className="w-5 h-5" /> : s}
                </div>
                {s < 3 && (
                  <div className={`w-12 h-1 transition-all ${s < step ? 'bg-green-500' : 'bg-gray-200'}`} />
                )}
              </div>
            ))}
          </div>

          <div className="text-center bg-gray-50 rounded-lg p-3 border border-gray-200">
            <h3 className="text-base font-semibold text-gray-900">
              Step {step} of 3: {stepInfo.title}
            </h3>
          </div>

          {error && (
            <Alert type="error" onClose={() => setError('')}>
              {error}
            </Alert>
          )}

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
                    disabled={loading}
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
                    disabled={loading}
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
                  disabled={loading}
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
                      className="w-full pl-28 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all hover:border-gray-400 disabled:bg-gray-100 disabled:cursor-not-allowed"
                      required
                      disabled={loading}
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
                  placeholder="e.g., SCT221-0001/2021"
                  value={formData.registration_number}
                  onChange={(e) => {
                    setFormData({ ...formData, registration_number: e.target.value })
                    setError('')
                  }}
                  required
                  disabled={loading}
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
                    disabled={collegesLoading || loading}
                  >
                    <option value="">{collegesLoading ? 'Loading colleges...' : 'Select your college'}</option>
                    {colleges.map((c) => (
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
                    disabled={!formData.college_id || schoolsLoading || loading}
                  >
                    <option value="">{schoolsLoading ? 'Loading schools...' : 'Select your school'}</option>
                    {schools.map((s) => (
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
                  placeholder="e.g., Bachelor of Science in Computer Science"
                  value={formData.course}
                  onChange={(e) => {
                    setFormData({ ...formData, course: e.target.value })
                    setError('')
                  }}
                  required
                  disabled={loading}
                />
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Year of Study <span className="text-red-500">*</span>
                  </label>
                  <select
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-white text-gray-900 transition-all hover:border-gray-400 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    value={formData.year_of_study}
                    onChange={(e) => {
                      setFormData({ ...formData, year_of_study: e.target.value })
                      setError('')
                    }}
                    required
                    disabled={loading}
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
                    disabled={loading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-11 text-gray-400 hover:text-gray-600 transition-colors"
                    disabled={loading}
                  >
                    {showPassword ? <EyeSlashIcon className="w-5 h-5" /> : <EyeIcon className="w-5 h-5" />}
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
                    disabled={loading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-11 text-gray-400 hover:text-gray-600 transition-colors"
                    disabled={loading}
                  >
                    {showConfirmPassword ? <EyeSlashIcon className="w-5 h-5" /> : <EyeIcon className="w-5 h-5" />}
                  </button>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
                  <p className="font-semibold text-gray-900 mb-3">Password Requirements:</p>
                  <ul className="space-y-2 text-gray-700">
                    <li className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${formData.password.length >= 8 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                      <span className={formData.password.length >= 8 ? 'text-green-700 font-medium' : ''}>At least 8 characters long</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${/[A-Z]/.test(formData.password) && /[a-z]/.test(formData.password) ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                      <span className={/[A-Z]/.test(formData.password) && /[a-z]/.test(formData.password) ? 'text-green-700 font-medium' : ''}>Contains uppercase and lowercase letters</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${/\d/.test(formData.password) ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                      <span className={/\d/.test(formData.password) ? 'text-green-700 font-medium' : ''}>Contains at least one number</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${/[!@#$%^&*(),.?":{}|<>]/.test(formData.password) ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                      <span className={/[!@#$%^&*(),.?":{}|<>]/.test(formData.password) ? 'text-green-700 font-medium' : ''}>Contains at least one special character</span>
                    </li>
                    {formData.confirm_password && (
                      <li className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${formData.password === formData.confirm_password ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        <span className={formData.password === formData.confirm_password ? 'text-green-700 font-medium' : 'text-red-700 font-medium'}>
                          {formData.password === formData.confirm_password ? 'Passwords match' : 'Passwords do not match'}
                        </span>
                      </li>
                    )}
                  </ul>
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-3">
            {step > 1 && (
              <Button
                type="button"
                onClick={handleBack}
                className="flex-1 bg-gray-100 text-gray-700 hover:bg-gray-200"
                disabled={loading}
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
                disabled={loading}
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
                disabled={loading}
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </Button>
            )}
          </div>

          <div className="text-center">
            <p className="text-gray-600 text-sm">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => navigate('/signin')}
                className="text-blue-600 hover:text-blue-700 font-medium transition-colors disabled:opacity-50"
                disabled={loading}
              >
                Sign in here
              </button>
            </p>
          </div>

          <div className="text-center mt-4">
            <div className="inline-flex items-center space-x-2 text-xs text-gray-500">
              <ShieldCheckIcon className="h-4 w-4" />
              <span>Your information is encrypted and secure</span>
            </div>
          </div>
        </div>
      </div>

      <div className="hidden lg:flex flex-1 bg-gradient-to-br from-blue-600 to-blue-800 relative overflow-hidden">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-72 h-72 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-white rounded-full blur-3xl"></div>
        </div>
        <div className="relative z-10 flex items-center justify-center p-8 text-white">
          <div className="text-center space-y-6 max-w-md">
            <div className="w-20 h-20 mx-auto bg-white/20 rounded-full flex items-center justify-center shadow-xl backdrop-blur-sm">
              {stepInfo && <stepInfo.icon className="h-10 w-10" />}
            </div>
            <h3 className="text-3xl font-bold">{stepInfo?.title}</h3>
            <p className="text-blue-100 text-lg leading-relaxed">
              {stepInfo?.description}
            </p>
            <div className="grid grid-cols-1 gap-4 text-left bg-white/10 rounded-xl p-5 backdrop-blur-sm">
              {stepInfo?.items.map((item, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <CheckIcon className="h-5 w-5 text-green-400 flex-shrink-0" />
                  <span className="text-sm">{item}</span>
                </div>
              ))}
            </div>
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
              <div className="flex items-center justify-center space-x-2 text-sm">
                <ShieldCheckIcon className="h-5 w-5 text-green-400" />
                <span>Your information is encrypted and secure</span>
              </div>
            </div>
            <div className="flex items-center justify-center space-x-1 text-sm text-blue-100">
              <span>Step {step} of 3</span>
              <span className="mx-2">•</span>
              <span>{Math.round((step / 3) * 100)}% Complete</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SignUp