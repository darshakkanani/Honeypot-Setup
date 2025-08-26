import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { 
  MagnifyingGlassIcon, 
  FunnelIcon, 
  ArrowDownTrayIcon,
  EyeIcon 
} from '@heroicons/react/24/outline'
import { formatRelativeTime, getSeverityColor, getAttackTypeColor } from '../lib/utils'

// Mock attack data
const mockAttacks = [
  {
    id: '1',
    type: 'brute_force',
    source_ip: '192.168.1.100',
    target: '/admin/login',
    severity: 'high',
    timestamp: new Date(Date.now() - 300000).toISOString(),
    blocked: true,
    country: 'CN',
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    payload: 'admin:password123'
  },
  {
    id: '2',
    type: 'sql_injection',
    source_ip: '10.0.0.45',
    target: '/api/users',
    severity: 'critical',
    timestamp: new Date(Date.now() - 600000).toISOString(),
    blocked: true,
    country: 'RU',
    user_agent: 'curl/7.68.0',
    payload: "' OR 1=1 --"
  },
  {
    id: '3',
    type: 'port_scan',
    source_ip: '172.16.0.23',
    target: 'tcp:22,80,443',
    severity: 'medium',
    timestamp: new Date(Date.now() - 900000).toISOString(),
    blocked: false,
    country: 'US',
    user_agent: 'nmap',
    payload: 'SYN scan'
  },
  {
    id: '4',
    type: 'xss',
    source_ip: '203.0.113.5',
    target: '/search?q=<script>',
    severity: 'high',
    timestamp: new Date(Date.now() - 1200000).toISOString(),
    blocked: true,
    country: 'BR',
    user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    payload: '<script>alert("XSS")</script>'
  }
]

export default function Attacks() {
  const [attacks] = useState(mockAttacks)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSeverity, setSelectedSeverity] = useState('all')
  const [selectedType, setSelectedType] = useState('all')

  const filteredAttacks = attacks.filter(attack => {
    const matchesSearch = attack.source_ip.includes(searchTerm) || 
                         attack.target.includes(searchTerm) ||
                         attack.type.includes(searchTerm)
    const matchesSeverity = selectedSeverity === 'all' || attack.severity === selectedSeverity
    const matchesType = selectedType === 'all' || attack.type === selectedType
    
    return matchesSearch && matchesSeverity && matchesType
  })

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Attack Logs</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and analyze security threats in real-time
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search by IP, target, or attack type..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <select
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value)}
                className="px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
              >
                <option value="all">All Types</option>
                <option value="brute_force">Brute Force</option>
                <option value="sql_injection">SQL Injection</option>
                <option value="xss">XSS</option>
                <option value="port_scan">Port Scan</option>
                <option value="ddos">DDoS</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Attack List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Recent Attacks ({filteredAttacks.length})</span>
            <Badge variant="outline">{attacks.length} total</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-border">
            {filteredAttacks.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-12 h-12 mx-auto mb-4 bg-muted rounded-full flex items-center justify-center">
                  <MagnifyingGlassIcon className="w-6 h-6 text-muted-foreground" />
                </div>
                <p className="text-muted-foreground">No attacks found matching your criteria</p>
              </div>
            ) : (
              filteredAttacks.map((attack) => (
                <div key={attack.id} className="p-6 hover:bg-accent/50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3 mb-2">
                        <Badge className={getAttackTypeColor(attack.type)} variant="outline">
                          {attack.type.replace('_', ' ').toUpperCase()}
                        </Badge>
                        <Badge className={getSeverityColor(attack.severity)} variant="outline">
                          {attack.severity.toUpperCase()}
                        </Badge>
                        {attack.blocked && (
                          <Badge variant="success">BLOCKED</Badge>
                        )}
                        <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                          {attack.country}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground mb-1">Source IP</p>
                          <p className="font-mono text-foreground">{attack.source_ip}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground mb-1">Target</p>
                          <p className="font-mono text-foreground truncate">{attack.target}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground mb-1">User Agent</p>
                          <p className="text-foreground truncate">{attack.user_agent}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground mb-1">Payload</p>
                          <p className="font-mono text-foreground truncate">{attack.payload}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2 ml-4">
                      <div className="text-right">
                        <p className="text-sm text-muted-foreground">
                          {formatRelativeTime(attack.timestamp)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(attack.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <Button variant="ghost" size="sm">
                        <EyeIcon className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
