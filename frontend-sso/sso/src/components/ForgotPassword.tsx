import { FC, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Input from './ui/Input'
import Button from './ui/Button'
import Alert from './ui/Alert'
import { EnvelopeIcon, LockClosedIcon } from '@heroicons/react/24/outline'

const ForgotPassword: FC = () => {
  const { requestPasswordReset } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const result = await requestPasswordReset(email)
      setSuccess(result.detail)
    } catch (err: any) {
      setError(err.message || 'Failed to send password reset email')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <LockClosedIcon className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Reset Password</h2>
          <p className="text-gray-600 mt-2">Enter your email to receive a password reset link</p>
        </div>

        {error && <Alert type="error" onClose={() => setError('')}>{error}</Alert>}
        {success && <Alert type="success" onClose={() => setSuccess('')}>{success}</Alert>}

        <form onSubmit={handleSubmit}>
          <Input
            label="Email Address"
            type="email"
            icon={EnvelopeIcon}
            placeholder="Enter your email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Button loading={loading} className="w-full">Send Reset Link</Button>
        </form>
        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Back to{' '}
            <button onClick={() => navigate('/signin')} className="text-blue-600 hover:text-blue-700 font-medium">
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

export default ForgotPassword