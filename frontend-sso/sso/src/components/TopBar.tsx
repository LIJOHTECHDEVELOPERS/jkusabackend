// components/TopBar.tsx
import { FC, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from './ui/Button';
import { AcademicCapIcon, Bars3Icon } from '@heroicons/react/24/outline';

interface TopBarProps {
  onSidebarToggle: () => void;
}

const TopBar: FC<TopBarProps> = ({ onSidebarToggle }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onSidebarToggle}
            className="md:hidden p-2 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <Bars3Icon className="w-6 h-6 text-gray-600" />
          </button>
          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
            <AcademicCapIcon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">JKUSA Portal</h1>
            <p className="text-xs text-gray-500">Student Dashboard</p>
          </div>
        </div>
        <Button onClick={async () => { await logout(); navigate('/signin'); }} variant="secondary">
          Logout
        </Button>
      </div>
    </nav>
  );
};

export default TopBar;