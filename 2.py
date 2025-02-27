import streamlit as st
import os
import json
import pandas as pd
import plotly.express as px
from groq import Groq
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def generate_checklist(topic):
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Generate a concise checklist (max 10 items) of key topics for studying {topic}."}],
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        stream=False,
    )
    checklist=chat_completion.choices[0].message.content.split("\n")
    checklist = [item.strip() for item in checklist if item.strip() and not item.lower().startswith("Here's a")]
    checklist.pop(0)
    return checklist

def get_best_youtube_video(query):
    request = youtube.search().list(
        part="snippet",
        maxResults=3,
        q=query,
        type="video",
        order="relevance"
    )
    response = request.execute()
    if response['items']:
        video_id = response['items'][0]['id']['videoId']
        return f"https://www.youtube.com/watch?v={video_id}"
    return None

def generate_youtube_links(checklist):
    youtube_links = {}
    for item in checklist:
        video_link = get_best_youtube_video(item)
        if video_link:
            youtube_links[item] = video_link
    return youtube_links

# Streamlit UI
st.title("Study Preparation App")
topic = st.text_input("Enter the topic you want to study:")

if st.button("Generate Checklist"):
    if topic:
        checklist = generate_checklist(topic)
        youtube_links = generate_youtube_links(checklist)
        
        if checklist:
            st.session_state["checklist"] = checklist
            st.session_state["progress"] = {item: False for item in checklist}
        else:
            st.error("Failed to generate checklist. Try again.")

        if youtube_links:
            st.session_state["youtube_links"] = youtube_links
        else:
            st.session_state["youtube_links"] = {}
    else:
        st.error("Please enter a topic.")

if "checklist" in st.session_state:
    st.subheader("Your Study Checklist")
    for item in st.session_state["checklist"]:
        st.session_state["progress"][item] = st.checkbox(item, st.session_state["progress"].get(item, False), key=item)

    completed = sum(st.session_state["progress"].values())
    total = len(st.session_state["progress"])
    st.progress(completed / total)

    progress_df = pd.DataFrame({"Status": ["Completed", "Remaining"], "Count": [completed, total - completed]})
    fig = px.pie(progress_df, names="Status", values="Count", title="Progress Overview")
    st.plotly_chart(fig)

    st.subheader("Recommended YouTube Videos")
    if "youtube_links" in st.session_state and st.session_state["youtube_links"]:
        for item, link in st.session_state["youtube_links"].items():
            st.markdown(f"**{item}**: [📺 Watch Video]({link})")
    else:
        st.write("No YouTube links available. Try generating again.")