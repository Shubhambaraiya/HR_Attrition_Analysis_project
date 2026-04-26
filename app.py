import streamlit as st
import pandas as pd
import plotly.express as px
st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    return pd.read_csv("final_data.csv")

df = load_data()

# ---------------- CLEAN COLUMN NAMES ----------------
df.columns = df.columns.str.strip()

# ---------------- REQUIRED COLUMNS CHECK ----------------
required_cols = [
    "Department", "JobRole", "OverTime",
    "YearsAtCompany", "JobSatisfaction",
    "WorkLifeBalance", "Attrition"
]

for col in required_cols:
    if col not in df.columns:
        st.error(f"Missing column: {col}")
        st.stop()

# ---------------- CLEAN DATA ----------------
df["OverTime"] = df["OverTime"].astype(str).str.strip().str.lower()
df["Attrition"] = df["Attrition"].astype(str).str.strip().str.lower()

df["WorkLifeBalance"] = pd.to_numeric(df["WorkLifeBalance"], errors="coerce").fillna(3)
df["JobSatisfaction"] = pd.to_numeric(df["JobSatisfaction"], errors="coerce").fillna(3)
df["YearsAtCompany"] = pd.to_numeric(df["YearsAtCompany"], errors="coerce").fillna(0)

# ---------------- FEATURE ENGINEERING ----------------
df["OverTime_Flag"] = df["OverTime"].apply(
    lambda x: 1 if x in ["yes", "y", "1", "true"] else 0
)

df["BurnoutScore"] = (
    df["OverTime_Flag"] * 0.6 +
    (4 - df["WorkLifeBalance"]) * 0.4
)

df["EngagementScore"] = (
    df["JobSatisfaction"] * 0.6 +
    df["WorkLifeBalance"] * 0.4
)

df["WorkloadStress"] = df["OverTime_Flag"]

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.header(" Filters")

department = st.sidebar.multiselect(
    "Department",
    df["Department"].unique(),
    default=df["Department"].unique()
)

job_role = st.sidebar.multiselect(
    "Job Role",
    df["JobRole"].unique(),
    default=df["JobRole"].unique()
)

overtime = st.sidebar.selectbox("Overtime", ["All", "Yes", "No"])

tenure = st.sidebar.slider(
    "Years at Company",
    int(df["YearsAtCompany"].min()),
    int(df["YearsAtCompany"].max()),
    (0, int(df["YearsAtCompany"].max()))
)

# ---------------- FILTER DATA ----------------
filtered_df = df[
    (df["Department"].isin(department)) &
    (df["JobRole"].isin(job_role)) &
    (df["YearsAtCompany"].between(tenure[0], tenure[1]))
]

if overtime != "All":
    filtered_df = filtered_df[filtered_df["OverTime"] == overtime.lower()]

# ---------------- KPI CALCULATIONS ----------------
avg_burnout = filtered_df["BurnoutScore"].mean()
avg_engagement = filtered_df["EngagementScore"].mean()
avg_wlb = filtered_df["WorkLifeBalance"].mean()
avg_satisfaction = filtered_df["JobSatisfaction"].mean()
avg_stress = filtered_df["WorkloadStress"].mean()

# ✅ POWER BI STYLE ATTRITION (COUNT OF YES)
# attrition = filtered_df[filtered_df["Attrition"] == "yes"].shape[0]

# ---------------- UI ----------------
st.title(" HR Analytics Dashboard")

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Burnout", round(avg_burnout, 2))
c2.metric(" Engagement", round(avg_engagement, 2))
c3.metric(" Work-Life Balance", round(avg_wlb, 2))
c4.metric(" Job Satisfaction", round(avg_satisfaction, 2))
c5.metric("Stress", round(avg_stress, 2))
# c6.metric("Total Attrition", attrition)

# ---------------- DEBUG ----------------
with st.expander(" Debug Attrition"):
    st.write(filtered_df["Attrition"].value_counts())
    # st.write("Total Attrition (Yes count):", attrition)

# ---------------- TABLE ----------------
st.subheader(" Department Analysis")

dept = filtered_df.groupby("Department").agg({
    "BurnoutScore": "mean",
    "EngagementScore": "mean",
    "WorkLifeBalance": "mean"
}).reset_index()

st.dataframe(dept, use_container_width=True)

# ---------------- CHARTS ----------------
col1, col2 = st.columns(2)

with col1:
    fig = px.histogram(filtered_df, x="JobSatisfaction", title="Job Satisfaction Distribution")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(filtered_df, x="Department", y="BurnoutScore",
                 color="Department", title="Burnout by Department")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- OVERTIME IMPACT ----------------
st.subheader(" Overtime Impact")

fig = px.scatter(
    filtered_df,
    x="WorkLifeBalance",
    y="BurnoutScore",
    color="OverTime"
)
st.plotly_chart(fig, use_container_width=True)

# ---------------- TREND ----------------
st.subheader(" Engagement vs Tenure")

trend = filtered_df.groupby("YearsAtCompany")["EngagementScore"].mean().reset_index()

fig = px.line(trend, x="YearsAtCompany", y="EngagementScore")
st.plotly_chart(fig, use_container_width=True)

# ---------------- ROLE ----------------
st.subheader(" Role-wise Engagement")

role = filtered_df.groupby("JobRole")["EngagementScore"].mean().reset_index()

fig = px.bar(role, x="JobRole", y="EngagementScore")
st.plotly_chart(fig, use_container_width=True)

# ---------------- ALERTS ----------------
st.subheader(" Insights & Alerts")

low_emp = filtered_df[filtered_df["EngagementScore"] < 2.5]
st.write(" Low Engagement Employees:", len(low_emp))

if avg_burnout > 1.5:
    st.error("High Burnout Risk!")

if avg_wlb < 2.5:
    st.warning("Low Work-Life Balance!")
