# Deployment Instructions

## 🚀 GitHub Upload Steps

1. **Initialize Git Repository** (if not already done):
   ```bash
   cd C:\scripts\bearduk
   git init
   git add .
   git commit -m "Initial commit: BEARD UK website with 80s synthwave theme and Facebook scraping"
   ```

2. **Connect to GitHub**:
   ```bash
   git remote add origin https://github.com/jc230285/bearduk.git
   git branch -M main
   git push -u origin main
   ```

## 🐳 Coolify Deployment

### Method 1: Direct GitHub Integration (Recommended)

1. **In Coolify Dashboard**:
   - Go to "Projects" → "New Project"
   - Select "Git Repository"
   - Enter: `https://github.com/jc230285/bearduk.git`
   - Branch: `main`

2. **Deployment Settings**:
   - **Build Pack**: Docker
   - **Port**: 5000
   - **Health Check**: `/` (root path)
   - **Auto Deploy**: Enabled

3. **Environment Variables** (optional):
   ```
   FLASK_ENV=production
   PORT=5000
   ```

### Method 2: Manual Docker Build

```bash
# Build locally and push to registry
docker build -t bearduk-website .
docker tag bearduk-website your-registry/bearduk-website
docker push your-registry/bearduk-website
```

## 🔧 Production Features

- ✅ **Gunicorn WSGI Server** for production performance
- ✅ **Google Chrome** installed for Selenium scraping
- ✅ **Health Checks** for container monitoring
- ✅ **Security** with non-root user
- ✅ **Optimized** with .dockerignore and layer caching
- ✅ **Persistent Data** with volume mounting (if needed)

## 🌐 Post-Deployment

After deployment, your BEARD website will be live with:

- **Automatic Facebook scraping** every 24 hours
- **Mobile-responsive design** 
- **80s synthwave aesthetics**
- **Real-time event updates**
- **Production-grade performance**

## 🔍 Monitoring

The container includes health checks that ping `http://localhost:5000/` every 30 seconds. Coolify will automatically restart the container if health checks fail.

## 🛠️ Troubleshooting

If Facebook scraping fails in production:
- The app has fallback manual events
- Check Coolify logs for Selenium errors
- Chrome headless mode is optimized for containers