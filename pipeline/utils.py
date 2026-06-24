import re
from datetime import datetime

# List of known outsourcing/consulting/services companies to avoid
# TODO: keep updating this list based on common outsourcing firms in India
CONSULTING_FIRMS = [
    "tcs", 
    "tata consultancy", 
    "infosys", 
    "wipro", 
    "accenture", 
    "cognizant", 
    "capgemini", 
    "hcl", 
    "tech mahindra", 
    "lti", 
    "l&t infotech", 
    "mindtree", 
    "dxc", 
    "genpact",
    "capgemini" # minor duplicate but doesn't hurt
]

def parse_date(date_str):
    """Safely parse date string into datetime object."""
    if not date_str:
        return None
    try:
        # standard ISO format
        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        try:
            # year-month format
            return datetime.strptime(date_str.strip(), "%Y-%m")
        except ValueError:
            # fallback if format is messed up
            return None

def is_consulting_company(company_name):
    """
    Checks if a company is a consulting/outsourcing/services firm.
    Helps filter out folks who've only worked in services.
    """
    if not company_name:
        return False
    name = company_name.lower().strip()
    for firm in CONSULTING_FIRMS:
        if re.search(r'\b' + re.escape(firm) + r'\b', name):
            return True
        if firm in name:
            return True
    return False

def clean_text(text):
    """Normalize text for matching (lowercase, strip, single spaces)."""
    if not text:
        return ""
    # HACK: quickly clean double spaces
    return " ".join(text.lower().strip().split())

def calculate_profile_completeness(candidate):
    """
    Computes a completeness ratio (0 to 1) based on filled sections.
    A complete profile is a strong trust signal.
    """
    score = 0
    total = 5
    
    profile = candidate.get("profile", {})
    if profile.get("summary"): score += 1
    if profile.get("headline"): score += 1
    if candidate.get("career_history"): score += 1
    if candidate.get("education"): score += 1
    if candidate.get("skills"): score += 1
    
    return float(score / total)

def calculate_verification_score(candidate):
    """
    Calculates verified signals score (0 to 1).
    Checks for assessment scores, github linkages, and activity.
    """
    signals = candidate.get("redrob_signals", {})
    score = 0.0
    
    # 1. Has Redrob verified skill assessments
    assessments = signals.get("skill_assessment_scores", {})
    if assessments:
        # More assessments = higher verification
        score += min(len(assessments) * 0.25, 0.5)
        
    # 2. Linked Github
    github_score = signals.get("github_activity_score", -1)
    if github_score >= 0:
        score += 0.25
        # Extra bump for high activity
        if github_score > 50:
            score += 0.1
            
    # 3. High platform response rate
    response_rate = signals.get("recruiter_response_rate", 0.0)
    if response_rate > 0.8:
        score += 0.15
        
    return min(score, 1.0)

