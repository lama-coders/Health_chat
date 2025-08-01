# file: main.py
import streamlit as st
import requests

# =============================
# Configure Groq API
# =============================
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    GROQ_API_KEY = ""
    st.warning("Using empty Groq key. Please add to secrets!")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"

# =============================
# SESSION STATE INIT
# =============================
for key, val in {
    'specialty': None,
    'user_data': {},
    'question_phase': 0,
    'questions': [],
    'answers': [],
    'problem': "",
    'profile_collected': False,
    'chat_started': False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =============================
# Prompt Engineering
# =============================
def get_specialty_prompt(specialty, user_data, problem, answers):
    return f"""
    ROLE: Senior {specialty}
    PATIENT CONCERN: {problem}
    PATIENT PROFILE: {user_data}
    RESPONSES: {answers}

    Provide helpful guidance and suggestions in plain English.
    """

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
        r = requests.post(GROQ_URL, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Groq API Error: {str(e)}")
        return "API Error"

# =============================
# UI LAYOUT
# =============================
st.title("🩺 Healthcare Chatbot")

if not st.session_state.chat_started:
    st.subheader("Select a Specialist")
    specialties = ["General Physician", "Nutritionist", "Mental Health", "Orthopedic", "Dentist"]
    cols = st.columns(len(specialties))
    for i, name in enumerate(specialties):
        if cols[i].button(name):
            st.session_state.specialty = name
            st.session_state.question_phase = 0
            st.session_state.answers = []
            st.session_state.problem = ""
            st.session_state.user_data = {}
            st.session_state.profile_collected = False
            st.session_state.chat_started = True
    st.stop()

st.success(f"Selected: {st.session_state.specialty}")

st.session_state.problem = st.text_area("📝 Describe your health concern:", value=st.session_state.problem)

if st.session_state.specialty == "Nutritionist" and not st.session_state.profile_collected:
    with st.form("profile_form"):
        age = st.text_input("Age:")
        weight = st.text_input("Weight (kg):")
        height = st.text_input("Height (cm):")
        gender = st.selectbox("Gender:", ["Male", "Female", "Other"])
        submitted = st.form_submit_button("Submit Profile")
        if submitted:
            st.session_state.user_data = {"age": age, "weight": weight, "height": height, "gender": gender}
            st.session_state.profile_collected = True
            st.success("Profile submitted.")

if st.session_state.problem and (st.session_state.specialty != "Nutritionist" or st.session_state.profile_collected):
    st.subheader("📋 Follow-up Questions")
    if not st.session_state.questions:
        st.session_state.questions = [
            f"How long have you been experiencing '{st.session_state.problem}' symptoms?",
            f"Have you consulted a doctor before for '{st.session_state.problem}'?",
            f"Is the issue affecting your daily activities?"
        ]

    idx = st.session_state.question_phase
    if idx < len(st.session_state.questions):
        with st.form(f"question_form_{idx}"):
            answer = st.text_input(st.session_state.questions[idx], key=f"q_{idx}")
            submitted = st.form_submit_button("Submit Answer")
            if submitted:
                st.session_state.answers.append(answer)
                st.session_state.question_phase += 1
    else:
        st.success("✅ All answers collected. Generating response...")
        prompt = get_specialty_prompt(
            st.session_state.specialty,
            st.session_state.user_data,
            st.session_state.problem,
            st.session_state.answers
        )
        result = get_groq_response(prompt)
        st.markdown("### 🧠 AI Suggestion")
        st.markdown(result)

if st.button("🔄 Start Over"):
    for key in ["specialty", "user_data", "question_phase", "questions", "answers", "problem", "profile_collected", "chat_started"]:
        st.session_state[key] = None if key == "specialty" else {} if isinstance(st.session_state[key], dict) else 0 if isinstance(st.session_state[key], int) else False if isinstance(st.session_state[key], bool) else ""
    st.experimental_rerun()
