import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="OpenSAM - Software Asset Management",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Business Professional Theme
st.markdown("""
<style>
    /* Business Professional Theme - Greens & Teals */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #16a085;
        margin-bottom: 0.5rem;
        border-bottom: 3px solid #1abc9c;
        padding-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #34495e;
        margin-bottom: 2rem;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #16a085 0%, #1abc9c 100%);
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    [data-testid="stSidebar"] .stButton button {
        background-color: white;
        color: #16a085 !important;
        font-weight: bold;
        border: 2px solid white;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #ecf0f1;
        border-color: #ecf0f1;
    }
    /* Metric cards */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #16a085;
        font-weight: bold;
    }
    /* Status badges */
    .badge-success {
        background-color: #27ae60;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 0.3rem;
        font-weight: 600;
    }
    .badge-warning {
        background-color: #f39c12;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 0.3rem;
        font-weight: 600;
    }
    .badge-danger {
        background-color: #e74c3c;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 0.3rem;
        font-weight: 600;
    }
    .badge-info {
        background-color: #3498db;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 0.3rem;
        font-weight: 600;
    }
    /* Headers */
    h1, h2, h3 {
        color: #2c3e50;
    }
    /* Links */
    a {
        color: #16a085;
        text-decoration: none;
    }
    a:hover {
        color: #1abc9c;
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar info
st.sidebar.markdown("# 💼 OpenSAM")
st.sidebar.markdown("*Software Asset Management*")
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "OpenSAM helps IT teams track software licenses, optimize spending, "
    "maintain compliance, and eliminate wasteful subscriptions."
)

st.sidebar.markdown("### Free vs Pro")
st.sidebar.markdown("""
**Free (Current)**
- Single-user mode
- CSV data storage
- All core features
- 5 analysis modules

**Pro Version**
- Multi-user with auth
- Database backend
- ServiceNow integration
- Automated renewals
- Custom branding
- Priority support
""")

if st.sidebar.button("🚀 Upgrade to Pro"):
    st.sidebar.success("Contact: paulsemaan007@gmail.com")

st.sidebar.markdown("---")

st.title("OpenSAM — Software Asset Management (Starter)")

# First-time user welcome banner
if "first_visit" not in st.session_state:
    st.session_state.first_visit = True

if st.session_state.first_visit:
    st.success("""
    👋 **Welcome to OpenSAM!** This is a live demo with sample data from a fictional company (Acme Corp).

    **Quick Start Guide:**
    - 💰 See that **$75K+ savings**? Those are unused seats you could reclaim
    - ⚠️ **Red badges** = Action needed (overages, expirations, terminated users)
    - 🔍 **Hover over ℹ️ icons** throughout for help on what each feature does
    - 📊 **Use the sidebar** to explore other pages (Renewal Radar, Product Drilldown, Scenarios)

    Click below to dismiss this message and start exploring!
    """)
    col_dismiss1, col_dismiss2, col_dismiss3 = st.columns([1, 1, 2])
    with col_dismiss1:
        if st.button("✅ Got it! Let me explore", use_container_width=True, type="primary"):
            st.session_state.first_visit = False
            st.rerun()

# Demo disclaimer banner
st.info("📊 **Demo Mode:** This is a live demo using sample data. Contact AppForge Labs for production deployment with your real data.", icon="ℹ️")

# ============================================================================
# Formatting Helpers (Reusable across all pages)
# ============================================================================

def fmt_currency(value):
    """Format value as currency."""
    if pd.isna(value):
        return "$0.00"
    return f"${value:,.2f}"

def fmt_currency_series(s):
    """Format pandas Series as currency."""
    return s.apply(lambda x: fmt_currency(x) if pd.notna(x) else "$0.00")

def fmt_date(value):
    """Format date value."""
    if pd.isna(value):
        return ""
    if isinstance(value, str):
        return value
    return pd.to_datetime(value, errors="coerce").strftime("%Y-%m-%d")

def fmt_date_series(s):
    """Format pandas Series as dates."""
    return pd.to_datetime(s, errors="coerce").dt.strftime("%Y-%m-%d")

def fmt_number(value):
    """Format number with commas."""
    if pd.isna(value):
        return "0"
    return f"{value:,.0f}"

# ============================================================================
# Schema Validation
# ============================================================================

def validate_schema(df, name, required_cols):
    """Validate that dataframe has required columns."""
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.warning(f"⚠️ {name} is missing columns: {', '.join(missing)}. Some features may be disabled.")
        return False
    return True

# ============================================================================
# Data Loading with Session State
# ============================================================================

@st.cache_data(ttl=60)
def load_csv(path):
    """Load CSV with caching and TTL."""
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        st.error(f"File not found: {path}")
        return pd.DataFrame()

def coerce_dates(df, cols):
    """Convert specified columns to date type."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    return df

def load_data():
    """Load all data sources and store in session_state."""
    # Check if we need to reload
    if "data" in st.session_state and "data_loaded" in st.session_state:
        return st.session_state["data"]

    # Load from uploads or files
    data = {}

    with st.sidebar:
        st.header("Data Sources")
        # Demo mode: CSV uploads disabled for security
        st.caption("📊 Using sample data (Acme Corp)")
        st.caption("💡 Want to use your own data? Contact AppForge Labs for a custom deployment.")

        # Load from local files only (secure for public demo)
        data["licenses"] = load_csv("data/licenses.csv")
        data["installs"] = load_csv("data/installations.csv")
        data["users"] = load_csv("data/users.csv")
        data["vendors"] = load_csv("data/vendors.csv")

    # Validate schemas
    validate_schema(data["licenses"], "licenses.csv",
                    ["software", "vendor", "license_type", "unit_cost_usd", "seats_purchased", "contract_end"])
    validate_schema(data["installs"], "installations.csv",
                    ["device_id", "user_email", "software", "last_used_date"])
    validate_schema(data["users"], "users.csv",
                    ["user_email", "status"])
    # vendors is optional, but check if it exists
    if not data["vendors"].empty:
        if "vendor" not in data["vendors"].columns:
            st.warning("⚠️ vendors.csv is missing 'vendor' column. Vendor data will not be used.")

    # Coerce dates
    data["licenses"] = coerce_dates(data["licenses"], ["contract_start", "contract_end"])
    data["installs"] = coerce_dates(data["installs"], ["install_date", "last_used_date"])

    # Normalize
    if "software" in data["licenses"].columns:
        data["licenses"]["software"] = data["licenses"]["software"].astype(str)
    if "software" in data["installs"].columns:
        data["installs"]["software"] = data["installs"]["software"].astype(str)

    # Store in session
    st.session_state["data"] = data
    st.session_state["data_loaded"] = True

    return data

# Load data
data = load_data()
licenses = data["licenses"]
installs = data["installs"]
users = data["users"]
vendors = data["vendors"]

# Check if data is empty
if licenses.empty or installs.empty or users.empty:
    st.error("❌ Required data files are missing or empty. Please check data/ folder.")
    st.stop()

# ============================================================================
# Seat Counting Toggle
# ============================================================================

with st.sidebar:
    st.markdown("---")
    st.header("Settings")
    count_by_user = st.checkbox(
        "Count seats by user (dedupe devices)",
        value=False,
        help="When ON: Count unique users instead of devices. Use for per-user licenses."
    )
    st.caption("📌 Per-user licenses dedupe devices; per-device licenses do not.")

    # Store in session state for other pages to access
    st.session_state["count_by_user"] = count_by_user

# ============================================================================
# Data Processing
# ============================================================================

# Join installs->users for status and department
installs_users = installs.merge(users, on="user_email", how="left")

# Fill missing status
if "status" in installs_users.columns:
    installs_users["status"] = installs_users["status"].fillna("unknown")

# Utilization calc per software
if count_by_user:
    # Count unique users, not devices
    usage = installs_users.groupby("software").agg(
        installs_count=("user_email", "nunique"),
        active_installs=("user_email", lambda s: installs_users.loc[s.index][installs_users.loc[s.index, "status"] == "active"]["user_email"].nunique()),
        inactive_installs=("user_email", lambda s: installs_users.loc[s.index][installs_users.loc[s.index, "status"] == "terminated"]["user_email"].nunique()),
        last_used_max=("last_used_date", "max"),
    ).reset_index()
else:
    # Count devices (original logic)
    usage = installs_users.groupby("software").agg(
        installs_count=("device_id", "nunique"),
        active_installs=("status", lambda s: (s == "active").sum() if s.notna().any() else 0),
        inactive_installs=("status", lambda s: (s == "terminated").sum() if s.notna().any() else 0),
        last_used_max=("last_used_date", "max"),
    ).reset_index()

# Merge with licenses
sam = licenses.merge(usage, on="software", how="left").fillna({"installs_count": 0, "active_installs": 0, "inactive_installs": 0})
sam["installs_count"] = sam["installs_count"].astype(int)
sam["active_installs"] = sam["active_installs"].astype(int)
sam["inactive_installs"] = sam["inactive_installs"].astype(int)

# ELP & savings
today = datetime.utcnow().date()
sam["seats_used"] = sam["active_installs"]
sam["seats_unused"] = (sam["seats_purchased"] - sam["seats_used"]).clip(lower=0)
sam["overage"] = (sam["seats_used"] - sam["seats_purchased"]).clip(lower=0)
sam["elp"] = sam["seats_purchased"] - sam["seats_used"]

# Contract days remaining with guard for NaT
if "contract_end" in sam.columns:
    sam["contract_days_remaining"] = sam["contract_end"].apply(
        lambda x: (x - today).days if pd.notna(x) else 999999
    )
else:
    sam["contract_days_remaining"] = 999999

sam["renewal_due"] = sam["contract_days_remaining"].apply(lambda d: d <= 30)

# Potential savings (SUBSCRIPTIONS ONLY)
if "license_type" in sam.columns and "unit_cost_usd" in sam.columns:
    sam["potential_savings_usd"] = np.where(
        sam["license_type"].str.contains("subscription", case=False, na=False),
        sam["seats_unused"] * sam["unit_cost_usd"],
        0
    )
else:
    sam["potential_savings_usd"] = 0

# ============================================================================
# Filters
# ============================================================================

st.subheader("Filters")
cols = st.columns(4)
with cols[0]:
    vendor_filter = st.multiselect(
        "Vendor",
        sorted(sam["vendor"].dropna().unique().tolist()) if "vendor" in sam.columns else [],
        help="🔍 Filter by software vendor (Microsoft, Salesforce, etc.)"
    )
with cols[1]:
    risk_filter = st.selectbox(
        "Risk",
        ["All", "Over-Used", "Expiring < 30d", "Inactive Users Present"],
        help="⚠️ Over-Used = compliance issue (more users than seats). Expiring = contract ends soon. Inactive = terminated users still have licenses."
    )
with cols[2]:
    min_savings = st.number_input(
        "Min Potential Savings ($)",
        value=0,
        min_value=0,
        step=50,
        help="💰 Only show products with at least this much savings potential (unused seats × unit cost)"
    )
with cols[3]:
    only_subs = st.toggle(
        "Subscriptions only",
        value=False,
        help="📅 Show only subscription licenses (exclude perpetual/one-time purchases)"
    )

st.caption("""
**Risk Definitions:**
• Over-Used = Active installs exceed purchased seats (overage > 0)
• Expiring < 30d = Contract ends within 30 days
• Inactive Users Present = Terminated users still hold installations
""")

# Apply filters
filtered = sam.copy()
if vendor_filter:
    filtered = filtered[filtered["vendor"].isin(vendor_filter)]
if only_subs and "license_type" in filtered.columns:
    filtered = filtered[filtered["license_type"].str.contains("subscription", case=False, na=False)]
if risk_filter != "All":
    if risk_filter == "Over-Used":
        filtered = filtered[filtered["overage"] > 0]
    elif risk_filter == "Expiring < 30d":
        filtered = filtered[filtered["renewal_due"] == True]
    elif risk_filter == "Inactive Users Present":
        filtered = filtered[filtered["inactive_installs"] > 0]
filtered = filtered[filtered["potential_savings_usd"] >= min_savings]

# ============================================================================
# How to Use This Page (Collapsible Guide)
# ============================================================================

with st.expander("🎯 How to Use This Page (Click to Expand)"):
    col_guide1, col_guide2 = st.columns(2)
    with col_guide1:
        st.markdown("**🔍 What You're Seeing:**")
        st.markdown("- **All software licenses** in your portfolio at a glance")
        st.markdown("- **Red ⚠️ badges** highlight products that need attention")
        st.markdown("- **Charts** show license breakdown, top vendors, and renewal timeline")
        st.markdown("- **Green savings numbers** = money you could reclaim from unused seats")
    with col_guide2:
        st.markdown("**✅ What To Do:**")
        st.markdown("1. Check **Action Items** alerts at the top (urgent issues)")
        st.markdown("2. Use **Filters** to find specific problems (overages, expiring contracts)")
        st.markdown("3. Review the **ELP table** below to see seat usage vs. purchased")
        st.markdown("4. Look at **Inactive Users** to reclaim licenses immediately")
        st.markdown("5. Download **CSV exports** at the bottom to share with your team")

st.markdown("---")

# ============================================================================
# Portfolio Overview Metrics
# ============================================================================

st.subheader("Portfolio Overview")
k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Vendors",
    filtered["vendor"].nunique() if "vendor" in filtered.columns else 0,
    help="🏢 Number of unique software vendors in your portfolio"
)
k2.metric(
    "Products",
    filtered["software"].nunique() if "software" in filtered.columns else 0,
    help="📦 Number of distinct software products (licenses)"
)
k3.metric(
    "Total Seats",
    int(filtered["seats_purchased"].sum()) if "seats_purchased" in filtered.columns else 0,
    help="💺 Total number of licenses purchased across all products"
)
k4.metric(
    "Potential Savings",
    fmt_currency(filtered["potential_savings_usd"].sum()),
    help="💰 Annual savings if you remove all unused seats from subscription licenses. Perpetual licenses excluded."
)

st.caption("💡 **Potential Savings** counts subscription licenses only (perpetual licenses excluded). Perpetual licenses may still incur maintenance/support costs; savings shown exclude those.")

# ============================================================================
# Smart Alerts Banner
# ============================================================================

# Calculate top alerts
alerts = []

# Alert 1: Contracts expiring soon
expiring_soon = filtered[filtered["contract_days_remaining"] <= 10]
if len(expiring_soon) > 0:
    alerts.append({
        "icon": "🔴",
        "priority": 1,
        "message": f"URGENT: {len(expiring_soon)} contract{'s' if len(expiring_soon) > 1 else ''} expiring in ≤10 days",
        "products": ", ".join(expiring_soon["software"].head(3).tolist())
    })

# Alert 2: Overage situations
overages = filtered[filtered["overage"] > 0]
if len(overages) > 0:
    total_overage = int(overages["overage"].sum())
    alerts.append({
        "icon": "⚠️",
        "priority": 2,
        "message": f"COMPLIANCE RISK: {len(overages)} product{'s' if len(overages) > 1 else ''} over-deployed ({total_overage} seats)",
        "products": ", ".join(overages["software"].head(3).tolist())
    })

# Alert 3: Reclaim opportunities
inactive_total = filtered["inactive_installs"].sum()
if inactive_total > 0:
    # Calculate reclaimable value (subscriptions only)
    reclaim_value = 0
    for _, row in filtered[filtered["inactive_installs"] > 0].iterrows():
        if pd.notna(row.get("license_type")) and "subscription" in str(row["license_type"]).lower():
            reclaim_value += row["inactive_installs"] * row.get("unit_cost_usd", 0)

    if reclaim_value > 0:
        alerts.append({
            "icon": "💰",
            "priority": 3,
            "message": f"SAVINGS OPPORTUNITY: Reclaim {fmt_currency(reclaim_value)} from {int(inactive_total)} inactive user{'s' if inactive_total > 1 else ''}",
            "products": ""
        })

# Alert 4: High potential savings
high_savings = filtered[filtered["potential_savings_usd"] >= 5000].sort_values("potential_savings_usd", ascending=False)
if len(high_savings) > 0 and len(alerts) < 3:
    top_product = high_savings.iloc[0]
    alerts.append({
        "icon": "📊",
        "priority": 4,
        "message": f"OPTIMIZATION: {top_product['software']} has {fmt_currency(top_product['potential_savings_usd'])} in unused seats",
        "products": ""
    })

# Display alerts
if alerts:
    st.markdown("### 🚨 Action Items")

    # Sort by priority
    alerts_sorted = sorted(alerts, key=lambda x: x["priority"])

    for alert in alerts_sorted[:3]:  # Show top 3
        if alert["products"]:
            st.warning(f"{alert['icon']} **{alert['message']}**\n\n*Products: {alert['products']}*")
        else:
            st.warning(f"{alert['icon']} **{alert['message']}**")

    st.markdown("---")

# ============================================================================
# Visual Dashboard
# ============================================================================

st.subheader("Portfolio Insights")

# Create 3 columns for charts
chart_col1, chart_col2, chart_col3 = st.columns(3)

with chart_col1:
    # Subscription vs Perpetual breakdown
    st.markdown("**License Type Distribution**")
    if "license_type" in filtered.columns:
        license_counts = filtered.groupby("license_type").agg(
            count=("software", "count"),
            total_spend=("unit_cost_usd", lambda x: (x * filtered.loc[x.index, "seats_purchased"]).sum())
        ).reset_index()

        fig_license = px.pie(
            license_counts,
            values="count",
            names="license_type",
            color_discrete_sequence=["#2563eb", "#64748b", "#10b981"]
        )
        fig_license.update_traces(textposition='inside', textinfo='percent+label')
        fig_license.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_license, use_container_width=True)

with chart_col2:
    # Top 5 vendors by spend
    st.markdown("**Top Vendors by Spend**")
    if "vendor" in filtered.columns and "unit_cost_usd" in filtered.columns:
        vendor_spend = filtered.groupby("vendor").apply(
            lambda x: (x["unit_cost_usd"] * x["seats_purchased"]).sum()
        ).sort_values(ascending=False).head(5).reset_index()
        vendor_spend.columns = ["vendor", "total_spend"]

        fig_vendor = px.bar(
            vendor_spend,
            x="total_spend",
            y="vendor",
            orientation="h",
            color_discrete_sequence=["#2563eb"]
        )
        fig_vendor.update_layout(
            showlegend=False,
            height=250,
            margin=dict(t=0, b=0, l=10, r=0),
            xaxis_title="Total Annual Spend ($)",
            yaxis_title=""
        )
        st.plotly_chart(fig_vendor, use_container_width=True)

with chart_col3:
    # Contracts expiring in next 90 days
    st.markdown("**Renewal Timeline (90 days)**")
    expiring_90 = filtered[filtered["contract_days_remaining"] <= 90].sort_values("contract_days_remaining")

    if len(expiring_90) > 0:
        # Create timeline chart
        expiring_90_display = expiring_90.head(10).copy()  # Top 10 soonest
        expiring_90_display["color"] = expiring_90_display["contract_days_remaining"].apply(
            lambda x: "Urgent (<30d)" if x <= 30 else "Soon (30-90d)"
        )

        fig_timeline = px.bar(
            expiring_90_display,
            y="software",
            x="contract_days_remaining",
            orientation="h",
            color="color",
            color_discrete_map={"Urgent (<30d)": "#dc2626", "Soon (30-90d)": "#f59e0b"}
        )
        fig_timeline.update_layout(
            showlegend=True,
            height=250,
            margin=dict(t=0, b=0, l=10, r=0),
            xaxis_title="Days Until Expiration",
            yaxis_title="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No contracts expiring in next 90 days")

st.markdown("---")

# ============================================================================
# ELP Table with Overage Badges
# ============================================================================

st.subheader("Effective License Position & Risks", help="📊 ELP = Seats Purchased - Seats Used. Shows if you're over or under-deployed.")

# Prepare display dataframe
display_cols = ["software", "vendor", "license_type", "seats_purchased", "seats_used", "elp", "overage", "seats_unused"]

# Add overage indicator column
filtered["overage_alert"] = filtered["overage"].apply(lambda x: "⚠️" if x > 0 else "")

display_df = filtered[["overage_alert"] + display_cols + ["unit_cost_usd", "potential_savings_usd", "contract_end", "contract_days_remaining", "renewal_due", "inactive_installs"]].copy()

# Format currency columns for display
display_df["unit_cost_usd_fmt"] = display_df["unit_cost_usd"].apply(fmt_currency)
display_df["potential_savings_usd_fmt"] = display_df["potential_savings_usd"].apply(fmt_currency)
display_df["contract_end_fmt"] = display_df["contract_end"].apply(fmt_date)

# Create final display with formatted columns
final_display = display_df[[
    "overage_alert", "software", "vendor", "license_type", "seats_purchased", "seats_used",
    "elp", "overage", "seats_unused", "unit_cost_usd_fmt", "potential_savings_usd_fmt",
    "contract_end_fmt", "contract_days_remaining", "renewal_due", "inactive_installs"
]].rename(columns={
    "overage_alert": "⚠️",
    "unit_cost_usd_fmt": "unit_cost_usd",
    "potential_savings_usd_fmt": "potential_savings_usd",
    "contract_end_fmt": "contract_end"
})

st.dataframe(final_display, use_container_width=True)

st.caption(f"📊 Active seats counted by: **{'unique users' if count_by_user else 'unique devices'}** (change in sidebar settings)")

# ============================================================================
# Find Optimizations
# ============================================================================

st.subheader("Find Optimizations", help="💡 Identify wasted spend: terminated users with licenses, and active users who aren't using their software")

# Inactive users consuming installs
inactive = installs_users[installs_users["status"] == "terminated"].copy()
st.markdown("**🔴 Inactive users still holding installs (Reclaim Now):**")
st.caption("These users are terminated but still have software installed. You can reclaim these seats immediately for instant savings.")
inactive_display_cols = ["user_email", "software", "device_id", "last_used_date"]
if "department" in inactive.columns:
    inactive_display_cols.append("department")
st.dataframe(inactive[inactive_display_cols], use_container_width=True)
st.caption(f"💰 {len(inactive)} installations to reclaim from terminated users → Remove their licenses to save money")

# Low-usage candidates (no use in last 60 days)
st.markdown("**⚠️ Low-usage installs (no activity in 60+ days):**")
st.caption("These active users haven't used their software in 60+ days. Consider reaching out to confirm they still need it before renewal.")
threshold = today - timedelta(days=60)
low = installs_users[
    ((pd.to_datetime(installs_users["last_used_date"]) < pd.to_datetime(threshold)) |
     (installs_users["last_used_date"].isna())) &
    (installs_users["status"] == "active")  # Only active users (terminated are in reclaim)
].copy()
low_display_cols = ["user_email", "software", "device_id", "last_used_date"]
if "department" in low.columns:
    low_display_cols.append("department")
st.dataframe(low[low_display_cols], use_container_width=True)
st.caption(f"💡 {len(low)} low-usage installations → Contact these users to verify if they still need their licenses")

# ============================================================================
# Export
# ============================================================================

st.subheader("Export", help="📁 Download data as CSV to share with stakeholders, import into Excel, or upload to ServiceNow")

def to_csv(df):
    """Convert dataframe to CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")

col1, col2, col3 = st.columns(3)

with col1:
    st.download_button(
        "📥 Download ELP Report (CSV)",
        data=to_csv(filtered),
        file_name="opensam_elp_report.csv",
        mime="text/csv",
        use_container_width=True,
        help="Full license position data with all fields"
    )

with col2:
    st.download_button(
        "📥 Download Inactive Installs (CSV)",
        data=to_csv(inactive),
        file_name="opensam_inactive_installs.csv",
        mime="text/csv",
        use_container_width=True,
        help="List of terminated users with licenses to reclaim"
    )

with col3:
    st.download_button(
        "📥 Download Low-Usage Installs (CSV)",
        data=to_csv(low),
        file_name="opensam_low_usage.csv",
        mime="text/csv",
        use_container_width=True,
        help="Users with no activity in 60+ days"
    )

st.caption("✅ All CSV exports respect current filter selections")

# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("**OpenSAM Starter Kit** — Powered by **AppForge Labs**")
    st.caption("Customize columns/calculations to mirror your organization's SAM workflows (Flexera, ServiceNow, Microsoft SAM, etc.)")
with col2:
    if st.button("🚀 Upgrade to Pro", use_container_width=True, help="Get custom features, integrations, and hosted deployment"):
        st.info("**AppForge Labs Pro Features:**\n\n✅ Custom integrations (SCCM, Intune, ServiceNow)\n✅ Automated data sync\n✅ Advanced analytics & forecasting\n✅ White-label deployment\n✅ Dedicated support\n\n📧 Contact: paulsemaan007@gmail.com")
