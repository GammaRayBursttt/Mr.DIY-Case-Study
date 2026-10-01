# ==========1. Import ==========
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math
from pathlib import Path

# ==========2. Constant==========
DATA_PATH = Path(__file__).parent / "packing_test.xlsx"
year = 2025
hours_per_day = 24
df_column_map = {
    'OUTLET CODE':         'Outlet Code',
    'IB DATE':             'IB Date',
    'TOTAL SKU':           'Total SKU',
    'TOTAL CTN PACKED':    'Total CTN Packed',
    'TOTAL PALLET PACKED': 'Total Pallet Packed',
    'TTL HRS':             'Total Hours Used',
    'NO. OF PACKER':       'No. of Packer',
}
hours_column = 'Total Hours Used'
date_column = 'IB Date'
packer_column = 'No. of Packer'
month_column = f'Months in {year}'
month_format = '%m'
outlet_column = 'Outlet Code'
carton_column = 'Total CTN Packed'

new_outlet_count = 20                 # defined before anything that uses it
target_min_months = 10                # outlets with fewer months are excluded
shift_hours_per_day = 8               # ASSUMPTION: 4 for part-time packers
working_days_per_month = 22           # ASSUMPTION: weekdays only

profile_months_column = 'Months Recorded'
scenario_column = 'Planning Scenario'
hours_scenarios = [('Light', 0.25), ('Typical', 0.50), ('Heavy', 0.75)]   # percentile of outlet workload
expected_scenario_name = 'Typical'
staff_col = f'Additional Staff ({new_outlet_count} outlets)'
hours_total_col = f'Packer-Hours per Month ({new_outlet_count} outlets)'

staffing_header = f"Forecast: Additional Staff Needed for {new_outlet_count} More Outlets"
staffing_chart_title = "Additional Staff (People) for New Outlets, by Scenario"
staffing_intro = (
    "Based on current packing workload: each new outlet is assumed to need the same packer-hours "
    "as an existing outlet. Those hours are converted into the number of people needed, "
    "given how many hours one person works per month."
)
staffing_scenario_note = (
    "**Scenarios change the packing workload per outlet:**  \n"
    "**Light**: workload like the lighter outlets (25th percentile)  \n"
    "**Typical**: workload like the median outlet  \n"
    "**Heavy**: workload like the busier outlets (75th percentile)"
)
staffing_note = (
    "**How the number is worked out**  \n"
    "1. **Workload:** median packer-hours per month at an existing outlet.  \n"
    "2. **Total labour:** packer-hours per outlet × number of new outlets.  \n"
    "3. **People:** total packer-hours ÷ hours one person works per month "
    "(shift hours × working days), rounded up.  \n"
    "Assumes the work can be spread across the people hired. If every outlet needs its own "
    "dedicated packer, the real headcount would be higher."
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
    """Return outlets with enough months of valid records."""
    data = df[df[hours_column].gt(0) & df[packer_column].gt(0)].copy()
    data[month_column] = data[date_column].dt.strftime(month_format)
    profile = data.groupby(outlet_column).agg(
        months=(month_column, 'nunique'),
    ).reset_index()
    profile = profile.rename(columns={'months': profile_months_column})
    return profile[profile[profile_months_column] >= target_min_months].copy()

def build_outlet_month_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return cartons and packer-hours for each outlet-month (valid records only)."""
    data = df[df[hours_column].gt(0) & df[packer_column].gt(0)].copy()
    data['packer_hours'] = data[hours_column] * data[packer_column]
    data[month_column] = data[date_column].dt.strftime(month_format)
    return (
        data.groupby([outlet_column, month_column])
        .agg(cartons=(carton_column, 'sum'), packer_hours=('packer_hours', 'sum'))
        .reset_index()
    )

def build_reference(df: pd.DataFrame) -> dict:
    """Return workload benchmarks per existing outlet."""
    valid = build_outlet_profile(df)[outlet_column]
    monthly = build_outlet_month_table(df)
    monthly = monthly[monthly[outlet_column].isin(valid)]
    hours_by_outlet = monthly.groupby(outlet_column)['packer_hours'].median()
    return {
        'hours_by_outlet': hours_by_outlet,                                           # median packer-hours per month, per outlet
        'hours_per_outlet': hours_by_outlet.median(),
        'cartons_per_outlet': monthly.groupby(outlet_column)['cartons'].median().median(),
        'avg_cartons_per_month': monthly['cartons'].mean(),
        'avg_cartons_year': monthly.groupby(outlet_column)['cartons'].sum().mean(),
    }

def build_staffing_scenarios(ref: dict, new_outlets: int, hours_per_person_month: float) -> pd.DataFrame:
    """Packer-hours per outlet -> total packer-hours -> people needed, per scenario."""
    rows = []
    for name, pct in hours_scenarios:
        hours_per_outlet = ref['hours_by_outlet'].quantile(pct)
        total_hours = hours_per_outlet * new_outlets
        rows.append({
            scenario_column: name,
            'Packer-Hours per Outlet per Month': round(hours_per_outlet),
            hours_total_col: round(total_hours),
            'Full-Time Equivalent': round(total_hours / hours_per_person_month, 1),
            staff_col: math.ceil(total_hours / hours_per_person_month),
        })
    return pd.DataFrame(rows)

# ==========5. Visualization==========
def build_staffing_chart(summary: pd.DataFrame) -> go.Figure:
    """Return one bar per scenario with the number of additional staff inside the bar."""
    fig = go.Figure()
    fig.add_bar(
        x=summary[scenario_column], y=summary[staff_col],
        marker_color='#1f77b4',
        text=summary[staff_col],
        textposition='inside', insidetextanchor='middle',
        textfont=dict(size=22, color='white'),
    )
    fig.update_layout(
        title=staffing_chart_title, height=350,
        yaxis_title='Additional staff (people)', xaxis_title=scenario_column,
        margin=dict(l=60, r=30, t=60, b=50),
    )
    return fig

# ==========6. App==========
df = load_data()
df = rename_columns(df)
df = parse_dates(df)
df = convert_hours(df)

st.subheader(staffing_header)
st.caption(staffing_intro)

with st.container(border=True):
    ref = build_reference(df)

    m1, m2 = st.columns(2)
    m1.metric("Median packer-hours per outlet per month", f"{ref['hours_per_outlet']:,.0f}",
              help="Packing labour time: hours × number of packers, summed per outlet per month, then the median across outlets.")
    m2.metric("Median cartons per outlet per month", f"{ref['cartons_per_outlet']:,.0f}")
    
    m3, m4 = st.columns(2)
    m3.metric("Average cartons per outlet per month", f"{ref['avg_cartons_per_month']:,.0f}")
    m4.metric(f"Average cartons per outlet in {year}", f"{ref['avg_cartons_year']:,.0f}")

    in1, in2 = st.columns(2)
    with in1:
        shift_hours = st.number_input("Shift length (hours per day)", min_value=1.0, max_value=12.0,
                                      value=float(shift_hours_per_day), step=0.5)
    with in2:
        work_days = st.number_input("Working days per person per month", min_value=1, max_value=31,
                                    value=working_days_per_month, step=1)
    hours_per_person_month = shift_hours * work_days
    st.caption(f"One person = {hours_per_person_month:,.0f} hours per month.")

    staffing_summary = build_staffing_scenarios(ref, new_outlet_count, hours_per_person_month)
    base = staffing_summary[staffing_summary[scenario_column] == expected_scenario_name].iloc[0]
    st.success(
        f"{new_outlet_count} new outlets need about {int(base[hours_total_col]):,} packer-hours per month. "
        f"At {hours_per_person_month:,.0f} hours per person per month, that is "
        f"**{int(base[staff_col])} additional staff** "
        f"(range {int(staffing_summary[staff_col].min())} to {int(staffing_summary[staff_col].max())})."
    )
    st.dataframe(staffing_summary, use_container_width=True, hide_index=True)
    st.plotly_chart(build_staffing_chart(staffing_summary), use_container_width=True)
    st.markdown(staffing_scenario_note)
    st.caption(staffing_note)
