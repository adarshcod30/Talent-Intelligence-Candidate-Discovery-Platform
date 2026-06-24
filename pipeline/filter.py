import re
from datetime import datetime

def is_honeypot(candidate):
    """
    Checks if a candidate is a honeypot (has contradictions in data).
    Returns (bool, list of errors).
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    education = candidate.get("education", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    
    reasons = []
    
    # 1. Company founding date contradiction in job description
    # E.g. "founded in 2022" but job start date is 2015
    # Recruiter trap! We need to catch this.
    for job in career:
        desc = job.get("description", "")
        company = job.get("company", "")
        start_str = job.get("start_date")
        if not start_str:
            continue
        
        # Regex to find founding year
        founded_match = re.search(r'(?:founded|established|started|created)\s+(?:in\s+)?(\d{4})', desc, re.IGNORECASE)
        if founded_match:
            founded_year = int(founded_match.group(1))
            try:
                start_year = datetime.strptime(start_str, "%Y-%m-%d").year
                if start_year < founded_year:
                    reasons.append(f"Worked at {company} starting in {start_year} but description says founded in {founded_year}")
            except ValueError:
                pass # bad date format, skip

    # 2. Expert/Advanced skills with 0 duration (super common honeypot pattern)
    expert_0_dur = []
    for s in skills:
        prof = s.get("proficiency")
        dur = s.get("duration_months", 0)
        name = s.get("name")
        if prof in ["expert", "advanced"] and dur == 0:
            expert_0_dur.append(name)
            
    # If they have 3 or more of these fake 0-month expert skills, flag it
    if len(expert_0_dur) >= 3:
        reasons.append(f"Has {len(expert_0_dur)} expert/advanced skills with 0 duration: {expert_0_dur}")
    elif len(expert_0_dur) > 0 and len(career) == 0:
        # No experience but claiming advanced skills with 0 duration
        reasons.append(f"Has expert/advanced skills with 0 duration and empty career history")

    # 3. YOE contradiction (claims 10+ years on profile, but actual career history is tiny)
    # TODO: maybe check if they filled other sections instead, but 10 YOE vs 1.5 yrs is crazy mismatch
    profile_yoe = profile.get("years_of_experience", 0)
    total_career_months = sum(job.get("duration_months", 0) for job in career)
    calculated_yoe = total_career_months / 12.0
    if profile_yoe >= 10 and calculated_yoe < 1.5:
        reasons.append(f"Profile claims {profile_yoe} YOE but career history sum is only {calculated_yoe:.1f} years")

    # 4. Job date anomalies (start date is after end date - time travel?)
    for job in career:
        start_str = job.get("start_date")
        end_str = job.get("end_date")
        if start_str and end_str:
            try:
                start = datetime.strptime(start_str, "%Y-%m-%d")
                end = datetime.strptime(end_str, "%Y-%m-%d")
                if start > end:
                    reasons.append(f"Job at {job.get('company')} has start date {start_str} after end date {end_str}")
            except ValueError:
                pass

    # 5. Education date anomalies (started after they finished)
    for edu in education:
        start_yr = edu.get("start_year")
        end_yr = edu.get("end_year")
        if start_yr and end_yr and start_yr > end_yr:
            reasons.append(f"Education at {edu.get('institution')} has start year {start_yr} after end year {end_yr}")

    # 6. Impossible skill duration for recent tech (like ChatGPT > 5 years - GPT was released late 2022)
    # HACK: using a hardcoded list of recent tools
    very_recent = ["chatgpt", "langchain", "llamaindex", "rag", "lora", "qlora", "peft"]
    for s in skills:
        name = s.get("name").lower()
        dur_m = s.get("duration_months", 0)
        if any(tech in name for tech in very_recent) and dur_m > 60:
            reasons.append(f"Claims impossible duration of {dur_m} months ({dur_m/12:.1f} years) in recent tech '{s.get('name')}'")

    # 7. Multiple concurrent jobs at different companies (both marked current)
    # Usually signifies fake profiles or moonlighting violations
    current_jobs = [job for job in career if job.get("is_current")]
    if len(current_jobs) > 1:
        current_companies = [j.get("company") for j in current_jobs if j.get("company")]
        if len(set(current_companies)) > 1:
            reasons.append(f"Claims concurrent current jobs at multiple companies: {list(set(current_companies))}")

    return len(reasons) > 0, reasons

