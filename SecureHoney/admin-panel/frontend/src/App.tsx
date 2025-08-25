import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import AttacksList from './components/AttacksList';
import Analytics from './components/Analytics';
import SystemHealth from './components/SystemHealth';
import DatabaseAnalytics from './components/DatabaseAnalytics';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import { useAuth } from './contexts/AuthContext';
import './App.css';

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="loading-screen">Loading SecureHoney...</div>;
  }

  if (!user) {
    return <Login />;
  }

  return (
    <WebSocketProvider>
      <div className="app-layout">
        <Sidebar />
        <div className="main-content">
          <Header />
          <div className="content-area">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/attacks" element={<AttacksList />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/database" element={<DatabaseAnalytics />} />
              <Route path="/health" element={<SystemHealth />} />
            </Routes>
          </div>
        </div>
      </div>
    </WebSocketProvider>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
}

export default App;
