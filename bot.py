# file: main.py
import streamlit as st
import requests
import re
from PIL import Image, ImageDraw, ImageFont
import io

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
# SESSION STATE INIT & RESET LOGIC
# =============================

# --- Reset Triggers ---
# This section handles resets triggered by buttons. It runs before the main initialization.

# 1. Main Menu Reset: Clears everything and returns to the specialty selection screen.
if st.session_state.get("reset_app", False):
    st.session_state.clear()
    st.session_state["reset_app"] = False # Reset the trigger

# 2. Start Fresh Reset: Clears only the question/answer flow, preserving specialty and problem.
if st.session_state.get("trigger_fresh_start", False):
    # Preserve important data that should not be reset
    specialty = st.session_state.get("specialty", None)
    problem = st.session_state.get("problem", "")
    user_data = st.session_state.get("user_data", {})
    profile_collected = st.session_state.get("profile_collected", False)
    
    # Only reset the question/answer flow
    st.session_state.question_phase = 0
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.chat_started = False
    
    # Reset the trigger
    st.session_state.trigger_fresh_start = False

# --- Main Initialization ---
# This loop ensures all necessary keys are present in the session state.
# It runs on every script rerun, guaranteeing a consistent state.

# Define the default state of the application
default_state = {
    'specialty': None,
    'user_data': {},
    'question_phase': 0,
    'questions': [],
    'answers': [],
    'problem': "",
    'profile_collected': False,
    'chat_started': False,
    'nutritionist_submit_attempted': False
}

# Initialize each key if it's not already in the session state
for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

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
def create_report_image(report_data):
    """Generates a professional-looking report image from structured text data."""
    width, height = 800, 1000
    bg_color = "white"
    font_color = "black"
    padding = 40

    # Create a blank image
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # Load fonts (try common fonts, fall back to default)
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 36)
        header_font = ImageFont.truetype("arialbd.ttf", 24)
        body_font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # Draw Header
    draw.text((padding, padding), "AI Health Report", font=title_font, fill=font_color)
    draw.line([(padding, 80), (width - padding, 80)], fill="#cccccc", width=2)

    # Draw sections
    y_pos = 100
    for section in report_data:
        title, content = section['title'], section['content']
        
        # Draw section title
        draw.text((padding, y_pos), title, font=header_font, fill=font_color)
        y_pos += 40

        # Draw section content with text wrapping
        lines = content.split('\n')
        for line in lines:
            # Simple wrap for long lines
            if body_font.getlength(line) > (width - 2 * padding):
                words = line.split()
                wrapped_line = ""
                for word in words:
                    if body_font.getlength(wrapped_line + word) < (width - 2 * padding):
                        wrapped_line += word + " "
                    else:
                        draw.text((padding, y_pos), wrapped_line, font=body_font, fill=font_color)
                        y_pos += 20
                        wrapped_line = word + " "
                draw.text((padding, y_pos), wrapped_line, font=body_font, fill=font_color)
                y_pos += 20
            else:
                draw.text((padding, y_pos), line, font=body_font, fill=font_color)
                y_pos += 20
        y_pos += 20 # Extra space between sections

    # Save image to a bytes buffer
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

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
            st.session_state.profile_collected = False
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

# Special handling for Nutritionist specialty
if st.session_state.specialty == "Nutritionist":
    if not st.session_state.profile_collected:
        # Friendly welcome message for Nutritionist
        st.markdown("""
        ### 🌟 Hey there! Welcome to your Nutrition Journey! 🌱
        
        Before we dive into your health concerns, let's calculate your **perfect weight range** and understand your current health status better! 
        
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
                            bmi_color = "blue"
                            advice = "You may need to gain some healthy weight."
                        elif 18.5 <= bmi < 25:
                            bmi_category = "Normal Weight"
                            bmi_color = "green"
                            advice = "Great! You're in the healthy weight range."
                        elif 25 <= bmi < 30:
                            bmi_category = "Overweight"
                            bmi_color = "orange"
                            advice = "Consider a balanced diet and regular exercise."
                        else:
                            bmi_category = "Obese"
                            bmi_color = "red"
                            advice = "Let's work together on a healthy weight management plan."
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
        
        # Health advice based on BMI
        bmi_category = st.session_state.user_data['bmi_category']
        if bmi_category == "Normal Weight":
            st.success(f"✅ {st.session_state.user_data['health_advice']}")
        elif bmi_category in ["Underweight", "Overweight"]:
            st.warning(f"⚠️ {st.session_state.user_data['health_advice']}")
        else:
            st.info(f"💪 {st.session_state.user_data['health_advice']}")
        
        st.markdown("---")
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
    # For all other specialties, show the regular problem input
    st.session_state.problem = st.text_area("📝 Describe your health concern:", value=st.session_state.problem)

if st.session_state.problem and (st.session_state.specialty != "Nutritionist" or st.session_state.chat_started):
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
        
        report_data = []
        for section_text in grouped_parts:
            lines = section_text.split('\n', 1)
            if lines:
                title = lines[0].replace('###', '').strip()
                content = lines[1].strip() if len(lines) > 1 else ""
                report_data.append({'title': title, 'content': content})

        # Display sections in expanders
        for section in report_data:
            with st.expander(f"**{section['title']}**", expanded=True):
                st.markdown(section['content'], unsafe_allow_html=True)

        # Add download button if report data exists
        if report_data:
            st.markdown("---")
            image_buffer = create_report_image(report_data)
            st.download_button(
                label="📥 Download Report as Image",
                data=image_buffer,
                file_name="ai_health_report.png",
                mime="image/png",
                help="Download a PNG image of the report."
            )

# Start Over button with improved handling
if st.button("🔄 Start Fresh", help="Clear all data and start over with this specialty"):
    # Use a flag to trigger reset at the top of the script
    st.session_state["trigger_fresh_start"] = True
    st.rerun()














