import streamlit as st
import tempfile
import time
from pdf import (
    extract_text_from_pdf, 
    extract_domains_from_pdf, 
    load_job_listings_from_file, 
    analyze_resume_with_job_listings,
    display_jobs_by_category
)
from scrap import (
    indeed_auto_extract, 
    naukri_auto_extract, 
    foundit_auto_extract, 
    generate_job_listings
)

st.set_page_config(
    page_title="Job Search",  
    page_icon="🔍",              
    layout="wide",                
    initial_sidebar_state="expanded"  
)

st.markdown("""
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
    }
    .stFileUploader label, .stSelectbox label {
        font-weight: bold;
        font-size: 1.1rem;
    }
    .domain-pill {
        display: inline-block;
        background: linear-gradient(135deg, #6e8efb, #a777e3);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        margin: 5px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .hero-container {
        text-align: center;
        padding: 2rem 0;
        background: rgba(255,255,255,0.05);
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="hero-container">
        <h1 style="font-size: 3rem; margin-bottom: 0;">🚀 Next-Hire</h1>
        <p style="font-size: 1.2rem; color: #888;">AI-Powered Resume Analysis & Job Matching</p>
    </div>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "Upload Resume"
if "domains" not in st.session_state:
    st.session_state.domains = None
if "resume_text" not in st.session_state:
    st.session_state.resume_text = None
if "job_listings_text" not in st.session_state:
    st.session_state.job_listings_text = None

st.sidebar.title("Navigation")
if st.session_state.page == "Upload Resume":
    st.sidebar.radio("Go to", ["Upload Resume", "Job Analysis", "Results"], index=0, key="nav")
elif st.session_state.page == "Job Analysis":
    st.sidebar.radio("Go to", ["Upload Resume", "Job Analysis", "Results"], index=1, key="nav")
elif st.session_state.page == "Results":
    st.sidebar.radio("Go to", ["Upload Resume", "Job Analysis", "Results"], index=2, key="nav")

if st.session_state.page == "Upload Resume":
    st.header("Step 1: Upload Your Resume")
    uploaded_file = st.file_uploader("Upload a PDF file:", type=["pdf"])
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        with st.status("Analyzing your resume...", expanded=True) as status:
            st.write("📄 Extracting text from PDF...")
            resume_text = extract_text_from_pdf(tmp_path)
            st.write("🧠 Identifying key domains...")
            domains = extract_domains_from_pdf(tmp_path)
            st.session_state.domains = domains
            st.session_state.resume_text = resume_text
            status.update(label="Resume Analysis Complete!", state="complete", expanded=False)

        st.subheader("🎯 Key Domains Identified")
        pills_html = "".join([f'<span class="domain-pill">{d}</span>' for d in st.session_state.domains])
        st.markdown(f"<div>{pills_html}</div><br>", unsafe_allow_html=True)
        
        st.session_state.page = "Job Analysis"
        st.rerun()
    else:
        st.info("Please upload a PDF file to continue.")

elif st.session_state.page == "Job Analysis":
    st.header("Step 2: Select a Job Site for Analysis")
    if st.session_state.domains is None or st.session_state.resume_text is None:
        st.warning("Please upload your resume first in 'Upload Resume' section.")
    else:
        options = ["Select a job site", "Indeed", "Naukri", "Foundit", "Jooble"]
        choice = st.selectbox("Choose a job site:", options)

        if choice and choice != "Select a job site":
            with st.status(f"Processing jobs from {choice}...", expanded=True) as status:
                st.write(f"🌐 Scraping latest listings from {choice}...")
                if choice == "Indeed":
                    for domain in st.session_state.domains:
                        indeed_auto_extract(domain)
                    st.session_state.job_listings_text = load_job_listings_from_file("indeed_job_cards.txt")
                elif choice == "Naukri":
                    for domain in st.session_state.domains:
                        naukri_auto_extract(domain)
                    st.session_state.job_listings_text = load_job_listings_from_file("naukri_job_cards.txt")
                elif choice == "Foundit":
                    for domain in st.session_state.domains:
                        foundit_auto_extract(domain)
                    st.session_state.job_listings_text = load_job_listings_from_file("foundit_job_cards.txt")
                elif choice == "Jooble":
                    generate_job_listings(st.session_state.domains)
                    st.session_state.job_listings_text = load_job_listings_from_file("jooble_job_cards.txt")

                st.write("🤖 AI is matching your skills with these jobs...")
                analyze_resume_with_job_listings(st.session_state.resume_text, st.session_state.job_listings_text)
                status.update(label="Job Analysis Completed!", state="complete", expanded=False)

            st.session_state.page = "Results"
            st.rerun()

elif st.session_state.page == "Results":
    st.header("Step 3: View Analysis Results")
    if st.session_state.job_listings_text is None:
        st.warning("Please complete the previous steps before viewing results.")
    else:
        file_path = "job_analysis_results.txt"
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                st.subheader("📝 Job Analysis Results")
                st.markdown("---")
                display_jobs_by_category(content)
        except FileNotFoundError:
            st.error("Analysis results not found. Please complete the previous steps.")

# Footer with additional notes
# st.write("---")
# st.markdown("""
# <div style="text-align: center; font-size: 12px;">
#     \n
#     footer
# </div>
# """, unsafe_allow_html=True)
