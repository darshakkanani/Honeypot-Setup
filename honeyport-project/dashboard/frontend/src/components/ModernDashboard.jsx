import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ShieldCheckIcon, 
  ExclamationTriangleIcon, 
  GlobeAltIcon, 
  ServerIcon,
  ChartBarIcon,
  EyeIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import clsx from 'clsx';

const ModernDashboard = () => {
  const [stats, setStats] = useState({
    total_events: 0,
    events_by_type: {},
    events_by_severity: {},
    top_source_ips: [],
    events_last_24h: 0,
    active_events: 0,
    unique_ips: 0,
    critical_alerts: 0
  });
  const [liveEvents, setLiveEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [realTimeEnabled, setRealTimeEnabled] = useState(true);

  useEffect(() => {
    fetchStats();
    fetchLiveEvents();
    
    let interval;
    if (realTimeEnabled) {
      interval = setInterval(() => {
        fetchStats();
        fetchLiveEvents();
      }, 5000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [realTimeEnabled]);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/stats', {
        headers: {
          'Authorization': 'Bearer demo-token'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(prevStats => {
          // Check for new critical alerts
          if (data.critical_alerts > prevStats.critical_alerts) {
            toast.error(`New critical alert detected!`, {
              icon: '🚨',
              duration: 5000
            });
          }
          return data;
        });
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
      toast.error('Failed to fetch statistics');
    } finally {
      setLoading(false);
    }
  };

  const fetchLiveEvents = async () => {
    try {
      const response = await fetch('/api/v1/live-events?limit=10', {
        headers: {
          'Authorization': 'Bearer demo-token'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setLiveEvents(data.events || []);
      }
    } catch (error) {
      console.error('Error fetching live events:', error);
    }
  };

  const blockIP = async (ip) => {
    try {
      const response = await fetch('/api/v1/block-ip', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo-token'
        },
        body: JSON.stringify({ ip, reason: 'Manual block from dashboard' })
      });
      
      if (response.ok) {
        toast.success(`IP ${ip} blocked successfully`);
        fetchStats(); // Refresh stats
      } else {
        toast.error('Failed to block IP');
      }
    } catch (error) {
      console.error('Error blocking IP:', error);
      toast.error('Error blocking IP');
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      info: 'bg-blue-100 text-blue-800',
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-red-100 text-red-800',
      critical: 'bg-red-200 text-red-900 animate-pulse'
    };
    return colors[severity] || colors.info;
  };

  const getEventTypeIcon = (eventType) => {
    const icons = {
      'http_request': '🌐',
      'ssh_connection': '🔐',
      'tcp_connection': '🔌',
      'ssh_auth_attempt': '🚪',
      'sql_injection': '💉',
      'xss': '🕷️',
      'brute_force': '🔨'
    };
    return icons[eventType] || '📡';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white shadow-lg border-b border-gray-200"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                HoneyPort Security Dashboard
              </h1>
              <p className="text-gray-600 mt-1">Real-time threat monitoring and analysis</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setRealTimeEnabled(!realTimeEnabled)}
                className={clsx(
                  "flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all",
                  realTimeEnabled 
                    ? "bg-green-100 text-green-800 hover:bg-green-200" 
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                )}
              >
                <EyeIcon className="w-5 h-5" />
                <span>{realTimeEnabled ? 'Live' : 'Paused'}</span>
              </button>
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <ClockIcon className="w-4 h-4" />
                <span>Last updated: {new Date().toLocaleTimeString()}</span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <StatCard
            title="Total Events"
            value={stats.total_events?.toLocaleString() || '0'}
            change={`+${stats.events_last_24h || 0} today`}
            icon={ShieldCheckIcon}
            color="blue"
          />
          <StatCard
            title="Critical Alerts"
            value={stats.events_by_severity?.critical || 0}
            change="High priority threats"
            icon={ExclamationTriangleIcon}
            color="red"
            pulse={stats.events_by_severity?.critical > 0}
          />
          <StatCard
            title="Active Threats"
            value={stats.active_events || 0}
            change="Real-time monitoring"
            icon={GlobeAltIcon}
            color="yellow"
          />
          <StatCard
            title="Unique Sources"
            value={stats.top_source_ips?.length || 0}
            change="Attack sources"
            icon={ServerIcon}
            color="green"
          />
        </motion.div>

        {/* Charts and Live Events */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Event Types Chart */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl shadow-lg p-6 border border-gray-200"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <ChartBarIcon className="w-5 h-5 mr-2 text-blue-600" />
              Event Distribution
            </h3>
            <EventTypeChart data={stats.events_by_type} />
          </motion.div>

          {/* Live Events */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden"
          >
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <EyeIcon className="w-5 h-5 mr-2 text-green-600" />
                Live Events
              </h3>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {liveEvents.length > 0 ? (
                liveEvents.map((event, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{getEventTypeIcon(event.event_type)}</span>
                        <div>
                          <p className="font-medium text-gray-900">{event.source_ip}</p>
                          <p className="text-sm text-gray-500">{event.event_type}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={clsx(
                          "px-2 py-1 rounded-full text-xs font-medium",
                          getSeverityColor(event.severity)
                        )}>
                          {event.severity}
                        </span>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div className="p-8 text-center text-gray-500">
                  <EyeIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No recent events</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Top Attackers */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden"
        >
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Top Attack Sources</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Attack Count
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {stats.top_source_ips?.slice(0, 10).map(([ip, count], index) => (
                  <motion.tr
                    key={ip}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {ip}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        {count} attacks
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => blockIP(ip)}
                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-md text-xs font-medium transition-colors"
                      >
                        Block IP
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, change, icon: Icon, color, pulse = false }) => {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    red: 'from-red-500 to-red-600',
    yellow: 'from-yellow-500 to-yellow-600',
    green: 'from-green-500 to-green-600'
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={clsx(
        "bg-white rounded-xl shadow-lg p-6 border border-gray-200 relative overflow-hidden",
        pulse && "animate-pulse"
      )}
    >
      <div className={clsx(
        "absolute top-0 left-0 right-0 h-1 bg-gradient-to-r",
        colorClasses[color]
      )} />
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 uppercase tracking-wide">
            {title}
          </p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          <p className="text-sm text-gray-500 mt-1">{change}</p>
        </div>
        <div className={clsx(
          "p-3 rounded-full bg-gradient-to-r",
          colorClasses[color]
        )}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </motion.div>
  );
};

const EventTypeChart = ({ data }) => {
  const chartData = Object.entries(data || {}).map(([type, count]) => ({
    type,
    count,
    percentage: Math.round((count / Object.values(data || {}).reduce((a, b) => a + b, 1)) * 100)
  }));

  return (
    <div className="space-y-4">
      {chartData.map(({ type, count, percentage }, index) => (
        <div key={type} className="flex items-center space-x-4">
          <div className="flex-1">
            <div className="flex justify-between text-sm">
              <span className="font-medium text-gray-700 capitalize">
                {type.replace('_', ' ')}
              </span>
              <span className="text-gray-500">{count}</span>
            </div>
            <div className="mt-1 bg-gray-200 rounded-full h-2">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${percentage}%` }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full"
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ModernDashboard;
