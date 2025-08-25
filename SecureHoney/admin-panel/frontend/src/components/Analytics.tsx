import React, { useState, useEffect } from 'react';
import './Analytics.css';

interface AnalyticsData {
  period: string;
  attack_trends: Array<{ hour: number; attacks: number }>;
  attack_types: Record<string, number>;
  top_countries: Array<{ country: string; attacks: number }>;
}

const Analytics: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('24h');

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  const fetchAnalytics = async () => {
    try {
      const token = localStorage.getItem('securehoney_token');
      const response = await fetch(`http://localhost:5001/api/analytics/trends?period=${period}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const analyticsData = await response.json();
        setData(analyticsData);
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading analytics...</div>;
  }

  return (
    <div className="analytics">
      <div className="analytics-header">
        <h1>📈 Security Analytics</h1>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="period-select"
        >
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
      </div>

      <div className="analytics-grid">
        <div className="card">
          <div className="card-header">
            <h2>Attack Trends</h2>
          </div>
          <div className="chart-container">
            <div className="bar-chart">
              {data?.attack_trends.map((item) => (
                <div key={item.hour} className="bar-item">
                  <div 
                    className="bar" 
                    style={{ height: `${(item.attacks / 25) * 100}%` }}
                  ></div>
                  <span className="bar-label">{item.hour}h</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Attack Types</h2>
          </div>
          <div className="attack-types">
            {Object.entries(data?.attack_types || {}).map(([type, count]) => (
              <div key={type} className="attack-type-item">
                <span className="attack-type-name">{type.replace('_', ' ')}</span>
                <div className="attack-type-bar">
                  <div 
                    className="attack-type-fill" 
                    style={{ width: `${(count / 50) * 100}%` }}
                  ></div>
                  <span className="attack-type-count">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Top Attack Sources</h2>
          </div>
          <div className="country-list">
            {data?.top_countries.map((country, index) => (
              <div key={country.country} className="country-item">
                <span className="country-rank">#{index + 1}</span>
                <span className="country-name">{country.country}</span>
                <span className="country-attacks">{country.attacks} attacks</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
