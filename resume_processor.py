import pdfplumber
import fitz
from cleantext import clean
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
import os
import pandas as pd

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        pass
    if not text:
        try:
            doc = fitz.open(pdf_path)
            text = " ".join(page.get_text() for page in doc)
        except Exception:
            text = ""
    return text

def preprocess_text(text):
    return clean(text, no_urls=True, no_emails=True, no_punct=True, lower=True)

def calculate_scores(job_description, resumes):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    kw_model = KeyBERT(model)
    job_keywords = kw_model.extract_keywords(job_description, top_n=15)
    job_keywords_text = ", ".join([kw[0] for kw in job_keywords])
    job_embedding = model.encode(job_keywords_text)
    resume_embeddings = [model.encode(preprocess_text(r)) for r in resumes]
    scores = [float(util.cos_sim(job_embedding, emb)) * 100 for emb in resume_embeddings]
    return scores

def generate_report(ranked_resumes):
    df = pd.DataFrame(ranked_resumes, columns=["Filename", "Score", "Rank"])
    report_path = os.path.join("uploads", "resume_rankings.csv")
    df.to_csv(report_path, index=False)
    return report_path