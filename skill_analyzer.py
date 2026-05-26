from sentence_transformers import util
from embedder import get_embedding

# -------------------------------------------------------
# SKILL BANK — a master list of ML/AI/Tech skills
# We check how many of these appear in the JD and resume
# -------------------------------------------------------
SKILL_BANK = [
    "Python", "PyTorch", "TensorFlow", "scikit-learn", "Keras",
    "NLP", "computer vision", "OpenCV", "YOLO", "object detection",
    "deep learning", "machine learning", "neural networks",
    "Flask", "FastAPI", "REST API", "MongoDB", "SQL",
    "LangChain", "Gemini", "GPT", "transformers", "BERT",
    "SHAP", "explainability", "feature engineering",
    "data preprocessing", "model deployment", "Docker",
    "Git", "GitHub", "Streamlit", "Hugging Face",
    "pandas", "numpy", "matplotlib", "seaborn",
    "classification", "regression", "clustering",
    "real-time inference", "embeddings", "vector database"
]

# Similarity threshold — if score >= this, skill is "present"
THRESHOLD = 0.25


def extract_skills_from_text(text, label="Text"):
    """
    For each skill in SKILL_BANK, compute how similar it is
    to the given text using BERT embeddings.
    Returns a dict: {skill: similarity_score}
    """
    text_embedding = get_embedding(text)
    skill_scores = {}

    for skill in SKILL_BANK:
        skill_embedding = get_embedding(skill)
        score = float(util.cos_sim(text_embedding, skill_embedding))
        skill_scores[skill] = round(score, 4)

    return skill_scores


def analyze_skill_gap(resume_text, jd_text):
    """
    Compares resume skills vs JD skills.
    Returns:
      - matched: skills present in both JD and resume ✅
      - missing: skills in JD but NOT in resume ❌
      - bonus:   skills in resume but not required by JD 🌟
    """
    print("\n🔍 Analyzing skills... (this takes ~20 seconds)")

    jd_skills = extract_skills_from_text(jd_text, "JD")
    resume_skills = extract_skills_from_text(resume_text, "Resume")

    # Skills the JD wants (above threshold)
    jd_required = {s for s, score in jd_skills.items() if score >= THRESHOLD}

    # Skills the resume has (above threshold)
    resume_has = {s for s, score in resume_skills.items() if score >= THRESHOLD}

    matched = jd_required & resume_has          # in both
    missing = jd_required - resume_has          # JD wants, resume lacks
    bonus   = resume_has - jd_required          # resume has extra skills

    return {
        "matched": sorted(matched),
        "missing": sorted(missing),
        "bonus":   sorted(bonus),
        "jd_required": sorted(jd_required),
        "resume_has":  sorted(resume_has)
    }


# --- TEST IT ---
if __name__ == "__main__":
    from extract import extract_text_from_pdf

    def read_file(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    resume_text = extract_text_from_pdf("sample_resume.pdf")
    jd_text     = read_file("job_description.txt")

    results = analyze_skill_gap(resume_text, jd_text)

    print("\n" + "="*50)
    print("📋 JD REQUIRES:")
    for s in results["jd_required"]:
        print(f"   • {s}")

    print("\n✅ YOU HAVE (matched):")
    for s in results["matched"]:
        print(f"   ✅ {s}")

    print("\n❌ YOU ARE MISSING:")
    for s in results["missing"]:
        print(f"   ❌ {s}")

    print("\n🌟 BONUS SKILLS (you have extra):")
    for s in results["bonus"]:
        print(f"   🌟 {s}")

    print("="*50)
    match_pct = round(len(results["matched"]) / max(len(results["jd_required"]), 1) * 100, 1)
    print(f"\n🎯 Skill Match: {len(results['matched'])}/{len(results['jd_required'])} = {match_pct}%")