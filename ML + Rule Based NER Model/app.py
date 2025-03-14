import streamlit as st
import pdfplumber      # For PDF extraction (pip install pdfplumber)
import docx2txt        # For DOCX extraction (pip install docx2txt)
from recommendation import get_recommendations
# Import your custom modules
import ner_module      # Contains ner_ml_rule and other NER functions
import cleaning_module    # Contains clean_text_with_groq
# from recommendation import recommend_skills_gap  # Recommendation function
import pandas as pd
def load_valid_skills(filepath="skill_set.txt"):
    """
    Loads a curated list of valid skills from a text file.
    Each line should contain one valid skill.
    """
    try:
        with open(filepath, "r") as file:
            valid_skills = [line.strip() for line in file if line.strip()]
        return valid_skills
    except Exception as e:
        return []

def load_data():
    """
    Loads the skills dataset for recommendations.
    """
    try:
        # Adjust the path as needed for your dataset
        return pd.read_csv("skills_dataset.csv")
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()
        return []

# Optionally load a curated skills list for reference (if needed for fuzzy matching)
valid_skills = load_valid_skills()

st.title("Dynamic Curriculum Design - Resume Input & Course Recommendation")

# Initialize session state variables if they don't exist
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "extracted_info" not in st.session_state:
    st.session_state.extracted_info = None
if "job_desc" not in st.session_state:
    st.session_state.job_desc = ""
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None

# File uploader widget: Accept PDF, DOCX, or TXT files.
uploaded_file = st.file_uploader("Upload your resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    file_type = uploaded_file.type
    resume_text = ""
    
    if file_type == "application/pdf":
        # Extract text from PDF using pdfplumber.
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                resume_text += page.extract_text() + "\n"
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # Extract text from DOCX using docx2txt.
        resume_text = docx2txt.process(uploaded_file)
    else:
        # For TXT files, decode the file content.
        resume_text = uploaded_file.getvalue().decode("utf-8")
    
    st.session_state.resume_text = resume_text  # Store the resume text in session state
    
    st.subheader("Extracted Resume Text")
    st.text_area("Resume Text", st.session_state.resume_text, height=300)

    if st.button("Extract Resume Information"):
        file_name = uploaded_file.name
        # Call your NER function using the resume text directly.
        result = ner_module.ner_ml_rule(file_name, st.session_state.resume_text)
        st.session_state.extracted_info = result  # Save the extracted info
        
        # Optionally, display a success message.
        st.success("Resume information extracted successfully!")

if st.session_state.extracted_info is not None:
    # Check if the extracted info is still a tuple (not yet processed)
    if isinstance(st.session_state.extracted_info, tuple):
        result = st.session_state.extracted_info
        # Process skills: assume result[7] is the raw skills list.
        raw_skills = result[7]
        raw_skills_text = ", ".join(raw_skills)
        
        # Clean the skills using the Groq-based cleaning function.
        cleaned_skills_text = cleaning_module.clean_text_with_groq(raw_skills_text)
        cleaned_skills = [skill.strip() for skill in cleaned_skills_text.split(",")]
        
        # Create a dictionary of the extracted details.
        details = {
            "Name": result[1],
            "Phone Number": result[2],
            "Email": ", ".join(result[3]),
            "Qualifications": result[4],
            "Graduation Year": ", ".join([str(y) for y in result[5]]),
            "Location": ", ".join(result[6]),
            "Skills (Raw)": raw_skills_text,
            "Skills (Cleaned)": cleaned_skills_text,
            "University": ", ".join(result[8]),
            "Company": ", ".join(result[9]),
            "Designation": ", ".join(result[10]),
        }
        
        st.session_state.extracted_info = details
    else:
        details = st.session_state.extracted_info

    st.subheader("Extracted Resume Information")
    table_html = "<table style='border-collapse: collapse; width: 70%;'>"  # reduced width
    for key, value in details.items():
        table_html += f"<tr><td style='border: 1px solid #ddd; padding: 8px;'><strong>{key}</strong></td>"
        table_html += f"<td style='border: 1px solid #ddd; padding: 8px;'>{value}</td></tr>"
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)
    
    # Job description input for course recommendation.
    st.subheader("Enter Job Description")
    st.session_state.job_desc = st.text_area("Job Description", st.session_state.job_desc, height=150)
    
    if st.button("Find Missing Skills & Recommend Courses"):  # renamed button
        missing_skills, recommendations = get_recommendations(
            st.session_state.job_desc,
            st.session_state.extracted_info['Skills (Cleaned)']
        )
        
        # Print missing skills and recommended courses to the terminal.
        print("Missing Skills & Recommended Courses:")
        for skill in missing_skills:
            print(f"Skill: {skill}")
            if recommendations.get(skill):
                for title, url in recommendations[skill]:
                    print(f"  - {title}: {url}")
            else:
                print("  - No courses found")
        
        st.subheader("Missing Skills & Recommended Courses")
        for skill in missing_skills:
            st.markdown(f"### {skill}")
            if recommendations.get(skill):
                for title, url in recommendations[skill]:
                    st.markdown(f"* [{title}]({url})")
            else:
                st.markdown("* No courses found")
            st.markdown("---")
