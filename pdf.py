import os
import re
import PyPDF2
from groq import Groq
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# API Key for Groq
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file safely.
    """
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text.strip()

def analyze_resume_with_llama(text):
    """
    Analyze the extracted text using the Groq API.
    """
    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY is not set. Please add it to your .env file.")
        return ""

    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""
    Analyze the following resume text and identify key domains related to the skills, projects, internships, and interests mentioned.
    Limit the identified domains to 6 critically most important ones. Provide only the domain names, one per line, without any numbers, bullet symbols, descriptions, or attached explanations.

    Resume Text: {text}
    """
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=512,
            top_p=1,
            stream=True,
            stop=None,
        )

        analysis_result = ""
        for chunk in completion:
            chunk_content = chunk.choices[0].delta.content or ""
            analysis_result += chunk_content

        return analysis_result
    except Exception as e:
        st.error(f"Error calling Groq API: {e}")
        return ""

def extract_domains_from_pdf(pdf_path_or_text):
    """
    Function to analyze PDF (or pre-extracted text) and extract important domains.
    """
    if isinstance(pdf_path_or_text, str) and os.path.exists(pdf_path_or_text):
        resume_text = extract_text_from_pdf(pdf_path_or_text)
    else:
        resume_text = pdf_path_or_text

    analysis = analyze_resume_with_llama(resume_text)
    domains = extract_and_limit_domains(analysis, max_domains=6)
    return domains

def extract_and_limit_domains(analysis_result, max_domains=6):
    """
    Extract important domains from the analysis result and limit to a maximum count.
    Cleans leading numbers, bullet symbols, and non-domain text.
    """
    domains = []
    lines = analysis_result.split("\n")

    for line in lines:
        cleaned = re.sub(r'^[\d+\.\-\*\•\s]+', '', line).strip()
        # Filter out empty lines or conversational responses
        if cleaned and len(cleaned.split()) <= 5 and not cleaned.lower().startswith(("here", "domain", "note", "based")):
            if cleaned not in domains:
                domains.append(cleaned)

    return domains[:max_domains]

def load_job_listings_from_file(file_path="job_listings.txt"):
    """
    Load job listings from a text file with UTF-8 encoding.
    """
    if not os.path.exists(file_path):
        return ""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def analyze_resume_with_job_listings(resume_text, job_listings_text):
    """
    Analyze the resume and job listings using the Groq API.
    """
    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY is not set. Please add it to your .env file.")
        return

    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""
    You are an AI job analysis assistant. Below is a resume and a list of job listings.
    Your tasks are:
    1. For each job listing, analyze the skills required based on the job description.
    2. Compare the required skills with the resume.
    3. For each job listing, identify:
        - Strengths: The skills the user possesses that match the job requirements.
        - Areas of Improvement: The skills the user lacks based on the job requirements.
    4. Categorize each job into:
        - Must Apply
        - Good Fit
        - Neutral
        - Doesn't Align
    5. Provide the output in a beautified, structured format, clearly listing:
        - Domain
        - Job Title
        - Company
        - Category
        - Strengths
        - Areas of Improvement
        - Reason for Categorization
    6. Make sure all the job listings are covered.

    Resume:
    {resume_text}

    Job Listings:
    {job_listings_text}
    """
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=True,
            stop=None,
        )

        analysis_result = ""
        for chunk in completion:
            chunk_content = chunk.choices[0].delta.content or ""
            analysis_result += chunk_content

        # Save the result to a text file
        output_file = "job_analysis_results.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(analysis_result)

    except Exception as e:
        st.error(f"Error analyzing job listings with Groq: {e}")

def display_jobs_by_category(content):
    """
    Displays job analysis results in a structured format using Streamlit.
    Gracefully falls back to markdown display if custom parser encounters unexpected format.
    """
    try:
        lines = content.split('\n')
        parsed_any = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("**") and stripped.endswith("**"):
                category = stripped.replace("**", "").strip()
                st.header(category)
                parsed_any = True

            elif re.match(r'^\d+\.', stripped):
                job_title = re.sub(r'^\d+\.\s*', '', stripped).strip()
                st.subheader(job_title)
                parsed_any = True

            elif stripped.startswith(('* ', '- ')):
                cleaned = stripped[2:].strip()
                if ': ' in cleaned:
                    key, value = cleaned.split(': ', 1)
                    st.markdown(f"**{key}:** {value}")
                else:
                    st.markdown(f"- {cleaned}")
                parsed_any = True

            elif stripped.startswith('---'):
                st.markdown("---")
                parsed_any = True

        if not parsed_any:
            st.markdown(content)

    except Exception as e:
        st.warning(f"Displaying results in standard format: {str(e)}")
        st.markdown(content)
