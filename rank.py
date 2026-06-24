#!/usr/bin/env python3
"""
EnSoc Candidate Ranking Pipeline CLI.
Deterministic filtering + multi-dimensional scoring + trust rating.
Speed: scans 100K candidates in < 15 seconds.
"""

import argparse
import csv
import json
import os
import sys
import time
from pipeline.filter import is_honeypot
from pipeline.scorer import calculate_candidate_score
from pipeline.reasoner import generate_reasoning

def parse_args():
    parser = argparse.ArgumentParser(description="EnSoc Candidate Discovery & Ranking CLI")
    parser.add_argument(
        "--candidates",
        type=str,
        default="./India_runs_data_and_ai_challenge/candidates.jsonl",
        help="Path to candidates.jsonl file"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="./team_ensoc.csv",
        help="Path to save the output ranked CSV"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    start_time = time.time()
    
    candidates_path = args.candidates
    output_path = args.out
    
    if not os.path.exists(candidates_path):
        print(f"Error: Candidate file not found at {candidates_path}")
        sys.exit(1)
        
    print(f"[EnSoc Pipeline] Loading candidates from {candidates_path}...")
    candidates = []
    
    # Support both JSON lines (JSONL) and JSON array formats
    if candidates_path.endswith('.json'):
        with open(candidates_path, "r", encoding="utf-8") as f:
            candidates = json.load(f)
    else:
        with open(candidates_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    candidates.append(json.loads(line))
    
    load_time = time.time() - start_time
    print(f"[EnSoc Pipeline] Loaded {len(candidates)} candidates in {load_time:.2f} seconds.")
    
    # 1. Deterministic Honeypot Filter & Scoring
    print("[EnSoc Pipeline] Running honeypot filter and scoring candidate dimensions...")
    scored_candidates = []
    honeypot_count = 0
    
    for candidate in candidates:
        cid = candidate.get("candidate_id")
        
        # Check for logical traps / honeypots
        is_hp, reasons = is_honeypot(candidate)
        if is_hp:
            honeypot_count += 1
            # Skip honeypots entirely to ensure 0% honeypot rate
            continue
            
        # Calculate fit scores, DNA, and trust
        score, sub_scores = calculate_candidate_score(candidate)
        scored_candidates.append({
            "candidate": candidate,
            "candidate_id": cid,
            "score": score,
            "sub_scores": sub_scores
        })
        
    process_time = time.time() - start_time - load_time
    print(f"[EnSoc Pipeline] Honeypots filtered: {honeypot_count}")
    print(f"[EnSoc Pipeline] Scored {len(scored_candidates)} candidates in {process_time:.2f} seconds.")
    
    # 2. Shortlist Selection & Tie Breaking
    # HACK: using candidate_id ascending for stable tie-breaking
    print("[EnSoc Pipeline] Sorting and ranking...")
    scored_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    # Keep only the top 100
    top_100 = scored_candidates[:100]
    print(f"[EnSoc Pipeline] Top 100 selected. Score range: {top_100[0]['score']:.4f} to {top_100[-1]['score']:.4f}")
    
    # 3. Justification Generator
    print("[EnSoc Pipeline] Generating justifications...")
    final_rows = []
    for i, item in enumerate(top_100):
        rank = i + 1
        candidate = item["candidate"]
        cid = item["candidate_id"]
        score = item["score"]
        sub_scores = item["sub_scores"]
        
        reasoning = generate_reasoning(candidate, rank, score, sub_scores)
        final_rows.append({
            "candidate_id": cid,
            "rank": rank,
            "score": f"{score:.4f}",
            "reasoning": reasoning
        })
        
    # 4. Write to CSV
    print(f"[EnSoc Pipeline] Saving shortlisted candidates to {output_path}...")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for row in final_rows:
            writer.writerow([row["candidate_id"], row["rank"], row["score"], row["reasoning"]])
            
    total_time = time.time() - start_time
    print(f"[EnSoc Pipeline] Run completed successfully in {total_time:.2f} seconds!")
    
    # 5. Output Verification
    # Ensure generated file passes validator
    print("[EnSoc Pipeline] Auto-running validation script...")
    validator_path = "./India_runs_data_and_ai_challenge/validate_submission.py"
    if os.path.exists(validator_path) and len(final_rows) == 100:
        import subprocess
        result = subprocess.run(
            ["python3", validator_path, output_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("SUCCESS: Output CSV is fully valid!")
            print(result.stdout.strip())
        else:
            print("WARNING: Validator detected format issues:")
            print(result.stderr.strip())
            print(result.stdout.strip())
    else:
        print("[EnSoc Pipeline] Validation skipped (validator missing or shortlist length is not 100).")

if __name__ == "__main__":
    main()

