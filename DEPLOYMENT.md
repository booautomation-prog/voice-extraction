# Cloud Deployment Guide

This guide helps you deploy the Voice Extraction web app to the cloud so you can access it from mobile devices.

## Option 1: Deploy to Railway (Recommended - Easiest)

### Prerequisites
- GitHub account
- Railway account (free tier available at [railway.app](https://railway.app))

### Steps

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/voice-extraction.git
   git push -u origin main
   ```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account and select your repository
   - Railway will auto-detect the Flask app and deploy it

3. **Configure Environment:**
   - In Railway dashboard, add variables if needed
   - Set up custom domain for easy access

4. **Access from Mobile:**
   - Once deployed, Railway gives you a URL like `your-app.railway.app`
   - Visit this URL on your mobile phone
   - Bookmark it for quick access

## Option 2: Deploy to Heroku (Requires Credit Card)

### Prerequisites
- Heroku account ([heroku.com](https://heroku.com))
- Heroku CLI installed

### Steps

1. **Create Procfile:**
   ```bash
   echo "web: gunicorn app:app" > Procfile
   ```

2. **Deploy:**
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```

3. **Access:**
   - Visit `your-app-name.herokuapp.com` from mobile

## Option 3: Run Locally & Access from Mobile (Advanced)

### Prerequisites
- Same network (home WiFi or hotspot)

### Steps

1. **Find your computer's IP:**
   ```powershell
   ipconfig | findstr /i "IPv4"
   ```
   Look for something like `192.168.x.x`

2. **Run the app:**
   ```bash
   python app.py
   ```

3. **On mobile phone:**
   - Connect to same WiFi
   - Open browser and go to: `http://YOUR_IP_ADDRESS:5000`
   - Port forward if accessing outside your network

## Limitations & Notes

⚠️ **Important:** The free tiers on Railway/Heroku have limitations:
- Model downloads (~200-500MB) on first run
- Processing takes 1-2 minutes per song
- Temporary files need cleanup

**For production use, consider:**
- Using a paid tier with more resources
- Pre-downloading models
- Implementing job queue system (Celery/Redis)
- Using async processing

## Troubleshooting

**"Model not found":**
- First run downloads the Demucs model (~500MB)
- Subsequent runs are faster

**"Timeout":**
- Long songs may timeout on free tiers
- Try with shorter songs first

**"Storage limit":**
- Railway/Heroku have limited storage
- Implement automatic cleanup of old files

## Environment Variables (Optional)

Create a `.env` file for production:
```
FLASK_ENV=production
MAX_UPLOAD_SIZE=500
CLEANUP_INTERVAL=3600
```
