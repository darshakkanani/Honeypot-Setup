import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import Dashboard from './pages/Dashboard';
import Attacks from './pages/Attacks';
import Analytics from './pages/Analytics';
import SystemHealth from './pages/SystemHealth';
import Alerts from './pages/Alerts';
import Honeypots from './pages/Honeypots';
import Users from './pages/Users';
import Logs from './pages/Logs';
import Settings from './pages/Settings';
import Login from './pages/Login';
import { cn } from './lib/utils';

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  return (
    <AuthProvider>
      <WebSocketProvider>
        <Router>
          <div className="min-h-screen bg-background text-foreground">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/*" element={
                <div className="flex h-screen">
                  <Sidebar 
                    isCollapsed={sidebarCollapsed} 
                    onToggle={toggleSidebar} 
                  />
                  <div className="flex-1 flex flex-col overflow-hidden">
                    <Header 
                      onSidebarToggle={toggleSidebar}
                      isSidebarCollapsed={sidebarCollapsed}
                    />
                    <main className="flex-1 overflow-auto p-6 bg-muted/30">
                      <div className="max-w-7xl mx-auto">
                        <Routes>
                          <Route path="/" element={<Dashboard />} />
                          <Route path="/attacks" element={<Attacks />} />
                          <Route path="/analytics" element={<Analytics />} />
                          <Route path="/system" element={<SystemHealth />} />
                          <Route path="/alerts" element={<Alerts />} />
                          <Route path="/honeypots" element={<Honeypots />} />
                          <Route path="/users" element={<Users />} />
                          <Route path="/logs" element={<Logs />} />
                          <Route path="/settings" element={<Settings />} />
                        </Routes>
                      </div>
                    </main>
                  </div>
                </div>
              } />
            </Routes>
          </div>
        </Router>
      </WebSocketProvider>
    </AuthProvider>
  );
}

export default App;
