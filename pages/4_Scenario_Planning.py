import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Scenario Planning - OpenSAM", layout="wide")

st.title("Scenario Planning")
st.markdown("Model seat reduction scenarios and generate removal recommendations based on usage patterns.")

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
installs = data["installs"]
users = data["users"]

# Check if data is empty
if licenses.empty or installs.empty or users.empty:
    st.error("❌ Required data files are missing or empty. Please check data/ folder.")
    st.stop()

# Get seat counting mode from session state
count_by_user = st.session_state.get("count_by_user", False)

# ============================================================================
# Data Processing
# ============================================================================

# Join installs → users to get status and department
installs_users = installs.merge(users, on="user_email", how="left")

# Fill missing status
if "status" in installs_users.columns:
    installs_users["status"] = installs_users["status"].fillna("unknown")

# ============================================================================
# Product Selection
# ============================================================================

st.subheader("Select Product")

# Get unique products from licenses
if "software" in licenses.columns:
    products = sorted(licenses["software"].dropna().unique().tolist())
else:
    st.error("❌ Column 'software' not found in licenses.csv")
    st.stop()

if not products:
    st.warning("⚠️ No products found in licenses.csv")
    st.stop()

selected_product = st.selectbox("Product", products, key="scenario_product")

# ============================================================================
# Filter Data for Selected Product
# ============================================================================

# Get license info
license_row = licenses[licenses["software"] == selected_product]

if license_row.empty:
    st.warning(f"⚠️ No license information found for {selected_product}")
    st.stop()

license_info = license_row.iloc[0]

# Get product installations
product_installs = installs_users[installs_users["software"] == selected_product].copy()

# Get license details
seats_purchased = int(license_info.get("seats_purchased", 0))
unit_cost = license_info.get("unit_cost_usd", 0)
if pd.isna(unit_cost):
    unit_cost = 0

license_type = license_info.get("license_type", "unknown")
is_subscription = "subscription" in str(license_type).lower()

# ============================================================================
# Current State
# ============================================================================

st.subheader("Current State")

# Calculate current usage
if count_by_user:
    active_count = product_installs[product_installs["status"] == "active"]["user_email"].nunique()
    terminated_count = product_installs[product_installs["status"] == "terminated"]["user_email"].nunique()
else:
    active_count = len(product_installs[product_installs["status"] == "active"])
    terminated_count = len(product_installs[product_installs["status"] == "terminated"])

total_in_use = active_count + terminated_count
unused_seats = max(0, seats_purchased - active_count)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Seats Purchased", seats_purchased)
with col2:
    st.metric("Active Users", active_count)
with col3:
    st.metric("Terminated Users", terminated_count)
with col4:
    st.metric("Unused Seats", unused_seats)

st.caption(f"💡 **License Type:** {license_type} | **Unit Cost:** {fmt_currency(unit_cost)}")
st.caption(f"📊 Counted by: **{'unique users' if count_by_user else 'unique devices'}**")

# ============================================================================
# Scenario Configuration
# ============================================================================

st.subheader("Configure Scenario")

col1, col2 = st.columns(2)

with col1:
    reduce_seats = st.slider(
        "Reduce N seats",
        min_value=0,
        max_value=seats_purchased,
        value=min(unused_seats, seats_purchased),
        step=1,
        help="Number of seats to reduce from current allocation"
    )

with col2:
    exclude_terminated = st.checkbox(
        "Exclude terminated users (recommended)",
        value=True,
        help="When ON: Generate removal list from active users only. Terminated users should be handled via reclaim process."
    )

# Calculate projected savings
if is_subscription:
    projected_savings = reduce_seats * unit_cost
    savings_note = f"Projected Annual Savings: {fmt_currency(projected_savings)}"
else:
    projected_savings = 0
    savings_note = f"Perpetual license (no recurring savings, but may reduce maintenance/support costs)"

st.info(f"💰 {savings_note}")

# ============================================================================
# Generate Recommendation List
# ============================================================================

st.subheader("Removal Recommendations")

# Filter users based on exclude_terminated setting
if exclude_terminated:
    candidate_users = product_installs[product_installs["status"] == "active"].copy()
    st.caption("🔍 Showing **active users only** (terminated users excluded). Handle terminated users via Reclaim process.")
else:
    candidate_users = product_installs.copy()
    st.caption("🔍 Showing **all users** (including terminated). Consider reviewing reclaim process first.")

# Convert last_used_date to datetime for sorting
if "last_used_date" in candidate_users.columns:
    candidate_users["last_used_datetime"] = pd.to_datetime(candidate_users["last_used_date"], errors="coerce")

    # Sort by last_used_date ascending (oldest first), NaT values last
    candidate_users = candidate_users.sort_values("last_used_datetime", ascending=True, na_position="last")
else:
    st.warning("⚠️ last_used_date column not found. Cannot generate usage-based recommendations.")
    candidate_users["last_used_datetime"] = pd.NaT

# If counting by user, dedupe to show one row per user (keep oldest last_used_date)
if count_by_user and "user_email" in candidate_users.columns:
    # Group by user and keep row with oldest last_used_date
    candidate_users = candidate_users.sort_values("last_used_datetime", ascending=True).groupby("user_email").first().reset_index()

# Take top N recommendations
recommendation_list = candidate_users.head(reduce_seats)

# Display recommendations
st.markdown(f"**Top {reduce_seats} users recommended for removal (sorted by least recent use):**")

display_cols = ["user_email", "device_id", "last_used_date", "status"]
if "department" in recommendation_list.columns:
    display_cols.append("department")

display_recommendation = recommendation_list[[col for col in display_cols if col in recommendation_list.columns]].copy()

# Format dates
if "last_used_date" in display_recommendation.columns:
    display_recommendation["last_used_date"] = display_recommendation["last_used_date"].apply(fmt_date)

st.dataframe(display_recommendation, use_container_width=True)

st.caption("💡 **Recommendation prioritizes least-recently-used active users.** Review with department heads before taking action. Users with no usage history appear at the bottom.")

# ============================================================================
# Impact Summary
# ============================================================================

st.subheader("Scenario Impact")

col1, col2, col3 = st.columns(3)

with col1:
    new_seat_count = seats_purchased - reduce_seats
    st.metric("New Seat Count", new_seat_count, delta=f"-{reduce_seats}")

with col2:
    remaining_users = active_count - min(reduce_seats, active_count)
    st.metric("Remaining Active Users", remaining_users)

with col3:
    if is_subscription:
        st.metric("Annual Savings", fmt_currency(projected_savings))
    else:
        st.metric("Savings", "$0 (Perpetual)")

# Warning if overage would result
if remaining_users > new_seat_count:
    overage = remaining_users - new_seat_count
    st.warning(f"⚠️ **Warning:** Reducing by {reduce_seats} seats would create an overage of {overage} seats. Consider reducing more or reassigning users.")
else:
    st.success(f"✅ After reduction, you would have {new_seat_count - remaining_users} unused seats remaining.")

# ============================================================================
# Export
# ============================================================================

st.subheader("Export Recommendations")

def to_csv(df):
    """Convert dataframe to CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")

col1, col2 = st.columns(2)

with col1:
    # Export full recommendation list
    if not recommendation_list.empty:
        export_cols = ["user_email", "device_id", "software", "last_used_date", "status"]
        if "department" in recommendation_list.columns:
            export_cols.append("department")

        export_df = recommendation_list[[col for col in export_cols if col in recommendation_list.columns]].copy()

        st.download_button(
            label="📥 Download Removal Recommendation List (CSV)",
            data=to_csv(export_df),
            file_name=f"{selected_product}_removal_recommendations.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No recommendations to export (reduce_seats = 0)")

with col2:
    # Export scenario summary
    scenario_summary = pd.DataFrame({
        "Product": [selected_product],
        "License Type": [license_type],
        "Current Seats": [seats_purchased],
        "Reduction": [reduce_seats],
        "New Seats": [seats_purchased - reduce_seats],
        "Active Users": [active_count],
        "Projected Savings": [fmt_currency(projected_savings)],
        "Exclude Terminated": [exclude_terminated],
        "Date Generated": [datetime.utcnow().strftime("%Y-%m-%d")]
    })

    st.download_button(
        label="📥 Download Scenario Summary (CSV)",
        data=to_csv(scenario_summary),
        file_name=f"{selected_product}_scenario_summary.csv",
        mime="text/csv",
        use_container_width=True
    )

# ============================================================================
# Additional Guidance
# ============================================================================

with st.expander("📋 Implementation Guidance"):
    st.markdown("""
### How to Use This Scenario

1. **Review Recommendations**: Check the list of users recommended for removal. Verify with department heads that these users no longer need access.

2. **Handle Terminated Users First**: If you haven't already, reclaim licenses from terminated users (see Product Drilldown page).

3. **Communicate with Stakeholders**: Before reducing seats, ensure affected users are aware and have alternative solutions if needed.

4. **Adjust License Count**: Contact your vendor to reduce seat count for the next renewal period.

5. **Monitor Impact**: After implementation, track usage to ensure remaining users have adequate licenses.

### Best Practices

- **Start Small**: Test with a modest reduction first to gauge impact
- **Review Quarterly**: Usage patterns change; re-run scenarios regularly
- **Document Decisions**: Keep records of why specific users were selected
- **Backup Plan**: Have a process to quickly add seats if business needs change

### Risk Mitigation

- Users with no last_used_date may still need access (e.g., new hires, seasonal workers)
- Consider upcoming projects that might require additional licenses
- Ensure critical business functions aren't impacted by reductions
    """)

# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("**OpenSAM Scenario Planning** — Powered by **AppForge Labs**")
    st.caption("💡 Run scenarios 60+ days before renewal to allow time for stakeholder review and vendor negotiations.")
with col2:
    if st.button("🚀 Predictive Planning", use_container_width=True, key="upgrade_scenario"):
        st.info("**AppForge Labs Scenario Tools:**\n\n✅ AI-powered usage forecasting\n✅ What-if analysis with multiple variables\n✅ ROI calculators\n✅ Automated stakeholder reports\n\n📧 Contact: paulsemaan007@gmail.com")
