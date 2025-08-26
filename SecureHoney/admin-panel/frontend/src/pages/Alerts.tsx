import React, { useState, useEffect } from 'react'
import { 
  ExclamationTriangleIcon, 
  BellIcon, 
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  FunnelIcon
} from '@heroicons/react/24/outline'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'

interface Alert {
  id: string
  title: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'active' | 'acknowledged' | 'resolved'
  timestamp: string
  source: string
  category: string
}

const mockAlerts: Alert[] = [
  {
    id: '1',
    title: 'Multiple Failed Login Attempts',
    description: 'Detected 15 failed login attempts from IP 192.168.1.100 in the last 5 minutes',
    severity: 'high',
    status: 'active',
    timestamp: new Date(Date.now() - 300000).toISOString(),
    source: 'SSH Honeypot',
    category: 'Authentication'
  },
  {
    id: '2',
    title: 'SQL Injection Attempt Blocked',
    description: 'Malicious SQL injection payload detected and blocked on /api/users endpoint',
    severity: 'critical',
    status: 'active',
    timestamp: new Date(Date.now() - 600000).toISOString(),
    source: 'Web Honeypot',
    category: 'Web Attack'
  },
  {
    id: '3',
    title: 'Unusual Port Scanning Activity',
    description: 'Systematic port scan detected from 172.16.0.23 targeting multiple services',
    severity: 'medium',
    status: 'acknowledged',
    timestamp: new Date(Date.now() - 900000).toISOString(),
    source: 'Network Monitor',
    category: 'Reconnaissance'
  },
  {
    id: '4',
    title: 'DDoS Attack Mitigated',
    description: 'Large volume of requests from botnet successfully mitigated',
    severity: 'critical',
    status: 'resolved',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    source: 'Traffic Analyzer',
    category: 'DDoS'
  }
]

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts)
  const [filter, setFilter] = useState<string>('')
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const filteredAlerts = alerts.filter(alert => {
    const matchesSearch = alert.title.toLowerCase().includes(filter.toLowerCase()) ||
                         alert.description.toLowerCase().includes(filter.toLowerCase())
    const matchesSeverity = severityFilter === 'all' || alert.severity === severityFilter
    const matchesStatus = statusFilter === 'all' || alert.status === statusFilter
    
    return matchesSearch && matchesSeverity && matchesStatus
  })

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'danger'
      case 'high': return 'warning'
      case 'medium': return 'honey'
      case 'low': return 'secondary'
      default: return 'secondary'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <ExclamationTriangleIcon className="w-4 h-4 text-danger-500" />
      case 'acknowledged':
        return <ClockIcon className="w-4 h-4 text-warning-500" />
      case 'resolved':
        return <CheckCircleIcon className="w-4 h-4 text-success-500" />
      default:
        return <BellIcon className="w-4 h-4" />
    }
  }

  const handleStatusChange = (alertId: string, newStatus: Alert['status']) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, status: newStatus } : alert
    ))
  }

  const activeAlerts = alerts.filter(a => a.status === 'active').length
  const criticalAlerts = alerts.filter(a => a.severity === 'critical' && a.status === 'active').length

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Security Alerts</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and manage security alerts across all honeypots
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="danger" className="px-3 py-1">
            {activeAlerts} Active
          </Badge>
          <Badge variant="warning" className="px-3 py-1">
            {criticalAlerts} Critical
          </Badge>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <FunnelIcon className="w-5 h-5 mr-2" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Search
              </label>
              <Input
                placeholder="Search alerts..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Severity
              </label>
              <select
                className="w-full h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Status
              </label>
              <select
                className="w-full h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setFilter('')
                  setSeverityFilter('all')
                  setStatusFilter('all')
                }}
                className="w-full"
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.map((alert) => (
          <Card key={alert.id} className="card-hover">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    {getStatusIcon(alert.status)}
                    <h3 className="text-lg font-semibold text-foreground">
                      {alert.title}
                    </h3>
                    <Badge variant={getSeverityColor(alert.severity)}>
                      {alert.severity.toUpperCase()}
                    </Badge>
                  </div>
                  
                  <p className="text-muted-foreground mb-3">
                    {alert.description}
                  </p>
                  
                  <div className="flex items-center space-x-6 text-sm text-muted-foreground">
                    <span>Source: {alert.source}</span>
                    <span>Category: {alert.category}</span>
                    <span>Time: {new Date(alert.timestamp).toLocaleString()}</span>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2 ml-4">
                  {alert.status === 'active' && (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleStatusChange(alert.id, 'acknowledged')}
                      >
                        Acknowledge
                      </Button>
                      <Button
                        size="sm"
                        variant="success"
                        onClick={() => handleStatusChange(alert.id, 'resolved')}
                      >
                        Resolve
                      </Button>
                    </>
                  )}
                  {alert.status === 'acknowledged' && (
                    <Button
                      size="sm"
                      variant="success"
                      onClick={() => handleStatusChange(alert.id, 'resolved')}
                    >
                      Resolve
                    </Button>
                  )}
                  {alert.status === 'resolved' && (
                    <Badge variant="success">Resolved</Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {filteredAlerts.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center">
              <BellIcon className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No alerts found</h3>
              <p className="text-muted-foreground">
                No alerts match your current filter criteria.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
