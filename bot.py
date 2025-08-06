# file: main.py
import streamlit as st
import requests
import re
import datetime
import math

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
        'current_page': 'home',
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
    'current_page': 'home',
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
# Calculator Functions
# =============================
def calculate_bmi(weight, height):
    try:
        bmi = round(weight / ((height/100)**2), 1)
        if bmi < 18.5:
            category = "Underweight"
            color = "blue"
            advice = "You may need to gain some healthy weight."
        elif 18.5 <= bmi < 25:
            category = "Normal Weight"
            color = "green"
            advice = "Great! You're in the healthy weight range."
        elif 25 <= bmi < 30:
            category = "Overweight"
            color = "orange"
            advice = "Consider a balanced diet and regular exercise."
        else:
            category = "Obese"
            color = "red"
            advice = "Let's work together on a healthy weight management plan."
        
        return bmi, category, advice, color
    except:
        return None, None, None, None

def calculate_body_fat(gender, waist, neck, height, hip=None):
    try:
        if gender == "Male":
            # US Navy method for men
            body_fat = 86.010 * math.log10(waist - neck) - 70.041 * math.log10(height) + 36.76
        else:
            # US Navy method for women
            body_fat = 163.205 * math.log10(waist + (hip or 0) - neck) - 97.684 * math.log10(height) - 78.387
        
        body_fat = round(body_fat, 1)
        
        # Body fat categories
        if gender == "Male":
            if body_fat < 6:
                category = "Essential Fat"
                color = "blue"
            elif 6 <= body_fat < 14:
                category = "Athlete"
                color = "green"
            elif 14 <= body_fat < 18:
                category = "Fitness"
                color = "lightgreen"
            elif 18 <= body_fat < 25:
                category = "Average"
                color = "orange"
            else:
                category = "Obese"
                color = "red"
        else:  # Female
            if body_fat < 16:
                category = "Essential Fat"
                color = "blue"
            elif 16 <= body_fat < 21:
                category = "Athlete"
                color = "green"
            elif 21 <= body_fat < 25:
                category = "Fitness"
                color = "lightgreen"
            elif 25 <= body_fat < 32:
                category = "Average"
                color = "orange"
            else:
                category = "Obese"
                color = "red"
                
        return body_fat, category, color
    except:
        return None, None, None

def calculate_calorie_needs(gender, age, weight, height, activity_level):
    try:
        # Basal Metabolic Rate (BMR) calculation
        if gender == "Male":
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
        # Activity multipliers
        activity_multipliers = {
            "Sedentary (little or no exercise)": 1.2,
            "Lightly active (light exercise 1-3 days/week)": 1.375,
            "Moderately active (moderate exercise 3-5 days/week)": 1.55,
            "Very active (hard exercise 6-7 days/week)": 1.725,
            "Extra active (very hard exercise & physical job)": 1.9
        }
        
        # Total Daily Energy Expenditure (TDEE)
        tdee = bmr * activity_multipliers.get(activity_level, 1.2)
        
        # Weight goals
        maintain = round(tdee)
        mild_loss = round(tdee * 0.9)  # 10% deficit
        loss = round(tdee * 0.79)      # 21% deficit
        extreme_loss = round(tdee * 0.59)  # 41% deficit
        
        return maintain, mild_loss, loss, extreme_loss
    except:
        return None, None, None, None

# =============================
# UI LAYOUT - HOME PAGE
# =============================
if st.session_state.current_page == 'home':
    st.title("🏥 Health Assistant Hub")
    st.markdown("""
    Welcome to your personal health assistant! Get instant medical guidance from AI specialists 
    or use our health calculators to monitor your wellness metrics.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍⚕️ Medical Checkups", help="Consult with AI medical specialists", use_container_width=True):
            st.session_state.current_page = 'checkups'
            st.rerun()
        st.markdown("""
        **Get AI consultations with specialists:**
        - Physician
        - Nutritionist
        - Mental Health
        - Orthopedic
        - Dentist
        """)
    
    with col2:
        if st.button("🔬 Medical Lab", help="Access health calculators and tools", use_container_width=True):
            st.session_state.current_page = 'lab'
            st.rerun()
        st.markdown("""
        **Health calculators and tools:**
        - BMI Calculator
        - Body Fat Percentage
        - Calorie Needs
        - More tools coming soon...
        """)
    
    st.markdown("---")
    st.info("💡 Remember: This tool provides AI-generated advice and should not replace professional medical consultation.")

# =============================
# UI LAYOUT - MEDICAL CHECKUPS
# =============================
elif st.session_state.current_page == 'checkups':
    specialty_title_map = {
        "Nutritionist": "Nutrition Specialist",
        "Physician": "Physician",
        "Mental Health": "Mental Health Expert",
        "Orthopedic": "Orthopedic Surgeon",
        "Dentist": "Dental Specialist"
    }
    
    # Specialty selection page
    if not st.session_state.chat_started:
        st.title("👨‍⚕️ Medical Checkups")
        st.subheader("Select a Specialist")
        
        # Back to home page button
        if st.button("🏠 Home", help="Go back to main menu"):
            st.session_state.current_page = 'home'
            st.rerun()
        
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
    
    # Specialty chat page
    # Add navigation header with back button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"🩺 {specialty_title_map.get(st.session_state.specialty)}")
    with col2:
        if st.button("🏠 Home", help="Go back to main menu"):
            st.session_state.current_page = 'home'
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

# =============================
# UI LAYOUT - MEDICAL LAB
# =============================
elif st.session_state.current_page == 'lab':
    st.title("🔬 Medical Lab Tools")
    
    # Back to home page button
    if st.button("🏠 Home", help="Go back to main menu"):
        st.session_state.current_page = 'home'
        st.rerun()
    
    # Create tabs for different calculators
    tab_bmi, tab_bodyfat, tab_calories = st.tabs([
        "📏 BMI Calculator", 
        "📊 Body Fat %", 
        "🍎 Calorie Needs"
    ])
    
    # BMI Calculator Tab
    with tab_bmi:
        st.subheader("Body Mass Index (BMI) Calculator")
        st.markdown("Calculate your Body Mass Index to understand your weight status.")
        
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age (years)", min_value=1, max_value=120, value=25, key="bmi_age")
            weight = st.number_input("Weight (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.1, key="bmi_weight")
        with col2:
            height = st.number_input("Height (cm)", min_value=50, max_value=250, value=170, key="bmi_height")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="bmi_gender")
        
        if st.button("Calculate BMI", type="primary", key="bmi_calc", use_container_width=True):
            bmi, category, advice, color = calculate_bmi(weight, height)
            
            if bmi:
                st.markdown("---")
                st.subheader("Your BMI Results")
                
                # Create a container for results
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("BMI Score", f"{bmi}")
                    with col2:
                        st.metric("Category", category)
                    with col3:
                        st.metric("Age", f"{age} years")
                    
                    # Health advice based on BMI
                    if color == "green":
                        st.success(f"✅ {advice}")
                    elif color == "orange":
                        st.warning(f"⚠️ {advice}")
                    elif color == "red":
                        st.error(f"❗ {advice}")
                    else:
                        st.info(f"💡 {advice}")
                    
                    # BMI chart
                    st.markdown("### BMI Categories:")
                    st.markdown("""
                    - **Underweight**: < 18.5
                    - **Normal weight**: 18.5 - 24.9
                    - **Overweight**: 25 - 29.9
                    - **Obese**: ≥ 30
                    """)
            else:
                st.error("Please enter valid weight and height values.")
    
    # Body Fat Percentage Tab
    with tab_bodyfat:
        st.subheader("Body Fat Percentage Calculator")
        st.markdown("Estimate your body fat percentage using the US Navy method.")
        
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("Gender", ["Male", "Female"], key="bf_gender")
            waist = st.number_input("Waist Circumference (cm)", min_value=50, max_value=200, value=80, key="bf_waist")
            neck = st.number_input("Neck Circumference (cm)", min_value=20, max_value=60, value=38, key="bf_neck")
        with col2:
            height = st.number_input("Height (cm)", min_value=50, max_value=250, value=170, key="bf_height")
            if gender == "Female":
                hip = st.number_input("Hip Circumference (cm)", min_value=50, max_value=200, value=95, key="bf_hip")
            else:
                hip = None
                st.info("👤 Hip measurement not required for men")
        
        if st.button("Calculate Body Fat %", type="primary", key="bf_calc", use_container_width=True):
            body_fat, category, color = calculate_body_fat(gender, waist, neck, height, hip)
            
            if body_fat:
                st.markdown("---")
                st.subheader("Your Body Fat Results")
                
                with st.container(border=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Body Fat Percentage", f"{body_fat}%")
                    with col2:
                        st.metric("Category", category)
                    
                    # Visual indicator
                    st.progress(min(body_fat/50, 1.0), text=f"Body Fat: {body_fat}%")
                    
                    # Body fat categories
                    st.markdown("### Body Fat Categories:")
                    if gender == "Male":
                        st.markdown("""
                        - **Essential**: 2-5%
                        - **Athlete**: 6-13%
                        - **Fitness**: 14-17%
                        - **Average**: 18-24%
                        - **Obese**: 25%+
                        """)
                    else:
                        st.markdown("""
                        - **Essential**: 10-13%
                        - **Athlete**: 14-20%
                        - **Fitness**: 21-24%
                        - **Average**: 25-31%
                        - **Obese**: 32%+
                        """)
            else:
                st.error("Please enter valid measurements.")
    
    # Calorie Needs Tab
    with tab_calories:
        st.subheader("Daily Calorie Needs Calculator")
        st.markdown("Calculate your daily calorie requirements based on your activity level.")
        
        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("Gender", ["Male", "Female"], key="cal_gender")
            age = st.number_input("Age (years)", min_value=1, max_value=120, value=30, key="cal_age")
            weight = st.number_input("Weight (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.1, key="cal_weight")
        with col2:
            height = st.number_input("Height (cm)", min_value=50, max_value=250, value=170, key="cal_height")
            activity_level = st.selectbox("Activity Level", [
                "Sedentary (little or no exercise)",
                "Lightly active (light exercise 1-3 days/week)",
                "Moderately active (moderate exercise 3-5 days/week)",
                "Very active (hard exercise 6-7 days/week)",
                "Extra active (very hard exercise & physical job)"
            ], key="cal_activity")
        
        if st.button("Calculate Calorie Needs", type="primary", key="cal_calc", use_container_width=True):
            maintain, mild_loss, loss, extreme_loss = calculate_calorie_needs(
                gender, age, weight, height, activity_level
            )
            
            if maintain:
                st.markdown("---")
                st.subheader("Your Daily Calorie Needs")
                
                with st.container(border=True):
                    st.metric("Maintain Weight", f"{maintain} calories/day")
                    
                    st.markdown("### Weight Loss Goals:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Mild Loss (0.25 kg/week)", f"{mild_loss} cal")
                    with col2:
                        st.metric("Loss (0.5 kg/week)", f"{loss} cal")
                    with col3:
                        st.metric("Extreme Loss (1 kg/week)", f"{extreme_loss} cal")
                    
                    st.info("💡 A safe calorie deficit is 300-500 calories below maintenance")
                    
                    st.markdown("### Nutrition Tips:")
                    st.markdown("""
                    - 🥦 Focus on protein-rich foods to preserve muscle mass
                    - 💧 Drink at least 2 liters of water daily
                    - ⏱️ Eat regular meals to maintain metabolism
                    - 🥑 Include healthy fats like avocado and nuts
                    """)
            else:
                st.error("Please enter valid information.")
    
    # Coming Soon Section
    st.markdown("---")
    st.subheader("🔜 More Lab Tools Coming Soon")
    st.markdown("""
    We're expanding our medical lab with new tools:
    - Heart Rate Zones Calculator
    - Ideal Weight Calculator
    - Hydration Calculator
    - Macronutrient Calculator
    """)
    st.info("Check back soon for these new features!")
