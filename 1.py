import streamlit as st
import os
import json
import pandas as pd
import plotly.express as px
from groq import Groq

# Initialize Groq Client
client = Groq(api_key="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")

def generate_checklist(topic):
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Generate a concise checklist (max 10 items) of key topics from beginner to advanced for studying {topic}."}],
        model="llama-3.3-70b-versatile",
        max_tokens=300,
        stream=False,
    )
    checklist=chat_completion.choices[0].message.content.split("\n")
    checklist = [item.strip() for item in checklist if item.strip() and not item.lower().startswith("here's a")]
    checklist.pop()
    return checklist

def generate_youtube_links(topic):
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Provide the most relevant YouTube video links for learning about {topic}."}],
        model="llama-3.3-70b-versatile",
        max_tokens=200,
        stream=False,
    )
    links = chat_completion.choices[0].message.content.split("\n")
    print(links)
    return [link.strip() for link in links if link.startswith("http")]
# Streamlit UI
st.title("Study Preparation App")
topic = st.text_input("Enter the topic you want to study:")

if st.button("Generate Checklist"):
    if topic:
        checklist = generate_checklist(topic)
        youtube_links = generate_youtube_links(topic)
        
        if checklist:
            st.session_state["checklist"] = checklist
            st.session_state["progress"] = {item: False for item in checklist}
        else:
            st.error("Failed to generate checklist. Try again.")

        if youtube_links:
            st.session_state["youtube_links"] = youtube_links
        else:
            st.session_state["youtube_links"] = []
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
        for link in st.session_state["youtube_links"]:
            st.markdown(f"[📺 Watch Video]({link})")
    else:
        st.write("No YouTube links available. Try generating again.")

