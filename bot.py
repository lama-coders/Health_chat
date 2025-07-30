import streamlit as st
import requests  # Changed from google.generativeai
from datetime import datetime

# Configure DeepSeek API
DEEPSEEK_API_KEY = st.secrets["sk-ed276fb90c7942f99d317171e41c7eb4"]  # Update secrets.toml
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# =============================
# INITIALIZE SESSION STATE (UNCHANGED)
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
# PROMPT ENGINEERING (UNCHANGED)
# =============================
def get_specialty_prompt(specialty, user_data, problem, answers):
    """Identical to original, no changes needed"""
    # ... [Keep all existing prompt templates] ...

# =============================
# DEEPSEEK API INTEGRATION (MODIFIED)
# =============================
def get_deepseek_response(prompt):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1500
    }
    
    try:
        response = requests.post(DEEPSEEK_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return "Sorry, I couldn't process your request. Please try again."

# =============================
# MODIFIED AI FUNCTIONS
# =============================
def generate_ai_questions(specialty, problem):
    """Replaces Gemini with DeepSeek"""
    prompt = f"""
    As a senior {specialty}, what 3 most important questions would you ask a patient who presents with:
    "{problem}"
    
    Format as:
    1. [Question about symptom history]
    2. [Question about severity]
    3. [Question about related factors]
    
    Use simple, non-medical language
    """
    return parse_numbered_list(get_deepseek_response(prompt))

def get_ai_response():
    """Replaces Gemini with DeepSeek"""
    prompt = get_specialty_prompt(
        st.session_state.specialty,
        st.session_state.user_data,
        st.session_state.problem,
        st.session_state.answers
    )
    return get_deepseek_response(prompt)

def parse_numbered_list(text):
    """Helper to extract numbered items from API response"""
    questions = []
    for line in text.split('\n'):
        if line.strip().startswith(('1.', '2.', '3.')):
            questions.append(line.split('.', 1)[1].strip())
    return questions[:3] or [
        "What are your main symptoms?",
        "How long has this been going on?",
        "What makes it better or worse?"
    ]

# =============================
# STREAMLIT UI COMPONENTS (ALL UNCHANGED)
# =============================
def main_page():
    # ... [Identical to original] ...

def nutrition_form():
    # ... [Identical to original] ...

def problem_input():
    # ... [Identical to original] ...

def question_phase():
    # ... [Identical to original] ...

def show_professional_advice():
    # ... [Identical to original] ...

def main():
    # ... [Identical to original] ...

if __name__ == "__main__":
    main()
