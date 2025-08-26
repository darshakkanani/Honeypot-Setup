import React, { useState, useEffect } from 'react'
import { 
  CubeIcon, 
  ServerIcon, 
  PlayIcon, 
  StopIcon, 
  CogIcon,
  PlusIcon,
  EyeIcon,
  TrashIcon
} from '@heroicons/react/24/outline'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'

interface Honeypot {
  id: string
  name: string
  type: 'ssh' | 'http' | 'ftp' | 'smtp' | 'telnet' | 'mysql'
  status: 'running' | 'stopped' | 'error'
  port: number
  ip: string
  interactions: number
  lastActivity: string
  uptime: string
  description: string
}

const mockHoneypots: Honeypot[] = [
  {
    id: '1',
    name: 'SSH Trap',
    type: 'ssh',
    status: 'running',
    port: 22,
    ip: '192.168.1.10',
    interactions: 1247,
    lastActivity: new Date(Date.now() - 300000).toISOString(),
    uptime: '15d 4h 23m',
    description: 'SSH honeypot simulating vulnerable server'
  },
  {
    id: '2',
    name: 'Web Server Decoy',
    type: 'http',
    status: 'running',
    port: 80,
    ip: '192.168.1.11',
    interactions: 892,
    lastActivity: new Date(Date.now() - 120000).toISOString(),
    uptime: '12d 8h 15m',
    description: 'HTTP honeypot with fake admin panel'
  },
  {
    id: '3',
    name: 'FTP Honeypot',
    type: 'ftp',
    status: 'stopped',
    port: 21,
    ip: '192.168.1.12',
    interactions: 234,
    lastActivity: new Date(Date.now() - 3600000).toISOString(),
    uptime: '0d 0h 0m',
    description: 'FTP server honeypot for file transfer attacks'
  },
  {
    id: '4',
    name: 'Database Trap',
    type: 'mysql',
    status: 'running',
    port: 3306,
    ip: '192.168.1.13',
    interactions: 567,
    lastActivity: new Date(Date.now() - 600000).toISOString(),
    uptime: '8d 12h 45m',
    description: 'MySQL honeypot with fake database'
  },
  {
    id: '5',
    name: 'Mail Server Decoy',
    type: 'smtp',
    status: 'error',
    port: 25,
    ip: '192.168.1.14',
    interactions: 89,
    lastActivity: new Date(Date.now() - 7200000).toISOString(),
    uptime: '0d 0h 0m',
    description: 'SMTP honeypot for email-based attacks'
  }
]

export default function Honeypots() {
  const [honeypots, setHoneypots] = useState<Honeypot[]>(mockHoneypots)
  const [filter, setFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')

  const filteredHoneypots = honeypots.filter(honeypot => {
    const matchesSearch = honeypot.name.toLowerCase().includes(filter.toLowerCase()) ||
                         honeypot.description.toLowerCase().includes(filter.toLowerCase())
    const matchesStatus = statusFilter === 'all' || honeypot.status === statusFilter
    const matchesType = typeFilter === 'all' || honeypot.type === typeFilter
    
    return matchesSearch && matchesStatus && matchesType
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'success'
      case 'stopped': return 'secondary'
      case 'error': return 'danger'
      default: return 'secondary'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'ssh': return '🔐'
      case 'http': return '🌐'
      case 'ftp': return '📁'
      case 'smtp': return '📧'
      case 'telnet': return '💻'
      case 'mysql': return '🗄️'
      default: return '🔧'
    }
  }

  const handleStatusToggle = (honeypotId: string) => {
    setHoneypots(prev => prev.map(honeypot => {
      if (honeypot.id === honeypotId) {
        const newStatus = honeypot.status === 'running' ? 'stopped' : 'running'
        return { ...honeypot, status: newStatus }
      }
      return honeypot
    }))
  }

  const runningCount = honeypots.filter(h => h.status === 'running').length
  const totalInteractions = honeypots.reduce((sum, h) => sum + h.interactions, 0)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Honeypots</h1>
          <p className="text-muted-foreground mt-1">
            Manage and monitor your honeypot deployments
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Badge variant="success" className="px-3 py-1">
            {runningCount} Running
          </Badge>
          <Badge variant="honey" className="px-3 py-1">
            {totalInteractions.toLocaleString()} Total Interactions
          </Badge>
          <Button variant="honey">
            <PlusIcon className="w-4 h-4 mr-2" />
            Deploy New
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Honeypots</p>
                <p className="text-2xl font-bold text-foreground">{honeypots.length}</p>
              </div>
              <CubeIcon className="w-8 h-8 text-honey-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Running</p>
                <p className="text-2xl font-bold text-success-600">{runningCount}</p>
              </div>
              <PlayIcon className="w-8 h-8 text-success-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Interactions</p>
                <p className="text-2xl font-bold text-foreground">{totalInteractions.toLocaleString()}</p>
              </div>
              <EyeIcon className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Errors</p>
                <p className="text-2xl font-bold text-danger-600">
                  {honeypots.filter(h => h.status === 'error').length}
                </p>
              </div>
              <ServerIcon className="w-8 h-8 text-danger-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Input
                placeholder="Search honeypots..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
            </div>
            <div>
              <select
                className="w-full h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All Statuses</option>
                <option value="running">Running</option>
                <option value="stopped">Stopped</option>
                <option value="error">Error</option>
              </select>
            </div>
            <div>
              <select
                className="w-full h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="all">All Types</option>
                <option value="ssh">SSH</option>
                <option value="http">HTTP</option>
                <option value="ftp">FTP</option>
                <option value="smtp">SMTP</option>
                <option value="mysql">MySQL</option>
                <option value="telnet">Telnet</option>
              </select>
            </div>
            <div>
              <Button
                variant="outline"
                onClick={() => {
                  setFilter('')
                  setStatusFilter('all')
                  setTypeFilter('all')
                }}
                className="w-full"
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Honeypots Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredHoneypots.map((honeypot) => (
          <Card key={honeypot.id} className="card-hover">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getTypeIcon(honeypot.type)}</span>
                  <div>
                    <CardTitle className="text-lg">{honeypot.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">{honeypot.type.toUpperCase()}</p>
                  </div>
                </div>
                <Badge variant={getStatusColor(honeypot.status)}>
                  {honeypot.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                {honeypot.description}
              </p>
              
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">IP Address:</span>
                  <span className="font-mono">{honeypot.ip}:{honeypot.port}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Interactions:</span>
                  <span className="font-semibold">{honeypot.interactions.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Uptime:</span>
                  <span>{honeypot.uptime}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Last Activity:</span>
                  <span>{new Date(honeypot.lastActivity).toLocaleString()}</span>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button
                  size="sm"
                  variant={honeypot.status === 'running' ? 'danger' : 'success'}
                  onClick={() => handleStatusToggle(honeypot.id)}
                  className="flex-1"
                >
                  {honeypot.status === 'running' ? (
                    <>
                      <StopIcon className="w-4 h-4 mr-1" />
                      Stop
                    </>
                  ) : (
                    <>
                      <PlayIcon className="w-4 h-4 mr-1" />
                      Start
                    </>
                  )}
                </Button>
                <Button size="sm" variant="outline">
                  <CogIcon className="w-4 h-4" />
                </Button>
                <Button size="sm" variant="outline">
                  <EyeIcon className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {filteredHoneypots.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <CubeIcon className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">No honeypots found</h3>
            <p className="text-muted-foreground mb-4">
              No honeypots match your current filter criteria.
            </p>
            <Button variant="honey">
              <PlusIcon className="w-4 h-4 mr-2" />
              Deploy Your First Honeypot
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
