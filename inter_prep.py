import streamlit as st
import requests
from pytube import Search

# Load API Key securely (Replace "your-groq-api-key" with st.secrets or env variable)
GROQ_API_KEY = "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"

# Function to generate quiz questions using Groq API
def generate_question(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"  # Corrected Groq API URL
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",  # Groq's available model
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.json()}"

# Streamlit App
st.title("Study Preparation Assistant")
st.write("Welcome! Let's create your study plan.")

# Session state for storing quiz questions
if 'quiz_questions' not in st.session_state:
    st.session_state.quiz_questions = []

# User Inputs
topic = st.text_input("What topic do you want to study?")
difficulty = st.selectbox("Select difficulty level", ["Beginner", "Intermediate", "Advanced"])

# Generate quiz questions
if st.button("Generate Quiz Questions"):
    st.session_state.quiz_questions = []  # Reset previous questions
    for i in range(3):  # Generate 3 quiz questions
        question = generate_question(f"Generate a {difficulty} level quiz question on {topic}.")
        st.session_state.quiz_questions.append(question)

# Display quiz questions
if st.session_state.quiz_questions:
    st.subheader("Your Quiz")
    for i, question in enumerate(st.session_state.quiz_questions):
        st.write(f"**Q{i+1}:** {question}")
        st.text_input(f"Your Answer for Q{i+1}", key=f"answer_{i}")

# YouTube Video Suggestions
if st.button("Get YouTube Video Suggestions"):
    st.subheader("YouTube Video Suggestions")
    search = Search(f"{topic} {difficulty} tutorial")
    for video in search.results[:5]:
        st.write(f"[{video.title}]({video.watch_url})")

# Function to generate quiz questions using Groq API

