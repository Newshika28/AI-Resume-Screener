from sentence_transformers import util
from embedder import get_embedding
from extract import extract_text_from_pdf

def read_text_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def compute_match_score(resume_path, jd_path):
    """
    1. Extract resume text from PDF
    2. Read job description from .txt
    3. Embed both using BERT
    4. Compute cosine similarity → match score
    """
    
    # Step 1: Get texts
    resume_text = extract_text_from_pdf(resume_path)
    jd_text = read_text_file(jd_path)
    
    # Step 2: Get embeddings
    resume_vector = get_embedding(resume_text)
    jd_vector = get_embedding(jd_text)
    
    # Step 3: Cosine similarity (measures angle between two vectors)
    # Score of 1.0 = identical, 0.0 = completely unrelated
    score = util.cos_sim(resume_vector, jd_vector)
    
    match_percent = round(float(score) * 100, 2)
    return match_percent


# --- TEST IT ---
if __name__ == "__main__":
    score = compute_match_score("sample_resume.pdf", "job_description.txt")
    print(f"\n✅ Resume Match Score: {score}%")