# ============================================================================
# SECTION 1: IMPORTS AND INITIAL SETUP
# ============================================================================
import streamlit as st
import json
from datetime import datetime, date, timedelta
from openai import OpenAI
import os
import re
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import string
import base64
import pandas as pd
import image_manager  # ADD THIS

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))

# ============================================================================
# SECTION 2: EMAIL CONFIGURATION
# ============================================================================
EMAIL_CONFIG = {
    "smtp_server": st.secrets.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(st.secrets.get("SMTP_PORT", 587)),
    "sender_email": st.secrets.get("SENDER_EMAIL", ""),
    "sender_password": st.secrets.get("SENDER_PASSWORD", ""),
    "use_tls": True
}

# ============================================================================
# SECTION 3: CSS STYLING
# ============================================================================
LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/01/logo.png"

st.markdown(f"""
<style>
    .main-header {{
        text-align: center;
        padding-top: 0.5rem;
        margin-top: -1rem;
        margin-bottom: 0.5rem;
    }}
    .logo-img {{
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        margin: 0 auto 0.25rem auto;
        display: block;
    }}
    .question-box {{
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4a5568;
        margin-bottom: 0.5rem;
        font-size: 1.3rem;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        line-height: 1.4;
    }}
    .progress-container {{
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        margin: 1rem 0;
    }}
    .html-link-btn {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        margin-top: 1rem;
        text-align: center;
        text-decoration: none;
        display: inline-block;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 4: SESSIONS DATA
# ============================================================================
SESSIONS = [
    {
        "id": 1,
        "title": "Childhood",
        "guidance": "Welcome to Session 1: Childhood. Focus on specific, sensory-rich memories.",
        "questions": [
            "What is your earliest memory?",
            "Can you describe your family home growing up?",
            "Who were the most influential people in your early years?",
            "What was school like for you?",
            "Were there any favourite games or hobbies?",
            "Is there a moment from childhood that shaped who you are?",
            "If you could give your younger self some advice, what would it be?"
        ],
        "completed": False,
        "word_target": 800
    },
    {
        "id": 2,
        "title": "Family & Relationships",
        "guidance": "Welcome to Session 2: Family & Relationships.",
        "questions": [
            "How would you describe your relationship with your parents?",
            "Are there any family traditions you remember fondly?",
            "What was your relationship like with siblings or close relatives?",
            "Can you share a story about a family celebration or challenge?",
            "How did your family shape your values?"
        ],
        "completed": False,
        "word_target": 700
    },
    {
        "id": 3,
        "title": "Education & Growing Up",
        "guidance": "Welcome to Session 3: Education & Growing Up.",
        "questions": [
            "What were your favourite subjects at school?",
            "Did you have any memorable teachers or mentors?",
            "How did you feel about exams and studying?",
            "Were there any big turning points in your education?",
            "Did you pursue further education or training?",
            "What advice would you give about learning?"
        ],
        "completed": False,
        "word_target": 600
    }
]

# ============================================================================
# SECTION 5: HISTORICAL EVENTS FUNCTIONS
# ============================================================================
def create_default_events_csv():
    """Create default historical events CSV"""
    default_events = [
        ["1920s","Women get the vote in UK","Political","UK","Women over 21 get the right to vote in 1928"],
        ["1940s","World War II","Military","Global","1939-1945 global conflict"],
        ["1940s","NHS founded","Healthcare","UK","National Health Service established in 1948"],
        ["1950s","Coronation of Elizabeth II","Royal","UK","Queen Elizabeth II crowned in 1953"],
        ["1960s","Man on the moon","Science","Global","Apollo 11 moon landing in 1969"],
        ["1970s","UK joins EEC","Political","UK","UK joins European Economic Community in 1973"],
        ["1980s","Falklands War","Military","UK","1982 war between UK and Argentina"],
        ["1990s","World Wide Web invented","Technology","Global","Tim Berners-Lee invents WWW in 1989"],
        ["2000s","Financial crisis","Economic","Global","2007-2008 global financial crisis"],
        ["2010s","Brexit referendum","Political","UK","2016 referendum to leave EU"],
        ["2020s","COVID-19 pandemic","Health","Global","Global pandemic begins 2020"]
    ]
    
    try:
        with open("historical_events.csv", "w", encoding="utf-8") as f:
            f.write("year_range,event,category,region,description\n")
            for event in default_events:
                f.write(",".join([f'"{item}"' for item in event]) + "\n")
        return True
    except:
        return False

def load_historical_events():
    """Load historical events from CSV"""
    try:
        csv_file = "historical_events.csv"
        
        if not os.path.exists(csv_file):
            create_default_events_csv()
        
        df = pd.read_csv(csv_file)
        events_by_decade = {}
        
        for _, row in df.iterrows():
            decade = str(row['year_range']).strip()
            event = str(row['event']).strip()
            description = str(row.get('description', '')).strip()
            
            if decade not in events_by_decade:
                events_by_decade[decade] = []
            
            events_by_decade[decade].append({
                'event': event,
                'description': description,
                'year_range': decade
            })
        
        return events_by_decade
        
    except Exception as e:
        print(f"Error loading historical events: {e}")
        return {}

def get_events_for_birth_year(birth_year):
    """Get historical events for a birth year"""
    try:
        events_by_decade = load_historical_events()
        current_year = datetime.now().year
        relevant_events = []
        
        start_decade_year = (birth_year // 10) * 10
        
        for decade_year in range(start_decade_year, current_year + 10, 10):
            decade_key = f"{decade_year}s"
            
            if decade_key in events_by_decade:
                for event in events_by_decade[decade_key]:
                    event_year = int(decade_key.replace('s', '')) + 5
                    age_at_event = event_year - birth_year
                    
                    if age_at_event >= 0:
                        event_with_age = event.copy()
                        event_with_age['approx_age'] = age_at_event
                        relevant_events.append(event_with_age)
        
        relevant_events.sort(key=lambda x: x['year_range'])
        return relevant_events[:15]
        
    except:
        return []

def format_historical_context(events, birth_year):
    """Format historical events for prompt"""
    if not events:
        return ""
    
    context_lines = []
    for event in events[:8]:
        event_text = f"- {event['event']} ({event['year_range']})"
        if 'approx_age' in event and event['approx_age'] >= 0:
            event_text += f" (Age {event['approx_age']})"
        context_lines.append(event_text)
    
    return f"""
HISTORICAL CONTEXT (Born {birth_year}):
During their lifetime:
{chr(10).join(context_lines)}
"""

# ============================================================================
# SECTION 6: AUTH FUNCTIONS (Simplified)
# ============================================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_account_data(user_id=None, email=None):
    """Get account data"""
    try:
        if user_id:
            filename = f"accounts/{user_id}_account.json"
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return json.load(f)
    except:
        pass
    return None

def authenticate_user(email, password):
    """Authenticate user"""
    try:
        account_data = get_account_data(email=email)
        if account_data:
            if hash_password(password) == account_data['password_hash']:
                return {
                    "success": True,
                    "user_id": account_data['user_id'],
                    "user_record": account_data
                }
        return {"success": False, "error": "Invalid email or password"}
    except:
        return {"success": False, "error": "Authentication error"}

def create_user_account(user_data, password):
    """Create new user account"""
    try:
        user_id = hashlib.sha256(f"{user_data['email']}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        user_record = {
            "user_id": user_id,
            "email": user_data["email"].lower().strip(),
            "password_hash": hash_password(password),
            "created_at": datetime.now().isoformat(),
            "profile": {
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "email": user_data["email"],
                "birthdate": user_data.get("birthdate", "")
            }
        }
        
        # Save account
        filename = f"accounts/{user_id}_account.json"
        os.makedirs("accounts", exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(user_record, f, indent=2)
        
        return {
            "success": True,
            "user_id": user_id,
            "user_record": user_record
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# SECTION 7: JSON STORAGE
# ============================================================================
def get_user_filename(user_id):
    filename_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
    return f"user_data_{filename_hash}.json"

def load_user_data(user_id):
    filename = get_user_filename(user_id)
    
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                if "responses" in data:
                    return data
        return {"responses": {}, "last_loaded": datetime.now().isoformat()}
    except:
        return {"responses": {}, "last_loaded": datetime.now().isoformat()}

def save_user_data(user_id, responses_data):
    filename = get_user_filename(user_id)
    
    try:
        data_to_save = {
            "user_id": user_id,
            "responses": responses_data,
            "last_saved": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        
        return True
    except:
        return False

# ============================================================================
# SECTION 8: SESSION STATE INIT
# ============================================================================
st.set_page_config(
    page_title="MemLife - Your Life Timeline",
    page_icon="📖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "user_account" not in st.session_state:
    st.session_state.user_account = None
if "current_session" not in st.session_state:
    st.session_state.current_session = 0
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "session_conversations" not in st.session_state:
    st.session_state.session_conversations = {}
if "ghostwriter_mode" not in st.session_state:
    st.session_state.ghostwriter_mode = True
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

# Initialize empty session structures
if not st.session_state.responses:
    for session in SESSIONS:
        session_id = session["id"]
        st.session_state.responses[session_id] = {
            "title": session["title"],
            "questions": {},
            "summary": "",
            "completed": False,
            "word_target": session.get("word_target", 500)
        }
        st.session_state.session_conversations[session_id] = {}

# Load user data if logged in
if st.session_state.logged_in and st.session_state.user_id and not st.session_state.data_loaded:
    user_data = load_user_data(st.session_state.user_id)
    
    if "responses" in user_data:
        for session_id_str, session_data in user_data["responses"].items():
            try:
                session_id = int(session_id_str)
                if session_id in st.session_state.responses and "questions" in session_data:
                    st.session_state.responses[session_id]["questions"] = session_data["questions"]
            except:
                continue
    
    st.session_state.data_loaded = True

# ============================================================================
# SECTION 9: CORE FUNCTIONS
# ============================================================================
def save_response(session_id, question, answer):
    """Save response"""
    user_id = st.session_state.user_id
    
    if not user_id or user_id == "":
        return False
    
    # Update session state
    if session_id not in st.session_state.responses:
        st.session_state.responses[session_id] = {
            "title": SESSIONS[session_id-1]["title"],
            "questions": {},
            "summary": "",
            "completed": False,
            "word_target": SESSIONS[session_id-1].get("word_target", 500)
        }
    
    st.session_state.responses[session_id]["questions"][question] = {
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save to JSON file
    return save_user_data(user_id, st.session_state.responses)

def calculate_author_word_count(session_id):
    total_words = 0
    session_data = st.session_state.responses.get(session_id, {})
    
    for question, answer_data in session_data.get("questions", {}).items():
        if answer_data.get("answer"):
            total_words += len(re.findall(r'\w+', answer_data["answer"]))
    
    return total_words

# ============================================================================
# SECTION 10: GHOSTWRITER PROMPT
# ============================================================================
def get_system_prompt():
    current_session = SESSIONS[st.session_state.current_session]
    
    # Get current question
    if st.session_state.get('current_question_override'):
        current_question = st.session_state.current_question_override
    else:
        current_question = current_session["questions"][st.session_state.current_question]
    
    # Get historical context
    historical_context = ""
    if st.session_state.user_account and st.session_state.user_account['profile'].get('birthdate'):
        try:
            birthdate = st.session_state.user_account['profile']['birthdate']
            birth_year = int(birthdate.split(', ')[-1])
            events = get_events_for_birth_year(birth_year)
            if events:
                historical_context = format_historical_context(events, birth_year)
        except:
            pass
    
    # Get image context
    image_context = ""
    if st.session_state.user_id:
        current_session_id = SESSIONS[st.session_state.current_session]["id"]
        images = image_manager.get_session_images(st.session_state.user_id, current_session_id)
        if images:
            image_context = "\n\n📸 **USER HAS UPLOADED PHOTOS:**\n"
            for img in images[:3]:
                image_context += f"- {img['original_filename']}"
                if img.get('description'):
                    image_context += f": {img['description']}"
                image_context += "\n"
            image_context += "\n**Reference these photos when relevant in your questions.**\n"
    
    if st.session_state.ghostwriter_mode:
        return f"""ROLE: You are a senior literary biographer.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT TOPIC: "{current_question}"
{historical_context}{image_context}

YOUR APPROACH:
1. Listen attentively
2. Focus on sensory details
3. Connect to historical context when relevant
4. Reference uploaded photos when appropriate
5. Find the deeper story

Tone: Professional and engaging.

IMPORTANT: Ask about photos when they relate to the topic."""
    else:
        return f"""You are a warm biographer helping document a life story.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT TOPIC: "{current_question}"
{historical_context}{image_context}

Please:
1. Listen actively
2. Ask ONE natural follow-up question
3. Reference photos or history when relevant
4. Keep conversation flowing

Tone: Kind and curious."""

# ============================================================================
# SECTION 11: LOGIN/SIGNUP
# ============================================================================
def show_login_signup():
    """Show login/signup interface"""
    st.markdown("""
    <div style="max-width: 500px; margin: 3rem auto; padding: 2.5rem; background: white; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
        <h1 style="text-align: center; color: #2c3e50;">MemLife</h1>
        <p style="text-align: center; color: #7f8c8d;">Your Life Timeline • Preserve Your Legacy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login", type="primary", use_container_width=True):
                if email and password:
                    result = authenticate_user(email, password)
                    if result["success"]:
                        st.session_state.user_id = result["user_id"]
                        st.session_state.user_account = result["user_record"]
                        st.session_state.logged_in = True
                        st.session_state.data_loaded = False
                        st.rerun()
                    else:
                        st.error("Login failed")
    
    with tab2:
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name*")
            with col2:
                last_name = st.text_input("Last Name*")
            
            email = st.text_input("Email Address*")
            password = st.text_input("Password*", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
            
            if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                if not all([first_name, last_name, email, password]):
                    st.error("All fields are required")
                elif password != confirm_password:
                    st.error("Passwords don't match")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters")
                else:
                    user_data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email
                    }
                    result = create_user_account(user_data, password)
                    if result["success"]:
                        st.session_state.user_id = result["user_id"]
                        st.session_state.user_account = result["user_record"]
                        st.session_state.logged_in = True
                        st.session_state.data_loaded = False
                        st.rerun()
                    else:
                        st.error("Error creating account")

# ============================================================================
# SECTION 12: MAIN APP FLOW
# ============================================================================
if not st.session_state.logged_in:
    show_login_signup()
    st.stop()

# ============================================================================
# SECTION 13: MAIN HEADER
# ============================================================================
st.markdown(f"""
<div class="main-header">
    <img src="{LOGO_URL}" class="logo-img" alt="MemLife Logo">
    <h2 style="margin: 0; line-height: 1.2;">MemLife - Your Life Timeline</h2>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 14: SIDEBAR
# ============================================================================
with st.sidebar:
    # User Profile
    st.header("👤 Your Profile")
    
    if st.session_state.user_account:
        profile = st.session_state.user_account['profile']
        st.success(f"✓ **{profile['first_name']} {profile['last_name']}**")
        st.caption(f"📧 {profile['email']}")
        
        if profile.get('birthdate'):
            st.caption(f"🎂 {profile['birthdate']}")
    
    # Logout
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = ""
        st.session_state.user_account = None
        st.rerun()
    
    st.divider()
    
    # Writing Streak
    st.subheader("🔥 Writing Streak")
    st.markdown("**5 day streak** ✨")
    
    # Stats
    st.divider()
    st.subheader("📊 Your Progress")
    
    total_responses = sum(len(session.get("questions", {})) for session in st.session_state.responses.values())
    total_words = sum(calculate_author_word_count(s["id"]) for s in SESSIONS)
    
    st.metric("Total Responses", total_responses)
    st.metric("Total Words", total_words)
    
    # Image Stats
    if st.session_state.user_id:
        total_images = image_manager.get_total_user_images(st.session_state.user_id)
        if total_images > 0:
            st.divider()
            st.subheader("🖼️ Your Photos")
            st.metric("Total Photos", total_images)
    
    # Interview Style
    st.divider()
    st.header("✍️ Interview Style")
    
    ghostwriter_mode = st.toggle(
        "Professional Ghostwriter Mode", 
        value=st.session_state.ghostwriter_mode,
        help="When enabled, the AI acts as a professional biographer."
    )
    
    if ghostwriter_mode != st.session_state.ghostwriter_mode:
        st.session_state.ghostwriter_mode = ghostwriter_mode
        st.rerun()
    
    # Session Navigation
    st.divider()
    st.header("📖 Sessions")
    
    for i, session in enumerate(SESSIONS):
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        responses_count = len(session_data.get("questions", {}))
        
        if i == st.session_state.current_session:
            status = "▶️"
        elif responses_count == len(session["questions"]):
            status = "✅"
        elif responses_count > 0:
            status = "🟡"
        else:
            status = "●"
        
        button_text = f"{status} Session {session_id}: {session['title']} ({responses_count}/{len(session['questions'])})"
        
        if st.button(button_text, key=f"select_session_{i}", use_container_width=True):
            st.session_state.current_session = i
            st.session_state.current_question = 0
            st.rerun()
    
    # Export Section
    st.divider()
    st.subheader("📤 Export")
    
    # Count stories and images
    total_stories = sum(len(session.get("questions", {})) for session in st.session_state.responses.values())
    total_images = 0
    if st.session_state.user_id:
        total_images = image_manager.get_total_user_images(st.session_state.user_id)
    
    if total_stories > 0:
        # Prepare export data
        export_data = {}
        for session in SESSIONS:
            session_id = session["id"]
            session_data = st.session_state.responses.get(session_id, {})
            
            if session_data.get("questions"):
                session_export = {
                    "title": session["title"],
                    "questions": session_data["questions"]
                }
                
                # Add images if available
                if st.session_state.user_id:
                    session_images = image_manager.get_session_images(st.session_state.user_id, session_id)
                    if session_images:
                        export_images = []
                        for img in session_images:
                            export_img = {
                                "id": img.get("id", ""),
                                "original_filename": img.get("original_filename", ""),
                                "description": img.get("description", ""),
                                "upload_date": img.get("upload_date", ""),
                                "dimensions": img.get("dimensions", ""),
                                "session_id": session_id,
                                "session_title": session["title"]
                            }
                            export_images.append(export_img)
                        
                        session_export["images"] = export_images
                
                export_data[str(session_id)] = session_export
        
        # Create JSON
        user_profile = {}
        if st.session_state.user_account:
            user_profile = st.session_state.user_account.get('profile', {})
        
        export_object = {
            "user": st.session_state.user_id,
            "user_name": f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip(),
            "user_profile": user_profile,
            "stories": export_data,
            "export_date": datetime.now().isoformat(),
            "stats": {
                "total_sessions": len(export_data),
                "total_stories": total_stories,
                "total_images": total_images
            }
        }
        
        json_data = json.dumps(export_object, indent=2, ensure_ascii=False)
        
        # Download button
        st.download_button(
            label=f"📥 Download JSON ({total_stories} stories, {total_images} photos)",
            data=json_data,
            file_name=f"LifeStory_{st.session_state.user_id}.json",
            mime="application/json",
            use_container_width=True
        )
        
        # Publisher link
        encoded_data = base64.b64encode(json_data.encode()).decode()
        publisher_url = f"https://your-publisher-app.streamlit.app/?data={encoded_data}"
        
        st.markdown(f'''
        <a href="{publisher_url}" target="_blank">
            <button class="html-link-btn">
                🖨️ Publish Biography
            </button>
        </a>
        ''', unsafe_allow_html=True)
    else:
        st.info("No stories to export yet")

# ============================================================================
# SECTION 15: MAIN CONTENT
# ============================================================================
current_session = SESSIONS[st.session_state.current_session]
current_session_id = current_session["id"]

# Get current question
current_question = current_session["questions"][st.session_state.current_question]

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(f"Session {current_session_id}: {current_session['title']}")
    
    # Show response count
    session_responses = len(st.session_state.responses[current_session_id].get("questions", {}))
    st.caption(f"📝 {session_responses}/{len(current_session['questions'])} topics answered")

with col2:
    st.markdown(f'<div style="margin-top: 1rem;">Topic {st.session_state.current_question + 1} of {len(current_session["questions"])}</div>', unsafe_allow_html=True)

# Question box
st.markdown(f"""
<div class="question-box">
    {current_question}
</div>
""", unsafe_allow_html=True)

# Session guidance
st.markdown(f"""
<div style="background-color: #e8f4f8; padding: 1rem; border-radius: 8px; border-left: 4px solid #3498db; margin-bottom: 1rem;">
    {current_session.get('guidance', '')}
</div>
""", unsafe_allow_html=True)

# Image Upload Section
st.divider()
st.subheader("📸 Add Photos to This Session")

# Upload interface
image_manager.image_upload_interface(st.session_state.user_id, current_session_id)

# Show existing images
images = image_manager.get_session_images(st.session_state.user_id, current_session_id)
if images:
    st.subheader(f"Your Photos ({len(images)})")
    
    cols = st.columns(3)
    for idx, img in enumerate(images):
        col_idx = idx % 3
        with cols[col_idx]:
            st.caption(f"📷 {img['original_filename']}")
            if img.get('description'):
                st.caption(f"💬 {img['description'][:30]}...")

# Conversation
st.divider()
st.subheader("💬 Conversation")

if current_session_id not in st.session_state.session_conversations:
    st.session_state.session_conversations[current_session_id] = {}

conversation = st.session_state.session_conversations[current_session_id].get(current_question, [])

if not conversation:
    # Check for saved response
    saved_response = st.session_state.responses[current_session_id]["questions"].get(current_question)
    
    if saved_response:
        conversation = [
            {"role": "assistant", "content": f"Let's explore: {current_question}"},
            {"role": "user", "content": saved_response["answer"]}
        ]
        st.session_state.session_conversations[current_session_id][current_question] = conversation
    else:
        with st.chat_message("assistant", avatar="👔"):
            st.markdown(f"**Let's explore this topic:**\n\n{current_question}")
            conversation.append({"role": "assistant", "content": f"Let's explore: {current_question}"})
            st.session_state.session_conversations[current_session_id][current_question] = conversation

# Display conversation
for message in conversation:
    if message["role"] == "assistant":
        with st.chat_message("assistant", avatar="👔"):
            st.markdown(message["content"])
    elif message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(message["content"])

# Chat input
user_input = st.chat_input("Type your answer here...")

if user_input:
    # Add user message
    conversation.append({"role": "user", "content": user_input})
    
    # Generate AI response
    with st.chat_message("assistant", avatar="👔"):
        with st.spinner("Thinking..."):
            try:
                messages_for_api = [
                    {"role": "system", "content": get_system_prompt()},
                    *conversation[:-1],
                    {"role": "user", "content": user_input}
                ]
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages_for_api,
                    temperature=0.7,
                    max_tokens=300
                )
                
                ai_response = response.choices[0].message.content
                st.markdown(ai_response)
                conversation.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                error_msg = "Thank you for sharing that. Your response has been saved."
                st.markdown(error_msg)
                conversation.append({"role": "assistant", "content": error_msg})
    
    # Save conversation and response
    st.session_state.session_conversations[current_session_id][current_question] = conversation
    save_response(current_session_id, current_question, user_input)
    
    st.rerun()

# Progress indicator
st.divider()
current_count = calculate_author_word_count(current_session_id)
target = st.session_state.responses[current_session_id].get("word_target", 500)
progress_percent = (current_count / target) * 100 if target > 0 else 100

st.markdown(f"""
<div class="progress-container">
    <div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; color: #2c3e50;">📊 Session Progress</div>
    <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">{progress_percent:.0f}% complete • {max(0, target - current_count)} words remaining</div>
    <div style="height: 10px; background-color: #e0e0e0; border-radius: 5px; overflow: hidden; margin: 1rem 0;">
        <div style="height: 100%; width: {min(progress_percent, 100)}%; background-color: #3498db; border-radius: 5px;"></div>
    </div>
    <div style="text-align: center; font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
        {current_count} / {target} words
    </div>
</div>
""", unsafe_allow_html=True)

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    total_words_all = sum(calculate_author_word_count(s["id"]) for s in SESSIONS)
    st.metric("Total Words", f"{total_words_all}")
with col2:
    completed_sessions = sum(1 for s in SESSIONS if len(st.session_state.responses[s["id"]].get("questions", {})) == len(s["questions"]))
    st.metric("Completed Sessions", f"{completed_sessions}/{len(SESSIONS)}")
with col3:
    total_topics = sum(len(st.session_state.responses[s["id"]].get("questions", {})) for s in SESSIONS)
    total_all_topics = sum(len(s["questions"]) for s in SESSIONS)
    st.metric("Topics Explored", f"{total_topics}/{total_all_topics}")
