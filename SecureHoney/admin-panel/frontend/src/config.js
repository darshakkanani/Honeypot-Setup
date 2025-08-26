// Configuration for different environments
const config = {
  development: {
    API_BASE_URL: 'http://localhost:5001/api',
    WS_URL: 'ws://localhost:5001/ws',
    APP_NAME: 'SecureHoney Admin Panel',
    VERSION: '1.0.0'
  },
  production: {
    API_BASE_URL: 'http://localhost:5001/api',
    WS_URL: 'ws://localhost:5001/ws',
    APP_NAME: 'SecureHoney Admin Panel',
    VERSION: '1.0.0'
  }
};

const environment = process.env.REACT_APP_ENV || 'development';
const currentConfig = config[environment] || config.development;

export default currentConfig;
