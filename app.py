import os
import streamlit as st
from io import BytesIO
import base64
import zipfile
import json
from typing import Dict, List
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import re
import time

# MUST be first Streamlit call
st.set_page_config(
    page_title="🎓 AI Career Builder Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"  # Fixed default
)

# Now it's safe to use any st.* calls
load_dotenv()

# Initialize session state AFTER page config
if 'sidebar_visible' not in st.session_state:
    st.session_state.sidebar_visible = True
if 'selected_template' not in st.session_state:
    st.session_state.selected_template = "Modern Professional"
if 'selected_portfolio_template' not in st.session_state:
    st.session_state.selected_portfolio_template = "Modern Minimal"
if 'student_profile' not in st.session_state:
    st.session_state.student_profile = {}
if 'profile_completeness' not in st.session_state:
    st.session_state.profile_completeness = 0

# Only now do your API key check
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    st.error("⚠️ Please set `GEMINI_API_KEY` in your `.env` file.")
    st.stop()
else:
    genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.0-flash-exp"

# Apply CSS to hide/show the sidebar
st.markdown(
    f"""
<style>
[data-testid="stSidebar"] {{
    display: {'block' if st.session_state.sidebar_visible else 'none'};
}}
/* Expand main area when sidebar hidden */
[data-testid="stAppViewContainer"] > .main {{
    margin-left: {'0rem' if not st.session_state.sidebar_visible else 'unset'};
}}
</style>
""",
    unsafe_allow_html=True
)

# ------------------------- Profile Management Functions -------------------------

def calculate_profile_completeness(data: Dict) -> int:
    """Calculate profile completion percentage"""
    required_fields = ['name', 'email', 'phone', 'education', 'target_role', 'technical_skills']
    optional_fields = ['experiences', 'projects', 'certifications', 'achievements', 'linkedin', 'github']
    
    filled_required = sum(
        1 for field in required_fields
        if (data.get(field).strip() if isinstance(data.get(field), str) else data.get(field))
    )
    
    filled_optional = sum(
        1 for field in optional_fields
        if data.get(field)
    )
    
    
    required_weight = 70
    optional_weight = 30
    
    required_score = (filled_required / len(required_fields)) * required_weight
    optional_score = (filled_optional / len(optional_fields)) * optional_weight
    
    return int(required_score + optional_score)

def save_profile_to_json(data: Dict) -> str:
    """Save student profile to JSON"""
    return json.dumps(data, indent=2)

def load_profile_from_json(json_str: str) -> Dict:
    """Load student profile from JSON"""
    try:
        return json.loads(json_str)
    except:
        return {}

# ------------------------- Advanced Styling -----------------------------

ADVANCED_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --secondary: #ec4899;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --dark: #0f172a;
        --light: #f8fafc;
        --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --gradient-4: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Removed header visibility: hidden to keep hamburger button visible */
    
    .main {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Enhanced Form Styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        color: white !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
    }
    
    .stNumberInput > div > div > input {
        background: rgba(255,255,255,0.05) !important;
        color: white !important;
    }
    
    /* Animated Header */
    .hero-header {
        background: var(--gradient-1);
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(99,102,241,0.4);
        animation: slideDown 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    }
    
    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
        background-size: 50px 50px;
        animation: backgroundMove 20s linear infinite;
    }
    
    .hero-header h1 {
        color: white;
        font-size: clamp(2rem, 5vw, 3.5rem);
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        font-family: 'Space Grotesk', sans-serif;
        position: relative;
        z-index: 1;
    }
    
    .hero-header .subtitle {
        color: rgba(255,255,255,0.95);
        font-size: clamp(1rem, 2vw, 1.3rem);
        margin-top: 1rem;
        font-weight: 400;
        position: relative;
        z-index: 1;
    }
    
    /* Glass Cards */
    .glass-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        animation: fadeInUp 0.6s ease-out;
    }
    
    .glass-card:hover {
        background: rgba(255,255,255,0.08);
        border-color: rgba(99,102,241,0.3);
        transform: translateY(-5px);
        box-shadow: 0 15px 45px rgba(99,102,241,0.3);
    }
    
    /* Buttons */
    .stButton>button {
        background: var(--gradient-1) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.9rem 2.5rem !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(99,102,241,0.4) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(99,102,241,0.5) !important;
    }
    
    /* Download Button */
    .download-btn {
        display: inline-block;
        padding: 0.9rem 2rem;
        background: var(--gradient-4);
        color: white;
        text-decoration: none;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(67,233,123,0.4);
        margin: 0.5rem;
    }
    
    .download-btn:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 8px 25px rgba(67,233,123,0.5);
        text-decoration: none;
        color: white;
    }
    
    /* Template Selection Cards */
    .template-card {
        background: rgba(255,255,255,0.05);
        border: 2px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .template-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.5s;
    }
    
    .template-card:hover::before {
        left: 100%;
    }
    
    .template-card:hover {
        background: rgba(255,255,255,0.1);
        border-color: var(--primary);
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(99,102,241,0.3);
    }
    
    .template-card.selected {
        background: rgba(99,102,241,0.2);
        border-color: var(--primary);
        box-shadow: 0 0 30px rgba(99,102,241,0.4);
    }
    
    .template-card h4 {
        color: white;
        font-size: 1.3rem;
        margin-bottom: 0.5rem;
    }
    
    .template-card p {
        color: rgba(255,255,255,0.7);
        font-size: 0.95rem;
    }
    
    .template-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        background: var(--gradient-1);
        border-radius: 20px;
        font-size: 0.75rem;
        margin-top: 0.5rem;
        color: white;
    }
    
    /* Alerts */
    .alert-success {
        background: linear-gradient(135deg, rgba(16,185,129,0.2) 0%, rgba(5,150,105,0.2) 100%);
        border-left: 4px solid #10b981;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #d1fae5;
        backdrop-filter: blur(10px);
    }
    
    .alert-error {
        background: linear-gradient(135deg, rgba(239,68,68,0.2) 0%, rgba(220,38,38,0.2) 100%);
        border-left: 4px solid #ef4444;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #fecaca;
        backdrop-filter: blur(10px);
    }
    
    .alert-info {
        background: linear-gradient(135deg, rgba(59,130,246,0.2) 0%, rgba(37,99,235,0.2) 100%);
        border-left: 4px solid #3b82f6;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #dbeafe;
        backdrop-filter: blur(10px);
    }
    
    .alert-warning {
        background: linear-gradient(135deg, rgba(245,158,11,0.2) 0%, rgba(217,119,6,0.2) 100%);
        border-left: 4px solid #f59e0b;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #fef3c7;
        backdrop-filter: blur(10px);
    }
    
    /* Feature Grid */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        cursor: pointer;
    }
    
    .feature-card:hover {
        transform: translateY(-10px) scale(1.02);
        background: rgba(255,255,255,0.08);
        box-shadow: 0 15px 40px rgba(99,102,241,0.3);
        border-color: rgba(99,102,241,0.5);
    }
    
    .feature-card .icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    /* Animations */
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-50px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes backgroundMove {
        0% { transform: translate(0, 0); }
        100% { transform: translate(50px, 50px); }
    }

    /* Advanced 3D Animations */
    .card-3d {
        transform-style: preserve-3d;
        transition: transform 0.6s;
    }
    
    .card-3d:hover {
        transform: rotateY(10deg) rotateX(-10deg);
    }
    
    /* Morphing Shapes */
    .morph-shape {
        border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
        animation: morph 8s ease-in-out infinite;
        background: linear-gradient(45deg, var(--primary), var(--secondary));
    }
    
    @keyframes morph {
        0% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
        50% { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }
        100% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
    }
    
    /* Parallax Background */
    .parallax-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        transform: translateZ(-1px) scale(2);
    }
    
    /* Cursor Following Effect */
    .cursor-follower {
        position: fixed;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.1);
        pointer-events: none;
        z-index: 9999;
        transition: transform 0.1s ease-out;
    }
    
    /* Glowing Text Effect */
    .glow-text {
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5),
                     0 0 20px rgba(255, 255, 255, 0.3),
                     0 0 30px rgba(255, 255, 255, 0.2);
    }
    
    /* Floating Animation */
    .floating {
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
        100% { transform: translateY(0px); }
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: rgba(255,255,255,0.05);
        padding: 0.5rem;
        border-radius: 15px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        color: rgba(255,255,255,0.7);
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient-1) !important;
        color: white !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .hero-header h1 {
            font-size: 2rem;
        }
        .feature-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
"""

# ------------------------- Gemini API Call -----------------------------

def call_gemini_with_retry(prompt: str, max_tokens: int = 2500, retries: int = 3) -> str:
    """Enhanced Gemini API call with retry logic"""
    
    for attempt in range(retries):
        try:
            model = genai.GenerativeModel(
                MODEL_NAME,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": max_tokens,
                },
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            
            response = model.generate_content(prompt)
            
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            
            if hasattr(response, 'candidates') and response.candidates:
                text_parts = []
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                
                if text_parts:
                    return ' '.join(text_parts).strip()
            
            if attempt < retries - 1:
                time.sleep(2)
                continue
            else:
                return "I apologize, but I couldn't generate content at this moment. Please try again."
                
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower():
                return "⚠️ API quota exceeded. Please try again later."
            elif "invalid" in error_msg.lower():
                return "⚠️ Invalid API key. Please check your GEMINI_API_KEY."
            elif attempt < retries - 1:
                time.sleep(2)
                continue
            else:
                return f"⚠️ Error: {error_msg}"
    
    return "Unable to generate content. Please try again."

# ------------------------- PDF Generation -----------------------------

def clean_markdown_for_pdf(content: str) -> str:
    """Remove markdown code blocks"""
    content = re.sub(r'```markdown\s*', '', content)
    content = re.sub(r'```\s*', '', content)
    content = content.replace('```', '')
    return content.strip()

def create_professional_pdf(content: str, name: str, doc_type: str = "resume") -> bytes:
    """Create professional PDF"""
    
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
        from reportlab.lib.colors import HexColor
    except ImportError:
        raise Exception("ReportLab not installed. Install with: pip install reportlab")
    
    content = clean_markdown_for_pdf(content)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#6366f1'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#4f46e5'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=HexColor('#1e293b'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=HexColor('#334155'),
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        leading=14
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=HexColor('#475569'),
        spaceAfter=4,
        leftIndent=20,
        bulletIndent=10,
        leading=13
    )
    
    story = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 0.1*inch))
            continue
        
        line = line.replace('**', '').replace('*', '')
        
        try:
            if line.startswith('# '):
                text = line[2:].strip()
                story.append(Paragraph(text, title_style))
                story.append(Spacer(1, 0.15*inch))
            elif line.startswith('## '):
                text = line[3:].strip()
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(text, heading_style))
            elif line.startswith('### '):
                text = line[4:].strip()
                story.append(Paragraph(text, subheading_style))
            elif line.startswith('- ') or line.startswith('• '):
                text = '• ' + line[2:].strip()
                story.append(Paragraph(text, bullet_style))
            else:
                story.append(Paragraph(line, body_style))
        except Exception as e:
            safe_text = line.replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(safe_text, body_style))
    
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")

# ------------------------- Resume Templates -----------------------------

RESUME_TEMPLATES = {
    "Modern Professional": {
        "description": "Clean, modern design with clear sections. Perfect for tech and corporate roles.",
        "badge": "Most Popular",
        "prompt_style": """
Use a modern, clean format with:
- Clear section dividers with horizontal lines
- Bold company/project names
- Italicized dates and locations
- Concise bullet points (1-2 lines each)
- Professional summary at top
- Skills grouped by category
"""
    },
    
    "ATS-Optimized": {
        "description": "Maximized for Applicant Tracking Systems. Simple formatting, keyword-rich.",
        "badge": "ATS-Friendly",
        "prompt_style": """
Use ATS-optimized format with:
- Simple, linear structure (no columns/tables)
- Standard section headings (EXPERIENCE, EDUCATION, SKILLS)
- Keywords from job description prominently placed
- Plain text formatting (no graphics/icons)
- Contact info at top in simple format
- Reverse chronological order
"""
    },
    
    "Creative": {
        "description": "Stand-out design for creative fields like design, marketing, content creation.",
        "badge": "Eye-Catching",
        "prompt_style": """
Use creative, engaging format with:
- Unique section names (e.g., "My Journey" instead of "Experience")
- Personality-driven language
- Story-telling approach
- Creative bullet point symbols (→, ★, ◆)
- Emphasis on portfolio/creative work
- Visual hierarchy with varied formatting
"""
    },
    
    "Technical/Engineering": {
        "description": "Detail-oriented format for developers, engineers, and technical roles.",
        "badge": "Tech-Focused",
        "prompt_style": """
Use technical format with:
- Detailed technical skills section with proficiency levels
- Project descriptions with tech stack details
- GitHub/technical portfolio links prominent
- Code/architecture achievements highlighted
- Certifications and technical training emphasized
- Metrics around system performance, scale, efficiency
"""
    },
    
    "Executive/Senior": {
        "description": "Leadership-focused format for senior positions and executives.",
        "badge": "Leadership",
        "prompt_style": """
Use executive format with:
- Strong professional summary/executive profile
- Leadership achievements and business impact
- Strategic initiatives and organizational results
- Board memberships, publications, speaking engagements
- High-level metrics (revenue, team size, budget)
- Focus on vision and strategy over tactical details
"""
    },
    
    "Academic/Research": {
        "description": "Comprehensive CV format for academia, research, and scientific positions.",
        "badge": "Research",
        "prompt_style": """
Use academic CV format with:
- Detailed education section with thesis/dissertation
- Publications and citations section
- Research experience with methodology details
- Grants, awards, and honors
- Conference presentations and talks
- Teaching experience and courses taught
- Academic service and committee work
"""
    },
    
    "Minimalist": {
        "description": "Ultra-clean, minimal design. Perfect for any industry.",
        "badge": "Simple",
        "prompt_style": """
Use minimalist format with:
- Maximum white space
- Simple typography (one or two fonts)
- Minimal use of bold/italics
- Clean section breaks
- Concise descriptions (1 line when possible)
- Focus on impact over details
- Elegant simplicity
"""
    },
    
    "Startup/Entrepreneurial": {
        "description": "Fast-paced, impact-focused format for startups and growth companies.",
        "badge": "Growth-Minded",
        "prompt_style": """
Use startup-focused format with:
- Emphasis on rapid growth and scaling
- Startup/entrepreneurial experience highlighted
- Metrics around user growth, revenue, market share
- Scrappy, resourceful achievements
- Cross-functional capabilities
- Innovation and experimentation
- "Wear many hats" versatility
"""
    }
}

# ------------------------- Enhanced Prompts -----------------------------

def generate_resume_prompt(template_name, candidate_data):
    """Generate resume prompt based on selected template"""
    
    template = RESUME_TEMPLATES[template_name]
    
    base_prompt = f"""
You are an elite resume writer specializing in {template_name} resumes.

Create an EXCEPTIONAL resume in CLEAN MARKDOWN format.

IMPORTANT: Do NOT wrap output in code blocks. Output plain markdown text only.

**TEMPLATE STYLE:**
{template['prompt_style']}

**CANDIDATE PROFILE:**
Name: {candidate_data.get('name', 'N/A')}
Email: {candidate_data.get('email', 'N/A')} | Phone: {candidate_data.get('phone', 'N/A')}
Location: {candidate_data.get('location', 'N/A')}
LinkedIn: {candidate_data.get('linkedin', 'N/A')} | GitHub: {candidate_data.get('github', 'N/A')}

Target Role: {candidate_data.get('target_role', 'N/A')}
Industry: {candidate_data.get('target_industry', 'N/A')}
Experience Level: {candidate_data.get('experience_level', 'N/A')}

Education: {candidate_data.get('education', 'N/A')}
GPA: {candidate_data.get('gpa', 'N/A')}
Coursework: {candidate_data.get('coursework', 'N/A')}

Technical Skills: {candidate_data.get('technical_skills', 'N/A')}
Soft Skills: {candidate_data.get('soft_skills', 'N/A')}
Languages: {candidate_data.get('languages', 'N/A')}

Work Experience:
{candidate_data.get('work_experience', 'N/A')}

Projects:
{candidate_data.get('projects', 'N/A')}

Certifications: {candidate_data.get('certifications', 'N/A')}
Achievements: {candidate_data.get('achievements', 'N/A')}

Tone: {candidate_data.get('tone', 'Professional')}

**REQUIREMENTS:**
1. Follow the {template_name} template style exactly
2. Use clean Markdown (# ## ### - *)
3. NO code blocks, NO tables
4. Every bullet point MUST have quantifiable metrics
5. Use powerful action verbs (Architected, Engineered, Optimized, Spearheaded)
6. Include ATS keywords for {candidate_data.get('target_role', 'the target role')}
7. Keep concise and impactful
8. Optimize for both ATS and human readers

**STRUCTURE:**

# {candidate_data.get('name', 'Full Name')}
{candidate_data.get('location', 'Location')} | {candidate_data.get('email', 'Email')} | {candidate_data.get('phone', 'Phone')}
LinkedIn: {candidate_data.get('linkedin', 'LinkedIn URL')} | GitHub: {candidate_data.get('github', 'GitHub URL')}

## PROFESSIONAL SUMMARY
[3-4 powerful lines]

## TECHNICAL SKILLS
- Programming Languages: [list]
- Frameworks & Libraries: [list]
- Tools & Platforms: [list]

## EXPERIENCE
### [Job Title] | [Company Name]
*[Dates] | [Location]*
- [Achievement with metrics]

## PROJECTS
### [Project Name]
*Technologies: [Stack]*
- [Description with impact]

## EDUCATION
### [Degree] in [Major]
*[University] | Graduated: [Date] | GPA: {candidate_data.get('gpa', 'N/A')}*

## CERTIFICATIONS & ACHIEVEMENTS
- [Items]

**OUTPUT:** Plain markdown text only, no wrappers.
"""
    
    return base_prompt

MASTER_COVER_LETTER_PROMPT = """
You are an expert career counselor writing compelling cover letters.

IMPORTANT: Output plain text only, no code blocks.

**DETAILS:**
Name: {name}
Role: {role}
Company: {company}
Education: {education}
Skills: {skills}
Why Role: {why_role}
Why Company: {why_company}
Achievement: {achievement}
Tone: {tone}

**STRUCTURE:**

{name}
{email} | {phone} | {linkedin}

{current_date}

Hiring Manager
{company}

Dear Hiring Manager,

**OPENING (3-4 sentences):**
[Hook that grabs attention. State the position.]

**YOUR BACKGROUND (4-5 sentences):**
[Your journey to this field. Relevant experiences. Genuine enthusiasm.]

**YOUR VALUE (4-5 sentences):**
[Top achievement using STAR method. Include technical details and metrics.]

**COMPANY FIT (3-4 sentences):**
[Why THIS company specifically. How you align with their mission. What excites you.]

**CLOSING (2-3 sentences):**
[Reiterate enthusiasm. Thank them. Express eagerness to discuss.]

Sincerely,
{name}

**REQUIREMENTS:**
- 300-450 words total
- Specific examples with metrics
- Show company research
- Authentic voice
- Zero typos

**OUTPUT:** Plain text, no code blocks.
"""

CAREER_ADVISOR_PROMPT = """
You are a senior career advisor with 20+ years of experience helping students and professionals.

**STUDENT PROFILE:**
Name: {name}
Education: {education}
Target Role: {role}
Experience Level: {experience_level}
Skills: {skills}
Industry: {industry}

**QUESTION:**
{question}

**YOUR RESPONSE SHOULD INCLUDE:**

## Direct Answer
[Provide clear, specific answer to their question]

## Actionable Steps
1. [First specific action]
2. [Second specific action]
3. [Third specific action]
4. [Fourth specific action]
5. [Fifth specific action]

## Timeline
- Week 1-2: [What to do]
- Week 3-4: [What to do]
- Month 2-3: [What to do]
- Month 4-6: [What to do]

## Resources
- **Online Courses:** [Specific recommendations]
- **Books:** [Specific titles]
- **Platforms:** [Specific websites/tools]
- **Communities:** [Where to network]

## Encouragement & Motivation
[Supportive, realistic advice that motivates them]

**TONE:** Be supportive, specific, and practical. Use examples when helpful.
"""

# ------------------------- Portfolio Templates -----------------------------

COLOR_PRESETS = {
    "Purple Dream": {"primary": "#6366f1", "secondary": "#764ba2", "accent": "#ec4899"},
    "Ocean Blue": {"primary": "#0ea5e9", "secondary": "#06b6d4", "accent": "#3b82f6"},
    "Sunset Orange": {"primary": "#f97316", "secondary": "#fb923c", "accent": "#ef4444"},
    "Forest Green": {"primary": "#10b981", "secondary": "#059669", "accent": "#34d399"},
    "Rose Gold": {"primary": "#ec4899", "secondary": "#f43f5e", "accent": "#fb7185"},
    "Cyber Purple": {"primary": "#a855f7", "secondary": "#9333ea", "accent": "#c026d3"},
}

FONT_PRESETS = {
    "Modern (Inter)": "font-family: 'Inter', sans-serif;",
    "Professional (Roboto)": "@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap'); font-family: 'Roboto', sans-serif;",
    "Creative (Poppins)": "@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap'); font-family: 'Poppins', sans-serif;",
    "Tech (Fira Code)": "@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500&display=swap'); font-family: 'Fira Code', monospace;",
}


PORTFOLIO_TEMPLATES = {
    "Modern Minimal": {
        "description": "Clean design with subtle animations and plenty of whitespace",
        "preview": "https://example.com/modern-minimal.png"  # You would add actual preview images
    },
    "Creative Portfolio": {
        "description": "Bold colors, creative layouts, and eye-catching animations",
        "preview": "https://example.com/creative.png"
    },
    "Tech Professional": {
        "description": "Dark theme with code snippets and terminal-style elements",
        "preview": "https://example.com/tech.png"
    },
    "Interactive Designer": {
        "description": "3D elements, parallax scrolling, and interactive components",
        "preview": "https://example.com/designer.png"
    }
}
def generate_particles_script(primary_color):
    """Generate particles.js script"""
    return f"""
<script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
<script>
    particlesJS('particles-js', {{
        particles: {{
            number: {{ value: 80, density: {{ enable: true, value_area: 800 }} }},
            color: {{ value: '{primary_color}' }},
            shape: {{ type: 'circle' }},
            opacity: {{ value: 0.5 }},
            size: {{ value: 3, random: true }},
            line_linked: {{
                enable: true,
                distance: 150,
                color: '{primary_color}',
                opacity: 0.4,
                width: 1
            }},
            move: {{ enable: true, speed: 2 }}
        }},
        interactivity: {{
            events: {{
                onhover: {{ enable: true, mode: 'repulse' }},
                onclick: {{ enable: true, mode: 'push' }}
            }}
        }}
    }});
</script>
"""

def generate_theme_toggle_script():
    """Generate theme toggle"""
    return """
<script>
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    const currentTheme = localStorage.getItem('theme') || 'dark';
    html.setAttribute('data-theme', currentTheme);
    
    if (themeToggle) {
        themeToggle.innerHTML = currentTheme === 'dark' ? '☀️' : '🌙';
        themeToggle.addEventListener('click', function() {
            const theme = html.getAttribute('data-theme');
            const newTheme = theme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            this.innerHTML = newTheme === 'dark' ? '☀️' : '🌙';
        });
    }
</script>
"""
def generate_modern_minimal_html(config, font_family, font_import, theme_toggle_html, theme_toggle_script, initial_theme):
    """Generate Modern Minimal portfolio HTML"""
    
    about_section = ""
    if config['show_about']:
        about_section = f"""
    <section id="about" class="section fade-in">
        <div class="container">
            <h2 class="section-title">About Me</h2>
            <div class="about-content">
                <div class="about-text">
                    <p>{config['about']}</p>
                </div>
                <div class="about-stats" style="{'display: none;' if not config['show_stats'] else ''}">
                    <div class="stat-card">
                        <div class="stat-number">{config['num_projects']}+</div>
                        <div class="stat-label">Projects</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{config['num_skills']}+</div>
                        <div class="stat-label">Technologies</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{config['years_exp']}</div>
                        <div class="stat-label">Years</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">100%</div>
                        <div class="stat-label">Passion</div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """

    # Main HTML
    html = f"""
<!DOCTYPE html>
<html lang="en" data-theme="{initial_theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config['name']} - Portfolio</title>
    <style>
        {font_import}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: {config['primary_color']};
            --secondary: {config['secondary_color']};
            --accent: {config['accent_color']};
        }}
        
        [data-theme="dark"] {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: rgba(248, 250, 252, 0.8);
            --card-bg: rgba(255, 255, 255, 0.05);
            --border-color: rgba(255, 255, 255, 0.1);
        }}
        
        [data-theme="light"] {{
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --card-bg: #ffffff;
            --border-color: #e2e8f0;
        }}
        
        body {{
            {font_family}
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow-x: hidden;
            scroll-behavior: smooth;
            transition: background 0.3s ease, color 0.3s ease;
        }}
        
        .theme-toggle {{
            position: fixed;
            top: 1.5rem;
            right: 1.5rem;
            z-index: 1001;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            cursor: pointer;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.1) rotate(20deg);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        }}
        
        #particles-js {{
            position: fixed;
            width: 100%;
            height: 100%;
            z-index: -1;
            {'display: none;' if not config['show_particles'] else ''}
        }}
        
        [data-theme="light"] #particles-js {{
            opacity: 0.3;
        }}
        
        nav {{
            position: fixed;
            top: 0;
            width: 100%;
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            padding: 1.5rem 0;
            z-index: 1000;
            border-bottom: 1px solid var(--border-color);
            {'display: none;' if not config['show_nav'] else ''}
        }}
        
        nav .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        nav .logo {{
            font-size: {config['logo_size']}rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        nav .nav-links {{
            display: flex;
            gap: 2rem;
            list-style: none;
        }}
        
        nav a {{
            color: var(--text-secondary);
            text-decoration: none;
            transition: 0.3s;
            font-weight: 500;
        }}
        
        nav a:hover {{
            color: var(--text-primary);
        }}
        
        .hero {{
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: {config['hero_align']};
            padding: 2rem;
        }}
        
        .hero-content h1 {{
            font-size: {config['hero_title_size']}rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            animation: fadeInUp 0.8s ease-out;
        }}
        
        .hero-content .tagline {{
            font-size: 1.5rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            animation: fadeInUp 0.8s ease-out 0.2s backwards;
        }}
        
        .hero-content .description {{
            font-size: 1.15rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            animation: fadeInUp 0.8s ease-out 0.4s backwards;
        }}
        
        .btn {{
            padding: 1rem 2rem;
            border-radius: {config['button_radius']}px;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            margin: 0.5rem;
            transition: all 0.3s ease;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        }}
        
        .btn-primary:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        }}
        
        .btn-secondary {{
            border: 2px solid var(--primary);
            color: var(--primary);
        }}
        
        .btn-secondary:hover {{
            background: rgba(99, 102, 241, 0.1);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        
        .section {{
            padding: 5rem 0;
        }}
        
        .section-title {{
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 3rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .about-content {{
            display: grid;
            grid-template-columns: {config.get('about_layout', '1fr 1fr')};
            gap: 3rem;
            align-items: center;
        }}
        
        .about-text {{
            font-size: 1.1rem;
            line-height: 1.7;
        }}
        
        .about-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
        }}
        
        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: {config['card_radius']}px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
        }}
        
        .skills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }}
        
        .skill-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: {config['card_radius']}px;
            padding: 2rem;
            transition: all 0.3s ease;
        }}
        
        .skill-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .skill-card h3 {{
            margin-bottom: 1rem;
            color: var(--primary);
        }}
        
        .skill-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        
        .skill-tag {{
            background: rgba(99, 102, 241, 0.1);
            color: var(--primary);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
        
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
        }}
        
        .project-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: {config['card_radius']}px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .project-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .project-image {{
            height: 200px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
        }}
        
        .project-content {{
            padding: 1.5rem;
        }}
        
        .project-content h3 {{
            margin-bottom: 1rem;
            color: var(--primary);
        }}
        
        .project-tech {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }}
        
        .tech-badge {{
            background: rgba(99, 102, 241, 0.1);
            color: var(--primary);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
        
        .contact-content {{
            text-align: center;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .contact-content p {{
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }}
        
        .contact-info {{
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }}
        
        .social-links {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            font-size: 1.5rem;
        }}
        
        .social-links a {{
            color: var(--primary);
            transition: all 0.3s ease;
        }}
        
        .social-links a:hover {{
            transform: translateY(-3px);
        }}
        
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .fade-in {{
            opacity: 0;
            transform: translateY(30px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }}
        
        .fade-in.visible {{
            opacity: 1;
            transform: translateY(0);
        }}
        
        @media (max-width: 768px) {{
            .about-content {{
                grid-template-columns: 1fr;
            }}
            
            .about-stats {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            nav .nav-links {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div id="particles-js"></div>
    {theme_toggle_html}
    <nav>
        <div class="container">
            <div class="logo">{config['name']}</div>
            <ul class="nav-links">
                <li><a href="#home">Home</a></li>
                {'<li><a href="#about">About</a></li>' if config['show_about'] else ''}
                <li><a href="#skills">Skills</a></li>
                <li><a href="#projects">Projects</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </div>
    </nav>

    <section id="home" class="hero">
        <div class="hero-content">
            <div style="font-size: 1.3rem; color: var(--primary); margin-bottom: 1rem;">{config['greeting_text']}</div>
            <h1>{config['name']}</h1>
            <p class="tagline">{config['tagline']}</p>
            <p class="description">{config['about']}</p>
            <div>
                <a href="#projects" class="btn btn-primary">View Work →</a>
                <a href="#contact" class="btn btn-secondary">Contact</a>
            </div>
        </div>
    </section>

    {about_section}

    <section id="skills" class="section fade-in">
        <div class="container">
            <h2 class="section-title">Skills & Expertise</h2>
            <div class="skills-grid">{config['skills_html']}</div>
        </div>
    </section>

    <section id="projects" class="section fade-in">
        <div class="container">
            <h2 class="section-title">Featured Projects</h2>
            <div class="projects-grid">{config['projects_html']}</div>
        </div>
    </section>

    <section id="contact" class="section fade-in">
        <div class="container">
            <h2 class="section-title">Let's Connect</h2>
            <div class="contact-content">
                <p>I'm always excited to collaborate on innovative projects!</p>
                <div class="contact-info">{config['email']}</div>
                <div class="social-links">{config['social_links_html']}</div>
            </div>
        </div>
    </section>

    {config['particles_script']}
    {theme_toggle_script}

    <script>
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth' }});
                }}
            }});
        }});
        
        // Fade in animation on scroll
        const observerOptions = {{
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        }};
        
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.classList.add('visible');
                }}
            }});
        }}, observerOptions);
        
        document.querySelectorAll('.fade-in').forEach(el => {{
            observer.observe(el);
        }});
    </script>
</body>
</html>
"""
    return html

def generate_creative_portfolio_html(config, font_family, font_import, theme_toggle_html, theme_toggle_script, initial_theme):
    """Generate Creative Portfolio HTML with morphing shapes and animations"""
    
    # Similar structure but with creative elements
    # This is a simplified version - you would expand it with more creative features
    
    about_section = ""
    if config['show_about']:
        about_section = f"""
    <section id="about" class="section">
        <div class="morph-shape"></div>
        <div class="container">
            <h2 class="section-title glow-text">About Me</h2>
            <div class="about-content">
                <div class="about-text">
                    <p>{config['about']}</p>
                </div>
                <div class="about-visual">
                    <div class="floating-element"></div>
                </div>
            </div>
        </div>
    </section>
    """

    html = f"""
<!DOCTYPE html>
<html lang="en" data-theme="{initial_theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config['name']} - Creative Portfolio</title>
    <style>
        {font_import}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: {config['primary_color']};
            --secondary: {config['secondary_color']};
            --accent: {config['accent_color']};
        }}
        
        [data-theme="dark"] {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: rgba(248, 250, 252, 0.8);
            --card-bg: rgba(255, 255, 255, 0.05);
            --border-color: rgba(255, 255, 255, 0.1);
        }}
        
        [data-theme="light"] {{
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --card-bg: #ffffff;
            --border-color: #e2e8f0;
        }}
        
        body {{
            {font_family}
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow-x: hidden;
            scroll-behavior: smooth;
            transition: background 0.3s ease, color 0.3s ease;
        }}
        
        .theme-toggle {{
            position: fixed;
            top: 1.5rem;
            right: 1.5rem;
            z-index: 1001;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            cursor: pointer;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.1) rotate(20deg);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        }}
        
        #particles-js {{
            position: fixed;
            width: 100%;
            height: 100%;
            z-index: -1;
            {'display: none;' if not config['show_particles'] else ''}
        }}
        
        [data-theme="light"] #particles-js {{
            opacity: 0.3;
        }}
        
        nav {{
            position: fixed;
            top: 0;
            width: 100%;
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            padding: 1.5rem 0;
            z-index: 1000;
            border-bottom: 1px solid var(--border-color);
            {'display: none;' if not config['show_nav'] else ''}
        }}
        
        nav .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        nav .logo {{
            font-size: {config['logo_size']}rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        nav .nav-links {{
            display: flex;
            gap: 2rem;
            list-style: none;
        }}
        
        nav a {{
            color: var(--text-secondary);
            text-decoration: none;
            transition: 0.3s;
            font-weight: 500;
        }}
        
        nav a:hover {{
            color: var(--text-primary);
        }}
        
        .hero {{
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: {config['hero_align']};
            padding: 2rem;
            position: relative;
            overflow: hidden;
        }}
        
        .hero::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 20% 80%, var(--primary) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, var(--secondary) 0%, transparent 50%);
            opacity: 0.1;
            z-index: -1;
        }}
        
        .hero-content h1 {{
            font-size: {config['hero_title_size']}rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            animation: fadeInUp 0.8s ease-out;
        }}
        
        .hero-content .tagline {{
            font-size: 1.5rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            animation: fadeInUp 0.8s ease-out 0.2s backwards;
        }}
        
        .hero-content .description {{
            font-size: 1.15rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            animation: fadeInUp 0.8s ease-out 0.4s backwards;
        }}
        
        .btn {{
            padding: 1rem 2rem;
            border-radius: {config['button_radius']}px;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            margin: 0.5rem;
            transition: all 0.3s ease;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        }}
        
        .btn-primary:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        }}
        
        .btn-secondary {{
            border: 2px solid var(--primary);
            color: var(--primary);
        }}
        
        .btn-secondary:hover {{
            background: rgba(99, 102, 241, 0.1);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        
        .section {{
            padding: 5rem 0;
            position: relative;
        }}
        
        .section-title {{
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 3rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .morph-shape {{
            position: absolute;
            top: 10%;
            right: 10%;
            width: 300px;
            height: 300px;
            border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
            background: linear-gradient(45deg, var(--primary), var(--secondary));
            opacity: 0.1;
            animation: morph 8s ease-in-out infinite;
            z-index: -1;
        }}
        
        .floating-element {{
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 50%;
            position: relative;
            animation: float 6s ease-in-out infinite;
        }}
        
        .about-content {{
            display: grid;
            grid-template-columns: {config.get('about_layout', '1fr 1fr')};
            gap: 3rem;
            align-items: center;
        }}
        
        .about-text {{
            font-size: 1.1rem;
            line-height: 1.7;
        }}
        
        .skills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }}
        
        .skill-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: {config['card_radius']}px;
            padding: 2rem;
            transition: all 0.3s ease;
            transform-style: preserve-3d;
        }}
        
        .skill-card:hover {{
            transform: translateY(-5px) rotateY(5deg);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .skill-card h3 {{
            margin-bottom: 1rem;
            color: var(--primary);
        }}
        
        .skill-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        
        .skill-tag {{
            background: rgba(99, 102, 241, 0.1);
            color: var(--primary);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
        
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
        }}
        
        .project-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: {config['card_radius']}px;
            overflow: hidden;
            transition: all 0.3s ease;
            transform-style: preserve-3d;
        }}
        
        .project-card:hover {{
            transform: translateY(-5px) rotateY(5deg);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .project-image {{
            height: 200px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
        }}
        
        .project-content {{
            padding: 1.5rem;
        }}
        
        .project-content h3 {{
            margin-bottom: 1rem;
            color: var(--primary);
        }}
        
        .project-tech {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }}
        
        .tech-badge {{
            background: rgba(99, 102, 241, 0.1);
            color: var(--primary);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
        
        .contact-content {{
            text-align: center;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .contact-content p {{
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }}
        
        .contact-info {{
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }}
        
        .social-links {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            font-size: 1.5rem;
        }}
        
        .social-links a {{
            color: var(--primary);
            transition: all 0.3s ease;
        }}
        
        .social-links a:hover {{
            transform: translateY(-3px);
        }}
        
        .glow-text {{
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.5),
                         0 0 20px rgba(255, 255, 255, 0.3),
                         0 0 30px rgba(255, 255, 255, 0.2);
        }}
        
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes morph {{
            0% {{ border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }}
            50% {{ border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }}
            100% {{ border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }}
        }}
        
        @keyframes float {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-20px); }}
            100% {{ transform: translateY(0px); }}
        }}
        
        @media (max-width: 768px) {{
            .about-content {{
                grid-template-columns: 1fr;
            }}
            
            nav .nav-links {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div id="particles-js"></div>
    {theme_toggle_html}
    <nav>
        <div class="container">
            <div class="logo">{config['name']}</div>
            <ul class="nav-links">
                <li><a href="#home">Home</a></li>
                {'<li><a href="#about">About</a></li>' if config['show_about'] else ''}
                <li><a href="#skills">Skills</a></li>
                <li><a href="#projects">Projects</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </div>
    </nav>

    <section id="home" class="hero">
        <div class="hero-content">
            <div style="font-size: 1.3rem; color: var(--primary); margin-bottom: 1rem;">{config['greeting_text']}</div>
            <h1>{config['name']}</h1>
            <p class="tagline">{config['tagline']}</p>
            <p class="description">{config['about']}</p>
            <div>
                <a href="#projects" class="btn btn-primary">View Work →</a>
                <a href="#contact" class="btn btn-secondary">Contact</a>
            </div>
        </div>
    </section>

    {about_section}

    <section id="skills" class="section">
        <div class="container">
            <h2 class="section-title">Skills & Expertise</h2>
            <div class="skills-grid">{config['skills_html']}</div>
        </div>
    </section>

    <section id="projects" class="section">
        <div class="container">
            <h2 class="section-title">Featured Projects</h2>
            <div class="projects-grid">{config['projects_html']}</div>
        </div>
    </section>

    <section id="contact" class="section">
        <div class="container">
            <h2 class="section-title">Let's Connect</h2>
            <div class="contact-content">
                <p>I'm always excited to collaborate on innovative projects!</p>
                <div class="contact-info">{config['email']}</div>
                <div class="social-links">{config['social_links_html']}</div>
            </div>
        </div>
    </section>

    {config['particles_script']}
    {theme_toggle_script}

    <script>
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth' }});
                }}
            }});
        }});
    </script>
</body>
</html>
"""
    return html

def generate_tech_professional_html(config, font_family, font_import, theme_toggle_html, theme_toggle_script, initial_theme):
    """Generate Tech Professional portfolio HTML with terminal-style elements"""
    
    # Similar structure but with tech-focused elements
    # This is a simplified version - you would expand it with more tech features
    
    about_section = ""
    if config['show_about']:
        about_section = f"""
    <section id="about" class="section">
        <div class="container">
            <h2 class="section-title">&gt; About Me</h2>
            <div class="terminal">
                <div class="terminal-header">
                    <div class="terminal-buttons">
                        <div class="terminal-button close"></div>
                        <div class="terminal-button minimize"></div>
                        <div class="terminal-button maximize"></div>
                    </div>
                    <div class="terminal-title">about.sh</div>
                </div>
                <div class="terminal-body">
                    <div class="terminal-line">
                        <span class="terminal-prompt">$</span>
                        <span class="terminal-command">cat about.txt</span>
                    </div>
                    <div class="terminal-output">
                        <p>{config['about']}</p>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """

    html = f"""
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config['name']} - Tech Portfolio</title>
    <style>
        {font_import}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: {config['primary_color']};
            --secondary: {config['secondary_color']};
            --accent: {config['accent_color']};
            --terminal-bg: #1e1e1e;
            --terminal-text: #f8f8f2;
            --terminal-prompt: #50fa7b;
            --terminal-cursor: #f8f8f0;
        }}
        
        body {{
            {font_family}
            background: #0d1117;
            color: #c9d1d9;
            overflow-x: hidden;
            scroll-behavior: smooth;
        }}
        
        .theme-toggle {{
            position: fixed;
            top: 1.5rem;
            right: 1.5rem;
            z-index: 1001;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            cursor: pointer;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.1) rotate(20deg);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        }}
        
        #particles-js {{
            position: fixed;
            width: 100%;
            height: 100%;
            z-index: -1;
            {'display: none;' if not config['show_particles'] else ''}
        }}
        
        nav {{
            position: fixed;
            top: 0;
            width: 100%;
            background: rgba(13, 17, 23, 0.8);
            backdrop-filter: blur(10px);
            padding: 1.5rem 0;
            z-index: 1000;
            border-bottom: 1px solid #30363d;
            {'display: none;' if not config['show_nav'] else ''}
        }}
        
        nav .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        nav .logo {{
            font-size: {config['logo_size']}rem;
            font-weight: 800;
            color: var(--primary);
            font-family: 'Fira Code', monospace;
        }}
        
        nav .nav-links {{
            display: flex;
            gap: 2rem;
            list-style: none;
        }}
        
        nav a {{
            color: #8b949e;
            text-decoration: none;
            transition: 0.3s;
            font-weight: 500;
            font-family: 'Fira Code', monospace;
        }}
        
        nav a:hover {{
            color: #c9d1d9;
        }}
        
        .hero {{
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: {config['hero_align']};
            padding: 2rem;
            position: relative;
        }}
        
        .hero::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                linear-gradient(to right, rgba(13, 17, 23, 0.8) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(13, 17, 23, 0.8) 1px, transparent 1px);
            background-size: 40px 40px;
            z-index: -1;
        }}
        
        .hero-content {{
            max-width: 800px;
        }}
        
        .hero-content h1 {{
            font-size: {config['hero_title_size']}rem;
            color: var(--primary);
            margin-bottom: 1rem;
            font-family: 'Fira Code', monospace;
            animation: fadeInUp 0.8s ease-out;
        }}
        
        .hero-content .tagline {{
            font-size: 1.5rem;
            color: #8b949e;
            margin-bottom: 2rem;
            animation: fadeInUp 0.8s ease-out 0.2s backwards;
        }}
        
        .hero-content .description {{
            font-size: 1.15rem;
            color: #8b949e;
            margin-bottom: 2rem;
            animation: fadeInUp 0.8s ease-out 0.4s backwards;
        }}
        
        .btn {{
            padding: 1rem 2rem;
            border-radius: {config['button_radius']}px;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            margin: 0.5rem;
            transition: all 0.3s ease;
            font-family: 'Fira Code', monospace;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        }}
        
        .btn-primary:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        }}
        
        .btn-secondary {{
            border: 2px solid var(--primary);
            color: var(--primary);
        }}
        
        .btn-secondary:hover {{
            background: rgba(99, 102, 241, 0.1);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        
        .section {{
            padding: 5rem 0;
        }}
        
        .section-title {{
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 3rem;
            color: var(--primary);
            font-family: 'Fira Code', monospace;
        }}
        
        .terminal {{
            background: var(--terminal-bg);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
        
        .terminal-header {{
            background: #21262d;
            padding: 0.5rem 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .terminal-buttons {{
            display: flex;
            gap: 0.5rem;
        }}
        
        .terminal-button {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        .terminal-button.close {{
            background: #ff5f56;
        }}
        
        .terminal-button.minimize {{
            background: #ffbd2e;
        }}
        
        .terminal-button.maximize {{
            background: #27c93f;
        }}
        
        .terminal-title {{
            color: var(--terminal-text);
            font-size: 0.9rem;
            font-family: 'Fira Code', monospace;
        }}
        
        .terminal-body {{
            padding: 1rem;
            font-family: 'Fira Code', monospace;
        }}
        
        .terminal-line {{
            display: flex;
            margin-bottom: 0.5rem;
        }}
        
        .terminal-prompt {{
            color: var(--terminal-prompt);
            margin-right: 0.5rem;
        }}
        
        .terminal-command {{
            color: var(--terminal-text);
        }}
        
        .terminal-output {{
            color: var(--terminal-text);
            margin-top: 0.5rem;
            white-space: pre-wrap;
        }}
        
        .terminal-cursor {{
            display: inline-block;
            width: 10px;
            height: 1.2em;
            background: var(--terminal-cursor);
            animation: blink 1s infinite;
        }}
        
        .skills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }}
        
        .skill-card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: {config['card_radius']}px;
            padding: 2rem;
            transition: all 0.3s ease;
        }}
        
        .skill-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
            border-color: var(--primary);
        }}
        
        .skill-card h3 {{
            margin-bottom: 1rem;
            color: var(--primary);
            font-family: 'Fira Code', monospace;
        }}
        
        .skill-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        
        .skill-tag {{
            background: rgba(99, 102, 241, 0.1);
            color: var(--primary);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-family: 'Fira Code', monospace;
        }}
        
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
        }}
        
        .project-card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: {config['card_radius']}px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .project-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
            border-color: var(--primary);
        }}
        
        .project-image {{
            height: 200px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
        }}
        
        .project-content {{
            padding: 1.5rem;
        }}
        
        .project-content h3 {{
            margin-bottom: 1rem;
            color: var(--primary);
            font-family: 'Fira Code', monospace;
        }}
        
        .project-tech {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }}
        
        .tech-badge {{
            background: rgba(99, 102, 241, 0.1);
            color: var(--primary);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-family: 'Fira Code', monospace;
        }}
        
        .contact-content {{
            text-align: center;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .contact-content p {{
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }}
        
        .contact-info {{
            font-size: 1.2rem;
            margin-bottom: 2rem;
            font-family: 'Fira Code', monospace;
        }}
        
        .social-links {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            font-size: 1.5rem;
        }}
        
        .social-links a {{
            color: var(--primary);
            transition: all 0.3s ease;
        }}
        
        .social-links a:hover {{
            transform: translateY(-3px);
        }}
        
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes blink {{
            0%, 50% {{ opacity: 1; }}
            51%, 100% {{ opacity: 0; }}
        }}
        
        @media (max-width: 768px) {{
            nav .nav-links {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div id="particles-js"></div>
    {theme_toggle_html}
    <nav>
        <div class="container">
            <div class="logo">{config['name']}</div>
            <ul class="nav-links">
                <li><a href="#home">Home</a></li>
                {'<li><a href="#about">About</a></li>' if config['show_about'] else ''}
                <li><a href="#skills">Skills</a></li>
                <li><a href="#projects">Projects</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </div>
    </nav>

    <section id="home" class="hero">
        <div class="hero-content">
            <div style="font-size: 1.3rem; color: var(--primary); margin-bottom: 1rem; font-family: 'Fira Code', monospace;">$ ./greeting.sh</div>
            <h1>{config['name']}</h1>
            <p class="tagline">{config['tagline']}</p>
            <p class="description">{config['about']}</p>
            <div>
                <a href="#projects" class="btn btn-primary">View Work →</a>
                <a href="#contact" class="btn btn-secondary">Contact</a>
            </div>
        </div>
    </section>

    {about_section}

    <section id="skills" class="section">
        <div class="container">
            <h2 class="section-title">&gt; Skills & Expertise</h2>
            <div class="skills-grid">{config['skills_html']}</div>
        </div>
    </section>

    <section id="projects" class="section">
        <div class="container">
            <h2 class="section-title">&gt; Featured Projects</h2>
            <div class="projects-grid">{config['projects_html']}</div>
        </div>
    </section>

    <section id="contact" class="section">
        <div class="container">
            <h2 class="section-title">&gt; Let's Connect</h2>
            <div class="contact-content">
                <p>I'm always excited to collaborate on innovative projects!</p>
                <div class="contact-info">{config['email']}</div>
                <div class="social-links">{config['social_links_html']}</div>
            </div>
        </div>
    </section>

    {config['particles_script']}
    {theme_toggle_script}

    <script>
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth' }});
                }}
            }});
        }});
    </script>
</body>
</html>
"""
    return html

def generate_interactive_designer_html(config, font_family, font_import, theme_toggle_html, theme_toggle_script, initial_theme):
    """Generate Interactive Designer portfolio HTML with 3D elements and parallax"""
    
    # Similar structure but with interactive designer elements
    # This is a simplified version - you would expand it with more interactive features
    
    about_section = ""
    if config['show_about']:
        about_section = f"""
    <section id="about" class="section">
        <div class="container">
            <h2 class="section-title">About Me</h2>
            <div class="about-content">
                <div class="about-text">
                    <p>{config['about']}</p>
                </div>
                <div class="about-visual">
                    <div class="interactive-element"></div>
                </div>
            </div>
        </div>
    </section>
    """

    html = f"""
<!DOCTYPE html>
<html lang="en" data-theme="{initial_theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config['name']} - Interactive Portfolio</title>
    <style>
        {font_import}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --primary: {config['primary_color']};
            --secondary: {config['secondary_color']};
            --accent: {config['accent_color']};
        }}
        
        [data-theme="dark"] {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: rgba(248, 250, 252, 0.8);
            --card-bg: rgba(255, 255, 255, 0.05);
            --border-color: rgba(255, 255, 255, 0.1);
        }}
        
        [data-theme="light"] {{
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --card-bg: #ffffff;
            --border-color: #e2e8f0;
        }}
        
        body {{
            {font_family}
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow-x: hidden;
            scroll-behavior: smooth;
            transition: background 0.3s ease, color 0.3s ease;
            perspective: 1000px;
        }}
        
        .theme-toggle {{
            position: fixed;
            top: 1.5rem;
            right: 1.5rem;
            z-index: 1001;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            cursor: pointer;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.1) rotate(20deg);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        }}
        
        #particles-js {{
            position: fixed;
            width: 100%;
            height: 100%;
            z-index: -1;
            {'display: none;' if not config['show_particles'] else ''}
        }}
        
        [data-theme="light"] #particles-js {{
            opacity: 0.3;
        }}
        
        nav {{
            position: fixed;
            top: 0;
            width: 100%;
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            padding: 1.5rem 0;
            z-index: 1000;
            border-bottom: 1px solid var(--border-color);
            {'display: none;' if not config['show_nav'] else ''}
        }}
        
        nav .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        nav .logo {{
            font-size: {config['logo_size']}rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        nav .nav-links {{
            display: flex;
            gap: 2rem;
            list-style: none;
        }}
        
        nav a {{
            color: var(--text-secondary);
            text-decoration: none;
            transition: 0.3s;
            font-weight: 500;
        }}
        
        nav a:hover {{
            color: var(--text-primary);
        }}
        
        .hero {{
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: {config['hero_align']};
            padding: 2rem;
            position: relative;
            overflow: hidden;
        }}
        
        .hero::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, var(--primary) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, var(--secondary) 0%, transparent 50%);
            opacity: 0.1;
            z-index: -1;
        }}
        
        .hero-content {{
            position: relative;
            z-index: 1;
        }}
        
        .hero-content h1 {{
            font-size: {config['hero_title_size']}rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            animation: fadeInUp 0.8s ease-out;
        }}
        
        .hero-content .tagline {{
            font-size: 1.5rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            animation: fadeInUp 0.8s ease-out 0.2s backwards;
        }}
        
        .hero-content .description {{
            font-size: 1.15rem;
            color: var(--text-secondary);
            margin-bottom: 2rem;
            animation: fadeInUp 0.8s ease-out 0.4s backwards;
        }}
        
        .btn {{
            padding: 1rem 2rem;
            border-radius: {config['button_radius']}px;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            margin: 0.5rem;
            transition: all 0.3s ease;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        }}
        
        .btn-primary:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        }}
        
        .btn-secondary {{
            border: 2px solid var(--primary);
            color: var(--primary);
        }}
        
        .btn-secondary:hover {{
            background: rgba(99, 102, 241, 0.1);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        
        .section {{
            padding: 5rem 0;
            position: relative;
        }}
        
        .section-title {{
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 3rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .about-content {{
            display: grid;
            grid-template-columns: {config.get('about_layout', '1fr 1fr')};
            gap: 3rem;
            align-items: center;
        }}
        
        .about-text {{
            font-size: 1.1rem;
            line-height: 1.7;
        }}
        
        .interactive-element {{
            width: 300px;
            height: 300px;
            position: relative;
            transform-style: preserve-3d;
            animation: rotate3d 20s infinite linear;
        }}
        
        .interactive-element-face {{
            position: absolute;
            width: 300px;
            height: 300px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            opacity: 0.7;
            border: 2px solid var(--primary);
        }}
        
        .interactive-element-face.front {{
            transform: translateZ(150px);
        }}
        
        .interactive-element-face.back {{
            transform: rotateY(180deg) translateZ(150px);
        }}
        
        .interactive-element-face.right {{
            transform: rotateY(90deg) translateZ(150px);
        }}
        
        .interactive-element-face.left {{
            transform: rotateY(-90deg) translateZ(150px);
        }}
        
        .interactive-element-face.top {{
            transform: rotateX(90deg) translateZ(150px);
        }}
        
        .interactive-element-face.bottom {{
            transform: rotateX(-90deg) translateZ(150px);
        }}
        
        .skills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }}
        
        .skill-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: {config['card_radius']}px;
            padding: 2rem;
            transition: all 0.3s ease;
            transform-style: preserve-3d;
        }}
        
        .skill-card:hover {{
            transform: translateY(-5px) rotateY(5deg);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .skill-card h3 {{
            margin-bottom: 1rem;
            color: var(--primary);
        }}
        
        .skill-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        
        .skill-tag {{
            background: rgba(99, 102, 241, 0.1);
            color: var(--primary);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
        
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
        }}
        
        .project-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: {config['card_radius']}px;
            overflow: hidden;
            transition: all 0.3s ease;
            transform-style: preserve-3d;
        }}
        
        .project-card:hover {{
            transform: translateY(-5px) rotateY(5deg);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .project-image {{
            height: 200px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
        }}
        
        .project-content {{
            padding: 1.5rem;
        }}
        
        .project-content h3 {{
            margin-bottom: 1rem;
            color: var(--primary);
        }}
        
        .project-tech {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }}
        
        .tech-badge {{
            background: rgba(99, 102, 241, 0.1);
            color: var(--primary);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
        
        .contact-content {{
            text-align: center;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .contact-content p {{
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }}
        
        .contact-info {{
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }}
        
        .social-links {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            font-size: 1.5rem;
        }}
        
        .social-links a {{
            color: var(--primary);
            transition: all 0.3s ease;
        }}
        
        .social-links a:hover {{
            transform: translateY(-3px);
        }}
        
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes rotate3d {{
            from {{ transform: rotateX(0deg) rotateY(0deg); }}
            to {{ transform: rotateX(360deg) rotateY(360deg); }}
        }}
        
        @media (max-width: 768px) {{
            .about-content {{
                grid-template-columns: 1fr;
            }}
            
            .interactive-element {{
                width: 200px;
                height: 200px;
            }}
            
            .interactive-element-face {{
                width: 200px;
                height: 200px;
            }}
            
            .interactive-element-face.front,
            .interactive-element-face.back {{
                transform: translateZ(100px);
            }}
            
            .interactive-element-face.right,
            .interactive-element-face.left {{
                transform: rotateY(90deg) translateZ(100px);
            }}
            
            .interactive-element-face.top,
            .interactive-element-face.bottom {{
                transform: rotateX(90deg) translateZ(100px);
            }}
            
            nav .nav-links {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div id="particles-js"></div>
    {theme_toggle_html}
    <nav>
        <div class="container">
            <div class="logo">{config['name']}</div>
            <ul class="nav-links">
                <li><a href="#home">Home</a></li>
                {'<li><a href="#about">About</a></li>' if config['show_about'] else ''}
                <li><a href="#skills">Skills</a></li>
                <li><a href="#projects">Projects</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </div>
    </nav>

    <section id="home" class="hero">
        <div class="hero-content">
            <div style="font-size: 1.3rem; color: var(--primary); margin-bottom: 1rem;">{config['greeting_text']}</div>
            <h1>{config['name']}</h1>
            <p class="tagline">{config['tagline']}</p>
            <p class="description">{config['about']}</p>
            <div>
                <a href="#projects" class="btn btn-primary">View Work →</a>
                <a href="#contact" class="btn btn-secondary">Contact</a>
            </div>
        </div>
    </section>

    {about_section}

    <section id="skills" class="section">
        <div class="container">
            <h2 class="section-title">Skills & Expertise</h2>
            <div class="skills-grid">{config['skills_html']}</div>
        </div>
    </section>

    <section id="projects" class="section">
        <div class="container">
            <h2 class="section-title">Featured Projects</h2>
            <div class="projects-grid">{config['projects_html']}</div>
        </div>
    </section>

    <section id="contact" class="section">
        <div class="container">
            <h2 class="section-title">Let's Connect</h2>
            <div class="contact-content">
                <p>I'm always excited to collaborate on innovative projects!</p>
                <div class="contact-info">{config['email']}</div>
                <div class="social-links">{config['social_links_html']}</div>
            </div>
        </div>
    </section>

    {config['particles_script']}
    {theme_toggle_script}

    <script>
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth' }});
                }}
            }});
        }});
    </script>
</body>
</html>
"""
    return html

def generate_portfolio_html(config):
    """Generate complete portfolio HTML with theme support"""
    
    # Get selected template
    template = config.get('template', 'Modern Minimal')
    
    font_import = ""
    font_family = config['font_family']
    if '@import' in font_family:
        parts = font_family.split(';')
        font_import = parts[0] + ';'
        if len(parts) > 1:
            font_family = f"font-family: {parts[1]};"
        else:
            font_family = "font-family: 'Inter', sans-serif;"
    else:
        font_family = "font-family: 'Inter', sans-serif;"

    theme_toggle_html = ""
    theme_toggle_script = ""
    
    if config['theme_mode'] == 'Toggle (User Choice)':
        theme_toggle_html = """
        <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">
            🌙
        </button>
        """
        theme_toggle_script = generate_theme_toggle_script()
    
    initial_theme = 'dark' if config['theme_mode'] in ['Dark', 'Toggle (User Choice)'] else 'light'
    
    # Generate different HTML based on template
    if template == "Modern Minimal":
        html_content = generate_modern_minimal_html(config, font_family, font_import, theme_toggle_html, theme_toggle_script, initial_theme)
    elif template == "Creative Portfolio":
        html_content = generate_creative_portfolio_html(config, font_family, font_import, theme_toggle_html, theme_toggle_script, initial_theme)
    elif template == "Tech Professional":
        html_content = generate_tech_professional_html(config, font_family, font_import, theme_toggle_html, theme_toggle_script, initial_theme)
    elif template == "Interactive Designer":
        html_content = generate_interactive_designer_html(config, font_family, font_import, theme_toggle_html, theme_toggle_script, initial_theme)
    else:
        # Default to Modern Minimal
        html_content = generate_modern_minimal_html(config, font_family, font_import, theme_toggle_html, theme_toggle_script, initial_theme)
    
    return html_content

# ------------------------- Helper Functions -----------------------------

def download_link_bytes(content: bytes, filename: str, mime: str = "application/octet-stream") -> str:
    b64 = base64.b64encode(content).decode()
    return f'<a href="data:{mime};base64,{b64}" download="{filename}" class="download-btn">⬇️ Download {filename}</a>'


def generate_skill_chart(skills):
    """Generate an animated skill chart with smooth transitions."""
    return f"""
    <style>
        .skill-chart-container {{
            width: 100%;
            max-width: 600px;
            margin: 20px auto;
        }}
        .skill-item {{
            margin-bottom: 15px;
        }}
        .skill-name {{
            font-weight: 600;
            margin-bottom: 5px;
            color: #222;
        }}
        .skill-bar {{
            width: 100%;
            height: 10px;
            background: #e5e5e5;
            border-radius: 20px;
            overflow: hidden;
        }}
        .skill-progress {{
            height: 10px;
            width: 0%;
            background: linear-gradient(90deg, #00b4d8, #0077b6);
            border-radius: 20px;
            transition: width 1.5s ease-in-out;
        }}
    </style>

    <div class="skill-chart-container">
        {"".join([
            f'''
            <div class="skill-item">
                <div class="skill-name">{skill.strip().title()}</div>
                <div class="skill-bar">
                    <div class="skill-progress" style="width: 0%;" data-width="{random.randint(70, 100)}%"></div>
                </div>
            </div>
            ''' for skill in skills.split(',')[:5]
        ])}
    </div>

    <script>
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const width = entry.target.getAttribute('data-width');
                    entry.target.style.width = width;
                }}
            }});
        }});

        document.querySelectorAll('.skill-progress').forEach(el => {{
            observer.observe(el);
        }});
    </script>
    """

def generate_3d_project_cards(projects):
    """Generate 3D project cards with hover effects"""
    return "".join([f"""
    <div class="project-card-3d card-3d">
        <div class="card-face card-front">
            <h3>{project['name']}</h3>
            <p>{project['description'][:100]}...</p>
        </div>
        <div class="card-face card-back">
            <h3>Technologies</h3>
            <p>{project['tech']}</p>
            <a href="{project['link']}" class="btn">View Project</a>
        </div>
    </div>
    """ for project in projects[:6]])

# ------------------------- Main App -----------------------------

def main():
    st.markdown(ADVANCED_CSS, unsafe_allow_html=True)
    
    # ========================= SIDEBAR =========================
    with st.sidebar:
        # Add a toggle button at the top of the sidebar
        if st.button("✕ Close" if st.session_state.sidebar_visible else "☰ Menu", key="sidebar_toggle_inside"):
            st.session_state.sidebar_visible = not st.session_state.sidebar_visible
            st.rerun()
        
        st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1.5rem; border-radius: 15px; text-align: center; margin-bottom: 1rem;">
                <h2 style="color: white; margin: 0;">👤 Your Profile</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # Profile Management Section
        with st.expander("💾 Save/Load Profile", expanded=False):
            st.markdown("**Profile Management**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Load Profile", use_container_width=True):
                    st.session_state.show_load = True
            with col2:
                if st.button("💾 Save Profile", use_container_width=True):
                    st.session_state.show_save = True
            
            if st.session_state.get('show_load', False):
                uploaded_file = st.file_uploader("Upload Profile JSON", type=['json'])
                if uploaded_file:
                    profile_data = json.load(uploaded_file)
                    st.session_state.student_profile = profile_data
                    st.success("✅ Profile loaded successfully!")
                    st.session_state.show_load = False
                    st.rerun()
            
            if st.session_state.get('show_save', False):
                profile_json = save_profile_to_json(st.session_state.get('student_profile', {}))
                st.download_button(
                    label="⬇️ Download Profile",
                    data=profile_json,
                    file_name="my_profile.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        # Progress Tracker
        profile_data = st.session_state.get('student_profile', {})
        completeness = calculate_profile_completeness(profile_data)
        st.session_state.profile_completeness = completeness
        
        st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span style="color: white;">Profile Completion</span>
                    <span style="color: #10b981; font-weight: bold;">{completeness}%</span>
                </div>
                <div style="background: rgba(255,255,255,0.1); height: 10px; border-radius: 5px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #10b981, #34d399); 
                                width: {completeness}%; height: 100%; transition: width 0.3s ease;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # === BASIC INFORMATION ===
        with st.expander("📋 Basic Information", expanded=True):
            st.markdown("**Essential Details** *")
            
            full_name = st.text_input(
                "Full Name *", 
                value=profile_data.get('name', ''),
                placeholder="e.g., Alex Johnson",
                help="Your full legal name"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input(
                    "Email *", 
                    value=profile_data.get('email', ''),
                    placeholder="alex@email.com"
                )
            with col2:
                phone = st.text_input(
                    "Phone *", 
                    value=profile_data.get('phone', ''),
                    placeholder="+1 (555) 123-4567"
                )
            
            location = st.text_input(
                "Location", 
                value=profile_data.get('location', ''),
                placeholder="San Francisco, CA"
            )
            
            st.markdown("**Headline/Title**")
            headline = st.text_input(
                "Professional Headline",
                value=profile_data.get('headline', ''),
                placeholder="Software Engineer | AI Enthusiast | Open Source Contributor",
                help="A catchy one-liner that describes you"
            )
        
        # === EDUCATION ===
        with st.expander("🎓 Education", expanded=True):
            st.markdown("**Academic Background**")
            
            num_education = st.number_input(
                "Number of Degrees/Programs",
                min_value=1,
                max_value=5,
                value=len(profile_data.get('education_list', [{}])),
                help="Add multiple degrees if applicable"
            )
            
            education_list = []
            for i in range(num_education):
                st.markdown(f"**Degree {i+1}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    degree = st.text_input(
                        "Degree Type",
                        value="B.S. Computer Science" if i == 0 else "",
                        key=f"degree_{i}",
                        placeholder="e.g., B.S., M.S., Ph.D."
                    )
                with col2:
                    major = st.text_input(
                        "Major/Field",
                        value="Computer Science" if i == 0 else "",
                        key=f"major_{i}",
                        placeholder="Your field of study"
                    )
                
                col3, col4 = st.columns(2)
                with col3:
                    university = st.text_input(
                        "University",
                        value="Stanford University" if i == 0 else "",
                        key=f"uni_{i}",
                        placeholder="University name"
                    )
                with col4:
                    grad_year = st.text_input(
                        "Graduation Year",
                        value="2024" if i == 0 else "",
                        key=f"grad_{i}",
                        placeholder="Expected: 2024"
                    )
                
                col5, col6 = st.columns(2)
                with col5:
                    gpa = st.text_input(
                        "GPA (Optional)",
                        value="3.8/4.0" if i == 0 else "",
                        key=f"gpa_{i}",
                        placeholder="3.8/4.0"
                    )
                with col6:
                    honors = st.text_input(
                        "Honors",
                        value="" if i == 0 else "",
                        key=f"honors_{i}",
                        placeholder="Cum Laude, Dean's List"
                    )
                
                coursework = st.text_area(
                    "Relevant Coursework",
                    value="Machine Learning, Data Structures, Algorithms" if i == 0 else "",
                    key=f"course_{i}",
                    height=60,
                    placeholder="Comma-separated courses"
                )
                
                education_list.append({
                    'degree': degree,
                    'major': major,
                    'university': university,
                    'grad_year': grad_year,
                    'gpa': gpa,
                    'honors': honors,
                    'coursework': coursework
                })
                
                if i < num_education - 1:
                    st.markdown("---")
        
        # === CAREER GOALS ===
        with st.expander("💼 Career Goals & Target", expanded=True):
            st.markdown("**What are you aiming for?**")
            
            col1, col2 = st.columns(2)
            with col1:
                target_role = st.text_input(
                    "Target Role *",
                    value=profile_data.get('target_role', 'Software Engineer'),
                    placeholder="e.g., Data Scientist"
                )
            with col2:
                target_industry = st.selectbox(
                    "Target Industry",
                    ["Technology", "Finance", "Healthcare", "Education", "Marketing", 
                     "Consulting", "Manufacturing", "Entertainment", "Retail", "Other"],
                    index=0
                )
            
            target_company = st.text_input(
                "Dream Companies (comma-separated)",
                value=profile_data.get('target_companies', 'Google, Microsoft, Apple'),
                placeholder="Google, Microsoft, Startup XYZ"
            )
            
            experience_level = st.select_slider(
                "Experience Level",
                options=["Entry Level", "1-2 Years", "3-5 Years", "5-10 Years", "10+ Years"],
                value=profile_data.get('experience_level', "Entry Level")
            )
            
            job_type = st.multiselect(
                "Job Type Preference",
                ["Full-time", "Part-time", "Contract", "Internship", "Freelance"],
                default=["Full-time"]
            )
            
            work_arrangement = st.multiselect(
                "Work Arrangement",
                ["Remote", "Hybrid", "On-site"],
                default=["Remote", "Hybrid"]
            )
            
            salary_expectation = st.text_input(
                "Salary Expectation (Optional)",
                placeholder="$80,000 - $100,000",
                help="Your expected salary range"
            )
        
        # === SKILLS ===
        with st.expander("⚡ Skills & Expertise", expanded=True):
            st.markdown("**Your Skillset**")
            
            # Skill Templates
            skill_template = st.selectbox(
                "Quick Fill Template",
                ["Custom", "Software Engineer", "Data Scientist", "Product Manager", 
                 "UI/UX Designer", "Marketing Specialist"],
                help="Auto-fill common skills for your role"
            )
            
            skill_templates = {
                "Software Engineer": {
                    "technical": "Python, JavaScript, React, Node.js, SQL, Git, Docker, AWS, REST APIs, MongoDB",
                    "soft": "Problem Solving, Team Collaboration, Agile Development, Code Review, Communication"
                },
                "Data Scientist": {
                    "technical": "Python, R, TensorFlow, PyTorch, Pandas, NumPy, Scikit-learn, SQL, Tableau, Jupyter",
                    "soft": "Statistical Analysis, Data Visualization, Research, Communication, Critical Thinking"
                },
                "Product Manager": {
                    "technical": "SQL, Google Analytics, JIRA, Figma, A/B Testing, Excel, Product Roadmapping",
                    "soft": "Leadership, Stakeholder Management, Strategic Thinking, Communication, Prioritization"
                },
                "UI/UX Designer": {
                    "technical": "Figma, Adobe XD, Sketch, Photoshop, Illustrator, HTML/CSS, Prototyping, User Research",
                    "soft": "Creativity, Empathy, Communication, Collaboration, Attention to Detail"
                },
                "Marketing Specialist": {
                    "technical": "SEO, Google Ads, Facebook Ads, Google Analytics, HubSpot, Mailchimp, Content Marketing",
                    "soft": "Creativity, Analytical Thinking, Communication, Project Management, Adaptability"
                }
            }
            
            default_technical = ""
            default_soft = ""
            if skill_template != "Custom" and skill_template in skill_templates:
                default_technical = skill_templates[skill_template]["technical"]
                default_soft = skill_templates[skill_template]["soft"]
            
            technical_skills = st.text_area(
                "Technical Skills *",
                value=profile_data.get('technical_skills', default_technical),
                height=100,
                placeholder="Python, JavaScript, React, SQL, AWS, Docker...",
                help="Technologies, tools, programming languages"
            )
            
            soft_skills = st.text_area(
                "Soft Skills",
                value=profile_data.get('soft_skills', default_soft),
                height=80,
                placeholder="Leadership, Communication, Problem Solving...",
                help="Interpersonal and professional skills"
            )
            
            languages = st.text_input(
                "Languages",
                value=profile_data.get('languages', 'English (Native)'),
                placeholder="English (Native), Spanish (Intermediate)"
            )
            
            # Skill Proficiency Levels
            st.markdown("**Skill Proficiency (Optional)**")
            show_proficiency = st.checkbox("Add proficiency levels", value=False)
            
            skill_proficiency = {}
            if show_proficiency:
                top_skills = [s.strip() for s in technical_skills.split(',')[:5]]
                for skill in top_skills:
                    if skill:
                        level = st.select_slider(
                            skill,
                            options=["Beginner", "Intermediate", "Advanced", "Expert"],
                            value="Intermediate",
                            key=f"prof_{skill}"
                        )
                        skill_proficiency[skill] = level
        
        # === WORK EXPERIENCE ===
        with st.expander("💼 Work Experience", expanded=True):
            st.markdown("**Professional Experience**")
            
            num_exp = st.number_input(
                "Number of Experiences",
                min_value=0,
                max_value=10,
                value=1,
                help="Include internships, full-time jobs, freelance work"
            )
            
            experiences = []
            for i in range(num_exp):
                st.markdown(f"**Experience {i+1}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    job_title = st.text_input(
                        "Job Title",
                        value="Software Engineering Intern" if i == 0 else "",
                        key=f"jt_{i}",
                        placeholder="e.g., Software Engineer"
                    )
                with col2:
                    company = st.text_input(
                        "Company",
                        value="TechCorp Inc." if i == 0 else "",
                        key=f"co_{i}",
                        placeholder="Company name"
                    )
                
                col3, col4 = st.columns(2)
                with col3:
                    start_date = st.text_input(
                        "Start Date",
                        value="Jun 2023" if i == 0 else "",
                        key=f"sd_{i}",
                        placeholder="MMM YYYY"
                    )
                with col4:
                    end_date = st.text_input(
                        "End Date",
                        value="Aug 2023" if i == 0 else "",
                        key=f"ed_{i}",
                        placeholder="Present or MMM YYYY"
                    )
                
                job_location = st.text_input(
                    "Location",
                    value="" if i == 0 else "",
                    key=f"jl_{i}",
                    placeholder="San Francisco, CA or Remote"
                )
                
                # Achievement template
                achievement_template = st.selectbox(
                    "Use Achievement Template",
                    ["Custom", "Increased Performance", "Led Team/Project", "Built Feature", 
                     "Reduced Cost", "Improved Process"],
                    key=f"at_{i}"
                )
                
                achievement_examples = {
                    "Increased Performance": "• Optimized API response time by 40%, improving user experience for 10,000+ daily users\n• Increased system throughput by 60% through code optimization",
                    "Led Team/Project": "• Led cross-functional team of 5 to deliver project 2 weeks ahead of schedule\n• Managed end-to-end development of feature used by 50,000+ users",
                    "Built Feature": "• Built RESTful API serving 10,000+ requests/day with 99.9% uptime\n• Developed full-stack feature increasing user engagement by 25%",
                    "Reduced Cost": "• Reduced server costs by $50K annually through infrastructure optimization\n• Decreased bug rate by 35% through implementing automated testing",
                    "Improved Process": "• Streamlined deployment process, reducing release time from 2 hours to 15 minutes\n• Improved code review efficiency by 40% through implementing new tools"
                }
                
                default_achievements = ""
                if achievement_template != "Custom":
                    default_achievements = achievement_examples.get(achievement_template, "")
                
                desc = st.text_area(
                    "Key Achievements & Responsibilities",
                    value=default_achievements if i == 0 and achievement_template != "Custom" else "• Built RESTful API serving 10,000+ requests/day\n• Reduced load time by 40% through optimization\n• Collaborated with cross-functional team of 8" if i == 0 else "",
                    height=150,
                    key=f"de_{i}",
                    placeholder="• Start each point with action verb\n• Include metrics and impact\n• Focus on achievements, not just duties",
                    help="Use bullet points. Include metrics!"
                )
                
                experiences.append({
                    'title': job_title,
                    'company': company,
                    'start_date': start_date,
                    'end_date': end_date,
                    'location': job_location,
                    'description': desc
                })
                
                if i < num_exp - 1:
                    st.markdown("---")
        
        # === PROJECTS ===
        with st.expander("🚀 Projects", expanded=True):
            st.markdown("**Personal & Academic Projects**")
            
            num_proj = st.number_input(
                "Number of Projects",
                min_value=0,
                max_value=15,
                value=2,
                help="Showcase your best work"
            )
            
            projects = []
            for i in range(num_proj):
                st.markdown(f"**Project {i+1}**")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    name = st.text_input(
                        "Project Name",
                        value="AI Chatbot Platform" if i == 0 else "E-commerce Dashboard" if i == 1 else "",
                        key=f"pn_{i}",
                        placeholder="Give it a catchy name"
                    )
                with col2:
                    proj_type = st.selectbox(
                        "Type",
                        ["Personal", "Academic", "Freelance", "Open Source", "Hackathon"],
                        key=f"pty_{i}"
                    )
                
                desc = st.text_area(
                    "Description & Impact",
                    value="Built intelligent chatbot using NLP and transformers, handling 1000+ conversations daily with 95% accuracy" if i == 0 else "Developed real-time analytics dashboard processing 100K+ transactions, reducing report generation time by 70%" if i == 1 else "",
                    height=80,
                    key=f"pd_{i}",
                    placeholder="What did you build? What problem did it solve? What was the impact?"
                )
                
                tech = st.text_input(
                    "Tech Stack",
                    value="Python, TensorFlow, React, MongoDB" if i == 0 else "React, Node.js, PostgreSQL, Docker" if i == 1 else "",
                    key=f"pt_{i}",
                    placeholder="Technologies used (comma-separated)"
                )
                
                col3, col4 = st.columns(2)
                with col3:
                    link = st.text_input(
                        "GitHub/Live Link",
                        value="" if i == 0 else "",
                        key=f"pl_{i}",
                        placeholder="github.com/username/project"
                    )
                with col4:
                    demo_link = st.text_input(
                        "Demo Link (Optional)",
                        value="",
                        key=f"pdl_{i}",
                        placeholder="youtube.com/demo"
                    )
                
                highlights = st.text_area(
                    "Key Highlights (Optional)",
                    value="",
                    height=60,
                    key=f"ph_{i}",
                    placeholder="• 500+ GitHub stars\n• Featured in TechCrunch\n• Won Best Project Award"
                )
                
                projects.append({
                    'name': name,
                    'type': proj_type,
                    'description': desc,
                    'tech': tech,
                    'link': link,
                    'demo': demo_link,
                    'highlights': highlights
                })
                
                if i < num_proj - 1:
                    st.markdown("---")
        
        # === CERTIFICATIONS & ACHIEVEMENTS ===
        with st.expander("🏆 Certifications & Achievements"):
            st.markdown("**Professional Credentials**")
            
            num_certs = st.number_input(
                "Number of Certifications",
                min_value=0,
                max_value=10,
                value=0
            )
            
            certifications_list = []
            for i in range(num_certs):
                col1, col2 = st.columns([2, 1])
                with col1:
                    cert_name = st.text_input(
                        "Certification",
                        key=f"cert_{i}",
                        placeholder="AWS Certified Developer"
                    )
                with col2:
                    cert_year = st.text_input(
                        "Year",
                        key=f"certyear_{i}",
                        placeholder="2024"
                    )
                certifications_list.append(f"{cert_name} ({cert_year})" if cert_year else cert_name)
            
            st.markdown("**Awards & Honors**")
            achievements = st.text_area(
                "Notable Achievements",
                value=profile_data.get('achievements', ''),
                height=100,
                placeholder="• 1st Place - University Hackathon 2023\n• Dean's List (All Semesters)\n• Published research paper on AI ethics\n• President of Computer Science Club"
            )
            
            st.markdown("**Publications (Optional)**")
            publications = st.text_area(
                "Research Papers/Articles",
                value="",
                height=60,
                placeholder="• 'Machine Learning for Climate Change' - IEEE Conference 2023"
            )
        
        # === EXTRACURRICULAR ===
        with st.expander("🎯 Extracurricular & Volunteer"):
            st.markdown("**Beyond Academics**")
            
            leadership = st.text_area(
                "Leadership Experience",
                value="",
                height=80,
                placeholder="• President of Coding Club (2022-2024)\n• Organized 5 workshops with 200+ attendees"
            )
            
            volunteer = st.text_area(
                "Volunteer Work",
                value="",
                height=80,
                placeholder="• Code.org Volunteer (100+ hours)\n• Mentored 20+ high school students in programming"
            )
            
            hobbies = st.text_input(
                "Hobbies & Interests",
                value="",
                placeholder="Photography, Hiking, Chess, Reading Sci-Fi"
            )
        
        # === SOCIAL LINKS ===
        with st.expander("🔗 Social & Portfolio Links"):
            st.markdown("**Online Presence**")
            
            col1, col2 = st.columns(2)
            with col1:
                linkedin = st.text_input(
                    "LinkedIn",
                    value=profile_data.get('linkedin', 'linkedin.com/in/username'),
                    placeholder="linkedin.com/in/username"
                )
                github = st.text_input(
                    "GitHub",
                    value=profile_data.get('github', 'github.com/username'),
                    placeholder="github.com/username"
                )
            with col2:
                portfolio = st.text_input(
                    "Portfolio Website",
                    value="",
                    placeholder="yourname.com"
                )
                twitter = st.text_input(
                    "Twitter/X",
                    value="",
                    placeholder="twitter.com/username"
                )
            
            other_links = st.text_area(
                "Other Links",
                value="",
                height=60,
                placeholder="Medium: medium.com/@username\nDribbble: dribbble.com/username"
            )
        
        # === PREFERENCES ===
        with st.expander("🎨 Resume Preferences"):
            st.markdown("**Customization**")
            
            tone = st.selectbox(
                "Writing Tone",
                ["Professional", "Creative", "Technical", "Startup", "Academic", "Executive"],
                help="How should your resume sound?"
            )
            
            resume_length = st.select_slider(
                "Resume Length",
                options=["Concise (1 page)", "Standard (1-2 pages)", "Detailed (2 pages)"],
                value="Standard (1-2 pages)"
            )
            
            include_photo = st.checkbox("Include Photo Space", value=False)
            include_summary = st.checkbox("Include Professional Summary", value=True)
            include_references = st.checkbox("Include 'References Available Upon Request'", value=False)
        
        # Save profile to session state
        st.session_state.student_profile = {
            'name': full_name,
            'email': email,
            'phone': phone,
            'location': location,
            'headline': headline,
            'education_list': education_list,
            'target_role': target_role,
            'target_industry': target_industry,
            'target_companies': target_company,
            'experience_level': experience_level,
            'technical_skills': technical_skills,
            'soft_skills': soft_skills,
            'languages': languages,
            'experiences': experiences,
            'projects': projects,
            'certifications': '\n'.join([c for c in certifications_list if c]),
            'achievements': achievements,
            'linkedin': linkedin,
            'github': github,
            'tone': tone
        }
    
    # ========================= MAIN CONTENT =========================
    
    # Sidebar toggle button in main content (only when sidebar is hidden)
    if not st.session_state.sidebar_visible:
        col_toggle, col_spacer = st.columns([1, 10])
        with col_toggle:
            if st.button("☰ Menu", key="sidebar_toggle_main"):
                st.session_state.sidebar_visible = True
                st.rerun()
    
    # Header
    st.markdown("""
        <div class="hero-header">
            <h1>🎓 AI Career Builder Pro</h1>
            <p class="subtitle">Land Your Dream Job with AI-Powered Tools</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards
    st.markdown("""
        <div class="feature-grid">
            <div class="feature-card">
                <span class="icon">📄</span>
                <h3>Smart Resumes</h3>
                <p>8 professional templates with PDF export</p>
            </div>
            <div class="feature-card">
                <span class="icon">💌</span>
                <h3>Cover Letters</h3>
                <p>Personalized and compelling</p>
            </div>
            <div class="feature-card">
                <span class="icon">🌐</span>
                <h3>Portfolio Sites</h3>
                <p>Theme-switchable websites</p>
            </div>
            <div class="feature-card">
                <span class="icon">🎯</span>
                <h3>Career Guidance</h3>
                <p>AI-powered career advisor</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # ========================= COMPILE CANDIDATE DATA =========================
    
    # Compile experience and projects for resume generation
    exp_text = "\n\n".join([
        f"**{e['title']}** at {e['company']} ({e['start_date']} - {e['end_date']})\n{e.get('location', '')}\n{e['description']}" 
        for e in experiences if e.get('title')
    ]) if experiences else "No work experience yet"
    
    proj_text = "\n\n".join([
        f"**{p['name']}** ({p.get('type', 'Personal')}): {p['description']}\nTech Stack: {p['tech']}\nLink: {p.get('link', 'N/A')}" 
        for p in projects if p.get('name')
    ]) if projects else "No projects listed"
    
    # Get candidate data from session state
    candidate_data = st.session_state.student_profile.copy()
    
    # Add compiled data
    candidate_data['work_experience'] = exp_text
    candidate_data['projects'] = proj_text
    
    # Handle education data
    if education_list and education_list[0].get('degree'):
        candidate_data['education'] = f"{education_list[0]['degree']} in {education_list[0].get('major', 'N/A')} from {education_list[0].get('university', 'N/A')}"
        candidate_data['gpa'] = education_list[0].get('gpa', '')
        candidate_data['coursework'] = education_list[0].get('coursework', '')
    else:
        candidate_data['education'] = ""
        candidate_data['gpa'] = ""
        candidate_data['coursework'] = ""
    
    # ========================= MAIN TABS =========================
    
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Resume Generator", "💌 Cover Letter", "🌐 Portfolio Website", "🎯 Career Advisor"])
    
    # TAB 1: Resume Generator
    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### ✨ AI Resume Generator")
        
        st.markdown("#### 📋 Choose Your Template")
        st.markdown("Select a template that best fits your industry and experience level:")
        
        # Display templates in a grid
        cols = st.columns(2)
        for idx, (template_name, template_info) in enumerate(RESUME_TEMPLATES.items()):
            with cols[idx % 2]:
                is_selected = st.session_state.selected_template == template_name
                
                if st.button(
                    f"{'✓ ' if is_selected else ''}{template_name}",
                    key=f"template_{template_name}",
                    use_container_width=True
                ):
                    st.session_state.selected_template = template_name
                    st.rerun()
                
                card_class = "template-card selected" if is_selected else "template-card"
                st.markdown(f"""
                    <div class="{card_class}">
                        <h4>{template_name}</h4>
                        <span class="template-badge">{template_info['badge']}</span>
                        <p>{template_info['description']}</p>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown(f"**Currently Selected:** {st.session_state.selected_template}")
        
        st.markdown("---")
        
        if st.button("🚀 Generate My Resume", use_container_width=True, key="gen_resume_btn"):
            if not full_name or not email:
                st.markdown('<div class="alert-warning">⚠️ Please fill in at least your name and email in the sidebar</div>', unsafe_allow_html=True)
            else:
                progress_bar = st.progress(0)
                status = st.empty()
                
                status.markdown('<div class="alert-info">📝 Analyzing your profile...</div>', unsafe_allow_html=True)
                progress_bar.progress(20)
                
                status.markdown(f'<div class="alert-info">🤖 Generating your {st.session_state.selected_template} resume...</div>', unsafe_allow_html=True)
                progress_bar.progress(50)
                
                # Generate resume
                prompt = generate_resume_prompt(st.session_state.selected_template, candidate_data)
                resume_content = call_gemini_with_retry(prompt, max_tokens=3500)
                
                progress_bar.progress(80)
                status.markdown('<div class="alert-info">📄 Formatting your resume...</div>', unsafe_allow_html=True)
                
                progress_bar.progress(100)
                time.sleep(0.5)
                status.empty()
                progress_bar.empty()
                
                if resume_content and not resume_content.startswith("⚠️"):
                    st.markdown(f'<div class="alert-success">✅ Your {st.session_state.selected_template} resume is ready!</div>', unsafe_allow_html=True)
                    
                    # Display resume
                    st.markdown("---")
                    st.markdown(resume_content)
                    st.markdown("---")
                    
                    # Download options
                    st.markdown("### 📥 Download Your Resume")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        try:
                            pdf_bytes = create_professional_pdf(resume_content, full_name)
                            st.markdown(
                                download_link_bytes(pdf_bytes, f"{full_name.replace(' ', '_')}_Resume.pdf", "application/pdf"),
                                unsafe_allow_html=True
                            )
                        except Exception as e:
                            st.error(f"PDF Error: {str(e)}")
                            st.info("You can still download as Markdown")
                    
                    with col2:
                        st.markdown(
                            download_link_bytes(resume_content.encode('utf-8'), f"{full_name.replace(' ', '_')}_Resume.md", "text/markdown"),
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown(f'<div class="alert-error">{resume_content}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # TAB 2: Cover Letter
    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 💌 AI Cover Letter Writer")
        
        st.markdown("Create a compelling cover letter tailored to the specific role and company.")
        
        col1, col2 = st.columns(2)
        with col1:
            why_role = st.text_area(
                "Why are you interested in this role? 🎯",
                "I'm passionate about building scalable systems and this role offers the perfect opportunity to work with cutting-edge technologies...",
                height=120
            )
        with col2:
            why_company = st.text_area(
                "Why this company specifically? 💼",
                "I admire their commitment to innovation and their impact on millions of users worldwide. I'm particularly excited about...",
                height=120
            )
        
        achievement = st.text_area(
            "Highlight ONE key achievement 🏆",
            "During my internship at TechCorp, I optimized the API response time by 40%, reducing server costs by $50K annually and improving user experience for 10,000+ daily users.",
            height=100
        )
        
        if st.button("✍️ Generate Cover Letter", use_container_width=True):
            if not full_name:
                st.warning("Please fill in your profile information in the sidebar")
            else:
                with st.spinner("📝 Writing your personalized cover letter..."):
                    current_date = datetime.now().strftime("%B %d, %Y")
                    
                    prompt = MASTER_COVER_LETTER_PROMPT.format(
                        name=full_name,
                        email=email,
                        phone=phone,
                        linkedin=linkedin,
                        role=target_role,
                        company=target_company,
                        education=candidate_data.get('education', 'N/A'),
                        skills=technical_skills,
                        why_role=why_role,
                        why_company=why_company,
                        achievement=achievement,
                        tone=tone,
                        current_date=current_date
                    )
                    
                    cover_letter = call_gemini_with_retry(prompt, max_tokens=2000)
                    
                    if cover_letter and not cover_letter.startswith("⚠️"):
                        st.markdown('<div class="alert-success">✅ Your cover letter is ready!</div>', unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.markdown(cover_letter)
                        st.markdown("---")
                        
                        st.markdown("### 📥 Download Your Cover Letter")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            try:
                                pdf_bytes = create_professional_pdf(cover_letter, full_name, "cover_letter")
                                st.markdown(
                                    download_link_bytes(pdf_bytes, f"{full_name.replace(' ', '_')}_CoverLetter.pdf", "application/pdf"),
                                    unsafe_allow_html=True
                                )
                            except:
                                pass
                        
                        with col2:
                            st.markdown(
                                download_link_bytes(cover_letter.encode('utf-8'), f"{full_name.replace(' ', '_')}_CoverLetter.md", "text/markdown"),
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(f'<div class="alert-error">{cover_letter}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # TAB 3: Portfolio Website
    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🌐 Advanced Portfolio Website Generator")
        
        st.markdown("Create a stunning, professional portfolio website with customizable themes and animations.")
        
        st.markdown("#### 🎨 Design Customization")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Color Scheme**")
            color_preset = st.selectbox("Color Preset", list(COLOR_PRESETS.keys()))
            colors = COLOR_PRESETS[color_preset]
            primary_color = st.color_picker("Primary Color", colors["primary"])
            secondary_color = st.color_picker("Secondary Color", colors["secondary"])
            accent_color = st.color_picker("Accent Color", colors["accent"])
        
        with col2:
            st.markdown("**Typography**")
            font_choice = st.selectbox("Font Family", list(FONT_PRESETS.keys()))
            hero_title_size = st.slider("Hero Title Size (rem)", 4, 8, 6)
            logo_size = st.slider("Logo Size (rem)", 1.0, 2.5, 1.5, 0.1)
        
        with col3:
            st.markdown("**Layout**")
            hero_align = st.selectbox("Hero Alignment", ["center", "left"])
            about_layout = st.selectbox("About Layout", ["1fr 1fr", "1fr", "2fr 1fr"])
            card_radius = st.slider("Card Border Radius (px)", 10, 30, 20)
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            st.markdown("**🌓 Theme Mode**")
            theme_mode = st.radio(
                "Portfolio Theme",
                ["Dark", "Light", "Toggle (User Choice)"],
                help="Toggle allows visitors to switch between dark and light themes"
            )
        
        with col5:
            st.markdown("**Effects**")
            show_particles = st.checkbox("Particle Background", True)
            show_nav = st.checkbox("Show Navigation", True)
            nav_opacity = st.slider("Nav Opacity", 0.5, 1.0, 0.8, 0.1)
        
        with col6:
            st.markdown("**Animation**")
            hover_effect = st.slider("Hover Lift (px)", -20, -5, -10, 1)
            button_radius = st.slider("Button Radius (px)", 10, 50, 50)

            animation_speed = st.slider("Animation Speed", 0.5, 3.0, 1.5, 0.1)

            st.markdown("**Interactive Elements**")
            enable_parallax = st.checkbox("Parallax Scrolling", True)
            enable_morphing = st.checkbox("Morphing Shapes on Hover", False)
            enable_3d_cards = st.checkbox("3D Card Effects", True)
            enable_cursor_follow = st.checkbox("Cursor-Following Effects", False)
        col7, col8 = st.columns(2)
        with col7:
            show_about = st.checkbox("Show About Section", True)
            show_stats = st.checkbox("Show Stats Cards", True)
        with col8:
            greeting_text = st.text_input("Greeting Text", "👋 Hello, I'm")

        
        st.markdown("#### 🎨 Choose Portfolio Template")

        template_cols = st.columns(2)
        for idx, (template_name, template_info) in enumerate(PORTFOLIO_TEMPLATES.items()):
            with template_cols[idx % 2]:
                if st.button(f"Select {template_name}", key=f"template_{template_name}"):
                    st.session_state.selected_portfolio_template = template_name
                
                st.markdown(f"""
                <div class="template-card {'selected' if st.session_state.get('selected_portfolio_template') == template_name else ''}">
                    <h4>{template_name}</h4>
                    <p>{template_info['description']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("#### ✍️ Content")
        tagline = st.text_input("Portfolio Tagline", f"{target_role} | Building innovative solutions")
        about_portfolio = st.text_area("About Section", f"Passionate {target_role} with expertise in {technical_skills.split(',')[0] if technical_skills else 'technology'}. I love building products that make a difference.", height=100)
        
        
        if st.button("🚀 Build My Portfolio", use_container_width=True):
            with st.spinner("🎨 Designing your portfolio website..."):
                # Get selected template
                selected_template = st.session_state.get('selected_portfolio_template', 'Modern Minimal')
                
                # Build skills HTML
                skills_categories = {
                    "Technical Skills": technical_skills.split(',')[:8],
                    "Soft Skills": soft_skills.split(',')[:5]
                }
                
                skills_html = ""
                for category, skills_list in skills_categories.items():
                    tags = "".join([f'<span class="skill-tag">{s.strip()}</span>' for s in skills_list if s.strip()])
                    skills_html += f'<div class="skill-card"><h3>{category}</h3><div class="skill-tags">{tags}</div></div>'
                
                # Build projects HTML
                projects_html = ""
                for proj in projects[:6]:
                    tech_badges = "".join([f'<span class="tech-badge">{t.strip()}</span>' for t in proj.get('tech', '').split(',') if t.strip()])
                    projects_html += f'''
                    <div class="project-card">
                        <div class="project-image">💡</div>
                        <div class="project-content">
                            <h3>{proj.get('name', 'Project')}</h3>
                            <p>{proj.get('description', '')}</p>
                            <div class="project-tech">{tech_badges}</div>
                        </div>
                    </div>
                    '''
                
                # Social links
                social_links_html = f'''
                    <a href="https://{github}" target="_blank" title="GitHub">🐙</a>
                    <a href="https://{linkedin}" target="_blank" title="LinkedIn">💼</a>
                    <a href="mailto:{email}" title="Email">📧</a>
                '''
                
                # Particles script
                particles_script = generate_particles_script(primary_color) if show_particles else ""
                
                # Portfolio config
                config = {
                    'name': full_name,
                    'tagline': tagline,
                    'about': about_portfolio,
                    'email': email,
                    'skills_html': skills_html,
                    'projects_html': projects_html,
                    'social_links_html': social_links_html,
                    'primary_color': primary_color,
                    'secondary_color': secondary_color,
                    'accent_color': accent_color,
                    'font_family': FONT_PRESETS[font_choice],
                    'hero_title_size': hero_title_size,
                    'logo_size': logo_size,
                    'hero_align': hero_align,
                    'about_layout': about_layout,
                    'card_radius': card_radius,
                    'hover_effect': hover_effect,
                    'button_radius': button_radius,
                    'nav_opacity': nav_opacity,
                    'show_nav': show_nav,
                    'show_particles': show_particles,
                    'show_about': show_about,
                    'show_stats': show_stats,
                    'greeting_text': greeting_text,
                    'particles_script': particles_script,
                    'num_projects': len(projects),
                    'num_skills': len(technical_skills.split(',')),
                    'years_exp': experience_level.split()[0] if experience_level.split()[0].isdigit() else "1",
                    'theme_mode': theme_mode,
                    'template': selected_template
                }
                
                html_content = generate_portfolio_html(config)
                
                st.markdown("### 🎨 Live Preview")
                st.components.v1.html(html_content, height=800, scrolling=True)
                
                # Show theme info
                if theme_mode == "Toggle (User Choice)":
                    st.markdown("""
                        <div class="alert-info">
                            💡 <strong>Theme Toggle Enabled!</strong><br>
                            Visitors can switch between dark/light mode using the ☀️/🌙 button in the top-right corner.
                            Their preference will be saved in browser storage.
                        </div>
                    """, unsafe_allow_html=True)
                
            

                
                # Create ZIP file
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    zf.writestr("index.html", html_content)
                    zf.writestr("README.md", f"""# {full_name}'s Portfolio

        ## 🌟 Features
        - 🌓 Theme: {theme_mode}
        - 🎨 Template: {selected_template}
        - 🎨 Responsive Design
        - ⚡ Fast Loading
        - 📱 Mobile Friendly
        - ✨ Smooth Animations

        ## 🚀 Deploy

        ### Option 1: Netlify (Easiest)
        1. Go to [netlify.com](https://netlify.com)
        2. Drag and drop this folder
        3. Your site is live!

        ### Option 2: Vercel
        1. Go to [vercel.com](https://vercel.com)
        2. Import from GitHub or upload files
        3. Deploy instantly

        ### Option 3: GitHub Pages
        1. Create a new repository
        2. Upload files
        3. Enable GitHub Pages in settings
        4. Your portfolio is live at username.github.io

        ## 📝 Customization
        Edit `index.html` to customize colors, content, and layout.

        Created with AI Career Builder Pro 🚀
        """)
                
                zip_buffer.seek(0)
                st.markdown(
                    download_link_bytes(zip_buffer.read(), "portfolio_website.zip", "application/zip"),
                    unsafe_allow_html=True
                )
                
                st.markdown("""
                    <div class="alert-success">
                        <strong>🎉 Your portfolio is ready!</strong><br>
                        Deploy to <a href="https://netlify.com" target="_blank" style="color: white; text-decoration: underline;">Netlify</a>, 
                        <a href="https://vercel.com" target="_blank" style="color: white; text-decoration: underline;">Vercel</a>, or 
                        <a href="https://pages.github.com" target="_blank" style="color: white; text-decoration: underline;">GitHub Pages</a>
                    </div>
                """, unsafe_allow_html=True)
        
       
    # TAB 4: Career Advisor
    with tab4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 AI Career Advisor")
        
        st.markdown("""
            <div class="alert-info">
                💡 Get personalized career advice, interview tips, skill roadmaps, and more from our AI advisor!
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 🚀 Quick Questions")
        col1, col2, col3 = st.columns(3)
        
        selected_quick = None
        with col1:
            if st.button("🎤 Interview Tips", use_container_width=True):
                selected_quick = f"Give me 5 specific interview tips for a {target_role} position, including common questions and how to answer them effectively."
        with col2:
            if st.button("📚 Learning Roadmap", use_container_width=True):
                selected_quick = f"Create a detailed 6-month learning roadmap to become a {target_role}. Include specific skills, resources, and milestones."
        with col3:
            if st.button("📝 Profile Review", use_container_width=True):
                selected_quick = "Review my profile and suggest 3-5 specific improvements to make me more competitive in the job market."
        
        question = st.text_area(
            "Ask anything about your career:",
            value=selected_quick if selected_quick else "",
            placeholder="Examples:\n- How do I negotiate salary?\n- What projects should I build to get hired?\n- How to switch careers into tech?\n- Resume tips for senior roles?",
            height=120
        )
        
        if st.button("🤖 Get AI Advice", use_container_width=True):
            if question.strip():
                with st.spinner("🧠 Analyzing your question and preparing personalized advice..."):
                    prompt = CAREER_ADVISOR_PROMPT.format(
                        name=full_name,
                        education=candidate_data.get('education', 'N/A'),
                        role=target_role,
                        experience_level=experience_level,
                        skills=technical_skills,
                        industry=target_industry,
                        question=question
                    )
                    
                    advice = call_gemini_with_retry(prompt, max_tokens=3000)
                    
                    if advice and not advice.startswith("⚠️"):
                        st.markdown('<div class="alert-success">💡 Here\'s your personalized advice:</div>', unsafe_allow_html=True)
                        st.markdown("---")
                        st.markdown(advice)
                        st.markdown("---")
                    else:
                        st.markdown(f'<div class="alert-error">{advice}</div>', unsafe_allow_html=True)
            else:
                st.warning("Please enter a question to get advice")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; color: rgba(255,255,255,0.5); padding: 2rem; border-top: 1px solid rgba(255,255,255,0.1);">
            <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">Made with ❤️ for students worldwide</p>
            <p style="font-size: 0.9rem;">Powered by Google Gemini AI • © 2025 AI Career Builder Pro</p>
            <p style="font-size: 0.85rem; margin-top: 0.5rem; color: rgba(255,255,255,0.3);">
                Helping students land their dream jobs one resume at a time 🚀
            </p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

