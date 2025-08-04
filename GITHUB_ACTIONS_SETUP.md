# GitHub Actions Automation Setup

**Single-Approach Solution: GitHub Actions + Free Replit**

## 🚀 How It Works

1. **GitHub Actions** runs daily at 10:00 AM UTC
2. **Wakes up your Replit** service (if sleeping)
3. **Calls your pipeline** via HTTP endpoint
4. **Scripts execute automatically** without user input
5. **Data gets processed** and saved to your repository

## 📋 Setup Steps

### Step 1: Upload to Replit
1. Create a new Replit project
2. Upload all your files
3. Click "Run" to start the web service
4. Note your Replit URL: `https://your-replit-name.your-username.repl.co`

### Step 2: Update GitHub Action
1. Edit `.github/workflows/daily-pipeline.yml`
2. Replace `your-replit-name.your-username.repl.co` with your actual Replit URL
3. Commit and push to GitHub

### Step 3: Enable GitHub Actions
1. Go to your GitHub repository
2. Click "Actions" tab
3. GitHub Actions should be automatically enabled
4. You'll see "Daily Field Reports Pipeline" workflow

### Step 4: Test the Setup
1. **Manual Test:** Go to Actions → "Daily Field Reports Pipeline" → "Run workflow"
2. **Check Replit:** Visit your Replit URL to see if it's working
3. **Verify Data:** Check if files are created in `data/` folder

## ⏰ Execution Schedule

- **Automatic:** Daily at 10:00 AM UTC
- **Manual:** Can be triggered anytime from GitHub Actions
- **Status:** Check at `your-replit-url/status`
- **Logs:** Check at `your-replit-url/logs`

## 🔧 Configuration

### Change Schedule
Edit `.github/workflows/daily-pipeline.yml`:
```yaml
schedule:
  - cron: '0 10 * * *'  # Daily at 10 AM UTC
  - cron: '0 22 * * *'  # Daily at 10 PM UTC (twice daily)
  - cron: '0 10 * * 1'  # Weekly on Mondays at 10 AM UTC
```

### Change Scripts
The workflow calls `/run-both` which runs:
1. `main.py` (field reports processing)
2. `final_run.py` (GeoNames enrichment) - only if main.py succeeds

## 📊 Monitoring

### Check Status
- **GitHub Actions:** See execution history in GitHub
- **Replit Status:** Visit `your-replit-url/status`
- **Recent Logs:** Visit `your-replit-url/logs`
- **Data Files:** Check `data/` folder for updates

### Troubleshooting
1. **GitHub Action fails:** Check the logs in GitHub Actions tab
2. **Replit sleeping:** The action automatically wakes it up
3. **Script errors:** Check `/logs` endpoint or Replit console
4. **No data:** Verify environment variables are set in Replit

## 🎯 Benefits of This Approach

✅ **Completely Free** - Uses GitHub Actions free tier  
✅ **Reliable** - GitHub's infrastructure, not dependent on external services  
✅ **Simple** - Single automation source  
✅ **Transparent** - All execution logs visible in GitHub  
✅ **Flexible** - Easy to modify schedule or add more workflows  

## 🔗 Quick Links

- **Manual Trigger:** GitHub → Actions → Daily Field Reports Pipeline → Run workflow
- **View Logs:** GitHub → Actions → Click on any workflow run
- **Check Service:** `your-replit-url/status`
- **View Data:** `your-replit-url/logs`

## 🚨 Important Notes

- **Free Replit** may sleep after inactivity - GitHub Actions will wake it up
- **GitHub Actions** has 2000 minutes/month free (more than enough for daily runs)
- **Execution time** is around 5-10 minutes per run
- **Data persistence** is maintained in your Replit project
