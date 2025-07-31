# Field Reports Pipeline - Usage Guide

This pipeline supports two execution modes based on the `AUTO_MODE` environment variable.

## Automatic Mode (For Scheduled Execution)
**Perfect for Replit scheduled runs or automated deployments**

### Usage:
```bash
export AUTO_MODE=true
python main.py
```

### Behavior:
- No user input required
- Automatically fetches ALL available reports
- Perfect for scheduled execution on Replit
- Logs all processing details

---

## Interactive Mode (For Manual Control)
**Perfect for manual operations and testing**

### Usage:
```bash
python main.py  # Default mode when AUTO_MODE is not set
```

### Available Options:
- **Option 3:** Fetch specific number of reports [DEFAULT]
- **Option 4:** Show existing processed reports  
- **Option 5:** Run tests

### Behavior:
- User can choose what to do
- Flexible report fetching (specific number or all)
- Can inspect existing data
- Can run tests

---

## Replit Setup for Scheduled Execution

### 1. Set Environment Variable in Replit:
- Go to your Replit project
- Click on "Secrets" tab
- Add: `AUTO_MODE = true`

### 2. Set up Scheduled Run:
- Your scheduled script should just run: `python main.py`
- It will automatically detect `AUTO_MODE=true` and run without prompts

### 3. Manual Testing:
- When you want to test manually, temporarily remove or set `AUTO_MODE = false`
- Run `python main.py` and you'll get the interactive menu

---

## File Structure After Execution:

```
data/
├── raw/
│   └── all_raw_reports.json           # Raw API data
├── processed/
│   └── all_processed_reports.json     # Processed field reports
├── extracted/
│   └── location_extraction_results.json # Location data (if available)
└── logs/
    └── processing_log_YYYYMMDD_HHMMSS.json # Processing logs
```

---

## Quick Start:

**For Replit Scheduled Execution:**
1. Set `AUTO_MODE=true` in Replit Secrets
2. Schedule: `python main.py`

**For Local Development:**
- Run: `python main.py` (interactive mode)
- Choose option 3, 4, or 5 as needed
