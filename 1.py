import streamlit as st
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
from googleapiclient.discovery import build
from dotenv import load_dotenv
import random
import datetime
from datetime import datetime, timedelta
import time

# Load environment variables
load_dotenv()

# Initialize clients
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Page configuration
st.set_page_config(
    page_title="StudyHub - Smart Learning Platform",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .study-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
        transition: transform 0.3s ease;
    }
    
    .study-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .study-card.completed {
        border-left-color: #2196F3;
        background: #f8f9fa;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
    }
    
    .quiz-question {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #007bff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state - FIXED VERSION
def initialize_session_state():
    """Initialize all session state variables with proper defaults"""
    defaults = {
        "checklist": [],
        "progress": {},
        "topic": "",
        "show_quiz": False,
        "youtube_links": {},
        "user_points": 0,
        "badges": [],
        "study_streak": 0,
        "last_study_date": None,
        "performance_history": [],
        "quiz_scores": [],
        "study_schedule": {},
        "learning_goals": {},
        "resource_bookmarks": [],
        "study_time_log": [],
        "difficulty_level": "Medium",
        "quiz": None,
        "answers": {},
        "submitted": False,
        "show_analytics": False,
        "current_page": "dashboard"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Checklist Functions
def generate_checklist(topic):
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Generate a comprehensive checklist (8-12 items) of key topics for studying {topic}. Make each item specific and actionable."}],
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            stream=False,
        )
        
        checklist = chat_completion.choices[0].message.content.split("\n")
        checklist = [item.strip().lstrip("0123456789.-* ") for item in checklist if item.strip() and not item.lower().startswith("here's")]
        return [item for item in checklist if len(item) > 10][:10]
    except Exception as e:
        st.error(f"Error generating checklist: {str(e)}")
        return []

def get_best_youtube_video(query):
    try:
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
    except Exception as e:
        st.error(f"Error fetching YouTube video: {str(e)}")
        return None

def generate_youtube_links(checklist):
    youtube_links = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, item in enumerate(checklist):
        status_text.text(f"Finding videos for: {item}")
        video_link = get_best_youtube_video(item)
        if video_link:
            youtube_links[item] = video_link
        progress_bar.progress((i + 1) / len(checklist))
        time.sleep(0.1)
    
    status_text.text("Video search complete!")
    return youtube_links

# Quiz Functions - FIXED VERSION
def generate_quiz_question(topic, checklist_item, difficulty):
    try:
        prompt = f"""Create a {difficulty}-difficulty multiple choice question about '{checklist_item}' in the context of {topic}. 
        Make it educational and relevant. Return in this exact format:
        Question: [question text]
        A) [option 1]
        B) [option 2]
        C) [option 3]
        D) [option 4]
        Correct: [correct option letter]"""
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            max_tokens=500,
            stream=False,
        )
        
        response = chat_completion.choices[0].message.content.split("\n")
        question = response[0].replace("Question: ", "")
        options = [line[3:] for line in response[1:5] if line.strip()]
        
        # Find correct answer
        correct_line = [line for line in response if line.startswith("Correct:")]
        if correct_line:
            correct_letter = correct_line[0].split(":")[1].strip()
            correct_index = ord(correct_letter.upper()) - ord('A')
            if 0 <= correct_index < len(options):
                correct_answer = options[correct_index]
            else:
                correct_answer = options[0]
        else:
            correct_answer = options[0]
        
        return question, options, correct_answer
    except Exception as e:
        st.error(f"Error generating quiz question: {str(e)}")
        return "Sample question", ["A", "B", "C", "D"], "A"

def generate_quiz(topic, checklist, difficulty, num_questions=5):
    questions = []
    random_items = random.sample(checklist, min(num_questions, len(checklist)))
    
    for item in random_items:
        q, opts, correct = generate_quiz_question(topic, item, difficulty)
        questions.append({
            "question": q,
            "options": opts,
            "correct": correct,
            "topic": item
        })
    
    return questions

# Quiz Center - FIXED VERSION
def quiz_center():
    st.subheader("🎯 Quiz Center")
    
    if not st.session_state["checklist"]:
        st.info("📝 Please generate a study checklist first to take quizzes!")
        return
    
    # Quiz configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        difficulty = st.selectbox(
            "Select Quiz Difficulty",
            ["Easy", "Medium", "Hard"],
            index=1,
            key="quiz_difficulty"
        )
    
    with col2:
        num_questions = st.selectbox(
            "Number of Questions",
            [3, 5, 7, 10],
            index=1
        )
    
    with col3:
        quiz_type = st.selectbox(
            "Quiz Type",
            ["Random Topics", "Incomplete Topics", "All Topics"]
        )
    
    # Generate quiz button
    if st.button("🎯 Generate Quiz", type="primary"):
        if quiz_type == "Incomplete Topics":
            available_topics = [topic for topic, completed in st.session_state["progress"].items() if not completed]
        else:
            available_topics = st.session_state["checklist"]
        
        if available_topics:
            st.session_state["show_quiz"] = True
            st.session_state["quiz"] = generate_quiz(
                st.session_state["topic"],
                available_topics,
                difficulty,
                num_questions
            )
            # FIXED: Properly initialize answers dictionary
            st.session_state["answers"] = {}
            st.session_state["submitted"] = False
            st.session_state["difficulty_level"] = difficulty
            st.rerun()
        else:
            st.warning("No topics available for this quiz type!")
    
    # Display quiz
    if st.session_state.get("show_quiz", False):
        display_quiz()

# Quiz Display - FIXED VERSION
def display_quiz():
    st.subheader(f"🎯 Quiz: {st.session_state['topic']} ({st.session_state.get('difficulty_level', 'Medium')} Level)")
    
    if not st.session_state.get("quiz"):
        st.error("No quiz data available. Please generate a quiz first.")
        return
    
    quiz = st.session_state["quiz"]
    
    # FIXED: Ensure answers dictionary is initialized
    if "answers" not in st.session_state:
        st.session_state["answers"] = {}
    
    # Quiz form with proper submit button
    with st.form(key="quiz_form"):
        for i, q in enumerate(quiz, 1):
            st.markdown(f"""
            <div class="quiz-question">
                <h4>Question {i}: {q['question']}</h4>
                <p><small>Topic: {q.get('topic', 'General')}</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            # FIXED: Use form widget keys and handle initialization properly
            answer = st.radio(
                f"Select your answer for Question {i}:",
                q["options"],
                index=None,
                key=f"quiz_answer_{i}"
            )
            
            # Store answer in session state
            if answer is not None:
                st.session_state["answers"][i] = answer
            
            st.markdown("---")
        
        # FIXED: Proper form submit button
        submitted = st.form_submit_button("Submit Quiz", type="primary")
        
        if submitted:
            # Check if all questions are answered
            answered_questions = len([k for k in st.session_state["answers"].keys() if st.session_state["answers"][k] is not None])
            
            if answered_questions == len(quiz):
                st.session_state["submitted"] = True
                st.rerun()
            else:
                st.error(f"⚠️ Please answer all questions before submitting! ({answered_questions}/{len(quiz)} answered)")
    
    # Display results
    if st.session_state.get("submitted", False):
        display_quiz_results()

# Quiz Results Display - FIXED VERSION
def display_quiz_results():
    st.subheader("📊 Quiz Results")
    
    quiz = st.session_state["quiz"]
    score = 0
    results = []
    
    for i, q in enumerate(quiz, 1):
        user_answer = st.session_state["answers"].get(i)
        is_correct = user_answer == q["correct"]
        score += 1 if is_correct else 0
        
        results.append({
            "Question": i,
            "Topic": q.get("topic", "General"),
            "Correct": is_correct,
            "User Answer": user_answer,
            "Correct Answer": q["correct"]
        })
    
    # Score display
    percentage = (score / len(quiz)) * 100
    st.session_state["quiz_scores"].append(percentage)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Score", f"{score}/{len(quiz)}")
    with col2:
        st.metric("Percentage", f"{percentage:.1f}%")
    with col3:
        if percentage >= 80:
            st.success("🎉 Excellent!")
        elif percentage >= 60:
            st.info("👍 Good job!")
        else:
            st.warning("📚 Keep studying!")
    
    # Detailed results
    st.subheader("📋 Detailed Results")
    
    for i, result in enumerate(results, 1):
        q = quiz[i-1]
        is_correct = result["Correct"]
        
        with st.expander(f"Question {i} - {'✅ Correct' if is_correct else '❌ Incorrect'}"):
            st.write(f"**Question:** {q['question']}")
            st.write(f"**Your Answer:** {result['User Answer']}")
            st.write(f"**Correct Answer:** {result['Correct Answer']}")
            st.write(f"**Topic:** {result['Topic']}")
            
            if not is_correct:
                st.markdown("💡 **Study Tip:** Review this topic in your checklist!")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Retake Quiz"):
            # Reset quiz state
            st.session_state["quiz"] = generate_quiz(
                st.session_state["topic"],
                st.session_state["checklist"],
                st.session_state["difficulty_level"],
                len(quiz)
            )
            st.session_state["answers"] = {}
            st.session_state["submitted"] = False
            st.rerun()
    
    with col2:
        if st.button("📝 Back to Checklist"):
            st.session_state["show_quiz"] = False
            st.rerun()
    
    with col3:
        if st.button("🆕 New Quiz"):
            st.session_state["show_quiz"] = False
            st.session_state["quiz"] = None
            st.session_state["answers"] = {}
            st.session_state["submitted"] = False
            st.rerun()

# Study Checklist Function
def study_checklist():
    st.subheader("📝 Study Checklist Generator")
    
    # Topic input
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Enter the topic you want to study:", placeholder="e.g., Python Programming, Data Science, Machine Learning")
    with col2:
        generate_btn = st.button("Generate Checklist", type="primary")
    
    if generate_btn and topic:
        with st.spinner("Generating your personalized study checklist..."):
            checklist = generate_checklist(topic)
            
            if checklist:
                st.session_state["checklist"] = checklist
                st.session_state["progress"] = {item: False for item in checklist}
                st.session_state["topic"] = topic
                st.session_state["show_quiz"] = False
                st.success("✅ Checklist generated successfully!")
                
                # Generate YouTube links
                with st.spinner("Finding relevant video resources..."):
                    youtube_links = generate_youtube_links(checklist)
                    st.session_state["youtube_links"] = youtube_links
            else:
                st.error("Failed to generate checklist. Please try again.")
    
    # Display checklist
    if st.session_state["checklist"]:
        st.subheader(f"📋 Study Checklist for: {st.session_state['topic']}")
        
        # Progress overview
        completed = sum(st.session_state["progress"].values())
        total = len(st.session_state["progress"])
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.progress(completed / total if total > 0 else 0)
            st.write(f"Progress: {completed}/{total} topics completed ({(completed/total*100):.1f}%)")
        
        with col2:
            if st.button("🔄 Regenerate Checklist"):
                st.session_state["checklist"] = []
                st.session_state["progress"] = {}
                st.rerun()
        
        # Checklist items
        for i, item in enumerate(st.session_state["checklist"]):
            is_completed = st.session_state["progress"].get(item, False)
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    new_status = st.checkbox(
                        f"**{item}**",
                        value=is_completed,
                        key=f"checkbox_{i}"
                    )
                    
                    if new_status != is_completed:
                        st.session_state["progress"][item] = new_status
                        st.rerun()
                
                with col2:
                    if item in st.session_state["youtube_links"]:
                        st.markdown(f"[📺 Video]({st.session_state['youtube_links'][item]})")
                    else:
                        st.write("🔍 No video")
        
        # Visual progress
        if total > 0:
            st.subheader("📊 Visual Progress")
            progress_data = pd.DataFrame({
                "Status": ["Completed", "Remaining"],
                "Count": [completed, total - completed]
            })
            fig = px.pie(progress_data, names="Status", values="Count", title="Progress Overview")
            st.plotly_chart(fig, use_container_width=True)

# Main Application
def main():
    # FIXED: Initialize session state first
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📚 StudyHub - Smart Learning Platform</h1>
        <p>Your AI-powered companion for effective studying and skill development</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Navigation
    with st.sidebar:
        st.title("🎯 Navigation")
        
        # Navigation
        page = st.selectbox(
            "Choose a section:",
            ["📝 Study Checklist", "🎯 Quiz Center"]
        )
    
    # Main content based on navigation
    if page == "📝 Study Checklist":
        study_checklist()
    elif page == "🎯 Quiz Center":
        quiz_center()

if __name__ == "__main__":
    main()
