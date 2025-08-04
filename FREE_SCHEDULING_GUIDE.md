# Free Scheduling Setup for Field Reports Pipeline

Since you don't have paid Replit service, here's how to schedule your scripts using free external services:

## 🚀 Setup Instructions

### 1. Configure Your Replit Project

Your project is now configured with:
- `web_runner.py` - Web interface for running scripts
- `.replit` - Configuration file to run web_runner.py
- `AUTO_MODE=true` - Set in Replit Secrets for automatic execution

### 2. Start Your Replit Web Service

1. Run your Replit project (it will start `web_runner.py`)
2. Your Replit will be accessible at: `https://your-replit-name.your-username.repl.co`
3. Visit the URL to see available endpoints

### 3. Available Endpoints

- `/run-main` - Runs main.py (field reports processing)
- `/run-final` - Runs final_run.py (GeoNames enrichment) 
- `/run-both` - Runs both scripts sequentially
- `/status` - Check if service is running

## 📅 Free Scheduling Options

### Option 1: cron-job.org (Recommended)

1. **Go to:** https://cron-job.org
2. **Create free account** (allows up to 3 cron jobs)
3. **Add new cron job:**
   - **URL:** `https://your-replit-name.your-username.repl.co/run-both`
   - **Schedule:** Choose your frequency:
     - `0 */6 * * *` (every 6 hours)
     - `0 9 * * *` (daily at 9 AM)
     - `0 */12 * * *` (every 12 hours)

### Option 2: Uptimerobot.com

1. **Go to:** https://uptimerobot.com
2. **Create free account** (50 monitors free)
3. **Add HTTP(s) monitor:**
   - **URL:** `https://your-replit-name.your-username.repl.co/run-both`
   - **Monitoring Interval:** 6 hours (minimum for free)

### Option 3: GitHub Actions (If you want to run from GitHub)

Create `.github/workflows/schedule.yml`:
```yaml
name: Run Field Reports Pipeline
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Replit Pipeline
        run: |
          curl -X GET "https://your-replit-name.your-username.repl.co/run-both"
```

## 🔧 Testing Your Setup

### Manual Test:
1. Visit: `https://your-replit-name.your-username.repl.co/run-main`
2. Should see JSON response with execution results
3. Check your data folder for new files

### Scheduled Test:
1. Set up a cron job for 5 minutes from now
2. Check the response/logs
3. Verify files are updated

## 📊 Monitoring

- **Check Status:** Visit `/status` endpoint
- **View Logs:** Check Replit console for execution logs
- **File Updates:** Monitor `data/logs/` for processing logs

## 🔒 Security Notes

- Your Replit URL is public but requires knowledge of exact endpoints
- Consider adding basic authentication if needed
- Monitor usage to stay within free tier limits

## 💡 Pro Tips

1. **Keep Replit Alive:** Visit your main URL occasionally to prevent sleeping
2. **Monitor Limits:** Free external services have call limits
3. **Backup Schedule:** Use multiple services for redundancy
4. **Test First:** Always test manually before setting up automation

## 📝 Example URLs

Replace `your-replit-name` and `your-username` with your actual values:

- **Main Page:** `https://your-replit-name.your-username.repl.co/`
- **Run Both Scripts:** `https://your-replit-name.your-username.repl.co/run-both`
- **Status Check:** `https://your-replit-name.your-username.repl.co/status`
