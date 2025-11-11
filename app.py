import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="OpenSAM", layout="wide")

st.title("OpenSAM — Software Asset Management (Starter)")

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
    vendor_filter = st.multiselect("Vendor", sorted(sam["vendor"].dropna().unique().tolist()) if "vendor" in sam.columns else [])
with cols[1]:
    risk_filter = st.selectbox("Risk", ["All", "Over-Used", "Expiring < 30d", "Inactive Users Present"])
with cols[2]:
    min_savings = st.number_input("Min Potential Savings ($)", value=0, min_value=0, step=50)
with cols[3]:
    only_subs = st.toggle("Subscriptions only", value=False)

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
# Portfolio Overview Metrics
# ============================================================================

st.subheader("Portfolio Overview")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Vendors", filtered["vendor"].nunique() if "vendor" in filtered.columns else 0)
k2.metric("Products", filtered["software"].nunique() if "software" in filtered.columns else 0)
k3.metric("Total Seats", int(filtered["seats_purchased"].sum()) if "seats_purchased" in filtered.columns else 0)
k4.metric("Potential Savings", fmt_currency(filtered["potential_savings_usd"].sum()))

st.caption("💡 **Potential Savings** counts subscription licenses only (perpetual licenses excluded). Perpetual licenses may still incur maintenance/support costs; savings shown exclude those.")

# ============================================================================
# ELP Table with Overage Badges
# ============================================================================

st.subheader("Effective License Position & Risks")

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

st.subheader("Find Optimizations")

# Inactive users consuming installs
inactive = installs_users[installs_users["status"] == "terminated"].copy()
st.markdown("**🔴 Inactive users still holding installs (Reclaim Now):**")
inactive_display_cols = ["user_email", "software", "device_id", "last_used_date"]
if "department" in inactive.columns:
    inactive_display_cols.append("department")
st.dataframe(inactive[inactive_display_cols], use_container_width=True)
st.caption(f"💰 {len(inactive)} installations to reclaim from terminated users")

# Low-usage candidates (no use in last 60 days)
st.markdown("**⚠️ Low-usage installs (no activity in 60+ days):**")
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
st.caption(f"💡 {len(low)} low-usage installations (60+ days without activity)")

# ============================================================================
# Export
# ============================================================================

st.subheader("Export")

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
        use_container_width=True
    )

with col2:
    st.download_button(
        "📥 Download Inactive Installs (CSV)",
        data=to_csv(inactive),
        file_name="opensam_inactive_installs.csv",
        mime="text/csv",
        use_container_width=True
    )

with col3:
    st.download_button(
        "📥 Download Low-Usage Installs (CSV)",
        data=to_csv(low),
        file_name="opensam_low_usage.csv",
        mime="text/csv",
        use_container_width=True
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
