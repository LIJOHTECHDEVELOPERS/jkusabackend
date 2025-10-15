// pages/Dashboard.tsx (updated)
import { FC } from 'react';
import { useAuth } from '../context/AuthContext';
import { AcademicCapIcon, BuildingOffice2Icon, BookOpenIcon } from '@heroicons/react/24/outline';

const Dashboard: FC = () => {
  const { user } = useAuth();

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
        <div className="flex items-start gap-6">
          <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full flex items-center justify-center text-white text-3xl font-bold">
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </div>
          <div className="flex-1">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Welcome back, {user?.first_name}!
            </h2>
            <p className="text-gray-600 mb-4">{user?.email}</p>
            <div className="flex items-center gap-4 text-sm">
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full font-medium">
                ✓ Verified
              </span>
              <span className="text-gray-500">
                Registration: {user?.registration_number}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <BuildingOffice2Icon className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">College</p>
              <p className="font-semibold text-gray-900">College ID: {user?.college_id}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <BookOpenIcon className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Course</p>
              <p className="font-semibold text-gray-900">{user?.course}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <AcademicCapIcon className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Year of Study</p>
              <p className="font-semibold text-gray-900">Year {user?.year_of_study}</p>
            </div>
          </div>
        </div>
      </div>
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-2xl shadow-lg p-8 text-white">
        <h3 className="text-2xl font-bold mb-4">Account Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-blue-200 text-sm mb-1">Full Name</p>
            <p className="font-medium">{user?.first_name} {user?.last_name}</p>
          </div>
          <div>
            <p className="text-blue-200 text-sm mb-1">Phone Number</p>
            <p className="font-medium">{user?.phone_number}</p>
          </div>
          <div>
            <p className="text-blue-200 text-sm mb-1">Email</p>
            <p className="font-medium">{user?.email}</p>
          </div>
          <div>
            <p className="text-blue-200 text-sm mb-1">Registration Number</p>
            <p className="font-medium">{user?.registration_number}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;