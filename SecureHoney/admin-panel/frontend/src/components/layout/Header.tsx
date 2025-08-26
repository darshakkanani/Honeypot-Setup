import React from 'react'
import { 
  BellIcon, 
  MagnifyingGlassIcon, 
  SunIcon, 
  MoonIcon, 
  ComputerDesktopIcon,
  Bars3Icon
} from '@heroicons/react/24/outline'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Badge } from '../ui/Badge'
import { useTheme } from '../../hooks/useTheme'
import { cn } from '../../lib/utils'

interface HeaderProps {
  onSidebarToggle: () => void
  isSidebarCollapsed: boolean
}

export function Header({ onSidebarToggle, isSidebarCollapsed }: HeaderProps) {
  const { theme, setTheme } = useTheme()
  const [notifications] = React.useState(3) // Mock notification count

  const getThemeIcon = () => {
    switch (theme) {
      case 'light':
        return <SunIcon className="w-4 h-4" />
      case 'dark':
        return <MoonIcon className="w-4 h-4" />
      default:
        return <ComputerDesktopIcon className="w-4 h-4" />
    }
  }

  const cycleTheme = () => {
    if (theme === 'light') setTheme('dark')
    else if (theme === 'dark') setTheme('system')
    else setTheme('light')
  }

  return (
    <header className="bg-card border-b border-border px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onSidebarToggle}
            className="md:hidden"
          >
            <Bars3Icon className="w-5 h-5" />
          </Button>
          
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search attacks, IPs, or events..."
              className="pl-10 w-64 md:w-80"
            />
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-2">
          {/* Theme toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={cycleTheme}
            title={`Current theme: ${theme}`}
          >
            {getThemeIcon()}
          </Button>

          {/* Notifications */}
          <div className="relative">
            <Button variant="ghost" size="icon">
              <BellIcon className="w-5 h-5" />
            </Button>
            {notifications > 0 && (
              <Badge
                variant="danger"
                className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
              >
                {notifications}
              </Badge>
            )}
          </div>

          {/* User menu */}
          <div className="flex items-center space-x-3 pl-3 border-l border-border">
            <div className="hidden md:block text-right">
              <p className="text-sm font-medium text-foreground">Admin User</p>
              <p className="text-xs text-muted-foreground">Administrator</p>
            </div>
            <div className="w-8 h-8 bg-gradient-to-br from-honey-400 to-honey-600 rounded-full flex items-center justify-center cursor-pointer hover:shadow-glow transition-shadow">
              <span className="text-xs font-semibold text-white">A</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
