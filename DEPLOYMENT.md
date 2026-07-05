# Deployment Guide

This guide provides step-by-step instructions for deploying the AI-Native Music Discovery Companion to production.

## Prerequisites

- GitHub repository with the project code
- Vercel account for frontend deployment
- Render account for backend deployment
- GitHub account with Actions enabled
- API keys for Groq and Last.fm
- Access to AI-Powered Review Discovery Engine

## Deployment Architecture

```
Frontend (Vercel) → Backend (Render) → Review Engine (External)
                      ↓
                   PostgreSQL (Render)
                   Redis (Render)
```

## Step 1: Backend Deployment (Render)

### 1.1 Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up or log in
3. Connect your GitHub account

### 1.2 Create PostgreSQL Database

1. Go to Render Dashboard
2. Click "New" → "PostgreSQL"
3. Configure:
   - Name: `ai-native-music-db`
   - Database: `music_discovery`
   - User: `postgres`
   - Region: Oregon (or nearest to your users)
4. Click "Create Database"
5. Copy the internal connection string

### 1.3 Create Redis Instance

1. Go to Render Dashboard
2. Click "New" → "Redis"
3. Configure:
   - Name: `ai-native-music-redis`
   - Region: Oregon (same as database)
4. Click "Create Redis"
5. Copy the connection details

### 1.4 Deploy Backend Service

1. Go to Render Dashboard
2. Click "New" → "Web Service"
3. Connect GitHub repository
4. Select branch: `main`
5. Configure:
   - Name: `ai-native-music-discovery-backend`
   - Runtime: `Python 3.11`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python run.py`
6. Add Environment Variables:
   ```
   GROQ_API_KEY=<your_groq_api_key>
   LASTFM_API_KEY=<your_lastfm_api_key>
   LASTFM_SHARED_SECRET=<your_lastfm_secret>
   REVIEW_ENGINE_URL=https://ai-powered-review-discovery-engine.onrender.com
   DATABASE_URL=<render_postgresql_connection_string>
   REDIS_HOST=<render_redis_host>
   REDIS_PORT=6379
   REDIS_PASSWORD=<render_redis_password>
   PORT=8005
   HOST=0.0.0.0
   CORS_ORIGINS=https://ai-native-music-discovery-frontend.vercel.app
   ```
7. Click "Create Web Service"
8. Wait for deployment to complete
9. Copy the service URL (e.g., `https://ai-native-music-discovery-backend.onrender.com`)

### 1.5 Verify Backend Deployment

1. Go to the service URL
2. Check health endpoint: `https://ai-native-music-discovery-backend.onrender.com/health`
3. Verify response shows all services as healthy

## Step 2: Frontend Deployment (Vercel)

### 2.1 Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Sign up or log in
3. Connect your GitHub account

### 2.2 Deploy Frontend

1. Go to Vercel Dashboard
2. Click "Add New Project"
3. Select GitHub repository
4. Configure:
   - Framework Preset: Next.js
   - Root Directory: `phase5-frontend-ui`
   - Build Command: `npm run build`
   - Output Directory: `.next`
5. Add Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://ai-native-music-discovery-backend.onrender.com
   NEXT_PUBLIC_APP_NAME=AI-Native Music Discovery Companion
   NEXT_PUBLIC_APP_VERSION=1.0.0
   ```
6. Click "Deploy"
7. Wait for deployment to complete
8. Copy the deployment URL (e.g., `https://ai-native-music-discovery-frontend.vercel.app`)

### 2.3 Verify Frontend Deployment

1. Go to the deployment URL
2. Verify the application loads
3. Test API connectivity by checking network requests

## Step 3: Scheduler Deployment (GitHub Actions)

### 3.1 Configure GitHub Secrets

1. Go to GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Add the following secrets:
   - `GROQ_API_KEY`: Your Groq API key
   - `LASTFM_API_KEY`: Your Last.fm API key
   - `LASTFM_SHARED_SECRET`: Your Last.fm shared secret

### 3.2 Verify Scheduler Workflow

1. Go to Actions tab in GitHub
2. Select "Weekly Music Discovery Scheduler"
3. Click "Run workflow" to test manually
4. Verify workflow completes successfully
5. Check logs for any errors

### 3.3 Monitor Scheduled Runs

1. The scheduler will run every Monday at 10:00 AM IST
2. Go to Actions tab to view execution history
3. Download logs as artifacts for detailed analysis

## Step 4: Update CORS Configuration

### 4.1 Backend CORS

The backend CORS is already configured in `phase4-backend-api/config.yaml`:

```yaml
api:
  cors_origins:
    - "https://ai-native-music-discovery-frontend.vercel.app"
    - "https://ai-native-music-discovery-frontend.vercel.app/*"
    - "http://localhost:3000"
```

### 4.2 Frontend Headers

Security headers are configured in `phase5-frontend-ui/vercel.json`:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

## Step 5: Environment Variables Reference

### Production Environment Variables

**Backend (Render)**:
```bash
GROQ_API_KEY=<your_groq_api_key>
LASTFM_API_KEY=<your_lastfm_api_key>
LASTFM_SHARED_SECRET=<your_lastfm_secret>
REVIEW_ENGINE_URL=https://ai-powered-review-discovery-engine.onrender.com
DATABASE_URL=<render_postgresql_connection_string>
REDIS_HOST=<render_redis_host>
REDIS_PORT=6379
REDIS_PASSWORD=<render_redis_password>
PORT=8005
HOST=0.0.0.0
CORS_ORIGINS=https://ai-native-music-discovery-frontend.vercel.app
```

**Frontend (Vercel)**:
```bash
NEXT_PUBLIC_API_URL=https://ai-native-music-discovery-backend.onrender.com
NEXT_PUBLIC_APP_NAME=AI-Native Music Discovery Companion
NEXT_PUBLIC_APP_VERSION=1.0.0
```

**Scheduler (GitHub Actions)**:
```bash
GROQ_API_KEY=<your_groq_api_key>
USE_MOCKS=false
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=Asia/Kolkata
LOG_DIR=./logs/scheduler
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Step 6: Monitoring and Maintenance

### Backend Monitoring (Render)

1. Go to Render Dashboard
2. Select backend service
3. View metrics: CPU, memory, response time
4. Check logs for errors
5. Set up alert notifications

### Frontend Monitoring (Vercel)

1. Go to Vercel Dashboard
2. Select frontend project
3. View analytics: page views, bandwidth
4. Check deployment logs
5. Monitor performance metrics

### Scheduler Monitoring (GitHub Actions)

1. Go to Actions tab
2. View workflow execution history
3. Download log artifacts
4. Check workflow summaries
5. Set up notifications for failures

## Step 7: Troubleshooting

### Common Issues

**Backend Deployment Fails**:
- Check Python version compatibility (3.11)
- Verify all dependencies in requirements.txt
- Check environment variables are set correctly
- Review build logs for specific errors

**Frontend Build Fails**:
- Check Node.js version compatibility
- Verify npm dependencies are up to date
- Check environment variables are set correctly
- Review build logs for specific errors

**CORS Errors**:
- Verify CORS origins match deployment URLs
- Check backend CORS configuration
- Ensure HTTPS is used in production
- Clear browser cache

**API Connection Errors**:
- Verify backend service is running
- Check API URL in frontend environment variables
- Review network requests in browser dev tools
- Check backend logs for connection errors

**Scheduler Fails**:
- Verify GitHub secrets are set correctly
- Check workflow logs for specific errors
- Ensure Phase 6 dependencies are installed
- Verify scheduler configuration

### Rollback Procedures

**Frontend Rollback (Vercel)**:
1. Go to Vercel Dashboard
2. Select frontend project
3. Go to Deployments tab
4. Click "..." on previous deployment
5. Select "Promote to Production"

**Backend Rollback (Render)**:
1. Go to Render Dashboard
2. Select backend service
3. Go to Events tab
4. Find previous successful deployment
5. Redeploy previous commit

**Scheduler Rollback (GitHub Actions)**:
1. Go to Actions tab
2. Select failed workflow run
3. Click "Re-run jobs"
4. Or revert to previous commit and push

## Step 8: Security Best Practices

1. **Never commit API keys** to repository
2. **Use platform-specific secrets** for sensitive data
3. **Rotate API keys** regularly
4. **Enable HTTPS only** in production
5. **Monitor for unusual activity**
6. **Keep dependencies updated**
7. **Review logs regularly**
8. **Implement rate limiting**
9. **Use strong passwords** for databases
10. **Enable two-factor authentication** on all platforms

## Step 9: Cost Optimization

**Free Tier Limits**:
- Vercel: 100GB bandwidth/month
- Render: 750 hours/month
- GitHub Actions: 2000 minutes/month

**Cost Reduction Strategies**:
- Use caching to reduce API calls
- Optimize database queries
- Implement CDN caching
- Monitor resource usage
- Scale based on demand

## Step 10: Backup Strategy

**Database Backups**:
- Render provides automatic daily backups
- Export database regularly
- Store backups in secure location
- Test restore procedures

**Application Backups**:
- Git provides version control
- Export environment variables
- Document configuration changes
- Keep deployment snapshots

## Support and Resources

- **Vercel Documentation**: https://vercel.com/docs
- **Render Documentation**: https://render.com/docs
- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **Project Architecture**: See ARCHITECTURE.md
- **Issue Reporting**: Create GitHub issue

## Deployment Checklist

- [ ] Backend deployed to Render
- [ ] PostgreSQL database created
- [ ] Redis instance created
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] CORS configured correctly
- [ ] GitHub Actions secrets set
- [ ] Scheduler workflow tested
- [ ] Health endpoints verified
- [ ] API connectivity tested
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Security measures in place
- [ ] Documentation updated

## Next Steps

After successful deployment:

1. Monitor application performance
2. Review logs regularly
3. Set up alert notifications
4. Plan for scaling
5. Implement additional features
6. Gather user feedback
7. Iterate on improvements

## Contact

For deployment issues or questions:
- Create a GitHub issue
- Check existing documentation
- Review platform-specific guides
- Contact platform support if needed
