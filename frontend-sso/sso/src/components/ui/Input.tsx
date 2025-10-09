import { FC, InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  icon?: React.ComponentType<{ className?: string }>
}

const Input: FC<InputProps> = ({ label, error, icon: Icon, className = '', ...props }) => (
  <div className="mb-4">
    {label && <label className="block text-sm font-medium text-gray-900 mb-2">{label}</label>}
    <div className="relative">
      {Icon && (
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
          <Icon className="w-5 h-5" />
        </div>
      )}
      <input
        className={`w-full ${Icon ? 'pl-10' : 'pl-4'} pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition bg-white text-black placeholder-gray-400 ${error ? 'border-red-500' : 'border-gray-300'} ${className}`}
        {...props}
      />
    </div>
    {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
  </div>
)

export default Input