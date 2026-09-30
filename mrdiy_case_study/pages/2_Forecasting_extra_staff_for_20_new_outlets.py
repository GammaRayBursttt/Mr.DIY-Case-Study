# ==========1. Import ==========
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import math
from scipy.stats import pearsonr
from plotly.subplots import make_subplots
from pathlib import Path

# ==========2. Constant==========
raw_data_file="packing_test.xlsx"
DATA_PATH = Path(__file__).parent / "packing_test.xlsx"
max_rows=2638
year=2025
hours_per_day=24
df_column_map = {
    'OUTLET CODE':         'Outlet Code',
    'IB DATE':             'IB Date',
    'TOTAL SKU':           'Total SKU',
    'TOTAL CTN PACKED':    'Total CTN Packed',
    'TOTAL PALLET PACKED': 'Total Pallet Packed',
    'TTL HRS':             'Total Hours Used',
    'NO. OF PACKER':       'No. of Packer',
}
hours_column='Total Hours Used'
date_column='IB Date'
packer_column='No. of Packer'
month_column = f'Months in {year}'
month_format = '%m'
outlet_column='Outlet Code'
carton_column='Total CTN Packed'

staffing_chart_title = "Packers Needed for New Outlets: Redeployed vs Recruited, by Scenario"
new_outlet_count = 20
hours_per_packer_year = 2000          # ASSUMPTION: hours one packer works per year (default: about 250 working days × 8 hours per day )
target_min_months = 10                # outlets with fewer months are excluded from the target
# surplus_buffer = 0.10                 # keeps 10% more people than the minimum, so it isn't cut to the bone
profile_cartons_column = 'Yearly Cartons'
profile_productivity_column = 'Cartons per Packer-Hour'
profile_months_column = 'Months Recorded'
scenario_column = 'Planning Scenario'
staffing_scenarios = [
    {'name': 'Efficient',    'target': 'median', 'benchmark_pct': 0.75},   # faster pace, fewest hires
    {'name': 'Standard',     'target': 'median', 'benchmark_pct': 0.50},   # typical pace (the 9.6)
    {'name': 'Conservative', 'target': 'median', 'benchmark_pct': 0.25},   # slower pace, most hires
]
expected_scenario_name = staffing_scenarios[0]['name']   # headline = lowest-hire scenario
staffing_header = f" Forecast: Minimum Hires Needed to Add {new_outlet_count} More Outlets"
staffing_chart_title = "Additional Packers to Hire for New Outlets, by Scenario"
staffing_note = (
    "**How the number is worked out**  \n"
    "1. **Workload:** each new outlet packs the typical monthly cartons of an existing outlet.  \n"
    "2. **Labour needed:** cartons ÷ cartons one packer packs per hour = packer-hours per outlet.  \n"
    "3. **Hires:** packer-hours for all new outlets ÷ hours one packer works per month, rounded up."
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

# ==========4. Calculation==========
def build_outlet_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Return yearly cartons, cartons per packer-hour and months recorded per outlet."""
    data = df[df[hours_column].gt(0) & df[packer_column].gt(0)].copy()
    data['packer_hours'] = data[hours_column] * data[packer_column]
    data[month_column] = data[date_column].dt.strftime(month_format)
    profile = data.groupby(outlet_column).agg(
        cartons=(carton_column, 'sum'),
        packer_hours=('packer_hours', 'sum'),
        months=(month_column, 'nunique'),
    ).reset_index()
    profile[profile_productivity_column] = profile['cartons'] / profile['packer_hours']
    profile = profile.rename(columns={'cartons': profile_cartons_column, 'months': profile_months_column})
    return profile[profile[profile_months_column] >= target_min_months].copy()

def build_outlet_month_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return cartons, packer-hours and avg crew for each outlet-month (valid records only)."""
    data = df[df[hours_column].gt(0) & df[packer_column].gt(0)].copy()
    data['packer_hours'] = data[hours_column] * data[packer_column]
    data[month_column] = data[date_column].dt.strftime(month_format)
    return (
        data.groupby([outlet_column, month_column])
        .agg(cartons=(carton_column, 'sum'),
        packer_hours=('packer_hours', 'sum'),
        packers=(packer_column, 'mean'))
        .reset_index()
    )

def build_workload_benchmarks(df: pd.DataFrame) -> tuple:
    """Return (outlet-month table, outlet profile), both limited to outlets with enough months."""
    profile = build_outlet_profile(df)
    monthly = build_outlet_month_table(df)
    monthly = monthly[monthly[outlet_column].isin(profile[outlet_column])]
    return monthly, profile

def build_part1_reference(df: pd.DataFrame) -> dict:
    """Return the Part 1 numbers the forecast is built on."""
    monthly, profile = build_workload_benchmarks(df)
    return {
        'median_cartons': monthly['cartons'].median(),
        'avg_packer_hours': monthly['packer_hours'].mean(),
        'median_productivity': profile[profile_productivity_column].median(),
    }

def pick_statistic(series: pd.Series, how: str) -> float:
    """Return 'median', 'mean', or a percentile such as 'p75' (a busy month)."""
    if how == 'median':
        return series.median()
    if how == 'mean':
        return series.mean()
    return series.quantile(float(how.lstrip('p')) / 100)

def build_staffing_scenarios(df: pd.DataFrame, new_outlets: int, hours_per_packer: float) -> pd.DataFrame:
    """Return one row per scenario with the packers (hires) needed for the new outlets."""
    monthly, profile = build_workload_benchmarks(df)
    hours_per_packer_month = hours_per_packer / 12
    rows = []
    for scenario in staffing_scenarios:
        monthly_cartons = pick_statistic(monthly['cartons'], scenario['target'])
        benchmark = profile[profile_productivity_column].quantile(scenario['benchmark_pct'])
        hours_per_outlet = monthly_cartons / benchmark                  # packer-hours per outlet-month
        total_hours = new_outlets * hours_per_outlet                    # packer-hours per month
        rows.append({
            scenario_column: scenario['name'],
            'Cartons per Outlet-Month': round(monthly_cartons),
            'Benchmark (cartons/packer-hr)': round(benchmark, 1),
            'Packer-Hours per Outlet-Month': round(hours_per_outlet),
            f'Packer-Hours per Month ({new_outlets} outlets)': round(total_hours),
            'Hires Needed': math.ceil(total_hours / hours_per_packer_month),
        })
    return pd.DataFrame(rows)

def describe_scenario(scenario: dict) -> str:
    pct = round(scenario['benchmark_pct'] * 100)
    if pct > 50:
        return f"fast pace, matching the top {100 - pct}% of outlets"
    if pct == 50:
        return "typical pace, matching the median outlet"
    return f"slow pace, matching the bottom {pct}% of outlets"

# ==========5. Visualization==========
def build_staffing_chart(summary: pd.DataFrame) -> go.Figure:
    """Return one bar per scenario with the number of hires inside the bar."""
    fig = go.Figure()
    fig.add_bar(
        x=summary[scenario_column], y=summary['Hires Needed'],
        marker_color='#1f77b4',
        text=summary['Hires Needed'],
        textposition='inside', insidetextanchor='middle',
        textfont=dict(size=22, color='white'),
    )
    fig.update_layout(
        title=staffing_chart_title, height=350,
        yaxis_title='Packers to hire', xaxis_title=scenario_column,
        margin=dict(l=60, r=30, t=60, b=50),
    )
    return fig

# ==========6. App==========
df = load_data()
df = rename_columns(df)
df = parse_dates(df)
df = convert_hours(df)

st.subheader(staffing_header)

working_days_per_year = 250      # ASSUMPTION: working days per packer per year
shift_hours_per_day = 8          # ASSUMPTION: 4 for part-time packers (default for the input below)
staffing_intro = (
    "The Outlet Performance Summary showed how many cartons an outlet handles per month and how many cartons one packer "
    "packs per hour. Here we use both to size the team for the new outlets. "
    "Every packer needed is counted as a new hire."
)
staffing_scenario_note = (
    "**All 3 scenarios have the same workload but different packing speed:**  \n"
    + "  \n".join(f"**{s['name']}**: {describe_scenario(s)}" for s in staffing_scenarios)
)
st.caption(staffing_intro)
with st.container(border=True):
    ref = build_part1_reference(df)
    m1, m2, m3 = st.columns(3)
    m1.metric("Median cartons per outlet-month", f"{ref['median_cartons']:,.0f}")
    m2.metric("Avg packer-hours per outlet-month", f"{ref['avg_packer_hours']:,.0f}")
    m3.metric("Median labour productivity (cartons per packer-hour)", f"{ref['median_productivity']:.1f}")
    new_outlets = new_outlet_count
    in1, in2 = st.columns(2)
    with in1:
        shift_hours = st.number_input("Shift length (hours per day)", min_value=1.0, max_value=12.0, value=float(shift_hours_per_day), step=0.5)
    with in2:
        work_days = st.number_input("Working days per year", min_value=50, max_value=365, value=working_days_per_year, step=10)
    hours_per_packer = shift_hours * work_days
    st.caption(f"One packer = {hours_per_packer:,.0f} hours per year.")
    staffing_summary = build_staffing_scenarios(df, new_outlets, hours_per_packer)
    base = staffing_summary[staffing_summary[scenario_column] == expected_scenario_name].iloc[0]
    st.success(
        f"Efficient estimate: {new_outlets} new outlets need about "
        f"{int(base[f'Packer-Hours per Month ({new_outlets} outlets)']):,} packer-hours per month, "
        f"so hire about {int(base['Hires Needed'])} packers on a {shift_hours:g}-hour shift. "
        f"Range across scenarios: {int(staffing_summary['Hires Needed'].min())} to "
        f"{int(staffing_summary['Hires Needed'].max())} hires."
    )
    st.caption("Standard and Conservative show how many more hires are needed if new packers work at a slower pace.")
    st.dataframe(staffing_summary, use_container_width=True, hide_index=True)
    st.plotly_chart(build_staffing_chart(staffing_summary), use_container_width=True)
    st.markdown(staffing_scenario_note)
    st.caption(staffing_note)
