import streamlit as st
from datetime import datetime
import time

from utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    load_job_descriptions,
    load_skills,
    extract_skills,
    compute_match_score,
    get_missing_skills,
    get_required_skills_from_jd,
    categorize_skills,
    compute_skill_coverage,
)

st.set_page_config(page_title="AI Resume Screener", page_icon="📄", layout="wide")


# ----------------------------
# Helper Functions
# ----------------------------

def get_confidence_label(score, coverage):
    """
    Confidence is based on BOTH:
    - semantic match score
    - skill coverage %
    """
    if score >= 75 and coverage >= 65:
        return "High ✅"
    elif score >= 55 and coverage >= 40:
        return "Medium ⚠️"
    else:
        return "Low ❌"


def generate_report(role, score, coverage, found_skills, required_skills, missing_skills):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""
AI RESUME SCREENER REPORT
Generated on: {now}

Model Used: Sentence-BERT (all-MiniLM-L6-v2)
Job Role: {role}

-----------------------------------------
Overall Match Score: {score}%
Skill Coverage: {coverage}%

-----------------------------------------
Required Skills (from JD):
{', '.join(required_skills) if required_skills else 'None'}

-----------------------------------------
Matched Skills:
{', '.join(found_skills) if found_skills else 'None'}

-----------------------------------------
Missing Skills:
{', '.join(missing_skills) if missing_skills else 'None'}

-----------------------------------------
Suggestions:
"""

    if missing_skills:
        report += f"Priority skills to learn: {', '.join(missing_skills[:8])}\n"
    else:
        report += "Great match! Add measurable achievements and strong projects.\n"

    return report.strip()


# ----------------------------
# UI Header
# ----------------------------

st.title("📄 AI Resume Screener ")
st.caption("🚀 Semantic Matching enabled using **Sentence-BERT Embeddings**")

st.markdown(
    """
<div style="padding:12px;border-radius:12px;background:#f1f5f9;border:1px solid #e2e8f0;">
<b>✅ BERT Matching Enabled</b><br>
This version matches meaning (semantic similarity), not just exact keywords.
</div>
""",
    unsafe_allow_html=True
)

# ----------------------------
# Load Data
# ----------------------------

jobs_df = load_job_descriptions()
skills_list = load_skills()

# ----------------------------
# Sidebar
# ----------------------------

st.sidebar.header("⚙️ Settings")
selected_role = st.sidebar.selectbox("Select Job Role", jobs_df["role"].tolist())

job_desc = jobs_df[jobs_df["role"] == selected_role]["description"].values[0]

# ----------------------------
# Layout
# ----------------------------

left, right = st.columns([1.2, 1])

with left:
    st.subheader("🧾 Job Description")
    st.info(job_desc)

with right:
    st.subheader("📤 Upload Resume")
    uploaded_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])


# ----------------------------
# Resume Processing
# ----------------------------

if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    else:
        resume_text = extract_text_from_docx(uploaded_file)

    st.subheader("📌 Extracted Resume Text (Preview)")
    st.text_area("Resume Text", resume_text[:3000], height=220)

    if st.button("🔍 Analyze Resume"):
        st.subheader("⏳ Analyzing...")

        progress = st.progress(0)
        status = st.empty()

        status.write("Step 1/4: Extracting skills from resume...")
        progress.progress(25)
        time.sleep(0.3)

        found_skills = extract_skills(resume_text, skills_list)

        status.write("Step 2/4: Extracting required skills from job description...")
        progress.progress(50)
        time.sleep(0.3)

        required_skills = get_required_skills_from_jd(job_desc, skills_list)

        status.write("Step 3/4: Computing BERT match score...")
        progress.progress(75)
        time.sleep(0.3)

        match_score = compute_match_score(resume_text, job_desc)

        status.write("Step 4/4: Finding skill gaps...")
        progress.progress(95)
        time.sleep(0.2)

        missing_skills = get_missing_skills(found_skills, job_desc, skills_list)

        progress.progress(100)
        status.success("✅ Analysis Completed!")

        # ----------------------------
        # Results
        # ----------------------------

        st.subheader("📊 Results Summary")

        coverage = compute_skill_coverage(found_skills, required_skills)
        confidence = get_confidence_label(match_score, coverage)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🎯 Match Score", f"{match_score}%")
        col2.metric("📌 Confidence", confidence)
        col3.metric("🧠 Skill Coverage", f"{coverage}%")
        col4.metric("❌ Missing Skills", len(missing_skills))

        # ----------------------------
        # Skill Gap Breakdown
        # ----------------------------

        st.subheader("🧩 Skill Gap Breakdown (What You Lack)")

        categorized_missing = categorize_skills(missing_skills)
        categorized_found = categorize_skills(found_skills)

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### ✅ Skills Present (by category)")
            if categorized_found:
                for cat, items in categorized_found.items():
                    st.write(f"**{cat}:** {', '.join(items)}")
            else:
                st.warning("No categorized skills found.")

        with c2:
            st.markdown("### ❌ Skills Missing (by category)")
            if categorized_missing:
                for cat, items in categorized_missing.items():
                    st.write(f"**{cat}:** {', '.join(items)}")
            else:
                st.success("No missing skills detected.")

        # ----------------------------
        # Priority Skills
        # ----------------------------

        st.subheader("🔥 Priority Skills to Improve")
        if missing_skills:
            st.write("Focus on these first (high impact for your selected role):")
            st.warning(", ".join(missing_skills[:6]))
        else:
            st.success("No priority missing skills. You're a strong match!")

        # ----------------------------
        # Resume Tips
        # ----------------------------

        st.subheader("📝 Resume Improvement Tips")
        tips = []

        if len(found_skills) < 6:
            tips.append("Add a dedicated **Skills** section with clear keywords (Python, SQL, etc.).")

        if "github" not in found_skills:
            tips.append("Add your **GitHub link** to improve credibility.")

        if match_score < 60:
            tips.append("Add more role-specific projects and mention outcomes (accuracy, impact, results).")

        if missing_skills:
            tips.append("Learn missing skills and add them in projects (not just in skills list).")

        if tips:
            for t in tips:
                st.write("✅ " + t)
        else:
            st.success("Your resume is strong. Add measurable achievements (numbers, impact).")

        # ----------------------------
        # Download Report
        # ----------------------------

        report_text = generate_report(
            selected_role,
            match_score,
            coverage,
            found_skills,
            required_skills,
            missing_skills
        )

        st.download_button(
            label="📥 Download Full Report",
            data=report_text,
            file_name="resume_screening_report.txt",
            mime="text/plain"
        )

else:
    st.info("👆 Upload a resume to start analysis.")
