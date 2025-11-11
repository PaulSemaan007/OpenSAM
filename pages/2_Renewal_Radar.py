import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Renewal Radar - OpenSAM", layout="wide")

st.title("Renewal Radar")
st.markdown("Track contract expirations, renewal windows, and proactively manage license renewals.")

# ============================================================================
# Formatting Helpers
# ============================================================================

def fmt_currency(value):
    """Format value as currency."""
    if pd.isna(value):
        return "$0.00"
    return f"${value:,.2f}"

def fmt_date(value):
    """Format date value."""
    if pd.isna(value):
        return ""
    if isinstance(value, str):
        return value
    return pd.to_datetime(value, errors="coerce").strftime("%Y-%m-%d")

# ============================================================================
# Load Data from Session State
# ============================================================================

# Check if data exists in session_state
if "data" not in st.session_state or "data_loaded" not in st.session_state:
    st.warning("⚠️ Data not loaded. Please visit the home page first to load data.")
    st.stop()

# Get data from session state
data = st.session_state["data"]
licenses = data["licenses"]
vendors = data["vendors"]

# Check if data is empty
if licenses.empty:
    st.error("❌ Licenses data is missing or empty. Please check data/ folder.")
    st.stop()

# ============================================================================
# Join Licenses with Vendors
# ============================================================================

# Join on vendor to get renewal_notice_days
if not vendors.empty and "vendor" in vendors.columns and "vendor" in licenses.columns:
    licenses_with_vendors = licenses.merge(vendors, on="vendor", how="left")
else:
    licenses_with_vendors = licenses.copy()
    if "renewal_notice_days" not in licenses_with_vendors.columns:
        licenses_with_vendors["renewal_notice_days"] = np.nan

# Default renewal_notice_days to 30 if missing
licenses_with_vendors["renewal_notice_days"] = licenses_with_vendors["renewal_notice_days"].fillna(30).astype(int)

# ============================================================================
# Calculate Renewal Metrics
# ============================================================================

today = datetime.utcnow().date()

# Days remaining (guard against NaT)
if "contract_end" in licenses_with_vendors.columns:
    licenses_with_vendors["days_remaining"] = licenses_with_vendors["contract_end"].apply(
        lambda x: (x - today).days if pd.notna(x) else 999999
    )
else:
    licenses_with_vendors["days_remaining"] = 999999

# Clamp negative days to 0 for display purposes
licenses_with_vendors["days_remaining_display"] = licenses_with_vendors["days_remaining"].apply(lambda x: max(0, x))

# Expiring within 30 days
licenses_with_vendors["expiring_30d"] = licenses_with_vendors["days_remaining"] <= 30

# Notice start date and in_notice_window
if "contract_end" in licenses_with_vendors.columns:
    licenses_with_vendors["notice_start"] = licenses_with_vendors.apply(
        lambda row: row["contract_end"] - timedelta(days=row["renewal_notice_days"]) if pd.notna(row["contract_end"]) else None,
        axis=1
    )
    licenses_with_vendors["in_notice_window"] = licenses_with_vendors.apply(
        lambda row: (today >= row["notice_start"]) and (row["days_remaining"] > 0) if pd.notna(row["notice_start"]) else False,
        axis=1
    )
else:
    licenses_with_vendors["notice_start"] = None
    licenses_with_vendors["in_notice_window"] = False

# Annual spend proxy
if "seats_purchased" in licenses_with_vendors.columns and "unit_cost_usd" in licenses_with_vendors.columns:
    licenses_with_vendors["annual_spend_proxy"] = licenses_with_vendors["seats_purchased"] * licenses_with_vendors["unit_cost_usd"]
else:
    licenses_with_vendors["annual_spend_proxy"] = 0

# Check if subscription
if "license_type" in licenses_with_vendors.columns:
    licenses_with_vendors["is_subscription"] = licenses_with_vendors["license_type"].str.contains("subscription", case=False, na=False)
else:
    licenses_with_vendors["is_subscription"] = False

# ============================================================================
# Filters
# ============================================================================

st.subheader("Filters")

col1, col2, col3 = st.columns(3)

with col1:
    vendor_filter = st.multiselect(
        "Vendor",
        sorted(licenses_with_vendors["vendor"].dropna().unique().tolist()) if "vendor" in licenses_with_vendors.columns else []
    )

with col2:
    only_subs = st.toggle("Subscriptions only", value=False)

with col3:
    max_days = st.slider(
        "Max days remaining",
        min_value=0,
        max_value=365,
        value=90,
        step=30,
        help="Show only contracts expiring within this many days"
    )

st.caption("💡 **Notice Window**: Period before contract end when renewal action is typically required (vendor-specific).")

# Apply filters
filtered = licenses_with_vendors.copy()

if vendor_filter:
    filtered = filtered[filtered["vendor"].isin(vendor_filter)]

if only_subs:
    filtered = filtered[filtered["is_subscription"] == True]

filtered = filtered[filtered["days_remaining"] <= max_days]

# ============================================================================
# KPIs
# ============================================================================

st.subheader("Key Metrics")

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("Products", len(filtered))

with k2:
    expiring_count = filtered["expiring_30d"].sum()
    st.metric("Expiring in 30d", expiring_count)

with k3:
    notice_count = filtered["in_notice_window"].sum()
    st.metric("In Notice Window", notice_count)

with k4:
    # Total Annual Spend Proxy (subscriptions only)
    total_spend = filtered[filtered["is_subscription"] == True]["annual_spend_proxy"].sum()
    st.metric("Total Annual Spend (Subs)", fmt_currency(total_spend))

st.caption("📊 **Total Annual Spend** includes subscription licenses only (perpetual licenses excluded).")

# ============================================================================
# Renewal Table
# ============================================================================

st.subheader("Renewal Schedule")

# Sort by days_remaining ascending
filtered_sorted = filtered.sort_values("days_remaining", ascending=True)

# Select display columns
display_cols = [
    "software", "vendor", "license_type", "seats_purchased", "unit_cost_usd",
    "contract_end", "days_remaining_display", "renewal_notice_days",
    "in_notice_window", "expiring_30d", "annual_spend_proxy"
]

# Create display dataframe
display_df = filtered_sorted[[col for col in display_cols if col in filtered_sorted.columns]].copy()

# Format currency and date columns
if "unit_cost_usd" in display_df.columns:
    display_df["unit_cost_usd_fmt"] = display_df["unit_cost_usd"].apply(fmt_currency)
if "annual_spend_proxy" in display_df.columns:
    display_df["annual_spend_proxy_fmt"] = display_df["annual_spend_proxy"].apply(fmt_currency)
if "contract_end" in display_df.columns:
    display_df["contract_end_fmt"] = display_df["contract_end"].apply(fmt_date)

# Add alert indicators
display_df["alert"] = display_df.apply(
    lambda row: "🔴" if row.get("expiring_30d", False) else ("🟡" if row.get("in_notice_window", False) else ""),
    axis=1
)

# Create final display
final_cols = ["alert", "software", "vendor", "license_type", "seats_purchased"]
if "unit_cost_usd_fmt" in display_df.columns:
    final_cols.append("unit_cost_usd_fmt")
if "contract_end_fmt" in display_df.columns:
    final_cols.append("contract_end_fmt")
final_cols.extend(["days_remaining_display", "renewal_notice_days", "in_notice_window", "expiring_30d"])
if "annual_spend_proxy_fmt" in display_df.columns:
    final_cols.append("annual_spend_proxy_fmt")

# Filter to columns that exist
final_cols = [col for col in final_cols if col in display_df.columns]

final_display = display_df[final_cols].rename(columns={
    "alert": "🚨",
    "unit_cost_usd_fmt": "unit_cost_usd",
    "annual_spend_proxy_fmt": "annual_spend_proxy",
    "contract_end_fmt": "contract_end",
    "days_remaining_display": "days_remaining"
})

st.dataframe(final_display, use_container_width=True)

st.caption("🔴 Expiring in 30 days | 🟡 In vendor notice window")

# ============================================================================
# Export Options
# ============================================================================

st.subheader("Export & Alerts")

def to_csv(df):
    """Convert dataframe to CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")

col1, col2, col3 = st.columns(3)

# Standard CSV Export
with col1:
    st.download_button(
        label="📥 Download Renewal Schedule (CSV)",
        data=to_csv(filtered_sorted),
        file_name="opensam_renewal_schedule.csv",
        mime="text/csv",
        use_container_width=True
    )

# ServiceNow Export Format
with col2:
    # ServiceNow mapping dictionary
    SNOW_MAPPING = {
        "name": "software",
        "manufacturer": "vendor",
        "license_metric": "license_type",
        "cost": "unit_cost_usd",
        "quantity": "seats_purchased",
        "expiration_date": "contract_end"
    }

    # Create ServiceNow formatted export
    snow_export = filtered_sorted.copy()
    snow_df = pd.DataFrame()

    for snow_col, local_col in SNOW_MAPPING.items():
        if local_col in snow_export.columns:
            snow_df[snow_col] = snow_export[local_col]

    # Add additional ServiceNow fields
    if "days_remaining" in snow_export.columns:
        snow_df["days_until_expiration"] = snow_export["days_remaining"]
    if "expiring_30d" in snow_export.columns:
        snow_df["requires_action"] = snow_export["expiring_30d"]

    st.download_button(
        label="📥 ServiceNow Format (CSV)",
        data=to_csv(snow_df),
        file_name="opensam_servicenow_export.csv",
        mime="text/csv",
        use_container_width=True,
        help="Export in ServiceNow CMDB format"
    )

    st.caption("ℹ️ **ServiceNow mapping**: Adjust for your instance schema (cmdb_ci, alm_license, software_model). See README for details.")

# Renewal Alerts Generator
with col3:
    if st.button("📧 Generate Alert Email", use_container_width=True):
        # Filter to expiring items
        expiring = filtered_sorted[filtered_sorted["expiring_30d"] == True]

        if expiring.empty:
            st.info("✅ No products expiring in 30 days!")
        else:
            # Build email text
            alert_text = f"RENEWAL ALERT: {len(expiring)} product(s) expiring in 30 days\n\n"

            for idx, row in expiring.iterrows():
                software = row.get("software", "Unknown")
                vendor = row.get("vendor", "Unknown")
                contract_end = fmt_date(row.get("contract_end"))
                seats = row.get("seats_purchased", 0)
                cost = fmt_currency(row.get("annual_spend_proxy", 0))
                days = row.get("days_remaining", 0)

                alert_text += f"• {software} | {vendor} | Expires: {contract_end} ({days} days) | Seats: {seats} | Annual Cost: {cost}\n"

            total_spend = expiring[expiring["is_subscription"] == True]["annual_spend_proxy"].sum()
            alert_text += f"\nTotal renewal spend (subscriptions): {fmt_currency(total_spend)}\n"
            alert_text += "\nAction Required: Contact vendors to initiate renewal process.\n"

            st.code(alert_text, language=None)
            st.caption("📋 Copy the text above for email/Slack alerts")

# ============================================================================
# ServiceNow Mapping Info
# ============================================================================

with st.expander("ℹ️ ServiceNow Integration Details"):
    st.markdown("""
### ServiceNow Export Mapping

**Default field mapping:**
- `name` ← software
- `manufacturer` ← vendor
- `license_metric` ← license_type
- `cost` ← unit_cost_usd
- `quantity` ← seats_purchased
- `expiration_date` ← contract_end

**Important Notes:**
- CMDB/Software Model fields vary by ServiceNow implementation
- Common tables: `cmdb_ci`, `alm_license`, `software_model`
- Adjust mapping in code to match your instance schema
- Consult your ServiceNow admin for exact field names

**Customization:**
The mapping dictionary at the top of this file can be easily modified:
```python
SNOW_MAPPING = {
    "your_field": "our_column",
    ...
}
```
    """)

# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("**OpenSAM Renewal Radar** — Powered by **AppForge Labs**")
    st.caption("💡 Set vendor-specific renewal windows. Contact vendors early to negotiate better terms and avoid auto-renewals.")
with col2:
    if st.button("🚀 Automate Alerts", use_container_width=True, key="upgrade_renewal"):
        st.info("**AppForge Labs Renewal Automation:**\n\n✅ Email/Slack alerts\n✅ Vendor negotiation tracking\n✅ Historical pricing analysis\n✅ Auto-renewal prevention\n\n📧 Contact: paulsemaan007@gmail.com")
