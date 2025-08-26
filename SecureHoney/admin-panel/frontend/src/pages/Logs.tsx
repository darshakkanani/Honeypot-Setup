import React, { useState, useEffect } from 'react'
import { 
  DocumentTextIcon, 
  FunnelIcon, 
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
  ClockIcon,
  ServerIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'

interface LogEntry {
  id: string
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'debug'
  source: string
  message: string
  details?: any
  ip?: string
  user?: string
}

const mockLogs: LogEntry[] = [
  {
    id: '1',
    timestamp: new Date(Date.now() - 60000).toISOString(),
    level: 'error',
    source: 'SSH Honeypot',
    message: 'Failed authentication attempt detected',
    details: { attempts: 5, username: 'admin' },
    ip: '192.168.1.100',
    user: 'attacker'
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 120000).toISOString(),
    level: 'warning',
    source: 'Web Honeypot',
    message: 'SQL injection attempt blocked',
    details: { payload: "'; DROP TABLE users; --", endpoint: '/api/login' },
    ip: '10.0.0.45'
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 180000).toISOString(),
    level: 'info',
    source: 'System',
    message: 'Honeypot service started successfully',
    details: { service: 'ssh-honeypot', port: 22 }
  },
  {
    id: '4',
    timestamp: new Date(Date.now() - 240000).toISOString(),
    level: 'debug',
    source: 'Network Monitor',
    message: 'Port scan detected from external IP',
    details: { ports: [22, 80, 443, 3306], duration: '30s' },
    ip: '172.16.0.23'
  },
  {
    id: '5',
    timestamp: new Date(Date.now() - 300000).toISOString(),
    level: 'error',
    source: 'Database',
    message: 'Connection timeout to analytics database',
    details: { timeout: '30s', retries: 3 }
  },
  {
    id: '6',
    timestamp: new Date(Date.now() - 360000).toISOString(),
    level: 'info',
    source: 'Alert System',
    message: 'New alert rule created',
    details: { rule: 'brute_force_detection', threshold: 10 },
    user: 'admin'
  },
  {
    id: '7',
    timestamp: new Date(Date.now() - 420000).toISOString(),
    level: 'warning',
    source: 'FTP Honeypot',
    message: 'Suspicious file upload attempt',
    details: { filename: 'backdoor.php', size: '2.3KB' },
    ip: '203.0.113.5'
  },
  {
    id: '8',
    timestamp: new Date(Date.now() - 480000).toISOString(),
    level: 'info',
    source: 'System',
    message: 'Daily backup completed successfully',
    details: { size: '1.2GB', duration: '45m' }
  }
]

export default function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>(mockLogs)
  const [filter, setFilter] = useState<string>('')
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const [sourceFilter, setSourceFilter] = useState<string>('all')
  const [timeFilter, setTimeFilter] = useState<string>('all')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.message.toLowerCase().includes(filter.toLowerCase()) ||
                         log.source.toLowerCase().includes(filter.toLowerCase()) ||
                         (log.ip && log.ip.includes(filter))
    const matchesLevel = levelFilter === 'all' || log.level === levelFilter
    const matchesSource = sourceFilter === 'all' || log.source === sourceFilter
    
    let matchesTime = true
    if (timeFilter !== 'all') {
      const logTime = new Date(log.timestamp).getTime()
      const now = Date.now()
      switch (timeFilter) {
        case '1h':
          matchesTime = now - logTime <= 3600000
          break
        case '24h':
          matchesTime = now - logTime <= 86400000
          break
        case '7d':
          matchesTime = now - logTime <= 604800000
          break
      }
    }
    
    return matchesSearch && matchesLevel && matchesSource && matchesTime
  })

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'danger'
      case 'warning': return 'warning'
      case 'info': return 'success'
      case 'debug': return 'secondary'
      default: return 'secondary'
    }
  }

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'error': return <ExclamationTriangleIcon className="w-4 h-4" />
      case 'warning': return <ExclamationTriangleIcon className="w-4 h-4" />
      case 'info': return <DocumentTextIcon className="w-4 h-4" />
      case 'debug': return <ServerIcon className="w-4 h-4" />
      default: return <DocumentTextIcon className="w-4 h-4" />
    }
  }

  const uniqueSources = Array.from(new Set(logs.map(log => log.source)))

  // Auto-refresh logs
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      // Simulate new log entries
      const newLog: LogEntry = {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        level: ['info', 'warning', 'error'][Math.floor(Math.random() * 3)] as any,
        source: uniqueSources[Math.floor(Math.random() * uniqueSources.length)],
        message: 'New log entry generated',
        details: { auto: true }
      }
      
      setLogs(prev => [newLog, ...prev.slice(0, 99)]) // Keep last 100 logs
    }, 10000)

    return () => clearInterval(interval)
  }, [autoRefresh, uniqueSources])

  const exportLogs = () => {
    const csvContent = [
      ['Timestamp', 'Level', 'Source', 'Message', 'IP', 'Details'].join(','),
      ...filteredLogs.map(log => [
        log.timestamp,
        log.level,
        log.source,
        `"${log.message}"`,
        log.ip || '',
        `"${JSON.stringify(log.details || {})}"`
      ].join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `honeypot-logs-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const logCounts = {
    total: logs.length,
    error: logs.filter(l => l.level === 'error').length,
    warning: logs.filter(l => l.level === 'warning').length,
    info: logs.filter(l => l.level === 'info').length
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">System Logs</h1>
          <p className="text-muted-foreground mt-1">
            Monitor system events and honeypot activities
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="autoRefresh"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="autoRefresh" className="text-sm text-muted-foreground">
              Auto-refresh
            </label>
          </div>
          <Button variant="outline" onClick={exportLogs}>
            <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Logs</p>
                <p className="text-2xl font-bold text-foreground">{logCounts.total}</p>
              </div>
              <DocumentTextIcon className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Errors</p>
                <p className="text-2xl font-bold text-danger-600">{logCounts.error}</p>
              </div>
              <ExclamationTriangleIcon className="w-8 h-8 text-danger-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Warnings</p>
                <p className="text-2xl font-bold text-warning-600">{logCounts.warning}</p>
              </div>
              <ExclamationTriangleIcon className="w-8 h-8 text-warning-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Info</p>
                <p className="text-2xl font-bold text-success-600">{logCounts.info}</p>
              </div>
              <DocumentTextIcon className="w-8 h-8 text-success-500" />
            </div>
          </CardContent>
        </Card>
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
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Search
              </label>
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search logs..."
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Level
              </label>
              <select
                className="w-full h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
              >
                <option value="all">All Levels</option>
                <option value="error">Error</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
                <option value="debug">Debug</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Source
              </label>
              <select
                className="w-full h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
              >
                <option value="all">All Sources</option>
                {uniqueSources.map(source => (
                  <option key={source} value={source}>{source}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Time Range
              </label>
              <select
                className="w-full h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={timeFilter}
                onChange={(e) => setTimeFilter(e.target.value)}
              >
                <option value="all">All Time</option>
                <option value="1h">Last Hour</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setFilter('')
                  setLevelFilter('all')
                  setSourceFilter('all')
                  setTimeFilter('all')
                }}
                className="w-full"
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Log Entries ({filteredLogs.length})</CardTitle>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <ClockIcon className="w-4 h-4" />
              <span>Last updated: {new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredLogs.map((log) => (
              <div
                key={log.id}
                className="flex items-start space-x-4 p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors"
              >
                <div className="flex-shrink-0 mt-1">
                  <Badge variant={getLevelColor(log.level)} className="flex items-center">
                    {getLevelIcon(log.level)}
                    <span className="ml-1 uppercase text-xs">{log.level}</span>
                  </Badge>
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-foreground truncate">
                      {log.message}
                    </p>
                    <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                    <span>Source: {log.source}</span>
                    {log.ip && <span>IP: {log.ip}</span>}
                    {log.user && <span>User: {log.user}</span>}
                  </div>
                  
                  {log.details && (
                    <details className="mt-2">
                      <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                        Show details
                      </summary>
                      <pre className="mt-1 text-xs bg-muted p-2 rounded overflow-x-auto">
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            ))}
            
            {filteredLogs.length === 0 && (
              <div className="text-center py-12">
                <DocumentTextIcon className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No logs found</h3>
                <p className="text-muted-foreground">
                  No log entries match your current filter criteria.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
