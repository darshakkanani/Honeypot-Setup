import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line
} from 'recharts'
import { 
  ChartBarIcon, 
  GlobeAltIcon, 
  ClockIcon,
  ShieldExclamationIcon
} from '@heroicons/react/24/outline'

// Mock data
const attackTypeData = [
  { name: 'Brute Force', value: 45, color: '#ef4444' },
  { name: 'SQL Injection', value: 23, color: '#8b5cf6' },
  { name: 'Port Scan', value: 18, color: '#3b82f6' },
  { name: 'XSS', value: 14, color: '#f59e0b' }
]

const countryData = [
  { country: 'China', attacks: 234, blocked: 230 },
  { country: 'Russia', attacks: 189, blocked: 185 },
  { country: 'USA', attacks: 156, blocked: 145 },
  { country: 'Brazil', attacks: 98, blocked: 95 },
  { country: 'India', attacks: 87, blocked: 82 }
]

const hourlyData = [
  { hour: '00', attacks: 12 },
  { hour: '04', attacks: 8 },
  { hour: '08', attacks: 25 },
  { hour: '12', attacks: 45 },
  { hour: '16', attacks: 38 },
  { hour: '20', attacks: 52 }
]

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('24h')

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
              <span className="font-medium text-foreground">{entry.value}</span>
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
          <h1 className="text-3xl font-bold text-foreground">Analytics</h1>
          <p className="text-muted-foreground mt-1">
            Deep insights into attack patterns and security trends
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="card-hover border-l-4 border-l-danger-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <ShieldExclamationIcon className="w-4 h-4 mr-2" />
              Total Threats
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">1,247</div>
            <p className="text-xs text-success-600 mt-1">↑ 12% from last period</p>
          </CardContent>
        </Card>

        <Card className="card-hover border-l-4 border-l-blue-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <GlobeAltIcon className="w-4 h-4 mr-2" />
              Countries
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">47</div>
            <p className="text-xs text-muted-foreground mt-1">Unique source countries</p>
          </CardContent>
        </Card>

        <Card className="card-hover border-l-4 border-l-warning-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <ClockIcon className="w-4 h-4 mr-2" />
              Peak Hour
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">20:00</div>
            <p className="text-xs text-muted-foreground mt-1">Most active time</p>
          </CardContent>
        </Card>

        <Card className="card-hover border-l-4 border-l-success-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <ChartBarIcon className="w-4 h-4 mr-2" />
              Block Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">96.1%</div>
            <p className="text-xs text-success-600 mt-1">↑ 2.3% improvement</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attack Types Pie Chart */}
        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Attack Types Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={attackTypeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={120}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {attackTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: any) => [`${value}%`, 'Percentage']}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-4">
              {attackTypeData.map((item, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm text-muted-foreground">{item.name}</span>
                  <span className="text-sm font-medium text-foreground">{item.value}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Hourly Activity */}
        <Card className="card-hover">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Hourly Attack Pattern</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={hourlyData}>
                  <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                  <XAxis 
                    dataKey="hour" 
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
                    dataKey="attacks"
                    stroke="#f59e0b"
                    strokeWidth={3}
                    dot={{ fill: '#f59e0b', strokeWidth: 2, r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Geographic Distribution */}
      <Card className="card-hover">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Top Attack Sources by Country</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={countryData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis type="number" className="text-xs text-muted-foreground" />
                <YAxis 
                  dataKey="country" 
                  type="category" 
                  className="text-xs text-muted-foreground"
                  width={80}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="attacks" fill="#ef4444" name="Total Attacks" />
                <Bar dataKey="blocked" fill="#22c55e" name="Blocked" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Stats Table */}
      <Card className="card-hover">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Detailed Country Statistics</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left p-4 font-medium text-muted-foreground">Country</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Total Attacks</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Blocked</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Block Rate</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {countryData.map((country, index) => {
                  const blockRate = ((country.blocked / country.attacks) * 100).toFixed(1)
                  return (
                    <tr key={index} className="hover:bg-accent/50">
                      <td className="p-4 font-medium text-foreground">{country.country}</td>
                      <td className="p-4 text-foreground">{country.attacks}</td>
                      <td className="p-4 text-foreground">{country.blocked}</td>
                      <td className="p-4 text-foreground">{blockRate}%</td>
                      <td className="p-4">
                        <Badge 
                          variant={parseFloat(blockRate) > 95 ? "success" : parseFloat(blockRate) > 90 ? "warning" : "danger"}
                        >
                          {parseFloat(blockRate) > 95 ? "Excellent" : parseFloat(blockRate) > 90 ? "Good" : "Needs Attention"}
                        </Badge>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
