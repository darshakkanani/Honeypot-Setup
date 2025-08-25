import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import './Header.css';

const Header: React.FC = () => {
  const { user } = useAuth();
  const { connectionStatus } = useWebSocket();

  return (
    <div className="header">
      <div className="header-title">
        <h1>Security Operations Center</h1>
      </div>
      
      <div className="header-status">
        <div className={`status-badge ${connectionStatus}`}>
          <span className="status-dot"></span>
          {connectionStatus === 'connected' ? 'Live Feed' : 'Offline'}
        </div>
        
        <div className="user-menu">
          <span className="user-greeting">Welcome, {user?.username}</span>
          <div className="user-avatar">👤</div>
        </div>
      </div>
    </div>
  );
};

export default Header;
