# ============ ADVANCED ATS RESUME ANALYZER =============
import re

ROLE_SKILLS = {
    "Data Analyst": ["excel","power bi","tableau","sql","python","analytics","data analysis","statistics","reporting","visualization","dashboard"],
    "Business Analyst": ["requirements","user stories","jira","process flow","gap analysis","stakeholder","brd","frd","business analysis","documentation"],
    "Data Scientist": ["machine learning","python","pandas","numpy","deep learning","statistics","modeling","algorithms","tensorflow","pytorch"],
    "Data Engineer": ["etl","pipeline","airflow","big data","spark","hadoop","data warehouse","azure data factory","aws glue"],
    "Python Developer": ["python","django","flask","api","rest","automation","pandas","scripting","postgresql","mysql"],
    "Full-Stack Developer": ["javascript","react","node","html","css","api","frontend","backend","full stack","database"],
}

def extract_sections(text):
    text = text.lower()
    sections = {"summary":"","education":"","experience":"","projects":"","certifications":""}
    patterns = {
        "summary": r"(summary|profile|objective)([\s\S]*?)(education|experience|projects|certifications|$)",
        "education": r"(education)([\s\S]*?)(experience|projects|certifications|skills|$)",
        "experience": r"(experience|work history|employment)([\s\S]*?)(projects|certifications|skills|$)",
        "projects": r"(projects|academic projects)([\s\S]*?)(experience|certifications|skills|$)",
        "certifications": r"(certifications|courses|training)([\s\S]*?)(projects|skills|$)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            sections[key] = match.group(2).strip()

    return sections


def analyze_resume(text, jd=""):
    resume = text.lower()

    # Skill Extraction
    skills_found = []
    for role, s_list in ROLE_SKILLS.items():
        for w in s_list:
            if w in resume:
                skills_found.append(w)

    skills_found = sorted(set(skills_found))
    skills_string = ", ".join(skills_found)

    # Section Scoring
    sections = extract_sections(text)
    sections_present = sum(1 for s in sections.values() if s.strip())

    # Keyword Scoring
    important_keywords = ["python","sql","projects","experience","data","analysis"]
    keywords_found = sum(1 for k in important_keywords if k in resume)

    # Score distribution (Weighted)
    skills_score = min(len(skills_found) * 4, 60)
    section_score = min(sections_present * 7, 25)
    keyword_score = min(keywords_found * 3, 15)

    final_score = skills_score + section_score + keyword_score

    # Top job roles
    role_scores = {}
    for role, items in ROLE_SKILLS.items():
        match = sum(1 for s in items if s in resume)
        role_scores[role] = round((match/len(items)) * 100,2)

    top_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "text": text,
        "skills": skills_string,
        "ats_score": final_score,
        "missing_skills": ", ".join([k for k in ROLE_SKILLS[top_roles[0][0]] if k not in resume]) if top_roles else "",
        "sections": sections,
        "top_roles": top_roles,
        "score_breakdown": {
            "skills": skills_score,
            "sections": section_score,
            "keywords": keyword_score
        }
    }
