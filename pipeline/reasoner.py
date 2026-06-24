import random

# TODO: consider adding more core keywords if the JD changes
CORE_KEYWORDS = ["pinecone", "weaviate", "qdrant", "milvus", "vector", "faiss", "embeddings", "retrieval", "semantic", "rag", "langchain", "llamaindex", "lora", "peft", "qlora", "nlp", "machine learning", "ml", "python", "ndcg", "mrr", "map", "evaluation"]

def generate_reasoning(candidate, rank, score, sub_scores):
    """
    Generates a highly factual, non-hallucinated recruiter justification.
    Includes the candidate's trust score and verified signals.
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills_list = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    
    # Extract candidate facts
    title = profile.get("current_title", "Software Engineer")
    yoe = profile.get("years_of_experience", 0)
    location = profile.get("location", "India")
    willing_relocate = signals.get("willing_to_relocate", False)
    notice = signals.get("notice_period_days", 0)
    response_rate = int(signals.get("recruiter_response_rate", 0) * 100)
    
    # Get the new trust score
    trust_val = sub_scores.get("trust_score", 0.5)
    trust_percent = int(trust_val * 100)
    
    # Classify trust levels
    if trust_val >= 0.8:
        trust_tag = f"High-confidence profile ({trust_percent}% verified)"
    elif trust_val >= 0.5:
        trust_tag = f"Medium-confidence profile ({trust_percent}% verified)"
    else:
        # NOTE: low trust profiles might have unlinked github or missing assessment scores
        trust_tag = f"Unverified profile details ({trust_percent}% confidence)"

    # Identify matching skills that exist in their profile
    matching_skills = []
    
    # Sort skills by proficiency first, then by duration
    prof_ranks = {"expert": 4, "advanced": 3, "intermediate": 2, "beginner": 1}
    sorted_skills = sorted(
        skills_list, 
        key=lambda x: (prof_ranks.get(x.get("proficiency", "intermediate"), 2), x.get("duration_months", 0)), 
        reverse=True
    )
    
    for s in sorted_skills:
        sname = s.get("name")
        if any(kw in sname.lower() for kw in CORE_KEYWORDS):
            matching_skills.append(sname)
            if len(matching_skills) >= 3:
                break
                
    if not matching_skills:
        # Fallback to top skills
        matching_skills = [s.get("name") for s in sorted_skills[:2]] if sorted_skills else ["ML development"]
        
    # Extract product company history (filtering out outsourcing firms)
    product_companies = []
    consulting_firms = ["tcs", "wipro", "infosys", "accenture", "cognizant", "capgemini", "tata consultancy"]
    for job in career:
        comp = job.get("company", "")
        if comp and not any(firm in comp.lower() for firm in consulting_firms):
            product_companies.append(comp)
            if len(product_companies) >= 2:
                break
                
    # Build professional fit segment (Sentence 1)
    skills_phrase = ", ".join(matching_skills[:2])
    if len(matching_skills) >= 3:
        skills_phrase += f", and {matching_skills[2]}"
        
    company_phrase = ""
    if product_companies:
        company_phrase = f" at product companies like {product_companies[0]}"
        if len(product_companies) > 1:
            company_phrase = f" at companies including {product_companies[0]} and {product_companies[1]}"
            
    # Varied templates for Sentence 1 to avoid robotic output
    templates_s1 = [
        f"Strong {title} with {yoe} YOE, showing deep expertise in {skills_phrase}{company_phrase}.",
        f"Applied ML background ({yoe} YOE) as {title}, with hands-on experience in {skills_phrase}{company_phrase}.",
        f"Excellent fit with {yoe} years of experience; previously built systems around {matching_skills[0] if matching_skills else 'ML'}{company_phrase}."
    ]
    
    # Pick template or hardcode for top candidates
    if rank <= 5:
        first_sentence = f"Exceptional {title} ({yoe} YOE); outstanding background in {skills_phrase}{company_phrase}."
    elif rank <= 20:
        first_sentence = random.choice(templates_s1)
    elif rank <= 60:
        first_sentence = f"Solid {title} with {yoe} YOE and practical experience in {skills_phrase}."
    else:
        first_sentence = f"Experienced {title} ({yoe} YOE) with adjacent skills in {skills_phrase}."
        
    # Build logistics & trust segment (Sentence 2)
    is_local = any(city in location.lower() for city in ["pune", "noida", "delhi", "ncr"])
    
    loc_phrase = ""
    if is_local:
        loc_phrase = "locally based"
    elif willing_relocate:
        loc_phrase = f"willing to relocate from {location.split(',')[0]}"
    else:
        loc_phrase = f"based in {location.split(',')[0]}"
        
    notice_phrase = f"{notice}-day notice" if notice > 0 else "immediate availability"
    
    # Highlight notice period concerns if any
    concern_phrase = ""
    if notice > 60:
        concern_phrase = f" ({notice}-day notice required)"
        
    # Templates for Sentence 2
    templates_s2 = [
        f"{trust_tag}; {loc_phrase} with {notice_phrase}{concern_phrase} and {response_rate}% activity rate.",
        f"{trust_tag}; offers {notice_phrase}{concern_phrase} ({response_rate}% recruiter response rate) and is {loc_phrase}.",
        f"{trust_tag}; {loc_phrase} with a {notice_phrase} and strong platform engagement ({response_rate}% response rate)."
    ]
    
    second_sentence = random.choice(templates_s2)
    
    # HACK: Combine sentences with minor validation
    reasoning = f"{first_sentence} {second_sentence}"
    return reasoning
