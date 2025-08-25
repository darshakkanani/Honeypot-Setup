import React, { useState, useEffect } from 'react';
import { FaShieldAlt, FaExclamationTriangle, FaGlobe, FaServer } from 'react-icons/fa';
import EventTable from '../components/EventTable';
import LiveMap from '../components/LiveMap';
import StatsChart from '../components/StatsChart';

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_events: 0,
    events_by_type: {},
    events_by_severity: {},
    top_source_ips: [],
    events_last_24h: 0,
    active_events: 0
  });
  const [liveEvents, setLiveEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    fetchLiveEvents();
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchStats();
      fetchLiveEvents();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/stats', {
        headers: {
          'Authorization': 'Bearer demo-token'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
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

  const getSeverityClass = (severity) => {
    return `severity-badge severity-${severity}`;
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Security Dashboard</h1>
        <p className="dashboard-subtitle">Real-time honeypot monitoring and threat analysis</p>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-title">Total Events</span>
            <FaShieldAlt className="stat-icon" />
          </div>
          <div className="stat-value">{stats.total_events.toLocaleString()}</div>
          <div className="stat-change">+{stats.events_last_24h} in last 24h</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-title">Critical Alerts</span>
            <FaExclamationTriangle className="stat-icon" />
          </div>
          <div className="stat-value">{stats.events_by_severity.critical || 0}</div>
          <div className="stat-change">High priority threats</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-title">Active Threats</span>
            <FaGlobe className="stat-icon" />
          </div>
          <div className="stat-value">{stats.active_events}</div>
          <div className="stat-change">Real-time monitoring</div>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-title">Unique IPs</span>
            <FaServer className="stat-icon" />
          </div>
          <div className="stat-value">{stats.top_source_ips.length}</div>
          <div className="stat-change">Attack sources</div>
        </div>
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
        <StatsChart 
          title="Events by Type" 
          data={stats.events_by_type}
          type="doughnut"
        />
        <StatsChart 
          title="Severity Distribution" 
          data={stats.events_by_severity}
          type="bar"
        />
      </div>

      {/* Map and Events Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
        <div className="chart-container">
          <h3 className="chart-title">Threat Map</h3>
          <LiveMap />
        </div>

        <div className="event-table">
          <div className="table-header">
            <h3 className="table-title">Recent Events</h3>
          </div>
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Source IP</th>
                  <th>Type</th>
                  <th>Severity</th>
                </tr>
              </thead>
              <tbody>
                {liveEvents.map((event, index) => (
                  <tr key={index}>
                    <td>{new Date(event.timestamp).toLocaleTimeString()}</td>
                    <td>{event.source_ip}</td>
                    <td>{event.event_type}</td>
                    <td>
                      <span className={getSeverityClass(event.severity)}>
                        {event.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Top Attackers */}
      <div className="event-table">
        <div className="table-header">
          <h3 className="table-title">Top Attack Sources</h3>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>IP Address</th>
              <th>Attack Count</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {stats.top_source_ips.slice(0, 10).map(([ip, count], index) => (
              <tr key={index}>
                <td>{ip}</td>
                <td>{count}</td>
                <td>
                  <button className="btn btn-danger" style={{ fontSize: '0.8rem', padding: '5px 10px' }}>
                    Block IP
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Dashboard;
