# AI Resume Screener (Streamlit)

AI Resume Screener is a simple AI-based web application built using **Streamlit**.  
It helps to screen resumes by comparing them with job descriptions using **semantic similarity** (meaning-based matching).

This project is useful for quick resume shortlisting and understanding how AI can support recruitment.

---

## Features

- Select a Job Role from the sidebar
- View the Job Description automatically
- Upload a Resume (PDF or DOCX)
- Compare resume content with the job description
- Shows similarity / matching result

---

## Tech Stack

- Python
- Streamlit
- Pandas
- Sentence Transformers (Sentence-BERT)

---

## Project Files


```txt
AI-Resume-Screener/
│── app.py
│── utils.py
│── requirements.txt
│── job_descriptions.csv
│── skills.csv
```
---

## How to Run

### 1. Install requirements
```bash
pip install -r requirements.txt
```
### 2. Run the Streamlit app
```bash
streamlit run app.py
```

## How It Works

1. User selects a **Job Role**
2. The app loads the related **Job Description**
3. User uploads a **Resume** (PDF or DOCX)
4. The app extracts the resume text
5. Sentence-BERT generates embeddings for both the resume and job description
6. A similarity score is calculated and displayed
