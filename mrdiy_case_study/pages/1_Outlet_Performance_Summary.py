# ==========1. Import ==========
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math
import numpy as np
from scipy.stats import pearsonr
from plotly.subplots import make_subplots
from pathlib import Path

# ==========2. Constant==========
raw_data_file="packing_test.xlsx"
DATA_PATH = Path(__file__).parent / "packing_test.xlsx"
max_rows=2638
year=2025
header=""
subheader=""
task_1_header="📦 Outlet Packing Performance Dashboard"
df_column_map = {
    'OUTLET CODE':         'Outlet Code',
    'IB DATE':             'IB Date',
    'TOTAL SKU':           'Total SKU',
    'TOTAL CTN PACKED':    'Total Carton Packed',
    'TOTAL PALLET PACKED': 'Total Pallet Packed',
    'TTL HRS':             'Total Hours Used',
    'NO. OF PACKER':       'No. of Packer',
}
hours_per_day=24
sum_columns=['Total SKU', 'Total Carton Packed', 'Total Pallet Packed']
date_column='IB Date'
index_columns = {
    'Total SKU':           'SKU Index',
    'Total Carton Packed':    'Carton Index',
    'Total Pallet Packed': 'Pallet Index',
}
index_chart_labels={
    'Month': 'Month in 2025',
    'value': 'Index Value',
    'variable': 'Metric'
}
index_chart_summary=("Workload was lowest in January and highest in October and December, with SKU, carton and pallet volumes moving closely together. Cartons can therefore serve as a proxy for overall workload in later analysis.")
p_value_significance_level = 0.05 # Pearson correlation coefficient(r-value) is statistically significant if p<0.05
r_value_strength_levels = [
    (0.9, "Very strong"),
    (0.7, "Strong"),
    (0.5, "Moderate"),
]
r_value_weakest_label = "Weak"
correlation_pairs = [
    ('Total SKU',    'Total Carton Packed'),
    ('Total Carton Packed', 'Total Pallet Packed'),
    ('Total SKU',    'Total Pallet Packed'),
]
outlet_column = 'Outlet Code'
raw_packer_column = 'No. of Packer'
carton_column = 'Total Carton Packed'
hours_column = 'Total Hours Used'
month_column = f'Month in {year}'
speed_expander_label = "Learn more about monthly outlet throughput (cartons/hr) in 2025"
speed_column = 'Packing Speed(cartons/hr)'
speed_heatmap_header = "### Outlet throughput heatmap: cartons packed per hour across 2025"
speed_heatmap_xgap = 0   # lines between months (vertical)
speed_heatmap_ygap = 1   # lines between outlets (horizontal), 0 = off
speed_heatmap_height = 1200
speed_heatmap_color_scale = [
    [0.0, '#fff5f0'],   # very light = slow
    [0.25, '#fcae91'],
    [0.5, '#fb6a4a'],
    [0.75, '#cb181d'],
    [1.0, '#67000d'],   # very dark = fast
]
speed_heatmap_low_pct = 0.10    # values below this percentile get the lightest colour
speed_heatmap_high_pct = 0.90   # values above this percentile get the darkest colour
speed_heatmap_labels = {'x': 'Month', 'y': 'Outlet', 'color': 'Cartons/hr'}
volume_line_header = "### Monthly Cartons Volume vs Per-Person Productivity per Outlet"
compare_outlet_count = 2
volume_line_height = 300          # was 400, less tall
carton_step_round = 100           # carton ticks are multiples of this
volume_line_color = '#1f77b4'
volume_line_width = 3
volume_packer_color = '#ff7f0e'
volume_packer_opacity = 0.4
volume_chart_margin = dict(l=60, r=60, t=40, b=50)  # Increased 'r' from 60 to 90
month_format = '%m'
axis_headroom = 1.1     # 10% space above the largest value
packer_column = 'AVG No. of Packer'
volume_legend_note = (
    f"🔵 **{carton_column}** (line, left axis)  |  "
    f"🟠 **{packer_column}** (bars, right axis)"
)
bubble_size_multiplier = 2  # Multiplies packer count so bubbles are visible (e.g., 5 packers = size 60)
bubble_border_color = 'white'
bubble_border_width = 1.5
monthly_efficiency_column = 'Cartons per Packer-Hour'
min_months = 6                       # CV needs at least this many months
rank_column = 'Rank'
overall_speed_column = 'Speed (cartons/hr)'
months_recorded_column = 'Months Recorded'
std_column = 'Std of Monthly Speed'
cv_column = 'Monthly Fluctuation/CV%'
consistency_column = 'Consistency'
cv_levels = [(15, "Steady"), (30, "Moderate")]   # CV % below the limit gets the label
cv_highest_label = "Not steady"
not_enough_label = "Insufficient Data"
consistency_header = "### Consistency per Outlet in 2025"
consistency_grid_style = '1px solid #bbbbbb'
consistency_colours = {
    cv_levels[0][1]: '#c6efce',     # green  = steady
    cv_levels[1][1]: '#ffeb9c',     # yellow = moderate
    cv_highest_label: '#ffc7ce',    # red    = erratic
    not_enough_label: '#eeeeee',    # grey   = not enough data
}
consistency_note = (
    "**Rank** = Fastest outlet first, based on Overall Speed. \n\n"
    f"**Overall Speed/Efficiency** = Total cartons ÷ total hours in {year} per outlet. \n\n"
    "**Standard Deviation(Std)** = How far an outlet's monthly speeds typically stray from its own average speed. \n\n"
    "**Coeficient of Variation (CV %)** = Std ÷ average monthly speed. How far monthly speed moves up or down from the outlet's average. Lower = steadier.  \n\n"
    f"🟢 **{cv_levels[0][1]}**: CV under {cv_levels[0][0]}%  |  "
    f"🟡 **{cv_levels[1][1]}**: CV under {cv_levels[1][0]}%  |  "
    f"🔴 **{cv_highest_label}**: CV {cv_levels[1][0]}% or above  |  "
    f"⚪ **{not_enough_label}**: fewer than {min_months} months of data"
)
top_30_most_efficient_outlet=30
efficiency_header_packer = (
    f"### Top {top_30_most_efficient_outlet} outlets by productivity: "
    f"most cartons per packer-hour, {year}"
)
efficiency_header_speed = (
    f"### Top {top_30_most_efficient_outlet} outlets by throughput: "
    f"most cartons per hour, {year}"
)
efficiency_toggle_label = "Adjust for packer efficiency per outlet"
packer_efficiency_column = 'Cartons per Packer-Hour'
packer_hours_column = 'Packer-Hours'
efficiency_bar_color = '#1f77b4'
efficiency_bar_height = 500
efficiency_chart_margin = dict(l=60, r=30, t=30, b=90)
efficiency_note_speed = "Bars show overall speed: total cartons ÷ total hours in the year."
efficiency_note_packer = (
    "Bars show cartons per packer-hour: total cartons ÷ (hours × number of packers), "
    "summed over all records. Records without a packer count are excluded."
)

# ==========3. Data==========
@st.cache_data
def load_data(max_rows=10000):
    return pd.read_excel(DATA_PATH).iloc[:max_rows]

def rename_columns(df: pd.DataFrame):
    return df.rename(columns=df_column_map)

def convert_hours(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with hours converted from day fractions to hours (negatives set to 0)."""
    result = df.copy()
    result[hours_column] = result[hours_column].clip(lower=0) * hours_per_day
    return result

def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with the date column converted to datetime."""
    result = df.copy()
    result[date_column] = pd.to_datetime(result[date_column], errors='coerce')
    return result

def get_length_of_df(df: pd.DataFrame) -> int:
    return len(df)

# ==========4. Calculation==========
def build_monthly_totals(df:pd.DataFrame) -> pd.DataFrame:
    """Return one row per month with summed SKU, carton and pallet totals."""
    monthly_subset = df[[date_column] + sum_columns].copy()
    monthly_subset['Month'] = monthly_subset[date_column].dt.strftime(month_format)
    return monthly_subset.groupby('Month')[sum_columns].sum().reset_index()

def build_index_table(monthly:pd.DataFrame) -> pd.DataFrame:
    baseline = monthly.iloc[0]
    index_table = monthly.copy()
    for source, index_column in index_columns.items():
        index_table[index_column] = ((monthly[source] / baseline[source]) * 100).round(1)
    return index_table.drop(columns=sum_columns)

# def add_sku_per_carton(monthly: pd.DataFrame) -> pd.DataFrame:
#     """Return a copy of monthly with an 'SKUs Per Carton' column."""
#     result = monthly.copy()
#     result['SKUs Per Carton'] = result['Total SKU'] / result['Total Carton Packed']
#     return result

# def classify_r_value_strength(r: float) -> str:
#     """Return a strength label for a correlation coefficient."""
#     for threshold, label in r_value_strength_levels:
#         if abs(r) >= threshold:
#             return label
#     return r_value_weakest_label

# def correlation_analysis(df: pd.DataFrame) -> pd.DataFrame:
#     """Return correlation, strength and significance for each index pair."""
#     rows = []
#     for col_a, col_b in correlation_pairs:
#         r, p = pearsonr(df[col_a], df[col_b])
#         rows.append({
#             'Pair': f'{col_a} ↔ {col_b}',
#             'r-value': round(r, 3),
#             'Direction': "Positive" if r > 0 else "Negative",
#             'r-value Strength': classify_r_value_strength(r),
#             'p-value': "< 0.001" if p < 0.001 else round(p, 3),
#             'Significant Level': p < p_value_significance_level# True / False
#         })
#     return pd.DataFrame(rows)

def build_outlet_monthly_speed(df: pd.DataFrame) -> pd.DataFrame:
    """Return cartons/hr for each outlet and month."""
    speed_subset = df[[outlet_column, date_column, carton_column, hours_column]].copy()
    speed_subset[month_column] = speed_subset[date_column].dt.strftime(month_format)
    monthly_speed = (
        speed_subset.groupby([outlet_column, month_column])[[carton_column, hours_column]]
        .sum()
        .reset_index()
    )
    monthly_speed = monthly_speed[monthly_speed[hours_column] > 0].copy()
    monthly_speed[speed_column] = monthly_speed[carton_column] / monthly_speed[hours_column]
    return monthly_speed

def build_speed_pivot(monthly_speed: pd.DataFrame) -> pd.DataFrame:
    """Return a grid with outlets as rows and months as columns, fastest outlet first."""
    pivot = monthly_speed.pivot(
        index=outlet_column,
        columns=month_column,
        values=speed_column,
    )
    return pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]

def build_outlet_monthly_volume(df: pd.DataFrame) -> pd.DataFrame:
    """Return cartons, avg packers (rounded down) and cartons per packer-hour for each outlet and month."""
    data = df[[outlet_column, date_column, carton_column, hours_column, raw_packer_column]].copy()
    data[month_column] = data[date_column].dt.strftime(month_format)
    valid = (data[hours_column] > 0) & (data[raw_packer_column] > 0)
    data[packer_hours_column] = (data[hours_column] * data[raw_packer_column]).where(valid)
    data['Valid Cartons'] = data[carton_column].where(valid)
    monthly = (
        data.groupby([outlet_column, month_column])
        .agg(**{
            carton_column: (carton_column, 'sum'),
            packer_column: (raw_packer_column, 'mean'),
            packer_hours_column: (packer_hours_column, 'sum'),
            'Valid Cartons': ('Valid Cartons', 'sum'),
        })
        .reset_index()
    )
    monthly[monthly_efficiency_column] = (
        monthly['Valid Cartons'] / monthly[packer_hours_column].replace(0, float('nan'))
    ).round(1)
    monthly[packer_column] = (
        np.floor(monthly[packer_column]).clip(lower=1).where(monthly[packer_column] > 0, 0)
    )
    return monthly.drop(columns=['Valid Cartons', packer_hours_column])

def get_outlet_monthly_volume(monthly_volume: pd.DataFrame, outlet: str) -> pd.DataFrame:
    all_months = sorted(monthly_volume[month_column].unique())
    outlet_df = (
        monthly_volume[monthly_volume[outlet_column] == outlet]
        .set_index(month_column)[[carton_column, packer_column, monthly_efficiency_column]]
        .reindex(all_months)
        .rename_axis(month_column)
        .reset_index()
    )
    # Missing months: 0 cartons and 0 packers, but efficiency stays NaN so no bubble is drawn
    outlet_df[[carton_column, packer_column]] = outlet_df[[carton_column, packer_column]].fillna(0)
    return outlet_df

def build_overall_throughput(monthly_speed: pd.DataFrame) -> pd.DataFrame:
    """Return overall cartons/hr per outlet for the year."""
    totals = monthly_speed.groupby(outlet_column)[[carton_column, hours_column]].sum()
    result = totals[carton_column] / totals[hours_column]
    return result.rename(overall_speed_column).reset_index()

# def classify_consistency(cv: float, months: int) -> str:
#     """Return a consistency label from the CV (%) and the number of months recorded."""
#     if months < min_months or pd.isna(cv):
#         return not_enough_label
#     for limit, label in cv_levels:
#         if cv < limit:
#             return label
#     return cv_highest_label

# def build_outlet_consistency(monthly_speed: pd.DataFrame) -> pd.DataFrame:
#     """Return one row per outlet: overall speed, spread of monthly speeds and a consistency label."""
#     totals = monthly_speed.groupby(outlet_column)[[carton_column, hours_column]].sum()
#     by_outlet = monthly_speed.groupby(outlet_column)[speed_column]
#     summary = pd.DataFrame({
#         overall_speed_column: totals[carton_column] / totals[hours_column],
#         months_recorded_column: by_outlet.count(),
#         std_column: by_outlet.std(),
#         cv_column: by_outlet.std() / by_outlet.mean() * 100,
#     })
#     too_few = summary[months_recorded_column] < min_months
#     summary.loc[too_few, [std_column, cv_column]] = float('nan')
#     summary[consistency_column] = [
#         classify_consistency(cv, months)
#         for cv, months in zip(summary[cv_column], summary[months_recorded_column])
#     ]
#     summary = summary.sort_values(overall_speed_column, ascending=False).reset_index()
#     summary.insert(0, rank_column, summary.index + 1)
#     return summary

# def find_consistent_high_performers(consistency_table: pd.DataFrame) -> list:
#     """Return outlets with above-median overall speed and a 'Steady' label."""
#     median_speed = consistency_table[overall_speed_column].median()
#     winners = consistency_table[
#         (consistency_table[overall_speed_column] > median_speed)
#         & (consistency_table[consistency_column] == cv_levels[0][1])
#     ]
#     return winners[outlet_column].tolist()

def build_packer_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    data = df[[outlet_column, carton_column, hours_column, raw_packer_column]].copy()
    data = data[(data[hours_column] > 0) & (data[raw_packer_column] > 0)].copy()
    data[packer_hours_column] = data[hours_column] * data[raw_packer_column]
    totals = data.groupby(outlet_column)[[carton_column, packer_hours_column]].sum()
    result = totals[carton_column] / totals[packer_hours_column]
    return result.rename(packer_efficiency_column).reset_index()

def select_efficiency(throughput: pd.DataFrame, packer_efficiency: pd.DataFrame, per_packer: bool) -> tuple:
    """Return (table, value column) for the chosen view, sorted highest first."""
    if per_packer:
        table, value_column = packer_efficiency, packer_efficiency_column
    else:
        table, value_column = throughput, overall_speed_column
    return table.sort_values(value_column, ascending=False).reset_index(drop=True), value_column

# ==========5. Visualization==========
def build_index_chart(index_table:pd.DataFrame):
    chart_data = index_table
    fig = px.line(
        chart_data,
        x='Month',
        y=list(index_columns.values()),
        markers=True,
    )
    fig.add_hline(y=100, line_dash='dash', line_color='gray')
    fig.update_layout(
        xaxis_title='Month in 2025',
        yaxis_title='Index Value (Jan 2025 = 100)',
        legend_title='Metric',
        hovermode='x unified',
        height=500
    )
    return fig

# def build_conversion_ratio_chart(ratio_table: pd.DataFrame) -> go.Figure:
#     fig = px.line(
#         ratio_table,
#         x='Month',
#         y='SKUs Per Carton',
#         markers=True,
#         labels={'Month': 'Month in 2025'}
#         )
#     fig.update_layout(hovermode='x unified', height=500)
#     return fig

def build_speed_heatmap(pivot: pd.DataFrame) -> go.Figure:
    """Return a heatmap of cartons/hr by outlet and month."""
    hover_text = pivot.round(2).astype(object).where(pivot.notna(), 'NA')
    all_values = pivot.stack()
    color_min = all_values.quantile(speed_heatmap_low_pct)
    color_max = all_values.quantile(speed_heatmap_high_pct)
    fig = px.imshow(
        pivot,
        color_continuous_scale=speed_heatmap_color_scale,
        zmin=color_min,
        zmax=color_max,
        aspect='auto',
        labels=speed_heatmap_labels,
    )
    fig.update_traces(
        customdata=hover_text.values,
        hovertemplate=(
            "Outlet: %{y}<br>"
            "Month: %{x}<br>"
            "Monthly Speed (Cartons/hr): %{customdata}<extra></extra>"
        ),
        hoverongaps=True,
        xgap=speed_heatmap_xgap,
        ygap=speed_heatmap_ygap,
    )
    fig.update_layout(height=speed_heatmap_height)
    return fig

def build_outlet_volume_line(outlet_data: pd.DataFrame, outlet: str) -> go.Figure:
    """Return cartons (line) and efficiency/packers (bubbles) with synchronized gridlines."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # 1. Left Axis: Total Cartons (Line)
    fig.add_scatter(
        x=outlet_data[month_column],
        y=outlet_data[carton_column],
        name=carton_column,
        mode='lines+markers',
        line=dict(color=volume_line_color, width=volume_line_width),
        secondary_y=False,
        # UPDATED HOVER TEMPLATE (Part 1 of sequence)
        hovertemplate=(
        "No. of Packers (avg): %{customdata:.0f}<br>"
        "Productivity: %{y:.1f} cartons/packer-hour<br>"
        "<extra></extra>"
    ),
    )

    # 2. Right Axis: Efficiency (Y-position) & Packers (Bubble Size)
    bubble_data = outlet_data.dropna(subset=[monthly_efficiency_column])
    fig.add_scatter(
        x=bubble_data[month_column],
        y=bubble_data[monthly_efficiency_column],
        name="Packers (size) & Efficiency (Y)",
        mode='markers',
        customdata=bubble_data[packer_column],
        marker=dict(
            size=bubble_data[packer_column] * bubble_size_multiplier,
            color=volume_packer_color,
            opacity=volume_packer_opacity,
            sizemode='diameter',
            line=dict(color=bubble_border_color, width=bubble_border_width)
        ),
        secondary_y=True,
        cliponaxis=False,
        # UPDATED HOVER TEMPLATE (Part 2 of sequence)
        hovertemplate=(
            "No. of Packers: %{customdata:.0f}<br>"
            "Efficiency: %{y:.1f} cartons/packer-hour<br>"
            "<extra></extra>"
        ),
    )
    # --- CALCULATIONS FOR CLEAN WHOLE NUMBER GRIDLINE ---
    max_cartons = outlet_data[carton_column].max()
    max_eff = bubble_data[monthly_efficiency_column].max() if not bubble_data.empty else 10
    num_intervals = 5
    left_max = math.ceil(max_cartons * 1.1 / 100) * 100
    right_max = math.ceil(max_eff * 1.2 / 5) * 5
    left_dtick = left_max / num_intervals
    right_dtick = right_max / num_intervals
    # 3. Layout
    fig.update_layout(
        title=f"Outlet {outlet}",
        height=volume_line_height,
        margin=dict(l=70, r=100, t=40, b=60),
        # hovermode='x unified',  # <--- CHANGED FROM 'x unified' to 'x' to remove the top-left number
        showlegend=False,
    )
    # 4. X-axis: STRICTLY 2, 4, 6, 8, 10, 12
    # We must use the EXACT string values from your data (e.g., '02', '04') for tickvals
    tick_vals_strings = ['02', '04', '06', '08', '10', '12']
    tick_labels_display = ['2', '4', '6', '8', '10', '12']
    fig.update_xaxes(
        title_text=month_column,
        tickmode='array',
        tickvals=tick_vals_strings,      # Must match the strings in your dataframe exactly
        ticktext=tick_labels_display,    # What the user actually sees
        # Removed 'range' because it conflicts with categorical string axes
    )
    # 5. Y-axes
    fig.update_yaxes(
        title_text="No. of Cartons",
        range=[0, left_max],
        dtick=left_dtick,
        tick0=0,
        tickformat='d',
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Labour Efficiency (Cartons/Packer-Hour)",
        range=[0, right_max],
        dtick=right_dtick,
        tick0=0,
        tickformat='d',
        secondary_y=True,
    )
    return fig

# def colour_consistency(label: str) -> str:
#     """Return CSS that colours a consistency label cell."""
#     colour = consistency_colours.get(label, '')
#     return f'background-color: {colour}; color: black;' if colour else ''

def build_efficiency_bar(table: pd.DataFrame, value_column: str, median_value: float) -> go.Figure:
    """Return a bar chart of efficiency per outlet, highest first."""
    fig = px.bar(table, x=outlet_column, y=value_column)
    fig.update_traces(
        marker_color=efficiency_bar_color,
        hovertemplate="Outlet: %{x}<br>" + value_column + ": %{y:.1f}<extra></extra>",
    )
    fig.add_hline(
        y=median_value, line_dash='dash', line_color='gray',
        annotation_text="Median (all outlets)", annotation_position="top right",
    )
    fig.update_xaxes(
    type='category',
    categoryorder='array',
    categoryarray=table[outlet_column].tolist(),
    tickmode='array',
    tickvals=table[outlet_column].tolist(),      # one label per outlet
    ticktext=table[outlet_column].astype(str).tolist(),
    tickangle=-90,
    tickfont=dict(size=9),
    title_text="Outlet Code",
)
    fig.update_yaxes(title_text=value_column)
    fig.update_layout(height=efficiency_bar_height, margin=efficiency_chart_margin, bargap=0.2)
    return fig

# ==========6. APP==========
st.subheader("2025 at a glance: workload grew through the year")

df = load_data()
df = rename_columns(df)
df = parse_dates(df)
df = convert_hours(df)

# Supportive linkage:index chart per month for sku, carton and pallet (do they move in the same trend, if yes, sku=carton=pallet)
monthly = build_monthly_totals(df)
index_table = build_index_table(monthly)

with st.container(border=True):
    st.write("### SKU, Carton and Pallet Indexes: Monthly % Change from January")
    fig=build_index_chart(index_table)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(index_chart_summary)
    with st.expander("Click to see draft for 'SKU, Carton and Pallet Indexes: Monthly % Change from January'"):
        st.subheader("SKU, Carton and Pallet Index Table")
        st.dataframe(index_table, use_container_width=True, hide_index=True)

monthly = build_monthly_totals(df)
index_table = build_index_table(monthly)
with st.expander("Click to see 'Monthly Totals of SKU, Carton and Pallet Across All Outlets'"):
    st.subheader("Monthly Totals of SKU, Carton and Pallet Across All Outlets")
    st.dataframe(monthly, use_container_width=True, hide_index=True)

# with st.expander("Learn more about the relationship between SKU, carton and pallet"):
#     st.markdown("### Correlation Results")
#     corr_table = correlation_analysis(df)
#     display_table = corr_table.copy()
#     display_table['Significant Level'] = display_table['Significant Level'].map(
#         {True: "Significant", False: "Not significant"}
#     )
#     st.caption(
#         f"Based on all {get_length_of_df(df)} packing records. "
#         "Each comparison pair has one r-value calculated across every record. "
#         "All comparison pair has relatively strong positive r-value, suggesting that  "
#     )
#     st.dataframe(display_table, use_container_width=True, hide_index=True)

# with st.expander("Learn more about the convertion ratio of SKUs to cartons."):
#     ratio_table = add_sku_per_carton(monthly)
#     fig = build_conversion_ratio_chart(ratio_table)
#     st.plotly_chart(fig, use_container_width=True)

st.subheader("Outlet throughput: how quickly each outlet clears cartons")
monthly_speed = build_outlet_monthly_speed(df)
speed_pivot = build_speed_pivot(monthly_speed)
with st.container(border=True):
    st.write(speed_heatmap_header)
    fig = build_speed_heatmap(speed_pivot)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Throughput = speed(cartons/hr) = how many cartons the outlet packs per hour, regardless of team size.")
    with st.expander("Learn more about the average monthly packing speed per outlet in 2025"):
        st.dataframe(monthly_speed.round(2), use_container_width=True, hide_index=True)

st.caption("Throughput shows which outlets handle high volumes, but it does not account for team size. To compare productivity fairly, we use cartons per packer-hour [cartons packed ÷ (hours × packers)] showing how much one packer produces in one hour.")

# consistency_table = build_outlet_consistency(monthly_speed) #whether a fast outlet is also steady
# top_performers = find_consistent_high_performers(consistency_table)
# styled_consistency = (
#     consistency_table.style
#     .map(colour_consistency, subset=[consistency_column])
#     .format({
#         overall_speed_column: "{:.1f}",
#         std_column: "{:.1f}",
#         cv_column: "{:.1f}%",
#     }, na_rep="")
#     .set_properties(**{'border': consistency_grid_style})
# )
# with st.container(border=True):
#     st.write(consistency_header)
#     if top_performers:
#         st.success(
#             f"{len(top_performers)} outlets combine above-median speed with steady monthly "
#             f"performance: {', '.join(map(str, top_performers))}."
#         )
#     else:
#         st.info("No outlet is both above-median in speed and steady.")
#     st.dataframe(
#         styled_consistency,          # styled table, not consistency_table
#         use_container_width=True,
#         hide_index=True,
#         column_config={
#             rank_column: st.column_config.NumberColumn(
#                 rank_column, help="Position by overall speed, fastest first."),
#             overall_speed_column: st.column_config.NumberColumn(
#                 overall_speed_column,
#                 help="Total cartons ÷ total hours across the year."),
#             months_recorded_column: st.column_config.NumberColumn(
#                 months_recorded_column,
#                 help="Months with data. Fewer months means less reliable results."),
#             std_column: st.column_config.NumberColumn(
#                 std_column,
#                 help="Typical distance of a month's speed from the outlet's average."),
#             cv_column: st.column_config.NumberColumn(
#                 cv_column,
#                 help="Std ÷ average monthly speed. Lower means steadier."),
#             consistency_column: st.column_config.TextColumn(
#                 consistency_column,
#                 help="Steady, Moderate or Erratic, based on CV."),
#         },
#     )
#     st.caption(consistency_note)

st.subheader("Beyond speed: how productive is each packer?")

monthly_volume = build_outlet_monthly_volume(df)
outlet_list = sorted(monthly_volume[outlet_column].unique())
with st.container(border=True):
    st.write(volume_line_header)
    columns = st.columns(compare_outlet_count)
    outlet_data_list = []
    selected_outlet_list = []
    # Get all unique months for x-axis synchronization
    all_months = sorted(monthly_volume[month_column].unique())
    # Pass 1: selectbox + chart in each column
    for position, column in enumerate(columns):
        with column:
            selected_outlet = st.selectbox(
                f"Select outlet {position + 1}",
                outlet_list,
                index=min(position, len(outlet_list) - 1),
                key=f"outlet_select_{position}",
            )
            selected_outlet_list.append(selected_outlet)
            outlet_data = get_outlet_monthly_volume(monthly_volume, selected_outlet)
            outlet_data_list.append(outlet_data)
            # Build chart (x-axis settings are already handled inside the function)
            fig = build_outlet_volume_line(outlet_data, selected_outlet)
            st.plotly_chart(fig, use_container_width=True, key=f"outlet_chart_{position}")
    # Shared legend at the bottom
    st.caption(
    "🔵 **Line**: total cartons packed (left axis)  |  "
    "🟠 **Bubbles**: cartons per packer-hour (right axis), size = average no. of packers (rounded down)"
    )
    st.text("The line shows volume, the bubbles show productivity and team size. Look for outlets whose volume rises while productivity holds, which suggests they scaled well. If productivity falls as the team grows, extra headcount isn't adding proportional output.")
    # Pass 2: 2 comparison tables tucked inside an expander
    with st.expander("View Detailed Monthly Comparison Tables"):
        st.caption("Click to expand and see the exact monthly carton and packer numbers for the selected outlets.")
        table_columns = st.columns(compare_outlet_count)
        for position, column in enumerate(table_columns):
            with column:
                st.markdown(f"**Outlet: {selected_outlet_list[position]}**")
                st.dataframe(
                    outlet_data_list[position],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        month_column: st.column_config.TextColumn("Month"),
                        carton_column: st.column_config.NumberColumn(carton_column, format="%d"),
                        packer_column: st.column_config.NumberColumn(packer_column, format="%d"),
                        monthly_efficiency_column: st.column_config.NumberColumn(monthly_efficiency_column, format="%.1f"),
                    }
                )

throughput = build_overall_throughput(monthly_speed)
packer_efficiency = build_packer_efficiency(df)
with st.container(border=True):
    title_slot = st.empty()                      # reserves the space above the toggle
    per_packer = st.toggle(efficiency_toggle_label, value=True)
    title_slot.write(efficiency_header_packer if per_packer else efficiency_header_speed)
    st.caption("With the toggle on, it ranks by labour productivity. With it off, it ranks by outlet throughput.")
    st.caption(efficiency_note_packer if per_packer else efficiency_note_speed)
    efficiency_table, efficiency_column = select_efficiency(throughput, packer_efficiency, per_packer)
    median_value = efficiency_table[efficiency_column].median()   # all outlets, before slicing
    fig = build_efficiency_bar(
        efficiency_table.head(top_30_most_efficient_outlet), efficiency_column, median_value
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        f"Showing the top {top_30_most_efficient_outlet} of {len(efficiency_table)} outlets. "
        "Dashed line = median of all outlets. "
        "High throughput with lower productivity indicates greater reliance on headcount, "
        "while high throughput and productivity indicate greater efficiency."
    )



