import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaShieldAlt, FaTachometerAlt, FaList, FaCog } from 'react-icons/fa';

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: FaTachometerAlt },
    { path: '/events', label: 'Events', icon: FaList },
    { path: '/settings', label: 'Settings', icon: FaCog },
  ];

  return (
    <nav className="navigation">
      <div className="nav-header">
        <div className="nav-title">
          <FaShieldAlt />
          HoneyPort
        </div>
      </div>
      <div className="nav-menu">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <Icon style={{ marginRight: '10px' }} />
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

export default Navigation;
