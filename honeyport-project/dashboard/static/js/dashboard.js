// HoneyPort Dashboard JavaScript
class HoneyPortDashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = 30000; // 30 seconds
        this.init();
    }

    init() {
        this.loadInitialData();
        this.setupEventListeners();
        this.startAutoRefresh();
        this.initializeCharts();
    }

    async loadInitialData() {
        await Promise.all([
            this.updateStats(),
            this.updateEvents(),
            this.updateAIInsights(),
            this.updateBlockchainStatus(),
            this.updateAlerts()
        ]);
    }

    setupEventListeners() {
        // Auto-refresh toggle
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
            }
        });
    }

    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            this.loadInitialData();
        }, this.refreshInterval);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
    }

    async updateStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();

            document.getElementById('total-attacks').textContent = data.total_attacks || 0;
            document.getElementById('unique-attackers').textContent = data.unique_attackers || 0;
            document.getElementById('blocked-ips').textContent = data.blocked_ips || 0;
            document.getElementById('ai-adaptations').textContent = data.ai_adaptations || 0;
            document.getElementById('system-uptime').textContent = data.uptime || '0h 0m';
            document.getElementById('system-behavior').textContent = data.current_behavior || 'Realistic';
            document.getElementById('last-attack').textContent = data.last_attack || 'Never';

            // Update attack types chart
            if (data.attack_types) {
                this.updateAttackTypesChart(data.attack_types);
            }
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }

    async updateEvents() {
        try {
            const response = await fetch('/api/events?limit=20');
            const data = await response.json();
            
            const eventsContainer = document.getElementById('events-feed');
            
            if (data.events && data.events.length > 0) {
                eventsContainer.innerHTML = data.events.map(event => `
                    <div class="event-item severity-${event.severity}">
                        <div class="event-icon severity-${event.severity}">
                            ${this.getEventIcon(event.attack_type)}
                        </div>
                        <div class="event-details">
                            <div class="event-title">
                                ${this.formatAttackType(event.attack_type)} from ${event.source_ip}
                            </div>
                            <div class="event-meta">
                                ${event.method} ${event.url} • ${event.user_agent}
                            </div>
                            <div class="event-time">
                                ${this.formatTimestamp(event.timestamp)}
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                eventsContainer.innerHTML = '<div class="loading">No recent events</div>';
            }
        } catch (error) {
            console.error('Error updating events:', error);
            document.getElementById('events-feed').innerHTML = '<div class="loading">Error loading events</div>';
        }
    }

    async updateAIInsights() {
        try {
            const response = await fetch('/api/ai/insights');
            const data = await response.json();

            document.getElementById('current-behavior').textContent = data.current_behavior || 'Realistic';
            
            // Update behavior chart
            if (data.behavior_distribution) {
                this.updateBehaviorChart(data.behavior_distribution);
            }
        } catch (error) {
            console.error('Error updating AI insights:', error);
        }
    }

    async updateBlockchainStatus() {
        try {
            // Get blockchain verification status
            const verifyResponse = await fetch('/api/blockchain/verify');
            const verifyData = await verifyResponse.json();
            
            // Get comprehensive blockchain status
            const statusResponse = await fetch('/api/blockchain/status');
            const statusData = await statusResponse.json();
            
            // Update verification status
            const statusElement = document.getElementById('blockchain-status');
            const totalBlocksElement = document.getElementById('total-blocks');
            const chainHashElement = document.getElementById('chain-hash');
            const smartContractElement = document.getElementById('smart-contract-status');
            const web3StatusElement = document.getElementById('web3-status');
            const contractAddressElement = document.getElementById('contract-address');
            const accountBalanceElement = document.getElementById('account-balance');
            
            if (verifyData.valid) {
                statusElement.innerHTML = '<i class="fas fa-check-circle"></i> Verified';
                statusElement.className = 'verification-status verified';
            } else {
                statusElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Invalid';
                statusElement.className = 'verification-status invalid';
            }
            
            if (totalBlocksElement) {
                totalBlocksElement.textContent = verifyData.total_blocks || 0;
            }
            
            if (chainHashElement) {
                const hash = verifyData.chain_hash || 'N/A';
                chainHashElement.textContent = hash.length > 16 ? hash.substring(0, 16) + '...' : hash;
                chainHashElement.title = hash;
            }
            
            // Update smart contract status
            if (smartContractElement) {
                if (statusData.smart_contract_connected) {
                    smartContractElement.innerHTML = '<i class="fas fa-check-circle text-success"></i> Connected';
                } else {
                    smartContractElement.innerHTML = '<i class="fas fa-times-circle text-warning"></i> Disconnected';
                }
            }
            
            // Update Web3 status
            if (web3StatusElement) {
                if (statusData.web3_connected) {
                    web3StatusElement.innerHTML = '<i class="fas fa-check-circle text-success"></i> Connected';
                } else {
                    web3StatusElement.innerHTML = '<i class="fas fa-times-circle text-warning"></i> Disconnected';
                }
            }
            
            // Update contract address
            if (contractAddressElement) {
                const address = statusData.contract_address || 'N/A';
                if (address !== 'N/A') {
                    contractAddressElement.textContent = address.length > 16 ? address.substring(0, 16) + '...' : address;
                    contractAddressElement.title = address;
                } else {
                    contractAddressElement.textContent = 'N/A';
                }
            }
            
            // Update account balance
            if (accountBalanceElement) {
                const balance = statusData.account_balance || 0;
                accountBalanceElement.textContent = `${balance.toFixed(4)} ETH`;
            }
            
        } catch (error) {
            console.error('Error updating blockchain status:', error);
            const statusElement = document.getElementById('blockchain-status');
            if (statusElement) {
                statusElement.innerHTML = '<i class="fas fa-times-circle"></i> Error';
                statusElement.className = 'verification-status error';
            }
        }
    }

    async updateAlerts() {
        try {
            const response = await fetch('/api/alerts');
            const data = await response.json();

            const alertsContainer = document.getElementById('alerts-list');
            const alertCount = document.getElementById('alert-count');

            if (data.alerts && data.alerts.length > 0) {
                alertCount.textContent = data.alerts.length;
                alertsContainer.innerHTML = data.alerts.map(alert => `
                    <div class="alert-item">
                        <div class="alert-title">${alert.type.replace(/_/g, ' ').toUpperCase()}</div>
                        <div class="alert-message">${alert.message}</div>
                        <div class="event-time">${this.formatTimestamp(alert.timestamp)}</div>
                    </div>
                `).join('');
            } else {
                alertCount.textContent = '0';
                alertsContainer.innerHTML = '<div class="no-alerts">No active alerts</div>';
            }
        } catch (error) {
            console.error('Error updating alerts:', error);
        }
    }

    initializeCharts() {
        // Attack Types Chart
        const attackCtx = document.getElementById('attackTypesChart');
        if (attackCtx) {
            this.charts.attackTypes = new Chart(attackCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#ef4444',
                            '#f59e0b',
                            '#10b981',
                            '#3b82f6',
                            '#8b5cf6',
                            '#f97316'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#e4e4e7',
                                padding: 20
                            }
                        }
                    }
                }
            });
        }

        // Behavior Chart
        const behaviorCtx = document.getElementById('behaviorChart');
        if (behaviorCtx) {
            this.charts.behavior = new Chart(behaviorCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Adaptations',
                        data: [],
                        backgroundColor: 'rgba(0, 212, 255, 0.6)',
                        borderColor: '#00d4ff',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: '#a1a1aa'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        },
                        x: {
                            ticks: {
                                color: '#a1a1aa'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        }
                    }
                }
            });
        }
    }

    updateAttackTypesChart(attackTypes) {
        if (!this.charts.attackTypes) return;

        const labels = Object.keys(attackTypes);
        const data = Object.values(attackTypes);

        this.charts.attackTypes.data.labels = labels;
        this.charts.attackTypes.data.datasets[0].data = data;
        this.charts.attackTypes.update();
    }

    updateBehaviorChart(behaviorDistribution) {
        if (!this.charts.behavior) return;

        const labels = Object.keys(behaviorDistribution);
        const data = Object.values(behaviorDistribution);

        this.charts.behavior.data.labels = labels;
        this.charts.behavior.data.datasets[0].data = data;
        this.charts.behavior.update();
    }

    getEventIcon(attackType) {
        const icons = {
            'sql_injection': '<i class="fas fa-database"></i>',
            'xss': '<i class="fas fa-code"></i>',
            'brute_force': '<i class="fas fa-hammer"></i>',
            'directory_traversal': '<i class="fas fa-folder-open"></i>',
            'command_injection': '<i class="fas fa-terminal"></i>',
            'reconnaissance': '<i class="fas fa-search"></i>',
            'default': '<i class="fas fa-bug"></i>'
        };
        return icons[attackType] || icons.default;
    }

    formatAttackType(attackType) {
        return attackType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return 'Unknown';
        try {
            const date = new Date(timestamp);
            return date.toLocaleString();
        } catch {
            return 'Invalid date';
        }
    }
}

// Global functions for button actions
async function refreshEvents() {
    const button = event.target.closest('.refresh-btn');
    const icon = button.querySelector('i');
    
    icon.classList.add('fa-spin');
    await dashboard.updateEvents();
    
    setTimeout(() => {
        icon.classList.remove('fa-spin');
    }, 1000);
}

async function verifyBlockchain() {
    const button = event.target;
    const originalText = button.innerHTML;
    
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';
    button.disabled = true;
    
    try {
        await dashboard.updateBlockchainStatus();
        button.innerHTML = '<i class="fas fa-check"></i> Verified';
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 2000);
    } catch (error) {
        button.innerHTML = '<i class="fas fa-times"></i> Error';
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 2000);
    }
}

async function retrainAI() {
    const button = event.target;
    const originalText = button.innerHTML;
    
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Training...';
    button.disabled = true;
    
    try {
        const response = await fetch('/api/ai/retrain', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            button.innerHTML = '<i class="fas fa-check"></i> Trained';
            await dashboard.updateAIInsights();
        } else {
            button.innerHTML = '<i class="fas fa-times"></i> Failed';
        }
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 3000);
    } catch (error) {
        button.innerHTML = '<i class="fas fa-times"></i> Error';
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 3000);
    }
}

async function exportLogs() {
    const button = event.target;
    const originalText = button.innerHTML;
    
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
    button.disabled = true;
    
    try {
        const response = await fetch('/api/export/logs?format=json');
        const data = await response.json();
        
        // Create download link
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `honeyport-logs-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        button.innerHTML = '<i class="fas fa-check"></i> Downloaded';
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 2000);
    } catch (error) {
        button.innerHTML = '<i class="fas fa-times"></i> Error';
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 2000);
    }
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new HoneyPortDashboard();
});
