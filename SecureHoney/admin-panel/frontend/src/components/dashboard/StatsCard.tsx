import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { cn } from '../../lib/utils'

interface StatsCardProps {
  title: string
  value: string | number
  change?: {
    value: number
    type: 'increase' | 'decrease'
  }
  icon?: React.ReactNode
  className?: string
  trend?: 'up' | 'down' | 'neutral'
}

export function StatsCard({ 
  title, 
  value, 
  change, 
  icon, 
  className,
  trend = 'neutral'
}: StatsCardProps) {
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return change?.type === 'increase' ? 'text-success-600' : 'text-danger-600'
      case 'down':
        return change?.type === 'decrease' ? 'text-success-600' : 'text-danger-600'
      default:
        return 'text-muted-foreground'
    }
  }

  const getChangeIcon = () => {
    if (!change) return null
    
    const isPositive = change.type === 'increase'
    return (
      <svg
        className={cn("w-4 h-4", getTrendColor())}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d={isPositive ? "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" : "M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"}
        />
      </svg>
    )
  }

  return (
    <Card className={cn("card-hover", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon && (
          <div className="text-muted-foreground">
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-foreground mb-1">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
        {change && (
          <div className="flex items-center space-x-1">
            {getChangeIcon()}
            <span className={cn("text-xs font-medium", getTrendColor())}>
              {Math.abs(change.value)}% from last period
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
