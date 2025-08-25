import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import StatCard from './StatCard';
import './Dashboard.css';

interface SystemStats {
  total_attacks: number;
  attacks_today: number;
  unique_attackers: number;
  blocked_ips: number;
  system_uptime: string;
  threat_level: string;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const { lastMessage, connectionStatus } = useWebSocket();

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    if (lastMessage?.type === 'stats_update') {
      setStats(lastMessage.data);
    }
  }, [lastMessage]);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('securehoney_token');
      const response = await fetch('http://localhost:5001/api/dashboard/stats', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>🛡️ Security Dashboard</h1>
        <div className={`connection-status ${connectionStatus}`}>
          <span className="status-dot"></span>
          {connectionStatus === 'connected' ? 'Live' : 'Offline'}
        </div>
      </div>

      <div className="stats-grid">
        <StatCard
          title="Total Attacks"
          value={stats?.total_attacks || 0}
          icon="🎯"
          trend={+12}
        />
        <StatCard
          title="Today's Attacks"
          value={stats?.attacks_today || 0}
          icon="📊"
          trend={+5}
        />
        <StatCard
          title="Unique Attackers"
          value={stats?.unique_attackers || 0}
          icon="👥"
          trend={-3}
        />
        <StatCard
          title="Blocked IPs"
          value={stats?.blocked_ips || 0}
          icon="🚫"
          trend={+8}
        />
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h2>System Status</h2>
          </div>
          <div className="system-status">
            <div className="status-item">
              <span className="status-label">Uptime:</span>
              <span className="status-value">{stats?.system_uptime}</span>
            </div>
            <div className="status-item">
              <span className="status-label">Threat Level:</span>
              <span className={`threat-level ${stats?.threat_level?.toLowerCase()}`}>
                {stats?.threat_level}
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Recent Activity</h2>
          </div>
          <div className="activity-feed">
            <div className="activity-item">
              <span className="activity-time">2 min ago</span>
              <span className="activity-text">SSH brute force detected from 192.168.1.100</span>
            </div>
            <div className="activity-item">
              <span className="activity-time">5 min ago</span>
              <span className="activity-text">HTTP injection attempt blocked</span>
            </div>
            <div className="activity-item">
              <span className="activity-time">8 min ago</span>
              <span className="activity-text">New attacker IP added to blocklist</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
