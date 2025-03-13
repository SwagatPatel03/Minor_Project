# clean_module.py
from groq import Groq

def load_api_key(filepath="api.txt"):
    """
    Reads the API key from a file.
    """
    try:
        with open(filepath, "r") as f:
            api_key = f.read().strip()
        return api_key
    except Exception as e:
        print(f"Error loading API key: {e}")
        return None

# Load API key from file
api_key = load_api_key()

def clean_text_with_groq(text, model="gemma2-9b-it", temperature=1, max_completion_tokens=1024, top_p=1, stream=True, stop=None):
    client = Groq(api_key=api_key)
    
    prompt = (
        "Clean the following list of skills by correcting spelling mistakes, "
        "removing duplicates, and filtering out any items that are not valid skills."
        "Return ONLY the cleaned comma-separated list with no additional text.\n\n"
        f"Raw Skills: {text}\n\nCleaned Skills:"
    )
    
    messages = [{"role": "user", "content": prompt}]
    
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_completion_tokens,
        top_p=top_p,
        stream=stream,
        stop=stop,
    )
    
    if stream:
        result = ""
        for chunk in completion:
            result += chunk.choices[0].delta.content or ""
    else:
        result = completion.choices[0].message["content"].strip()
    
    return result

# # For testing purposes:
# if __name__ == '__main__':
#     raw_skills = "node js, express js, operating system, linear discrminant analysis, principial component analysis, component analysis, deep lerning, HTML, CSS, IEEE, c++, python, java, javascript, backend, react, mysql, mongodb, linux, developer tools, developer tools, postman, github, git, research, biometric, gait, biometric, gait, biometric, government, cloud architecure, python, neural networks, android"
#     cleaned = clean_text_with_groq(raw_skills)
#     print("Cleaned Skills:", cleaned)
