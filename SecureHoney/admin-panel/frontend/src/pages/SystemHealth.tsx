import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { 
  ServerIcon, 
  CpuChipIcon, 
  CircleStackIcon, 
  WifiIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts'

// Mock system data
const systemMetrics = {
  cpu: { usage: 23, cores: 8, temperature: 45 },
  memory: { usage: 67, total: 32, used: 21.4 },
  disk: { usage: 45, total: 1000, used: 450 },
  network: { status: 'healthy', latency: 12, throughput: 850 }
}

const services = [
  { name: 'Honeypot Engine', status: 'running', uptime: '15d 4h 23m', cpu: 12, memory: 256 },
  { name: 'Admin Backend', status: 'running', uptime: '15d 4h 23m', cpu: 8, memory: 128 },
  { name: 'Database', status: 'running', uptime: '15d 4h 23m', cpu: 15, memory: 512 },
  { name: 'Redis Cache', status: 'running', uptime: '15d 4h 23m', cpu: 3, memory: 64 },
  { name: 'Log Processor', status: 'warning', uptime: '2h 15m', cpu: 25, memory: 192 },
  { name: 'Alert System', status: 'running', uptime: '15d 4h 23m', cpu: 5, memory: 32 }
]

const performanceData = [
  { time: '00:00', cpu: 15, memory: 45, disk: 30 },
  { time: '04:00', cpu: 12, memory: 42, disk: 28 },
  { time: '08:00', cpu: 25, memory: 55, disk: 35 },
  { time: '12:00', cpu: 35, memory: 68, disk: 42 },
  { time: '16:00', cpu: 28, memory: 62, disk: 38 },
  { time: '20:00', cpu: 23, memory: 67, disk: 45 }
]

export default function SystemHealth() {
  const [metrics, setMetrics] = useState(systemMetrics)
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
      // Simulate real-time metric updates
      setMetrics(prev => ({
        ...prev,
        cpu: { ...prev.cpu, usage: prev.cpu.usage + (Math.random() - 0.5) * 2 },
        memory: { ...prev.memory, usage: Math.max(0, Math.min(100, prev.memory.usage + (Math.random() - 0.5) * 1)) }
      }))
    }, 5000)

    return () => clearInterval(timer)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'success'
      case 'warning':
        return 'warning'
      case 'error':
        return 'danger'
      default:
        return 'secondary'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircleIcon className="w-4 h-4" />
      case 'warning':
      case 'error':
        return <ExclamationTriangleIcon className="w-4 h-4" />
      default:
        return <ServerIcon className="w-4 h-4" />
    }
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg shadow-lg p-3">
          <p className="text-sm font-medium text-foreground mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center space-x-2 text-sm">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-muted-foreground">{entry.dataKey}:</span>
              <span className="font-medium text-foreground">{entry.value}%</span>
            </div>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">System Health</h1>
          <p className="text-muted-foreground mt-1">
            Monitor system performance and service status
          </p>
        </div>
        <div className="text-sm text-muted-foreground">
          Last updated: {currentTime.toLocaleTimeString()}
        </div>
      </div>

      {/* System Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="card-hover border-l-4 border-l-blue-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <CpuChipIcon className="w-4 h-4 mr-2" />
              CPU Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{Math.round(metrics.cpu.usage)}%</div>
            <div className="mt-2 bg-muted rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${metrics.cpu.usage}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.cpu.cores} cores • {metrics.cpu.temperature}°C
            </p>
          </CardContent>
        </Card>

        <Card className="card-hover border-l-4 border-l-green-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <CircleStackIcon className="w-4 h-4 mr-2" />
              Memory Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{Math.round(metrics.memory.usage)}%</div>
            <div className="mt-2 bg-muted rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${metrics.memory.usage}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.memory.used}GB / {metrics.memory.total}GB
            </p>
          </CardContent>
        </Card>

        <Card className="card-hover border-l-4 border-l-yellow-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <ServerIcon className="w-4 h-4 mr-2" />
              Disk Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{metrics.disk.usage}%</div>
            <div className="mt-2 bg-muted rounded-full h-2">
              <div 
                className="bg-yellow-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${metrics.disk.usage}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.disk.used}GB / {metrics.disk.total}GB
            </p>
          </CardContent>
        </Card>

        <Card className="card-hover border-l-4 border-l-purple-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <WifiIcon className="w-4 h-4 mr-2" />
              Network
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{metrics.network.latency}ms</div>
            <Badge variant="success" className="mt-2">
              {metrics.network.status.toUpperCase()}
            </Badge>
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.network.throughput} Mbps throughput
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Chart */}
      <Card className="card-hover">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">System Performance Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis 
                  dataKey="time" 
                  className="text-xs text-muted-foreground"
                  tick={{ fontSize: 12 }}
                />
                <YAxis 
                  className="text-xs text-muted-foreground"
                  tick={{ fontSize: 12 }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                  name="CPU"
                />
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={{ fill: '#22c55e', strokeWidth: 2, r: 4 }}
                  name="Memory"
                />
                <Line
                  type="monotone"
                  dataKey="disk"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={{ fill: '#f59e0b', strokeWidth: 2, r: 4 }}
                  name="Disk"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          
          {/* Legend */}
          <div className="flex items-center justify-center space-x-6 mt-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full" />
              <span className="text-sm text-muted-foreground">CPU Usage</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-sm text-muted-foreground">Memory Usage</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full" />
              <span className="text-sm text-muted-foreground">Disk Usage</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Services Status */}
      <Card className="card-hover">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Service Status</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-border">
            {services.map((service, index) => (
              <div key={index} className="p-4 hover:bg-accent/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${
                      service.status === 'running' ? 'bg-success-100 text-success-600 dark:bg-success-900 dark:text-success-400' :
                      service.status === 'warning' ? 'bg-warning-100 text-warning-600 dark:bg-warning-900 dark:text-warning-400' :
                      'bg-danger-100 text-danger-600 dark:bg-danger-900 dark:text-danger-400'
                    }`}>
                      {getStatusIcon(service.status)}
                    </div>
                    <div>
                      <h3 className="font-medium text-foreground">{service.name}</h3>
                      <p className="text-sm text-muted-foreground">Uptime: {service.uptime}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">CPU: {service.cpu}%</p>
                      <p className="text-sm text-muted-foreground">RAM: {service.memory}MB</p>
                    </div>
                    <Badge variant={getStatusColor(service.status)}>
                      {service.status.toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
