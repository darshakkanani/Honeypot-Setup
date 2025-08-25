import React, { useState, useEffect } from 'react';
import EventTable from '../components/EventTable';
import { FaFilter, FaSync } from 'react-icons/fa';

const EventView = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState(null);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await fetch('/api/v1/events?limit=100', {
        headers: {
          'Authorization': 'Bearer demo-token'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setEvents(data.events || []);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
      // Mock data for demo
      setEvents([
        {
          id: 1,
          timestamp: new Date().toISOString(),
          source_ip: '192.168.1.100',
          event_type: 'http_request',
          severity: 'high',
          attack_type: 'sql_injection'
        },
        {
          id: 2,
          timestamp: new Date(Date.now() - 60000).toISOString(),
          source_ip: '10.0.0.50',
          event_type: 'ssh_auth_attempt',
          severity: 'medium',
          attack_type: 'brute_force'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleEventClick = (event) => {
    setSelectedEvent(event);
  };

  const closeEventDetails = () => {
    setSelectedEvent(null);
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
        <h1 className="dashboard-title">Security Events</h1>
        <p className="dashboard-subtitle">Detailed view of all honeypot events</p>
        <button className="btn btn-primary" onClick={fetchEvents}>
          <FaSync style={{ marginRight: '5px' }} />
          Refresh
        </button>
      </div>

      <EventTable events={events} onEventClick={handleEventClick} />

      {/* Event Details Modal */}
      {selectedEvent && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: '#334155',
            borderRadius: '12px',
            padding: '20px',
            maxWidth: '600px',
            width: '90%',
            maxHeight: '80vh',
            overflowY: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ color: '#f8fafc' }}>Event Details</h2>
              <button 
                onClick={closeEventDetails}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  fontSize: '24px',
                  cursor: 'pointer'
                }}
              >
                ×
              </button>
            </div>
            
            <div style={{ color: '#e2e8f0' }}>
              <p><strong>ID:</strong> {selectedEvent.id}</p>
              <p><strong>Timestamp:</strong> {new Date(selectedEvent.timestamp).toLocaleString()}</p>
              <p><strong>Source IP:</strong> {selectedEvent.source_ip}</p>
              <p><strong>Event Type:</strong> {selectedEvent.event_type}</p>
              <p><strong>Severity:</strong> <span className={`severity-badge severity-${selectedEvent.severity}`}>{selectedEvent.severity}</span></p>
              <p><strong>Attack Type:</strong> {selectedEvent.attack_type || 'Normal'}</p>
              
              {selectedEvent.enriched_data && (
                <div style={{ marginTop: '20px' }}>
                  <h3>Enriched Data</h3>
                  <pre style={{ 
                    backgroundColor: '#1e293b', 
                    padding: '10px', 
                    borderRadius: '6px',
                    fontSize: '12px',
                    overflow: 'auto'
                  }}>
                    {JSON.stringify(selectedEvent.enriched_data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventView;
