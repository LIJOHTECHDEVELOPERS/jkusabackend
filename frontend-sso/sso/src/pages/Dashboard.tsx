import { FC } from 'react'
import { useAuth } from '../context/AuthContext'
import { 
  AcademicCapIcon, 
  BuildingOffice2Icon, 
  BookOpenIcon,
  ChartBarIcon,
  ClockIcon,
  CalendarIcon,
  DocumentTextIcon,
  CurrencyDollarIcon,
  UserGroupIcon,
  ArrowTrendingUpIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline'
import Layout from '../components/Layout'

const Dashboard: FC = () => {
  const { user } = useAuth()

  // Mock data for dashboard
  const upcomingEvents = [
    { 
      id: 1, 
      title: 'Mathematics Exam', 
      date: 'Oct 20, 2025', 
      time: '9:00 AM',
      type: 'exam',
      location: 'Room 301' 
    },
    { 
      id: 2, 
      title: 'Physics Assignment Due', 
      date: 'Oct 18, 2025', 
      time: '11:59 PM',
      type: 'assignment',
      location: 'Online Submission' 
    },
    { 
      id: 3, 
      title: 'Project Presentation', 
      date: 'Oct 22, 2025', 
      time: '2:00 PM',
      type: 'presentation',
      location: 'Lab 4' 
    },
    { 
      id: 4, 
      title: 'Group Study Session', 
      date: 'Oct 17, 2025', 
      time: '4:00 PM',
      type: 'study',
      location: 'Library' 
    },
  ]

  const quickStats = [
    { 
      label: 'Current GPA', 
      value: '3.85', 
      change: '+0.12',
      trend: 'up',
      color: 'green',
      icon: ChartBarIcon 
    },
    { 
      label: 'Active Courses', 
      value: '6', 
      change: 'This Semester',
      trend: 'neutral',
      color: 'blue',
      icon: BookOpenIcon 
    },
    { 
      label: 'Attendance', 
      value: '92%', 
      change: '+3%',
      trend: 'up',
      color: 'purple',
      icon: CheckCircleIcon 
    },
    { 
      label: 'Pending Tasks', 
      value: '4', 
      change: '2 Due Soon',
      trend: 'down',
      color: 'orange',
      icon: ExclamationCircleIcon 
    },
  ]

  const recentActivities = [
    {
      id: 1,
      title: 'Completed Data Structures Assignment',
      description: 'Submitted Lab Report #5',
      time: '2 hours ago',
      type: 'assignment',
      icon: DocumentTextIcon,
      color: 'blue'
    },
    {
      id: 2,
      title: 'Attended Physics Lab Session',
      description: 'Practical: Wave Motion Experiment',
      time: '1 day ago',
      type: 'attendance',
      icon: ClockIcon,
      color: 'green'
    },
    {
      id: 3,
      title: 'Exam Results Published',
      description: 'Database Management Systems - A',
      time: '3 days ago',
      type: 'result',
      icon: ChartBarIcon,
      color: 'purple'
    },
    {
      id: 4,
      title: 'Library Book Borrowed',
      description: 'Introduction to Algorithms (3rd Ed)',
      time: '5 days ago',
      type: 'library',
      icon: BookOpenIcon,
      color: 'orange'
    },
  ]

  const courseProgress = [
    { name: 'Data Structures', progress: 85, color: 'blue' },
    { name: 'Web Development', progress: 72, color: 'green' },
    { name: 'Database Systems', progress: 90, color: 'purple' },
    { name: 'Computer Networks', progress: 65, color: 'orange' },
  ]

  const announcements = [
    {
      id: 1,
      title: 'Mid-Semester Break',
      message: 'Campus will be closed from Oct 25-29',
      priority: 'high',
      date: 'Oct 15, 2025'
    },
    {
      id: 2,
      title: 'Registration for Next Semester',
      message: 'Online registration opens Nov 1st',
      priority: 'medium',
      date: 'Oct 14, 2025'
    },
    {
      id: 3,
      title: 'Career Fair 2025',
      message: 'Top companies recruiting on campus',
      priority: 'low',
      date: 'Oct 12, 2025'
    },
  ]

  return (
    <Layout title="Dashboard">
      <div className="max-w-7xl mx-auto px-4 py-6 lg:py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 mb-2">
            Welcome back, {user?.first_name}! 👋
          </h2>
          <p className="text-gray-600">
            Here's what's happening with your studies today. Keep up the great work!
          </p>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {quickStats.map((stat, index) => {
            const Icon = stat.icon
            return (
              <div 
                key={index} 
                className="bg-white rounded-xl shadow-sm p-5 border border-gray-100 hover:shadow-md transition-all duration-300"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`w-12 h-12 bg-${stat.color}-100 rounded-xl flex items-center justify-center`}>
                    <Icon className={`w-6 h-6 text-${stat.color}-600`} />
                  </div>
                  {stat.trend === 'up' && (
                    <span className="text-green-600 text-xs font-medium bg-green-50 px-2 py-1 rounded-full">
                      {stat.change}
                    </span>
                  )}
                  {stat.trend === 'down' && (
                    <span className="text-orange-600 text-xs font-medium bg-orange-50 px-2 py-1 rounded-full">
                      {stat.change}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500 mb-1">{stat.label}</p>
                <p className={`text-3xl font-bold text-${stat.color}-600`}>{stat.value}</p>
                {stat.trend === 'neutral' && (
                  <p className="text-xs text-gray-400 mt-1">{stat.change}</p>
                )}
              </div>
            )
          })}
        </div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - 2/3 width */}
          <div className="lg:col-span-2 space-y-6">
            {/* Profile Card */}
            <div className="bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 rounded-2xl shadow-lg p-6 lg:p-8 text-white">
              <div className="flex flex-col sm:flex-row items-start gap-4 mb-6">
                <div className="w-20 h-20 sm:w-24 sm:h-24 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center text-white text-2xl sm:text-3xl font-bold border-2 border-white/30 flex-shrink-0">
                  {user?.first_name?.[0]}{user?.last_name?.[0]}
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl lg:text-3xl font-bold mb-2">
                    {user?.first_name} {user?.last_name}
                  </h3>
                  <p className="text-blue-100 text-sm mb-3">{user?.email}</p>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-500/90 text-white rounded-full text-xs font-medium">
                      <CheckCircleIcon className="w-4 h-4" />
                      Verified Student
                    </span>
                    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/20 backdrop-blur-sm text-white rounded-full text-xs font-medium">
                      <UserGroupIcon className="w-4 h-4" />
                      Year {user?.year_of_study}
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3">
                  <p className="text-blue-200 text-xs mb-1">Registration Number</p>
                  <p className="font-semibold text-sm">{user?.registration_number}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3">
                  <p className="text-blue-200 text-xs mb-1">Phone Number</p>
                  <p className="font-semibold text-sm">{user?.phone_number}</p>
                </div>
              </div>
            </div>

            {/* Academic Info Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100 hover:shadow-md transition-all duration-300 hover:border-blue-200">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <BuildingOffice2Icon className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-500 mb-1">College ID</p>
                    <p className="font-semibold text-gray-900 text-sm truncate">
                      {user?.college_id}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100 hover:shadow-md transition-all duration-300 hover:border-purple-200">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <BookOpenIcon className="w-6 h-6 text-purple-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-500 mb-1">Course</p>
                    <p className="font-semibold text-gray-900 text-sm truncate">
                      {user?.course}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100 hover:shadow-md transition-all duration-300 hover:border-green-200">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <AcademicCapIcon className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-500 mb-1">Year of Study</p>
                    <p className="font-semibold text-gray-900 text-sm">
                      Year {user?.year_of_study}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Course Progress */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold text-gray-900">Course Progress</h3>
                <ArrowTrendingUpIcon className="w-5 h-5 text-gray-400" />
              </div>
              <div className="space-y-4">
                {courseProgress.map((course, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900">{course.name}</span>
                      <span className={`text-sm font-bold text-${course.color}-600`}>
                        {course.progress}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div 
                        className={`bg-${course.color}-600 h-2.5 rounded-full transition-all duration-500`}
                        style={{ width: `${course.progress}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold text-gray-900">Recent Activity</h3>
                <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                  View All
                </button>
              </div>
              <div className="space-y-4">
                {recentActivities.map((activity, index) => {
                  const Icon = activity.icon
                  return (
                    <div 
                      key={activity.id} 
                      className={`flex items-start gap-4 ${
                        index !== recentActivities.length - 1 ? 'pb-4 border-b border-gray-100' : ''
                      }`}
                    >
                      <div className={`w-10 h-10 bg-${activity.color}-100 rounded-lg flex items-center justify-center flex-shrink-0`}>
                        <Icon className={`w-5 h-5 text-${activity.color}-600`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                        <p className="text-xs text-gray-600 mt-1">{activity.description}</p>
                        <p className="text-xs text-gray-400 mt-1">{activity.time}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Right Column - 1/3 width */}
          <div className="space-y-6">
            {/* Upcoming Events */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold text-gray-900">Upcoming Events</h3>
                <CalendarIcon className="w-5 h-5 text-gray-400" />
              </div>
              <div className="space-y-3">
                {upcomingEvents.map((event) => (
                  <div 
                    key={event.id}
                    className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all cursor-pointer group"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                        event.type === 'exam' ? 'bg-red-500' :
                        event.type === 'assignment' ? 'bg-orange-500' :
                        event.type === 'presentation' ? 'bg-blue-500' :
                        'bg-green-500'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                          {event.title}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">{event.date} • {event.time}</p>
                        <p className="text-xs text-gray-400 mt-1">{event.location}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <button className="w-full mt-4 py-2.5 text-sm text-blue-600 hover:text-blue-700 font-medium hover:bg-blue-50 rounded-lg transition-colors">
                View Calendar
              </button>
            </div>

            {/* Announcements */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold text-gray-900">Announcements</h3>
                <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              </div>
              <div className="space-y-3">
                {announcements.map((announcement) => (
                  <div 
                    key={announcement.id}
                    className="p-4 rounded-lg border transition-all cursor-pointer"
                    style={{
                      borderColor: announcement.priority === 'high' ? '#fee2e2' : 
                                   announcement.priority === 'medium' ? '#fef3c7' : '#e5e7eb',
                      backgroundColor: announcement.priority === 'high' ? '#fef2f2' : 
                                      announcement.priority === 'medium' ? '#fffbeb' : '#f9fafb'
                    }}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <p className="text-sm font-medium text-gray-900 flex-1">
                        {announcement.title}
                      </p>
                      {announcement.priority === 'high' && (
                        <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full flex-shrink-0">
                          Important
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mb-2">{announcement.message}</p>
                    <p className="text-xs text-gray-400">{announcement.date}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <CalendarIcon className="w-4 h-4" />
                  View Timetable
                </button>
                <button className="w-full py-3 px-4 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <ChartBarIcon className="w-4 h-4" />
                  Check Results
                </button>
                <button className="w-full py-3 px-4 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <BookOpenIcon className="w-4 h-4" />
                  Library Resources
                </button>
                <button className="w-full py-3 px-4 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <CurrencyDollarIcon className="w-4 h-4" />
                  Pay Fees
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default Dashboard