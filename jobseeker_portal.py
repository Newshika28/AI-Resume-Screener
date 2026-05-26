import streamlit as st
import tempfile, os
import plotly.graph_objects as go
from extract import extract_text_from_pdf
from scorer import compute_match_score
from skill_analyzer import analyze_skill_gap

def compute_ats_score(resume_text, matched_skills, missing_skills, jd_required):
    """
    Real ATS scoring based on actual ATS system behavior.
    Returns (score, list of issues)
    """
    score = 100
    issues = []
    word_count = len(resume_text.split())
    resume_lower = resume_text.lower()

    # 1. Word count check
    if word_count < 150:
        score -= 25
        issues.append(("❌ Critical", "Resume too short — ATS expects 300–800 words for entry-level roles"))
    elif word_count < 300:
        score -= 10
        issues.append(("⚠️ Warning", f"Resume is short ({word_count} words) — consider expanding project descriptions"))

    # 2. Measurable achievements
    import re
    numbers = re.findall(r'\d+[\%\+xX]?', resume_text)
    if len(numbers) < 2:
        score -= 20
        issues.append(("❌ Critical", "No measurable results found — add metrics like '95% accuracy', '3x faster', '10K images'"))
    elif len(numbers) < 4:
        score -= 8
        issues.append(("⚠️ Warning", "Few measurable results — try to quantify more achievements"))

    # 3. Keyword density — missing skills
    missing_ratio = len(missing_skills) / max(len(jd_required), 1)
    if missing_ratio > 0.6:
        score -= 20
        issues.append(("❌ Critical", f"Keyword match too low — {len(missing_skills)} required skills missing from resume"))
    elif missing_ratio > 0.35:
        score -= 10
        issues.append(("⚠️ Warning", f"{len(missing_skills)} JD keywords missing — add them naturally to project descriptions"))

    # 4. Weak action verbs
    weak_verbs = ["worked on", "helped with", "did", "made", "assisted", "involved in"]
    found_weak = [v for v in weak_verbs if v in resume_lower]
    if found_weak:
        score -= 10
        issues.append(("⚠️ Warning", f"Weak verbs found: '{', '.join(found_weak)}' — replace with: Built, Engineered, Developed, Optimized"))

    # 5. Contact info check
    has_email = "@" in resume_text
    has_phone = bool(re.search(r'\d{10}|\d{3}[-.\s]\d{3}', resume_text))
    if not has_email:
        score -= 10
        issues.append(("⚠️ Warning", "No email detected — ensure contact info is ATS-readable (not inside image/header)"))
    if not has_phone:
        score -= 5
        issues.append(("ℹ️ Info", "No phone number detected — may be inside a graphic header that ATS can't read"))

    # 6. Section headers check
    common_sections = ["education", "experience", "project", "skill", "certification"]
    found_sections = [s for s in common_sections if s in resume_lower]
    if len(found_sections) < 3:
        score -= 10
        issues.append(("⚠️ Warning", f"Only {len(found_sections)} standard sections found — ATS looks for: Education, Skills, Projects, Experience"))

    return max(score, 0), issues


def generate_mock_questions(matched_skills, missing_skills, role="ML/AI Engineer"):
    """
    Generates targeted mock interview questions based on
    matched skills (they'll be asked these) and
    missing skills (they should prepare for these too).
    """
    questions = {
        "✅ Expect These (Your Strong Areas)": [],
        "⚠️ Prepare These (Your Weak Areas)": [],
        "🧠 General ML Concepts": [
            "Explain the bias-variance tradeoff with an example.",
            "What's the difference between overfitting and underfitting? How do you fix each?",
            "Walk me through how you'd approach a new ML problem from scratch.",
            "What metrics would you use for an imbalanced classification dataset?"
        ]
    }

    skill_question_map = {
        "Python":            "Write a Python function to find duplicates in a list without using set().",
        "PyTorch":           "How do you define a custom neural network in PyTorch? Walk me through nn.Module.",
        "TensorFlow":        "What is a TensorFlow computational graph and why does it matter?",
        "scikit-learn":      "Explain the difference between fit(), transform(), and fit_transform().",
        "computer vision":   "How does a CNN extract features from an image? Explain convolution layers.",
        "OpenCV":            "How would you detect edges in an image using OpenCV?",
        "YOLO":              "How does YOLO differ from two-stage detectors like Faster R-CNN?",
        "object detection":  "What is IoU (Intersection over Union) and why is it used in object detection?",
        "deep learning":     "Explain backpropagation in simple terms.",
        "machine learning":  "What's the difference between supervised and unsupervised learning?",
        "NLP":               "How does tokenization work and why does it matter in NLP?",
        "Flask":             "How would you expose an ML model as a REST API using Flask?",
        "FastAPI":           "What's the difference between Flask and FastAPI for ML deployment?",
        "MongoDB":           "When would you choose MongoDB over a relational database for an ML project?",
        "LangChain":         "How does LangChain help in building LLM-powered applications?",
        "SHAP":              "What is SHAP and how does it explain a model's predictions?",
        "Docker":            "How would you containerize an ML model using Docker?",
        "model deployment":  "What are the challenges of deploying ML models in production?",
        "feature engineering": "What feature engineering techniques have you used? Give an example.",
        "pandas":            "How do you handle missing values in a pandas DataFrame?",
        "neural networks":   "Explain the role of activation functions in neural networks.",
        "transformers":      "How does the attention mechanism work in transformer models?",
        "BERT":              "What makes BERT different from earlier NLP models like Word2Vec?",
        "Git":               "How do you resolve a merge conflict in Git?",
        "Streamlit":         "How did you use Streamlit to deploy your ML project?",
        "real-time inference": "What optimizations would you use for real-time model inference?",
    }

    for skill in matched_skills:
        if skill in skill_question_map:
            questions["✅ Expect These (Your Strong Areas)"].append(
                (skill, skill_question_map[skill])
            )

    for skill in missing_skills:
        if skill in skill_question_map:
            questions["⚠️ Prepare These (Your Weak Areas)"].append(
                (skill, skill_question_map[skill])
            )

    return questions


def render():
    st.markdown("## 👤 Job Seeker Portal")
    st.markdown("Upload your resume and paste a job description to get your full AI analysis.")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 Your Resume")
        uploaded_file = st.file_uploader("PDF only", type=["pdf"], key="js_resume")
    with col2:
        st.subheader("📋 Job Description")
        jd_text = st.text_area("Paste the JD here", height=200, key="js_jd",
                               placeholder="We are looking for an ML Engineer with Python, PyTorch...")

    analyze_btn = st.button("🚀 Analyze My Resume", use_container_width=True, type="primary")

    if analyze_btn:
        if not uploaded_file:
            st.error("❌ Please upload your resume PDF.")
            return
        if not jd_text.strip():
            st.error("❌ Please paste a job description.")
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        jd_path = tmp_path + "_jd.txt"
        with open(jd_path, "w", encoding="utf-8") as f:
            f.write(jd_text)

        progress = st.progress(0, text="📄 Reading your resume...")

        try:
            resume_text = extract_text_from_pdf(tmp_path)
            progress.progress(25, text="🧠 Running BERT analysis...")
            overall_score = compute_match_score(tmp_path, jd_path)
            progress.progress(55, text="🔍 Analyzing skill gaps...")
            results = analyze_skill_gap(resume_text, jd_text)
            progress.progress(85, text="🎯 Computing ATS score...")
            ats_score, ats_issues = compute_ats_score(
                resume_text, results["matched"], results["missing"], results["jd_required"]
            )
            progress.progress(100, text="✅ Done!")
            progress.empty()

            # ── OVERALL SCORE ──
            st.markdown("---")
            st.markdown("## 📊 Your Results")

            if overall_score >= 70:
                color, verdict = "#2ecc71", "🟢 Strong Match — Apply now!"
            elif overall_score >= 50:
                color, verdict = "#f39c12", "🟡 Moderate Match — Improve before applying"
            else:
                color, verdict = "#e74c3c", "🔴 Weak Match — Significant gaps found"

            st.markdown(f"""
            <div style='background:#1a1a2e;border:2px solid {color};border-radius:12px;
                        padding:20px;text-align:center;margin:16px 0'>
                <div style='font-size:64px;font-weight:800;color:{color}'>{overall_score}%</div>
                <div style='font-size:15px;color:#aaa'>{verdict}</div>
            </div>""", unsafe_allow_html=True)

            skill_pct = round(len(results["matched"]) / max(len(results["jd_required"]), 1) * 100, 1)
            st.metric("🎯 Skill Match", f"{skill_pct}%",
                      f"{len(results['matched'])} of {len(results['jd_required'])} required skills found")
            st.divider()

            # ── SKILL CARDS ──
            st.markdown("### ✅ Skills You Have")
            if results["matched"]:
                st.markdown("".join([
                    f"<span style='background:#1a3a1a;border:1px solid #2ecc71;border-radius:8px;padding:6px 12px;margin:4px;display:inline-block;color:#2ecc71;font-weight:600'>✅ {s}</span>"
                    for s in results["matched"]
                ]), unsafe_allow_html=True)

            st.markdown("### ❌ Skills You're Missing")
            if results["missing"]:
                st.markdown("".join([
                    f"<span style='background:#3a1a1a;border:1px solid #e74c3c;border-radius:8px;padding:6px 12px;margin:4px;display:inline-block;color:#e74c3c;font-weight:600'>❌ {s}</span>"
                    for s in results["missing"]
                ]), unsafe_allow_html=True)
            else:
                st.success("🎉 You have all required skills!")

            if results["bonus"]:
                st.markdown("### 🌟 Bonus Skills")
                st.markdown("".join([
                    f"<span style='background:#1a2a3a;border:1px solid #3498db;border-radius:8px;padding:6px 12px;margin:4px;display:inline-block;color:#3498db;font-weight:600'>🌟 {s}</span>"
                    for s in results["bonus"]
                ]), unsafe_allow_html=True)

            st.divider()

            # ── ATS SCORE ──
            st.markdown("### 🎯 ATS Score Simulator")
            st.caption("ATS bots filter resumes before any human sees them. This score simulates how well yours passes.")

            ats_color = "#2ecc71" if ats_score >= 75 else "#f39c12" if ats_score >= 50 else "#e74c3c"
            ats_label = "✅ ATS Friendly" if ats_score >= 75 else "⚠️ Needs Improvement" if ats_score >= 50 else "❌ High Risk of Rejection"

            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"""
                <div style='background:#1a1a2e;border:2px solid {ats_color};border-radius:12px;
                            padding:16px;text-align:center'>
                    <div style='font-size:48px;font-weight:800;color:{ats_color}'>{ats_score}</div>
                    <div style='color:#aaa;font-size:13px'>out of 100</div>
                    <div style='color:{ats_color};font-size:13px;margin-top:6px'>{ats_label}</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                if ats_issues:
                    for severity, msg in ats_issues:
                        if "Critical" in severity:
                            st.error(f"**{severity}:** {msg}")
                        elif "Warning" in severity:
                            st.warning(f"**{severity}:** {msg}")
                        else:
                            st.info(f"**{severity}:** {msg}")
                else:
                    st.success("✅ No ATS issues detected! Your resume is well-optimized.")

            st.divider()

            # ── RADAR CHART ──
            st.markdown("### 📈 Skill Radar Chart")
            categories = ["ML & Algorithms", "Deep Learning", "Computer Vision", "Deployment & APIs", "Dev Tools"]
            ml_skills     = ["machine learning","scikit-learn","classification","regression","clustering","feature engineering","SHAP"]
            dl_skills     = ["deep learning","PyTorch","TensorFlow","Keras","neural networks","transformers","BERT","embeddings"]
            cv_skills     = ["computer vision","OpenCV","YOLO","object detection","real-time inference"]
            deploy_skills = ["Flask","FastAPI","REST API","model deployment","Docker","Streamlit","Hugging Face"]
            tool_skills   = ["Python","Git","GitHub","pandas","numpy","matplotlib","MongoDB","SQL"]

            def coverage(skill_list, user_skills):
                matched = sum(1 for s in skill_list if s in user_skills)
                return round((matched / len(skill_list)) * 100)

            user_all = set(results["matched"] + results["bonus"])
            values = [
                coverage(ml_skills, user_all),
                coverage(dl_skills, user_all),
                coverage(cv_skills, user_all),
                coverage(deploy_skills, user_all),
                coverage(tool_skills, user_all),
            ]

            fig = go.Figure(data=go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                fillcolor='rgba(155,89,182,0.3)',
                line=dict(color='#9b59b6', width=2),
                marker=dict(size=6, color='#9b59b6')
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0,100],
                                    tickfont=dict(color='#aaa'), gridcolor='#333'),
                    angularaxis=dict(tickfont=dict(color='white'), gridcolor='#333'),
                    bgcolor='#1a1a2e'
                ),
                paper_bgcolor='#0f0f0f',
                font=dict(color='white'),
                showlegend=False,
                height=420
            )
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # ── MOCK INTERVIEW ──
            st.markdown("### 🎤 Mock Interview Questions")
            st.caption("Based on your skill gap analysis — these are the questions you're likely to face.")

            questions = generate_mock_questions(results["matched"], results["missing"])

            for section, items in questions.items():
                if not items:
                    continue
                with st.expander(f"{section} ({len(items)} questions)", expanded=(section == "✅ Expect These (Your Strong Areas)")):
                    if isinstance(items[0], tuple):
                        for skill, question in items:
                            st.markdown(f"""
                            <div style='background:#1a1a2e;border-left:3px solid #9b59b6;
                                        padding:12px 16px;border-radius:6px;margin:8px 0'>
                                <div style='color:#9b59b6;font-size:12px;font-weight:600'>{skill}</div>
                                <div style='color:white;margin-top:4px'>❓ {question}</div>
                            </div>""", unsafe_allow_html=True)
                    else:
                        for question in items:
                            st.markdown(f"""
                            <div style='background:#1a1a2e;border-left:3px solid #3498db;
                                        padding:12px 16px;border-radius:6px;margin:8px 0'>
                                <div style='color:white'>❓ {question}</div>
                            </div>""", unsafe_allow_html=True)

            st.divider()

            # ── FINAL RECOMMENDATION ──
            st.markdown("### 💡 Final Recommendation")
            if overall_score >= 70:
                st.success("🟢 Strong match! Your resume is ready. Apply directly to this role.")
            elif overall_score >= 50:
                st.warning(f"🟡 Moderate match. Add these to your resume: **{', '.join(results['missing'][:3])}**")
            else:
                st.error(f"🔴 Weak match. Focus on building: **{', '.join(results['missing'][:5])}** before applying.")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
        finally:
            os.unlink(tmp_path)
            if os.path.exists(jd_path):
                os.unlink(jd_path)