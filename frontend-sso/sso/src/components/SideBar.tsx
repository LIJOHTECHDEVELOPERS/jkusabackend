// components/SideBar.tsx
import { FC } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { HomeIcon, UserIcon, BookOpenIcon, BuildingOffice2Icon, ArrowRightOnRectangleIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface SideBarProps {
  isOpen: boolean;
  onClose: () => void;
}

const SideBar: FC<SideBarProps> = ({ isOpen, onClose }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/signin');
  };

  return (
    <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:relative md:translate-x-0 transition-transform duration-300 ease-in-out flex flex-col`}>
      <div className="flex items-center justify-between p-4 border-b md:hidden">
        <h2 className="text-lg font-bold text-gray-900">Menu</h2>
        <button onClick={onClose} className="p-1 rounded-md hover:bg-gray-100">
          <XMarkIcon className="w-6 h-6 text-gray-600" />
        </button>
      </div>
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          <li>
            <Link to="/dashboard" className="flex items-center gap-3 p-3 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-colors" onClick={onClose}>
              <HomeIcon className="w-5 h-5" />
              <span>Dashboard</span>
            </Link>
          </li>
          <li>
            <Link to="/profile" className="flex items-center gap-3 p-3 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-colors" onClick={onClose}>
              <UserIcon className="w-5 h-5" />
              <span>Profile</span>
            </Link>
          </li>
          <li>
            <Link to="/courses" className="flex items-center gap-3 p-3 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-colors" onClick={onClose}>
              <BookOpenIcon className="w-5 h-5" />
              <span>Courses</span>
            </Link>
          </li>
          <li>
            <Link to="/college" className="flex items-center gap-3 p-3 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600 transition-colors" onClick={onClose}>
              <BuildingOffice2Icon className="w-5 h-5" />
              <span>College</span>
            </Link>
          </li>
        </ul>
      </nav>
      <div className="p-4 border-t">
        <button onClick={handleLogout} className="flex items-center gap-3 p-3 rounded-lg hover:bg-red-50 text-gray-700 hover:text-red-600 transition-colors w-full">
          <ArrowRightOnRectangleIcon className="w-5 h-5" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
};

export default SideBar;