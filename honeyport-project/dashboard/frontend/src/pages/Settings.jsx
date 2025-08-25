import React, { useState, useEffect } from 'react';
import { FaSave, FaTrash, FaPlus } from 'react-icons/fa';

const Settings = () => {
  const [blockedIPs, setBlockedIPs] = useState([]);
  const [newIP, setNewIP] = useState('');
  const [newReason, setNewReason] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBlockedIPs();
  }, []);

  const fetchBlockedIPs = async () => {
    try {
      const response = await fetch('/api/v1/blocked-ips', {
        headers: {
          'Authorization': 'Bearer demo-token'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setBlockedIPs(data.blocked_ips || []);
      }
    } catch (error) {
      console.error('Error fetching blocked IPs:', error);
      // Mock data for demo
      setBlockedIPs([
        { ip_address: '192.168.1.100', reason: 'SQL Injection attempts', created_at: new Date().toISOString() },
        { ip_address: '10.0.0.50', reason: 'Brute force attack', created_at: new Date().toISOString() }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const blockIP = async () => {
    if (!newIP || !newReason) return;

    try {
      const response = await fetch('/api/v1/block-ip', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer demo-token'
        },
        body: JSON.stringify({
          ip: newIP,
          reason: newReason
        })
      });

      if (response.ok) {
        setNewIP('');
        setNewReason('');
        fetchBlockedIPs();
      }
    } catch (error) {
      console.error('Error blocking IP:', error);
    }
  };

  const unblockIP = async (ip) => {
    try {
      const response = await fetch(`/api/v1/blocked-ips/${ip}`, {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer demo-token'
        }
      });

      if (response.ok) {
        fetchBlockedIPs();
      }
    } catch (error) {
      console.error('Error unblocking IP:', error);
    }
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
        <h1 className="dashboard-title">Settings</h1>
        <p className="dashboard-subtitle">Configure honeypot security settings</p>
      </div>

      {/* Block New IP Section */}
      <div className="event-table" style={{ marginBottom: '30px' }}>
        <div className="table-header">
          <h3 className="table-title">Block IP Address</h3>
        </div>
        <div style={{ padding: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr auto', gap: '15px', alignItems: 'end' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', color: '#cbd5e1' }}>IP Address</label>
              <input
                type="text"
                value={newIP}
                onChange={(e) => setNewIP(e.target.value)}
                placeholder="192.168.1.100"
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #475569',
                  backgroundColor: '#1e293b',
                  color: '#e2e8f0'
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', color: '#cbd5e1' }}>Reason</label>
              <input
                type="text"
                value={newReason}
                onChange={(e) => setNewReason(e.target.value)}
                placeholder="Malicious activity detected"
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #475569',
                  backgroundColor: '#1e293b',
                  color: '#e2e8f0'
                }}
              />
            </div>
            <button className="btn btn-danger" onClick={blockIP}>
              <FaPlus style={{ marginRight: '5px' }} />
              Block IP
            </button>
          </div>
        </div>
      </div>

      {/* Blocked IPs Table */}
      <div className="event-table">
        <div className="table-header">
          <h3 className="table-title">Blocked IP Addresses</h3>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>IP Address</th>
              <th>Reason</th>
              <th>Blocked Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {blockedIPs.map((blockedIP, index) => (
              <tr key={index}>
                <td>{blockedIP.ip_address}</td>
                <td>{blockedIP.reason}</td>
                <td>{new Date(blockedIP.created_at).toLocaleString()}</td>
                <td>
                  <button 
                    className="btn btn-warning"
                    style={{ fontSize: '0.8rem', padding: '5px 10px' }}
                    onClick={() => unblockIP(blockedIP.ip_address)}
                  >
                    <FaTrash style={{ marginRight: '5px' }} />
                    Unblock
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {blockedIPs.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
            No blocked IP addresses
          </div>
        )}
      </div>

      {/* System Configuration */}
      <div className="event-table" style={{ marginTop: '30px' }}>
        <div className="table-header">
          <h3 className="table-title">System Configuration</h3>
        </div>
        <div style={{ padding: '20px' }}>
          <div style={{ display: 'grid', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', color: '#cbd5e1' }}>Alert Email</label>
              <input
                type="email"
                defaultValue="admin@example.com"
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #475569',
                  backgroundColor: '#1e293b',
                  color: '#e2e8f0'
                }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '5px', color: '#cbd5e1' }}>Alert Threshold</label>
              <select
                defaultValue="medium"
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: '6px',
                  border: '1px solid #475569',
                  backgroundColor: '#1e293b',
                  color: '#e2e8f0'
                }}
              >
                <option value="low">Low - All events</option>
                <option value="medium">Medium - Medium+ severity</option>
                <option value="high">High - High+ severity only</option>
                <option value="critical">Critical - Critical only</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#cbd5e1' }}>
                <input type="checkbox" defaultChecked />
                Enable real-time alerts
              </label>
            </div>

            <div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#cbd5e1' }}>
                <input type="checkbox" defaultChecked />
                Enable GeoIP enrichment
              </label>
            </div>

            <button className="btn btn-primary" style={{ justifySelf: 'start' }}>
              <FaSave style={{ marginRight: '5px' }} />
              Save Configuration
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
