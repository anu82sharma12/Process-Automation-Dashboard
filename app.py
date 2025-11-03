import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import base64
from export_report import export_pdf, export_excel

st.set_page_config(page_title="Reporting Engine", layout="wide")
st.title("Process-Automation Dashboard")
st.caption("10+ hours saved monthly — one click")

# Load / generate data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data/mock_operations.csv")
    except:
        from generate_data import create_mock
        df = create_mock()
        df.to_csv("data/mock_operations.csv", index=False)
    return df

df = load_data()

# Auto-clean
df["OrderDate"] = pd.to_datetime(df["OrderDate"])
df["Delay"] = (pd.to_datetime(df["ShipDate"]) - pd.to_datetime(df["DeliveryDate"])).dt.days
df["Month"] = df["OrderDate"].dt.strftime("%b-%Y")

# Sidebar filters
st.sidebar.header("Filters")
regions = st.sidebar.multiselect("Region", df["Region"].unique(), df["Region"].unique())
months = st.sidebar.multiselect("Month", df["Month"].unique(), df["Month"].unique())

filtered = df[df["Region"].isin(regions) & df["Month"].isin(months)]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Orders", f"{len(filtered):,}")
col2.metric("Avg Delay", f"{filtered['Delay'].mean():.1f} days", "-2.1")
col3.metric("On-Time %", f"{(filtered['Delay']<=0).mean():.1%}", "up 4%")
col4.metric("Cost Saved", f"${filtered['CostSaved'].sum():,.0f}")

# Charts
tab1, tab2, tab3 = st.tabs(["Delay Trends", "Regional Heatmap", "Top SKUs"])

with tab1:
    fig = px.line(filtered.groupby("Month")["Delay"].mean().reset_index(),
                  x="Month", y="Delay", title="Average Delay by Month")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    heat = filtered.pivot_table(values="Delay", index="Region", columns="Category", aggfunc="mean")
    fig = px.imshow(heat, text_auto=".1f", color_continuous_scale="RdYlGn_r")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    top = filtered.groupby("Product")["Revenue"].sum().nlargest(10)
    fig = px.bar(x=top.index, y=top.values, labels={"x":"Product","y":"Revenue"})
    st.plotly_chart(fig, use_container_width=True)

# Export
col1, col2 = st.columns(2)
with col1:
    if st.button("Export PDF Report"):
        pdf_bytes = export_pdf(filtered)
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="Report_{datetime.now():%b%Y}.pdf">Download PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

with col2:
    if st.button("Export Excel"):
        excel_bytes = export_excel(filtered)
        b64 = base64.b64encode(excel_bytes).decode()
        href = f'<a href="data:application/vnd.openxmlformats;base64,{b64}" download="Data_{datetime.now():%b%Y}.xlsx">Download Excel</a>'
        st.markdown(href, unsafe_allow_html=True)
