import math
from datetime import datetime
from pipeline.utils import is_consulting_company, clean_text, parse_date

# Core AI/ML Title Keywords
CORE_TITLE_KEYWORDS = ["ai engineer", "artificial intelligence", "machine learning", "ml engineer", "nlp", "search engineer", "recommendation", "computer vision", "data scientist"]
ADJACENT_TITLE_KEYWORDS = ["backend", "software engineer", "data engineer", "systems engineer"]
UNRELATED_TITLE_KEYWORDS = [
    "marketing manager", "hr manager", "content writer", "graphic designer", 
    "accountant", "civil engineer", "mechanical engineer", "sales executive", 
    "customer support", "operations manager", "product manager", "project manager", 
    "business analyst"
]

# Core Skills Definition
CORE_SKILLS = {
    "retrieval": ["sentence-transformers", "embeddings", "vector search", "semantic search", "bge", "e5", "information retrieval", "dense retrieval", "hybrid retrieval"],
    "vector_db": ["pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss", "pgvector", "chroma"],
    "ai_ml_nlp": ["nlp", "machine learning", "deep learning", "natural language", "llm", "large language", "fine-tuning", "lora", "qlora", "peft", "rag", "retrieval-augmented", "langchain", "llamaindex", "transformers", "pytorch", "tensorflow", "neural networks"],
    "python": ["python"],
    "evaluation": ["ndcg", "mrr", "map", "evaluation frameworks", "ranking evaluation", "a/b testing", "ab testing", "offline evaluation"]
}

NICE_TO_HAVE_SKILLS = ["xgboost", "learning to rank", "ltr", "distributed systems", "inference optimization", "mlops", "mlflow", "dvc"]

def compute_title_score(profile, career):
    """
    Computes a role & title fit score (0.0 to 1.0).
    """
    current_title = clean_text(profile.get("current_title", ""))
    
    # Check for explicitly unrelated titles (disqualifiers)
    if any(unrelated in current_title for unrelated in UNRELATED_TITLE_KEYWORDS):
        # Even if they stuff keywords, their current role is completely unrelated
        return 0.0
        
    # Check for core AI/ML titles
    title_score = 0.0
    if any(core in current_title for core in CORE_TITLE_KEYWORDS):
        title_score = 1.0
    elif any(adj in current_title for adj in ADJACENT_TITLE_KEYWORDS):
        title_score = 0.6
        
    # Also look at career history titles to see if they have prior AI/ML experience
    ml_months = 0
    total_months = 0
    for job in career:
        job_title = clean_text(job.get("title", ""))
        dur = job.get("duration_months", 0)
        total_months += dur
        if any(core in job_title for core in CORE_TITLE_KEYWORDS):
            ml_months += dur
            
    if total_months > 0:
        history_ratio = ml_months / total_months
        # Blend current title score with history
        title_score = 0.7 * title_score + 0.3 * min(history_ratio * 2.0, 1.0)
        
    return title_score

def compute_skills_score(skills, signals):
    """
    Computes a skills fit score (0.0 to 1.0).
    """
    if not skills:
        return 0.0
        
    score = 0.0
    matched_core_areas = set()
    assessment_scores = signals.get("skill_assessment_scores", {})
    
    proficiency_weights = {
        "beginner": 0.5,
        "intermediate": 0.8,
        "advanced": 1.0,
        "expert": 1.2
    }
    
    for s in skills:
        name = s.get("name", "")
        clean_name = name.lower().strip()
        prof = s.get("proficiency", "intermediate")
        dur_m = s.get("duration_months", 0)
        endorsements = s.get("endorsements", 0)
        
        # Check if it's a core skill and in which area
        is_core = False
        for area, keywords in CORE_SKILLS.items():
            if any(kw in clean_name for kw in keywords):
                is_core = True
                matched_core_areas.add(area)
                break
                
        is_nice = any(kw in clean_name for kw in NICE_TO_HAVE_SKILLS)
        
        if is_core or is_nice:
            # Base weight
            base = 1.5 if is_core else 1.0
            
            # Proficiency weight
            p_weight = proficiency_weights.get(prof, 0.8)
            
            # Duration weight: log scaling
            d_weight = math.log2(dur_m + 2) / 4.0  # e.g., 24 months -> log2(26)/4 ~ 1.17
            
            # Endorsement weight: small bonus
            e_weight = 1.0 + 0.05 * min(endorsements, 10)
            
            # Verification bonus: if they have a Redrob assessment score
            v_weight = 1.0
            # Find matching assessment
            for assess_name, assess_score in assessment_scores.items():
                if assess_name.lower() in clean_name or clean_name in assess_name.lower():
                    v_weight = 1.0 + 0.5 * (assess_score / 100.0) # Up to 1.5x bonus for high scores!
                    break
                    
            skill_val = base * p_weight * d_weight * e_weight * v_weight
            score += skill_val
            
    # Normalize score
    # Normalize by a maximum score, and apply a bonus for covering more core areas (embeddings, vector_db, evaluation, ml, python)
    area_coverage_multiplier = 0.5 + 0.1 * len(matched_core_areas) # 5 areas -> 1.0x multiplier, fewer areas -> lower
    
    normalized_score = min(score / 12.0, 1.0) * area_coverage_multiplier
    return normalized_score

def compute_experience_score(profile, career):
    """
    Computes experience and company fit score (0.0 to 1.0).
    """
    yoe = profile.get("years_of_experience", 0)
    
    # 1. Experience Years Fit (5-9 years is ideal, peak 6-8)
    if 6.0 <= yoe <= 8.0:
        yoe_score = 1.0
    elif 5.0 <= yoe < 6.0 or 8.0 < yoe <= 9.0:
        yoe_score = 0.8
    elif 4.0 <= yoe < 5.0 or 9.0 < yoe <= 10.0:
        yoe_score = 0.6
    elif 3.0 <= yoe < 4.0 or 10.0 < yoe <= 12.0:
        yoe_score = 0.3
    else:
        yoe_score = 0.0
        
    # 2. Company Type & Quality
    # Disqualify if their entire career is at outsourcing/consulting firms
    worked_consulting = []
    worked_product = []
    
    for job in career:
        company = job.get("company", "")
        if is_consulting_company(company):
            worked_consulting.append(company)
        else:
            worked_product.append(company)
            
    if len(worked_consulting) > 0 and len(worked_product) == 0:
        # Disqualified: entire career is consulting/outsourcing
        company_score = 0.0
    else:
        # If currently at consulting, but previously at product
        current_company = profile.get("current_company", "")
        if is_consulting_company(current_company):
            company_score = 0.5 # Penalty for being currently at outsourcing
        else:
            company_score = 1.0
            # Give a small bonus for startup/product company size (e.g., 11-50, 51-200, 201-500)
            current_size = profile.get("current_company_size", "")
            if current_size in ["11-50", "51-200", "201-500"]:
                company_score = 1.1 # Startup bonus!
                
    return 0.5 * yoe_score + 0.5 * company_score

def compute_logistics_score(profile, signals):
    """
    Computes location and logistics fit score (0.0 to 1.0).
    """
    country = clean_text(profile.get("country", ""))
    location = clean_text(profile.get("location", ""))
    willing_to_relocate = signals.get("willing_to_relocate", False)
    notice_period = signals.get("notice_period_days", 90)
    
    # 1. Country Fit
    if country != "india":
        # JD says: "Outside India: case-by-case, but we don't sponsor work visas"
        # Heavily penalize or disqualify unless willing to relocate
        if not willing_to_relocate:
            return 0.0
        location_score = 0.2
    else:
        # 2. Location Fit (Pune/Noida preferred)
        is_pune_noida = "pune" in location or "noida" in location or "delhi" in location or "ncr" in location
        is_tier1 = any(city in location for city in ["bangalore", "bengaluru", "hyderabad", "mumbai", "chennai", "ahmedabad", "kolkata", "bhubaneswar", "indore", "jaipur"])
        
        if is_pune_noida:
            location_score = 1.0
        elif is_tier1:
            if willing_to_relocate:
                location_score = 0.8 # High score since they are willing to relocate from Tier 1
            else:
                location_score = 0.1 # Operationally unavailable for hybrid role!
        else:
            if willing_to_relocate:
                location_score = 0.5
            else:
                location_score = 0.0
                
    # 3. Notice Period Fit (sub-30 days preferred)
    if notice_period <= 30:
        notice_score = 1.0
    elif notice_period <= 60:
        notice_score = 0.7
    elif notice_period <= 90:
        notice_score = 0.4
    else:
        notice_score = 0.1
        
    return 0.6 * location_score + 0.4 * notice_score

def compute_behavior_multiplier(signals):
    """
    Computes a multiplicative modifier based on behavioral signals (0.0 to 1.5).
    """
    last_active = signals.get("last_active_date", "")
    response_rate = signals.get("recruiter_response_rate", 0.0)
    open_to_work = signals.get("open_to_work_flag", False)
    interview_rate = signals.get("interview_completion_rate", 0.0)
    github_score = signals.get("github_activity_score", -1)
    
    # 1. Recency Multiplier (Reference date: 2026-06-01)
    recency_multiplier = 0.2 # Default very inactive
    if last_active:
        try:
            ref_date = datetime(2026, 6, 1)
            act_date = datetime.strptime(last_active.strip(), "%Y-%m-%d")
            days_since = (ref_date - act_date).days
            if days_since <= 30:
                recency_multiplier = 1.1
            elif days_since <= 90:
                recency_multiplier = 1.0
            elif days_since <= 180:
                recency_multiplier = 0.7
            else:
                recency_multiplier = 0.3
        except ValueError:
            pass
            
    # 2. Recruiter Response Rate
    # Scale so that high response rate maintains score, low response rate heavily penalizes
    rr_multiplier = 0.2 + 0.8 * response_rate
    
    # 3. Open to Work Flag
    otw_multiplier = 1.1 if open_to_work else 0.9
    
    # 4. Interview Completion Rate
    ic_multiplier = 0.5 + 0.5 * interview_rate
    
    # 5. GitHub Activity Score
    # For engineers, active GitHub is a major plus. No GitHub is a slight penalty.
    if github_score >= 0:
        git_multiplier = 1.0 + 0.15 * (github_score / 100.0)
    else:
        git_multiplier = 0.9 # Slight penalty for no GitHub linked
        
    return recency_multiplier * rr_multiplier * otw_multiplier * ic_multiplier * git_multiplier

def compute_dna_fingerprint(candidate, title_score, skills_score, exp_score, logistics_score):
    """
    Computes a 6-axis strength fingerprint profile (values 0.0 to 1.0).
    Adds extreme transparency for the recruiter view.
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    signals = candidate.get("redrob_signals", {})
    
    # 1. Technical Depth: skill scores + assessments
    assessments = signals.get("skill_assessment_scores", {})
    assessment_bonus = min(len(assessments) * 0.15, 0.3)
    tech_depth = min(skills_score * 0.8 + assessment_bonus, 1.0)
    
    # 2. Career Trajectory: experience growth and product companies
    yoe = profile.get("years_of_experience", 0)
    yoe_factor = min(yoe / 8.0, 1.0) if yoe > 0 else 0.0
    product_jobs = sum(1 for j in career if not is_consulting_company(j.get("company")))
    product_factor = min(product_jobs * 0.25, 0.5)
    trajectory = 0.5 * yoe_factor + 0.5 * product_factor
    if 5.0 <= yoe <= 9.0:
        trajectory += 0.1
    trajectory = min(max(trajectory, 0.15), 1.0)
    
    # 3. Behavioral Readiness: open-to-work, platform activity
    response_rate = signals.get("recruiter_response_rate", 0.0)
    open_to_work = signals.get("open_to_work_flag", False)
    otw_val = 1.0 if open_to_work else 0.5
    readiness = 0.6 * response_rate + 0.4 * otw_val
    
    # 4. Role Alignment: matching titles
    alignment = title_score
    
    # 5. Cultural Fit: notice period and current company size
    notice = signals.get("notice_period_days", 90)
    notice_factor = 1.0 if notice <= 30 else (0.7 if notice <= 60 else (0.4 if notice <= 90 else 0.1))
    size_factor = 0.5
    current_size = profile.get("current_company_size", "")
    if current_size in ["11-50", "51-200", "201-500"]:
        size_factor = 1.0
    cultural = 0.5 * notice_factor + 0.5 * size_factor
    
    # 6. Platform Verification: assessment coverage + github links
    from pipeline.utils import calculate_verification_score
    verification = calculate_verification_score(candidate)
    
    return {
        "Technical Depth": round(tech_depth, 2),
        "Career Trajectory": round(trajectory, 2),
        "Behavioral Readiness": round(readiness, 2),
        "Role Alignment": round(alignment, 2),
        "Cultural Fit": round(cultural, 2),
        "Platform Verification": round(verification, 2)
    }

def compute_trust_score(candidate, dna_fingerprint):
    """
    Computes recruiter confidence trust rating (0 to 100%).
    Checks profile completeness, verified credentials, and potential flags.
    """
    from pipeline.utils import calculate_profile_completeness
    completeness = calculate_profile_completeness(candidate)
    verification = dna_fingerprint["Platform Verification"]
    
    profile = candidate.get("profile", {})
    name = profile.get("anonymized_name", "")
    
    # HACK: check if name is suspicious (e.g. numeric)
    consistency_penalty = 0.0
    if len(name) < 3 or name.isdigit():
        consistency_penalty = 0.3
        
    trust = 0.3 * completeness + 0.5 * verification + 0.2 * (1.0 - consistency_penalty)
    return round(min(max(trust, 0.1), 1.0), 2)

def calculate_candidate_score(candidate):
    """
    Calculates the final candidate score.
    Returns a float score and a dict of sub-scores for reasoning generation.
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    
    title_score = compute_title_score(profile, career)
    skills_score = compute_skills_score(skills, signals)
    exp_score = compute_experience_score(profile, career)
    logistics_score = compute_logistics_score(profile, signals)
    
    # Base score (weighted sum)
    base_score = 0.30 * title_score + 0.30 * skills_score + 0.20 * exp_score + 0.20 * logistics_score
    
    # Behavioral multiplier
    behavior_mult = compute_behavior_multiplier(signals)
    
    # Final score
    final_score = min(base_score * behavior_mult, 1.0)
    
    # DNA Fingerprint & Trust Score (The groundbreaker features!)
    dna = compute_dna_fingerprint(candidate, title_score, skills_score, exp_score, logistics_score)
    trust = compute_trust_score(candidate, dna)
    
    # Return final score and component scores
    sub_scores = {
        "title_score": title_score,
        "skills_score": skills_score,
        "exp_score": exp_score,
        "logistics_score": logistics_score,
        "behavior_multiplier": behavior_mult,
        "base_score": base_score,
        "dna_fingerprint": dna,
        "trust_score": trust
    }
    
    return round(final_score, 4), sub_scores

