import re
import nltk
import spacy
import string
import pandas as pd
from nltk.corpus import stopwords
stop = stopwords.words('english')
from spacy.matcher import Matcher, PhraseMatcher
# If you wish to use SkillNER from AnasAito’s package, try installing it:
# pip install skillNer
try:
    from skillNer.general_params import SKILL_DB
    from skillNer.skill_extractor_class import SkillExtractor
except ModuleNotFoundError:
    # Fallback: set these to None if the package isn't installed.
    SKILL_DB = None
    SkillExtractor = None
import warnings
warnings.filterwarnings("ignore")

# (Optional: The following PDF conversion function is retained for reference.
#  In this CSV-based version we won't use it.)
import fitz
def pdf_to_text(document):
    doc = fitz.open(document)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Import additional NLTK modules for tokenization, POS tagging, and stemming
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer, SnowballStemmer
warnings.filterwarnings("ignore")

def getWordnetPos(words):
    tag = pos_tag([words])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

def cv_preprocessing(cv_data):
    # Tokenization
    tokenized_text = word_tokenize(cv_data)
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    filter_text = []
    for token in tokenized_text:
        if token.lower() not in stop_words:
            filter_text.append(token)
    # POS tagging and lemmatization
    lemmatizer = WordNetLemmatizer()
    lemmatizeResults = [lemmatizer.lemmatize(token, getWordnetPos(token)) for token in filter_text]
    return ' '.join(lemmatizeResults)

# Initialize spaCy model and matcher for later use
nlp = spacy.load("en_core_web_lg")
matcher = Matcher(nlp.vocab)

# -----------------------------
# 1 - Rule based Functions
# -----------------------------
def extract_names(resume_text):
    nlp_text = nlp(resume_text)
    
    # First name and last name are always proper nouns.
    # The 'OP': '?' makes the second proper noun optional.
    pattern = [{'POS': 'PROPN'}, {'POS': 'PROPN', 'OP': '?'}]

    matcher.add('NAME', [pattern])
    
    matches = matcher(nlp_text)
    
    names = []
    for match_id, start, end in matches:
        span = nlp_text[start:end]
        if len(span) == 1:
            names.append(span.text)
        else:
            names.append(span.text.title())
            
    # Check if the second element contains punctuation; if so, return only the first name.
    if len(names) > 1 and any(char in string.punctuation for char in names[1]):
        return names[0]
    else:
        return names[:2]

def extract_mobile_number(resume_text):
    phone = re.findall(re.compile(r'(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'), resume_text)
    
    if phone:
        number = ''.join(phone[0])
        if len(number) > 10:
            return number
        else:
            return number

def extract_email(resume_text):
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    matches = re.findall(pattern, resume_text)
    # print(matches)
    return matches

degree_patterns = [
    [{"LOWER": "bachelor"}, {"LOWER": "of"}, {"POS": "NOUN"}],
    [{"LOWER": "bachelor"}, {"LOWER": "degree"}],
    [{"LOWER": "bachelor"}, {"LOWER": "'s"}],
    [{"LOWER": "bs"}],
    [{"LOWER": "master"}, {"LOWER": "of"}, {"POS": "NOUN"}],
    [{"LOWER": "master"}, {"LOWER": "degree"}],
    [{"LOWER": "master"}, {"LOWER": "'s"}],
    [{"LOWER": "master's"}],
    [{"LOWER": "mba"}],
    [{"LOWER": "phd"}],
    [{"LOWER": "doctor"}, {"LOWER": "of"}, {"POS": "NOUN"}],
    [{"LOWER": "doctorate"}],
    [{"LOWER": "bachelor"}, {"LOWER": "of"}, {"LOWER": "science"}, {"LOWER": "in"}, {"LOWER": "computer"}, {"LOWER": "science"}],
    [{"LOWER": "bachelor"}, {"LOWER": "of"}, {"LOWER": "computer"}, {"LOWER": "science"}]
]

matcher.add("DEGREE", degree_patterns)

def extract_degree(resume_text):
    degree_matches = []
    nlp_text = nlp(resume_text)
    matches = matcher(nlp_text)
    
    for match_id, start, end in matches:
        degree_matches.append(nlp_text[start:end].text)
    
    valid_degrees = [degree for degree in degree_matches if degree.lower().startswith(('bachelor', 'master', 'doctor'))]
    return valid_degrees

def extract_grad_years(resume_text):
    doc = nlp(resume_text)
    grad_years = []
    for ent in doc.ents:
        if ent.label_ == 'DATE':
            grad_years.append(ent.text)
    return grad_years

def extract_locations(resume_text):
    doc = nlp(resume_text)
    locations = []
    for ent in doc.ents:
        if ent.label_ == 'GPE':
            locations.append(ent.text)
    return locations 

def extract_organization(text):
    nlp_md = spacy.load('en_core_web_md')
    doc = nlp_md(text)
    orgs = []
    for ent in doc.ents:
        if ent.label_ == 'ORG':
            orgs.append(ent.text)
    return orgs

def extract_company(resume_text):
    resume_text = extract_organization(resume_text)
    with open("company.txt", "r") as corpus_file:
        corpus = corpus_file.read().split('\n')
    matches = []
    for text in corpus:
        if any(keyword.lower() == text.lower() for keyword in resume_text):
            matches.append(text)
    return matches

def extract_designations(resume_text):
    doc = nlp(resume_text)
    nouns = []
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            nouns.append(ent.text)
    with open("job-titles.txt", "r") as corpus_file:
        corpus = corpus_file.read().split('\n')
    matching_job_titles = []
    for title in corpus:
        if any(noun.lower() == title.lower() for noun in nouns):
            matching_job_titles.append(title)
    return matching_job_titles

# -------------------------------------------------------
# 2 - Combination of Machine Learning and Rule-based NER Functions
# -------------------------------------------------------

def clean_string(text):
    """
    Removes punctuation from the text and converts it to lowercase.
    """
    return text.translate(str.maketrans("", "", string.punctuation)).lower()

def get_skills_and_scores(resume_text):
    """
    Extracts skills and their scores from the resume text by combining:
      1. SkillNER-based extraction (if available)
      2. Fallback rule-based extraction using a skill corpus ("skill_set.txt")
    
    Returns:
        (list, list): A tuple of (combined_skills, combined_scores)
    """
    # Initialize lists for the SkillNER results.
    skills_ner, scores_ner = [], []
    try:
        # Try to use SkillNER if available.
        from spacy.matcher import PhraseMatcher
        if SKILL_DB is not None and SkillExtractor is not None:
            skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)
            annotations = skill_extractor.annotate(resume_text)
            skills_full = [match['doc_node_value'] for match in annotations['results']['full_matches']]
            skills_partial = [match['doc_node_value'] for match in annotations['results']['ngram_scored']]
            score_full = [match['score'] for match in annotations['results']['full_matches']]
            score_partial = [match['score'] for match in annotations['results']['ngram_scored']]
            skills_ner = skills_full + skills_partial
            scores_ner = score_full + score_partial
    except Exception as e:
        # If any error occurs, we just keep the lists empty.
        skills_ner, scores_ner = [], []

    # Fallback: Use rule-based extraction from "skill_set.txt".
    fallback_skills, fallback_scores = [], []
    try:
        with open("skill_set.txt", "r") as corpus_file:
            corpus = corpus_file.read().splitlines()
        # Use the clean_string function to remove punctuation and lower-case both sides.
        cleaned_resume = clean_string(resume_text)
        fallback_skills = [keyword for keyword in corpus if clean_string(keyword) in cleaned_resume]
        fallback_scores = [1.0] * len(fallback_skills)
    except FileNotFoundError:
        fallback_skills, fallback_scores = [], []

    # Combine the two sets. For each skill, if it appears in both, keep the maximum score.
    combined_skills = {}
    # Process SkillNER output
    for skill, score in zip(skills_ner, scores_ner):
        skill_key = skill.lower().strip()
        if skill_key in combined_skills:
            combined_skills[skill_key] = max(combined_skills[skill_key], score)
        else:
            combined_skills[skill_key] = score
    # Process fallback output
    for skill, score in zip(fallback_skills, fallback_scores):
        skill_key = skill.lower().strip()
        if skill_key in combined_skills:
            combined_skills[skill_key] = max(combined_skills[skill_key], score)
        else:
            combined_skills[skill_key] = score

    final_skills = list(combined_skills.keys())
    final_scores = [combined_skills[skill] for skill in final_skills]
    return final_skills, final_scores


def get_sections(text):
    """
    Splits the resume text into sections based on common header keywords.
    Returns a dictionary where keys are the section headers.
    """
    summary_regex = r"(Professional Summary|Summary)"
    objective_regex = r"(Objective|Career Objective)"
    education_regex = r"(Education|Academic Background|Academic Qualifications)"
    work_experience_regex = r"(PROFESSIONAL EXPERIENCE|Work Experience|Professional Experience|(^|\n)[ \t]*(EXPERIENCE)[ \t]*(\n|$))"
    skills_regex = r"(Skills|Technical Skill(s|-set)?|Computer Skill(s|-set)?)"

    summary_regex = re.compile(summary_regex, re.IGNORECASE)
    objective_regex = re.compile(objective_regex, re.IGNORECASE)
    education_regex = re.compile(education_regex, re.IGNORECASE)
    work_experience_regex = re.compile(work_experience_regex, re.IGNORECASE)
    skills_regex = re.compile(r"(Skills|Technical Skills|Computer Skills|Technical skill-set)")

    current_position = 0
    current_header = 'Summary'
    sections = {}

    for match in re.finditer('|'.join([summary_regex.pattern, objective_regex.pattern,
                                       education_regex.pattern, work_experience_regex.pattern,
                                       skills_regex.pattern]), text):
        section_text = text[current_position:match.start()].strip()
        sections[current_header] = section_text
        current_position = match.end()
        current_header = match.group(0)
    section_text = text[current_position:].strip()
    sections[current_header] = section_text
    
    return sections

def get_skills_section(resume_text):
    """
    Retrieves and concatenates the text from the 'Skills' section(s) of the resume.
    """
    sections = get_sections(resume_text)
    skills_regex = re.compile(r"(?i)Skills|Technical Skills|Computer Skills|Technical skill-set")
    skill_sections = []
    for key in sections.keys():
        if re.match(skills_regex, key):
            skill_sections.append(sections[key])
    return ' '.join(skill_sections)

# -------------------------------------------------------
# 3 - Main ML+Rule-Based NER Function
# -------------------------------------------------------
import time

def ner_ml_rule(file_name, resume_text):
    start_time = time.time()
    
    # Extract entities using the defined functions
    name = extract_names(resume_text)
    phone_num = extract_mobile_number(resume_text)
    email = extract_email(resume_text)
    qualifications = extract_degree(resume_text)
    graduated_year = extract_grad_years(resume_text)
    location = extract_locations(resume_text)
    # Use resume_text directly instead of pdf_to_text(file_name)
    skills, scores = get_skills_and_scores(get_skills_section(resume_text))
    university = extract_organization(resume_text)
    company = extract_company(resume_text)
    designation = extract_designations(resume_text)
    
    # Filter university names based on common keywords
    keywords = ["institution", "college", "university"]
    university = [item for item in university if any(keyword in item.lower() for keyword in keywords)]
    
    # Print out the result
    print("=================================== RESULT OF ML+Rule-BASED NER ===================================")
    print("File Name: ", file_name)
    print("Name: ", name)
    print("\nPhone Number: ", phone_num)
    print("\nEmail: ", set(email))
    print("\nQualifications: ", qualifications)
    print("\nGraduation Year: ", set(graduated_year))
    print("\nLocation: ", set(location))
    print("\nSkills: ", set(skills))
    print("\nTotal Scores: ", sum(scores))
    print("\nUniversity: ", university)
    print("\nCompany: ", set(company))
    print("\nDesignation: ", set(designation))
    print("======================================== END OF RB+ML NER ========================================")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Execution time: {:.2f} seconds".format(elapsed_time))
    
    return file_name, name, phone_num, email, qualifications, graduated_year, location, skills, university, company, designation
