import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Department Allocation - OpenSAM", layout="wide")

st.title("Department Allocation")
st.markdown("Analyze software license costs and utilization by department. Identify reclaim opportunities and cost allocation.")

# How to Use This Page
with st.expander("🎯 How to Use This Page (Click to Expand)"):
    col_guide1, col_guide2 = st.columns(2)
    with col_guide1:
        st.markdown("**🔍 What You're Seeing:**")
        st.markdown("- **Cost breakdown** by department (chargeback model)")
        st.markdown("- **Reclaimable savings** from terminated users per department")
        st.markdown("- **Share of total spend** for each department")
        st.markdown("- **Software usage** details for selected department")
    with col_guide2:
        st.markdown("**✅ What To Do:**")
        st.markdown("1. Review **department breakdown** table to see cost distribution")
        st.markdown("2. Identify departments with high **reclaimable savings**")
        st.markdown("3. Select a department to see **detailed software usage**")
        st.markdown("4. Download **CSV exports** for budget allocation meetings")
        st.markdown("5. Engage department heads to review licenses and reclaim unused seats")

st.markdown("---")

# ============================================================================
# Formatting Helpers
# ============================================================================

def fmt_currency(value):
    """Format value as currency."""
    if pd.isna(value):
        return "$0.00"
    return f"${value:,.2f}"

def fmt_percent(value):
    """Format value as percentage."""
    if pd.isna(value):
        return "0.0%"
    return f"{value:.1f}%"

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

# Check if department column exists
if "department" not in users.columns:
    st.error("❌ Column 'department' not found in users.csv. This page requires department information.")
    st.stop()

# ============================================================================
# Data Processing
# ============================================================================

# Join installs → users to get department and status
installs_users = installs.merge(users, on="user_email", how="left")

# Fill missing values
if "status" in installs_users.columns:
    installs_users["status"] = installs_users["status"].fillna("unknown")
if "department" in installs_users.columns:
    installs_users["department"] = installs_users["department"].fillna("Unknown")

# Join with licenses to get unit costs and license type
installs_users_licenses = installs_users.merge(
    licenses[["software", "unit_cost_usd", "license_type"]],
    on="software",
    how="left"
)

# Fill missing costs
installs_users_licenses["unit_cost_usd"] = installs_users_licenses["unit_cost_usd"].fillna(0)

# Check if subscription
installs_users_licenses["is_subscription"] = installs_users_licenses["license_type"].str.contains("subscription", case=False, na=False)

# ============================================================================
# Calculate Department Metrics
# ============================================================================

# Group by department
if count_by_user:
    # Count unique users per department
    dept_stats = installs_users_licenses.groupby("department").agg(
        used_seats=("user_email", lambda x: installs_users_licenses.loc[x.index][installs_users_licenses.loc[x.index, "status"] == "active"]["user_email"].nunique()),
        terminated_seats=("user_email", lambda x: installs_users_licenses.loc[x.index][installs_users_licenses.loc[x.index, "status"] == "terminated"]["user_email"].nunique()),
        total_installs=("user_email", "nunique")
    ).reset_index()
else:
    # Count devices per department
    dept_stats = installs_users_licenses.groupby("department").agg(
        used_seats=("status", lambda s: (s == "active").sum()),
        terminated_seats=("status", lambda s: (s == "terminated").sum()),
        total_installs=("device_id", "count")
    ).reset_index()

# Calculate reclaimable savings (subscription licenses only)
# For each department, calculate cost of terminated seats
reclaimable_by_dept = []

for dept in dept_stats["department"]:
    dept_terminated = installs_users_licenses[
        (installs_users_licenses["department"] == dept) &
        (installs_users_licenses["status"] == "terminated") &
        (installs_users_licenses["is_subscription"] == True)
    ]

    if count_by_user:
        # Count unique users, then multiply by unit cost
        # For simplicity, we'll use average unit cost per user
        if not dept_terminated.empty:
            # Group by user to avoid double-counting multi-device users
            user_costs = dept_terminated.groupby("user_email")["unit_cost_usd"].first()
            reclaimable_savings = user_costs.sum()
        else:
            reclaimable_savings = 0
    else:
        # Count each install
        reclaimable_savings = dept_terminated["unit_cost_usd"].sum()

    reclaimable_by_dept.append(reclaimable_savings)

dept_stats["reclaimable_savings"] = reclaimable_by_dept

# Calculate share of total spend (proportional allocation)
# Allocate costs based on used_seats
total_used_seats = dept_stats["used_seats"].sum()

if total_used_seats > 0:
    # Calculate total portfolio cost (subscription licenses only)
    total_portfolio_cost = licenses[
        licenses["license_type"].str.contains("subscription", case=False, na=False)
    ]["unit_cost_usd"].sum() * licenses[
        licenses["license_type"].str.contains("subscription", case=False, na=False)
    ]["seats_purchased"].sum()

    # Allocate proportionally
    dept_stats["share_of_spend"] = (dept_stats["used_seats"] / total_used_seats) * total_portfolio_cost
    dept_stats["share_percent"] = (dept_stats["used_seats"] / total_used_seats) * 100
else:
    dept_stats["share_of_spend"] = 0
    dept_stats["share_percent"] = 0

# Sort by share_of_spend descending
dept_stats = dept_stats.sort_values("share_of_spend", ascending=False)

# ============================================================================
# Display Metrics
# ============================================================================

st.subheader("Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Departments", len(dept_stats))

with col2:
    st.metric("Total Used Seats", int(dept_stats["used_seats"].sum()))

with col3:
    st.metric("Reclaimable Seats", int(dept_stats["terminated_seats"].sum()))

with col4:
    st.metric("Total Reclaimable Savings", fmt_currency(dept_stats["reclaimable_savings"].sum()))

st.caption(f"📊 Seats counted by: **{'unique users' if count_by_user else 'unique devices'}** | **Reclaimable savings** apply to subscription licenses only.")

# ============================================================================
# Department Table
# ============================================================================

st.subheader("Department Breakdown")

# Format display table
display_df = dept_stats.copy()
display_df["used_seats_fmt"] = display_df["used_seats"].astype(int)
display_df["terminated_seats_fmt"] = display_df["terminated_seats"].astype(int)
display_df["reclaimable_savings_fmt"] = display_df["reclaimable_savings"].apply(fmt_currency)
display_df["share_of_spend_fmt"] = display_df["share_of_spend"].apply(fmt_currency)
display_df["share_percent_fmt"] = display_df["share_percent"].apply(fmt_percent)

final_display = display_df[[
    "department", "used_seats_fmt", "terminated_seats_fmt",
    "reclaimable_savings_fmt", "share_of_spend_fmt", "share_percent_fmt"
]].rename(columns={
    "used_seats_fmt": "used_seats",
    "terminated_seats_fmt": "terminated_seats",
    "reclaimable_savings_fmt": "reclaimable_savings",
    "share_of_spend_fmt": "share_of_spend",
    "share_percent_fmt": "share_%"
})

st.dataframe(final_display, use_container_width=True)

st.caption("💡 **Share of Spend**: Proportional allocation based on active seat usage across subscription licenses.")

# ============================================================================
# Visualizations
# ============================================================================

st.subheader("Cost Distribution")

# Create bar chart data
chart_data = dept_stats[["department", "share_of_spend"]].set_index("department")
st.bar_chart(chart_data)

# ============================================================================
# Detailed Drilldown
# ============================================================================

st.subheader("Department Detail View")

selected_dept = st.selectbox(
    "Select Department",
    sorted(dept_stats["department"].unique().tolist())
)

if selected_dept:
    # Filter installs for selected department
    dept_installs = installs_users_licenses[installs_users_licenses["department"] == selected_dept]

    # Show software breakdown for this department
    software_breakdown = dept_installs.groupby(["software", "status"]).agg(
        count=("device_id", "count" if not count_by_user else "nunique")
    ).reset_index()

    software_pivot = software_breakdown.pivot(index="software", columns="status", values="count").fillna(0)

    st.markdown(f"**Software Usage by {selected_dept}:**")
    st.dataframe(software_pivot, use_container_width=True)

    # Show terminated users from this department
    dept_terminated = dept_installs[dept_installs["status"] == "terminated"]

    if not dept_terminated.empty:
        st.markdown(f"**Terminated Users in {selected_dept} (Reclaim Opportunities):**")
        reclaim_cols = ["user_email", "software", "device_id", "last_used_date"]
        reclaim_display = dept_terminated[[col for col in reclaim_cols if col in dept_terminated.columns]]
        st.dataframe(reclaim_display, use_container_width=True)

        # Calculate savings for this department
        dept_savings = dept_stats[dept_stats["department"] == selected_dept]["reclaimable_savings"].iloc[0]
        st.info(f"💰 Reclaimable savings for {selected_dept}: {fmt_currency(dept_savings)}")

# ============================================================================
# Export
# ============================================================================

st.subheader("Export")

def to_csv(df):
    """Convert dataframe to CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="📥 Download Department Summary (CSV)",
        data=to_csv(dept_stats),
        file_name="opensam_department_allocation.csv",
        mime="text/csv",
        use_container_width=True
    )

with col2:
    if selected_dept:
        dept_installs_export = dept_installs[["user_email", "software", "device_id", "status", "last_used_date", "unit_cost_usd"]]
        st.download_button(
            label=f"📥 Download {selected_dept} Details (CSV)",
            data=to_csv(dept_installs_export),
            file_name=f"opensam_{selected_dept}_details.csv",
            mime="text/csv",
            use_container_width=True
        )

# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("**OpenSAM Department Allocation** — Powered by **AppForge Labs**")
    st.caption("💡 Use this view for chargeback models or budget allocation. Engage department heads to review licenses and usage.")
with col2:
    if st.button("🚀 Advanced Allocation", use_container_width=True, key="upgrade_allocation"):
        st.info("**AppForge Labs Cost Allocation:**\n\n✅ Multi-dimension allocation (dept, location, project)\n✅ Custom chargeback rules\n✅ Automated invoicing\n✅ Budget forecasting\n\n📧 Contact: paulsemaan007@gmail.com")
