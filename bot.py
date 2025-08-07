# file: main.py
import streamlit as st
import requests
import re
import datetime
import math
import time
import random
import pandas as pd
import altair as alt

# Set page configuration
st.set_page_config(
    page_title="AI SMART HOSPITAL",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================
# Custom CSS for Animations and Styling
# =============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

:root {
    --primary: #2563eb;
    --secondary: #0ea5e9;
    --accent: #8b5cf6;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --dark: #1e293b;
    --light: #f8fafc;
}

* {
    font-family: 'Montserrat', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
}

/* Header styling */
h1, h2, h3, h4, h5, h6 {
    color: var(--dark) !important;
}

/* Animated buttons */
.stButton>button {
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    position: relative;
    overflow: hidden;
}

.stButton>button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
}

.stButton>button:active {
    transform: translateY(1px) !important;
}

.stButton>button:after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(255, 255, 255, 0.1);
    transform: scale(0, 1);
    transform-origin: top right;
    transition: transform 0.5s;
    z-index: 1;
}

.stButton>button:hover:after {
    transform: scale(1, 1);
    transform-origin: top left;
}

/* Primary buttons */
.stButton>button:first-child:focus:not(:active) {
    background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
    color: white !important;
}

/* Secondary buttons */
.stButton>button:not(:first-child) {
    background: white !important;
    color: var(--primary) !important;
    border: 2px solid var(--primary) !important;
}

/* Containers */
.stContainer {
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    background: white;
    padding: 24px;
    margin-bottom: 24px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 12px !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
}

.stTabs [aria-selected="true"] {
    background: var(--primary) !important;
    color: white !important;
}

/* Metrics */
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

/* Progress bars */
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--primary), var(--accent)) !important;
}

/* Animation for loading */
@keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.05); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
}

.pulse {
    animation: pulse 2s infinite;
}

/* Floating animation */
@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
    100% { transform: translateY(0px); }
}

.floating {
    animation: float 3s ease-in-out infinite;
}

/* Card styling */
.card {
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    background: white;
    padding: 24px;
    transition: all 0.3s ease;
    height: 100%;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.card h3 {
    color: var(--primary) !important;
    margin-top: 0;
}

.card-icon {
    font-size: 2.5rem;
    margin-bottom: 16px;
    color: var(--primary);
}

/* Fix for follow-up question text color */
.stTextInput > label {
    color: var(--dark) !important;
    font-weight: 600 !important;
}


</style>
""", unsafe_allow_html=True)

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
        'in_checkups': False  # Track if we're in the checkups section
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
    'in_checkups': False
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
    formatted_report = f"AI SMART HOSPITAL - Medical Consultation Report\n"
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
            color = "#3b82f6"  # blue
            advice = "You may need to gain some healthy weight."
        elif 18.5 <= bmi < 25:
            category = "Normal Weight"
            color = "#10b981"  # green
            advice = "Great! You're in the healthy weight range."
        elif 25 <= bmi < 30:
            category = "Overweight"
            color = "#f59e0b"  # orange
            advice = "Consider a balanced diet and regular exercise."
        else:
            category = "Obese"
            color = "#ef4444"  # red
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
                color = "#3b82f6"  # blue
            elif 6 <= body_fat < 14:
                category = "Athlete"
                color = "#10b981"  # green
            elif 14 <= body_fat < 18:
                category = "Fitness"
                color = "#86efac"  # lightgreen
            elif 18 <= body_fat < 25:
                category = "Average"
                color = "#f59e0b"  # orange
            else:
                category = "Obese"
                color = "#ef4444"  # red
        else:  # Female
            if body_fat < 16:
                category = "Essential Fat"
                color = "#3b82f6"  # blue
            elif 16 <= body_fat < 21:
                category = "Athlete"
                color = "#10b981"  # green
            elif 21 <= body_fat < 25:
                category = "Fitness"
                color = "#86efac"  # lightgreen
            elif 25 <= body_fat < 32:
                category = "Average"
                color = "#f59e0b"  # orange
            else:
                category = "Obese"
                color = "#ef4444"  # red
                
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
# Visual Chart Functions
# =============================
def create_bmi_chart(bmi_value):
    # Create BMI ranges
    categories = ["Underweight", "Normal", "Overweight", "Obese"]
    ranges = [18.5, 25, 30]
    
    # Create a DataFrame for the chart
    data = pd.DataFrame({
        'Category': categories,
        'Min': [0, 18.5, 25, 30],
        'Max': [18.5, 25, 30, 40]
    })
    
    # Create the chart
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('Min:Q', axis=alt.Axis(title='BMI Value')),
        x2='Max:Q',
        y=alt.Y('Category:N', axis=None),
        color=alt.Color('Category:N', scale=alt.Scale(
            domain=['Underweight', 'Normal', 'Overweight', 'Obese'],
            range=['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
        ), legend=None),
        tooltip=['Category', 'Min', 'Max']
    ).properties(
        height=100
    )
    
    # Add a rule for the user's BMI
    rule = alt.Chart(pd.DataFrame({'value': [bmi_value]})).mark_rule(
        color='black',
        strokeWidth=3
    ).encode(
        x='value:Q'
    )
    
    # Add a point for the user's BMI
    point = alt.Chart(pd.DataFrame({'value': [bmi_value]})).mark_point(
        size=100,
        filled=True,
        color='black'
    ).encode(
        x='value:Q',
        y=alt.value(20)
    )
    
    # Combine the charts
    final_chart = (chart + rule + point).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False
    )
    
    return final_chart

def create_body_fat_chart(body_fat, gender):
    # Define body fat ranges based on gender
    if gender == "Male":
        ranges = [
            {"category": "Essential", "min": 2, "max": 5, "color": "#3b82f6"},
            {"category": "Athlete", "min": 6, "max": 13, "color": "#10b981"},
            {"category": "Fitness", "min": 14, "max": 17, "color": "#86efac"},
            {"category": "Average", "min": 18, "max": 24, "color": "#f59e0b"},
            {"category": "Obese", "min": 25, "max": 40, "color": "#ef4444"}
        ]
    else:
        ranges = [
            {"category": "Essential", "min": 10, "max": 13, "color": "#3b82f6"},
            {"category": "Athlete", "min": 14, "max": 20, "color": "#10b981"},
            {"category": "Fitness", "min": 21, "max": 24, "color": "#86efac"},
            {"category": "Average", "min": 25, "max": 31, "color": "#f59e0b"},
            {"category": "Obese", "min": 32, "max": 45, "color": "#ef4444"}
        ]
    
    # Create a DataFrame for the chart
    data = pd.DataFrame(ranges)
    
    # Create the chart
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('min:Q', title='Body Fat Percentage'),
        x2='max:Q',
        y=alt.Y('category:N', axis=None),
        color=alt.Color('category:N', scale=alt.Scale(
            domain=data['category'].tolist(),
            range=data['color'].tolist()
        ), legend=None),
        tooltip=['category', 'min', 'max']
    ).properties(
        height=150
    )
    
    # Add a rule for the user's body fat
    rule = alt.Chart(pd.DataFrame({'value': [body_fat]})).mark_rule(
        color='black',
        strokeWidth=3
    ).encode(
        x='value:Q'
    )
    
    # Add a point for the user's body fat
    point = alt.Chart(pd.DataFrame({'value': [body_fat]})).mark_point(
        size=100,
        filled=True,
        color='black'
    ).encode(
        x='value:Q',
        y=alt.value(20)
    )
    
    # Combine the charts
    final_chart = (chart + rule + point).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False
    )
    
    return final_chart

def create_calorie_chart(maintain, mild_loss, loss, extreme_loss):
    # Create data for the chart
    data = pd.DataFrame({
        'Goal': ['Maintain Weight', 'Mild Loss (0.25kg/week)', 'Loss (0.5kg/week)', 'Extreme Loss (1kg/week)'],
        'Calories': [maintain, mild_loss, loss, extreme_loss]
    })
    
    # Create the chart
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X('Calories:Q', title='Calories per Day'),
        y=alt.Y('Goal:N', sort='-x', title='Weight Goal'),
        color=alt.Color('Goal:N', legend=None),
        tooltip=['Goal', 'Calories']
    ).properties(
        height=300
    )
    
    return chart

# =============================
# UI LAYOUT - HOME PAGE
# =============================
if st.session_state.current_page == 'home':
    # Header with animation
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("<div class='floating'>🏥</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<h1 style='margin-bottom: 0;'>AI SMART HOSPITAL</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #4b5563; margin-top: 0;'>Your AI-Powered Healthcare Companion</h3>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div style='text-align: center; margin-bottom: 32px;'>
        <h3>Advanced AI diagnostics combined with comprehensive health analytics</h3>
        <p>Get instant medical guidance from AI specialists or use our advanced health calculators to monitor your wellness metrics.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature cards
    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            st.markdown("""
            <div class='card'>
                <div class='card-icon'>👨‍⚕️</div>
                <h3>Medical Checkups</h3>
                <p>Consult with AI medical specialists for personalized health assessments and treatment plans.</p>
                <p><strong>Specialties:</strong> Physician, Nutritionist, Mental Health, Orthopedic, Dentist</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Start Medical Checkup", key="checkups_btn", use_container_width=True):
                st.session_state.current_page = 'checkups'
                st.session_state.in_checkups = True
                st.session_state.chat_started = False
                st.rerun()
    
    with col2:
        with st.container():
            st.markdown("""
            <div class='card'>
                <div class='card-icon'>🔬</div>
                <h3>Medical Lab</h3>
                <p>Access advanced health calculators and analytics tools to monitor your wellness metrics.</p>
                <p><strong>Tools:</strong> BMI Calculator, Body Fat %, Calorie Needs, Health Analytics</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Visit Medical Lab", key="lab_btn", use_container_width=True):
                st.session_state.current_page = 'lab'
                st.rerun()
    
    st.markdown("---")
    
    # Testimonials
    st.subheader("Patient Experiences")
    cols = st.columns(3)
    testimonials = [
        {"name": "Sarah T.", "text": "The AI physician accurately diagnosed my migraine triggers and provided a comprehensive management plan that actually worked!"},
        {"name": "Michael R.", "text": "The nutritionist AI helped me lose 15kg in 3 months with personalized meal plans and lifestyle recommendations."},
        {"name": "Emma K.", "text": "The mental health specialist gave me practical techniques to manage my anxiety that I use every day."}
    ]
    
    for i, testimonial in enumerate(testimonials):
        with cols[i]:
            st.markdown(f"""
            <div class='card'>
                <div style='padding: 16px; background: #f0f9ff; border-radius: 12px;'>
                    <p style='font-style: italic;'>"{testimonial['text']}"</p>
                    <p style='text-align: right; font-weight: bold;'>— {testimonial['name']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px; color: #64748b;'>
        <p>AI SMART HOSPITAL • Advanced AI Diagnostics • Personalized Healthcare</p>
        <p>Note: This tool provides AI-generated advice and should not replace professional medical consultation.</p>
    </div>
    """, unsafe_allow_html=True)

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
    
    specialty_icons = {
        "Nutritionist": "🥗",
        "Physician": "👨‍⚕️",
        "Mental Health": "🧠",
        "Orthopedic": "🦴",
        "Dentist": "🦷"
    }
    
    # Specialty selection page
    if not st.session_state.chat_started:
        st.title("👨‍⚕️ AI Medical Checkups")
        
        # Back to home page button
        if st.button("🏠 Home", help="Go back to main menu"):
            st.session_state.current_page = 'home'
            st.rerun()
        
        st.markdown("""
        <div style='text-align: center; margin: 30px 0;'>
            <h2>Select a Specialist</h2>
            <p>Choose an AI specialist for personalized healthcare consultation</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Specialty cards
        specialties = list(specialty_title_map.keys())
        cols = st.columns(len(specialties))
        for i, name in enumerate(specialties):
            with cols[i]:
                st.markdown(f"""
                <div class='card' style='text-align: center;'>
                    <div style='font-size: 3rem;'>{specialty_icons[name]}</div>
                    <h3>{name}</h3>
                    <p>{specialty_title_map[name]}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Consult with {name}", key=f"spec_{name}"):
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
    col1, col2, col3 = st.columns([3, 3, 2])
    with col1:
        st.title(f"{specialty_icons.get(st.session_state.specialty, '🩺')} {specialty_title_map.get(st.session_state.specialty)}")
    with col2:
        st.markdown(f"<div style='margin-top: 25px;'><strong>Patient Consultation</strong></div>", unsafe_allow_html=True)
    with col3:
        if st.button("🏠 Home", help="Go back to main menu", use_container_width=True):
            st.session_state.current_page = 'home'
            st.rerun()
        if st.button("⬅️ Back to Specialties", help="Go back to specialty selection", use_container_width=True):
            st.session_state.chat_started = False
            st.session_state.specialty = None
            st.rerun()
    
    # Show problem input for all specialties
    st.markdown("### 📝 Describe Your Health Concern")
    st.session_state.problem = st.text_area(
        "Please describe your symptoms or health concern in detail:", 
        value=st.session_state.problem,
        placeholder="Example: I've been experiencing persistent headaches for the past week, especially in the afternoons...",
        height=150
    )
    
    # For all specialties, including Nutritionist
    if st.session_state.problem:
        st.markdown("---")
        st.markdown("### 📋 Follow-up Questions")
        
        # Generate questions dynamically based on problem and specialty
        max_questions = 3  # Limit to 3 questions for better UX
        
        if st.session_state.question_phase < max_questions:
            # Generate current question dynamically
            if st.session_state.question_phase >= len(st.session_state.questions):
                with st.spinner("🔍 Generating relevant question..."):
                    new_question = generate_follow_up_question(
                        st.session_state.specialty,
                        st.session_state.problem,
                        st.session_state.answers,
                        st.session_state.question_phase + 1
                    )
                    st.session_state.questions.append(new_question)
            
            # Display current question
            st.markdown(f"<div class='pulse' style='font-size: 1.2rem; padding: 16px; background: #2563eb; color: white; border-radius: 12px; margin-bottom: 16px;'>{st.session_state.questions[st.session_state.question_phase]}</div>", unsafe_allow_html=True)
            
            # Use regular text input without form
            answer = st.text_input("Your answer:", key=f"q_{st.session_state.question_phase}", placeholder="Type your response here...")
            
            # User-friendly buttons
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✅ Submit & Continue", key=f"submit_{st.session_state.question_phase}", help="Submit your answer and continue", use_container_width=True):
                    if answer.strip():
                        st.session_state.answers.append(answer)
                        st.session_state.question_phase += 1
                        st.session_state.question_advance_rerun = True
                    else:
                        st.warning("Please provide an answer or get your results.")
            with col2:
                if st.button("🚀 Skip to Results", key=f"skip_{st.session_state.question_phase}", help="Skip remaining questions and get AI advice", use_container_width=True):
                    st.session_state.question_phase = max_questions
                    st.session_state.question_advance_rerun = True
            if st.session_state.get("question_advance_rerun", False):
                st.session_state.question_advance_rerun = False  # Reset after rerun
                st.rerun()
        else:
            if st.session_state.ai_report is None:
                with st.spinner("🧠 Analyzing your case with professional expertise..."):
                    # Add a small delay to simulate processing
                    time.sleep(1.5)
                    prompt = get_specialty_prompt(
                        st.session_state.specialty,
                        st.session_state.user_data,
                        st.session_state.problem,
                        st.session_state.answers
                    )
                    result = get_groq_response(prompt)
                    st.session_state.ai_report = result
            
            st.markdown("---")
            st.markdown("## 🧠 Professional Medical Assessment")
            
            # Create a container for the report with a border
            with st.container(border=True):
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
                            # The #1e293b color is the --dark variable
                            if "Initial Assessment" in title:
                                st.subheader(f"📝 {title}")
                                st.markdown(f"<div style='color: #1e293b;'>{content}</div>", unsafe_allow_html=True)
                            elif "Recommendations" in title:
                                st.subheader(f"💡 {title}")
                                st.markdown(f"<div style='color: #1e293b;'>{content}</div>", unsafe_allow_html=True)
                            elif "Management Plan" in title:
                                st.subheader(f"📋 {title}")
                                st.markdown(f"<div style='color: #1e293b;'>{content}</div>", unsafe_allow_html=True)
                            elif "Critical Considerations" in title:
                                st.markdown("<div style='padding: 16px; background: #fffbeb; border-radius: 12px; color: #1e293b;'>", unsafe_allow_html=True)
                                st.subheader(f"⚠️ {title}")
                                st.markdown(content) # Markdown inside this div will inherit the color
                                st.markdown("</div>", unsafe_allow_html=True)
                            else:
                                st.subheader(title)
                                st.markdown(f"<div style='color: #1e293b;'>{content}</div>", unsafe_allow_html=True)
                except:
                    # Fallback if parsing fails
                    st.markdown(f"<div style='color: #1e293b;'>{st.session_state.ai_report}</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Download button for the report
            if st.session_state.ai_report:
                report_text, filename = generate_report_download(
                    st.session_state.ai_report, 
                    st.session_state.specialty
                )
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info("💡 You can download your full medical assessment report")
                with col2:
                    st.download_button(
                        label="📥 Download Full Report",
                        data=report_text,
                        file_name=filename,
                        mime="text/plain",
                        help="Download your complete medical assessment report",
                        use_container_width=True
                    )
    
    # New consultation button
    st.markdown("---")
    if st.button("🔄 Start New Consultation", help="Start a new consultation with the same specialist", use_container_width=True):
        # Use a flag to trigger reset at the top of the script
        st.session_state["trigger_fresh_start"] = True
        st.rerun()

# =============================
# UI LAYOUT - MEDICAL LAB
# =============================
elif st.session_state.current_page == 'lab':
    st.title("🔬 Medical Lab Tools")
    
    # Back to home page button
    if st.button("🏠 Home", help="Go back to main menu", use_container_width=True):
        st.session_state.current_page = 'home'
        st.rerun()
    
    # Create tabs for different calculators
    tab_bmi, tab_bodyfat, tab_calories, tab_analytics = st.tabs([
        "📏 BMI Calculator", 
        "📊 Body Fat %", 
        "🍎 Calorie Needs",
        "📈 Health Analytics"
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
                        st.metric("BMI Score", f"{bmi}", help="Body Mass Index")
                    with col2:
                        st.metric("Category", category, delta_color="off", help="Weight category based on BMI")
                    with col3:
                        st.metric("Age", f"{age} years", help="Your current age")
                    
                    # Visual BMI chart
                    st.markdown("### BMI Category Visualization")
                    st.altair_chart(create_bmi_chart(bmi), use_container_width=True)
                    
                    # Health advice based on BMI
                    st.markdown(f"### Health Advice")
                    st.markdown(f"<div style='padding: 16px; background: #f0fdf4; border-radius: 12px;'>{advice}</div>", unsafe_allow_html=True)
                    
                    # BMI chart reference
                    st.markdown("### BMI Categories Reference:")
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
                        st.metric("Body Fat Percentage", f"{body_fat}%", help="Estimated body fat percentage")
                    with col2:
                        st.metric("Category", category, delta_color="off", help="Body composition category")
                    
                    # Visual body fat chart
                    st.markdown("### Body Fat Visualization")
                    st.altair_chart(create_body_fat_chart(body_fat, gender), use_container_width=True)
                    
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
                    st.metric("Maintain Weight", f"{maintain} calories/day", help="Calories needed to maintain current weight")
                    
                    st.markdown("### Weight Loss Goals:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Mild Loss (0.25 kg/week)", f"{mild_loss} cal", help="10% calorie deficit")
                    with col2:
                        st.metric("Loss (0.5 kg/week)", f"{loss} cal", help="21% calorie deficit")
                    with col3:
                        st.metric("Extreme Loss (1 kg/week)", f"{extreme_loss} cal", help="41% calorie deficit")
                    
                    # Visual calorie chart
                    st.markdown("### Calorie Goals Visualization")
                    st.altair_chart(create_calorie_chart(maintain, mild_loss, loss, extreme_loss), use_container_width=True)
                    
                    st.info("💡 A safe calorie deficit is 300-500 calories below maintenance")
                    
                    st.markdown("### Nutrition Tips:")
                    st.markdown("""
                    - 🥦 Focus on protein-rich foods to preserve muscle mass
                    - 💧 Drink at least 2 liters of water daily
                    - ⏱️ Eat regular meals to maintain metabolism
                    - 🥑 Include healthy fats like avocado and nuts
                    - 🍎 Prioritize whole foods over processed options
                    """)
            else:
                st.error("Please enter valid information.")
    
    # Health Analytics Tab
    with tab_analytics:
        st.subheader("Health Trend Analytics")
        st.markdown("Visualize and track your health metrics over time.")
        
        # Sample health data
        dates = pd.date_range(start="2023-01-01", periods=12, freq="M")
        weight_data = [72, 71.5, 70.8, 70.2, 69.7, 69.5, 69.0, 68.5, 68.0, 67.8, 67.5, 67.0]
        bmi_data = [round(w / (1.75**2), 1) for w in weight_data]
        calorie_data = [random.randint(1800, 2200) for _ in range(12)]
        
        # Create data frame
        health_df = pd.DataFrame({
            "Month": dates,
            "Weight (kg)": weight_data,
            "BMI": bmi_data,
            "Calories": calorie_data
        })
        
        # Weight chart
        st.markdown("#### Weight Trend")
        weight_chart = alt.Chart(health_df).mark_line(point=True).encode(
            x=alt.X('Month:T', axis=alt.Axis(title='Date')),
            y=alt.Y('Weight (kg):Q', axis=alt.Axis(title='Weight (kg)')),
            tooltip=['Month', 'Weight (kg)']
        ).properties(height=300)
        st.altair_chart(weight_chart, use_container_width=True)
        
        # BMI chart
        st.markdown("#### BMI Trend")
        bmi_chart = alt.Chart(health_df).mark_line(point=True, color='orange').encode(
            x=alt.X('Month:T', axis=alt.Axis(title='Date')),
            y=alt.Y('BMI:Q', axis=alt.Axis(title='BMI')),
            tooltip=['Month', 'BMI']
        ).properties(height=300)
        st.altair_chart(bmi_chart, use_container_width=True)
        
        # Calories chart
        st.markdown("#### Daily Calorie Intake")
        calorie_chart = alt.Chart(health_df).mark_bar().encode(
            x=alt.X('Month:T', axis=alt.Axis(title='Date')),
            y=alt.Y('Calories:Q', axis=alt.Axis(title='Calories')),
            tooltip=['Month', 'Calories'],
            color=alt.value('#8b5cf6')
        ).properties(height=300)
        st.altair_chart(calorie_chart, use_container_width=True)
        
        # Health insights
        st.markdown("#### Health Insights")
        st.markdown("""
        - Your weight has shown a consistent downward trend over the past year
        - BMI has decreased from 23.5 to 21.9, moving toward the optimal range
        - Calorie intake has remained relatively stable with minor fluctuations
        - Continue your current regimen for continued progress
        """)
    
    # Coming Soon Section
    st.markdown("---")
    st.subheader("🔜 More Lab Tools Coming Soon")
    st.markdown("""
    We're expanding our medical lab with new tools:
    - Heart Rate Zones Calculator
    - Hydration Calculator
    - Macronutrient Calculator
    - Sleep Quality Analyzer
    - Stress Level Assessment
    """)
    st.info("Check back soon for these new features!")
