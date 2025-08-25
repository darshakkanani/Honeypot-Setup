import React, { useState, useEffect } from 'react';
import './AttacksList.css';

interface Attack {
  id: string;
  timestamp: string;
  source_ip: string;
  target_port: number;
  attack_type: string;
  severity: string;
  confidence: number;
  location: { country: string; city: string };
}

const AttacksList: React.FC = () => {
  const [attacks, setAttacks] = useState<Attack[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');

  useEffect(() => {
    fetchAttacks();
  }, [severityFilter]);

  const fetchAttacks = async () => {
    try {
      const token = localStorage.getItem('securehoney_token');
      const url = severityFilter 
        ? `http://localhost:5001/api/attacks?severity=${severityFilter}`
        : 'http://localhost:5001/api/attacks';
        
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setAttacks(data.attacks);
      }
    } catch (error) {
      console.error('Failed to fetch attacks:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredAttacks = attacks.filter(attack =>
    attack.source_ip.includes(filter) ||
    attack.attack_type.toLowerCase().includes(filter.toLowerCase())
  );

  const getSeverityClass = (severity: string) => {
    return `severity-${severity.toLowerCase()}`;
  };

  if (loading) {
    return <div className="loading">Loading attacks...</div>;
  }

  return (
    <div className="attacks-list">
      <div className="attacks-header">
        <h1>🎯 Attack Logs</h1>
        <div className="filters">
          <input
            type="text"
            placeholder="Filter by IP or attack type..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="filter-input"
          />
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="filter-select"
          >
            <option value="">All Severities</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>
      </div>

      <div className="attacks-table-container">
        <table className="attacks-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Source IP</th>
              <th>Port</th>
              <th>Attack Type</th>
              <th>Severity</th>
              <th>Confidence</th>
              <th>Location</th>
            </tr>
          </thead>
          <tbody>
            {filteredAttacks.map((attack) => (
              <tr key={attack.id}>
                <td>{new Date(attack.timestamp).toLocaleString()}</td>
                <td className="ip-cell">{attack.source_ip}</td>
                <td>{attack.target_port}</td>
                <td className="attack-type">{attack.attack_type}</td>
                <td>
                  <span className={`severity-badge ${getSeverityClass(attack.severity)}`}>
                    {attack.severity}
                  </span>
                </td>
                <td>{(attack.confidence * 100).toFixed(0)}%</td>
                <td>{attack.location.country}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AttacksList;
