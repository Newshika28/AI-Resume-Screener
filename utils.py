import re
import pandas as pd
import pdfplumber
from docx import Document

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ✅ Load Sentence-BERT model only once
bert_model = SentenceTransformer("all-MiniLM-L6-v2")


# ----------------------------
# Skill Categories (Realistic)
# ----------------------------
SKILL_CATEGORIES = {
    "Programming": [
        "python", "java", "c++", "javascript"
    ],
    "Data & Analytics": [
        "pandas", "numpy", "sql", "excel", "statistics", "data visualization",
        "power bi", "tableau"
    ],
    "Machine Learning": [
        "machine learning", "scikit-learn", "feature engineering", "model deployment"
    ],
    "Deep Learning": [
        "deep learning", "tensorflow", "pytorch", "cnn", "transformers"
    ],
    "NLP": [
        "nlp", "bert", "tokenization", "sentiment analysis", "named entity recognition"
    ],
    "Computer Vision": [
        "computer vision", "opencv", "yolo", "object detection", "segmentation"
    ],
    "Backend / APIs": [
        "flask", "django", "api", "rest api"
    ],
    "Cloud & DevOps": [
        "aws", "azure", "docker", "kubernetes", "ci/cd", "linux"
    ],
    "Databases": [
        "mysql", "mongodb", "data warehouse"
    ],
}


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
    return text.strip()


def extract_text_from_pdf(file) -> str:
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def extract_text_from_docx(file) -> str:
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs]).strip()


def load_job_descriptions(path="job_descriptions.csv"):
    return pd.read_csv(path)


def load_skills(path="skills.csv"):
    df = pd.read_csv(path)
    return df["skill"].dropna().str.lower().tolist()


def extract_skills(resume_text: str, skills_list):
    resume_text = clean_text(resume_text)
    found = []

    for skill in skills_list:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, resume_text):
            found.append(skill)

    return sorted(list(set(found)))


def compute_match_score(resume_text: str, job_desc: str) -> int:
    """
    Semantic similarity using Sentence-BERT embeddings.
    Returns match score as integer percentage (no decimals).
    """
    resume_text = clean_text(resume_text)
    job_desc = clean_text(job_desc)

    resume_embedding = bert_model.encode(resume_text, convert_to_tensor=False)
    job_embedding = bert_model.encode(job_desc, convert_to_tensor=False)

    score = cosine_similarity([resume_embedding], [job_embedding])[0][0]
    return int(score * 100)


def get_required_skills_from_jd(job_desc: str, skills_list):
    job_desc_clean = clean_text(job_desc)
    required = []

    for skill in skills_list:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, job_desc_clean):
            required.append(skill)

    return sorted(list(set(required)))


def get_missing_skills(found_skills, job_desc, skills_list):
    required = set(get_required_skills_from_jd(job_desc, skills_list))
    found = set(found_skills)
    missing = sorted(list(required - found))
    return missing


def categorize_skills(skills):
    """
    Returns a dict: category -> list of skills
    """
    categorized = {cat: [] for cat in SKILL_CATEGORIES.keys()}
    categorized["Other"] = []

    for s in skills:
        placed = False
        for cat, cat_skills in SKILL_CATEGORIES.items():
            if s in cat_skills:
                categorized[cat].append(s)
                placed = True
                break
        if not placed:
            categorized["Other"].append(s)

    # remove empty categories
    categorized = {k: v for k, v in categorized.items() if len(v) > 0}
    return categorized


def compute_skill_coverage(found_skills, required_skills):
    """
    Coverage % = matched required skills / total required skills
    """
    required = set(required_skills)
    found = set(found_skills)

    if len(required) == 0:
        return 0

    matched = required.intersection(found)
    coverage = (len(matched) / len(required)) * 100
    return int(coverage)
