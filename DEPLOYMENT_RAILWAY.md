# Railway Deployment Guide

This guide walks you through deploying the OCR + Translation API to [Railway.app](https://railway.app).

## Prerequisites

- Railway account (free tier available at https://railway.app)
- GitHub account with your repository pushed
- Git CLI installed locally

## Step-by-Step Deployment

### 1. Create Railway Account & Login

```bash
# Install Railway CLI (macOS with Homebrew)
brew install railway

# Login to Railway
railway login
```

### 2. Create a New Project

Option A: **Using Railway Dashboard** (Easiest)
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Authorize Railway to access your GitHub repos
5. Select your `eng-guj-ocr` repository
6. Click "Deploy"

Option B: **Using Railway CLI**
```bash
cd /path/to/Eng_Guj
railway init
# Follow prompts to create a new project
railway up
```

### 3. Configure Environment Variables (Dashboard)

After deployment starts:
1. Go to your project on Railway
2. Click on the service/deployment
3. Go to **Variables** tab
4. Add the following environment variables:

```
PYTHONUNBUFFERED=1
EASYOCR_MODULE_PATH=/root/.EasyOCR
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
```

**Optional optimizations:**
```
# Smaller Whisper model for faster cold starts (smaller = faster)
WHISPER_MODEL=tiny

# Use GPU if available (usually not on free tier)
WHISPER_DEVICE=cuda
```

### 4. Monitor Deployment

1. Watch the build logs in Railway dashboard
2. First build takes **5-10 minutes** (downloading ML models)
3. Once "Success ✓" appears, your app is live

### 5. Access Your Application

Find your URL in Railway:
1. Go to your service
2. Look for **Domains** section
3. Your URL will be like: `https://ocr-api-production.up.railway.app`

Visit your API:
- **Frontend UI**: `https://your-railway-url.app`
- **API Docs**: `https://your-railway-url.app/docs`
- **API Info**: `https://your-railway-url.app/api-info`

## Post-Deployment

### Connect Custom Domain (Optional)
1. In Railway, go to **Domains**
2. Add custom domain
3. Configure DNS records as instructed

### View Logs

```bash
# Watch live logs
railway logs -f

# Or via Dashboard: Service → Logs tab
```

### Restart Service

```bash
railway redeploy
```

### Stop Service

```bash
railway down
```

## Troubleshooting

### Build Fails with Disk Space Error
- Railway free tier has **500MB** limit
- This project uses ~300MB with ML models
- **Solution**: Use `railway up --select` to choose a service tier with more space

### App Crashes During First Request
- **Reason**: ML models are initializing (normal)
- **Solution**: Wait 30-60 seconds, then try again
- Models cache after first load

### Port Binding Error
- Ensure `Dockerfile` uses environment variable: `--port $PORT`
- Railway automatically assigns `PORT` variable
- ✓ Already configured in our setup

### Timeout on OCR/Whisper
- **Reason**: Large files or complex images
- **Solution**: Increase Railway timeout in dashboard
  - Service Settings → Timeout → Set to 120s

### Out of Memory
- **Reason**: Multiple concurrent requests with OCR
- **Solution**: 
  - Scale up to paid tier for more memory
  - Implement request queuing
  - Reduce model size (use `tiny` Whisper)

## Costs

**Railway Free Tier:**
- $5 credit/month (usually enough)
- Includes: 500MB storage, 100 hours/month
- Great for testing

**Paid Tiers:**
- Pay-as-you-go ($0.50/GB storage, $0.10/GB bandwidth)
- More reliable for production

## Monitoring & Logs

```bash
# View detailed logs
railway logs -f

# Check service health
railway logs --service ocr-api
```

## Redeploy Latest Code

```bash
git push
# Railway auto-deploys on push (if configured)
```

Or manually:
```bash
railway redeploy
```

## Environment-Specific Configuration

### Production Settings
```
WHISPER_MODEL=base      # Better accuracy
PYTHONUNBUFFERED=1
DEBUG=false
```

### Development/Testing
```
WHISPER_MODEL=tiny      # Faster for testing
DEBUG=true
```

## GitHub Integration

Railway auto-deploys on push to main branch:

```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

Check deployment status in Railway dashboard under **Deployments** tab.

## API Rate Limiting (Optional)

If getting rate-limited, add to `advanced_ocr_api.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/translate-text")
@limiter.limit("10/minute")
async def translate_text(...):
    ...
```

## Useful Railway Commands

```bash
# List all projects
railway list

# Switch project
railway switch

# View service status
railway status

# SSH into container
railway shell

# Deploy from specific branch
railway deploy --branch develop

# Set environment variables
railway variables set KEY=value

# View variables
railway variables
```

## Next Steps

1. ✅ Deployed on Railway
2. Share your URL: `https://your-railway-url.app`
3. Monitor logs regularly
4. Consider upgrading if you need more resources
5. Set up GitHub CI/CD for automated deployments

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: Add troubleshooting details
