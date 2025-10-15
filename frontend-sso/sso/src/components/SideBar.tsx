import { FC } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { 
  AcademicCapIcon,
  HomeIcon,
  UserIcon,
  ChartBarIcon,
  DocumentTextIcon,
  CogIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import { useAuth } from '../context/AuthContext'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const Sidebar: FC<SidebarProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuth()

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: HomeIcon, path: '/dashboard' },
    { id: 'profile', label: 'My Profile', icon: UserIcon, path: '/profile' },
    { id: 'academics', label: 'Academics', icon: AcademicCapIcon, path: '/academics' },
    { id: 'results', label: 'Results', icon: ChartBarIcon, path: '/results' },
    { id: 'documents', label: 'Documents', icon: DocumentTextIcon, path: '/documents' },
    { id: 'settings', label: 'Settings', icon: CogIcon, path: '/settings' },
  ]

  const handleNavigation = (path: string) => {
    navigate(path)
    onClose() // Close sidebar on mobile after navigation
  }

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-200 z-50
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-6 border-b">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center">
                <AcademicCapIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">JKUSA</h1>
                <p className="text-xs text-gray-500">Portal</p>
              </div>
            </div>
            <button onClick={onClose} className="lg:hidden text-gray-500 hover:text-gray-700">
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavigation(item.path)}
                  className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium
                    transition-colors duration-200
                    ${isActive 
                      ? 'bg-blue-50 text-blue-600' 
                      : 'text-gray-700 hover:bg-gray-50'
                    }
                  `}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </button>
              )
            })}
          </nav>

          {/* User Info */}
          <div className="p-4 border-t">
            <div className="flex items-center gap-3 p-3 rounded-xl bg-gray-50">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full flex items-center justify-center text-white text-sm font-bold">
                {user?.first_name?.[0]}{user?.last_name?.[0]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-gray-500 truncate">Student</p>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar