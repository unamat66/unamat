import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Scientific Visualisation Dashboard",
    layout="wide"
)

st.title("’📈 Scientific Visualisation Dashboard")
st.subheader(
    "Income, Marriages, and Prison Statistics in Malaysia (2020–2024)"
)

st.markdown("""
This dashboard explores the yearly patterns and relationships
between national income, marriages, and prisoners in Malaysia
from 2020 to 2024.
""")

# ==================================================
# 2. LOAD AND PROCESS DATA
# ==================================================

@st.cache_data
def load_data():
    income_df = pd.read_csv("income.csv")
    marriages_df = pd.read_csv("marriages_age.csv")
    crime_df = pd.read_csv("crime.csv")

    for df in [income_df, marriages_df, crime_df]:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["year"] = df["date"].dt.year

    income_df = income_df[income_df["year"].between(2020, 2024)].copy()
    marriages_df = marriages_df[marriages_df["year"].between(2020, 2024)].copy()
    crime_df = crime_df[crime_df["year"].between(2020, 2024)].copy()

    income_df["income"] = pd.to_numeric(
        income_df["income"].replace("?", pd.NA), errors="coerce"
    )
    marriages_df["abs"] = pd.to_numeric(marriages_df["abs"], errors="coerce")
    crime_df["prisoners"] = pd.to_numeric(crime_df["prisoners"], errors="coerce")

    for df in [income_df, marriages_df, crime_df]:
        for col in ["state", "sex", "age", "variable"]:
            if col in df.columns:
                df[col] = df[col].astype("string").str.strip()

    income_yearly = (
        income_df[income_df["variable"].str.lower() == "mean"]
        .groupby("year")["income"]
        .mean()
        .reset_index(name="avg_income")
    )

    marriages_yearly = (
        marriages_df[marriages_df["age"].str.lower() == "all"]
        .groupby("year")["abs"]
        .sum(min_count=1)
        .reset_index(name="total_marriages")
    )

    crime_yearly = (
        crime_df[
            (crime_df["state"].str.lower() == "malaysia") &
            (crime_df["sex"].str.lower() == "both")
        ]
        .groupby("year")["prisoners"]
        .sum(min_count=1)
        .reset_index(name="total_prisoners")
    )

    merged_yearly = income_yearly.merge(marriages_yearly, on="year", how="outer")
    merged_yearly = merged_yearly.merge(crime_yearly, on="year", how="outer")
    merged_yearly = merged_yearly.sort_values("year").reset_index(drop=True)

    return merged_yearly

try:
    merged_yearly_df = load_data()
except Exception as e:
    st.error(f"Error loading datasets: {e}")
    st.stop()

# ==================================================
# 3. GENERAL FUNCTIONS
# ==================================================

def format_number(value, prefix="", suffix="", decimals=0):
    if value is None or pd.isna(value):
        return "N/A"
    return f"{prefix}{value:,.{decimals}f}{suffix}"

def get_value(data, column):
    if data.empty:
        return None
    val = data[column].iloc[0]
    if pd.isna(val):
        return None
    return float(val)

def percentage_change(current, previous):
    if current is None or previous is None:
        return None
    if previous == 0:
        return None
    return ((current - previous) / abs(previous)) * 100

def get_correlation(data, x, y):
    valid = data[[x, y]].dropna()
    if len(valid) < 2:
        return None
    if valid[x].nunique() < 2 or valid[y].nunique() < 2:
        return None
    return valid[x].corr(valid[y])

def indexed_data(data, columns):
    result = data[["year"] + columns].dropna().copy()
    if result.empty:
        return result
    base = result.iloc[0]
    for col in columns:
        if base[col] == 0:
            return pd.DataFrame()
        result[col] = (result[col] / base[col]) * 100
    return result

def show_metric(label, value, delta=None):
    st.metric(label=label, value=value, delta=delta)

# ==================================================
# 4. YEAR SELECTOR
# ==================================================

all_years = sorted(merged_yearly_df["year"].dropna().astype(int).unique())

if not all_years:
    st.error("No data available for 2020–2024.")
    st.stop()

selected_year = st.sidebar.selectbox(
    "Select Year for Summary Metrics",
    all_years,
    index=len(all_years) - 1
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Dashboard Information")
st.sidebar.write("Period: 2020–2024")
st.sidebar.write("Data Level: Malaysia National")
st.sidebar.write("Total Objectives: 3")
st.sidebar.write("Total Visualisations: 9")

year_data = merged_yearly_df[merged_yearly_df["year"] == selected_year]
previous_data = merged_yearly_df[merged_yearly_df["year"] == selected_year - 1]

avg_income = get_value(year_data, "avg_income")
total_marriages = get_value(year_data, "total_marriages")
total_prisoners = get_value(year_data, "total_prisoners")

previous_income = get_value(previous_data, "avg_income")
previous_marriages = get_value(previous_data, "total_marriages")
previous_prisoners = get_value(previous_data, "total_prisoners")

income_change = percentage_change(avg_income, previous_income)
marriage_change = percentage_change(total_marriages, previous_marriages)
prisoner_change = percentage_change(total_prisoners, previous_prisoners)

# ==================================================
# 5. PREPARE PAIR DATA
# ==================================================

income_prisoner = merged_yearly_df[["year", "avg_income", "total_prisoners"]].dropna().sort_values("year")
marriage_prisoner = merged_yearly_df[["year", "total_marriages", "total_prisoners"]].dropna().sort_values("year")
income_marriage = merged_yearly_df[["year", "avg_income", "total_marriages"]].dropna().sort_values("year")

corr_income_prisoner = get_correlation(merged_yearly_df, "avg_income", "total_prisoners")
corr_marriage_prisoner = get_correlation(merged_yearly_df, "total_marriages", "total_prisoners")
corr_income_marriage = get_correlation(merged_yearly_df, "avg_income", "total_marriages")

# ==================================================
# 6. THREE VISUALISATION PAGES (TABS)
# ==================================================

tab1, tab2, tab3 = st.tabs([
    "1. Income vs Prisoners",
    "2. Marriages vs Prisoners",
    "3. Income vs Marriages"
])

# ==================================================
# TAB 1: INCOME VS PRISONERS
# ==================================================
with tab1:
    st.header("Objective 1: Income vs Prisoners")
    st.markdown("""
    **Objective Statement**
    To examine the annual trends and relationship between
    Malaysia's average income and total number of prisoners
    from 2020 to 2024.
    """)

    st.markdown("### 📊 Summary Box")
    col1, col2, col3 = st.columns(3)
    with col1:
        show_metric(
            f"Average Income ({selected_year})",
            format_number(avg_income, "RM ", decimals=2),
            f"{income_change:+.2f}%" if income_change is not None else None
        )
    with col2:
        show_metric(
            f"Total Prisoners ({selected_year})",
            format_number(total_prisoners),
            f"{prisoner_change:+.2f}%" if prisoner_change is not None else None
        )
    with col3:
        show_metric(
            "Income-Prisoner Correlation",
            format_number(corr_income_prisoner, decimals=3)
        )

    st.caption("Percentage changes compare the selected year with the previous year. Correlation uses matching annual observations.")
    st.divider()

    # GRAPH 1: DUAL AXIS LINE CHART
    st.subheader("Visualisation 1: Annual Income and Prisoner Trends")
    if not income_prisoner.empty:
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(
            go.Scatter(
                x=income_prisoner["year"], y=income_prisoner["avg_income"],
                name="Average Income (RM)", mode="lines+markers",
                line=dict(width=3, color="blue")
            ), secondary_y=False
        )
        fig1.add_trace(
            go.Scatter(
                x=income_prisoner["year"], y=income_prisoner["total_prisoners"],
                name="Total Prisoners", mode="lines+markers",
                line=dict(width=3, color="red")
            ), secondary_y=True
        )
        fig1.update_layout(
            title="Annual Trends of Income and Prisoners",
            xaxis_title="Year", template="plotly_white", hovermode="x unified"
        )
        fig1.update_yaxes(title_text="Average Income (RM)", secondary_y=False)
        fig1.update_yaxes(title_text="Total Prisoners", secondary_y=True)
        st.plotly_chart(fig1, use_container_width=True)
        st.caption("Interpretation: This chart compares the yearly direction of average income and prisoner totals.")
    else:
        st.warning("Insufficient matching data.")

    st.divider()

    # GRAPH 2: SCATTER PLOT
    st.subheader("Visualisation 2: Income-Prisoner Relationship")
    if len(income_prisoner) >= 2:
        fig2 = px.scatter(
            income_prisoner, x="avg_income", y="total_prisoners", text="year",
            title="Relationship between Average Income and Prisoners",
            labels={"avg_income": "Average Income (RM)", "total_prisoners": "Total Prisoners"},
            color="year"
        )
        fig2.update_traces(textposition="top center")
        fig2.update_layout(template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Interpretation: Each point represents one year. The scatter plot helps identify associations.")
    else:
        st.warning("At least two matching observations are required.")

    st.divider()

    # GRAPH 3: INDEXED TREND CHART
    st.subheader("Visualisation 3: Indexed Income and Prisoner Trends")
    indexed1 = indexed_data(income_prisoner, ["avg_income", "total_prisoners"])
    if not indexed1.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=indexed1["year"], y=indexed1["avg_income"], mode="lines+markers", name="Income Index"))
        fig3.add_trace(go.Scatter(x=indexed1["year"], y=indexed1["total_prisoners"], mode="lines+markers", name="Prisoner Index"))
        fig3.add_hline(y=100, line_dash="dash", annotation_text="Base Year = 100")
        fig3.update_layout(title="Indexed Annual Changes (Base Year = 100)", xaxis_title="Year", yaxis_title="Index Value", template="plotly_white")
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("Interpretation: Relative changes normalized to 100 in the first available matching year.")
    else:
        st.warning("Unable to calculate indexed values.")

# ==================================================
# TAB 2: MARRIAGES VS PRISONERS
# ==================================================
with tab2:
    st.header("Objective 2: Marriages vs Prisoners")
    st.markdown("""
    **Objective Statement**
    To investigate yearly changes and the relationship between
    the total number of marriages and prisoners in Malaysia
    from 2020 to 2024.
    """)

    st.markdown("### 📊 Summary Box")
    col1, col2, col3 = st.columns(3)
    with col1:
        show_metric(
            f"Total Marriages ({selected_year})",
            format_number(total_marriages),
            f"{marriage_change:+.2f}%" if marriage_change is not None else None
        )
    with col2:
        show_metric(
            f"Total Prisoners ({selected_year})",
            format_number(total_prisoners),
            f"{prisoner_change:+.2f}%" if prisoner_change is not None else None
        )
    with col3:
        show_metric(
            "Marriage-Prisoner Correlation",
            format_number(corr_marriage_prisoner, decimals=3)
        )

    st.caption("Percentage changes compare the selected year with the previous year.")
    st.divider()

    # GRAPH 4: GROUPED BAR CHART
    st.subheader("Visualisation 4: Yearly Marriage and Prisoner Comparison")
    if not marriage_prisoner.empty:
        fig4 = make_subplots(specs=[[{"secondary_y": True}]])
        fig4.add_trace(
            go.Bar(x=marriage_prisoner["year"], y=marriage_prisoner["total_marriages"], name="Total Marriages", marker_color="skyblue"),
            secondary_y=False
        )
        fig4.add_trace(
            go.Bar(x=marriage_prisoner["year"], y=marriage_prisoner["total_prisoners"], name="Total Prisoners", marker_color="salmon"),
            secondary_y=True
        )
        fig4.update_layout(
            title="Yearly Comparison of Marriages and Prisoners", barmode="group",
            xaxis_title="Year", template="plotly_white", hovermode="x unified"
        )
        fig4.update_yaxes(title_text="Total Marriages", secondary_y=False)
        fig4.update_yaxes(title_text="Total Prisoners", secondary_y=True)
        st.plotly_chart(fig4, use_container_width=True)
        st.caption("Interpretation: Compares marriages and prisoners. Scales on separate axes.")
    else:
        st.warning("Insufficient matching data.")

    st.divider()

    # GRAPH 5: SCATTER PLOT
    st.subheader("Visualisation 5: Marriage-Prisoner Relationship")
    if len(marriage_prisoner) >= 2:
        fig5 = px.scatter(
            marriage_prisoner, x="total_marriages", y="total_prisoners", text="year", color="year",
            title="Relationship between Marriages and Prisoners",
            labels={"total_marriages": "Total Marriages", "total_prisoners": "Total Prisoners"}
        )
        fig5.update_traces(textposition="top center")
        fig5.update_layout(template="plotly_white")
        st.plotly_chart(fig5, use_container_width=True)
        st.caption("Interpretation: Examines relationship points over time.")
    else:
        st.warning("At least two matching observations are required.")

    st.divider()

    # GRAPH 6: INDEXED TREND
    st.subheader("Visualisation 6: Indexed Marriage and Prisoner Trends")
    indexed2 = indexed_data(marriage_prisoner, ["total_marriages", "total_prisoners"])
    if not indexed2.empty:
        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(x=indexed2["year"], y=indexed2["total_marriages"], mode="lines+markers", name="Marriage Index"))
        fig6.add_trace(go.Scatter(x=indexed2["year"], y=indexed2["total_prisoners"], mode="lines+markers", name="Prisoner Index"))
        fig6.add_hline(y=100, line_dash="dash", annotation_text="Base Year = 100")
        fig6.update_layout(title="Indexed Marriage and Prisoner Changes", xaxis_title="Year", yaxis_title="Index Value", template="plotly_white")
        st.plotly_chart(fig6, use_container_width=True)
        st.caption("Interpretation: Comparison of index trends over time.")
    else:
        st.warning("Unable to calculate indexed values.")

# ==================================================
# TAB 3: INCOME VS MARRIAGES
# ==================================================
with tab3:
    st.header("Objective 3: Income vs Marriages")
    st.markdown("""
    **Objective Statement**
    To analyse the annual trends, association and correlation
    between Malaysia's average income and total marriages
    from 2020 to 2024.
    """)

    st.markdown("### 📊 Summary Box")
    col1, col2, col3 = st.columns(3)
    with col1:
        show_metric(
            f"Average Income ({selected_year})",
            format_number(avg_income, "RM ", decimals=2),
            f"{income_change:+.2f}%" if income_change is not None else None
        )
    with col2:
        show_metric(
            f"Total Marriages ({selected_year})",
            format_number(total_marriages),
            f"{marriage_change:+.2f}%" if marriage_change is not None else None
        )
    with col3:
        show_metric(
            "Income-Marriage Correlation",
            format_number(corr_income_marriage, decimals=3)
        )

    st.caption("Correlation is calculated using matching annual observations from 2020 to 2024.")
    st.divider()

    # GRAPH 7: DUAL AXIS LINE CHART
    st.subheader("Visualisation 7: Income and Marriage Trends")
    if not income_marriage.empty:
        fig7 = make_subplots(specs=[[{"secondary_y": True}]])
        fig7.add_trace(
            go.Scatter(
                x=income_marriage["year"], y=income_marriage["avg_income"],
                mode="lines+markers", name="Average Income (RM)",
                line=dict(color="blue", width=3)
            ), secondary_y=False
        )
        fig7.add_trace(
            go.Scatter(
                x=income_marriage["year"], y=income_marriage["total_marriages"],
                mode="lines+markers", name="Total Marriages",
                line=dict(color="green", width=3)
            ), secondary_y=True
        )
        fig7.update_layout(
            title="Annual Trends of Income and Marriages",
            xaxis_title="Year", template="plotly_white", hovermode="x unified"
        )
        fig7.update_yaxes(title_text="Average Income (RM)", secondary_y=False)
        fig7.update_yaxes(title_text="Total Marriages", secondary_y=True)
        st.plotly_chart(fig7, use_container_width=True)
        st.caption("Interpretation: Dual line chart to explore trend alignment.")
    else:
        st.warning("Insufficient matching data.")

    st.divider()

    # GRAPH 8: SCATTER PLOT
    st.subheader("Visualisation 8: Income-Marriage Relationship")
    if len(income_marriage) >= 2:
        fig8 = px.scatter(
            income_marriage, x="avg_income", y="total_marriages", text="year", color="year",
            title="Relationship between Average Income and Marriages",
            labels={"avg_income": "Average Income (RM)", "total_marriages": "Total Marriages"}
        )
        fig8.update_traces(textposition="top center")
        fig8.update_layout(template="plotly_white")
        st.plotly_chart(fig8, use_container_width=True)
        st.caption("Interpretation: Examining scatter alignment of income versus marriage levels.")
    else:
        st.warning("At least two matching observations are required.")

    st.divider()

    # GRAPH 9: CORRELATION HEATMAP
    st.subheader("Visualisation 9: Income and Marriage Correlation Heatmap")
    if len(income_marriage) >= 2:
        corr_matrix_tab3 = income_marriage[["avg_income", "total_marriages"]].corr()
        fig9 = px.imshow(
            corr_matrix_tab3, text_auto=".3f", aspect="auto", color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1, labels={"color": "Correlation Coefficient"},
            x=["Average Income", "Total Marriages"], y=["Average Income", "Total Marriages"],
            title="Correlation Matrix: Income and Marriages"
        )
        fig9.update_layout(template="plotly_white")
        st.plotly_chart(fig9, use_container_width=True)
        st.caption("Interpretation: Displays the Pearson correlation coefficient between Income and Marriages.")
    else:
        st.warning("At least two matching observations are required.")

# ==================================================
# 7. FOOTER
# ==================================================
st.divider()
st.markdown("### About This Dashboard")
st.write("This dashboard uses three datasets from the Department of Statistics Malaysia (DOSM) and Malaysia Open Data.")
st.caption("Scientific Visualisation Assignment | JIE42403 | 2020–2024")
st.caption("Note: Correlation does not imply causation.")
