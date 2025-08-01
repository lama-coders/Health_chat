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
GROQ_MODEL = "llama3-8b-8192"  # Free, fast, chat-compatible model

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
        ROLE: Senior Clinical Nutritionist
        USER PROFILE: {user_data}
        PATIENT CONCERN: {problem}
        ANSWERS: {answers}

        Provide a clear nutrition assessment and plan using simple terms and bullet points.
        """,

        "General Physician": f"""
        ROLE: Senior General Physician
        PATIENT CONCERN: {problem}
        ANSWERS: {answers}

        Provide a layman-friendly diagnosis summary and action steps.
        """,

        "Mental Health": f"""
        ROLE: Experienced Clinical Psychologist
        PATIENT CONCERN: {problem}
        ANSWERS: {answers}

        Give empathetic explanation and coping strategies.
        """
    }
    return base_prompts.get(specialty, f"""
        ROLE: Senior {specialty}
        PATIENT CONCERN: {problem}
        ANSWERS: {answers}

        Offer helpful, simple advice.
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
            {"role": "system", "content": "You are a helpful health assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2048
    }
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error: {response.status_code} — {response.text}")
        return "Sorry, the API rejected the request."
    except Exception as e:
        st.error(f"Groq API Error: {str(e)}")
        return "Sorry, there was an error."

# =============================
# Standalone Groq Test Section
# =============================
def run_standalone_groq_test():
    st.header("🔍 Standalone Groq API Test")
    st.caption("This sends a direct call to Groq without UI context.")
    if st.button("🚀 Run Groq Test", use_container_width=True):
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Tell me a fun fact about medicine."}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        try:
            r = requests.post(GROQ_URL, headers=headers, json=payload)
            r.raise_for_status()
            reply = r.json()['choices'][0]['message']['content']
            st.success("✅ Response from Groq:")
            st.code(reply)
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ HTTP Error {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"❌ Exception: {e}")

# =============================
# Debug Test Button
# =============================
if st.sidebar.button("🔍 Test Groq Key"):
    st.sidebar.info(f"✅ Key ends with: {GROQ_API_KEY[-6:]}")
    test_result = get_groq_response("Say hello in one sentence.")
    st.sidebar.success("Response from Groq:")
    st.sidebar.code(test_result)

# Optional debug section (visible in main panel for direct testing)
run_standalone_groq_test()

# =============================
# Full UI Chatbot Logic
# =============================
st.title("🩺 AI Health Assistant")

specialties = ["General Physician", "Nutritionist", "Mental Health"]
st.session_state.specialty = st.selectbox("Select Specialty:", specialties)

st.session_state.problem = st.text_area("Describe your issue:", value=st.session_state.problem)

if st.button("Next ➡️"):
    st.session_state.question_phase += 1
    st.session_state.questions = ["What is your age?", "What is your gender?", "Do you have chronic illnesses?", "Are you taking medications?"]

if st.session_state.question_phase > 0:
    q_index = st.session_state.question_phase - 1
    if q_index < len(st.session_state.questions):
        question = st.session_state.questions[q_index]
        answer = st.text_input(f"{question}", key=f"q_{q_index}")
        if st.button("Submit Answer"):
            st.session_state.answers.append(answer)
            st.session_state.question_phase += 1
    else:
        st.success("✅ All answers submitted. Generating response...")
        prompt = get_specialty_prompt(
            st.session_state.specialty,
            st.session_state.user_data,
            st.session_state.problem,
            st.session_state.answers
        )
        result = get_groq_response(prompt)
        st.markdown("### 🧠 AI Suggestion")
        st.markdown(result)

