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
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error: {response.status_code} — {response.text}")
        return "Sorry, the API rejected the request."
    except Exception as e:
        st.error(f"Groq API Error: {str(e)}")
        return "Sorry, there was an error."

# =============================
# Debug Test Button
# =============================
if st.sidebar.button("🔍 Test Groq Key"):
    test_result = get_groq_response("Say hello in one sentence.")
    st.sidebar.success("Response from Groq:")
    st.sidebar.code(test_result)

# =============================
# Streamlit UI Components
# =============================
def main_page():
    st.set_page_config(page_title="AI Health Advisor", page_icon="⚕️", layout="wide")
    st.title("⚕️ Professional Health Advisor")
    st.subheader("Consult with AI specialists")

    cols = st.columns(3)
    specialties = ["Nutritionist", "General Physician", "Mental Health"]

    for i, specialty in enumerate(specialties):
        with cols[i % 3]:
            if st.button(f"**{specialty}**", use_container_width=True, key=f"btn_{specialty}"):
                st.session_state.specialty = specialty
                st.session_state.question_phase = 0
                st.rerun()

    st.markdown("---")
    st.caption("Note: AI provides general guidance only. Not a substitute for professional medical care.")

def nutrition_form():
    with st.container(border=True):
        st.subheader("📊 Health Profile")
        cols = st.columns([1,1,1,1])
        with cols[0]:
            weight = st.number_input("Weight (kg)", 30, 200, 70, key="weight")
        with cols[1]:
            height = st.number_input("Height (cm)", 100, 250, 170, key="height")
        with cols[2]:
            age = st.number_input("Age", 1, 120, 30, key="age")
        with cols[3]:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="gender")

        if st.button("Save Profile", type="primary"):
            bmi = weight / ((height/100) ** 2)
            st.session_state.user_data = {
                "weight": weight,
                "height": height,
                "age": age,
                "gender": gender,
                "bmi": round(bmi, 1),
                "timestamp": datetime.now().strftime("%Y-%m-%d")
            }
            st.success("Profile saved!")
            st.session_state.question_phase = -1

def problem_input():
    with st.form("problem_form"):
        st.subheader(f"Describe your concern to the {st.session_state.specialty}")
        problem = st.text_area("What would you like to discuss?", placeholder="e.g., I've been experiencing persistent headaches...", height=120)

        if st.form_submit_button("Get Professional Advice", type="primary"):
            if problem.strip():
                st.session_state.problem = problem
                with st.spinner("Preparing relevant questions..."):
                    st.session_state.questions = generate_ai_questions(st.session_state.specialty, problem)
                st.session_state.question_phase = 1
                st.rerun()
            else:
                st.warning("Please describe your concern")

def question_phase():
    current_phase = st.session_state.question_phase
    question_text = st.session_state.questions[current_phase - 1]

    with st.container(border=True):
        st.progress(current_phase/3, text=f"Question {current_phase} of 3")
        st.subheader(question_text)
        answer = st.text_area("Your response:", height=100, key=f"ans_{current_phase}")

        if st.button("Submit Answer", type="primary"):
            if answer.strip():
                st.session_state.answers.append(answer)
                if current_phase < 3:
                    st.session_state.question_phase += 1
                else:
                    st.session_state.question_phase = 4
                st.rerun()
            else:
                st.warning("Please provide a response")

def show_professional_advice():
    st.subheader("🧑‍⚕️ Professional Consultation Results")
    st.caption(f"Specialty: {st.session_state.specialty} | Concern: {st.session_state.problem[:50]}...")

    with st.spinner("Preparing your personalized recommendations..."):
        advice = get_ai_response()

    st.markdown("---")
    st.markdown(advice, unsafe_allow_html=True)
    st.markdown("---")

    cols = st.columns([1,1])
    with cols[0]:
        if st.button("🔄 Start New Consultation", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['specialty', 'user_data']:
                    del st.session_state[key]
            st.session_state.question_phase = 0
            st.rerun()
    with cols[1]:
        st.download_button("📥 Save Consultation", advice, file_name=f"health_advice_{datetime.now().strftime('%Y%m%d')}.txt", use_container_width=True)

def main():
    if not st.session_state.specialty:
        main_page()
    elif st.session_state.specialty == "Nutritionist" and not st.session_state.user_data:
        nutrition_form()
    elif st.session_state.question_phase == -1 or (st.session_state.specialty != "Nutritionist" and not st.session_state.problem):
        problem_input()
    elif 1 <= st.session_state.question_phase <= 3:
        question_phase()
    elif st.session_state.question_phase == 4:
        show_professional_advice()

    st.markdown("---")
    st.caption("**Disclaimer:** This AI provides general information only. It is not medical advice. Consult a healthcare professional for personal medical concerns.")

if __name__ == "__main__":
    main()

