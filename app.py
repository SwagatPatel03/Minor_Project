import streamlit as st
import pdfplumber      # For PDF extraction (pip install pdfplumber)
import docx2txt        # For DOCX extraction (pip install docx2txt)

# Import your custom modules
import ner_module      # Contains ner_ml_rule and other NER functions
import cleaning_module    # Contains clean_text_with_groq

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

# Optionally load a curated skills list for reference (if needed for fuzzy matching)
valid_skills = load_valid_skills()

st.title("Dynamic Curriculum Design - Resume Input & Course Recommendation")

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
    
    st.subheader("Extracted Resume Text")
    st.text_area("Resume Text", resume_text, height=300)
    
    if st.button("Extract Resume Information"):
        file_name = uploaded_file.name
        
        # Call your NER function using the resume text directly.
        result = ner_module.ner_ml_rule(file_name, resume_text)
        
        # Assume result[7] is the raw skills list; convert it to a comma-separated string.
        raw_skills = result[7]
        raw_skills_text = ", ".join(raw_skills)
        
        # Clean the skills using the Groq-based cleaning function.
        cleaned_skills_text = cleaning_module.clean_text_with_groq(raw_skills_text)
        # Optionally, split back into a list:
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
        
        # Display the extracted information in a beautifully formatted HTML table.
        st.subheader("Extracted Resume Information")
        table_html = "<table style='border-collapse: collapse; width: 100%;'>"
        for key, value in details.items():
            table_html += f"<tr><td style='border: 1px solid #ddd; padding: 8px;'><strong>{key}</strong></td>"
            table_html += f"<td style='border: 1px solid #ddd; padding: 8px;'>{value}</td></tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)
        
        # Placeholder: Integrate your course recommendation logic here.
        st.subheader("Course Recommendations")
        st.write("Based on your profile, the recommended courses will appear here.")
