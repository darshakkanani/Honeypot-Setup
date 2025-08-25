# SecureHoney Netlify Deployment Guide

## Deployment Strategy

Since SecureHoney is a full-stack honeypot system, we'll use a hybrid approach:

1. **Frontend (Admin Panel)** → Netlify Static Hosting
2. **Backend API** → Netlify Functions (Serverless)
3. **Database** → External PostgreSQL (Supabase/Neon/Railway)
4. **Honeypot Engine** → Separate VPS/Cloud Server

## ⚠️ Important Limitations

**What CAN be deployed on Netlify:**
- ✅ Admin Panel Frontend (React)
- ✅ Basic API endpoints via Netlify Functions
- ✅ Authentication and configuration management
- ✅ Dashboard and reporting

**What CANNOT be deployed on Netlify:**
- ❌ Actual honeypot services (SSH, FTP, etc.)
- ❌ Real-time network listeners
- ❌ Long-running processes
- ❌ Direct database connections (need serverless)

## Recommended Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Netlify       │    │  External DB     │    │  VPS/Cloud      │
│  (Admin Panel)  │◄──►│  (Supabase)      │◄──►│  (Honeypots)    │
│  - Frontend     │    │  - PostgreSQL    │    │  - SSH:22       │
│  - API Functions│    │  - Real-time     │    │  - HTTP:80      │
│  - Auth         │    │  - Backups       │    │  - FTP:21       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Option 1: Admin Panel Only (Recommended for Netlify)

Deploy just the admin dashboard to Netlify for monitoring and management.

### Setup Steps:

1. **Prepare Frontend for Netlify**
2. **Set up External Database**
3. **Create Netlify Functions**
4. **Deploy to Netlify**
5. **Run Honeypots Separately**

## Option 2: Full Demo Version

Create a demo version with simulated data for showcase purposes.
