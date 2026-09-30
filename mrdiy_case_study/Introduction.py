import streamlit as st

# ==========1. Constants==========
page_title = "Introduction"
page_icon = "👋"

# --- About me (edit these) ---
my_name = "Chong Chi Rui"
my_tagline = "Using the MR.DIY case study, I applied data analysis, forecasting, and visualisation to evaluate outlet performance and support workforce planning decisions."
about_header = "👋 Hi, I'm " + my_name
# about_text = (
#     "I'm [one line on your background, e.g. a business analyst in the making]. "
#     "I like the moment when a confusing spreadsheet turns into a chart that makes people say "
#     "\"ah, that's what's going on.\" This dashboard is my take on a real-world case study, "
#     "built from raw data to final recommendation."
# )
about_facts = [
    ("🛠️ Tools I use", "Python, Pandas, NumPy, Streamlit, Plotly, Excel"),
    # ("💡 What I enjoy", "finding the story and impacts behind the numbers"),
    # ("☕ Outside of work", "[e.g. coffee hunting, badminton, trying new recipes"),
]
# contact_text = "📬 Let's connect: [LinkedIn link] | [Email]"

# --- Case study (as given) ---
goal_header = "Case Study Goal:"
goal_text = (
    "**Please create a simple case study dashboard with the following:**\n\n"
    "- A summary dashboard showing outlet performance in terms of carton packs and pallet packing.\n"
    "- A forecast projection: if we add 20 more outlets, based on current packer manpower, "
    "estimate how many additional staff would be required."
)

# ==========2. App==========
st.set_page_config(
    page_title=page_title,
    page_icon=page_icon,
)

st.header(about_header)
st.caption(my_tagline)
# st.markdown(about_text)

columns = st.columns(len(about_facts))
for column, (label, value) in zip(columns, about_facts):
    with column:
        with st.container(border=True):
            st.markdown(f"**{label}: {value}**")

# st.markdown(contact_text)

st.divider()

st.subheader(goal_header)
with st.container(border=True):
    st.markdown(goal_text)
