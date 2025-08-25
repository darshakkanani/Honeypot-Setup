const { Pool } = require('pg');

// Database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

exports.handler = async (event, context) => {
  // Enable CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
  };

  // Handle preflight requests
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  try {
    const client = await pool.connect();
    
    switch (event.httpMethod) {
      case 'GET':
        return await handleGet(client, event, headers);
      default:
        return {
          statusCode: 405,
          headers,
          body: JSON.stringify({ error: 'Method not allowed' })
        };
    }
  } catch (error) {
    console.error('Database error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'Internal server error' })
    };
  }
};

async function handleGet(client, event, headers) {
  try {
    // Get dashboard statistics
    const statsQuery = `
      SELECT 
        COUNT(*) as total_attacks,
        COUNT(DISTINCT source_ip) as unique_attackers,
        COUNT(*) FILTER (WHERE timestamp >= CURRENT_DATE) as attacks_today,
        COUNT(*) FILTER (WHERE severity = 'CRITICAL') as critical_attacks
      FROM securehoney.attacks
    `;
    
    const statsResult = await client.query(statsQuery);
    const stats = statsResult.rows[0];

    // Get recent attacks
    const recentQuery = `
      SELECT 
        source_ip,
        attack_type,
        severity,
        timestamp,
        target_port
      FROM securehoney.attacks 
      ORDER BY timestamp DESC 
      LIMIT 10
    `;
    
    const recentResult = await client.query(recentQuery);
    const recentAttacks = recentResult.rows;

    // Get geographic distribution
    const geoQuery = `
      SELECT 
        g.country,
        g.country_code,
        COUNT(a.*) as attack_count
      FROM securehoney.attacks a
      JOIN securehoney.geolocation_data g ON a.source_ip = g.ip_address
      GROUP BY g.country, g.country_code
      ORDER BY attack_count DESC
      LIMIT 10
    `;
    
    const geoResult = await client.query(geoQuery);
    const geoData = geoResult.rows;

    client.release();

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        statistics: {
          total_attacks: parseInt(stats.total_attacks),
          unique_attackers: parseInt(stats.unique_attackers),
          attacks_today: parseInt(stats.attacks_today),
          critical_attacks: parseInt(stats.critical_attacks),
          system_uptime: '99.9%',
          threat_level: calculateThreatLevel(parseInt(stats.attacks_today))
        },
        recent_attacks: recentAttacks,
        geographic_data: geoData,
        timestamp: new Date().toISOString()
      })
    };
  } catch (error) {
    console.error('Query error:', error);
    throw error;
  }
}

function calculateThreatLevel(attacksToday) {
  if (attacksToday >= 100) return 'CRITICAL';
  if (attacksToday >= 50) return 'HIGH';
  if (attacksToday >= 20) return 'MEDIUM';
  return 'LOW';
}
