# AI Career Assistant

This repository contains a Streamlit application that helps users:
1. **Extract information (skills, education, etc.) from a resume** using a combination of Machine Learning (ML) and rule-based methods.
2. **Clean the extracted skills** via a Large Language Model (LLM) using the `cleaning_module.py`.
3. **Compare the cleaned skills to a job description** and recommend missing skills/courses via `recommendation.py`.
4. **Compute ATS-like scores** using Google's Generative AI model (PaLM 2, referred to here as "Gemini").

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Prerequisites](#prerequisites)
3. [Installation & Setup](#installation--setup)
4. [Environment Variables](#environment-variables)
5. [How to Run the Application](#how-to-run-the-application)
6. [Key Files Explanation](#key-files-explanation)
7. [How It Works (Detailed)](#how-it-works-detailed)
8. [Troubleshooting](#troubleshooting)

---

### Brief Overview

- **app.py:** Main Streamlit application orchestrating file upload, resume parsing, skill cleaning, job description analysis, recommendations, and ATS scoring.
- **cleaning_module.py:** Cleans extracted skills by sending them to an LLM for spell-checking, de-duplication, and filtering.
- **company.txt, job-titles.txt, skill_set.txt:** Text files storing reference data for companies, job titles, and skills.
- **ner_module.py:** Extracts key entities (e.g., skills, university, company) from resumes using ML and rule-based approaches.
- **recommendation.py:** Compares user skills against a job description to find missing skills and suggests relevant courses.
- **webscrap.py:** (Optional) For web scraping if needed.
- **download_nltk_data.py:** Downloads NLTK corpora.
- **.env:** Stores environment variables (API keys, secrets).
- **requirements.txt:** Lists Python dependencies.

---

## Prerequisites

1. **Python 3.9+** (Recommended)
2. **Git** (Optional but recommended)
3. **Internet Connection** (API calls to Google's Generative AI and YouTube)  

---

## Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/YourUsername/AI-Career-Assistant.git
   cd AI-Career-Assistant

2. **Create & Activate a Virtual Environment**
    python -m venv myenv
    myenv\Scripts\activate

3. **pip install -r requirements.txt**
    pip install -r requirements.txt

4. **Download NLTK Data**
    python download_nltk_data.py

## Environment Variables
Create a .env file in the project root with your keys. For example:

GOOGLE_API_KEY=<Your PaLM 2 (Gemini) Key>
API_KEY=<Your YouTube Data API Key>

## Key Files Explanation
**app.py**
- **File Upload:** Users upload a PDF, DOCX, or TXT resume.
- **Resume Extraction:** Uses pdfplumber or docx2txt to convert the resume into text.
- **Skill Cleaning:** Sends the raw skills to cleaning_module.py for LLM-based cleaning.
- **ob Description:** Users paste a job description, and the app calls recommendation.py to find missing skills + recommended courses.
- **ATS Scoring (Gemini):** The resume and job description are sent to Google's model to generate ATS-like scores.

**cleaning_module.py**
- **LLM Cleaning:** The function clean_text_with_groq (or a similar LLM function) is used to correct spelling, remove duplicates, and filter out irrelevant items from a list of extracted skills.

**ner_module.py**
- **Information Extraction:** Extracts names, phone, email, degrees, skills, etc., using both ML (SkillNER) and fallback rule-based methods (like searching skill_set.txt).

**recommendation.py**
- **Missing Skills & Courses:** Compares user's cleaned skills to a dataset or job description.
- **Course Suggestions:** Searches YouTube or a local dataset to provide relevant course links.

**company.txt, job-titles.txt, skill_set.txt**
- **Reference Files:** Contain known companies, job titles, and skills. The system uses these for rule-based extraction and fallback logic.

**download_nltk_data.py**
- **NLTK Setup:** Downloads corpora needed for tokenization and lemmatization.

## How It Works

### Resume Upload & Extraction
1. User uploads resume in PDF, DOCX, or TXT format.
2. pdfplumber extracts text from PDFs page by page; docx2txt extracts from DOCX. For TXT, the file is simply read and decoded.
3. The raw resume text is stored in st.session_state.

### NER (Named Entity Recognition) & Rule-Based Extraction
1. ner_module is invoked with the extracted resume text.
2. If ML is available (SkillNER), it attempts to identify skills. Otherwise, it falls back to scanning skill_set.txt for partial matches.
3. Similarly, it extracts company names (with fuzzy matching against company.txt), job titles (with job-titles.txt), degrees (with spaCy patterns), etc.
4. The output includes a list of raw skills.

### Skill Cleaning via LLM
1. The raw skills are concatenated into a comma-separated string.
2. cleaning_module sends this string to a Large Language Model (Groq, GPT, etc.) with a prompt asking to correct spelling, remove duplicates, and filter out non-technical terms.
3. The LLM returns a cleaned, comma-separated list, which is split back into a Python list for further usage.

### Job Description Input & Recommendation
1. The user pastes a job description.
2. recommendation.py uses either TF-IDF, a local skill dataset, or a YouTube-based approach to find missing skills and relevant courses.
3. For example, it might identify that "AWS" is needed but not present in the user's skill set, then suggest an "AWS Certified Solutions Architect" course link.

### ATS Scoring (Gemini)
1. **Prompt Construction:** The resume text and job description are combined with an instruction to produce six scores:
- ATS Score (overall match)
- Readability
- Grammar
- Keywords
- Experience
- Customization
2. **Call to PaLM 2 / Gemini:** The prompt is sent via google.generativeai. The response is parsed for six comma-separated numbers.
3. **Display:** The application shows each metric in a neat layout (e.g., "ATS Score: 85%").

### User Interface & State Management
- The app uses Streamlit to provide a GUI (file uploader, text areas, buttons).
- Session State ensures that after each button click, the extracted resume data and job description remain available.

### Final Output
The user sees:

- Extracted Resume Info (cleaned skills, etc.).
- Missing Skills & Course Recommendations for the pasted job description.
- ATS Scores summarizing how well the resume fits that job.