import { FC, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
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
  ExclamationCircleIcon,
  TicketIcon,
  SpeakerWaveIcon,
  BellAlertIcon,
  UsersIcon
} from '@heroicons/react/24/outline'
import Layout from '../components/Layout'

const Dashboard: FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()

  // Redirect to signin if user is not authenticated
  useEffect(() => {
    if (!user) {
      navigate('/signin')
    }
  }, [user, navigate])

  const quickStats = [
    { 
      label: 'Events Registered', 
      value: '5', 
      change: '2 Upcoming',
      trend: 'up',
      color: 'green',
      icon: CheckCircleIcon 
    },
    { 
      label: 'Available Events', 
      value: '12', 
      change: 'This Month',
      trend: 'neutral',
      color: 'blue',
      icon: CalendarIcon 
    },
    { 
      label: 'Active Membership', 
      value: 'Gold', 
      change: 'Valid Till Dec',
      trend: 'neutral',
      color: 'purple',
      icon: TicketIcon 
    },
    { 
      label: 'Community Points', 
      value: '850', 
      change: '+120',
      trend: 'up',
      color: 'orange',
      icon: ArrowTrendingUpIcon 
    },
  ]

  const eventsRegistered = [
    { 
      id: 1, 
      title: 'JKUSA Annual Leadership Summit', 
      date: 'Oct 22, 2025', 
      time: '9:00 AM',
      location: 'Main Auditorium',
      status: 'confirmed',
      category: 'Leadership'
    },
    { 
      id: 2, 
      title: 'Tech Innovation Workshop', 
      date: 'Oct 25, 2025', 
      time: '2:00 PM',
      location: 'ICT Lab B',
      status: 'confirmed',
      category: 'Technology'
    },
    { 
      id: 3, 
      title: 'Career Fair & Mentorship Day', 
      date: 'Nov 5, 2025', 
      time: '10:00 AM',
      location: 'Student Center',
      status: 'waitlist',
      category: 'Career'
    },
    { 
      id: 4, 
      title: 'Cultural Night Celebration', 
      date: 'Nov 12, 2025', 
      time: '6:00 PM',
      location: 'Open Grounds',
      status: 'confirmed',
      category: 'Cultural'
    },
  ]

  const availableEvents = [
    {
      id: 5,
      title: 'Sports Day Extravaganza',
      date: 'Oct 28, 2025',
      time: '8:00 AM',
      location: 'Sports Complex',
      spotsLeft: 45,
      totalSpots: 100,
      category: 'Sports',
      fee: 'Free'
    },
    {
      id: 6,
      title: 'Entrepreneurship Bootcamp',
      date: 'Nov 2, 2025',
      time: '1:00 PM',
      location: 'Business Lab',
      spotsLeft: 12,
      totalSpots: 30,
      category: 'Business',
      fee: 'KES 500'
    },
    {
      id: 7,
      title: 'Environmental Conservation Drive',
      date: 'Nov 8, 2025',
      time: '7:00 AM',
      location: 'Campus Grounds',
      spotsLeft: 78,
      totalSpots: 150,
      category: 'Community',
      fee: 'Free'
    },
    {
      id: 8,
      title: 'Mental Health Awareness Seminar',
      date: 'Nov 10, 2025',
      time: '3:00 PM',
      location: 'Conference Hall',
      spotsLeft: 23,
      totalSpots: 50,
      category: 'Wellness',
      fee: 'Free'
    },
    {
      id: 9,
      title: 'Music & Arts Festival',
      date: 'Nov 18, 2025',
      time: '5:00 PM',
      location: 'Student Arena',
      spotsLeft: 156,
      totalSpots: 200,
      category: 'Cultural',
      fee: 'KES 300'
    },
  ]

  const announcements = [
    {
      id: 1,
      title: 'JKUSA Elections 2025 Nominations Open',
      message: 'Submit your nomination papers by October 30th. Be part of the change!',
      priority: 'high',
      date: 'Oct 14, 2025',
      category: 'Elections'
    },
    {
      id: 2,
      title: 'New Student Welfare Program Launched',
      message: 'Free counseling sessions now available every Tuesday and Thursday',
      priority: 'high',
      date: 'Oct 13, 2025',
      category: 'Welfare'
    },
    {
      id: 3,
      title: 'Campus Wi-Fi Upgrade Complete',
      message: 'Enjoy faster internet speeds across all campus zones',
      priority: 'medium',
      date: 'Oct 12, 2025',
      category: 'Infrastructure'
    },
    {
      id: 4,
      title: 'JKUSA Scholarship Applications',
      message: 'Apply for academic excellence scholarships. Deadline: Nov 15th',
      priority: 'high',
      date: 'Oct 10, 2025',
      category: 'Scholarships'
    },
    {
      id: 5,
      title: 'New Partnership with Local Businesses',
      message: 'Student discount cards now valid at 50+ local establishments',
      priority: 'medium',
      date: 'Oct 8, 2025',
      category: 'Benefits'
    },
  ]

  const recentActivities = [
    {
      id: 1,
      title: 'Registered for Leadership Summit',
      description: 'Successfully confirmed your spot',
      time: '2 hours ago',
      type: 'registration',
      icon: TicketIcon,
      color: 'green'
    },
    {
      id: 2,
      title: 'Attended Community Service',
      description: 'Earned 50 community points',
      time: '1 day ago',
      type: 'attendance',
      icon: UsersIcon,
      color: 'blue'
    },
    {
      id: 3,
      title: 'Membership Renewed',
      description: 'Gold tier active until December 2025',
      time: '3 days ago',
      type: 'membership',
      icon: CheckCircleIcon,
      color: 'purple'
    },
    {
      id: 4,
      title: 'Voted in Student Poll',
      description: 'Campus improvement initiatives survey',
      time: '5 days ago',
      type: 'engagement',
      icon: ChartBarIcon,
      color: 'orange'
    },
  ]

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'Leadership': 'blue',
      'Technology': 'purple',
      'Career': 'green',
      'Cultural': 'pink',
      'Sports': 'orange',
      'Business': 'indigo',
      'Community': 'teal',
      'Wellness': 'emerald'
    }
    return colors[category] || 'gray'
  }

  return (
    <Layout title="Dashboard">
      <div className="max-w-7xl mx-auto px-4 py-6 lg:py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 mb-2">
            Welcome back, {user?.first_name}! 👋
          </h2>
          <p className="text-gray-600">
            Stay connected with JKUSA events, announcements, and your student community.
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
                  {stat.trend === 'neutral' && (
                    <span className="text-gray-600 text-xs font-medium bg-gray-50 px-2 py-1 rounded-full">
                      {stat.change}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500 mb-1">{stat.label}</p>
                <p className={`text-3xl font-bold text-${stat.color}-600`}>{stat.value}</p>
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
                      JKUSA Member
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

            {/* Events Registered */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <TicketIcon className="w-5 h-5 text-blue-600" />
                  My Registered Events
                </h3>
                <span className="text-sm text-blue-600 font-medium">
                  {eventsRegistered.length} Events
                </span>
              </div>
              <div className="space-y-3">
                {eventsRegistered.map((event) => (
                  <div 
                    key={event.id}
                    className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group"
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`px-2 py-1 bg-${getCategoryColor(event.category)}-100 text-${getCategoryColor(event.category)}-700 text-xs font-medium rounded-full`}>
                            {event.category}
                          </span>
                          {event.status === 'confirmed' ? (
                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full flex items-center gap-1">
                              <CheckCircleIcon className="w-3 h-3" />
                              Confirmed
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-medium rounded-full">
                              Waitlist
                            </span>
                          )}
                        </div>
                        <p className="text-sm font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                          {event.title}
                        </p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
                          <span className="flex items-center gap-1">
                            <CalendarIcon className="w-4 h-4" />
                            {event.date}
                          </span>
                          <span className="flex items-center gap-1">
                            <ClockIcon className="w-4 h-4" />
                            {event.time}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{event.location}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <button className="w-full mt-4 py-2.5 text-sm text-blue-600 hover:text-blue-700 font-medium hover:bg-blue-50 rounded-lg transition-colors">
                View All My Events
              </button>
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
            {/* Available Events */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <CalendarIcon className="w-5 h-5 text-green-600" />
                  Available Events
                </h3>
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              </div>
              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {availableEvents.map((event) => {
                  const spotsPercentage = (event.spotsLeft / event.totalSpots) * 100
                  return (
                    <div 
                      key={event.id}
                      className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-green-300 hover:bg-green-50 transition-all cursor-pointer group"
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <span className={`px-2 py-1 bg-${getCategoryColor(event.category)}-100 text-${getCategoryColor(event.category)}-700 text-xs font-medium rounded-full`}>
                          {event.category}
                        </span>
                        <span className="text-xs font-semibold text-green-600">
                          {event.fee}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-gray-900 group-hover:text-green-600 transition-colors mb-2">
                        {event.title}
                      </p>
                      <p className="text-xs text-gray-500 mb-2">{event.date} • {event.time}</p>
                      <p className="text-xs text-gray-400 mb-3">{event.location}</p>
                      <div className="mb-2">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-gray-600">Spots Available</span>
                          <span className={`font-medium ${spotsPercentage < 30 ? 'text-red-600' : 'text-gray-900'}`}>
                            {event.spotsLeft}/{event.totalSpots}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div 
                            className={`h-1.5 rounded-full transition-all ${
                              spotsPercentage < 30 ? 'bg-red-500' : 
                              spotsPercentage < 60 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${spotsPercentage}%` }}
                          />
                        </div>
                      </div>
                      <button className="w-full mt-2 py-2 bg-green-600 hover:bg-green-700 text-white text-xs font-medium rounded-lg transition-colors">
                        Register Now
                      </button>
                    </div>
                  )
                })}
              </div>
              <button className="w-full mt-4 py-2.5 text-sm text-green-600 hover:text-green-700 font-medium hover:bg-green-50 rounded-lg transition-colors">
                Browse All Events
              </button>
            </div>

            {/* Announcements */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <BellAlertIcon className="w-5 h-5 text-red-600" />
                  Announcements
                </h3>
                <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              </div>
              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {announcements.map((announcement) => (
                  <div 
                    key={announcement.id}
                    className="p-4 rounded-lg border transition-all cursor-pointer"
                    style={{
                      borderColor: announcement.priority === 'high' ? '#fee2e2' : '#fef3c7',
                      backgroundColor: announcement.priority === 'high' ? '#fef2f2' : '#fffbeb'
                    }}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                            {announcement.category}
                          </span>
                          {announcement.priority === 'high' && (
                            <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full flex items-center gap-1">
                              <ExclamationCircleIcon className="w-3 h-3" />
                              Important
                            </span>
                          )}
                        </div>
                        <p className="text-sm font-medium text-gray-900">
                          {announcement.title}
                        </p>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600 mb-2">{announcement.message}</p>
                    <p className="text-xs text-gray-400">{announcement.date}</p>
                  </div>
                ))}
              </div>
              <button className="w-full mt-4 py-2.5 text-sm text-orange-600 hover:text-orange-700 font-medium hover:bg-orange-50 rounded-lg transition-colors">
                View All Announcements
              </button>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <CalendarIcon className="w-4 h-4" />
                  Browse Events
                </button>
                <button className="w-full py-3 px-4 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <UserGroupIcon className="w-4 h-4" />
                  Join Community
                </button>
                <button className="w-full py-3 px-4 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <SpeakerWaveIcon className="w-4 h-4" />
                  Submit Feedback
                </button>
                <button className="w-full py-3 px-4 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <CurrencyDollarIcon className="w-4 h-4" />
                  Pay Membership
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