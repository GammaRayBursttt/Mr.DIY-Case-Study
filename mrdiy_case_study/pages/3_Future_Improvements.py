import streamlit as st


# ==========1. Constants==========
page_title = "Future Improvements"

improvements = [
    {
        'title': "1. Machine learning forecasting model",
        'summary': "Replace fixed benchmarks with a model that learns from historical data.",
        'why': (
            "The current forecast assumes every new outlet behaves like the typical existing one. "
            "Outlets differ, so a single median hides a lot of variation. A model can capture "
            "patterns such as the Q4 peak and give a forecast with a range instead of three fixed scenarios."
        ),
    },
    {
        'title': "2. Consider redeployment before recruiting",
        'summary': "Check for spare packers at existing outlets before hiring.",
        'why': (
            "Redeployment is usually faster and cheaper than recruiting. It avoids hiring and "
            "training costs, and the packers already know the work."
        ),
    },
    {
        'title': "3. Reduce uncertainty: track packer IDs and real headcount",
        'summary': "Record who packed, not just how many packed.",
        'why': (
            "The current data only has crew size per packing record, which is used as a proxy for headcount. "
            "With packer IDs, headcount becomes the number of unique packers per outlet, and hours become "
            "measured instead of assumed, so the hires estimate rests on actual people."
        ),
    },
]

page_intro = (
    "The current forecast is a **floor estimate**. It assumes typical workload and packing speed, "
    "counts every packer needed as a new hire, and treats crew size as headcount. "
    f"These {len(improvements)} improvements would make it more accurate and more realistic."
)

# ==========2. App==========
st.header(page_title)
st.caption(page_intro)

for item in improvements:
    with st.container(border=True):
        st.subheader(item['title'])
        st.markdown(f"*{item['summary']}*")
        st.markdown(f"**Why it helps:** {item['why']}")