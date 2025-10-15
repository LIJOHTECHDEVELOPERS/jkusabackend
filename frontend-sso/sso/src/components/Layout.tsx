import { FC, ReactNode, useState, useEffect } from 'react'
import Sidebar from './SideBar'
import TopBar from './TopBar'

interface LayoutProps {
  children: ReactNode
  title?: string
}

const Layout: FC<LayoutProps> = ({ children, title }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Close sidebar when clicking outside on mobile
  useEffect(() => {
    if (sidebarOpen && isMobile) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [sidebarOpen, isMobile])

  const handleSidebarClose = () => {
    setSidebarOpen(false)
  }

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen)
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar Component */}
      <Sidebar isOpen={sidebarOpen} onClose={handleSidebarClose} />

      {/* Main Content Wrapper */}
      <div className="flex-1 flex flex-col overflow-hidden w-full lg:w-auto">
        {/* Top Bar Component */}
        <TopBar 
          onMenuClick={handleSidebarToggle} 
          title={title}
        />

        {/* Page Content Area */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden bg-gray-50">
          <div className="min-h-full">
            {children}
          </div>
        </main>

        {/* Footer (Optional) */}
        <footer className="bg-white border-t border-gray-200 py-4 px-4 lg:px-6">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <p className="text-sm text-gray-600">
              © 2025 JKUSA Portal. All rights reserved.
            </p>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <a href="/help" className="hover:text-blue-600 transition-colors">
                Help Center
              </a>
              <span className="text-gray-300">|</span>
              <a href="/privacy" className="hover:text-blue-600 transition-colors">
                Privacy Policy
              </a>
              <span className="text-gray-300">|</span>
              <a href="/terms" className="hover:text-blue-600 transition-colors">
                Terms of Service
              </a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default Layout