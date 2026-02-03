# ============================================================================
# SECTION 1: IMPORTS AND INITIAL SETUP
# ============================================================================
import streamlit as st
import json
from datetime import datetime, date, timedelta
from openai import OpenAI
import os
import sqlite3
import re  # For word counting
import hashlib  # For creating user file names
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import string

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))

# ============================================================================
# SECTION 1A: EMAIL CONFIGURATION
# ============================================================================
EMAIL_CONFIG = {
    "smtp_server": st.secrets.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(st.secrets.get("SMTP_PORT", 587)),
    "sender_email": st.secrets.get("SENDER_EMAIL", ""),
    "sender_password": st.secrets.get("SENDER_PASSWORD", ""),
    "use_tls": True
}

# ============================================================================
# SECTION 2: CSS STYLING AND VISUAL DESIGN
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
    
    .chapter-guidance {{
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
        font-size: 0.95rem;
        line-height: 1.5;
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
    
    .question-counter {{
        font-size: 1.1rem;
        font-weight: bold;
        color: #2c3e50;
    }}
    
    .stChatMessage {{
        margin-bottom: 0.5rem !important;
    }}
    
    .user-message-container {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        width: 100%;
    }}
    
    .message-text {{
        flex: 1;
        min-width: 0;
    }}
    
    [data-testid="stAppViewContainer"] {{
        padding-top: 0.5rem !important;
    }}
    
    .ghostwriter-tag {{
        font-size: 0.8rem;
        color: #666;
        font-style: italic;
        margin-top: 0.5rem;
    }}
    
    .edit-target-box {{
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #dee2e6;
    }}
    
    .warning-box {{
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    
    .progress-container {{
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        margin: 1rem 0;
    }}
    
    .progress-header {{
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #2c3e50;
    }}
    
    .progress-status {{
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }}
    
    .progress-bar-container {{
        height: 10px;
        background-color: #e0e0e0;
        border-radius: 5px;
        overflow: hidden;
        margin: 1rem 0;
    }}
    
    .progress-bar-fill {{
        height: 100%;
        border-radius: 5px;
        transition: width 0.3s ease;
    }}
    
    .jot-box {{
        background-color: #fff8e1;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffb300;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }}
    
    .streak-flame {{
        font-size: 1.5rem;
        animation: pulse 2s infinite;
    }}
    
    @keyframes pulse {{
        0% {{ opacity: 0.8; }}
        50% {{ opacity: 1; }}
        100% {{ opacity: 0.8; }}
    }}
    
    .refresh-prompt-btn {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        cursor: pointer;
        transition: transform 0.2s;
    }}
    
    .refresh-prompt-btn:hover {{
        transform: scale(1.05);
    }}
    
    /* Account Setup Styles */
    .account-setup-container {{
        max-width: 600px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
    
    .account-setup-title {{
        text-align: center;
        color: #2c3e50;
        margin-bottom: 2rem;
        font-size: 2rem;
        font-weight: 300;
    }}
    
    .account-setup-subtitle {{
        text-align: center;
        color: #7f8c8d;
        margin-bottom: 2rem;
        font-size: 1.1rem;
        line-height: 1.6;
    }}
    
    .form-section {{
        margin-bottom: 2rem;
    }}
    
    .form-section-title {{
        font-size: 1.2rem;
        color: #3498db;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #f1f2f6;
    }}
    
    .form-group {{
        margin-bottom: 1.5rem;
    }}
    
    .form-label {{
        display: block;
        margin-bottom: 0.5rem;
        color: #2c3e50;
        font-weight: 500;
    }}
    
    .form-input {{
        width: 100%;
        padding: 0.75rem;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        font-size: 1rem;
        transition: border-color 0.3s;
    }}
    
    .form-input:focus {{
        border-color: #3498db;
        outline: none;
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
    }}
    
    .gender-options {{
        display: flex;
        gap: 1rem;
        margin-top: 0.5rem;
    }}
    
    .gender-option {{
        flex: 1;
        padding: 0.75rem;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }}
    
    .gender-option:hover {{
        background-color: #f8f9fa;
    }}
    
    .gender-option.selected {{
        border-color: #3498db;
        background-color: #e3f2fd;
        color: #3498db;
    }}
    
    .birthdate-group {{
        display: flex;
        gap: 1rem;
    }}
    
    .birthdate-select {{
        flex: 1;
        padding: 0.75rem;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        font-size: 1rem;
    }}
    
    .account-for-options {{
        display: flex;
        gap: 1rem;
        margin-top: 0.5rem;
    }}
    
    .account-for-option {{
        flex: 1;
        padding: 1rem;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .account-for-option:hover {{
        background-color: #f8f9fa;
    }}
    
    .account-for-option.selected {{
        border-color: #3498db;
        background-color: #e3f2fd;
        color: #3498db;
    }}
    
    .setup-button {{
        width: 100%;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: transform 0.3s, box-shadow 0.3s;
        margin-top: 1rem;
    }}
    
    .setup-button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }}
    
    .setup-button:disabled {{
        background: #bdc3c7;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }}
    
    .success-message {{
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
    }}
    
    .error-message {{
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }}
    
    /* Account Settings Styles */
    .settings-container {{
        max-width: 800px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
    
    .settings-section {{
        margin-bottom: 2.5rem;
    }}
    
    .settings-title {{
        color: #2c3e50;
        margin-bottom: 1.5rem;
        font-size: 1.8rem;
        font-weight: 600;
    }}
    
    .settings-card {{
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-left: 4px solid #3498db;
    }}
    
    .settings-card-title {{
        font-size: 1.2rem;
        color: #2c3e50;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .settings-info-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
    }}
    
    .info-item {{
        background: white;
        padding: 0.75rem;
        border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    
    .info-label {{
        font-size: 0.9rem;
        color: #7f8c8d;
        margin-bottom: 0.25rem;
    }}
    
    .info-value {{
        font-size: 1rem;
        color: #2c3e50;
        font-weight: 500;
    }}
    
    .account-actions {{
        display: flex;
        gap: 1rem;
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 1px solid #e0e0e0;
    }}
    
    .action-button {{
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s;
    }}
    
    .primary-button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }}
    
    .secondary-button {{
        background: #f1f2f6;
        color: #2c3e50;
    }}
    
    .danger-button {{
        background: #dc3545;
        color: white;
    }}
    
    .action-button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 3: SESSION DEFINITIONS AND DATA STRUCTURE
# ============================================================================
SESSIONS = [
    {
        "id": 1,
        "title": "Childhood",
        "guidance": "Welcome to Session 1: Childhood—this is where we lay the foundation of your story. Professional biographies thrive on specific, sensory-rich memories. I'm looking for the kind of details that transport readers: not just what happened, but how it felt, smelled, sounded. The 'insignificant' moments often reveal the most. Take your time—we're mining for gold here.",
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
        "guidance": "Welcome to Session 2: Family & Relationships—this is where we explore the people who shaped you. Family stories are complex ecosystems. We're not seeking perfect narratives, but authentic ones. The richest material often lives in the tensions, the unsaid things, the small rituals. My job is to help you articulate what usually goes unspoken. Think in scenes rather than summaries.",
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
        "guidance": "Welcome to Session 3: Education & Growing Up—this is where we explore how you learned to navigate the world. Education isn't just about schools—it's about how you learned to navigate the world. We're interested in the hidden curriculum: what you learned about yourself, about systems, about survival and growth. Think beyond grades to transformation.",
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
# FALLBACK PROMPTS FOR "NO BLANK PAGES" FEATURE
# ============================================================================
FALLBACK_PROMPTS = [
    "Describe a smell or sound that brings back a strong memory.",
    "What's a small moment that had a big impact?",
    "Tell me about a place that felt like home.",
    "Who believed in you when you didn't believe in yourself?",
    "What's something you learned the hard way?",
    "Describe a meal that holds special meaning.",
    "What was a turning point in how you see yourself?",
    "Tell me about a gift that meant more than its cost.",
    "What's a risk that paid off (or didn't)?",
    "Describe a time you felt truly proud."
]

# ============================================================================
# SECTION 4: NEW USER ACCOUNT MANAGEMENT FUNCTIONS
# ============================================================================
def generate_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def create_user_account(user_data):
    """Create a new user account and save to accounts database"""
    try:
        # Generate a unique user ID
        user_id = hashlib.sha256(f"{user_data['email']}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # Generate initial password
        password = generate_password()
        
        # Create user record
        user_record = {
            "user_id": user_id,
            "account_type": user_data.get("account_for", "self"),
            "created_at": datetime.now().isoformat(),
            "profile": {
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "email": user_data["email"],
                "gender": user_data.get("gender", ""),
                "birthdate": user_data.get("birthdate", ""),
                "timeline_start": user_data.get("birthdate", "")
            },
            "credentials": {
                "password": password,
                "last_login": None,
                "password_changed": False
            },
            "settings": {
                "email_notifications": True,
                "auto_save": True,
                "privacy_level": "private",
                "theme": "light"
            },
            "stats": {
                "total_sessions": 0,
                "total_words": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "account_age_days": 0
            }
        }
        
        # Save to accounts database
        save_account_data(user_record)
        
        return {
            "success": True,
            "user_id": user_id,
            "password": password,
            "user_record": user_record
        }
        
    except Exception as e:
        print(f"Error creating user account: {e}")
        return {"success": False, "error": str(e)}

def save_account_data(user_record):
    """Save account data to JSON file"""
    try:
        filename = f"accounts/{user_record['user_id']}_account.json"
        os.makedirs("accounts", exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(user_record, f, indent=2)
        
        # Also update accounts index
        update_accounts_index(user_record)
        
        return True
    except Exception as e:
        print(f"Error saving account data: {e}")
        return False

def update_accounts_index(user_record):
    """Update main accounts index file"""
    try:
        index_file = "accounts/accounts_index.json"
        os.makedirs("accounts", exist_ok=True)
        
        if os.path.exists(index_file):
            with open(index_file, 'r') as f:
                index = json.load(f)
        else:
            index = {}
        
        # Add or update user in index
        index[user_record['user_id']] = {
            "email": user_record['profile']['email'],
            "first_name": user_record['profile']['first_name'],
            "last_name": user_record['profile']['last_name'],
            "created_at": user_record['created_at'],
            "account_type": user_record['account_type']
        }
        
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error updating accounts index: {e}")
        return False

def get_account_data(user_id):
    """Get account data for a user"""
    try:
        filename = f"accounts/{user_id}_account.json"
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading account data: {e}")
    return None

def update_account_settings(user_id, settings):
    """Update user account settings"""
    try:
        account_data = get_account_data(user_id)
        if account_data:
            account_data['settings'].update(settings)
            save_account_data(account_data)
            return True
    except Exception as e:
        print(f"Error updating account settings: {e}")
    return False

def send_welcome_email(user_data, credentials):
    """Send welcome email with account details"""
    try:
        # Check if email is configured
        if not EMAIL_CONFIG['sender_email'] or not EMAIL_CONFIG['sender_password']:
            print("Email not configured - skipping email send")
            return False
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = user_data['email']
        msg['Subject'] = "Welcome to MemLife - Your Account Details"
        
        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Welcome to MemLife, {user_data['first_name']}!</h2>
                
                <p>Thank you for creating your account. We're excited to help you build your life timeline.</p>
                
                <div style="background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">Your Account Details:</h3>
                    <p><strong>Account ID:</strong> {credentials['user_id']}</p>
                    <p><strong>Email:</strong> {user_data['email']}</p>
                    <p><strong>Temporary Password:</strong> {credentials['password']}</p>
                </div>
                
                <div style="background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4 style="color: #2c3e50; margin-top: 0;">Getting Started:</h4>
                    <ol>
                        <li>Log in with your email and temporary password</li>
                        <li>Change your password in Account Settings</li>
                        <li>Start building your timeline from your birthdate: {user_data.get('birthdate', 'Not specified')}</li>
                        <li>Add memories, photos, and stories to your timeline</li>
                    </ol>
                </div>
                
                <p>Your MemLife timeline starts from your birthdate and grows with you as you add more memories and milestones.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://your-app-url.com/login" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Start Your MemLife Journey</a>
                </div>
                
                <p style="color: #7f8c8d; font-size: 0.9em; border-top: 1px solid #eee; padding-top: 20px;">
                    If you didn't create this account, please ignore this email or contact support.<br>
                    This is an automated message, please do not reply directly.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            if EMAIL_CONFIG['use_tls']:
                server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        print(f"Welcome email sent to {user_data['email']}")
        return True
        
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False

# ============================================================================
# SECTION 5: JSON-BASED STORAGE FUNCTIONS (RELIABLE ON STREAMLIT CLOUD)
# ============================================================================
def get_user_filename(user_id):
    """Create a safe filename for user data"""
    filename_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
    return f"user_data_{filename_hash}.json"

def load_user_data(user_id):
    """Load user data from JSON file"""
    filename = get_user_filename(user_id)
    
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                # Ensure we have the expected structure
                if "responses" in data:
                    return data
        return {"responses": {}, "last_loaded": datetime.now().isoformat()}
    except Exception as e:
        print(f"Error loading user data for {user_id}: {e}")
        return {"responses": {}, "last_loaded": datetime.now().isoformat()}

def save_user_data(user_id, responses_data):
    """Save user data to JSON file"""
    filename = get_user_filename(user_id)
    
    try:
        data_to_save = {
            "user_id": user_id,
            "responses": responses_data,
            "last_saved": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        
        print(f"DEBUG: Saved data for {user_id} to {filename}")
        return True
    except Exception as e:
        print(f"Error saving user data for {user_id}: {e}")
        return False

# ============================================================================
# SECTION 6: NEW FUNCTIONS FOR ADDED FEATURES
# ============================================================================
def update_streak():
    """Update user's writing streak"""
    if "streak_days" not in st.session_state:
        st.session_state.streak_days = 1
    if "last_active" not in st.session_state:
        st.session_state.last_active = date.today().isoformat()
    if "total_writing_days" not in st.session_state:
        st.session_state.total_writing_days = 1
    
    today = date.today().isoformat()
    
    if st.session_state.last_active != today:
        try:
            last_date = date.fromisoformat(st.session_state.last_active)
            today_date = date.today()
            days_diff = (today_date - last_date).days
            
            if days_diff == 1:
                # Consecutive day
                st.session_state.streak_days += 1
            elif days_diff > 1:
                # Broken streak
                st.session_state.streak_days = 1
            
            st.session_state.total_writing_days += 1
            st.session_state.last_active = today
        except:
            st.session_state.last_active = today

def get_streak_emoji(streak_days):
    """Get flame emoji based on streak length"""
    if streak_days >= 30:
        return "🔥🔥🔥"
    elif streak_days >= 7:
        return "🔥🔥"
    elif streak_days >= 3:
        return "🔥"
    else:
        return "✨"

def estimate_year_from_text(text):
    """Simple year extraction from text"""
    try:
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
        if years:
            return int(years[0])
    except:
        pass
    return None

def save_jot(text, estimated_year=None):
    """Save a quick jot to session state"""
    if "quick_jots" not in st.session_state:
        st.session_state.quick_jots = []
    
    jot_data = {
        "text": text,
        "year": estimated_year,
        "date": datetime.now().isoformat(),
        "word_count": len(re.findall(r'\w+', text))
    }
    
    st.session_state.quick_jots.append(jot_data)
    return True

# ============================================================================
# SECTION 7: SESSION STATE INITIALIZATION WITH PERSISTENCE
# ============================================================================

# Set page config first
st.set_page_config(
    page_title="MemLife - Your Life Timeline",
    page_icon="📖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize ALL session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "user_account" not in st.session_state:
    st.session_state.user_account = None
if "show_account_setup" not in st.session_state:
    st.session_state.show_account_setup = False
if "show_account_settings" not in st.session_state:
    st.session_state.show_account_settings = False
if "current_session" not in st.session_state:
    st.session_state.current_session = 0
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "session_conversations" not in st.session_state:
    st.session_state.session_conversations = {}
if "editing" not in st.session_state:
    st.session_state.editing = None
if "edit_text" not in st.session_state:
    st.session_state.edit_text = ""
if "ghostwriter_mode" not in st.session_state:
    st.session_state.ghostwriter_mode = True
if "spellcheck_enabled" not in st.session_state:
    st.session_state.spellcheck_enabled = True
if "editing_word_target" not in st.session_state:
    st.session_state.editing_word_target = False
if "confirming_clear" not in st.session_state:
    st.session_state.confirming_clear = None
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "prompt_index" not in st.session_state:
    st.session_state.prompt_index = 0
if "current_question_override" not in st.session_state:
    st.session_state.current_question_override = None
if "quick_jots" not in st.session_state:
    st.session_state.quick_jots = []
if "current_jot" not in st.session_state:
    st.session_state.current_jot = ""
if "show_jots" not in st.session_state:
    st.session_state.show_jots = False

# Initialize streak system
if "streak_days" not in st.session_state:
    st.session_state.streak_days = 1
if "last_active" not in st.session_state:
    st.session_state.last_active = date.today().isoformat()
if "total_writing_days" not in st.session_state:
    st.session_state.total_writing_days = 1

# Check URL for user parameter - THIS IS THE KEY TO PERSISTENCE
if 'user' in st.query_params:
    url_user = st.query_params['user']
    if url_user != st.session_state.user_id:
        st.session_state.user_id = url_user
        st.session_state.data_loaded = False  # Force reload when user changes

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

# Load user data if we have a user and data hasn't been loaded yet
if st.session_state.user_id and st.session_state.user_id != "" and not st.session_state.data_loaded:
    print(f"DEBUG: Loading data for user {st.session_state.user_id}")
    
    # Try to load account data first
    account_data = get_account_data(st.session_state.user_id)
    if account_data:
        st.session_state.user_account = account_data
    
    # Load biography data
    user_data = load_user_data(st.session_state.user_id)
    
    if "responses" in user_data:
        for session_id_str, session_data in user_data["responses"].items():
            try:
                session_id = int(session_id_str)
                if session_id in st.session_state.responses:
                    # Only load if we have questions
                    if "questions" in session_data:
                        st.session_state.responses[session_id]["questions"] = session_data["questions"]
            except ValueError:
                continue
    
    st.session_state.data_loaded = True
    print(f"DEBUG: Data loaded for {st.session_state.user_id}")

# ============================================================================
# SECTION 8: CORE APPLICATION FUNCTIONS
# ============================================================================
def save_response(session_id, question, answer):
    """Save response to both session state AND JSON file"""
    user_id = st.session_state.user_id
    
    # CRITICAL: Don't save if no user
    if not user_id or user_id == "":
        print("DEBUG: No user_id, cannot save")
        return False
    
    print(f"DEBUG: Saving for user {user_id}, session {session_id}, question: {question[:50]}...")
    
    # Update streak when user saves
    update_streak()
    
    # Update account stats
    if st.session_state.user_account:
        word_count = len(re.findall(r'\w+', answer))
        if "stats" not in st.session_state.user_account:
            st.session_state.user_account["stats"] = {}
        
        st.session_state.user_account["stats"]["total_words"] = st.session_state.user_account["stats"].get("total_words", 0) + word_count
        st.session_state.user_account["stats"]["total_sessions"] = len(st.session_state.responses[session_id].get("questions", {}))
        save_account_data(st.session_state.user_account)
    
    # 1. Save to session state
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
    
    # 2. Save to JSON file
    if save_user_data(user_id, st.session_state.responses):
        print(f"DEBUG: Successfully saved to JSON file for {user_id}")
        return True
    else:
        print(f"DEBUG: Failed to save to JSON file for {user_id}")
        return False

def calculate_author_word_count(session_id):
    total_words = 0
    session_data = st.session_state.responses.get(session_id, {})
    
    for question, answer_data in session_data.get("questions", {}).items():
        if answer_data.get("answer"):
            total_words += len(re.findall(r'\w+', answer_data["answer"]))
    
    return total_words

def get_progress_info(session_id):
    current_count = calculate_author_word_count(session_id)
    target = st.session_state.responses[session_id].get("word_target", 500)
    
    if target == 0:
        progress_percent = 100
        emoji = "🟢"
        color = "#2ecc71"
    else:
        progress_percent = (current_count / target) * 100 if target > 0 else 100
        
        if progress_percent >= 100:
            emoji = "🟢"
            color = "#2ecc71"
        elif progress_percent >= 70:
            emoji = "🟡"
            color = "#f39c12"
        else:
            emoji = "🔴"
            color = "#e74c3c"
    
    remaining_words = max(0, target - current_count)
    status_text = f"{remaining_words} words remaining" if remaining_words > 0 else "Target achieved!"
    
    return {
        "current_count": current_count,
        "target": target,
        "progress_percent": progress_percent,
        "emoji": emoji,
        "color": color,
        "remaining_words": remaining_words,
        "status_text": status_text
    }

# ============================================================================
# SECTION 9: AUTO-CORRECT FUNCTION
# ============================================================================
def auto_correct_text(text):
    """Auto-correct text using OpenAI"""
    if not text or not st.session_state.spellcheck_enabled:
        return text
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Fix spelling and grammar mistakes in the following text. Return only the corrected text."},
                {"role": "user", "content": text}
            ],
            max_tokens=len(text) + 100,
            temperature=0.1
        )
        return response.choices[0].message.content
    except:
        return text

# ============================================================================
# SECTION 10: GHOSTWRITER PROMPT FUNCTION
# ============================================================================
def get_system_prompt():
    current_session = SESSIONS[st.session_state.current_session]
    
    # Use override prompt if set
    if st.session_state.current_question_override:
        current_question = st.session_state.current_question_override
    else:
        current_question = current_session["questions"][st.session_state.current_question]
    
    if st.session_state.ghostwriter_mode:
        return f"""ROLE: You are a senior literary biographer with multiple award-winning books to your name.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT TOPIC: "{current_question}"

YOUR APPROACH:
1. Listen like an archivist
2. Think in scenes, sensory details, and emotional truth
3. Find the story that needs to be told
4. Respect silence and complexity

Tone: Literary but not pretentious. Serious but not solemn."""
    else:
        return f"""You are a warm, professional biographer helping document a life story.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT TOPIC: "{current_question}"

Please:
1. Listen actively
2. Acknowledge warmly
3. Ask ONE natural follow-up question
4. Keep conversation flowing

Tone: Kind, curious, professional"""

# ============================================================================
# SECTION 11: ACCOUNT SETUP COMPONENT
# ============================================================================
def show_account_setup():
    """Display the account setup form"""
    st.markdown("""
    <div class="account-setup-container">
        <h1 class="account-setup-title">MemLife</h1>
        <p class="account-setup-subtitle">
            Just a few things to get started<br>
            Please fill out the information below.<br>
            MemLife will set up an account and timeline of your life starting from your birthdate.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("account_setup_form", clear_on_submit=False):
        # Personal Information Section
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="form-section-title">Personal Information</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name*", key="setup_first_name")
        with col2:
            last_name = st.text_input("Last Name*", key="setup_last_name")
        
        email = st.text_input("Email Address*", key="setup_email")
        
        # Gender selection
        st.markdown('<div class="form-group">', unsafe_allow_html=True)
        st.markdown('<div class="form-label">Gender</div>', unsafe_allow_html=True)
        
        gender_col1, gender_col2, gender_col3 = st.columns(3)
        with gender_col1:
            male_selected = st.button("👨 Male", key="gender_male", use_container_width=True)
        with gender_col2:
            female_selected = st.button("👩 Female", key="gender_female", use_container_width=True)
        with gender_col3:
            other_selected = st.button("⚧ Other", key="gender_other", use_container_width=True)
        
        if 'selected_gender' not in st.session_state:
            st.session_state.selected_gender = ""
        
        if male_selected:
            st.session_state.selected_gender = "Male"
        if female_selected:
            st.session_state.selected_gender = "Female"
        if other_selected:
            st.session_state.selected_gender = "Other"
        
        gender = st.session_state.selected_gender
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close form-section
        
        # Birthdate Section
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="form-section-title">Birthdate</h3>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            months = ["Month", "January", "February", "March", "April", "May", "June", 
                     "July", "August", "September", "October", "November", "December"]
            birth_month = st.selectbox("Month*", months, key="setup_month")
        with col2:
            days = ["Day"] + list(range(1, 32))
            birth_day = st.selectbox("Day*", days, key="setup_day")
        with col3:
            current_year = datetime.now().year
            years = ["Year"] + list(range(current_year, current_year - 120, -1))
            birth_year = st.selectbox("Year*", years, key="setup_year")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Account Type Section
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="form-section-title">Account Type</h3>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="margin-bottom: 1rem;">
            Do you want to create this for yourself, or someone else?<br>
            <small>You can add more accounts at any time.</small>
        </div>
        """, unsafe_allow_html=True)
        
        account_col1, account_col2 = st.columns(2)
        with account_col1:
            self_account = st.button("👤 For Me", key="account_self", use_container_width=True)
        with account_col2:
            other_account = st.button("👥 For Someone Else", key="account_other", use_container_width=True)
        
        if 'account_for' not in st.session_state:
            st.session_state.account_for = "self"
        
        if self_account:
            st.session_state.account_for = "self"
        if other_account:
            st.session_state.account_for = "other"
        
        account_for = st.session_state.account_for
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Terms and Conditions
        st.markdown("""
        <div style="margin: 2rem 0; padding: 1rem; background-color: #f8f9fa; border-radius: 8px;">
            <p style="font-size: 0.9rem; color: #666; margin: 0;">
                By creating an account, you agree to our <a href="#" style="color: #3498db;">Terms of Service</a> and <a href="#" style="color: #3498db;">Privacy Policy</a>.
                Your data will be stored securely and you can export it at any time.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Submit button
        submit_button = st.form_submit_button("Create My MemLife Account", type="primary", use_container_width=True)
        
        if submit_button:
            # Validate form
            errors = []
            
            if not first_name:
                errors.append("First name is required")
            if not last_name:
                errors.append("Last name is required")
            if not email or "@" not in email:
                errors.append("Valid email is required")
            if birth_month == "Month" or birth_day == "Day" or birth_year == "Year":
                errors.append("Complete birthdate is required")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Create birthdate string
                birthdate = f"{birth_month} {birth_day}, {birth_year}"
                
                # Prepare user data
                user_data = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "gender": gender,
                    "birthdate": birthdate,
                    "account_for": account_for
                }
                
                # Create account
                with st.spinner("Creating your account and setting up your timeline..."):
                    result = create_user_account(user_data)
                    
                    if result["success"]:
                        # Send welcome email
                        email_sent = send_welcome_email(user_data, {
                            "user_id": result["user_id"],
                            "password": result["password"]
                        })
                        
                        # Set user session
                        st.session_state.user_id = result["user_id"]
                        st.session_state.user_account = result["user_record"]
                        st.session_state.show_account_setup = False
                        
                        # Show success message
                        st.success("✅ Account created successfully!")
                        
                        if email_sent:
                            st.info(f"📧 Welcome email sent to {email}")
                        
                        # Show account details
                        with st.expander("Your Account Details", expanded=True):
                            st.write(f"**Account ID:** `{result['user_id']}`")
                            st.write(f"**Temporary Password:** `{result['password']}`")
                            st.write("**Please save these credentials!**")
                            st.write("You can change your password in Account Settings.")
                        
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Error creating account: {result.get('error', 'Unknown error')}")

# ============================================================================
# SECTION 12: ACCOUNT SETTINGS COMPONENT
# ============================================================================
def show_account_settings():
    """Display account settings page"""
    if not st.session_state.user_account:
        st.error("No account found. Please create an account first.")
        return
    
    account = st.session_state.user_account
    
    st.markdown("""
    <div class="settings-container">
        <h1 class="settings-title">🔧 Account Settings</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Profile Information
    with st.container():
        st.markdown('<div class="settings-section">', unsafe_allow_html=True)
        st.subheader("👤 Profile Information")
        
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("View Profile", expanded=True):
                st.markdown(f"""
                **Full Name:** {account['profile']['first_name']} {account['profile']['last_name']}
                
                **Email:** {account['profile']['email']}
                
                **Gender:** {account['profile'].get('gender', 'Not specified')}
                
                **Birthdate:** {account['profile'].get('birthdate', 'Not specified')}
                
                **Timeline Start:** {account['profile'].get('timeline_start', 'Birthdate')}
                
                **Account Type:** {account['account_type'].title()}
                
                **Member Since:** {datetime.fromisoformat(account['created_at']).strftime('%B %d, %Y')}
                """)
        
        with col2:
            with st.expander("Edit Profile", expanded=False):
                # Profile edit form
                new_first = st.text_input("First Name", value=account['profile']['first_name'])
                new_last = st.text_input("Last Name", value=account['profile']['last_name'])
                new_email = st.text_input("Email", value=account['profile']['email'])
                new_gender = st.selectbox("Gender", ["", "Male", "Female", "Other", "Prefer not to say"], 
                                        index=["", "Male", "Female", "Other", "Prefer not to say"].index(account['profile'].get('gender', "")) if account['profile'].get('gender') in ["", "Male", "Female", "Other", "Prefer not to say"] else 0)
                
                if st.button("Update Profile", type="primary"):
                    # Update profile
                    account['profile']['first_name'] = new_first
                    account['profile']['last_name'] = new_last
                    account['profile']['email'] = new_email
                    account['profile']['gender'] = new_gender
                    
                    if save_account_data(account):
                        st.session_state.user_account = account
                        st.success("Profile updated successfully!")
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Account Settings
    with st.container():
        st.markdown('<div class="settings-section">', unsafe_allow_html=True)
        st.subheader("⚙️ Account Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("Notification Settings", expanded=True):
                email_notifications = st.toggle(
                    "Email Notifications",
                    value=account['settings'].get('email_notifications', True),
                    help="Receive email updates about your timeline"
                )
                
                auto_save = st.toggle(
                    "Auto-Save",
                    value=account['settings'].get('auto_save', True),
                    help="Automatically save your work as you type"
                )
                
                if st.button("Save Preferences", type="primary"):
                    account['settings']['email_notifications'] = email_notifications
                    account['settings']['auto_save'] = auto_save
                    
                    if save_account_data(account):
                        st.session_state.user_account = account
                        st.success("Preferences saved!")
                        st.rerun()
        
        with col2:
            with st.expander("Privacy & Security", expanded=True):
                privacy_level = st.selectbox(
                    "Privacy Level",
                    ["Private", "Friends Only", "Public"],
                    index=["Private", "Friends Only", "Public"].index(account['settings'].get('privacy_level', "Private"))
                )
                
                theme = st.selectbox(
                    "Theme",
                    ["Light", "Dark", "Auto"],
                    index=["Light", "Dark", "Auto"].index(account['settings'].get('theme', "Light"))
                )
                
                # Password change
                st.divider()
                st.write("**Change Password**")
                current_pass = st.text_input("Current Password", type="password")
                new_pass = st.text_input("New Password", type="password")
                confirm_pass = st.text_input("Confirm New Password", type="password")
                
                if st.button("Change Password", type="primary"):
                    if new_pass == confirm_pass and len(new_pass) >= 8:
                        # In a real app, verify current password first
                        account['credentials']['password'] = new_pass
                        account['credentials']['password_changed'] = True
                        
                        if save_account_data(account):
                            st.session_state.user_account = account
                            st.success("Password changed successfully!")
                    elif len(new_pass) < 8:
                        st.error("Password must be at least 8 characters")
                    else:
                        st.error("New passwords don't match")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Account Statistics
    with st.container():
        st.markdown('<div class="settings-section">', unsafe_allow_html=True)
        st.subheader("📊 Account Statistics")
        
        stats = account.get('stats', {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Stories", stats.get('total_sessions', 0))
        with col2:
            st.metric("Total Words", stats.get('total_words', 0))
        with col3:
            st.metric("Current Streak", stats.get('current_streak', 0))
        with col4:
            st.metric("Account Age", f"{stats.get('account_age_days', 0)} days")
        
        # Timeline progress
        st.divider()
        st.write("**Your Timeline Progress**")
        
        # Calculate timeline progress based on age
        if account['profile'].get('birthdate'):
            try:
                birth_year = int(account['profile']['birthdate'].split(', ')[-1])
                current_year = datetime.now().year
                age = current_year - birth_year
                
                if age > 0:
                    # Simplified progress - in real app, would be based on actual entries
                    timeline_progress = min(100, (stats.get('total_sessions', 0) / (age * 12)) * 100)  # Rough estimate
                    
                    st.progress(timeline_progress / 100)
                    st.caption(f"Your timeline covers approximately {timeline_progress:.1f}% of your life so far")
            except:
                pass
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Account Actions
    with st.container():
        st.markdown('<div class="settings-section">', unsafe_allow_html=True)
        st.subheader("⚠️ Account Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Export All Data", use_container_width=True):
                # Prepare data for export
                export_data = {
                    "account_info": account,
                    "biography_data": st.session_state.responses,
                    "export_date": datetime.now().isoformat()
                }
                
                json_data = json.dumps(export_data, indent=2)
                
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"MemLife_Export_{st.session_state.user_id}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col2:
            if st.button("🔄 Reset Timeline", use_container_width=True):
                st.warning("This will clear all your timeline entries. Are you sure?")
                if st.button("Confirm Reset", type="primary", key="confirm_reset"):
                    # Clear all responses
                    for session_id in st.session_state.responses:
                        st.session_state.responses[session_id]["questions"] = {}
                    
                    # Save empty data
                    save_user_data(st.session_state.user_id, st.session_state.responses)
                    st.success("Timeline reset successfully!")
                    st.rerun()
        
        with col3:
            if st.button("🗑️ Delete Account", type="secondary", use_container_width=True):
                st.error("⚠️ **Permanent Account Deletion**")
                st.write("This action cannot be undone. All your data will be permanently deleted.")
                
                confirm_text = st.text_input("Type 'DELETE' to confirm:")
                if st.button("Permanently Delete Account", type="primary", disabled=confirm_text != "DELETE"):
                    # In a real app, this would delete the account from database
                    st.error("Account deletion would be performed here")
                    # For safety, we're not implementing actual deletion in this demo
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back to Biography", use_container_width=True):
        st.session_state.show_account_settings = False
        st.rerun()

# ============================================================================
# SECTION 13: MAIN APP HEADER
# ============================================================================
st.markdown(f"""
<div class="main-header">
    <img src="{LOGO_URL}" class="logo-img" alt="MemLife Logo">
    <h2 style="margin: 0; line-height: 1.2;">MemLife - Your Life Timeline</h2>
    <p style="font-size: 0.9rem; color: #666; margin: 0; line-height: 1.2;">Preserve Your Legacy • Build Your Timeline • Share Your Story</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 14: MAIN APP FLOW CONTROL
# ============================================================================

# Show account setup if requested
if st.session_state.show_account_setup:
    show_account_setup()
    st.stop()

# Show account settings if requested
if st.session_state.show_account_settings:
    show_account_settings()
    st.stop()

# Show user setup if no user ID
if not st.session_state.user_id or st.session_state.user_id == "":
    st.title("👋 Welcome to MemLife")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## Your Life, Your Timeline
        
        MemLife helps you create a beautiful, detailed timeline of your life story
        starting from your birthdate. Every memory, every milestone, preserved forever.
        
        **✨ Features:**
        - 📅 Timeline starting from your birth
        - 📖 Guided biography sessions
        - 📸 Add photos and memories
        - 🔗 Share with family and friends
        - 🔒 Secure, private storage
        - 📤 Export anytime
        
        **Ready to start your life timeline?**
        """)
        
        if st.button("🚀 Create Your MemLife Account", type="primary", use_container_width=True):
            st.session_state.show_account_setup = True
            st.rerun()
        
        st.divider()
        
        # Existing user login
        with st.form("existing_user_form"):
            st.write("**Already have an account?**")
            existing_user = st.text_input("Enter your Account ID:", key="existing_user_id")
            login_submit = st.form_submit_button("Continue My Timeline", type="secondary")
            
            if login_submit and existing_user:
                # Check if account exists
                account_data = get_account_data(existing_user)
                if account_data:
                    st.session_state.user_id = existing_user
                    st.session_state.user_account = account_data
                    st.session_state.data_loaded = False
                    st.rerun()
                else:
                    st.error("Account not found. Please check your Account ID or create a new account.")
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; color: white; height: 100%;">
            <h3 style="color: white; margin-top: 0;">📖 Your Life Story</h3>
            <p>Every life is a unique story waiting to be told. MemLife helps you:</p>
            <ul style="color: white; padding-left: 1.2rem;">
                <li>Document memories</li>
                <li>Preserve family history</li>
                <li>Create legacy stories</li>
                <li>Share across generations</li>
            </ul>
            <p><small>Start free • No credit card required</small></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Don't show the rest of the app
    st.stop()

# ============================================================================
# SECTION 15: SIDEBAR - USER PROFILE AND SETTINGS
# ============================================================================
with st.sidebar:
    # User Profile Header with Account Info
    st.header("👤 Your Profile")
    
    # Show current user with account info
    if st.session_state.user_account:
        profile = st.session_state.user_account['profile']
        st.success(f"✓ **{profile['first_name']} {profile['last_name']}**")
        st.caption(f"📧 {profile['email']}")
        
        # Show birthdate and timeline info
        if profile.get('birthdate'):
            st.caption(f"🎂 Born: {profile['birthdate']}")
        
        # Account type
        account_type = st.session_state.user_account['account_type']
        st.caption(f"👤 Account: {account_type.title()}")
        
        # Account Settings Button
        if st.button("⚙️ Account Settings", use_container_width=True):
            st.session_state.show_account_settings = True
            st.rerun()
        
        # Add Another Account Button
        if st.button("👥 Add Another Account", use_container_width=True):
            st.session_state.show_account_setup = True
            st.rerun()
    
    else:
        st.info(f"✍️ Writing as: {st.session_state.user_id}")
    
    st.divider()
    
    # ============================================================================
    # NEW: STREAK SYSTEM DISPLAY
    # ============================================================================
    st.subheader("🔥 Writing Streak")
    
    streak_emoji = get_streak_emoji(st.session_state.streak_days)
    st.markdown(f"<div class='streak-flame'>{streak_emoji}</div>", unsafe_allow_html=True)
    st.markdown(f"**{st.session_state.streak_days} day streak**")
    st.caption(f"Total writing days: {st.session_state.total_writing_days}")
    
    # Show milestone badges
    if st.session_state.streak_days >= 7:
        st.success("🏆 Weekly Writer!")
    if st.session_state.streak_days >= 30:
        st.success("🌟 Monthly Master!")
    
    # Timeline Progress (if we have birthdate)
    if st.session_state.user_account and st.session_state.user_account['profile'].get('birthdate'):
        try:
            birth_year = int(st.session_state.user_account['profile']['birthdate'].split(', ')[-1])
            current_year = datetime.now().year
            age = current_year - birth_year
            
            if age > 0:
                # Calculate timeline coverage (simplified)
                total_possible_entries = age * 12  # Rough estimate: 12 entries per year
                actual_entries = sum(len(session.get("questions", {})) for session in st.session_state.responses.values())
                coverage = min(100, (actual_entries / total_possible_entries) * 500)  # Scale for visibility
                
                st.divider()
                st.subheader("📅 Timeline Coverage")
                st.progress(coverage / 100)
                st.caption(f"{actual_entries} memories across {age} years")
        except:
            pass
    
    # Stats
    st.divider()
    st.subheader("📊 Your Progress")
    total_responses = sum(len(session.get("questions", {})) for session in st.session_state.responses.values())
    total_words = sum(calculate_author_word_count(s["id"]) for s in SESSIONS)
    
    st.metric("Total Responses", total_responses)
    st.metric("Total Words", total_words)
    
    # ============================================================================
    # NEW: JOT NOW FEATURE (FIXED VERSION)
    # ============================================================================
    st.divider()
    st.subheader("⚡ Quick Capture")
    
    with st.expander("💭 **Jot Now - Quick Memory**", expanded=False):
        # Use a text area with a unique key
        quick_note = st.text_area(
            "Got a memory? Jot it down:",
            value="",
            height=120,
            placeholder="E.g., 'That summer at grandma's house in 1995...' or 'My first day at IBM in 2003'",
            key="jot_text_area",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Jot", key="save_jot_btn", use_container_width=True):
                if quick_note and quick_note.strip():
                    estimated_year = estimate_year_from_text(quick_note)
                    save_jot(quick_note, estimated_year)
                    
                    st.success("Saved! ✨")
                    # The text area will clear on rerun
                    st.rerun()
                else:
                    st.warning("Please write something first!")
        
        with col2:
            use_disabled = not quick_note or not quick_note.strip()
            if st.button("📝 Use as Prompt", key="use_jot_btn", use_container_width=True, disabled=use_disabled):
                # Use this text as a new prompt
                st.session_state.current_question_override = quick_note
                st.session_state.prompt_index = (st.session_state.prompt_index + 1) % len(FALLBACK_PROMPTS)
                st.info("Ready to write about this!")
                st.rerun()
    
    # Show saved jots if any
    if st.session_state.get('quick_jots'):
        st.caption(f"📝 {len(st.session_state.quick_jots)} quick notes saved")
        if st.button("View Quick Notes", key="view_jots_btn"):
            st.session_state.show_jots = True
            st.rerun()
    
    # Option to switch account
    st.divider()
    if st.button("🔄 Switch Account", key="switch_account_btn", use_container_width=True):
        st.session_state.user_id = ""
        st.session_state.user_account = None
        st.query_params.clear()
        st.session_state.data_loaded = False
        st.rerun()
    
    # ============================================================================
    # REST OF THE SIDEBAR (Original content from your script)
    # ============================================================================
    st.divider()
    st.header("✍️ Interview Style")
    
    ghostwriter_mode = st.toggle(
        "Professional Ghostwriter Mode", 
        value=st.session_state.ghostwriter_mode,
        help="When enabled, the AI acts as a professional biographer using advanced interviewing techniques.",
        key="ghostwriter_toggle"
    )
    
    if ghostwriter_mode != st.session_state.ghostwriter_mode:
        st.session_state.ghostwriter_mode = ghostwriter_mode
        st.rerun()
    
    spellcheck_enabled = st.toggle(
        "Auto Spelling Correction",
        value=st.session_state.spellcheck_enabled,
        help="Automatically correct spelling and grammar as you type",
        key="spellcheck_toggle"
    )
    
    if spellcheck_enabled != st.session_state.spellcheck_enabled:
        st.session_state.spellcheck_enabled = spellcheck_enabled
        st.rerun()
    
    if st.session_state.ghostwriter_mode:
        st.success("✓ Professional mode active")
    else:
        st.info("Standard mode active")
    
    # ============================================================================
    # SECTION 12A: SIDEBAR - SESSION NAVIGATION
    # ============================================================================
    st.divider()
    st.header("📖 Sessions")
    
    for i, session in enumerate(SESSIONS):
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        
        # Calculate responses in this session
        responses_count = len(session_data.get("questions", {}))
        total_questions = len(session["questions"])
        
        # Determine session status
        if i == st.session_state.current_session:
            status = "▶️"
        elif responses_count == total_questions:
            status = "✅"
        elif responses_count > 0:
            status = "🟡"
        else:
            status = "●"
        
        button_text = f"{status} Session {session_id}: {session['title']} ({responses_count}/{total_questions})"
        
        if st.button(button_text, 
                    key=f"select_session_{i}",
                    use_container_width=True):
            st.session_state.current_session = i
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.session_state.current_question_override = None
            st.rerun()
    
    # ============================================================================
    # SECTION 12B: SIDEBAR - NAVIGATION CONTROLS
    # ============================================================================
    st.divider()
    st.subheader("Topic Navigation")
    
    current_session = SESSIONS[st.session_state.current_session]
    st.markdown(f'<div class="question-counter">Topic {st.session_state.current_question + 1} of {len(current_session["questions"])}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous Topic", disabled=st.session_state.current_question == 0, key="prev_q_sidebar"):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.session_state.current_question_override = None
            st.rerun()
    
    with col2:
        if st.button("Next Topic →", disabled=st.session_state.current_question >= len(current_session["questions"]) - 1, key="next_q_sidebar"):
            st.session_state.current_question = min(len(current_session["questions"]) - 1, st.session_state.current_question + 1)
            st.session_state.editing = None
            st.session_state.current_question_override = None
            st.rerun()
    
    st.divider()
    st.subheader("Session Navigation")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous Session", disabled=st.session_state.current_session == 0, key="prev_session_sidebar"):
            st.session_state.current_session = max(0, st.session_state.current_session - 1)
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.session_state.current_question_override = None
            st.rerun()
    with col2:
        if st.button("Next Session →", disabled=st.session_state.current_session >= len(SESSIONS)-1, key="next_session_sidebar"):
            st.session_state.current_session = min(len(SESSIONS)-1, st.session_state.current_session + 1)
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.session_state.current_question_override = None
            st.rerun()
    
    session_options = [f"Session {s['id']}: {s['title']}" for s in SESSIONS]
    selected_session = st.selectbox("Jump to session:", session_options, index=st.session_state.current_session, key="session_selectbox")
    if session_options.index(selected_session) != st.session_state.current_session:
        st.session_state.current_session = session_options.index(selected_session)
        st.session_state.current_question = 0
        st.session_state.editing = None
        st.session_state.current_question_override = None
        st.rerun()
    
    st.divider()
    
    # ============================================================================
    # SECTION 12C: SIDEBAR - EXPORT OPTIONS
    # ============================================================================
    st.subheader("📤 Export Options")
    
    total_answers = sum(len(session.get("questions", {})) for session in st.session_state.responses.values())
    st.caption(f"Total answers: {total_answers}")
    
    # Prepare data for export
    export_data = {}
    for session in SESSIONS:
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        if session_data.get("questions"):
            export_data[str(session_id)] = {
                "title": session["title"],
                "questions": session_data["questions"]
            }
    
    # Create JSON data
    if export_data:
        json_data = json.dumps({
            "user": st.session_state.user_id,
            "stories": export_data,
            "export_date": datetime.now().isoformat()
        }, indent=2)
        
        # Encode the data for URL
        import base64
        encoded_data = base64.b64encode(json_data.encode()).decode()
        
        # Create URL with the data (UPDATE THIS URL TO YOUR PUBLISHER APP)
        publisher_base_url = "https://deeperbiographer-dny9n2j6sflcsppshrtrmu.streamlit.app/"
        publisher_url = f"{publisher_base_url}?data={encoded_data}"
        
        # Download button
        st.download_button(
            label="📥 Download as JSON",
            data=json_data,
            file_name=f"LifeStory_{st.session_state.user_id}.json",
            mime="application/json",
            use_container_width=True,
            key="download_json_btn"
        )
        
        # Link to publisher
        st.link_button(
            "🖨️ Publish Biography",
            publisher_url,
            use_container_width=True,
            help="Format your biography professionally",
            key="publish_btn"
        )
    else:
        st.warning("No responses to export yet!")
    
    st.divider()
    
    # ============================================================================
    # SECTION 12D: SIDEBAR - DANGEROUS ACTIONS WITH CONFIRMATION
    # ============================================================================
    st.subheader("⚠️ Clear Data")
    
    if st.session_state.confirming_clear == "session":
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("**WARNING: This will delete ALL answers in the current session!**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Delete Session", type="primary", use_container_width=True, key="confirm_delete_session"):
                current_session_id = SESSIONS[st.session_state.current_session]["id"]
                try:
                    # Clear from session state
                    st.session_state.responses[current_session_id]["questions"] = {}
                    # Update the JSON file
                    save_user_data(st.session_state.user_id, st.session_state.responses)
                    st.session_state.confirming_clear = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        with col2:
            if st.button("❌ Cancel", type="secondary", use_container_width=True, key="cancel_delete_session"):
                st.session_state.confirming_clear = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.confirming_clear == "all":
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("**WARNING: This will delete ALL answers for ALL sessions!**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Delete All", type="primary", use_container_width=True, key="confirm_delete_all"):
                try:
                    # Clear from session state
                    for session in SESSIONS:
                        session_id = session["id"]
                        st.session_state.responses[session_id]["questions"] = {}
                    # Update the JSON file
                    save_user_data(st.session_state.user_id, st.session_state.responses)
                    st.session_state.confirming_clear = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        with col2:
            if st.button("❌ Cancel", type="secondary", use_container_width=True, key="cancel_delete_all"):
                st.session_state.confirming_clear = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Session", type="secondary", use_container_width=True, key="clear_session_btn"):
                st.session_state.confirming_clear = "session"
                st.rerun()
        
        with col2:
            if st.button("🔥 Clear All", type="secondary", use_container_width=True, key="clear_all_btn"):
                st.session_state.confirming_clear = "all"
                st.rerun()

# ============================================================================
# SECTION 16: QUICK NOTES VIEWER (IF REQUESTED)
# ============================================================================
if st.session_state.get('show_jots', False) and st.session_state.quick_jots:
    st.markdown("---")
    st.subheader("📝 Your Quick Notes")
    
    for i, jot in enumerate(st.session_state.quick_jots):
        with st.expander(f"Note {i+1} - {jot.get('year', 'No year')} - {jot['word_count']} words", expanded=False):
            st.markdown(f'<div class="jot-box">{jot["text"]}</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✏️ Use as Prompt", key=f"use_jot_{i}"):
                    st.session_state.current_question_override = jot["text"]
                    st.session_state.show_jots = False
                    st.rerun()
            with col2:
                if st.button(f"🗑️ Delete", key=f"delete_jot_{i}"):
                    st.session_state.quick_jots.pop(i)
                    st.rerun()
    
    if st.button("Close Quick Notes", key="close_jots_btn"):
        st.session_state.show_jots = False
        st.rerun()
    
    st.markdown("---")

# ============================================================================
# SECTION 17: MAIN CONTENT - SESSION HEADER WITH "NO BLANK PAGES" FEATURE
# ============================================================================
current_session = SESSIONS[st.session_state.current_session]
current_session_id = current_session["id"]

# Get the current question text (either override or regular)
if st.session_state.current_question_override:
    current_question_text = st.session_state.current_question_override
    question_source = "custom"
else:
    current_question_text = current_session["questions"][st.session_state.current_question]
    question_source = "regular"

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader(f"Session {current_session_id}: {current_session['title']}")
    
    # Show response count for this session
    session_responses = len(st.session_state.responses[current_session_id].get("questions", {}))
    total_questions = len(current_session["questions"])
    st.caption(f"📝 {session_responses}/{total_questions} topics answered")
    
    if st.session_state.ghostwriter_mode:
        st.markdown('<p class="ghostwriter-tag">Professional Ghostwriter Mode</p>', unsafe_allow_html=True)
        
with col2:
    if question_source == "custom":
        st.markdown(f'<div class="question-counter" style="margin-top: 1rem; color: #ff6b00;">✨ Custom Prompt</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="question-counter" style="margin-top: 1rem;">Topic {st.session_state.current_question + 1} of {len(current_session["questions"])}</div>', unsafe_allow_html=True)

with col3:
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("← Previous Topic", disabled=st.session_state.current_question == 0, key="prev_q_quick", use_container_width=True):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.session_state.current_question_override = None
            st.rerun()
    with nav_col2:
        # NEW: REFRESH PROMPT BUTTON
        if st.button("🔄 New Prompt", key="refresh_prompt_btn", use_container_width=True):
            # Rotate through fallback prompts
            st.session_state.prompt_index = (st.session_state.prompt_index + 1) % len(FALLBACK_PROMPTS)
            st.session_state.current_question_override = FALLBACK_PROMPTS[st.session_state.prompt_index]
            st.rerun()

# Show current topic
st.markdown(f"""
<div class="question-box">
    {current_question_text}
</div>
""", unsafe_allow_html=True)

# Show session guidance (only for regular prompts)
if question_source == "regular":
    st.markdown(f"""
    <div class="chapter-guidance">
        {current_session.get('guidance', '')}
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("✨ **Custom Prompt** - Write about whatever comes to mind!")

# Topics progress (only for regular prompts)
if question_source == "regular":
    session_data = st.session_state.responses.get(current_session_id, {})
    topics_answered = len(session_data.get("questions", {}))
    total_topics = len(current_session["questions"])

    if total_topics > 0:
        topic_progress = topics_answered / total_topics
        st.progress(min(topic_progress, 1.0))
        st.caption(f"📝 Topics explored: {topics_answered}/{total_topics} ({topic_progress*100:.0f}%)")

# ============================================================================
# SECTION 18: CONVERSATION DISPLAY AND CHAT INPUT
# ============================================================================
if current_session_id not in st.session_state.session_conversations:
    st.session_state.session_conversations[current_session_id] = {}

conversation = st.session_state.session_conversations[current_session_id].get(current_question_text, [])

if not conversation:
    # Check if we have a saved response for this question
    saved_response = st.session_state.responses[current_session_id]["questions"].get(current_question_text)
    
    if saved_response:
        # We have a saved response but no conversation - create one
        conversation = [
            {"role": "assistant", "content": f"Let's explore this topic in detail: {current_question_text}"},
            {"role": "user", "content": saved_response["answer"]}
        ]
        st.session_state.session_conversations[current_session_id][current_question_text] = conversation
    else:
        # Start new conversation
        with st.chat_message("assistant", avatar="👔"):
            welcome_msg = f"""<div style='font-size: 1.4rem; margin-bottom: 1rem;'>
Let's explore this topic in detail:
</div>
<div style='font-size: 1.8rem; font-weight: bold; color: #2c3e50; line-height: 1.3;'>
{current_question_text}
</div>
<div style='font-size: 1.1rem; margin-top: 1.5rem; color: #555;'>
Take your time with this—good biographies are built from thoughtful reflection.
</div>"""
            
            st.markdown(welcome_msg, unsafe_allow_html=True)
            conversation.append({"role": "assistant", "content": f"Let's explore this topic in detail: {current_question_text}\n\nTake your time with this—good biographies are built from thoughtful reflection."})
            st.session_state.session_conversations[current_session_id][current_question_text] = conversation

# Display existing conversation
for i, message in enumerate(conversation):
    if message["role"] == "assistant":
        with st.chat_message("assistant", avatar="👔"):
            st.markdown(message["content"])
    
    elif message["role"] == "user":
        is_editing = (st.session_state.editing == (current_session_id, current_question_text, i))
        
        with st.chat_message("user", avatar="👤"):
            if is_editing:
                # Edit mode
                new_text = st.text_area(
                    "Edit your answer:",
                    value=st.session_state.edit_text,
                    key=f"edit_area_{current_session_id}_{hash(current_question_text)}_{i}",
                    height=150,
                    label_visibility="collapsed"
                )
                
                if new_text:
                    edit_word_count = len(re.findall(r'\w+', new_text))
                    st.caption(f"📝 Editing: {edit_word_count} words")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Save", key=f"save_{current_session_id}_{hash(current_question_text)}_{i}", type="primary"):
                        # Auto-correct before saving
                        if st.session_state.spellcheck_enabled:
                            new_text = auto_correct_text(new_text)
                        
                        # Update conversation
                        conversation[i]["content"] = new_text
                        st.session_state.session_conversations[current_session_id][current_question_text] = conversation
                        
                        # Save to JSON file
                        save_response(current_session_id, current_question_text, new_text)
                        
                        st.session_state.editing = None
                        st.rerun()
                with col2:
                    if st.button("✕ Cancel", key=f"cancel_{current_session_id}_{hash(current_question_text)}_{i}"):
                        st.session_state.editing = None
                        st.rerun()
            else:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(message["content"])
                    word_count = len(re.findall(r'\w+', message["content"]))
                    st.caption(f"📝 {word_count} words • Click ✏️ to edit")
                with col2:
                    if st.button("✏️", key=f"edit_{current_session_state.current_session}_{hash(current_question_text)}_{i}"):
                        st.session_state.editing = (current_session_id, current_question_text, i)
                        st.session_state.edit_text = message["content"]
                        st.rerun()

# ============================================================================
# CHAT INPUT BOX
# ============================================================================
input_container = st.container()

with input_container:
    st.write("")
    st.write("")
    
    user_input = st.chat_input("Type your answer here...", key="chat_input")
    
    if user_input:
        # Auto-correct if enabled
        if st.session_state.spellcheck_enabled:
            user_input = auto_correct_text(user_input)
        
        # Add user message to conversation
        conversation.append({"role": "user", "content": user_input})
        
        # Generate AI response
        with st.chat_message("assistant", avatar="👔"):
            with st.spinner("Reflecting on your story..."):
                try:
                    # Generate thoughtful response
                    conversation_history = conversation[:-1]
                    
                    messages_for_api = [
                        {"role": "system", "content": get_system_prompt()},
                        *conversation_history,
                        {"role": "user", "content": user_input}
                    ]
                    
                    if st.session_state.ghostwriter_mode:
                        temperature = 0.8
                        max_tokens = 400
                    else:
                        temperature = 0.7
                        max_tokens = 300
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages_for_api,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    ai_response = response.choices[0].message.content
                    
                    # Add professional note
                    word_count = len(re.findall(r'\w+', user_input))
                    if word_count < 50:
                        ai_response += f"\n\n**Note:** You've touched on something important. Consider expanding on the sensory details—what did you see, hear, feel?"
                    elif word_count < 150:
                        ai_response += f"\n\n**Note:** Good detail. Where does the emotional weight live in this memory?"
                    
                    st.markdown(ai_response)
                    conversation.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    error_msg = "Thank you for sharing that. Your response has been saved."
                    st.markdown(error_msg)
                    conversation.append({"role": "assistant", "content": error_msg})
        
        # Save conversation
        st.session_state.session_conversations[current_session_id][current_question_text] = conversation
        
        # CRITICAL: Save the response to JSON file
        save_response(current_session_id, current_question_text, user_input)
        
        st.rerun()

# ============================================================================
# SECTION 19: WORD PROGRESS INDICATOR
# ============================================================================
st.divider()

# Get progress info
progress_info = get_progress_info(current_session_id)

# Display progress container
st.markdown(f"""
<div class="progress-container">
    <div class="progress-header">📊 Session Progress</div>
    <div class="progress-status">{progress_info['emoji']} {progress_info['progress_percent']:.0f}% complete • {progress_info['status_text']}</div>
    <div class="progress-bar-container">
        <div class="progress-bar-fill" style="width: {min(progress_info['progress_percent'], 100)}%; background-color: {progress_info['color']};"></div>
    </div>
    <div style="text-align: center; font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
        {progress_info['current_count']} / {progress_info['target']} words
    </div>
</div>
""", unsafe_allow_html=True)

# Edit target button
if st.button("✏️ Change Word Target", key="edit_word_target_bottom", use_container_width=True):
    st.session_state.editing_word_target = not st.session_state.editing_word_target
    st.rerun()

# Show edit interface when triggered
if st.session_state.editing_word_target:
    st.markdown('<div class="edit-target-box">', unsafe_allow_html=True)
    st.write("**Change Word Target**")
    
    new_target = st.number_input(
        "Target words for this session:",
        min_value=100,
        max_value=5000,
        value=progress_info['target'],
        key="target_edit_input_bottom",
        label_visibility="collapsed"
    )
    
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 Save", key="save_word_target_bottom", type="primary", use_container_width=True):
            # Update session state
            st.session_state.responses[current_session_id]["word_target"] = new_target
            # Update JSON file
            save_user_data(st.session_state.user_id, st.session_state.responses)
            st.session_state.editing_word_target = False
            st.rerun()
    with col_cancel:
        if st.button("❌ Cancel", key="cancel_word_target_bottom", use_container_width=True):
            st.session_state.editing_word_target = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# SECTION 20: FOOTER WITH STATISTICS
# ============================================================================
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    total_words_all_sessions = sum(calculate_author_word_count(s["id"]) for s in SESSIONS)
    st.metric("Total Words", f"{total_words_all_sessions}")
with col2:
    completed_sessions = sum(1 for s in SESSIONS if len(st.session_state.responses[s["id"]].get("questions", {})) == len(s["questions"]))
    st.metric("Completed Sessions", f"{completed_sessions}/{len(SESSIONS)}")
with col3:
    total_topics_answered = sum(len(st.session_state.responses[s["id"]].get("questions", {})) for s in SESSIONS)
    total_all_topics = sum(len(s["questions"]) for s in SESSIONS)
    st.metric("Topics Explored", f"{total_topics_answered}/{total_all_topics}")

# ============================================================================
# SECTION 21: PUBLISH & VAULT SECTION
# ============================================================================
st.divider()
st.subheader("📘 Publish & Save Your Biography")

# Get the current user's data
current_user = st.session_state.get('user_id', '')
export_data = {}

# Prepare data for export
for session in SESSIONS:
    session_id = session["id"]
    session_data = st.session_state.responses.get(session_id, {})
    if session_data.get("questions"):
        export_data[str(session_id)] = {
            "title": session["title"],
            "questions": session_data["questions"]
        }

if current_user and current_user != "" and export_data:
    # Count total stories
    total_stories = sum(len(session['questions']) for session in export_data.values())
    
    # Create JSON data for the publisher
    json_data = json.dumps({
        "user": current_user,
        "stories": export_data,
        "export_date": datetime.now().isoformat()
    }, indent=2)
    
    # Encode the data for URL
    import base64
    encoded_data = base64.b64encode(json_data.encode()).decode()
    
    # Create URL for the publisher (UPDATE THIS TO YOUR ACTUAL PUBLISHER URL)
    publisher_base_url = "https://deeperbiographer-dny9n2j6sflcsppshrtrmu.streamlit.app/"
    publisher_url = f"{publisher_base_url}?data={encoded_data}"
    
    st.success(f"✅ **{total_stories} stories ready to publish!**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🖨️ Create Your Book")
        st.markdown(f"""
        Generate a beautiful, formatted biography from your stories.
        
        **[📘 Click to Create Biography]({publisher_url})**
        
        Your book will include:
        • Professional formatting
        • Table of contents
        • All your stories organized
        • Ready to print or share
        """)
    
    with col2:
        st.markdown("#### 🔐 Save to Your Vault")
        st.markdown("""
        **After creating your book:**
        
        1. Generate your biography (link on left)
        2. Download the formatted PDF
        3. Save it to your secure vault
        
        **[💾 Go to Secure Vault](https://digital-legacy-vault-vwvd4eclaeq4hxtcbbshr2.streamlit.app/)**
        
        Your vault preserves important documents forever.
        """)
    
    # Backup download
    with st.expander("📥 Download Raw Data (Backup)"):
        st.download_button(
            label="Download Stories as JSON",
            data=json_data,
            file_name=f"{current_user}_stories.json",
            mime="application/json",
            use_container_width=True,
            key="backup_download_btn"
        )
        st.caption("Use this if the publisher link doesn't work")
        
elif current_user and current_user != "":
    st.info("📝 **Answer some questions first!** Come back here after saving some stories.")
else:
    st.info("👤 **Enter your name to begin**")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")

# Show account info in footer if available
if st.session_state.user_account:
    profile = st.session_state.user_account['profile']
    account_age = (datetime.now() - datetime.fromisoformat(st.session_state.user_account['created_at'])).days
    
    footer_info = f"""
    MemLife Timeline • 👤 {profile['first_name']} {profile['last_name']} • 📧 {profile['email']} • 
    🎂 {profile.get('birthdate', 'Not specified')} • 🔥 {st.session_state.streak_days} day streak • 
    📅 Account Age: {account_age} days
    """
    st.caption(footer_info)
else:
    st.caption(f"DeeperVault UK Legacy Builder • User: {st.session_state.user_id} • 🔥 {st.session_state.streak_days} day streak • Data saved to JSON files")
