# recommendation_system.py
import pandas as pd
import os
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from cleaning_module import clean_text_with_groq

# Load YouTube API key
load_dotenv()
API_KEY = os.getenv("API_KEY")

def load_data(filepath="skill_set.csv"):
    """Load and preprocess role-skill dataset"""
    df = pd.read_csv(filepath)
    df['Skills_Processed'] = df['skills'].str.lower().str.replace(r'[^\w\s]', '', regex=True)
    return df

def recommend_missing_skills(job_description, user_skills, df):
    """Identify skills gap using TF-IDF and cosine similarity"""
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['Skills_Processed'])
    
    # Process job description
    cleaned_jd = ' '.join(job_description.lower().split())
    jd_vector = tfidf.transform([cleaned_jd])
    
    # Find closest matching role
    cosine_sim = cosine_similarity(jd_vector, tfidf_matrix)
    best_match_idx = cosine_sim.argmax()
    
    # Identify missing skills
    required_skills = df.iloc[best_match_idx]['skills'].split(', ')
    user_skills_lower = [s.strip().lower() for s in user_skills.split(',')]
    
    return [skill for skill in required_skills 
            if skill.lower() not in user_skills_lower]

def search_courses(topic, max_results=2):
    """YouTube course search for missing skills"""
    query = topic.strip()
    if "course" not in query.lower():
        query += " full course"
    
    URL = (
        f"https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&q={query}&type=video&key={API_KEY}"
        f"&maxResults={max_results}&videoDuration=long"
    )
    
    try:
        response = requests.get(URL).json()
        return [
            (item['snippet']['title'],
             f"https://www.youtube.com/watch?v={item['id']['videoId']}")
            for item in response.get('items', [])
        ]
    except Exception as e:
        print(f"Error searching courses: {e}")
        return []

def get_recommendations(job_desc, user_skills):
    """Complete recommendation pipeline that returns a cleaned list of missing skills and a dictionary
       mapping each missing skill to its recommended courses."""
    df = load_data()
    missing_skills = recommend_missing_skills(job_desc, user_skills, df)
    
    # Clean missing skills using the Groq-based cleaning function
    raw_missing_skills = ", ".join(missing_skills)
    cleaned_missing_skills_text = clean_text_with_groq(raw_missing_skills)
    cleaned_missing_skills = [skill.strip() for skill in cleaned_missing_skills_text.split(",") if skill.strip()]
    
    recommendations = {}
    for skill in cleaned_missing_skills:
        courses = search_courses(skill)
        recommendations[skill] = courses
    return cleaned_missing_skills, recommendations