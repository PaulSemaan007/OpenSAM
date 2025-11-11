# OpenSAM Quick Start Guide

Welcome to OpenSAM! This guide will get you up and running in minutes.

**Powered by AppForge Labs** - Forging solutions from real-world requirements

---

## Prerequisites

- **Python 3.12 or higher** ([Download here](https://www.python.org/downloads/))
- **pip** (comes with Python)
- **Git** (optional, for cloning the repo)

---

## Installation Methods

### Option 1: Automated Setup (Recommended)

#### Windows:
```bash
# Double-click setup.bat
# Or run from Command Prompt:
setup.bat
```

#### Mac/Linux:
```bash
# Make executable and run:
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Check Python installation
2. Create a virtual environment
3. Install all dependencies
4. Confirm successful installation

---

### Option 2: Manual Setup

If you prefer manual installation:

```bash
# 1. Navigate to the OpenSAM directory
cd OpenSAM

# 2. Create virtual environment
# Windows:
python -m venv .venv
# Mac/Linux:
python3 -m venv .venv

# 3. Activate virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Running OpenSAM

### Windows:
```bash
# Option 1: Use the run script
run.bat

# Option 2: Manual
.venv\Scripts\activate
streamlit run app.py
```

### Mac/Linux:
```bash
# Option 1: Manual activation
source .venv/bin/activate
streamlit run app.py
```

The app will open automatically in your default browser at `http://localhost:8501`

---

## What You'll See

OpenSAM comes pre-loaded with **sample data** from a fictional company (Acme Corp) to demonstrate all features:

### 📊 Main Dashboard (Home)
- **Portfolio Overview**: Vendor count, product count, total seats, potential savings
- **ELP Table**: Effective License Position with overage alerts
- **Optimization Opportunities**: Inactive users and low-usage installations

### 🔍 Product Drilldown
- Deep-dive analysis for individual software products
- Active installations, terminated users, low-usage tracking
- Per-product savings calculations

### 📅 Renewal Radar
- Contract expiration tracking with vendor notice windows
- Expiring soon alerts (🔴) and notice window warnings (🟡)
- ServiceNow export format
- Email alert generator

### 💰 Department Allocation
- Cost allocation by department
- Chargeback model with reclaim opportunities
- Department-specific software breakdown

### 🎯 Scenario Planning
- Model seat reduction scenarios
- Prioritized removal recommendations (by least-recently-used)
- Projected savings calculations
- Implementation guidance

---

## Using Your Own Data

To use OpenSAM with your organization's data:

### 1. Prepare Your CSV Files

Place your files in the `data/` folder:

- **licenses.csv** - Your software licenses and contracts
- **installations.csv** - Discovered installations from endpoint tools
- **users.csv** - Employee roster with status
- **vendors.csv** - Vendor contact information (optional)

### 2. CSV Format Requirements

Refer to the **Data Dictionary** section in [README.md](README.md) for required columns and formats.

**Key Tips:**
- Software names must match exactly between licenses.csv and installations.csv
- Dates should be in YYYY-MM-DD format
- Use "subscription" or "perpetual" for license_type
- User status must be "active" or "terminated"

### 3. Restart the App

After updating CSV files, refresh your browser or restart Streamlit.

---

## Configuration

### Seat Counting Mode

In the **sidebar → Settings**, you can toggle:

- **Count by device** (default): Each installation = 1 seat
- **Count by user**: Dedupe multiple devices per user (for "per-user" licenses)

This affects active seat calculations across all pages.

---

## Customization

OpenSAM is open-source and fully customizable!

**Common Customizations:**
- Adjust low-usage threshold (default: 60 days) in app.py line 327
- Change renewal notice window (default: 30 days) in vendors.csv or app.py line 213
- Modify ServiceNow field mapping in pages/2_Renewal_Radar.py
- Add custom metrics or columns to any page

**Need help customizing?** Contact AppForge Labs for professional services.

---

## Troubleshooting

### "Python not found"
- Install Python 3.12+ from [python.org](https://www.python.org/downloads/)
- **Windows:** Check "Add Python to PATH" during installation
- **Mac:** Use `python3` instead of `python` in commands

### "Module not found" errors
```bash
# Ensure virtual environment is activated
# Then reinstall dependencies:
pip install -r requirements.txt
```

### "Port 8501 already in use"
```bash
# Stop any running Streamlit apps or use a different port:
streamlit run app.py --server.port 8502
```

### Data not loading
- Verify CSV files are in the `data/` folder
- Check for required columns (see README Data Dictionary)
- Look for errors in the terminal/console output

---

## Next Steps

### Explore All Features
Navigate through all 5 pages using the sidebar to see OpenSAM's full capabilities.

### Export Reports
Each page has CSV download buttons for:
- ELP reports
- Renewal schedules (standard + ServiceNow format)
- Department allocations
- Scenario analysis

### Upgrade to Pro

Need more advanced features?

**AppForge Labs Pro offers:**
- Custom integrations (SCCM, Intune, ServiceNow, Active Directory)
- Automated data sync and alerts
- Hosted/managed deployment
- Advanced analytics and forecasting
- White-label customization
- Dedicated support

**Get a quote:** paulsemaan007@gmail.com

---

## Support

**Free Version (Community Support):**
- GitHub Issues: Report bugs or request features
- GitHub Discussions: Ask questions, share tips

**Pro Version (Priority Support):**
- Email: paulsemaan007@gmail.com
- Custom quote for your organization's needs

---

## Resources

- **Full Documentation:** [README.md](README.md)
- **Data Dictionary:** See README.md "Data Dictionary" section
- **Sample Data:** Pre-loaded in `data/` folder
- **License:** MIT License (see [LICENSE](LICENSE))

---

**Built by AppForge Labs**
Forging solutions from real-world requirements

Website: [Coming Soon]
Email: paulsemaan007@gmail.com
GitHub: github.com/paulsemaan007
