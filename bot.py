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
    specialty = st.session_state.get("specialty", "")
    
    # Reset common keys for all specialties
    st.session_state.question_phase = 0
    st.session_state.answers = []
    st.session_state.questions = []
    st.session_state.problem = ""
    st.session_state.chat_started = False
    
    # Reset Nutritionist-specific keys
    if specialty == "Nutritionist":
        st.session_state.user_data = {}
        st.session_state.profile_collected = False
        if "nutritionist_submit_attempted" in st.session_state:
            st.session_state.nutritionist_submit_attempted = False
    
    # Clear the trigger flag and immediately rerun
    st.session_state["trigger_fresh_start"] = False
    st.rerun()

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
    "Nutritionist": "Nutrition Specialist",
    "Physician": "Physician",
    "Mental Health": "Mental Health Expert",
    "Orthopedic": "Orthopedic Surgeon",
    "Dentist": "Dental Specialist"
}

if not st.session_state.get('specialty'):
    st.title("🩺 Healthcare Chatbot")
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
            st.session_state.chat_started = False # Start in the problem input phase
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

# This is the main logic gate. It shows either the problem input or the follow-up questions,
# but never both at the same time.
if not st.session_state.chat_started:
    # --- PROBLEM INPUT PHASE ---
    # This block handles the initial problem description for ALL specialties before the chat begins.
    if st.session_state.specialty == "Nutritionist":
        if not st.session_state.profile_collected:
            # Friendly welcome message for Nutritionist
            st.markdown("""
            ### 🌟 Hey there! Welcome to your Nutrition Journey! 🌱
            
            Before we dive into your health concerns, let's calculate your *perfect weight range* and understand your current health status better! 
            
            This will help me provide you with the most personalized nutrition advice. 🎯
            """)
            
            st.markdown("#### 📋 Please fill in your basic information:")
            
            # Profile collection with better UX
            col1, col2 = st.columns(2)
            with col1:
                age = st.text_input("🎂 Age (years)", placeholder="e.g., 25")
                weight = st.text_input("⚖️ Current Weight (kg)", placeholder="e.g., 70")
            with col2:
                height = st.text_input("📏 Height (cm)", placeholder="e.g., 175")
                gender = st.selectbox("👤 Gender", ["Select...", "Male", "Female", "Other"])
            
            # Improved single-click submit button with validation flags
            if 'nutritionist_submit_attempted' not in st.session_state:
                st.session_state.nutritionist_submit_attempted = False
            calculate_clicked = st.button("🚀 Calculate My Health Profile", help="Calculate BMI and health status")
            if calculate_clicked:
                st.session_state.nutritionist_submit_attempted = True
            if st.session_state.nutritionist_submit_attempted:
                age_clean = age.strip()
                weight_clean = weight.strip()
                height_clean = height.strip()
                if not (age_clean and weight_clean and height_clean and gender != "Select..."):
                    st.warning("📝 Please fill in all fields to continue.")
                else:
                    try:
                        age_val = int(age_clean)
                        weight_val = float(weight_clean)
                        height_val = float(height_clean)
                    except ValueError:
                        st.error("⚠️ Please enter valid numbers for age, weight, and height.")
                    else:
                        try:
                            bmi = round(weight_val / ((height_val/100)**2), 1)
                            if bmi < 18.5:
                                bmi_category = "Underweight"
                            elif 18.5 <= bmi < 25:
                                bmi_category = "Normal Weight"
                            elif 25 <= bmi < 30:
                                bmi_category = "Overweight"
                            else:
                                bmi_category = "Obese"
                            advice = {
                                "Underweight": "You may need to gain some healthy weight.",
                                "Normal Weight": "Great! You're in the healthy weight range.",
                                "Overweight": "Consider a balanced diet and regular exercise.",
                                "Obese": "Let's work together on a healthy weight management plan."
                            }.get(bmi_category)
                            st.session_state.user_data = {
                                "age": age_val,
                                "weight": weight_val,
                                "height": height_val,
                                "gender": gender,
                                "BMI": bmi,
                                "bmi_category": bmi_category,
                                "health_advice": advice
                            }
                            st.session_state.profile_collected = True
                            st.session_state.nutritionist_submit_attempted = False
                            st.rerun()
                        except Exception:
                            st.error("⚠️ Please enter valid numbers for age, weight, and height.")
        else:
            # Show BMI results after profile is collected
            st.markdown("### 🎉 Your Health Profile Results")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("⚖️ BMI", f"{st.session_state.user_data['BMI']}")
            with col2:
                st.metric("🏅 Category", st.session_state.user_data['bmi_category'])
            with col3:
                st.metric("🎂 Age", f"{st.session_state.user_data['age']} years")
            bmi_category = st.session_state.user_data['bmi_category']
            if bmi_category == "Normal Weight":
                st.success(f"✅ {st.session_state.user_data['health_advice']}")
            elif bmi_category in ["Underweight", "Overweight"]:
                st.warning(f"⚠️ {st.session_state.user_data['health_advice']}")
            else:
                st.info(f"💪 {st.session_state.user_data['health_advice']}")
            st.markdown("--- ")
            st.markdown("### 📝 Now, tell me about your nutrition concerns:")
            st.session_state.problem = st.text_area(
                "🍎 What would you like help with today?", 
                value=st.session_state.problem,
                placeholder="e.g., I want to lose weight, I need a meal plan, I have digestive issues..."
            )
            if st.session_state.problem:
                if st.button("Start Answering Questions ➡️"):
                    st.session_state.chat_started = True
                    st.rerun()
    else:
        # For all other specialties, show the regular problem input.
        st.session_state.problem = st.text_area("📝 Describe your health concern:", value=st.session_state.problem)
        if st.session_state.problem:
            if st.button("🤖 Get AI Consultation"):
                st.session_state.chat_started = True
                st.rerun()

else: # This means st.session_state.chat_started is True
    # --- Q&A PHASE ---
    st.subheader("📋 Follow-up Questions")
    
    # Generate questions dynamically based on problem and specialty
    max_questions = 3  # Limit to 3 questions for better UX
    
    if st.session_state.question_phase < max_questions:
        # Generate current question dynamically
        if st.session_state.question_phase >= len(st.session_state.questions):
            with st.spinner("Generating relevant question..."):
                new_question = generate_follow_up_question(
                    st.session_state.specialty,
                    st.session_state.problem,
                    st.session_state.answers,
                    st.session_state.question_phase + 1
                )
                st.session_state.questions.append(new_question)
        
        # Display current question
        current_question = st.session_state.questions[st.session_state.question_phase]
        
        # Use regular text input without form
        answer = st.text_input(current_question, key=f"q_{st.session_state.question_phase}", placeholder="Type your answer here...")
        
        # --- Button Logic ---
        # We use a two-button system: one to submit the current answer and move to the next question,
        # and another to finalize the process and get the AI suggestion.

        # --- Button Logic ---
        # A clear, three-button system for a better user experience.

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            if st.button("✅ Submit & Next Question", key=f"submit_{st.session_state.question_phase}"):
                if answer.strip():
                    st.session_state.answers.append(answer)
                    st.session_state.question_phase += 1
                    st.rerun()
                else:
                    st.warning("Please provide an answer before proceeding.")

        with col2:
            # Show the 'Get Suggestion' button only after the first question is answered.
            if len(st.session_state.answers) > 0:
                if st.button("💡 Get AI Suggestion", help="Finish asking questions and get the AI's advice."):
                    # If there's a pending answer in the text box, add it before getting results.
                    if answer.strip() and len(st.session_state.answers) == st.session_state.question_phase:
                        st.session_state.answers.append(answer)
                    st.session_state.question_phase = max_questions # End the question phase
                    st.rerun()

        with col3:
            if st.button("🔄", help="Start the questions over for this consultation"):
                st.session_state.question_phase = 0
                st.session_state.questions = []
                st.session_state.answers = []
                st.rerun()
    else:
        st.success("✅ Generating personalized response...")
        prompt = get_specialty_prompt(
            st.session_state.specialty,
            st.session_state.user_data,
            st.session_state.problem,
            st.session_state.answers
        )
        result = get_groq_response(prompt)
        st.markdown("### 🧠 AI Suggestion")

        # Define the sections in the order they should appear
        section_titles = [
            "📝 Initial Assessment",
            "💡 Recommendations",
            "💊 Suggested Plan",
            "⚠️ Important Disclaimer"
        ]

        # Split the response into parts based on the '###' markdown heading
        # The pattern (###\s.*) captures the headings themselves
        parts = re.split(r'(###\s.*)', result.strip())[1:]

        # Group parts into (title, content) tuples
        grouped_parts = [(''.join(parts[i:i+2])).strip() for i in range(0, len(parts), 2)]

        # Display sections in expanders
        for section_text in grouped_parts:
            # Find the title and content
            lines = section_text.split('\n', 1)
            if lines:
                title = lines[0].replace('###', '').strip()
                content = lines[1].strip() if len(lines) > 1 else ""
                with st.expander(f"*{title}*", expanded=True):
                    st.markdown(content, unsafe_allow_html=True)










