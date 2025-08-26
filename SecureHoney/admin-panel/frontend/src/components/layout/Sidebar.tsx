import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { 
  HomeIcon, 
  ShieldExclamationIcon, 
  ChartBarIcon, 
  ServerIcon, 
  CogIcon, 
  UserGroupIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  CubeIcon
} from '@heroicons/react/24/outline'
import { cn } from '../../lib/utils'

interface SidebarProps {
  isCollapsed: boolean
  onToggle: () => void
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Attacks', href: '/attacks', icon: ShieldExclamationIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'System Health', href: '/system', icon: ServerIcon },
  { name: 'Alerts', href: '/alerts', icon: ExclamationTriangleIcon },
  { name: 'Honeypots', href: '/honeypots', icon: CubeIcon },
  { name: 'Users', href: '/users', icon: UserGroupIcon },
  { name: 'Logs', href: '/logs', icon: DocumentTextIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
]

export function Sidebar({ isCollapsed, onToggle }: SidebarProps) {
  const location = useLocation()

  return (
    <div className={cn(
      "bg-card border-r border-border transition-all duration-300 flex flex-col",
      isCollapsed ? "w-16" : "w-64"
    )}>
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-honey-500 rounded-lg flex items-center justify-center">
                <CubeIcon className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-lg text-foreground">SecureHoney</span>
            </div>
          )}
          <button
            onClick={onToggle}
            className="p-1.5 rounded-md hover:bg-accent transition-colors"
          >
            <svg
              className={cn("w-4 h-4 transition-transform", isCollapsed && "rotate-180")}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={cn(
                "flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors group",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent",
                isCollapsed ? "justify-center" : "justify-start"
              )}
              title={isCollapsed ? item.name : undefined}
            >
              <item.icon className={cn("w-5 h-5 flex-shrink-0", !isCollapsed && "mr-3")} />
              {!isCollapsed && <span>{item.name}</span>}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className={cn(
          "flex items-center",
          isCollapsed ? "justify-center" : "space-x-3"
        )}>
          <div className="w-8 h-8 bg-gradient-to-br from-honey-400 to-honey-600 rounded-full flex items-center justify-center">
            <span className="text-xs font-semibold text-white">A</span>
          </div>
          {!isCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">Admin User</p>
              <p className="text-xs text-muted-foreground truncate">admin@securehoney.com</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
