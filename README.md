# OpenSAM — Software Asset Management Starter Kit

A comprehensive, free Software Asset Management (SAM) solution built with Streamlit that helps organizations track software licenses, optimize spending, and maintain compliance. OpenSAM provides Effective License Position (ELP) analysis, renewal tracking, cost allocation, and scenario planning—all the core capabilities found in enterprise SAM platforms like Flexera, ServiceNow SAM, and Snow License Manager.

## Why OpenSAM?

Software Asset Management is critical for:
- **Cost Optimization**: Identify unused licenses and over-deployed software to reduce unnecessary spending
- **Compliance Management**: Avoid audit risks by tracking license usage against entitlements
- **Renewal Planning**: Proactively manage contract renewals and vendor negotiations
- **Budget Allocation**: Allocate software costs across departments for accurate chargeback models

OpenSAM aligns with **ISO 19770-1 ITAM** best practices and provides workflows similar to industry-leading SAM platforms, making it ideal for organizations building or enhancing their software asset management practices.

---

## Quickstart

### Requirements
- **Python 3.12** or higher
- pip package manager

### Installation

```bash
# 1. Clone or download this repository
cd OpenSAM

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`. Sample data is loaded from the `data/` folder by default.

### Using Your Own Data

You can either:
1. **Replace CSV files** in the `data/` folder with your own data (maintain the same column structure)
2. **Upload via UI**: Toggle "Upload CSVs" in the sidebar and upload your files directly

---

## Features

### 1. **Portfolio Overview** (Home Page)
Track your entire software portfolio with key metrics and filtering:

**Key Metrics**:
- Vendors count
- Total products
- Total seats purchased
- Potential savings (subscription licenses)

**Features**:
- Effective License Position (ELP) table with 14+ columns
- Overage badges (⚠️) for at-risk products
- Risk filtering: Over-Used, Expiring < 30d, Inactive Users Present
- Vendor and license type filtering
- Minimum savings threshold filter
- Seat counting toggle: Count by device or by user (for per-user licenses)

**Optimization Tables**:
- **Inactive Users**: Terminated employees still holding installations (reclaim opportunities)
- **Low-Usage**: Installations with no activity in 60+ days

**Exports**:
- ELP Report (CSV)
- Inactive Installs (CSV)
- Low-Usage Installs (CSV)

---

### 2. **Product Drilldown**
Deep-dive analysis for individual products:

**Metrics**:
- Seats Purchased, Active Installs, Unused Seats, Overage, Potential Savings

**Three Detailed Tables**:
- **Active Installs**: Current users with devices and last-used dates
- **Terminated Users (Reclaim Now)**: Immediate reclaim opportunities with savings calculation
- **Low-Usage (60+ days)**: Active users with stale installations

**Key Features**:
- Respects seat counting mode (device vs. user)
- Savings calculations apply to **subscription licenses only**
- Perpetual licenses show $0 savings with maintenance cost disclaimer
- CSV downloads for each table

---

### 3. **Renewal Radar**
Proactive contract expiration tracking and renewal management:

**Key Metrics**:
- Products count
- Expiring in 30 days
- In vendor notice window
- Total annual spend (subscriptions only)

**Features**:
- Vendor-specific renewal notice windows (defaults to 30 days)
- Visual indicators: 🔴 Expiring soon | 🟡 In notice window
- Days remaining calculation with NaT guards
- Max days slider filter (default: 90 days)

**Exports & Integrations**:
- **Standard CSV export**: Full renewal schedule
- **ServiceNow Format**: Pre-mapped fields for CMDB import
- **Email Alert Generator**: Copy-paste text for email/Slack notifications

**ServiceNow Integration**:
- Default mapping for common CMDB fields
- Customizable mapping dictionary in code
- Supports `cmdb_ci`, `alm_license`, `software_model` tables

---

### 4. **Department Allocation**
Cost allocation and chargeback analysis by department:

**Overview Metrics**:
- Total departments
- Total used seats
- Reclaimable seats (terminated users)
- Total reclaimable savings

**Department Table**:
- Used seats per department
- Terminated seats (reclaim opportunities)
- Reclaimable savings (subscription licenses only)
- Share of total spend (proportional allocation)
- Share percentage

**Features**:
- Visual cost distribution chart
- Department-specific software breakdown
- Detailed terminated user lists per department
- Dual CSV exports (summary + department details)

**Use Cases**:
- Budget allocation and chargeback models
- Department-level cost accountability
- Identifying which teams have the most reclaim opportunities

---

### 5. **Scenario Planning**
Model seat reduction scenarios and generate removal recommendations:

**Current State Metrics**:
- Seats Purchased, Active Users, Terminated Users, Unused Seats

**Scenario Configuration**:
- **Reduction Slider**: Choose how many seats to reduce
- **Exclude Terminated Users Checkbox** (recommended): Focus on active users only

**Outputs**:
- **Removal Recommendation List**: Prioritized by least-recently-used (oldest last_used_date first)
- **Projected Savings**: Annual cost reduction (subscription licenses only)
- **Impact Analysis**: New seat count, remaining users, overage warnings

**Exports**:
- Removal Recommendation List (CSV) — ready for department head review
- Scenario Summary (CSV) — documents the analysis with timestamp

**Guidance**:
- Built-in implementation best practices
- Risk mitigation strategies
- Step-by-step action plan

---

## Data Dictionary

### `data/licenses.csv`
Tracks purchased software licenses and contract information.

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `software` | string | ✅ | Product name | `Microsoft 365 E3` |
| `vendor` | string | ✅ | Vendor/publisher name | `Microsoft` |
| `license_type` | string | ✅ | Subscription or perpetual | `subscription` |
| `unit_cost_usd` | float | ✅ | Cost per seat/user (USD) | `36.00` |
| `seats_purchased` | integer | ✅ | Number of purchased licenses | `100` |
| `contract_start` | date | optional | Contract start date (YYYY-MM-DD) | `2025-01-01` |
| `contract_end` | date | ✅ | Contract expiration date (YYYY-MM-DD) | `2025-12-31` |
| `license_key` | string | optional | License key or identifier | `MSFT-XXXX-E3` |

**Notes**:
- Missing `contract_end` will be treated as far-future (no expiration)
- `license_type` must contain "subscription" for savings calculations to apply

---

### `data/installations.csv`
Discovered software installations from endpoint management tools (SCCM, Intune, Jamf, etc.).

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `device_id` | string | ✅ | Unique device identifier | `LAP-001` |
| `user_email` | string | ✅ | User email (joins to users.csv) | `ava@acme.com` |
| `software` | string | ✅ | Product name (matches licenses.csv) | `Microsoft 365 E3` |
| `version` | string | optional | Installed version | `16.0` |
| `install_date` | date | optional | Installation date (YYYY-MM-DD) | `2025-01-02` |
| `last_used_date` | date | ✅ | Last usage timestamp (YYYY-MM-DD) | `2025-11-02` |

**Notes**:
- `last_used_date` drives low-usage analysis (threshold: 60 days)
- `software` must exactly match `software` in licenses.csv

---

### `data/users.csv`
Employee/user roster with organizational metadata.

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `user_email` | string | ✅ | Unique user identifier | `ava@acme.com` |
| `department` | string | optional | Department/cost center | `Engineering` |
| `country` | string | optional | Geographic location | `US` |
| `status` | string | ✅ | Employment status | `active` or `terminated` |

**Notes**:
- `status = terminated` triggers reclaim opportunities
- `department` required for Department Allocation page
- Missing `status` defaults to "unknown"

---

### `data/vendors.csv`
Vendor contact information and renewal settings (optional but recommended).

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `vendor` | string | ✅ | Vendor name (matches licenses.csv) | `Microsoft` |
| `account_manager` | string | optional | Vendor contact name | `Ada Lovelace` |
| `email` | string | optional | Vendor contact email | `alovelace@microsoft.com` |
| `renewal_notice_days` | integer | optional | Days before expiration to alert | `60` |

**Notes**:
- `renewal_notice_days` defaults to **30** if missing
- Used in Renewal Radar to calculate "in notice window"

---

## Configuration & Customization

### Seat Counting Mode
**Location**: Sidebar → Settings

- **Count by device** (default): Each installation = 1 seat
- **Count by user**: Dedupe multiple devices per user

**When to use Count by User**:
- Named user licenses (e.g., "per user" instead of "per device")
- Want to count users, not installations

**Impact**: Affects active seat calculations across all pages

---

### Savings Methodology

**Subscription Licenses**:
- Potential Savings = Unused Seats × Unit Cost
- Applies to: unused seats, terminated users, low-usage scenarios

**Perpetual Licenses**:
- Savings = $0 (no recurring cost)
- Disclaimer: May still incur maintenance/support fees
- Optimization still valuable for reducing support overhead

**Why This Matters**:
Aligns with real-world SAM accounting—perpetual licenses have upfront costs but no annual recurrence, so "savings" from seat reduction doesn't apply.

---

## ServiceNow Integration

### Export Format
The Renewal Radar page includes a ServiceNow-compatible CSV export with field mapping:

**Default Mapping**:
```python
SNOW_MAPPING = {
    "name": "software",
    "manufacturer": "vendor",
    "license_metric": "license_type",
    "cost": "unit_cost_usd",
    "quantity": "seats_purchased",
    "expiration_date": "contract_end"
}
```

### Customization
**Important**: CMDB/Software Model fields vary by ServiceNow implementation.

**Common Tables**:
- `cmdb_ci` (Configuration Item)
- `alm_license` (Asset & License Management)
- `software_model` (Software Asset)

**How to Customize**:
1. Open `pages/2_Renewal_Radar.py`
2. Locate the `SNOW_MAPPING` dictionary (around line 100)
3. Adjust field names to match your ServiceNow instance schema
4. Consult your ServiceNow admin for exact field names

**Example**:
```python
# Your instance may use different field names:
SNOW_MAPPING = {
    "u_product_name": "software",  # custom field
    "manufacturer": "vendor",
    "license_type": "license_type",
    ...
}
```

---

## SAM Workflow Alignment

### How OpenSAM Mirrors Enterprise SAM Tools

| OpenSAM Feature | Flexera Equivalent | ServiceNow SAM Equivalent |
|-----------------|---------------------|--------------------------|
| ELP Table | Effective License Position | License Compliance |
| Overage Badges | Non-Compliant Installations | Compliance Violations |
| Renewal Radar | Contract Manager | Renewal Workflow |
| Department Allocation | Cost Center Reporting | Cost Allocation |
| Scenario Planning | Optimization Advisor | License Optimization |

### ISO 19770-1 ITAM Alignment
OpenSAM supports core ITAM lifecycle processes:
- **Procurement**: License contract tracking
- **Deployment**: Installation discovery
- **Utilization**: Last-used-date monitoring
- **Optimization**: Unused seat identification
- **Retirement**: Terminated user reclamation

---

## Testing & Validation

### Test Cases Included
The sample data includes edge cases for validation:

1. **Overage Product**: `Slack Enterprise` (5 seats purchased, 8 active users)
2. **Expiring Soon**: `Jira Software` and `Slack Enterprise` (< 30 days to expiration)
3. **Perpetual License**: `SAP S/4HANA`, `Adobe Acrobat Pro` (savings = $0)
4. **Terminated Users**: `paul@acme.com`, `uma@acme.com` (reclaim opportunities)
5. **Low-Usage**: `tina@acme.com` (last_used_date > 60 days ago)
6. **Missing Renewal Notice**: `Slack` vendor (tests default = 30 days)
7. **Missing Contract End**: `GitHub Enterprise` (tests NaT guard → 999999 days)

### Manual Acceptance Checklist

Run through these scenarios to validate functionality:

✅ **Overview Page**
- [ ] Change filters → KPIs update correctly
- [ ] ELP table shows ⚠️ badge for Slack Enterprise (overage)
- [ ] CSV downloads match filtered data
- [ ] Savings = $0 for perpetual licenses (SAP, Adobe)
- [ ] Toggle "Subscriptions only" → perpetual products hidden

✅ **Product Drilldown**
- [ ] Select Slack Enterprise → shows 8 active installs, 3 overage
- [ ] Metrics update when selecting different products
- [ ] Terminated Users table shows paul@ and uma@
- [ ] Low-Usage table shows tina@ (if 60+ days old)
- [ ] CSV downloads work for all 3 tables

✅ **Renewal Radar**
- [ ] Jira and Slack show 🔴 (expiring in 30 days)
- [ ] Products with missing contract_end show 999999 days
- [ ] Slack vendor defaults renewal_notice_days to 30
- [ ] "Total Annual Spend" sums subscriptions only (excludes perpetual)
- [ ] ServiceNow CSV exports with mapped fields
- [ ] Email alert generator produces correct text

✅ **Department Allocation**
- [ ] Engineering shows highest seat usage (most users)
- [ ] Reclaimable savings includes paul@ and uma@
- [ ] Share of spend totals to ~100%
- [ ] Department drilldown shows correct software breakdown

✅ **Scenario Planning**
- [ ] Select product → current state metrics accurate
- [ ] "Exclude terminated" ON → only active users in recommendations
- [ ] Recommendations sorted by oldest last_used_date
- [ ] Projected savings correct for subscriptions, $0 for perpetual
- [ ] CSV exports include all selected users

✅ **Session State & Upload**
- [ ] Upload CSV in sidebar → all pages reflect new data
- [ ] Navigate between pages → data persists
- [ ] Toggle seat counting mode → affects all pages

---

## Roadmap & Future Enhancements

### Completed Features ✅
- ✅ ELP tracking and overage detection
- ✅ Renewal tracking with vendor-specific notice windows
- ✅ Department cost allocation
- ✅ Scenario planning with removal recommendations
- ✅ ServiceNow export format
- ✅ Email alert generator

### Planned Enhancements
- [ ] Automated email/Slack alerts via scheduling
- [ ] Historical trend analysis (snapshot comparisons)
- [ ] Compliance workflow with approval process
- [ ] Integration with endpoint management APIs (Intune, Jamf)
- [ ] Advanced reporting with PDF export
- [ ] Multi-currency support

---

## Contributing

Contributions welcome! Please open an issue or pull request for:
- Bug fixes
- New features
- Documentation improvements
- Additional test cases

---

## License

This project is provided as-is under the MIT License. See LICENSE file for details.

---

## Free vs Pro Tiers

### OpenSAM Starter (Free & Open-Source)
Perfect for organizations getting started with Software Asset Management:

✅ **Core Features:**
- Effective License Position (ELP) tracking
- Renewal radar with expiration alerts
- Department cost allocation
- Scenario planning and optimization
- CSV exports (ELP, renewals, allocations)
- ServiceNow-compatible exports
- Local deployment (your infrastructure)

✅ **What You Get:**
- Full source code on GitHub
- Setup scripts for Windows/Mac/Linux
- Comprehensive documentation
- Sample data for testing
- Community support

**Get Started:** Clone the repo and run locally in minutes!

---

### AppForge Labs Pro (Custom Solutions)
Enterprise-ready features with professional implementation:

🚀 **Advanced Features:**
- **Custom Integrations:** SCCM, Intune, Jamf, ServiceNow, Active Directory
- **Automated Data Sync:** Real-time updates from endpoint management tools
- **Alert Automation:** Email, Slack, Microsoft Teams notifications
- **Advanced Analytics:** Usage forecasting, trend analysis, ROI calculators
- **Multi-Tenant Support:** Separate environments for different business units
- **White-Label Deployment:** Branded for your organization
- **Historical Trending:** Track changes over time, compliance snapshots
- **Custom Workflows:** Approval processes, audit trails, compliance reporting

💼 **Professional Services:**
- **Hosted/Managed Version:** We run it for you (cloud deployment)
- **Custom Feature Development:** Build features specific to your needs
- **Integration Services:** Connect to your existing IT infrastructure
- **Training & Onboarding:** Get your team up to speed
- **Dedicated Support:** Priority email/Slack support channel

📊 **Pricing:**
- **Custom Features:** Starting at $500 per feature
- **Integration Services:** Starting at $1,000 per integration
- **Hosted Deployment:** Starting at $50/month
- **Contact us for a custom quote:** paulsemaan007@gmail.com

---

## Support

**For Free Version (OpenSAM Starter):**
- Open an issue on GitHub
- Community support via GitHub Discussions

**For Pro Version & Custom Solutions:**
- Email: paulsemaan007@gmail.com
- Get a custom quote for your organization's needs
- Powered by **AppForge Labs** - Forging solutions from real-world requirements

---

## Credits

**Built by AppForge Labs** - Forging solutions from real-world requirements

**Technology Stack:**
- **Streamlit** — Web application framework
- **Pandas** — Data manipulation and analysis
- **NumPy** — Numerical computing

**Inspired by enterprise SAM platforms:**
- Flexera FlexNet Manager
- ServiceNow SAM Pro
- Snow License Manager
- Microsoft SAM

---

**About AppForge Labs:**
We turn real-world business needs into production-ready applications. OpenSAM was built by analyzing Software Asset Management Analyst job requirements and creating an open-source solution that addresses core SAM workflows.

Visit our website to see more projects and custom solutions.