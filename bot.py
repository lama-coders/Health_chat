# file: main.py
import streamlit as st
import requests
import re

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
# Handle app reset for a true one-click Main Menu experience
if st.session_state.get("reset_app", False): 
    st.session_state.clear()
    # Reinitialize keys after clearing
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
        st.session_state[key] = val
    st.session_state["reset_app"] = False

# Handle fresh start for specialty (single-click reset)
if st.session_state.get("trigger_fresh_start", False):
    # Reset keys for a clean slate within the same specialty
    st.session_state.question_phase = 0
    st.session_state.answers = []
    st.session_state.questions = []
    st.session_state.problem = ""
    st.session_state.user_data = {}
    st.session_state.profile_collected = False
    st.session_state.chat_started = False
    
    # Clear the trigger flag
    st.session_state["trigger_fresh_start"] = False

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
    # Base instructions for a structured, professional response
    base_task = """
    TASK:
    Provide a professional, personalized assessment based on the user's problem and answers. 
    Your response MUST be structured with the following markdown headings:

    ### 📝 Initial Assessment
    (Provide a summary of the problem based on the user's input.)

    ### 💡 Recommendations
    (Offer clear, actionable suggestions, home care, or lifestyle advice. Use bullet points.)

    ### 💊 Suggested Plan
    (Outline a step-by-step plan, which could include medications, exercises, or a nutrition plan. Be specific.)

    ### ⚠️ Important Disclaimer
    (Include a disclaimer that this is AI-generated advice and not a substitute for professional medical consultation.)
    """

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

        {base_task}
        """
    elif specialty == "Physician":
        return f"""
        ROLE: Experienced Physician
        PATIENT COMPLAINT: {problem}
        RESPONSES: {answers}

        {base_task}
        """
    elif specialty == "Mental Health":
        return f"""
        ROLE: Clinical Psychologist
        CONCERN: {problem}
        RESPONSES: {answers}

        {base_task}
        """
    elif specialty == "Orthopedic":
        return f"""
        ROLE: Senior Orthopedic Surgeon
        COMPLAINT: {problem}
        RESPONSES: {answers}

        {base_task}
        """
    elif specialty == "Dentist":
        return f"""
        ROLE: Professional Dental Surgeon
        DENTAL ISSUE: {problem}
        RESPONSES: {answers}

        {base_task}
        """
    return f"""
    ROLE: Healthcare Expert
    ISSUE: {problem}
    ANSWERS: {answers}

    {base_task}
    """

# =============================
# Dynamic Question Generation
# =============================
def generate_follow_up_question(specialty, problem, previous_answers, question_number):
    """Generate a relevant follow-up question using LLM based on the problem and specialty"""
    prompt = f"""
    You are a {specialty} assistant. A patient has described their problem as: "{problem}"
    
    Previous answers given: {previous_answers if previous_answers else "None yet"}
    
    Generate ONE specific, relevant follow-up question (question #{question_number}) that would help you better understand their condition and provide better advice. 
    
    The question must be:
    - Very short (around 6-7 words).
    - A single line.
    - Directly related to their problem.
    - Professional and empathetic.
    - Specific to your specialty area.
    
    Return ONLY the question text, nothing else.
    """
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful medical assistant that generates relevant follow-up questions."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 30
    }
    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        st.error(f"Error generating question: {str(e)}")
        return f"Can you tell me more about your {problem.lower()}?"

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
    "Nutritionist": "Nutritionist",
    "Physician": "Physician",
    "Infectious Disease Specialist": "Infectious Disease Specialist",
    "Dentist": "Dentist",
    "Medical Checkups": "Medical Checkups"
}

if st.session_state.specialty is None:
    st.title("🩺 Healthcare Chatbot")
    st.subheader("Select a Specialist")
    specialties = list(specialty_title_map.keys())
    cols = st.columns(len(specialties))
    for i, name in enumerate(specialties):
        if cols[i].button(name):
            st.session_state.specialty = name
            # No longer setting chat_started here
            st.rerun()
    st.stop()

# Add navigation header with back button
col1, col2 = st.columns([4, 1])
with col1:
    st.title(f"🩺 {specialty_title_map.get(st.session_state.specialty)}")
with col2:
    if st.button("🏠 Main Menu", help="Go back to specialty selection"):
        # Use a dedicated reset flag to guarantee a single-click reset
        st.session_state.clear()
        st.session_state["reset_app"] = True
        st.rerun()

# Route to the correct UI based on specialty
if st.session_state.specialty == "Medical Checkups":
    # --- BMI CALCULATOR UI ---
    st.markdown("### ⚖️ BMI (Body Mass Index) Calculator")
    st.markdown("BMI is a simple calculation using a person's height and weight. The formula is BMI = kg/m2 where kg is a person's weight in kilograms and m2 is their height in metres squared.")
    st.markdown("--- ")
    
    col1, col2 = st.columns(2)
    with col1:
        age = st.text_input("🎂 Age (years)", placeholder="e.g., 25")
        weight = st.text_input("⚖️ Current Weight (kg)", placeholder="e.g., 70")
    with col2:
        height = st.text_input("📏 Height (cm)", placeholder="e.g., 175")
        gender = st.selectbox("👤 Gender", ["Select...", "Male", "Female", "Other"])
    
    if st.button("🚀 Calculate My BMI"):
        if not (age.strip() and weight.strip() and height.strip() and gender != "Select..."):
            st.warning("📝 Please fill in all fields to continue.")
        else:
            try:
                age_val, weight_val, height_val = int(age), float(weight), float(height)
                bmi = round(weight_val / ((height_val/100)**2), 1)
                
                if bmi < 18.5:
                    bmi_category = "Underweight"
                    advice = "You may need to gain some healthy weight."
                elif 18.5 <= bmi < 25:
                    bmi_category = "Normal Weight"
                    advice = "Great! You're in the healthy weight range."
                elif 25 <= bmi < 30:
                    bmi_category = "Overweight"
                    advice = "Consider a balanced diet and regular exercise."
                else:
                    bmi_category = "Obese"
                    advice = "A healthcare provider can help you with a weight management plan."
                
                st.markdown("### 🎉 Your Results")
                col1, col2 = st.columns(2)
                col1.metric("⚖️ Your BMI", f"{bmi}")
                col2.metric("🏅 Category", bmi_category)
                
                if bmi_category == "Normal Weight":
                    st.success(f"✅ {advice}")
                else:
                    st.warning(f"⚠️ {advice}")
            except ValueError:
                st.error("⚠️ Please enter valid numbers for age, weight, and height.")
    st.stop() # Stop execution here, this is a standalone tool

# --- DEFAULT CONSULTATION UI ---
else:
    st.markdown("### 📝 Your Health Concern")
    problem_label = "🩺 Describe your health concern:"
    problem_placeholder = "e.g., I have a toothache, I've been having chest pains..."

    st.text_area(
        problem_label,
        placeholder=problem_placeholder,
        key="problem",
        disabled=st.session_state.chat_started
    )

    if st.session_state.chat_started:
        st.subheader("📋 Follow-up Questions")
        max_questions = 3
        
        if st.session_state.question_phase < max_questions:
            if st.session_state.question_phase >= len(st.session_state.questions):
                with st.spinner("Generating relevant question..."):
                    new_question = generate_follow_up_question(
                        st.session_state.specialty,
                        st.session_state.problem,
                        st.session_state.answers,
                        st.session_state.question_phase + 1
                    )
                    st.session_state.questions.append(new_question)
            
            current_question = st.session_state.questions[st.session_state.question_phase]
            answer = st.text_input(current_question, key=f"q_{st.session_state.question_phase}", placeholder="Type your answer here...")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("✅ Submit & Next", key=f"submit_{st.session_state.question_phase}"):
                    if answer.strip():
                        st.session_state.answers.append(answer)
                        st.session_state.question_phase += 1
                        st.rerun()
                    else:
                        st.warning("Please provide an answer.")
            with col2:
                if st.button("💡 Get AI Suggestion", key=f"skip_{st.session_state.question_phase}"):
                    st.session_state.question_phase = max_questions
                    st.rerun()
            with col3:
                if st.button("🔄 Start Over", help="Reset the questions for this consultation"):
                    st.session_state.question_phase = 0
                    st.session_state.questions = []
                    st.session_state.answers = []
                    st.rerun()
        else:
            st.success("✅ You've answered all questions! Generating your report...")
            prompt = get_specialty_prompt(
                st.session_state.specialty,
                st.session_state.user_data,
                st.session_state.problem,
                st.session_state.answers
            )
            result = get_groq_response(prompt)
            st.markdown("### 🧠 AI Suggestion")

            parts = re.split(r'(###\s.*)', result.strip())[1:]
            grouped_parts = [(''.join(parts[i:i+2])).strip() for i in range(0, len(parts), 2)]
            for section_text in grouped_parts:
                lines = section_text.split('\n', 1)
                if lines:
                    title = lines[0].replace('###', '').strip()
                    content = lines[1].strip() if len(lines) > 1 else ""
                    with st.expander(f"*{title}*", expanded=True):
                        st.markdown(content, unsafe_allow_html=True)
            
            if st.button("🔄 Start a New Consultation"):
                st.session_state.trigger_fresh_start = True
                st.rerun()
    else:
        if st.session_state.problem:
            if st.button("🤖 Get AI Consultation"):
                st.session_state.chat_started = True
                st.rerun()




