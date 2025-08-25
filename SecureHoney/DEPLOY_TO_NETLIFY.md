# Deploy SecureHoney to Netlify

Complete guide to deploy the SecureHoney admin panel to Netlify.

## 🚀 Quick Deployment

### Step 1: Prepare for Deployment

```bash
cd SecureHoney

# Install Netlify CLI
npm install -g netlify-cli

# Install frontend dependencies
cd admin-panel/frontend
npm install

# Install function dependencies
cd ../../netlify/functions
npm install
```

### Step 2: Set up External Database

Since Netlify can't host PostgreSQL, use one of these services:

**Option A: Supabase (Recommended)**
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Get connection string from Settings > Database
4. Import your schema using Supabase SQL editor

**Option B: Neon**
1. Go to [neon.tech](https://neon.tech)
2. Create database
3. Get connection string

**Option C: Railway**
1. Go to [railway.app](https://railway.app)
2. Deploy PostgreSQL
3. Get connection string

### Step 3: Deploy to Netlify

```bash
cd SecureHoney

# Login to Netlify
netlify login

# Deploy
netlify deploy

# For production deployment
netlify deploy --prod
```

### Step 4: Configure Environment Variables

In Netlify dashboard, go to Site Settings > Environment Variables and add:

```
DATABASE_URL=postgresql://user:pass@host:port/dbname
JWT_SECRET=your-super-secret-jwt-key
NODE_ENV=production
```

## 🔧 Manual Deployment

### Option 1: Drag & Drop

1. Build the frontend:
```bash
cd admin-panel/frontend
npm run build
```

2. Drag the `build` folder to Netlify dashboard

### Option 2: Git Integration

1. Push to GitHub:
```bash
git add .
git commit -m "Prepare for Netlify deployment"
git push origin main
```

2. Connect repository in Netlify dashboard

## 📊 What Gets Deployed

**✅ Included:**
- Admin Panel Frontend (React)
- Authentication system
- Dashboard with statistics
- User management
- Configuration interface
- API via serverless functions

**❌ Not Included:**
- Actual honeypot services (SSH, FTP, HTTP)
- Real-time network monitoring
- Database (needs external service)

## 🔗 Access Your Deployment

After deployment:
- **Admin Panel**: `https://your-site-name.netlify.app`
- **API**: `https://your-site-name.netlify.app/.netlify/functions/`

Default login: `admin` / `admin123`

## 🛠 Troubleshooting

### Build Fails
```bash
# Check build logs in Netlify dashboard
# Common issues:
# 1. Missing dependencies
# 2. Environment variables not set
# 3. Build command incorrect
```

### Functions Not Working
```bash
# Check function logs in Netlify dashboard
# Common issues:
# 1. DATABASE_URL not set
# 2. Missing dependencies in netlify/functions/package.json
# 3. CORS issues
```

### Database Connection Issues
```bash
# Test connection string locally:
node -e "
const { Pool } = require('pg');
const pool = new Pool({ connectionString: 'YOUR_DATABASE_URL' });
pool.query('SELECT NOW()', (err, res) => {
  console.log(err ? err : res.rows[0]);
  pool.end();
});
"
```

## 🔒 Security Setup

1. **Change Default Password**
   - Login and update admin password immediately

2. **Configure CORS**
   - Update allowed origins in functions

3. **Set Strong JWT Secret**
   - Use a secure random string for JWT_SECRET

4. **Enable HTTPS**
   - Netlify provides HTTPS by default

## 📈 Monitoring

- **Netlify Analytics**: Built-in traffic analytics
- **Function Logs**: Monitor API usage
- **Database Metrics**: Use your database provider's monitoring

## 🔄 Updates

To update your deployment:

```bash
# Make changes
git add .
git commit -m "Update description"
git push origin main

# Or redeploy manually
netlify deploy --prod
```

## 💡 Demo Mode

If you want to showcase without a database, the frontend includes mock data fallback. Set environment variable:

```
REACT_APP_DEMO_MODE=true
```

This will show simulated honeypot data for demonstration purposes.

## 🎯 Next Steps

1. Deploy admin panel to Netlify
2. Set up external database
3. Configure environment variables
4. Test authentication and dashboard
5. For actual honeypot services, deploy to VPS/cloud server
6. Connect honeypot data to your Netlify dashboard via API

The Netlify deployment gives you a professional admin interface for monitoring and managing your honeypot system!
