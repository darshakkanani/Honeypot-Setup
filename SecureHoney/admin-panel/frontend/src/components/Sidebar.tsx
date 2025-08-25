import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Sidebar.css';

const Sidebar: React.FC = () => {
  const location = useLocation();
  const { user, logout } = useAuth();

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/attacks', label: 'Attack Logs', icon: '🎯' },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/system', label: 'System Health', icon: '💻' },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>🛡️ SecureHoney</h2>
        <p>Admin Panel</p>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </Link>
        ))}
        <Link to="/analytics" className={location.pathname === '/analytics' ? 'active' : ''}>
          <span className="nav-icon">📊</span>
          <span className="nav-label">Analytics</span>
        </Link>
        <Link to="/database" className={location.pathname === '/database' ? 'active' : ''}>
          <span className="nav-icon">🗄️</span>
          <span className="nav-label">Database Analytics</span>
        </Link>
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="user-avatar">👤</div>
          <div className="user-details">
            <div className="user-name">{user?.username}</div>
            <div className="user-role">{user?.role}</div>
          </div>
        </div>
        <button onClick={logout} className="logout-btn">
          🚪 Logout
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
