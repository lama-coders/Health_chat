# file: main.py
import streamlit as st
import requests
import re
import datetime

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
        'chat_started': False,
        'ai_report': None,  # Store the final AI report
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
    st.session_state.ai_report = None
    
    # Clear the trigger flag
    st.session_state["trigger_fresh_start"] = False

for key, val in {
    'specialty': None,
    'user_data': {},
    'question_phase': 0,
    'questions': [],
    'answers': [],
    'problem': "",
    'chat_started': False,
    'ai_report': None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =============================
# Enhanced Prompt Engineering
# =============================
def get_specialty_prompt(specialty, user_data, problem, answers):
    # Enhanced base instructions for detailed, professional responses
    base_task = """
    TASK:
    As a healthcare professional, provide a comprehensive, personalized assessment based on the user's problem and answers. 
    Your response MUST be structured with the following markdown headings and include the specified details:

    ### 📝 Initial Assessment
    - Provide a detailed clinical summary of the problem based on the user's input
    - Include potential underlying causes and risk factors
    - Mention relevant clinical observations based on the information provided

    ### 💡 Professional Recommendations
    - Offer 3-5 specific, evidence-based recommendations
    - Include lifestyle modifications, home care, and preventive measures
    - Provide clear rationales for each recommendation
    - Use bullet points for readability

    ### 💊 Comprehensive Management Plan
    - Outline a step-by-step 4-week action plan with specific timelines
    - Include dietary modifications, exercises, medications, or therapies as appropriate
    - Specify monitoring parameters and follow-up schedule
    - Provide detailed instructions for each phase of the plan

    ### ⚠️ Critical Considerations
    - List red flags that require immediate medical attention
    - Include important contraindications or precautions
    - Specify when to seek professional medical help
    - Add a strong disclaimer that this is AI-generated advice and not a substitute for professional consultation
    """

    # Specialty-specific enhancements
    if specialty == "Nutritionist":
        return f"""
        ROLE: Certified Clinical Nutritionist with 15+ years experience
        HEALTH CONCERN: {problem}
        ADDITIONAL INPUT: {answers}
        
        SPECIAL INSTRUCTIONS:
        - Focus on evidence-based nutritional interventions
        - Include specific food recommendations and meal timing
        - Address micronutrient deficiencies if relevant
        - Provide supplement recommendations with dosing guidelines
        - Include metabolic considerations
        
        {base_task}
        """
    elif specialty == "Physician":
        return f"""
        ROLE: Board-Certified Physician with 20+ years clinical experience
        PATIENT COMPLAINT: {problem}
        RESPONSES: {answers}
        
        SPECIAL INSTRUCTIONS:
        - Conduct a thorough differential diagnosis
        - Discuss both pharmacological and non-pharmacological approaches
        - Include diagnostic considerations and potential tests
        - Address comorbidities and polypharmacy risks
        - Provide detailed medication guidance including dosing and side effects
        
        {base_task}
        """
    elif specialty == "Mental Health":
        return f"""
        ROLE: Licensed Clinical Psychologist specializing in cognitive-behavioral therapy
        CONCERN: {problem}
        RESPONSES: {answers}
        
        SPECIAL INSTRUCTIONS:
        - Include cognitive restructuring techniques
        - Provide specific mindfulness exercises
        - Outline behavioral activation strategies
        - Address coping mechanisms for acute distress
        - Include therapeutic homework assignments
        
        {base_task}
        """
    elif specialty == "Orthopedic":
        return f"""
        ROLE: Senior Orthopedic Surgeon specializing in sports medicine
        COMPLAINT: {problem}
        RESPONSES: {answers}
        
        SPECIAL INSTRUCTIONS:
        - Provide detailed rehabilitation protocols
        - Include specific exercises with proper form instructions
        - Discuss surgical and non-surgical options
        - Address pain management strategies
        - Include return-to-activity guidelines
        
        {base_task}
        """
    elif specialty == "Dentist":
        return f"""
        ROLE: Prosthodontist with expertise in restorative dentistry
        DENTAL ISSUE: {problem}
        RESPONSES: {answers}
        
        SPECIAL INSTRUCTIONS:
        - Provide detailed oral hygiene protocols
        - Include specific techniques for brushing and flossing
        - Discuss preventive strategies for common dental issues
        - Address pain management and emergency care
        - Include professional treatment options with timelines
        
        {base_task}
        """
    return f"""
    ROLE: Senior Healthcare Consultant
    ISSUE: {problem}
    ANSWERS: {answers}
    
    SPECIAL INSTRUCTIONS:
    - Provide comprehensive health guidance
    - Address both acute and chronic aspects
    - Include holistic approaches
    - Focus on preventive strategies
    
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
        "max_tokens": 4096  # Increased for more detailed responses
    }
    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Groq API Error: {str(e)}")
        return "API Error"

# =============================
# Report Download Function
# =============================
def generate_report_download(report_content, specialty):
    """Generate a downloadable report file"""
    # Create a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{specialty}_Report_{timestamp}.txt"
    
    # Format the report content for download
    formatted_report = f"Medical Consultation Report\n"
    formatted_report += f"Specialty: {specialty}\n"
    formatted_report += f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    formatted_report += "="*50 + "\n\n"
    
    # Remove markdown syntax for plain text report
    clean_report = re.sub(r'#{1,6}\s*', '', report_content)  # Remove headings
    clean_report = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', clean_report)  # Remove bold/italic
    clean_report = re.sub(r'-\s+', '* ', clean_report)  # Convert dashes to bullets
    formatted_report += clean_report
    
    return formatted_report, filename

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

if not st.session_state.chat_started:
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
            st.session_state.chat_started = True
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

# Show problem input for all specialties
st.session_state.problem = st.text_area("📝 Describe your health concern:", 
                                        value=st.session_state.problem,
                                        placeholder="Briefly describe your health concern...")

# For all specialties, including Nutritionist
if st.session_state.problem:
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
        
        # User-friendly buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Next Question", key=f"submit_{st.session_state.question_phase}", help="Submit your answer and continue"):
                if answer.strip():
                    st.session_state.answers.append(answer)
                    st.session_state.question_phase += 1
                    st.session_state.question_advance_rerun = True
                else:
                    st.warning("Please provide an answer or get your results.")
        with col2:
            if st.button("🚀 Get My Results", key=f"skip_{st.session_state.question_phase}", help="Skip remaining questions and get AI advice"):
                st.session_state.question_phase = max_questions
                st.session_state.question_advance_rerun = True
        if st.session_state.get("question_advance_rerun", False):
            st.session_state.question_advance_rerun = False  # Reset after rerun
            st.rerun()
    else:
        if st.session_state.ai_report is None:
            st.success("✅ Generating personalized response...")
            with st.spinner("🧠 Analyzing your case with professional expertise..."):
                prompt = get_specialty_prompt(
                    st.session_state.specialty,
                    st.session_state.user_data,
                    st.session_state.problem,
                    st.session_state.answers
                )
                result = get_groq_response(prompt)
                st.session_state.ai_report = result
        
        st.markdown("### 🧠 Professional Medical Assessment")
        
        # Create a container for the report with a border
        report_container = st.container(border=True)
        
        # Process and display the structured response
        try:
            # Split the response into sections
            sections = re.split(r'###\s+', st.session_state.ai_report)
            sections = [s.strip() for s in sections if s.strip()]
            
            # Display each section in the report container
            for section in sections:
                if section:
                    # Split into title and content
                    lines = section.split('\n', 1)
                    title = lines[0].strip()
                    content = lines[1].strip() if len(lines) > 1 else ""
                    
                    # Special formatting for certain sections
                    with report_container:
                        if "Initial Assessment" in title:
                            st.subheader(f"📝 {title}")
                            st.markdown(content)
                        elif "Recommendations" in title:
                            st.subheader(f"💡 {title}")
                            st.markdown(content)
                        elif "Management Plan" in title:
                            st.subheader(f"📋 {title}")
                            st.markdown(content)
                        elif "Critical Considerations" in title:
                            st.subheader(f"⚠️ {title}")
                            st.markdown(content)
                        else:
                            st.subheader(title)
                            st.markdown(content)
        except:
            # Fallback if parsing fails
            with report_container:
                st.markdown(st.session_state.ai_report)
        
        # Download button for the report
        if st.session_state.ai_report:
            report_text, filename = generate_report_download(
                st.session_state.ai_report, 
                st.session_state.specialty
            )
            
            st.download_button(
                label="📥 Download Full Report",
                data=report_text,
                file_name=filename,
                mime="text/plain",
                help="Download your complete medical assessment report",
                use_container_width=True
            )

# Changed "Start Fresh" to "AI Consultation"
if st.button("🤖 New Consultation", help="Start a new consultation with the same specialist"):
    # Use a flag to trigger reset at the top of the script
    st.session_state["trigger_fresh_start"] = True
    st.rerun()
