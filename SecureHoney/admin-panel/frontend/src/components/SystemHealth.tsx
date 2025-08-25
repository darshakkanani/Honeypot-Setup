import React, { useState, useEffect } from 'react';
import './SystemHealth.css';

interface SystemHealth {
  status: string;
  services: Record<string, string>;
  resources: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  };
}

const SystemHealth: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSystemHealth();
    const interval = setInterval(fetchSystemHealth, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchSystemHealth = async () => {
    try {
      const token = localStorage.getItem('securehoney_token');
      const response = await fetch('http://localhost:5001/api/system/health', {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setHealth(data);
      }
    } catch (error) {
      console.error('Failed to fetch system health:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
      case 'healthy':
      case 'connected':
      case 'synced':
        return 'status-good';
      case 'warning':
        return 'status-warning';
      case 'error':
      case 'down':
        return 'status-error';
      default:
        return 'status-unknown';
    }
  };

  const getUsageClass = (usage: number) => {
    if (usage < 50) return 'usage-good';
    if (usage < 80) return 'usage-warning';
    return 'usage-critical';
  };

  if (loading) {
    return <div className="loading">Loading system health...</div>;
  }

  return (
    <div className="system-health">
      <div className="health-header">
        <h1>💻 System Health</h1>
        <div className={`overall-status ${getStatusClass(health?.status || 'unknown')}`}>
          {health?.status?.toUpperCase() || 'UNKNOWN'}
        </div>
      </div>

      <div className="health-grid">
        <div className="card">
          <div className="card-header">
            <h2>Services Status</h2>
          </div>
          <div className="services-list">
            {Object.entries(health?.services || {}).map(([service, status]) => (
              <div key={service} className="service-item">
                <span className="service-name">
                  {service.replace('_', ' ').toUpperCase()}
                </span>
                <span className={`service-status ${getStatusClass(status)}`}>
                  {status.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Resource Usage</h2>
          </div>
          <div className="resources">
            <div className="resource-item">
              <div className="resource-header">
                <span className="resource-name">CPU Usage</span>
                <span className={`resource-value ${getUsageClass(health?.resources.cpu_usage || 0)}`}>
                  {health?.resources.cpu_usage.toFixed(1)}%
                </span>
              </div>
              <div className="resource-bar">
                <div 
                  className={`resource-fill ${getUsageClass(health?.resources.cpu_usage || 0)}`}
                  style={{ width: `${health?.resources.cpu_usage || 0}%` }}
                ></div>
              </div>
            </div>

            <div className="resource-item">
              <div className="resource-header">
                <span className="resource-name">Memory Usage</span>
                <span className={`resource-value ${getUsageClass(health?.resources.memory_usage || 0)}`}>
                  {health?.resources.memory_usage.toFixed(1)}%
                </span>
              </div>
              <div className="resource-bar">
                <div 
                  className={`resource-fill ${getUsageClass(health?.resources.memory_usage || 0)}`}
                  style={{ width: `${health?.resources.memory_usage || 0}%` }}
                ></div>
              </div>
            </div>

            <div className="resource-item">
              <div className="resource-header">
                <span className="resource-name">Disk Usage</span>
                <span className={`resource-value ${getUsageClass(health?.resources.disk_usage || 0)}`}>
                  {health?.resources.disk_usage.toFixed(1)}%
                </span>
              </div>
              <div className="resource-bar">
                <div 
                  className={`resource-fill ${getUsageClass(health?.resources.disk_usage || 0)}`}
                  style={{ width: `${health?.resources.disk_usage || 0}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealth;
