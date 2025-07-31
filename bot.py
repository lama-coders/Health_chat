# file: main.py
import streamlit as st
import requests
from datetime import datetime

# =============================
# Configure Groq API
# =============================
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    GROQ_API_KEY = ""
    st.warning("Using empty Groq key. Please add to secrets!")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "mixtral-8x7b-32768"

# =============================
# SESSION STATE
# =============================
if 'specialty' not in st.session_state:
    st.session_state.specialty = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'question_phase' not in st.session_state:
    st.session_state.question_phase = 0
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'problem' not in st.session_state:
    st.session_state.problem = ""

# =============================
# Prompt Engineering
# =============================
def get_specialty_prompt(specialty, user_data, problem, answers):
    base_prompts = {
        "Nutritionist": f"""
        ROLE: Senior Clinical Nutritionist at Mayo Clinic (15 years experience)
        USER PROFILE: {user_data}
        PATIENT CONCERN: {problem}
        ANSWERS: {answers}

        Provide a personalized nutrition assessment and plan in simple terms with clear section headings.
        """,

        "General Physician": f"""
        ROLE: Chief Medical Officer at Johns Hopkins Hospital
        PATIENT CONCERN: {problem}
        ANSWERS: {answers}

        Provide a basic diagnosis and action plan in layman terms.
        """,

        "Mental Health": f"""
        ROLE: Senior Clinical Psychologist (20 years experience)
        PATIENT CONCERN: {problem}
        ANSWERS: {answers}

        Provide emotional insights and practical strategies with empathy.
        """
    }
    return base_prompts.get(specialty, f"""
        ROLE: Senior {specialty}
        PATIENT CONCERN: {problem}
        ANSWERS: {answers}

        Provide appropriate advice in simple language.
    """)

# =============================
# Groq API Integration
# =============================
def get_groq_response(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful medical assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2048
    }
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Groq API Error: {str(e)}")
        return "Sorry, there was an error."

def parse_numbered_list(text):
    questions = []
    for line in text.split('\n'):
        if line.strip().startswith(('1.', '2.', '3.')):
            questions.append(line.split('.', 1)[1].strip())
    return questions[:3] or [
        "What are your main symptoms?",
        "How long has this been going on?",
        "What makes it better or worse?"
    ]

def generate_ai_questions(specialty, problem):
    prompt = f"""
    As a {specialty}, list 3 simple follow-up questions to ask a patient with:
    "{problem}"

    Format:
    1. Question
    2. Question
    3. Question
    """
    return parse_numbered_list(get_groq_response(prompt))

def get_ai_response():
    prompt = get_specialty_prompt(
        st.session_state.specialty,
        st.session_state.user_data,
        st.session_state.problem,
        st.session_state.answers
    )
    return get_groq_response(prompt)

# =============================
# Remaining Streamlit Code... (Unchanged)
# You can continue from UI sections like main_page(), nutrition_form(), etc.
