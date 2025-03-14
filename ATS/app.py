from dotenv import load_dotenv
import base64
import streamlit as st
import os
import io
from PIL import Image 
import pdf2image
import google.generativeai as genai
import re  # Import regex for extracting numbers

# Load API Key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get Gemini response
def get_gemini_response(input_prompt, pdf_content, job_description):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input_prompt, pdf_content[0], job_description])
    return response.text

# Function to process uploaded PDF
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(uploaded_file.read(), poppler_path=r"C:\poppler-24.08.0\Library\bin")
        first_page = images[0]

        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

## Streamlit App

st.set_page_config(page_title="ATS Resume Expert")
st.header("ATS Tracking System")
input_text = st.text_area("Job Description:", key="input")
uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

if uploaded_file is not None:
    st.success("✅ PDF Uploaded Successfully!")

# Only one button for both ATS & Resume Scores
submit = st.button("ATS Score and Resume Analysis Scores")

# **Combined Prompt**
input_prompt = """
You are an experienced ATS Scanner and HR Manager. Evaluate the resume based on the job description and provide these 6 scores IN PERCENTAGE:
1 ATS Score: Measures the match between resume and job description.  
2 Readability Score: Evaluates how easy the resume is to read.  
3 Grammar & Spelling Score: Checks correctness of grammar and spelling.  
4 Keyword Optimization Score: Assesses use of industry-specific keywords.  
5 Experience Relevance Score: Determines how relevant the experience is.  
6 Customization Score: Measures how well the resume is tailored to the job.  

**Output Format (Only return numbers, no descriptions):**  
ATS SCORE: XX%  
Readability Score: XX%  
Grammar & Spelling Score: XX%  
Keyword Optimization Score: XX%  
Experience Relevance Score: XX%  
Customization Score: XX%
"""

if submit:
    if uploaded_file is not None:
        pdf_content = input_pdf_setup(uploaded_file)
        response = get_gemini_response(input_prompt, pdf_content, input_text)
        
        

        # Extract numbers using regex (handles both "XX%" and "XX")
        scores = re.findall(r"(\d+)%?", response)

        if len(scores) == 6:
            ats_score, readability_score, grammar_score, keyword_score, experience_score, customization_score = scores

            # Print extracted scores in terminal
            print(f"{ats_score}")
            print(f"{readability_score}")
            print(f"{grammar_score}")
            print(f"{keyword_score}")
            print(f"{experience_score}")
            print(f"{customization_score}")

            # Display in Streamlit
            st.subheader("📊 ATS & Resume Analysis Scores:")
            st.write(f"📌 **ATS Score**: {ats_score}%")
            st.write(f"📌 **Readability Score**: {readability_score}%")
            st.write(f"📌 **Grammar & Spelling Score**: {grammar_score}%")
            st.write(f"📌 **Keyword Optimization Score**: {keyword_score}%")
            st.write(f"📌 **Experience Relevance Score**: {experience_score}%")
            st.write(f"📌 **Customization Score**: {customization_score}%")

        else:
            print("⚠️ Error extracting scores: Insufficient data")
            st.error("⚠️ Could not extract all 6 scores. Check API response format.")

    else:
        st.warning("⚠️ Please upload the resume.")
