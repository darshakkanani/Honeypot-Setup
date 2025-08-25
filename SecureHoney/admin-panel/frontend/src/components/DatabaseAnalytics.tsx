import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './DatabaseAnalytics.css';

interface AttackTrend {
  timestamp: string;
  value: number;
}

interface GeographicData {
  country: string;
  country_code: string;
  total_attacks: number;
  unique_attackers: number;
  attack_percentage: number;
  risk_score: number;
}

interface ThreatActor {
  ip_address: string;
  threat_level: string;
  reputation_score: number;
  total_attacks: number;
  skill_level: string;
  first_seen: string;
  last_seen: string;
  preferred_ports: number[];
  attack_types: string[];
}

const DatabaseAnalytics: React.FC = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [attackTrends, setAttackTrends] = useState<AttackTrend[]>([]);
  const [geographicData, setGeographicData] = useState<GeographicData[]>([]);
  const [topThreats, setTopThreats] = useState<ThreatActor[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState('24h');
  const [selectedMetric, setSelectedMetric] = useState('attacks');
  const [searchIP, setSearchIP] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedPeriod, selectedMetric]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      // Load attack trends
      const trendsResponse = await fetch(
        `/api/database/analytics/trends?period=${selectedPeriod}&metric=${selectedMetric}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      const trendsData = await trendsResponse.json();
      
      if (trendsData.success && Array.isArray(trendsData.trends)) {
        setAttackTrends(trendsData.trends);
      }

      // Load geographic analysis
      const geoResponse = await fetch('/api/database/geographic/analysis?days=7', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const geoData = await geoResponse.json();
      
      if (geoData.success) {
        setGeographicData(Object.entries(geoData.geographic_analysis.country_statistics).map(
          ([country, data]: [string, any]) => ({
            country,
            ...data
          })
        ));
      }

      // Load top threats
      const threatsResponse = await fetch('/api/database/attackers/top-threats?limit=10', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const threatsData = await threatsResponse.json();
      
      if (threatsData.success) {
        setTopThreats(threatsData.top_threats);
      }

    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchAttacker = async () => {
    if (!searchIP.trim()) return;

    try {
      const response = await fetch(`/api/database/attackers/${searchIP}/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (data.success) {
        setSearchResults([data.profile]);
      }
    } catch (error) {
      console.error('Failed to search attacker:', error);
    }
  };

  const getThreatLevelColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return '#ff4444';
      case 'HIGH': return '#ff8800';
      case 'MEDIUM': return '#ffaa00';
      case 'LOW': return '#44aa44';
      default: return '#666666';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="database-analytics">
        <div className="loading-spinner">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="database-analytics">
      <div className="analytics-header">
        <h1>Database Analytics</h1>
        <div className="analytics-controls">
          <select 
            value={selectedPeriod} 
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="period-selector"
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          
          <select 
            value={selectedMetric} 
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="metric-selector"
          >
            <option value="attacks">Total Attacks</option>
            <option value="unique_ips">Unique Attackers</option>
            <option value="severity">Attack Severity</option>
            <option value="ports">Target Ports</option>
          </select>
        </div>
      </div>

      <div className="analytics-grid">
        {/* Attack Trends Chart */}
        <div className="analytics-card trends-card">
          <h3>Attack Trends - {selectedMetric}</h3>
          <div className="trend-chart">
            {attackTrends.length > 0 ? (
              <div className="simple-chart">
                {attackTrends.map((trend, index) => (
                  <div key={index} className="chart-bar">
                    <div 
                      className="bar" 
                      style={{ 
                        height: `${(trend.value / Math.max(...attackTrends.map(t => t.value))) * 100}%` 
                      }}
                    />
                    <span className="bar-label">{trend.value}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p>No trend data available</p>
            )}
          </div>
        </div>

        {/* Geographic Analysis */}
        <div className="analytics-card geographic-card">
          <h3>Geographic Attack Distribution</h3>
          <div className="geographic-list">
            {geographicData.slice(0, 10).map((country, index) => (
              <div key={index} className="country-item">
                <div className="country-info">
                  <span className="country-flag">{country.country_code}</span>
                  <span className="country-name">{country.country}</span>
                </div>
                <div className="country-stats">
                  <span className="attack-count">{country.total_attacks} attacks</span>
                  <span className="unique-attackers">{country.unique_attackers} IPs</span>
                  <div 
                    className="risk-bar"
                    style={{ 
                      width: `${country.risk_score}%`,
                      backgroundColor: country.risk_score > 70 ? '#ff4444' : 
                                     country.risk_score > 40 ? '#ff8800' : '#44aa44'
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Threat Actors */}
        <div className="analytics-card threats-card">
          <h3>Top Threat Actors</h3>
          <div className="threats-list">
            {topThreats.map((threat, index) => (
              <div key={index} className="threat-item">
                <div className="threat-header">
                  <span className="threat-ip">{threat.ip_address}</span>
                  <span 
                    className="threat-level"
                    style={{ color: getThreatLevelColor(threat.threat_level) }}
                  >
                    {threat.threat_level}
                  </span>
                </div>
                <div className="threat-details">
                  <span>Score: {threat.reputation_score}</span>
                  <span>Attacks: {threat.total_attacks}</span>
                  <span>Skill: {threat.skill_level}</span>
                </div>
                <div className="threat-activity">
                  <span>First: {formatDate(threat.first_seen)}</span>
                  <span>Last: {formatDate(threat.last_seen)}</span>
                </div>
                {threat.attack_types.length > 0 && (
                  <div className="attack-types">
                    {threat.attack_types.slice(0, 3).map((type, i) => (
                      <span key={i} className="attack-type-tag">{type}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Attacker Search */}
        <div className="analytics-card search-card">
          <h3>Attacker Profile Search</h3>
          <div className="search-controls">
            <input
              type="text"
              placeholder="Enter IP address..."
              value={searchIP}
              onChange={(e) => setSearchIP(e.target.value)}
              className="search-input"
            />
            <button onClick={searchAttacker} className="search-button">
              Search
            </button>
          </div>
          
          {searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.map((result, index) => (
                <div key={index} className="search-result">
                  <h4>Profile for {result.ip_address}</h4>
                  <div className="profile-details">
                    <p><strong>Threat Level:</strong> {result.threat_level}</p>
                    <p><strong>Total Attacks:</strong> {result.total_attacks}</p>
                    <p><strong>Reputation Score:</strong> {result.reputation_score}</p>
                    <p><strong>Skill Level:</strong> {result.skill_level}</p>
                    <p><strong>First Seen:</strong> {formatDate(result.first_seen)}</p>
                    <p><strong>Last Seen:</strong> {formatDate(result.last_seen)}</p>
                  </div>
                  
                  {result.behavioral_patterns && (
                    <div className="behavioral-patterns">
                      <h5>Behavioral Patterns</h5>
                      <ul>
                        {Object.entries(result.behavioral_patterns).map(([key, value]: [string, any]) => (
                          <li key={key}><strong>{key}:</strong> {JSON.stringify(value)}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DatabaseAnalytics;
