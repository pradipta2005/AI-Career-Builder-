# 🎓 **AI Career Builder Pro**
> 🚀 *Your Intelligent Career Companion — Build Professional Resumes, Cover Letters, and Portfolios with AI Precision*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Framework-Streamlit-red.svg)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-purple.svg)](https://ai.google.dev/)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Click%20Here-green.svg)](https://ai-career-builder.onrender.com/)
[![Deploy on Render](https://render.com/images/badge-deploy-on-render-blue.svg)](https://render.com/)

---

## 🧠 Overview
**AI Career Builder Pro** is a next-generation AI-powered platform that helps **students and professionals** build exceptional, tailored, and ATS-optimized career documents — including **resumes, cover letters, and portfolio websites** — with just a few clicks.

It’s not just another resume generator — it’s your **personal AI career assistant**, offering smart content creation, design customization, and career guidance powered by **Google Gemini AI**.

---

## ✨ **Key Features**
### 📄 **Smart Resume Generator**
- 🧩 **8 Tailored Templates:** Modern, ATS-Optimized, Creative, Technical, Executive, Academic, Minimalist, and Startup
- 🤖 **AI-Generated Content:** Auto-generated summaries, achievements, and bullet points using Google Gemini
- 📊 **Metrics & Achievements:** Highlights measurable impact in your experiences
- 🧾 **Export Options:** Download in beautifully formatted PDFs
- 🧠 **ATS-Friendly:** Optimized for recruitment systems

### 💌 **AI Cover Letter Creator**
- 🏢 **Company & Role Specific:** Personalized letters for each job
- 🧱 **STAR Framework:** Structured with Situation, Task, Action, and Result
- ✍️ **Custom Tone:** Choose between Professional, Creative, Academic, Technical, or Executive tones
- ⏱ **Word Count Control:** Ideal length (300–450 words)

### 🌐 **Portfolio Website Builder**
- 🎨 **4 Premium Templates:** Modern Minimal, Creative, Tech Pro, and Interactive Designer
- 🌗 **Custom Themes:** Choose light/dark modes & save preferences
- 🧩 **Interactive Animations:** Particle effects, parallax, 3D cards, morphing shapes
- 💻 **Responsive Design:** Mobile, tablet, and desktop optimized
- ⚡ **One-Click Deployment:** Ready for Netlify, Vercel, or GitHub Pages
- 📱 **Device Preview:** Preview how your site looks on multiple screens

### 🎯 **AI Career Advisor**
- 🧭 Personalized career suggestions based on user profile
- 💬 AI-powered interview preparation
- 📘 Learning roadmaps (6-month upskilling plans)
- 📚 Curated resource recommendations (courses, tools, books)
- ⚡ Quick “Ask AI” mode for instant answers

### 💾 **Profile Management**
- 💡 Save & load complete user profiles
- 📈 Progress tracking & visualization
- 🔄 Persistent data across sessions

---

## 🚀 **Live Demo**
Experience AI Career Builder Pro now:  
👉 **[ai-career-builder.onrender.com](https://ai-career-builder.onrender.com/)**

---

## 🧰 **Technology Stack**
| Category | Technology |
|-----------|-------------|
| 💻 Frontend | Streamlit |
| 🧠 AI Engine | Google Gemini API (`gemini-2.0-flash-exp`) |
| 🧾 PDF Generation | ReportLab |
| 🎨 Styling | Custom CSS with animations |
| ☁️ Deployment | Render |
| 🔗 Version Control | Git |

---

## ⚙️ **Installation & Setup**

### 🧩 **Prerequisites**
- Python **3.9+**
- A valid **Google Gemini API Key**
- Git installed on your system

### 🔧 **Steps**
#### 1️⃣ Clone Repository
```bash
git clone https://github.com/yourusername/ai-career-builder-pro.git
cd ai-career-builder-pro
```
#### 2️⃣ Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate      # For macOS/Linux
venv\Scripts\activate         # For Windows
```
#### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
#### 4️⃣ Add Environment Variables
Create a `.env` file in the project root and add:
```bash
GEMINI_API_KEY=your_google_gemini_api_key_here
```
To get your key:
1. Visit [Google AI Studio](https://ai.google.dev/)
2. Sign in → Create API Key → Copy it here.

#### 5️⃣ Run the App
```bash
streamlit run app.py
```
Now open your browser at **http://localhost:8501**

---

## 🧭 **Usage Guide**
### 🧾 Creating a Resume
1. Fill in personal, academic, and professional details  
2. Choose from **8 industry-ready templates**  
3. Let AI generate your resume content  
4. Review → Edit → Download PDF

### 🌐 Building a Portfolio
1. Choose your **theme** (color, font, layout)  
2. Add projects, skills, and social links  
3. Preview on different devices  
4. Deploy with one click on Netlify or Vercel

### 🎓 Career Guidance
- Ask AI for career advice  
- Get **personalized learning roadmaps**  
- Access curated resources instantly

---

## 🎨 **Customization Options**
| Category | Customizable Options |
|-----------|----------------------|
| 🎨 Color Schemes | `Purple Dream`, `Ocean Blue`, `Sunset Orange`, `Forest Green`, `Rose Gold`, `Cyber Purple` |
| 🖋️ Font Styles | Inter, Roboto, Poppins, Fira Code |
| 🧱 Templates | Modify in `RESUME_TEMPLATES` and `PORTFOLIO_TEMPLATES` |
| 🌀 Animations | Adjustable via CSS in `/static/style.css` |

---

## 🧩 **Environment Variables**
| Variable | Description | Required |
|-----------|-------------|-----------|
| `GEMINI_API_KEY` | Google Gemini API key | ✅ Yes |

---

## 📂 **Project Structure**
```
ai-career-builder-pro/
├── app.py                  # Main application logic
├── .env                    # Environment variables
├── requirements.txt        # Dependencies
├── README.md               # Documentation (this file)
├── assets/                 # Images, icons, and static files
└── templates/              # Template structures for resumes and portfolios
```

---

## 🙏 **Acknowledgments**
- 💡 **Google Gemini** – for powerful content generation  
- 🌐 **Streamlit** – for a seamless interactive UI  
- 🧾 **ReportLab** – for precise PDF rendering  
- 🎆 **Particles.js** – for aesthetic particle animations  
- ☁️ **Render** – for cloud deployment  

---

## 📞 **Support**
If you encounter any issues:
1. Check the **FAQ** section  
2. Search existing **Issues**  
3. Create a new issue including:
   - Description of the problem  
   - Steps to reproduce  
   - Screenshots (if applicable)  
   - Browser & environment details  

---

## 🪄 **Future Enhancements**
- AI-driven portfolio content generation  
- LinkedIn & GitHub integration  
- Career progress analytics dashboard  
- Multi-language resume support  

---

## 🧠 **License**
This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

---

## 🌟 **Show Your Support**
If you find **AI Career Builder Pro** helpful:  
⭐ Star this repo on GitHub & share it with others!
