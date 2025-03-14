import streamlit as st
import pdfplumber
import docx2txt
import re
import os
from recommendation import get_recommendations
import ner_module
import cleaning_module
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables and configure Gemini once
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Preload static data
@st.cache_data
def load_valid_skills(filepath="skill_set.txt"):
    try:
        with open(filepath, "r") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception:
        return []

@st.cache_data
def load_skills_data():
    try:
        return pd.read_csv("skills_dataset.csv")
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

# Initialize Gemini model once
@st.cache_resource
def load_gemini_model():
    return genai.GenerativeModel('gemini-1.5-flash')

# Session state initialization
if 'resume_data' not in st.session_state:
    st.session_state.resume_data = {
        'text': '',
        'extracted': None,
        'job_desc': '',
        'recommendations': None,
        'ats_scores': None
    }

# ATS scoring prompt
ats_prompt = """
Analyze this resume and job description to provide these 6 scores:
1. ATS Score: Match between resume and job description (0-100%)
2. Readability: Resume clarity and structure (0-100%)
3. Grammar: Spelling and grammar correctness (0-100%)
4. Keywords: Industry-specific keyword usage (0-100%)
5. Experience: Relevance of experience (0-100%)
6. Customization: Tailoring to this specific job (0-100%)

Format response ONLY as comma-separated numbers: 
ATS,Readability,Grammar,Keywords,Experience,Customization
"""

st.title("AI Career Assistant")

# File upload section
with st.sidebar:
    uploaded_file = st.file_uploader("📄 Upload Resume", type=["pdf", "docx", "txt"])
    if uploaded_file:
        # Process resume text once
        if not st.session_state.resume_data['text']:
            if uploaded_file.type == "application/pdf":
                with pdfplumber.open(uploaded_file) as pdf:
                    st.session_state.resume_data['text'] = "\n".join(
                        [page.extract_text() for page in pdf.pages]
                    )
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                st.session_state.resume_data['text'] = docx2txt.process(uploaded_file)
            else:
                st.session_state.resume_data['text'] = uploaded_file.getvalue().decode("utf-8")

        # Extract information once
        if st.button("🔍 Extract Resume Information") and not st.session_state.resume_data['extracted']:
            result = ner_module.ner_ml_rule(uploaded_file.name, st.session_state.resume_data['text'])
            raw_skills = result[7]
            cleaned_skills = cleaning_module.clean_text_with_groq(", ".join(raw_skills)).split(",")
            
            st.session_state.resume_data['extracted'] = {
                "Skills (Cleaned)": ", ".join(cleaned_skills),
                # Keep other fields as needed
            }
            st.success("Information extracted!")

# Main content area
if st.session_state.resume_data['extracted']:
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Display extracted cleaned skills before job description
        st.subheader("Extracted Skills")
        st.text(st.session_state.resume_data['extracted']['Skills (Cleaned)'])
        
        # Job description input
        st.session_state.resume_data['job_desc'] = st.text_area(
            "📝 Paste Job Description", 
            height=200,
            value=st.session_state.resume_data['job_desc']
        )
        
        # Permanent Analyze Compatibility button
        if st.button("🚀 Analyze Compatibility", key="analyze_comp"):
            if st.session_state.resume_data['job_desc'].strip():
                with st.spinner("Analyzing resume and generating recommendations..."):
                    # Get recommendations
                    missing_skills, recs = get_recommendations(
                        st.session_state.resume_data['job_desc'],
                        st.session_state.resume_data['extracted']['Skills (Cleaned)']
                    )
                    
                    # Get ATS scores using Gemini
                    model = load_gemini_model()
                    response = model.generate_content([
                        ats_prompt,
                        st.session_state.resume_data['text'],
                        st.session_state.resume_data['job_desc']
                    ])
                    
                    # Process scores
                    scores = re.findall(r"\d+", response.text)
                    if len(scores) == 6:
                        st.session_state.resume_data['ats_scores'] = {
                            "ATS Score": f"{scores[0]}%",
                            "Readability": f"{scores[1]}%",
                            "Grammar": f"{scores[2]}%",
                            "Keywords": f"{scores[3]}%",
                            "Experience": f"{scores[4]}%",
                            "Customization": f"{scores[5]}%"
                        }
                    else:
                        st.error("Failed to retrieve ATS scores")
                    
                    # Store recommendations and trigger a rerun
                    st.session_state.resume_data['recommendations'] = (missing_skills, recs)
                    st.rerun()
            else:
                st.warning("Please enter a job description before analyzing.")
    
    with col2:
        # Display ATS scores
        if st.session_state.resume_data['ats_scores']:
            st.subheader("📊 ATS Evaluation")
            for metric, score in st.session_state.resume_data['ats_scores'].items():
                st.metric(label=metric, value=score)
        
        # Display Skill Recommendations
        if st.session_state.resume_data['recommendations']:
            st.subheader("📚 Recommended Learning")
            missing_skills, recs = st.session_state.resume_data['recommendations']
            for skill in missing_skills:
                with st.expander(f"🎯 {skill}", expanded=True):
                    if recs.get(skill):
                        for title, url in recs[skill]:
                            st.markdown(f"[{title}]({url})")
                    else:
                        st.info("No courses found for this skill")

# Display raw resume text
# if st.session_state.resume_data['text']:
#     with st.expander("📜 View Raw Resume Text"):
#         st.text(st.session_state.resume_data['text'])