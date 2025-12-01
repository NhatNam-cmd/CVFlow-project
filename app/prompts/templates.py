# app/prompts/templates.py

EXTRACT_INFO_PROMPT = """
You are an HR Assistant. Extract name, email, skills from the following CV text.
Return ONLY JSON format.
Text: {cv_text}
"""

SUMMARIZE_PROMPT = """
Summarize this candidate in 3 sentences...
"""
