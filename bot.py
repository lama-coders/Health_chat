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
    if specialty == "Nutritionist":
        return f"""
        ROLE: Certified Clinical Nutritionist
        USER PROFILE:
        - Age: {user_data.get('age')}
        - Weight: {user_data.get('weight')} kg
        - Height: {user_data.get('height')} cm
        - Gender: {user_data.get('gender')}

        HEALTH CONCERN: {problem}
        ADDITIONAL INPUT: {answers}

        TASK:
        - Calculate BMI and classify it
        - Provide a structured, clear weekly nutrition plan
        - Include hydration tips, meal timings, and snacks
        """
    elif specialty == "General Physician":
        return f"""
        ROLE: Experienced General Physician
        PATIENT COMPLAINT: {problem}
        RESPONSES: {answers}

        Provide a detailed but simple explanation of possible conditions and suggested next steps including home care and medications.
        """
    elif specialty == "Mental Health":
        return f"""
        ROLE: Clinical Psychologist
        CONCERN: {problem}
        RESPONSES: {answers}

        Deliver empathetic, actionable mental health advice with daily coping tools and therapy suggestions.
        """
    elif specialty == "Orthopedic":
        return f"""
        ROLE: Senior Orthopedic Surgeon
        COMPLAINT: {problem}
        RESPONSES: {answers}

        Give analysis of musculoskeletal symptoms and recommend posture, exercise, or diagnostics needed.
        """
    elif specialty == "Dentist":
        return f"""
        ROLE: Professional Dental Surgeon
        DENTAL ISSUE: {problem}
        RESPONSES: {answers}

        Outline potential dental diagnoses and hygienic practices with cost-effective treatment paths.
        """
    return f"""
    ROLE: Healthcare Expert
    ISSUE: {problem}
    ANSWERS: {answers}

    Provide helpful health suggestions.
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
specialty_title_map = {
    "Nutritionist": "Nutrition Specialist",
    "General Physician": "General Physcian",
    "Mental Health": "Mental Health Expert",
    "Orthopedic": "Orthopedic Surgeon",
    "Dentist": "Dental Specialist"
}

if not st.session_state.chat_started:
    st.title("🩺 AI Hospital")
    st.subheader("Select a Specialist")
    specialties = list(specialty_title_map.keys())
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

st.title(f"🩺 {specialty_title_map.get(st.session_state.specialty)}")

st.session_state.problem = st.text_area("📝 Describe your health concern:", value=st.session_state.problem)

# Nutritionist Custom Fields
if st.session_state.specialty == "Nutritionist" and not st.session_state.profile_collected:
    with st.form("profile_form"):
        col1, col2, col3, col4 = st.columns(4)
        age = col1.text_input("Age")
        weight = col2.text_input("Weight (kg)")
        height = col3.text_input("Height (cm)")
        gender = col4.selectbox("Gender", ["Male", "Female", "Other"])
        submitted = st.form_submit_button("Submit Profile")
        if submitted:
            try:
                bmi = round(float(weight) / ((float(height)/100)**2), 1)
            except:
                bmi = "Invalid"
            st.session_state.user_data = {
                "age": age,
                "weight": weight,
                "height": height,
                "gender": gender,
                "BMI": bmi
            }
            st.session_state.profile_collected = True
            st.success(f"Profile submitted. BMI = {bmi}")
            st.markdown("#### 🧭 Would you like a personalized plan from Nutrition Specialist?")

if st.session_state.problem and (st.session_state.specialty != "Nutritionist" or st.session_state.profile_collected):
    st.subheader("📋 Follow-up Questions")
    if not st.session_state.questions:
        st.session_state.questions = [
            f"How long have you been experiencing '{st.session_state.problem}'?",
            f"Have you taken any treatment or medication for it?",
            f"Is the issue affecting your daily life or appetite?"
        ]

    idx = st.session_state.question_phase
    if idx < len(st.session_state.questions):
        with st.form(f"question_form_{idx}"):
            answer = st.text_input(st.session_state.questions[idx], key=f"q_{idx}")
            submitted = st.form_submit_button("Submit Answer")
            if submitted:
                st.session_state.answers.append(answer)
                st.session_state.question_phase += 1
                st.experimental_rerun()
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
        st.markdown(result, unsafe_allow_html=True)

if st.button("🔄 Start Over"):
    st.session_state.clear()
    st.rerun()


