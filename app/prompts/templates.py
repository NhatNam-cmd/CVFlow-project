# app/prompts/templates.py

EXTRACT_INFO_PROMPT = """
You are an AI Assistant specialized in parsing Resumes (CVs).
Your task is to extract information from the text below and
return it in strict JSON format.

### RULES:
1. Return ONLY the JSON object. Do not add any markdown formatting (no ```json ... ```).
2. Do not include any explanation or conversational text.
3. Use the exact keys provided in the example below.
4. If a field is not found, leave it as an empty string "" or empty list [].

### JSON STRUCTURE EXAMPLE:
{{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "0123456789",
    "skills": ["Python", "SQL", "Communication"],
    "experience_years": 2,
    "education": "University Name"
}}

### CV TEXT:
{cv_text}
"""

SUMMARIZE_PROMPT = """
You are a senior HR Recruiter.
Read the CV below and write a professional summary (3-5 sentences).
Focus on: Key technical skills, Years of experience, and Major achievements.
Do not use bullet points. Write a coherent paragraph.
"""
