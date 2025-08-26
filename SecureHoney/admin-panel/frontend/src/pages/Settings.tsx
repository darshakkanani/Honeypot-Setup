import React, { useState } from 'react'
import { 
  CogIcon, 
  BellIcon, 
  ShieldCheckIcon,
  ServerIcon,
  UserIcon,
  KeyIcon,
  CircleStackIcon,
  GlobeAltIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'

interface Settings {
  general: {
    systemName: string
    timezone: string
    language: string
    autoBackup: boolean
    backupRetention: number
  }
  security: {
    sessionTimeout: number
    maxLoginAttempts: number
    requireMFA: boolean
    passwordPolicy: {
      minLength: number
      requireSpecialChars: boolean
      requireNumbers: boolean
      requireUppercase: boolean
    }
  }
  notifications: {
    emailAlerts: boolean
    slackIntegration: boolean
    webhookUrl: string
    alertThresholds: {
      criticalAlerts: number
      highVolumeAttacks: number
      systemErrors: number
    }
  }
  honeypots: {
    defaultPorts: {
      ssh: number
      http: number
      ftp: number
      smtp: number
    }
    logRetention: number
    autoResponse: boolean
    geoBlocking: boolean
  }
  database: {
    host: string
    port: number
    name: string
    backupSchedule: string
    compressionEnabled: boolean
  }
}

const defaultSettings: Settings = {
  general: {
    systemName: 'SecureHoney',
    timezone: 'UTC',
    language: 'en',
    autoBackup: true,
    backupRetention: 30
  },
  security: {
    sessionTimeout: 30,
    maxLoginAttempts: 5,
    requireMFA: false,
    passwordPolicy: {
      minLength: 8,
      requireSpecialChars: true,
      requireNumbers: true,
      requireUppercase: true
    }
  },
  notifications: {
    emailAlerts: true,
    slackIntegration: false,
    webhookUrl: '',
    alertThresholds: {
      criticalAlerts: 1,
      highVolumeAttacks: 100,
      systemErrors: 10
    }
  },
  honeypots: {
    defaultPorts: {
      ssh: 22,
      http: 80,
      ftp: 21,
      smtp: 25
    },
    logRetention: 90,
    autoResponse: true,
    geoBlocking: false
  },
  database: {
    host: 'localhost',
    port: 5432,
    name: 'securehoney',
    backupSchedule: 'daily',
    compressionEnabled: true
  }
}

export default function Settings() {
  const [settings, setSettings] = useState<Settings>(defaultSettings)
  const [activeTab, setActiveTab] = useState<string>('general')
  const [hasChanges, setHasChanges] = useState(false)

  const updateSetting = (section: keyof Settings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }))
    setHasChanges(true)
  }

  const updateNestedSetting = (section: keyof Settings, parentKey: string, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [parentKey]: {
          ...(prev[section] as any)[parentKey],
          [key]: value
        }
      }
    }))
    setHasChanges(true)
  }

  const saveSettings = () => {
    // In real app, this would save to backend
    console.log('Saving settings:', settings)
    setHasChanges(false)
    // Show success message
  }

  const resetSettings = () => {
    setSettings(defaultSettings)
    setHasChanges(false)
  }

  const tabs = [
    { id: 'general', name: 'General', icon: CogIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'honeypots', name: 'Honeypots', icon: ServerIcon },
    { id: 'database', name: 'Database', icon: CircleStackIcon }
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Configure system preferences and security settings
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {hasChanges && (
            <Badge variant="warning" className="px-3 py-1">
              Unsaved Changes
            </Badge>
          )}
          <Button variant="outline" onClick={resetSettings}>
            Reset
          </Button>
          <Button variant="honey" onClick={saveSettings} disabled={!hasChanges}>
            Save Changes
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar Navigation */}
        <div className="lg:col-span-1">
          <Card>
            <CardContent className="p-4">
              <nav className="space-y-2">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                    }`}
                  >
                    <tab.icon className="w-4 h-4 mr-3" />
                    {tab.name}
                  </button>
                ))}
              </nav>
            </CardContent>
          </Card>
        </div>

        {/* Settings Content */}
        <div className="lg:col-span-3">
          {/* General Settings */}
          {activeTab === 'general' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CogIcon className="w-5 h-5 mr-2" />
                  General Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground mb-2 block">
                      System Name
                    </label>
                    <Input
                      value={settings.general.systemName}
                      onChange={(e) => updateSetting('general', 'systemName', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground mb-2 block">
                      Timezone
                    </label>
                    <select
                      className="w-full h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
                      value={settings.general.timezone}
                      onChange={(e) => updateSetting('general', 'timezone', e.target.value)}
                    >
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                      <option value="Europe/London">London</option>
                      <option value="Asia/Tokyo">Tokyo</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 border border-border rounded-lg">
                  <div>
                    <h4 className="font-medium text-foreground">Auto Backup</h4>
                    <p className="text-sm text-muted-foreground">Automatically backup system data</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.general.autoBackup}
                    onChange={(e) => updateSetting('general', 'autoBackup', e.target.checked)}
                    className="rounded"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-2 block">
                    Backup Retention (days)
                  </label>
                  <Input
                    type="number"
                    value={settings.general.backupRetention}
                    onChange={(e) => updateSetting('general', 'backupRetention', parseInt(e.target.value))}
                  />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Security Settings */}
          {activeTab === 'security' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <ShieldCheckIcon className="w-5 h-5 mr-2" />
                  Security Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground mb-2 block">
                      Session Timeout (minutes)
                    </label>
                    <Input
                      type="number"
                      value={settings.security.sessionTimeout}
                      onChange={(e) => updateSetting('security', 'sessionTimeout', parseInt(e.target.value))}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground mb-2 block">
                      Max Login Attempts
                    </label>
                    <Input
                      type="number"
                      value={settings.security.maxLoginAttempts}
                      onChange={(e) => updateSetting('security', 'maxLoginAttempts', parseInt(e.target.value))}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 border border-border rounded-lg">
                  <div>
                    <h4 className="font-medium text-foreground">Require Multi-Factor Authentication</h4>
                    <p className="text-sm text-muted-foreground">Require MFA for all user accounts</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.security.requireMFA}
                    onChange={(e) => updateSetting('security', 'requireMFA', e.target.checked)}
                    className="rounded"
                  />
                </div>

                <div className="border border-border rounded-lg p-4">
                  <h4 className="font-medium text-foreground mb-4">Password Policy</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-2 block">
                        Minimum Length
                      </label>
                      <Input
                        type="number"
                        value={settings.security.passwordPolicy.minLength}
                        onChange={(e) => updateNestedSetting('security', 'passwordPolicy', 'minLength', parseInt(e.target.value))}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Require Special Characters</span>
                        <input
                          type="checkbox"
                          checked={settings.security.passwordPolicy.requireSpecialChars}
                          onChange={(e) => updateNestedSetting('security', 'passwordPolicy', 'requireSpecialChars', e.target.checked)}
                          className="rounded"
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Require Numbers</span>
                        <input
                          type="checkbox"
                          checked={settings.security.passwordPolicy.requireNumbers}
                          onChange={(e) => updateNestedSetting('security', 'passwordPolicy', 'requireNumbers', e.target.checked)}
                          className="rounded"
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Require Uppercase</span>
                        <input
                          type="checkbox"
                          checked={settings.security.passwordPolicy.requireUppercase}
                          onChange={(e) => updateNestedSetting('security', 'passwordPolicy', 'requireUppercase', e.target.checked)}
                          className="rounded"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Notifications Settings */}
          {activeTab === 'notifications' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BellIcon className="w-5 h-5 mr-2" />
                  Notification Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-border rounded-lg">
                    <div>
                      <h4 className="font-medium text-foreground">Email Alerts</h4>
                      <p className="text-sm text-muted-foreground">Send alerts via email</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.notifications.emailAlerts}
                      onChange={(e) => updateSetting('notifications', 'emailAlerts', e.target.checked)}
                      className="rounded"
                    />
                  </div>

                  <div className="flex items-center justify-between p-4 border border-border rounded-lg">
                    <div>
                      <h4 className="font-medium text-foreground">Slack Integration</h4>
                      <p className="text-sm text-muted-foreground">Send alerts to Slack channel</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.notifications.slackIntegration}
                      onChange={(e) => updateSetting('notifications', 'slackIntegration', e.target.checked)}
                      className="rounded"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-2 block">
                    Webhook URL
                  </label>
                  <Input
                    placeholder="https://hooks.slack.com/services/..."
                    value={settings.notifications.webhookUrl}
                    onChange={(e) => updateSetting('notifications', 'webhookUrl', e.target.value)}
                  />
                </div>

                <div className="border border-border rounded-lg p-4">
                  <h4 className="font-medium text-foreground mb-4">Alert Thresholds</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-2 block">
                        Critical Alerts
                      </label>
                      <Input
                        type="number"
                        value={settings.notifications.alertThresholds.criticalAlerts}
                        onChange={(e) => updateNestedSetting('notifications', 'alertThresholds', 'criticalAlerts', parseInt(e.target.value))}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-2 block">
                        High Volume Attacks
                      </label>
                      <Input
                        type="number"
                        value={settings.notifications.alertThresholds.highVolumeAttacks}
                        onChange={(e) => updateNestedSetting('notifications', 'alertThresholds', 'highVolumeAttacks', parseInt(e.target.value))}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-2 block">
                        System Errors
                      </label>
                      <Input
                        type="number"
                        value={settings.notifications.alertThresholds.systemErrors}
                        onChange={(e) => updateNestedSetting('notifications', 'alertThresholds', 'systemErrors', parseInt(e.target.value))}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Honeypots Settings */}
          {activeTab === 'honeypots' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <ServerIcon className="w-5 h-5 mr-2" />
                  Honeypot Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="border border-border rounded-lg p-4">
                  <h4 className="font-medium text-foreground mb-4">Default Ports</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-2 block">SSH</label>
                      <Input
                        type="number"
                        value={settings.honeypots.defaultPorts.ssh}
                        onChange={(e) => updateNestedSetting('honeypots', 'defaultPorts', 'ssh', parseInt(e.target.value))}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-2 block">HTTP</label>
                      <Input
                        type="number"
                        value={settings.honeypots.defaultPorts.http}
                        onChange={(e) => updateNestedSetting('honeypots', 'defaultPorts', 'http', parseInt(e.target.value))}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-2 block">FTP</label>
                      <Input
                        type="number"
                        value={settings.honeypots.defaultPorts.ftp}
                        onChange={(e) => updateNestedSetting('honeypots', 'defaultPorts', 'ftp', parseInt(e.target.value))}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted-foreground mb-2 block">SMTP</label>
                      <Input
                        type="number"
                        value={settings.honeypots.defaultPorts.smtp}
                        onChange={(e) => updateNestedSetting('honeypots', 'defaultPorts', 'smtp', parseInt(e.target.value))}
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-2 block">
                    Log Retention (days)
                  </label>
                  <Input
                    type="number"
                    value={settings.honeypots.logRetention}
                    onChange={(e) => updateSetting('honeypots', 'logRetention', parseInt(e.target.value))}
                  />
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-border rounded-lg">
                    <div>
                      <h4 className="font-medium text-foreground">Auto Response</h4>
                      <p className="text-sm text-muted-foreground">Automatically respond to attacks</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.honeypots.autoResponse}
                      onChange={(e) => updateSetting('honeypots', 'autoResponse', e.target.checked)}
                      className="rounded"
                    />
                  </div>

                  <div className="flex items-center justify-between p-4 border border-border rounded-lg">
                    <div>
                      <h4 className="font-medium text-foreground">Geo-blocking</h4>
                      <p className="text-sm text-muted-foreground">Block traffic from specific countries</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.honeypots.geoBlocking}
                      onChange={(e) => updateSetting('honeypots', 'geoBlocking', e.target.checked)}
                      className="rounded"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Database Settings */}
          {activeTab === 'database' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CircleStackIcon className="w-5 h-5 mr-2" />
                  Database Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground mb-2 block">
                      Host
                    </label>
                    <Input
                      value={settings.database.host}
                      onChange={(e) => updateSetting('database', 'host', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground mb-2 block">
                      Port
                    </label>
                    <Input
                      type="number"
                      value={settings.database.port}
                      onChange={(e) => updateSetting('database', 'port', parseInt(e.target.value))}
                    />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-2 block">
                    Database Name
                  </label>
                  <Input
                    value={settings.database.name}
                    onChange={(e) => updateSetting('database', 'name', e.target.value)}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium text-muted-foreground mb-2 block">
                    Backup Schedule
                  </label>
                  <select
                    className="w-full h-10 px-3 py-2 border border-input bg-background rounded-md text-sm"
                    value={settings.database.backupSchedule}
                    onChange={(e) => updateSetting('database', 'backupSchedule', e.target.value)}
                  >
                    <option value="hourly">Hourly</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>

                <div className="flex items-center justify-between p-4 border border-border rounded-lg">
                  <div>
                    <h4 className="font-medium text-foreground">Compression Enabled</h4>
                    <p className="text-sm text-muted-foreground">Compress database backups</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.database.compressionEnabled}
                    onChange={(e) => updateSetting('database', 'compressionEnabled', e.target.checked)}
                    className="rounded"
                  />
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
