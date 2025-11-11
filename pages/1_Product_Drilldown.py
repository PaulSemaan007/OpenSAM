import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Product Drilldown - OpenSAM", layout="wide")

st.title("Product Drilldown")
st.markdown("Deep dive into license utilization, active installs, and reclaim opportunities for a specific product.")

# ============================================================================
# Formatting Helpers (Same as app.py)
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
installs = data["installs"]
users = data["users"]

# Check if data is empty
if licenses.empty or installs.empty or users.empty:
    st.error("❌ Required data files are missing or empty. Please check data/ folder.")
    st.stop()

# Get seat counting mode from session state (set in main app)
count_by_user = st.session_state.get("count_by_user", False)

# ============================================================================
# Data Processing
# ============================================================================

# Join installs → users to get user status and department
installs_users = installs.merge(users, on="user_email", how="left")

# Fill missing status with "unknown"
if "status" in installs_users.columns:
    installs_users["status"] = installs_users["status"].fillna("unknown")

# ============================================================================
# Product Selection
# ============================================================================

# Get unique products from licenses
if "software" in licenses.columns:
    products = sorted(licenses["software"].dropna().unique().tolist())
else:
    st.error("❌ Column 'software' not found in licenses.csv")
    st.stop()

if not products:
    st.warning("⚠️ No products found in licenses.csv")
    st.stop()

selected_product = st.selectbox("Select Product", products, key="product_selector")

# ============================================================================
# Filter Data for Selected Product
# ============================================================================

# Filter licenses for selected product
license_row = licenses[licenses["software"] == selected_product]

if license_row.empty:
    st.warning(f"⚠️ No license information found for {selected_product}")
    st.stop()

# Get first row (in case of duplicates)
license_info = license_row.iloc[0]

# Filter installations for selected product
product_installs = installs_users[installs_users["software"] == selected_product].copy()

# ============================================================================
# Calculate Metrics
# ============================================================================

today = datetime.utcnow().date()

# Seats Purchased
seats_purchased = int(license_info.get("seats_purchased", 0))

# License type
license_type = license_info.get("license_type", "unknown")
is_subscription = "subscription" in str(license_type).lower()

# Active Installs (used seats) - respects count_by_user toggle
if count_by_user:
    # Count unique users with status="active"
    active_installs_df = product_installs[product_installs.get("status") == "active"]
    active_installs_count = active_installs_df["user_email"].nunique() if "user_email" in active_installs_df.columns else 0
else:
    # Count unique devices with status="active"
    active_installs_df = product_installs[product_installs.get("status") == "active"]
    active_installs_count = active_installs_df["device_id"].nunique() if "device_id" in active_installs_df.columns else 0

# Unused Seats
unused_seats = max(0, seats_purchased - active_installs_count)

# Overage
overage = max(0, active_installs_count - seats_purchased)

# Potential Savings (SUBSCRIPTION ONLY)
unit_cost = license_info.get("unit_cost_usd", 0)
if pd.isna(unit_cost):
    unit_cost = 0

if is_subscription:
    potential_savings = unused_seats * unit_cost
else:
    potential_savings = 0

# ============================================================================
# Display Metrics
# ============================================================================

st.subheader(f"📊 Metrics: {selected_product}")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Seats Purchased", seats_purchased)
with col2:
    st.metric("Active Installs", active_installs_count)
with col3:
    st.metric("Unused Seats", unused_seats)
with col4:
    delta_label = "⚠️ Risk" if overage > 0 else None
    st.metric("Overage", overage, delta=delta_label)
with col5:
    st.metric("Potential Savings", fmt_currency(potential_savings))

st.caption(f"💡 **License Type:** {license_type} | **Savings apply to subscriptions only.** Perpetual licenses may still incur maintenance/support costs; savings shown exclude those.")
st.caption(f"📊 Active seats counted by: **{'unique users' if count_by_user else 'unique devices'}** (change in home page sidebar)")

# Show license details
with st.expander("📋 License Details"):
    details_cols = ["vendor", "license_type", "unit_cost_usd", "contract_start", "contract_end", "license_key"]
    details_data = {}
    for col in details_cols:
        if col in license_info.index:
            val = license_info[col]
            if col == "unit_cost_usd":
                details_data[col] = fmt_currency(val)
            elif col in ["contract_start", "contract_end"]:
                details_data[col] = fmt_date(val)
            else:
                details_data[col] = val
    if details_data:
        for key, value in details_data.items():
            st.text(f"{key}: {value}")

# ============================================================================
# Prepare Tables
# ============================================================================

threshold_60_days = today - timedelta(days=60)

# Define display columns
base_display_cols = ["user_email", "device_id", "last_used_date"]
if "department" in product_installs.columns:
    base_display_cols.append("department")

# Table 1: Active Installs
active_installs_table = active_installs_df[base_display_cols].copy() if not active_installs_df.empty else pd.DataFrame(columns=base_display_cols)

# Table 2: Terminated Users (Reclaim Now)
terminated_users_df = product_installs[product_installs.get("status") == "terminated"].copy()
terminated_users_table = terminated_users_df[base_display_cols].copy() if not terminated_users_df.empty else pd.DataFrame(columns=base_display_cols)

# Calculate immediate savings (subscription only)
if is_subscription:
    if count_by_user:
        terminated_count = terminated_users_df["user_email"].nunique() if not terminated_users_df.empty else 0
    else:
        terminated_count = len(terminated_users_df)
    immediate_savings = terminated_count * unit_cost
else:
    immediate_savings = 0
    terminated_count = 0

# Table 3: Low-Usage (No activity 60+ days) - ACTIVE USERS ONLY
if "last_used_date" in product_installs.columns:
    product_installs["last_used_datetime"] = pd.to_datetime(product_installs["last_used_date"], errors="coerce")

    low_usage_df = product_installs[
        (
            (product_installs["last_used_datetime"].isna()) |
            (product_installs["last_used_datetime"] < pd.to_datetime(threshold_60_days))
        ) &
        (product_installs.get("status") == "active")  # Only active users
    ].copy()

    low_usage_table = low_usage_df[base_display_cols].copy() if not low_usage_df.empty else pd.DataFrame(columns=base_display_cols)

    # Calculate low-usage savings (subscription only)
    if is_subscription:
        if count_by_user:
            low_usage_count = low_usage_df["user_email"].nunique() if not low_usage_df.empty else 0
        else:
            low_usage_count = len(low_usage_df)
        low_usage_savings = low_usage_count * unit_cost
    else:
        low_usage_savings = 0
else:
    low_usage_table = pd.DataFrame(columns=base_display_cols)
    low_usage_savings = 0

# ============================================================================
# Display Tables
# ============================================================================

st.markdown("---")

# Table 1: Active Installs
st.subheader("✅ Active Installs")
st.markdown(f"*{len(active_installs_table)} active installations*")
st.dataframe(active_installs_table, use_container_width=True)

# CSV Download for Active Installs
def to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📥 Download Active Installs CSV",
    data=to_csv(active_installs_table),
    file_name=f"{selected_product}_active_installs.csv",
    mime="text/csv",
    key="download_active"
)

st.markdown("---")

# Table 2: Terminated Users (Reclaim Now)
st.subheader("🔴 Terminated Users (Reclaim Now)")
st.markdown(f"*{len(terminated_users_table)} installations to reclaim*")
if not terminated_users_table.empty and immediate_savings > 0:
    st.info(f"💰 **Immediate Savings:** {fmt_currency(immediate_savings)} ({license_type})")
elif not terminated_users_table.empty and not is_subscription:
    st.info(f"ℹ️ {terminated_count} installations from terminated users. Perpetual license (savings = $0, but may reduce maintenance costs).")

st.dataframe(terminated_users_table, use_container_width=True)

st.download_button(
    label="📥 Download Terminated Users CSV",
    data=to_csv(terminated_users_table),
    file_name=f"{selected_product}_terminated_users.csv",
    mime="text/csv",
    key="download_terminated"
)

st.markdown("---")

# Table 3: Low-Usage (No activity 60+ days)
st.subheader("⚠️ Low-Usage (No activity 60+ days)")
st.markdown(f"*{len(low_usage_table)} low-usage installations (active users only)*")
if not low_usage_table.empty and low_usage_savings > 0:
    st.warning(f"💡 **Potential Savings from Optimization:** {fmt_currency(low_usage_savings)} ({license_type})")
elif not low_usage_table.empty and not is_subscription:
    st.info(f"ℹ️ {len(low_usage_table)} low-usage installations. Perpetual license (savings = $0, but may reduce support needs).")

st.dataframe(low_usage_table, use_container_width=True)

st.download_button(
    label="📥 Download Low-Usage CSV",
    data=to_csv(low_usage_table),
    file_name=f"{selected_product}_low_usage.csv",
    mime="text/csv",
    key="download_low_usage"
)

# ============================================================================
# Summary
# ============================================================================

st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("**OpenSAM Product Drilldown** — Powered by **AppForge Labs**")
    st.caption("💡 Review terminated users for immediate reclamation. Engage with low-usage users to assess ongoing need.")
with col2:
    if st.button("🚀 Get Custom Reports", use_container_width=True, key="upgrade_drilldown"):
        st.info("**Need advanced product analytics?**\n\n✅ Usage trend analysis\n✅ Predictive recommendations\n✅ Automated reclaim workflows\n\n📧 Contact: paulsemaan007@gmail.com")
