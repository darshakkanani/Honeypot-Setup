import React, { useState, useEffect } from 'react'
import { 
  UserGroupIcon, 
  UserIcon, 
  PlusIcon, 
  PencilIcon,
  TrashIcon,
  ShieldCheckIcon,
  KeyIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'

interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'analyst' | 'viewer'
  status: 'active' | 'inactive' | 'suspended'
  lastLogin: string
  createdAt: string
  permissions: string[]
  avatar?: string
}

const mockUsers: User[] = [
  {
    id: '1',
    username: 'admin',
    email: 'admin@securehoney.com',
    role: 'admin',
    status: 'active',
    lastLogin: new Date(Date.now() - 300000).toISOString(),
    createdAt: new Date(Date.now() - 86400000 * 30).toISOString(),
    permissions: ['all']
  },
  {
    id: '2',
    username: 'security_analyst',
    email: 'analyst@securehoney.com',
    role: 'analyst',
    status: 'active',
    lastLogin: new Date(Date.now() - 1800000).toISOString(),
    createdAt: new Date(Date.now() - 86400000 * 15).toISOString(),
    permissions: ['view_attacks', 'manage_alerts', 'view_analytics']
  },
  {
    id: '3',
    username: 'john_viewer',
    email: 'john@company.com',
    role: 'viewer',
    status: 'active',
    lastLogin: new Date(Date.now() - 3600000).toISOString(),
    createdAt: new Date(Date.now() - 86400000 * 7).toISOString(),
    permissions: ['view_dashboard', 'view_attacks']
  },
  {
    id: '4',
    username: 'temp_user',
    email: 'temp@company.com',
    role: 'viewer',
    status: 'suspended',
    lastLogin: new Date(Date.now() - 86400000 * 3).toISOString(),
    createdAt: new Date(Date.now() - 86400000 * 5).toISOString(),
    permissions: ['view_dashboard']
  }
]

export default function Users() {
  const [users, setUsers] = useState<User[]>(mockUsers)
  const [filter, setFilter] = useState<string>('')
  const [roleFilter, setRoleFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.username.toLowerCase().includes(filter.toLowerCase()) ||
                         user.email.toLowerCase().includes(filter.toLowerCase())
    const matchesRole = roleFilter === 'all' || user.role === roleFilter
    const matchesStatus = statusFilter === 'all' || user.status === statusFilter
    
    return matchesSearch && matchesRole && matchesStatus
  })

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'danger'
      case 'analyst': return 'honey'
      case 'viewer': return 'secondary'
      default: return 'secondary'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success'
      case 'inactive': return 'secondary'
      case 'suspended': return 'danger'
      default: return 'secondary'
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin': return <ShieldCheckIcon className="w-4 h-4" />
      case 'analyst': return <KeyIcon className="w-4 h-4" />
      case 'viewer': return <EyeIcon className="w-4 h-4" />
      default: return <UserIcon className="w-4 h-4" />
    }
  }

  const handleStatusToggle = (userId: string) => {
    setUsers(prev => prev.map(user => {
      if (user.id === userId) {
        const newStatus = user.status === 'active' ? 'suspended' : 'active'
        return { ...user, status: newStatus }
      }
      return user
    }))
  }

  const activeUsers = users.filter(u => u.status === 'active').length
  const adminUsers = users.filter(u => u.role === 'admin').length

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">User Management</h1>
          <p className="text-muted-foreground mt-1">
            Manage user accounts and permissions
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Badge variant="success" className="px-3 py-1">
            {activeUsers} Active
          </Badge>
          <Badge variant="danger" className="px-3 py-1">
            {adminUsers} Admins
          </Badge>
          <Button variant="honey" onClick={() => setShowCreateModal(true)}>
            <PlusIcon className="w-4 h-4 mr-2" />
            Add User
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Users</p>
                <p className="text-2xl font-bold text-foreground">{users.length}</p>
              </div>
              <UserGroupIcon className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Users</p>
                <p className="text-2xl font-bold text-success-600">{activeUsers}</p>
              </div>
              <UserIcon className="w-8 h-8 text-success-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Administrators</p>
                <p className="text-2xl font-bold text-danger-600">{adminUsers}</p>
              </div>
              <ShieldCheckIcon className="w-8 h-8 text-danger-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="card-hover">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Suspended</p>
                <p className="text-2xl font-bold text-warning-600">
                  {users.filter(u => u.status === 'suspended').length}
                </p>
              </div>
              <EyeSlashIcon className="w-8 h-8 text-warning-500" />
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
                placeholder="Search users..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
            </div>
            <div>
              <select
                className="w-full h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
              >
                <option value="all">All Roles</option>
                <option value="admin">Administrator</option>
                <option value="analyst">Analyst</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>
            <div>
              <select
                className="w-full h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>
            <div>
              <Button
                variant="outline"
                onClick={() => {
                  setFilter('')
                  setRoleFilter('all')
                  setStatusFilter('all')
                }}
                className="w-full"
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">User</th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">Role</th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">Status</th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">Last Login</th>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">Created</th>
                  <th className="text-right py-3 px-4 font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="border-b border-border hover:bg-muted/50">
                    <td className="py-4 px-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-honey-400 to-honey-600 rounded-full flex items-center justify-center">
                          <span className="text-sm font-semibold text-white">
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium text-foreground">{user.username}</p>
                          <p className="text-sm text-muted-foreground">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <Badge variant={getRoleColor(user.role)} className="flex items-center w-fit">
                        {getRoleIcon(user.role)}
                        <span className="ml-1 capitalize">{user.role}</span>
                      </Badge>
                    </td>
                    <td className="py-4 px-4">
                      <Badge variant={getStatusColor(user.status)}>
                        {user.status}
                      </Badge>
                    </td>
                    <td className="py-4 px-4 text-sm text-muted-foreground">
                      {new Date(user.lastLogin).toLocaleString()}
                    </td>
                    <td className="py-4 px-4 text-sm text-muted-foreground">
                      {new Date(user.createdAt).toLocaleDateString()}
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center justify-end space-x-2">
                        <Button size="sm" variant="outline">
                          <PencilIcon className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant={user.status === 'active' ? 'danger' : 'success'}
                          onClick={() => handleStatusToggle(user.id)}
                        >
                          {user.status === 'active' ? 'Suspend' : 'Activate'}
                        </Button>
                        {user.role !== 'admin' && (
                          <Button size="sm" variant="outline">
                            <TrashIcon className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {filteredUsers.length === 0 && (
            <div className="text-center py-12">
              <UserGroupIcon className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No users found</h3>
              <p className="text-muted-foreground">
                No users match your current filter criteria.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Permissions Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Role Permissions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-3">
              <h4 className="font-semibold text-foreground flex items-center">
                <ShieldCheckIcon className="w-5 h-5 mr-2 text-danger-500" />
                Administrator
              </h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Full system access</li>
                <li>• User management</li>
                <li>• System configuration</li>
                <li>• All honeypot controls</li>
              </ul>
            </div>
            
            <div className="space-y-3">
              <h4 className="font-semibold text-foreground flex items-center">
                <KeyIcon className="w-5 h-5 mr-2 text-honey-500" />
                Security Analyst
              </h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• View all attacks</li>
                <li>• Manage alerts</li>
                <li>• Access analytics</li>
                <li>• Control honeypots</li>
              </ul>
            </div>
            
            <div className="space-y-3">
              <h4 className="font-semibold text-foreground flex items-center">
                <EyeIcon className="w-5 h-5 mr-2 text-blue-500" />
                Viewer
              </h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• View dashboard</li>
                <li>• View attack logs</li>
                <li>• Read-only access</li>
                <li>• Basic analytics</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
