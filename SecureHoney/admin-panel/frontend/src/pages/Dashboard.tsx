import React, { useState, useEffect } from 'react'
import { 
  ShieldExclamationIcon, 
  ServerIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline'
import { StatsCard } from '../components/dashboard/StatsCard'
import { AttackChart } from '../components/dashboard/AttackChart'
import { RecentAttacks } from '../components/dashboard/RecentAttacks'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'

// Mock data - in real app this would come from API
const mockStats = {
  totalAttacks: 1247,
  blockedAttacks: 1198,
  activeHoneypots: 12,
  criticalAlerts: 3
}

const mockChartData = [
  { time: '00:00', attacks: 45, blocked: 42 },
  { time: '04:00', attacks: 32, blocked: 30 },
  { time: '08:00', attacks: 78, blocked: 75 },
  { time: '12:00', attacks: 123, blocked: 118 },
  { time: '16:00', attacks: 89, blocked: 85 },
  { time: '20:00', attacks: 156, blocked: 148 },
]

const mockRecentAttacks = [
  {
    id: '1',
    type: 'brute_force',
    source_ip: '192.168.1.100',
    target: '/admin/login',
    severity: 'high',
    timestamp: new Date(Date.now() - 300000).toISOString(),
    blocked: true,
    country: 'CN'
  },
  {
    id: '2',
    type: 'sql_injection',
    source_ip: '10.0.0.45',
    target: '/api/users',
    severity: 'critical',
    timestamp: new Date(Date.now() - 600000).toISOString(),
    blocked: true,
    country: 'RU'
  },
  {
    id: '3',
    type: 'port_scan',
    source_ip: '172.16.0.23',
    target: 'tcp:22,80,443',
    severity: 'medium',
    timestamp: new Date(Date.now() - 900000).toISOString(),
    blocked: false,
    country: 'US'
  },
  {
    id: '4',
    type: 'xss',
    source_ip: '203.0.113.5',
    target: '/search?q=<script>',
    severity: 'high',
    timestamp: new Date(Date.now() - 1200000).toISOString(),
    blocked: true,
    country: 'BR'
  },
  {
    id: '5',
    type: 'ddos',
    source_ip: '198.51.100.10',
    target: '/',
    severity: 'critical',
    timestamp: new Date(Date.now() - 1500000).toISOString(),
    blocked: true,
    country: 'KR'
  }
]

export default function Dashboard() {
  const [stats, setStats] = useState(mockStats)
  const [chartData, setChartData] = useState(mockChartData)
  const [recentAttacks, setRecentAttacks] = useState(mockRecentAttacks)

  // In real app, this would fetch data from API
  useEffect(() => {
    // Simulate real-time updates
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        totalAttacks: prev.totalAttacks + Math.floor(Math.random() * 3),
        blockedAttacks: prev.blockedAttacks + Math.floor(Math.random() * 3)
      }))
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const blockRate = ((stats.blockedAttacks / stats.totalAttacks) * 100).toFixed(1)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Real-time security monitoring and threat analysis
          </p>
        </div>
        <div className="text-sm text-muted-foreground">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Attacks"
          value={stats.totalAttacks}
          change={{ value: 12.5, type: 'increase' }}
          trend="up"
          icon={<ShieldExclamationIcon className="w-5 h-5" />}
          className="border-l-4 border-l-danger-500"
        />
        <StatsCard
          title="Blocked Attacks"
          value={stats.blockedAttacks}
          change={{ value: 8.3, type: 'increase' }}
          trend="up"
          icon={<ShieldExclamationIcon className="w-5 h-5" />}
          className="border-l-4 border-l-success-500"
        />
        <StatsCard
          title="Active Honeypots"
          value={stats.activeHoneypots}
          icon={<ServerIcon className="w-5 h-5" />}
          className="border-l-4 border-l-honey-500"
        />
        <StatsCard
          title="Critical Alerts"
          value={stats.criticalAlerts}
          change={{ value: 25.0, type: 'decrease' }}
          trend="down"
          icon={<ExclamationTriangleIcon className="w-5 h-5" />}
          className="border-l-4 border-l-warning-500"
        />
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <AttackChart data={chartData} type="area" />
        </div>
        <div>
          <RecentAttacks attacks={recentAttacks} limit={5} />
        </div>
      </div>

      {/* Additional Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center">
              <ChartBarIcon className="w-5 h-5 mr-2 text-honey-500" />
              Block Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-success-600 mb-2">
              {blockRate}%
            </div>
            <p className="text-sm text-muted-foreground">
              of attacks successfully blocked
            </p>
            <div className="mt-4 bg-muted rounded-full h-2">
              <div 
                className="bg-success-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${blockRate}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center">
              <ServerIcon className="w-5 h-5 mr-2 text-blue-500" />
              System Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">CPU Usage</span>
                <span className="text-sm font-medium">23%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Memory</span>
                <span className="text-sm font-medium">67%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Disk</span>
                <span className="text-sm font-medium">45%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Network</span>
                <span className="text-sm font-medium text-success-600">Healthy</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 mr-2 text-warning-500" />
              Top Threats
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Brute Force</span>
                <span className="text-sm font-medium">45%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">SQL Injection</span>
                <span className="text-sm font-medium">23%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Port Scan</span>
                <span className="text-sm font-medium">18%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">XSS</span>
                <span className="text-sm font-medium">14%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
