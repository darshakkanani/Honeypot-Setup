import React, { useState, useEffect } from 'react';
import { FaSearch, FaDownload, FaEye } from 'react-icons/fa';

const EventTable = ({ events = [], onEventClick }) => {
  const [filteredEvents, setFilteredEvents] = useState(events);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  useEffect(() => {
    let filtered = events;

    if (searchTerm) {
      filtered = filtered.filter(event => 
        event.source_ip.includes(searchTerm) ||
        event.event_type.includes(searchTerm) ||
        (event.attack_type && event.attack_type.includes(searchTerm))
      );
    }

    if (severityFilter !== 'all') {
      filtered = filtered.filter(event => event.severity === severityFilter);
    }

    if (typeFilter !== 'all') {
      filtered = filtered.filter(event => event.event_type === typeFilter);
    }

    setFilteredEvents(filtered);
  }, [events, searchTerm, severityFilter, typeFilter]);

  const getSeverityClass = (severity) => {
    return `severity-badge severity-${severity}`;
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const exportToCsv = () => {
    const headers = ['Timestamp', 'Source IP', 'Event Type', 'Severity', 'Attack Type'];
    const csvContent = [
      headers.join(','),
      ...filteredEvents.map(event => [
        event.timestamp,
        event.source_ip,
        event.event_type,
        event.severity,
        event.attack_type || 'N/A'
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'honeypot_events.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="event-table">
      <div className="table-header">
        <h3 className="table-title">Security Events</h3>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <FaSearch style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
            <input
              type="text"
              placeholder="Search events..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                paddingLeft: '35px',
                padding: '8px',
                borderRadius: '6px',
                border: '1px solid #475569',
                backgroundColor: '#1e293b',
                color: '#e2e8f0'
              }}
            />
          </div>
          
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{
              padding: '8px',
              borderRadius: '6px',
              border: '1px solid #475569',
              backgroundColor: '#1e293b',
              color: '#e2e8f0'
            }}
          >
            <option value="all">All Severities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>

          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            style={{
              padding: '8px',
              borderRadius: '6px',
              border: '1px solid #475569',
              backgroundColor: '#1e293b',
              color: '#e2e8f0'
            }}
          >
            <option value="all">All Types</option>
            <option value="http_request">HTTP Request</option>
            <option value="ssh_connection">SSH Connection</option>
            <option value="ssh_auth_attempt">SSH Auth</option>
            <option value="tcp_connection">TCP Connection</option>
          </select>

          <button className="btn btn-primary" onClick={exportToCsv}>
            <FaDownload style={{ marginRight: '5px' }} />
            Export
          </button>
        </div>
      </div>

      <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Source IP</th>
              <th>Event Type</th>
              <th>Severity</th>
              <th>Attack Type</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredEvents.map((event, index) => (
              <tr key={event.id || index}>
                <td>{formatTimestamp(event.timestamp)}</td>
                <td>{event.source_ip}</td>
                <td>{event.event_type}</td>
                <td>
                  <span className={getSeverityClass(event.severity)}>
                    {event.severity}
                  </span>
                </td>
                <td>{event.attack_type || 'Normal'}</td>
                <td>
                  <button 
                    className="btn btn-primary"
                    style={{ fontSize: '0.8rem', padding: '5px 10px' }}
                    onClick={() => onEventClick && onEventClick(event)}
                  >
                    <FaEye style={{ marginRight: '5px' }} />
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredEvents.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
          No events found matching your criteria
        </div>
      )}
    </div>
  );
};

export default EventTable;
