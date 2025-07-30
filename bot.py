import streamlit as st
import requests
from datetime import datetime

# Configure DeepSeek API
DEEPSEEK_API_KEY = st.secrets["sk-ed276fb90c7942f99d317171e41c7eb4"]
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# =============================
# INITIALIZE SESSION STATE
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
# ENHANCED PROMPT ENGINEERING
# =============================
def get_specialty_prompt(specialty, user_data, problem, answers):
    """Generate professional yet simple prompts for each specialty"""
    base_prompts = {
        "Nutritionist": f"""
        ROLE: Senior Clinical Nutritionist at Mayo Clinic (15 years experience)
        USER PROFILE: {user_data}
        PATIENT CONCERN: {problem}
        
        INSTRUCTIONS:
        1. Analyze the patient's BMI ({user_data.get('bmi', 'N/A')}) and health metrics
        2. Generate 3 CRITICAL follow-up questions to clarify:
           - Dietary habits and preferences
           - Lifestyle constraints
           - Specific health goals
        3. After receiving answers: {answers}
        4. Create personalized recommendations with:
           - Clear section headings (## Assessment, ## Plan)
           - Bullet points for key recommendations
           - A sample meal table (| Time | Meal | Calories |)
           - Practical implementation tips
        5. Use simple language avoiding medical jargon
        6. Always include: "Consult a certified nutritionist for personalized guidance"
        
        RESPONSE FORMAT:
        ## Professional Assessment
        [Concise analysis of patient's situation]
        
        ## Personalized Nutrition Plan
        [Structured recommendations]
        
        ## Sample Meal Schedule
        | Time   | Meal          | Calories | Key Nutrients |
        |--------|---------------|----------|---------------|
        | 8 AM   | Oatmeal...    | 350      | Fiber, Protein|
        
        ## Next Steps
        [Actionable advice]
        
        DISCLAIMER: [Medical disclaimer]
        """,
        
        "General Physician": f"""
        ROLE: Chief Medical Officer at Johns Hopkins Hospital
        PATIENT CONCERN: {problem}
        
        INSTRUCTIONS:
        1. Generate 3 KEY diagnostic questions about:
           - Symptom duration and progression
           - Pain characteristics
           - Relevant medical history
        2. After answers: {answers}
        3. Provide professional assessment with:
           - Differential diagnosis (in simple terms)
           - Recommended actions (## Immediate Steps, ## Monitoring)
           - Red flag warnings (❗️ notation)
        4. Format with clear headings and bullet points
        5. Use simple language: "You might be experiencing... rather than medical terms"
        
        RESPONSE FORMAT:
        ## Clinical Assessment
        [Analysis in simple terms]
        
        ## Recommended Action Plan
        - [ ] Step 1: ...
        - [ ] Step 2: ...
        
        ## When to Seek Immediate Care
        ❗️ [Warning signs]
        
        DISCLAIMER: [Medical disclaimer]
        """,
        
        "Mental Health": f"""
        ROLE: Senior Clinical Psychologist (PhD, 20 years experience)
        PATIENT CONCERN: {problem}
        
        INSTRUCTIONS:
        1. Generate 3 THERAPEUTIC questions about:
           - Emotional patterns
           - Impact on daily life
           - Coping mechanisms
        2. After answers: {answers}
        3. Provide evidence-based guidance with:
           - Cognitive behavioral framework
           - Practical coping strategies
           - Resources table (| Type | Resource | Contact |)
        4. Use empathetic language: "Many people experience..."
        
        RESPONSE FORMAT:
        ## Psychological Perspective
        [Normalized explanation]
        
        ## Coping Strategies
        - Technique 1: ...
        - Technique 2: ...
        
        ## Support Resources
        | Type       | Resource          | Contact          |
        |------------|-------------------|------------------|
        | Crisis     | National Hotline  | 1-800-XXX-XXXX  |
        
        DISCLAIMER: [Professional care advice]
        """
    }
    
    return base_prompts.get(specialty, f"""
    ROLE: Senior {specialty} Specialist
    PATIENT CONCERN: {problem}
    
    INSTRUCTIONS:
    1. Generate 3 RELEVANT clinical questions
    2. After answers: {answers}
    3. Provide structured professional advice with:
       - Clear section headings
       - Bullet point recommendations
       - Practical next steps
    4. Use simple, non-technical language
    
    RESPONSE FORMAT:
    ## Professional Assessment
    [Brief analysis]
    
    ## Recommended Approach
    - Step 1: ...
    - Step 2: ...
    
    DISCLAIMER: Seek professional medical advice
    """)

# =============================
# DEEPSEEK API INTEGRATION
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

def generate_ai_questions(specialty, problem):
    """Generate 3 relevant questions using DeepSeek"""
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
    """Generate professional advice using DeepSeek"""
    prompt = get_specialty_prompt(
        st.session_state.specialty,
        st.session_state.user_data,
        st.session_state.problem,
        st.session_state.answers
    )
    return get_deepseek_response(prompt)

# =============================
# STREAMLIT UI COMPONENTS
# =============================
def main_page():
    st.set_page_config(page_title="AI Health Advisor", page_icon="⚕️", layout="wide")
    st.title("⚕️ Professional Health Advisor")
    st.subheader("Consult with AI specialists")
    
    cols = st.columns(3)
    specialties = ["Nutritionist", "General Physician", "Mental Health"]
    
    for i, specialty in enumerate(specialties):
        with cols[i % 3]:
            if st.button(f"**{specialty}**", use_container_width=True, 
                         help=f"Consult with a {specialty} specialist", key=f"btn_{specialty}"):
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
            st.session_state.question_phase = -1  # Move to problem input

def problem_input():
    with st.form("problem_form"):
        st.subheader(f"Describe your concern to the {st.session_state.specialty}")
        problem = st.text_area("What would you like to discuss?", 
                              placeholder="e.g., I've been experiencing persistent headaches...",
                              height=120)
        
        if st.form_submit_button("Get Professional Advice", type="primary"):
            if problem.strip():
                st.session_state.problem = problem
                
                # Generate AI-driven questions
                with st.spinner("Preparing relevant questions..."):
                    st.session_state.questions = generate_ai_questions(
                        st.session_state.specialty, 
                        problem
                    )
                
                if st.session_state.questions:
                    st.session_state.question_phase = 1
                    st.rerun()
                else:
                    st.error("Failed to generate questions. Please try again.")
            else:
                st.warning("Please describe your concern")

def question_phase():
    current_phase = st.session_state.question_phase
    question_text = st.session_state.questions[current_phase - 1]
    
    with st.container(border=True):
        st.progress(current_phase/3, text=f"Question {current_phase} of 3")
        st.subheader(question_text)
        
        answer = st.text_area("Your response:", height=100, 
                             placeholder="Type your answer here...", 
                             key=f"ans_{current_phase}")
        
        if st.button("Submit Answer", type="primary"):
            if answer.strip():
                st.session_state.answers.append(answer)
                if current_phase < 3:
                    st.session_state.question_phase += 1
                else:
                    st.session_state.question_phase = 4  # Show results
                st.rerun()
            else:
                st.warning("Please provide a response")

def show_professional_advice():
    st.subheader("🧑‍⚕️ Professional Consultation Results")
    st.caption(f"Specialty: {st.session_state.specialty} | Concern: {st.session_state.problem[:50]}...")
    
    with st.spinner("Preparing your personalized recommendations..."):
        advice = get_ai_response()
    
    # Display with professional styling
    st.markdown("---")
    st.markdown(advice, unsafe_allow_html=True)
    st.markdown("---")
    
    # Consultation management
    cols = st.columns([1,1])
    with cols[0]:
        if st.button("🔄 Start New Consultation", use_container_width=True):
            # Reset session state
            for key in list(st.session_state.keys()):
                if key not in ['specialty', 'user_data']:  # Keep specialty and nutrition data
                    del st.session_state[key]
            st.session_state.question_phase = 0
            st.rerun()
    with cols[1]:
        if st.download_button("📥 Save Consultation", advice, 
                             file_name=f"health_advice_{datetime.now().strftime('%Y%m%d')}.txt",
                             use_container_width=True):
            st.success("Download started!")

# =============================
# MAIN APP CONTROLLER
# =============================
def main():
    # Page routing
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
    
    # Add disclaimer to all pages
    st.markdown("---")
    st.caption("**Disclaimer:** This AI provides general information only. It is not medical advice. Consult a healthcare professional for personal medical concerns. Do not ignore professional medical advice or delay seeking it based on AI-generated content.")

if __name__ == "__main__":
    main()
