import streamlit as st
from openai import OpenAI
import json

# Force layout to wide mode for perfect desktop dashboard and tablet scaling
st.set_page_config(page_title="AI Study Assistant", layout="wide", initial_sidebar_state="expanded")

st.title("🎓 Smart Class Notes & Study Assistant")
st.write("Upload your Zoom/Meet recordings to generate clean notes and dynamic practice quizzes.")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter OpenAI API Key:", type="password")
course_name = st.sidebar.selectbox("Select Course", ["Calculus", "Computer Science", "Biology", "Physics", "History"])

# --- SESSION STATE INITIALIZATION ---
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "notes" not in st.session_state:
    st.session_state.notes = ""
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}

# --- MAIN INTERFACE TABS ---
tab1, tab2, tab3 = st.tabs(["📥 1. Process Lecture", "📝 2. Study Notes", "🧠 3. Practice Quiz"])

# --- TAB 1: UPLOAD AND PROCESS ---
with tab1:
    st.subheader("Upload Class Audio Recording")
    st.info("💡 Pro-Tip: Record your Zoom/Meet screen on your laptop or iPad, separate the audio, or upload the recorded audio file directly here.")
    
    uploaded_file = st.file_uploader("Choose an audio file (mp3, wav, m4a)", type=["mp3", "wav", "m4a"])
    
    if st.button("🚀 Process Lecture Recording"):
        if not api_key:
            st.error("Please enter your OpenAI API Key in the sidebar first!")
        elif uploaded_file is None:
            st.error("Please upload an audio file first.")
        else:
            with st.spinner("Step 1/2: Transcribing lecture with Whisper AI... Please wait."):
                try:
                    client = OpenAI(api_key=api_key)
                    
                    # Transcribe audio file using OpenAI Whisper
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=uploaded_file
                    )
                    st.session_state.transcript = transcription.text
                    st.success("Audio transcribed successfully!")
                    
                except Exception as e:
                    st.error(f"Transcription error: {str(e)}")
            
            if st.session_state.transcript:
                with st.spinner("Step 2/2: Generating Study Guide and Quizzes..."):
                    try:
                        # Construct a multi-step prompt requesting structured JSON output for the quiz
                        prompt = f"""
                        Analyze the following lecture transcript for the course '{course_name}'.
                        Perform two tasks:
                        1. Generate structured, highly readable study notes using bold keywords, clean headings, bullet points, and an explicit 'Key Equations/Definitions' section.
                        2. Generate an active-recall 3-question multiple-choice quiz based on the core content.
                        
                        You must respond strictly in JSON format with exactly two keys: "notes" and "quiz".
                        The "quiz" key must be an array of objects, where each object has: "question", "options" (array of 4 choices), and "correct_answer" (the exact matching string from the options array).
                        
                        Transcript:
                        {st.session_state.transcript}
                        """
                        
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            response_format={"type": "json_object"},
                            messages=[
                                {"role": "system", "content": "You are a world-class academic assistant that outputs structured JSON data."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        
                        # Parse the JSON response
                        result_json = json.loads(response.choices[0].message.content)
                        st.session_state.notes = result_json.get("notes", "Failed to generate notes.")
                        st.session_state.quiz_data = result_json.get("quiz", [])
                        st.session_state.user_answers = {}  # Reset answers
                        st.success("🎉 Study Guide and Quiz successfully generated! Head over to Tabs 2 and 3.")
                        
                    except Exception as e:
                        st.error(f"AI Processing error: {str(e)}")

# --- TAB 2: STUDY NOTES ---
with tab2:
    st.subheader(f"📝 Master Study Notes: {course_name}")
    if st.session_state.notes:
        st.markdown(st.session_state.notes)
    else:
        st.warning("No notes available. Please upload and process a lecture recording in Tab 1.")

# --- TAB 3: ACTIVE RECALL PRACTICE QUIZ ---
with tab3:
    st.subheader("🧠 Active Recall Quiz")
    if st.session_state.quiz_data:
        score = 0
        total_questions = len(st.session_state.quiz_data)
        
        # Display each question interactively
        for i, q in enumerate(st.session_state.quiz_data):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            
            # Persist selected choice in session state
            current_choice = st.radio(
                f"Select an answer for Q{i+1}:", 
                q['options'], 
                key=f"q_radio_{i}", 
                index=None
            )
            st.session_state.user_answers[i] = current_choice
            st.write("---")
            
        # Evaluation step
        if st.button("📝 Grade My Quiz"):
            correct_count = 0
            for i, q in enumerate(st.session_state.quiz_data):
                user_ans = st.session_state.user_answers.get(i)
                if user_ans == q['correct_answer']:
                    correct_count += 1
                    st.success(f"Question {i+1}: Correct! (Your answer: {user_ans})")
                else:
                    st.error(f"Question {i+1}: Incorrect. The correct answer was: **{q['correct_answer']}**")
            
            st.metric(label="Final Score", value=f"{correct_count} / {total_questions}")
    else:
        st.warning("No quiz available yet. Complete a processing run in Tab 1 to test your memory.")
