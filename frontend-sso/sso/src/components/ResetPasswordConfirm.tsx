import { FC, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Input from './ui/Input'
import Button from './ui/Button'
import Alert from './ui/Alert'
import { LockClosedIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline'

const ResetPasswordConfirm: FC = () => {
  const { confirmPasswordReset } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [formData, setFormData] = useState({ new_password: '', confirm_password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const token = searchParams.get('token') || ''

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    if (formData.new_password !== formData.confirm_password) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      const result = await confirmPasswordReset(token, formData.new_password, formData.confirm_password)
      setSuccess(result.detail)
      setTimeout(() => navigate('/signin'), 2000)
    } catch (err: any) {
      setError(err.message || 'Password reset failed')
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
          <h2 className="text-3xl font-bold text-gray-900">Set New Password</h2>
          <p className="text-gray-600 mt-2">Enter your new password</p>
        </div>

        {error && <Alert type="error" onClose={() => setError('')}>{error}</Alert>}
        {success && <Alert type="success" onClose={() => setSuccess('')}>{success}</Alert>}

        <form onSubmit={handleSubmit}>
          <div className="relative mb-4">
            <Input
              label="New Password"
              type={showPassword ? 'text' : 'password'}
              icon={LockClosedIcon}
              placeholder="Enter new password"
              value={formData.new_password}
              onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-11 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? <EyeSlashIcon className="w-5 h-5" /> : <EyeIcon className="w-5 h-5" />}
            </button>
          </div>
          <Input
            label="Confirm Password"
            type={showPassword ? 'text' : 'password'}
            icon={LockClosedIcon}
            placeholder="Confirm new password"
            value={formData.confirm_password}
            onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
            required
          />
          <Button loading={loading} className="w-full">Reset Password</Button>
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

export default ResetPasswordConfirm