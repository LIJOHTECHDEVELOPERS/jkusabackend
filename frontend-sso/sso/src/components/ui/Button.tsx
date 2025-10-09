import { FC, ButtonHTMLAttributes } from 'react'
import { ArrowPathIcon } from '@heroicons/react/24/outline'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean
  variant?: 'primary' | 'secondary' | 'danger'
}

const Button: FC<ButtonProps> = ({ children, loading, variant = 'primary', className = '', ...props }) => {
  const styles = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
    danger: 'bg-red-600 hover:bg-red-700 text-white'
  }

  return (
    <button
      className={`${styles[variant]} px-6 py-3 rounded-lg font-medium transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 ${className}`}
      disabled={loading}
      {...props}
    >
      {loading && <ArrowPathIcon className="w-5 h-5 animate-spin" />}
      {children}
    </button>
  )
}

export default Button