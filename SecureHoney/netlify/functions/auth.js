const { Pool } = require('pg');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

exports.handler = async (event, context) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  const path = event.path.replace('/.netlify/functions/auth', '');

  try {
    const client = await pool.connect();
    
    switch (event.httpMethod) {
      case 'POST':
        if (path === '/login') {
          return await handleLogin(client, event, headers);
        } else if (path === '/logout') {
          return await handleLogout(client, event, headers);
        }
        break;
      case 'GET':
        if (path === '/verify') {
          return await handleVerify(client, event, headers);
        }
        break;
    }

    client.release();
    return {
      statusCode: 404,
      headers,
      body: JSON.stringify({ error: 'Endpoint not found' })
    };

  } catch (error) {
    console.error('Auth error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'Internal server error' })
    };
  }
};

async function handleLogin(client, event, headers) {
  try {
    const { username, password } = JSON.parse(event.body);

    if (!username || !password) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Username and password required' })
      };
    }

    // Get user from database
    const userQuery = `
      SELECT id, username, email, password_hash, role, is_active, 
             failed_login_attempts, account_locked_until
      FROM securehoney.admin_users 
      WHERE username = $1 AND is_active = true
    `;
    
    const userResult = await client.query(userQuery, [username]);
    
    if (userResult.rows.length === 0) {
      return {
        statusCode: 401,
        headers,
        body: JSON.stringify({ error: 'Invalid credentials' })
      };
    }

    const user = userResult.rows[0];

    // Check if account is locked
    if (user.account_locked_until && new Date() < new Date(user.account_locked_until)) {
      return {
        statusCode: 423,
        headers,
        body: JSON.stringify({ error: 'Account is locked' })
      };
    }

    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.password_hash);
    
    if (!isValidPassword) {
      // Increment failed attempts
      await client.query(
        'UPDATE securehoney.admin_users SET failed_login_attempts = failed_login_attempts + 1 WHERE id = $1',
        [user.id]
      );
      
      return {
        statusCode: 401,
        headers,
        body: JSON.stringify({ error: 'Invalid credentials' })
      };
    }

    // Reset failed attempts and update last login
    await client.query(
      'UPDATE securehoney.admin_users SET failed_login_attempts = 0, last_login = NOW() WHERE id = $1',
      [user.id]
    );

    // Generate JWT token
    const token = jwt.sign(
      { 
        userId: user.id, 
        username: user.username, 
        role: user.role 
      },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    client.release();

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        token,
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          role: user.role
        }
      })
    };

  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

async function handleVerify(client, event, headers) {
  try {
    const authHeader = event.headers.authorization || event.headers.Authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return {
        statusCode: 401,
        headers,
        body: JSON.stringify({ error: 'No token provided' })
      };
    }

    const token = authHeader.substring(7);
    
    try {
      const decoded = jwt.verify(token, JWT_SECRET);
      
      // Get fresh user data
      const userQuery = `
        SELECT id, username, email, role, is_active
        FROM securehoney.admin_users 
        WHERE id = $1 AND is_active = true
      `;
      
      const userResult = await client.query(userQuery, [decoded.userId]);
      
      if (userResult.rows.length === 0) {
        return {
          statusCode: 401,
          headers,
          body: JSON.stringify({ error: 'User not found' })
        };
      }

      const user = userResult.rows[0];
      client.release();

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          user: {
            id: user.id,
            username: user.username,
            email: user.email,
            role: user.role
          }
        })
      };

    } catch (jwtError) {
      return {
        statusCode: 401,
        headers,
        body: JSON.stringify({ error: 'Invalid token' })
      };
    }

  } catch (error) {
    console.error('Verify error:', error);
    throw error;
  }
}

async function handleLogout(client, event, headers) {
  // For JWT, logout is handled client-side by removing the token
  client.release();
  
  return {
    statusCode: 200,
    headers,
    body: JSON.stringify({ message: 'Logged out successfully' })
  };
}
