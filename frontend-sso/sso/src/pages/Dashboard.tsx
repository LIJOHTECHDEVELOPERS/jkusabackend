import { useNavigate } from 'react-router-dom'
import { useEffect, useState, type FC } from 'react'
import { useAuth } from '../context/AuthContext'
import {
  AcademicCapIcon,
  BuildingOffice2Icon,
  BookOpenIcon,
  CalendarIcon,
  UserGroupIcon,
  CheckCircleIcon,
  SpeakerWaveIcon,
  BellAlertIcon,
  UsersIcon,
  SparklesIcon,
  BuildingLibraryIcon
} from '@heroicons/react/24/outline'
import Layout from '../components/Layout'

interface Event {
  id: number
  title: string
  description: string
  date?: string
  start_datetime?: string
  end_datetime?: string
  location: string
  image_url?: string
  featured_image_url?: string
  slug?: string
}

interface Announcement {
  id: number
  title: string
  content: string
  image_url: string | null
  announced_at: string
}

interface Activity {
  id: number
  title: string
  description: string
  date: string
  location: string
  image_url?: string
}

const Dashboard: FC = () => {
  const { user, loading } = useAuth()
  const navigate = useNavigate()
  const [publicEvents, setPublicEvents] = useState<Event[]>([])
  const [activities, setActivities] = useState<Activity[]>([])
  const [announcements, setAnnouncements] = useState<Announcement[]>([])
  const [collegeName, setCollegeName] = useState('')
  const [schoolName, setSchoolName] = useState('')
  const [loadingEvents, setLoadingEvents] = useState(true)
  const [loadingActivities, setLoadingActivities] = useState(true)
  const [loadingAnnouncements, setLoadingAnnouncements] = useState(true)

  // Redirect to signin if user is not authenticated (only after loading completes)
  useEffect(() => {
    if (!loading && !user) {
      navigate('/signin')
    }
  }, [user, loading, navigate])

  // Show loading screen while checking authentication
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-gray-50">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    )
  }

  // Set college and school name from user object
  useEffect(() => {
    if (user?.college?.name) {
      setCollegeName(user.college.name)
    }
    if (user?.school?.name) {
      setSchoolName(user.school.name)
    }
  }, [user])

  // Fetch public events
  useEffect(() => {
    const fetchPublicEvents = async () => {
      try {
        const response = await fetch('https://backend.jkusa.org/events/')
        const data = await response.json()
        const eventsData = Array.isArray(data) ? data : data.items || []
        setPublicEvents(eventsData.slice(0, 6))
      } catch (error) {
        console.error('Error fetching events:', error)
      } finally {
        setLoadingEvents(false)
      }
    }
    fetchPublicEvents()
  }, [])

  // Fetch activities
  useEffect(() => {
    const fetchActivities = async () => {
      try {
        const response = await fetch('https://backend.jkusa.org/activities/')
        const data = await response.json()
        const activitiesData = Array.isArray(data) ? data : data.items || []
        setActivities(activitiesData.slice(0, 4))
      } catch (error) {
        console.error('Error fetching activities:', error)
      } finally {
        setLoadingActivities(false)
      }
    }
    fetchActivities()
  }, [])

  // Fetch announcements
  useEffect(() => {
    const fetchAnnouncements = async () => {
      try {
        const response = await fetch('https://backend.jkusa.org/announcements/')
        const data = await response.json()
        const announcementsData = Array.isArray(data) ? data : data.items || []
        const oneMonthAgo = new Date()
        oneMonthAgo.setDate(oneMonthAgo.getDate() - 30)
        const recentAnnouncements = announcementsData.filter((a: Announcement) => new Date(a.announced_at) >= oneMonthAgo)
        setAnnouncements(recentAnnouncements)
      } catch (error) {
        console.error('Error fetching announcements:', error)
      } finally {
        setLoadingAnnouncements(false)
      }
    }
    fetchAnnouncements()
  }, [])

  const quickStats = [
    {
      label: 'Events Registered',
      value: '0',
      change: 'Coming Soon',
      trend: 'neutral',
      color: 'purple',
      icon: SparklesIcon
    },
    {
      label: 'Available Events',
      value: publicEvents.length.toString(),
      change: 'Live Now',
      trend: 'neutral',
      color: 'blue',
      icon: CalendarIcon
    },
    {
      label: 'Account Active',
      value: 'Yes',
      change: 'Gold Asso.',
      trend: 'neutral',
      color: 'green',
      icon: CheckCircleIcon
    },
    {
      label: 'Announcements',
      value: announcements.length.toString(),
      change: 'New Updates',
      trend: 'up',
      color: 'orange',
      icon: BellAlertIcon
    },
  ]

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const stripHtml = (html: string) => {
    const tmp = document.createElement('DIV')
    tmp.innerHTML = html
    return tmp.textContent || tmp.innerText || ''
  }

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.substr(0, maxLength) + '...'
  }

  const recentActivitiesDisplay = activities.map(activity => ({
    id: activity.id,
    title: activity.title,
    description: truncateText(stripHtml(activity.description), 50),
    time: formatDate(activity.date),
    type: 'activity',
    icon: UsersIcon,
    color: 'blue'
  }))

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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100 hover:shadow-md transition-all duration-300 hover:border-indigo-200">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <BuildingLibraryIcon className="w-6 h-6 text-indigo-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-500 mb-1">School</p>
                    <p className="font-semibold text-gray-900 text-sm truncate">
                      {schoolName || 'Loading...'}
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100 hover:shadow-md transition-all duration-300 hover:border-blue-200">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <BuildingOffice2Icon className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-500 mb-1">College</p>
                    <p className="font-semibold text-gray-900 text-sm truncate">
                      {collegeName || 'Loading...'}
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
            {/* Events Registered - Coming Soon */}
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-sm border-2 border-dashed border-purple-300 p-6">
              <div className="flex flex-col items-center justify-center text-center py-8">
                <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mb-4">
                  <SparklesIcon className="w-10 h-10 text-purple-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  Event Registration Coming Soon!
                </h3>
                <p className="text-gray-600 max-w-md">
                  We're working on an amazing event registration system. Soon you'll be able to register for events, track your bookings, and get instant confirmations!
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  <span className="px-4 py-2 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                    🎯 Track Registrations
                  </span>
                  <span className="px-4 py-2 bg-pink-100 text-pink-700 rounded-full text-sm font-medium">
                    🎟️ Get Tickets
                  </span>
                  <span className="px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                    ⚡ Instant Confirmation
                  </span>
                </div>
              </div>
            </div>
            {/* Recent Activity */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold text-gray-900">Recent Activities</h3>
                <button
                  onClick={() => navigate('/calender')}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  View All
                </button>
              </div>
              {loadingActivities ? (
                <div className="flex justify-center items-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : recentActivitiesDisplay.length > 0 ? (
                <div className="space-y-4">
                  {recentActivitiesDisplay.map((activity, index) => {
                    const Icon = activity.icon
                    return (
                      <div
                        key={activity.id}
                        className={`flex items-start gap-4 ${
                          index !== recentActivitiesDisplay.length - 1 ? 'pb-4 border-b border-gray-100' : ''
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
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <UsersIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>No recent activities</p>
                </div>
              )}
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
              {loadingEvents ? (
                <div className="flex justify-center items-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                </div>
              ) : publicEvents.length > 0 ? (
                <>
                  <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                    {publicEvents.map((event) => {
                      const eventDate = event.start_datetime || event.date
                      return (
                        <div
                          key={event.id}
                          className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-green-300 hover:bg-green-50 transition-all cursor-pointer group"
                        >
                          {(event.image_url || event.featured_image_url) && (
                            <img
                              src={event.image_url || event.featured_image_url}
                              alt={event.title}
                              className="w-full h-32 object-cover rounded-lg mb-3"
                            />
                          )}
                          <p className="text-sm font-medium text-gray-900 group-hover:text-green-600 transition-colors mb-2">
                            {event.title}
                          </p>
                          <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                            {truncateText(stripHtml(event.description), 80)}
                          </p>
                          {eventDate && (
                            <p className="text-xs text-gray-500 mb-2">
                              📅 {formatDate(eventDate)} • {formatTime(eventDate)}
                            </p>
                          )}
                          <p className="text-xs text-gray-400 mb-3">📍 {event.location}</p>
                          <button
                            onClick={() => navigate(`/events/${event.slug}`)}
                            className="w-full mt-2 py-2 bg-green-600 hover:bg-green-700 text-white text-xs font-medium rounded-lg transition-colors"
                          >
                            View Details
                          </button>
                        </div>
                      )
                    })}
                  </div>
                  <button
                    onClick={() => navigate('/events')}
                    className="w-full mt-4 py-2.5 text-sm text-green-600 hover:text-green-700 font-medium hover:bg-green-50 rounded-lg transition-colors"
                  >
                    Browse All Events
                  </button>
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <CalendarIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>No events available</p>
                </div>
              )}
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
              {loadingAnnouncements ? (
                <div className="flex justify-center items-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
                </div>
              ) : announcements.length > 0 ? (
                <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                  {announcements.map((announcement) => (
                    <div
                      key={announcement.id}
                      className="p-4 rounded-lg border border-red-100 bg-red-50 transition-all cursor-pointer hover:shadow-md"
                    >
                      {announcement.image_url && (
                        <img
                          src={announcement.image_url}
                          alt={announcement.title}
                          className="w-full h-24 object-cover rounded-lg mb-3"
                        />
                      )}
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <p className="text-sm font-medium text-gray-900 flex-1">
                          {announcement.title}
                        </p>
                        <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full flex-shrink-0">
                          New
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 mb-2 line-clamp-3">
                        {truncateText(stripHtml(announcement.content), 100)}
                      </p>
                      <p className="text-xs text-gray-400">
                        {formatDate(announcement.announced_at)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <BellAlertIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>No announcements</p>
                </div>
              )}
            </div>
            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <button
                  onClick={() => navigate('/events')}
                  className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                >
                  <CalendarIcon className="w-4 h-4" />
                  Browse Events
                </button>
                <button className="w-full py-3 px-4 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <SpeakerWaveIcon className="w-4 h-4" />
                  Submit Feedback
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