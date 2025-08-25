import config from '../config';

class ApiService {
  constructor() {
    this.baseURL = config.API_BASE_URL;
    this.token = localStorage.getItem('securehoney_token');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('securehoney_token', token);
    } else {
      localStorage.removeItem('securehoney_token');
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication
  async login(username, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    
    if (response.token) {
      this.setToken(response.token);
    }
    
    return response;
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.setToken(null);
    }
  }

  async verifyToken() {
    return await this.request('/auth/verify');
  }

  // Dashboard data
  async getDashboardData() {
    return await this.request('/dashboard');
  }

  // For demo purposes - generate mock data when backend is not available
  getMockDashboardData() {
    return {
      statistics: {
        total_attacks: 1247,
        unique_attackers: 89,
        attacks_today: 23,
        critical_attacks: 5,
        system_uptime: '99.9%',
        threat_level: 'MEDIUM'
      },
      recent_attacks: [
        {
          source_ip: '192.168.1.100',
          attack_type: 'BRUTE_FORCE',
          severity: 'HIGH',
          timestamp: new Date().toISOString(),
          target_port: 22
        },
        {
          source_ip: '10.0.0.50',
          attack_type: 'PORT_SCAN',
          severity: 'MEDIUM',
          timestamp: new Date(Date.now() - 300000).toISOString(),
          target_port: 80
        }
      ],
      geographic_data: [
        { country: 'United States', country_code: 'US', attack_count: 45 },
        { country: 'China', country_code: 'CN', attack_count: 32 },
        { country: 'Russia', country_code: 'RU', attack_count: 28 }
      ],
      timestamp: new Date().toISOString()
    };
  }

  // Fallback method that tries real API first, then mock data
  async getDashboardDataWithFallback() {
    try {
      return await this.getDashboardData();
    } catch (error) {
      console.warn('API unavailable, using mock data:', error.message);
      return this.getMockDashboardData();
    }
  }
}

export default new ApiService();
