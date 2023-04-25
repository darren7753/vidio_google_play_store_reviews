# Import libraries
import os
import numpy as np
import pandas as pd
from pymongo import MongoClient
from google_play_scraper import app
import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Change the page settings
st.set_page_config(
    page_title="Vidio Reviews Dashboard",
    layout="wide"
)

# Reduce space at the top
reduce_header_height_style = """
    <style>
        div.block-container {padding-top:1rem;}
        div.block-container {padding-bottom:1rem;}
    </style>
"""
st.markdown(reduce_header_height_style, unsafe_allow_html=True)

# Remove red line at the top and "Made with Streamlit" writing at the bottom
hide_decoration_bar_style = """
    <style>
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

# Create a connection to MongoDB
@st.cache_resource
def init_connection():
    return MongoClient(
        os.environ["MONGODB_URL"],
        serverSelectionTimeoutMS=300000
    )

client = init_connection()

# Title
st.markdown(
    """
    <div style='display: flex; align-items: center; justify-content: center;'>
        <img src='https://raw.githubusercontent.com/darren7753/vidio_google_play_store_reviews/main/Logo_Vidio.png' height='45px' style='margin-right: -13px;'/>
        <h1 style='text-align: center; color: #ed203f;'>Reviews Dashboard</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Insert timestamp
@st.cache_data(ttl=600)
def load_timestamp():
    db = client["vidio"]
    collection = db["current_timestamp"]
    doc = collection.find_one()
    return doc["timestamp"]

timestamp = load_timestamp()
st.markdown(f"<p style='text-align: center;'>Last updated on {timestamp}</p>", unsafe_allow_html=True)

# Create filters
st.markdown("<br>", unsafe_allow_html=True)
lnk = '<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.12.1/css/all.css" crossorigin="anonymous">'

col1, col2, col3 = st.columns(3)
with col1:
    period = st.selectbox(
        label="Period",
        options=["day", "week", "month"]
    )

    st.write(
        f"""
        <style>
            .st-bp .st-ax {{
                box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.15);
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

end_date = datetime.date.today()

if period == "day":
    start_date = end_date - datetime.timedelta(days=30)
    resample = "D"
elif period == "week":
    start_date = end_date - datetime.timedelta(weeks=12)
    resample = "W"
else:
    start_date = end_date - relativedelta(months=6)
    resample = "M"

with col2:
    filter_start_date = st.date_input(
        label="Start Date",
        value=start_date
    )

with col3:
    filter_end_date = st.date_input(
        label="End Date",
        value=end_date
    )

end_date_time = datetime.datetime.combine(filter_end_date, datetime.time(23, 59, 59))
start_date_time = datetime.datetime.combine(filter_start_date, datetime.time(0, 0, 0))

# Read Me
st.markdown(lnk + "<h2><i class='fab fa-readme' style='font-size: 30px; color: #ed203f;'></i>&nbsp;Read Me</h2>", unsafe_allow_html=True)
st.markdown("""
    <ul>
        <li>This dashboard is updated daily at around 9 AM local time in Asia/Jakarta.</li>
        <li>The data shown on the dashboard is sourced from Indonesian reviews of the Vidio app on the Google Play Store, specifically from users located in Indonesia.</li>
        <li>By default, this dashboard displays data from the last 30 days when <i>day</i> is selected, from the last 12 weeks when <i>week</i> is selected, and from the last 6 months when <i>month</i> is selected.</li>
        <li>To view the full code for this dashboard, please visit this <a href="https://github.com/darren7753/vidio_google_play_store_reviews">GitHub Repository</a>.</li>
    </ul>
""", unsafe_allow_html=True)

# Load the data
@st.cache_data(ttl=1)
def load_data():
    db = client["vidio"]
    collection = db["google_play_store_reviews"]
    query = {"at": {
        "$gte": start_date_time,
        "$lte": end_date_time + datetime.timedelta(days=1)
    }}
    return pd.DataFrame(list(collection.find(query)))

df = load_data()
df = df.drop_duplicates()
df = df.drop("_id", axis=1)
df = df.replace("empty", np.nan)
df = df.sort_values("at", ascending=False)
df = df.reset_index(drop=True)
df.index += 1

# Create score cards
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("<h4>Average Rating</h4>", unsafe_allow_html=True)
    wch_colour_box = (255, 255, 255)
    wch_colour_font = (0, 0, 0)
    fontsize = 50
    valign = "left"
    iconname = "fas fa-star"
    i = round(df["score"].mean(), 2)

    htmlstr = f"""
        <p style='background-color: rgb(
            {wch_colour_box[0]}, 
            {wch_colour_box[1]}, 
            {wch_colour_box[2]}, 0.75
        ); 
        color: rgb(
            {wch_colour_font[0]}, 
            {wch_colour_font[1]}, 
            {wch_colour_font[2]}, 0.75
        ); 
        font-size: {fontsize}px;    
        border-radius: 7px; 
        padding-top: 40px; 
        padding-bottom: 40px; 
        line-height:25px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);'>
        <i class='{iconname}' style='font-size: 40px; color: #ed203f;'></i>&nbsp;{i}</p>
    """

    st.markdown(lnk + htmlstr, unsafe_allow_html=True)

with col2:
    st.markdown("<h4>Total Reviews</h4>", unsafe_allow_html=True)
    wch_colour_box = (255, 255, 255)
    wch_colour_font = (0, 0, 0)
    fontsize = 50
    valign = "left"
    iconname = "fas fa-comments"
    i = f"{len(df):,}"

    htmlstr = f"""
        <p style='background-color: rgb(
            {wch_colour_box[0]}, 
            {wch_colour_box[1]}, 
            {wch_colour_box[2]}, 0.75
        ); 
        color: rgb(
            {wch_colour_font[0]}, 
            {wch_colour_font[1]}, 
            {wch_colour_font[2]}, 0.75
        ); 
        font-size: {fontsize}px;    
        border-radius: 7px; 
        padding-top: 40px; 
        padding-bottom: 40px; 
        line-height:25px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);'>
        <i class='{iconname}' style='font-size: 40px; color: #ed203f;'></i>&nbsp;{i}</p>
    """
    
    st.markdown(lnk + htmlstr, unsafe_allow_html=True)

with col3:
    st.markdown("<h4>Total Downloads Since Release</h4>", unsafe_allow_html=True)
    wch_colour_box = (255, 255, 255)
    wch_colour_font = (0, 0, 0)
    fontsize = 50
    valign = "left"
    iconname = "fas fa-download"
    i = app('com.vidio.android', lang="id", country="id")["installs"].replace(".", ",")

    htmlstr = f"""
        <p style='background-color: rgb(
            {wch_colour_box[0]}, 
            {wch_colour_box[1]}, 
            {wch_colour_box[2]}, 0.75
        ); 
        color: rgb(
            {wch_colour_font[0]}, 
            {wch_colour_font[1]}, 
            {wch_colour_font[2]}, 0.75
        ); 
        font-size: {fontsize}px;    
        border-radius: 7px; 
        padding-top: 40px; 
        padding-bottom: 40px; 
        line-height:25px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);'>
        <i class='{iconname}' style='font-size: 40px; color: #ed203f;'></i>&nbsp;{i}</p>
    """
    
    st.markdown(lnk + htmlstr, unsafe_allow_html=True)

# Charts
st.markdown(lnk + "<h2><i class='fas fa-chart-bar' style='font-size: 30px; color: #ed203f;'></i>&nbsp;Charts</h2>", unsafe_allow_html=True)

# Graphic showing number of reviews and average rating
st.markdown("<h4>Number of Reviews and Average Rating</h4>", unsafe_allow_html=True)

df_sliced = df.copy()
df_sliced = df_sliced.set_index("at")

def sentiment(x):
    if x > 3:
        return "Positive"
    elif x == 3:
        return "Neutral"
    else:
        return "Negative"
df_sliced["sentiment"] = df_sliced["score"].apply(sentiment)

df1 = df_sliced.resample(resample).agg({"score":"mean", "content_original":"count"}).fillna(0)
df1.columns = ["mean", "count"]
df1["Count Growth"] = df1["count"].pct_change().fillna(0) * 100
df1["Mean Growth"] = df1["mean"].pct_change().fillna(0) * 100

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Bar(
        x=df1.index,
        y=df1["count"],
        name="Count",
        marker_color="#0088cc",
        customdata=df1["Count Growth"]
    ),
    secondary_y=False
)
fig.add_trace(
    go.Scatter(
        x=df1.index,
        y=df1["mean"],
        mode="lines+markers",
        name="Average",
        line=dict(color="#fc576c", width=2.5),
        customdata=df1["Mean Growth"]
    ),
    secondary_y=True
)
fig.update_layout(
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    height=350,
    margin={"r":0, "l":0, "t":0, "b":0},
    yaxis2=dict(showgrid=False)
)
fig.update_traces(
    hovertemplate="Date: %{x|%b %d, %Y}<br>" + "Value: %{y}<br>" + "Growth: %{customdata:.2f}%"
)
st.plotly_chart(fig,use_container_width=True)

col1, col2 = st.columns([2, 1])

# Graphic showing number of reviews based on sentiment
with col1:
    st.markdown("<h4>Number of Reviews Based on Sentiment</h4>", unsafe_allow_html=True)

    positive = df_sliced[df_sliced["sentiment"] == "Positive"][["sentiment"]].resample(resample).apply(lambda x: x.value_counts())
    neutral = df_sliced[df_sliced["sentiment"] == "Neutral"][["sentiment"]].resample(resample).apply(lambda x: x.value_counts())
    negative = df_sliced[df_sliced["sentiment"] == "Negative"][["sentiment"]].resample(resample).apply(lambda x: x.value_counts())

    df2 = pd.concat([positive, neutral, negative], axis=1, ignore_index=True).fillna(0)
    df2.columns = ["Positive", "Neutral", "Negative"]

    df2["Positive Growth"] = df2["Positive"].pct_change().fillna(0) * 100
    df2["Neutral Growth"] = df2["Neutral"].pct_change().fillna(0) * 100
    df2["Negative Growth"] = df2["Negative"].pct_change().fillna(0) * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df2.index,
        y=df2.Positive,
        mode="lines+markers",
        name="Positive",
        line=dict(color="#12b95c"),
        customdata=df2["Positive Growth"]
    ))
    fig.add_trace(go.Scatter(
        x=df2.index,
        y=df2.Neutral,
        mode="lines+markers",
        name="Neutral",
        line=dict(color="#feac00"),
        customdata=df2["Neutral Growth"]
    ))
    fig.add_trace(go.Scatter(
        x=df2.index,
        y=df2.Negative,
        mode="lines+markers",
        name="Negative",
        line=dict(color="#fc576c"),
        customdata=df2["Negative Growth"]
    ))
    fig.update_traces(
        hovertemplate="Date: %{x|%b %d, %Y}<br>" + "Value: %{y}<br>" + "Growth: %{customdata:.2f}%"
    )
    fig.update_layout(
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        height=350,
        margin={"r":0, "l":0, "t":0, "b":0},
    )
    st.plotly_chart(fig,use_container_width=True)

# Graphic showing percentages of each sentiment category
with col2:
    st.markdown("<h4>Percentages for Each Sentiment Category</h4>", unsafe_allow_html=True)

    count_positive = len(df_sliced[df_sliced["sentiment"] == "Positive"])
    count_neutral = len(df_sliced[df_sliced["sentiment"] == "Neutral"])
    count_negative = len(df_sliced[df_sliced["sentiment"] == "Negative"])

    fig = go.Figure(go.Pie(
        labels=["Positive", "Neutral", "Negative"],
        values=[count_positive, count_neutral, count_negative],
        hole=0.3,
        marker=dict(colors=["#12b95c","#feac00","#fc576c"]),
        text=["Positive", "Neutral", "Negative"],
    ))
    fig.update_traces(
        hoverinfo="label+percent+value"
    )
    fig.update_layout(
        showlegend=False,
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        height=350,
        margin={"r":0, "l":0, "t":40, "b":40},
    )
    st.plotly_chart(fig,use_container_width=True)

# Topic Modeling
st.markdown(lnk + "<h2><i class='fas fa-pen' style='font-size: 30px; color: #ed203f;'></i>&nbsp;Topic Modeling</h2>", unsafe_allow_html=True)

st.write("Our topic modeling feature uses the Latent Dirichlet Allocation (LDA) model to identify relevant topics in neutral to negative reviews with scores of 3 or less. However, there is a possibility of misclassification. Therefore, we continuously work to refine and enhance our model.")

col1, col2 = st.columns(2)
with col1:
    st.write("Select one of the following options to view the reviews in the desired language. All translations are performed using the GPT-3.5 Turbo model.")

    st.write("<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: center;} </style>", unsafe_allow_html=True)
    choose = st.radio(
        label="label",
        options=["Indonesian", "Formal Indonesian", "English"],
        label_visibility="collapsed"
    )

    if choose == "Indonesian":
        content_column = "content_original"
    elif choose == "Formal Indonesian":
        content_column = "content_formal_indonesian"
    else:
        content_column = "content_english"

df_topic_1 = df_sliced[df_sliced["topic"] == "Bad Application"][[content_column, "score"]]
df_topic_2 = df_sliced[df_sliced["topic"] == "Package"][[content_column, "score"]]
df_topic_3 = df_sliced[df_sliced["topic"] == "Advertisement"][[content_column, "score"]]
df_topic_4 = df_sliced[df_sliced["topic"] == "Watching Experience"][[content_column, "score"]]

with col2:
    st.write("Slide to choose the number of rows to display. Please keep in mind that choosing a higher number may increase the system load.")

    if max([len(df_topic_1), len(df_topic_2), len(df_topic_3), len(df_topic_4)]) < 1000:
        slider_value = max([len(df_topic_1), len(df_topic_2), len(df_topic_3), len(df_topic_4)])
    else:
        slider_value = 1000

    n_rows = st.slider(
        label="label",
        min_value=1,
        max_value=max([len(df_topic_1), len(df_topic_2), len(df_topic_3), len(df_topic_4)]),
        value=slider_value,
        label_visibility="collapsed"
    )

col1, col2 = st.columns(2)
with col1:
    pct = len(df_topic_1) / sum([len(df_topic_1), len(df_topic_2), len(df_topic_3), len(df_topic_4)]) * 100
    st.markdown(f"<h4>Bad Application ({round(pct, 2)}%)</h4>", unsafe_allow_html=True)
    st.dataframe(df_topic_1.head(n_rows), use_container_width=True)
with col2:
    pct = len(df_topic_2) / sum([len(df_topic_1), len(df_topic_2), len(df_topic_3), len(df_topic_4)]) * 100
    st.markdown(f"<h4>Package ({round(pct, 2)}%)</h4>", unsafe_allow_html=True)
    st.dataframe(df_topic_2.head(n_rows), use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    pct = len(df_topic_3) / sum([len(df_topic_1), len(df_topic_2), len(df_topic_3), len(df_topic_4)]) * 100
    st.markdown(f"<h4>Advertisement ({round(pct, 2)}%)</h4>", unsafe_allow_html=True)
    st.dataframe(df_topic_3.head(n_rows), use_container_width=True)
with col2:
    pct = len(df_topic_4) / sum([len(df_topic_1), len(df_topic_2), len(df_topic_3), len(df_topic_4)]) * 100
    st.markdown(f"<h4>Watching Experience ({round(pct, 2)}%)</h4>", unsafe_allow_html=True)
    st.dataframe(df_topic_4.head(n_rows), use_container_width=True)
    
# Write credit
st.markdown(lnk + """
    <br>
    <p>Made by <b>Mathew Darren Kusuma</b></p>
    <a href='https://github.com/darren7753'><i class='fab fa-github' style='font-size: 30px; color: #ed203f;'></i></a>&nbsp;
    <a href='https://www.linkedin.com/in/mathewdarren/'><i class='fab fa-linkedin' style='font-size: 30px; color: #ed203f;'></i></a>&nbsp;
    <a href='https://www.instagram.com/darren_matthew_/'><i class='fab fa-instagram' style='font-size: 30px; color: #ed203f;'></i></a>
""", unsafe_allow_html=True)