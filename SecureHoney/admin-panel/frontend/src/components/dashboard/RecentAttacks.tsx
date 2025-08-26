import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { formatRelativeTime, getSeverityColor, getAttackTypeColor } from '../../lib/utils'

interface Attack {
  id: string
  type: string
  source_ip: string
  target: string
  severity: string
  timestamp: string
  blocked: boolean
  country?: string
}

interface RecentAttacksProps {
  attacks: Attack[]
  limit?: number
}

export function RecentAttacks({ attacks, limit = 5 }: RecentAttacksProps) {
  const displayAttacks = attacks.slice(0, limit)

  return (
    <Card className="card-hover">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg font-semibold">Recent Attacks</CardTitle>
        <Badge variant="outline" className="text-xs">
          {attacks.length} total
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        {displayAttacks.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 mx-auto mb-4 bg-success-100 dark:bg-success-900 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-muted-foreground">No recent attacks detected</p>
          </div>
        ) : (
          displayAttacks.map((attack) => (
            <div key={attack.id} className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors">
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <Badge 
                    className={getAttackTypeColor(attack.type)}
                    variant="outline"
                  >
                    {attack.type.replace('_', ' ').toUpperCase()}
                  </Badge>
                  <Badge 
                    className={getSeverityColor(attack.severity)}
                    variant="outline"
                  >
                    {attack.severity.toUpperCase()}
                  </Badge>
                  {attack.blocked && (
                    <Badge variant="success">
                      BLOCKED
                    </Badge>
                  )}
                </div>
                <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                  <span className="font-mono">{attack.source_ip}</span>
                  <span>→</span>
                  <span className="truncate">{attack.target}</span>
                  {attack.country && (
                    <span className="text-xs bg-muted px-2 py-1 rounded">
                      {attack.country}
                    </span>
                  )}
                </div>
              </div>
              <div className="text-xs text-muted-foreground ml-4">
                {formatRelativeTime(attack.timestamp)}
              </div>
            </div>
          ))
        )}
        
        {attacks.length > limit && (
          <div className="text-center pt-4 border-t border-border">
            <button className="text-sm text-primary hover:underline">
              View all {attacks.length} attacks
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
