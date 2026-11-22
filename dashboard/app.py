"""Ghost Warehouse fulfillment dashboard.

Run: pip install streamlit pandas
     streamlit run dashboard/app.py
Generate KPI files first: python scripts/run_fulfillment.py
"""
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
st.set_page_config(page_title="Ghost Warehouse | Operations", page_icon="📦", layout="wide")
st.title("Ghost Warehouse")
st.caption("Synthetic BMW M parts distribution center · pilot fulfillment analytics")

required = ["fulfillment_kpis.csv", "fulfillment_order_status.csv",
            "fulfillment_pick_tasks.csv", "fulfillment_events.csv",
            "fulfillment_balances.csv"]
missing = [f for f in required if not (DATA / f).exists()]
if missing:
    st.warning("Run `python scripts/run_fulfillment.py` to generate the dashboard data.")
    st.code("python scripts/run_fulfillment.py")
    st.stop()

kpi = pd.read_csv(DATA / required[0]).iloc[0]
orders = pd.read_csv(DATA / required[1])
tasks = pd.read_csv(DATA / required[2])
events = pd.read_csv(DATA / required[3])
balances = pd.read_csv(DATA / required[4])
a,b,c,d = st.columns(4)
a.metric("Orders shipped", f'{int(kpi["shipped_orders"]):,} / {int(kpi["orders"]):,}')
b.metric("Units shipped", f'{int(kpi["shipped_units"]):,}')
c.metric("Ending inventory", f'{int(kpi["ending_units"]):,} units')
d.metric("Average cycle", f'{float(kpi["average_cycle_minutes"]):.1f} min')
st.caption("Times and route distances are simulated assumptions, not measured facility performance.")
left,right = st.columns(2)
with left:
    st.subheader("Fulfillment status")
    st.bar_chart(orders["status"].value_counts())
with right:
    st.subheader("Picking assignments by employee")
    st.bar_chart(tasks["employee_id"].value_counts())
st.subheader("Order explorer")
selected = st.selectbox("Order ID", orders["order_id"].tolist())
st.dataframe(orders[orders["order_id"] == selected], hide_index=True, use_container_width=True)
st.dataframe(tasks[tasks["order_id"] == selected], hide_index=True, use_container_width=True)
st.dataframe(events[events["order_id"] == selected], hide_index=True, use_container_width=True)
st.subheader("Inventory reconciliation")
st.write(f'Opening: **{int(kpi["opening_units"]):,}** · Shipped: **{int(kpi["shipped_units"]):,}** · Ending: **{int(kpi["ending_units"]):,}** units')
if (balances["ending_quantity"] < 0).any():
    st.error("Negative stock detected")
else:
    st.success("No negative stock in generated pilot balances")
