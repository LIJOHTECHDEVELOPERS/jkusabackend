import { FC } from 'react'
import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline'

interface AlertProps {
  type?: 'info' | 'success' | 'error' | 'warning'
  children: React.ReactNode
  onClose?: () => void
}

const Alert: FC<AlertProps> = ({ type = 'info', children, onClose }) => {
  const styles = {
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800'
  }

  const icons = {
    success: <CheckCircleIcon className="w-5 h-5" />,
    error: <ExclamationCircleIcon className="w-5 h-5" />,
    warning: <ExclamationCircleIcon className="w-5 h-5" />,
    info: <ExclamationCircleIcon className="w-5 h-5" />
  }

  return (
    <div className={`border rounded-lg p-4 flex items-start gap-3 mb-4 ${styles[type]}`}>
      <div className="flex-shrink-0 mt-0.5">{icons[type]}</div>
      <div className="flex-1">{children}</div>
      {onClose && (
        <button onClick={onClose} className="flex-shrink-0 text-gray-500 hover:text-gray-700">
          ×
        </button>
      )}
    </div>
  )
}

export default Alert