# 🤖 AI Resume Screener

An end-to-end AI-powered resume screening system built with BERT semantic 
matching, ATS simulation, skill gap analysis, and role-based access control.

## 🔗 Live Demo
[Try it on Hugging Face →](YOUR_LINK_HERE)

## 🎯 What it does

### 👤 Job Seeker Portal
- Upload resume PDF + paste any job description
- Get overall match % using BERT semantic similarity
- Skill gap analysis — matched ✅ vs missing ❌ skills
- ATS Score Simulator — checks keyword density, metrics, verb strength
- Radar Chart — visual skill coverage across 5 ML domains
- Mock Interview Questions — personalised to your skill gaps

### 🏢 HR Recruiter Portal
- Upload multiple resumes at once
- Auto-ranks all candidates against a single JD
- Smart relative shortlisting — always finds best candidates even in weak pools
- Three-tier verdict: ✅ Shortlist | ⏳ Waitlist | ❌ Reject
- Pool quality warnings for weak applicant batches
- Export full report as CSV

## 🛠️ Tech Stack
| Layer | Technology |
|---|---|
| Semantic Matching | BERT (sentence-transformers) |
| Skill Analysis | Hybrid: keyword + cosine similarity |
| ATS Simulation | Custom rule-based scoring engine |
| Visualisation | Plotly radar charts |
| Frontend | Streamlit |
| Auth | SHA-256 hashed credentials (JSON store) |
| PDF Parsing | PyMuPDF |

## 🚀 Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/ai-resume-screener
cd ai-resume-screener
pip install -r requirements.txt
streamlit run app.py
```

## 📁 Project Structure
├── app.py                # Main app + login router
├── auth.py               # Role-based auth+   SHA-256 hashing
├── jobseeker_portal.py   # Job seeker features
├── hr_portal.py          # HR recruiter features
├── extract.py            # PDF text extraction
├── embedder.py           # BERT embedding engine
├── scorer.py             # Cosine similarity scorer
├── skill_analyzer.py     # Skill gap analyzer
└── requirements.txt

## 👩‍💻 Built by
Newshika S K — B.Tech AI & Data Science, Kumaraguru College of Technology