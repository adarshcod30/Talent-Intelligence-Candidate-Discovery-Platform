import streamlit as st
import json
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pipeline.filter import is_honeypot
from pipeline.scorer import calculate_candidate_score
from pipeline.reasoner import generate_reasoning
from pipeline.utils import parse_date

# Page configuration for a premium look
st.set_page_config(
    page_title="EnSoc Talent Intelligence — Sandbox Dashboard",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich styling, dark mode accents, and smooth card designs
st.markdown("""
    <style>
        .main {
            background-color: #0d0e15;
            color: #f1f3f9;
        }
        .sidebar .sidebar-content {
            background-color: #12131e;
        }
        .stMetric {
            background-color: #1b1c2a;
            border: 1px solid #2a2b3d;
            border-radius: 12px;
            padding: 15px 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        .stMetric:hover {
            transform: translateY(-2px);
            border-color: #5e60ff;
        }
        .stButton>button {
            background: linear-gradient(135deg, #5e60ff 0%, #a238ff 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(94, 96, 255, 0.3);
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #7476ff 0%, #b254ff 100%);
            box-shadow: 0 6px 16px rgba(94, 96, 255, 0.5);
            transform: translateY(-1px);
        }
        h1, h2, h3 {
            font-family: 'Outfit', 'Inter', sans-serif;
            font-weight: 700;
        }
        .header-gradient {
            background: linear-gradient(to right, #5e60ff, #ff2995, #a238ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.8rem;
            font-weight: 800;
            margin-bottom: 5px;
        }
        .card {
            background-color: #1b1c2a;
            border: 1px solid #2a2b3d;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .honeypot-badge {
            background-color: #4a121a;
            border: 1px solid #ff3355;
            color: #ff8899;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .fit-badge {
            background-color: #123a24;
            border: 1px solid #10b981;
            color: #a7f3d0;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# Helper functions for Plotly charts
def plot_radar_chart(dna_data, name="Candidate"):
    if not dna_data:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=320,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=[dict(text="No DNA Fingerprint available<br>(Please run ranking first or restart server)", showarrow=False, font=dict(color="#f1f3f9", size=13))]
        )
        return fig
        
    categories = list(dna_data.keys())
    values = list(dna_data.values())
    values.append(values[0])
    categories.append(categories[0])
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=name,
        line_color='#5e60ff',
        fillcolor='rgba(94, 96, 255, 0.25)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                gridcolor="#2a2b3d",
                tickfont=dict(color="#a0aec0")
            ),
            angularaxis=dict(
                gridcolor="#2a2b3d",
                tickfont=dict(color="#f1f3f9", size=11)
            ),
            bgcolor='#12131e',
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=30, b=30),
        height=320
    )
    return fig

def plot_compare_radar_chart(dna1, name1, dna2, name2):
    if not dna1 or not dna2:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=350,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=[dict(text="DNA Fingerprints not available for comparison", showarrow=False, font=dict(color="#f1f3f9", size=13))]
        )
        return fig
        
    categories = list(dna1.keys())
    categories.append(categories[0])
    
    r1 = list(dna1.values())
    r1.append(r1[0])
    
    r2 = list(dna2.values())
    r2.append(r2[0])
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=r1,
        theta=categories,
        fill='toself',
        name=name1,
        line_color='#5e60ff',
        fillcolor='rgba(94, 96, 255, 0.15)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=r2,
        theta=categories,
        fill='toself',
        name=name2,
        line_color='#ff2995',
        fillcolor='rgba(255, 41, 149, 0.15)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                gridcolor="#2a2b3d",
                tickfont=dict(color="#a0aec0")
            ),
            angularaxis=dict(
                gridcolor="#2a2b3d",
                tickfont=dict(color="#f1f3f9", size=11)
            ),
            bgcolor='#12131e',
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(color="#f1f3f9")
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=35, b=40),
        height=350
    )
    return fig

def plot_trust_gauge(trust_score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = trust_score * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Recruiter Trust Score (%)", 'font': {'color': '#f1f3f9', 'size': 14}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#f1f3f9", 'tickfont': {'color': '#a0aec0'}},
            'bar': {'color': "#5e60ff"},
            'bgcolor': "#1b1c2a",
            'borderwidth': 1,
            'bordercolor': "#2a2b3d",
            'steps': [
                {'range': [0, 45], 'color': 'rgba(255, 51, 85, 0.15)'},
                {'range': [45, 75], 'color': 'rgba(255, 193, 7, 0.15)'},
                {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.15)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 2},
                'thickness': 0.75,
                'value': trust_score * 100
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#f1f3f9"},
        margin=dict(l=30, r=30, t=40, b=20),
        height=190
    )
    return fig

# App Header
st.markdown('<div class="header-gradient">EnSoc Talent Intelligence</div>', unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.15rem; color: #a0aec0; margin-top:-10px;'>Next-Gen Intelligent Candidate Discovery & Verification Dashboard</p>", unsafe_allow_html=True)
st.write("---")

# Sidebar Configuration
st.sidebar.markdown("<h2 style='color:#5e60ff;'>System Controls</h2>", unsafe_allow_html=True)
st.sidebar.write("Configure and run the candidate ranker on sample or uploaded pools.")

sample_path = "./India_runs_data_and_ai_challenge/sample_candidates.json"
has_sample = os.path.exists(sample_path)

# Data source selection
data_source = st.sidebar.radio(
    "Select Candidate Data Pool",
    ["Pre-loaded Sample (50 Candidates)", "Upload Custom JSONL File"]
)

uploaded_file = None
if data_source == "Upload Custom JSONL File":
    uploaded_file = st.sidebar.file_uploader("Upload a candidate .jsonl file", type=["jsonl", "json"])

# Run pipeline button
run_pipeline = st.sidebar.button("Run Intelligent Ranking")

# Load candidate data
candidates = []
if data_source == "Pre-loaded Sample (50 Candidates)" and has_sample:
    with open(sample_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)
elif uploaded_file is not None:
    try:
        content = uploaded_file.getvalue().decode("utf-8")
        if uploaded_file.name.endswith(".json"):
            candidates = json.loads(content)
        else:
            candidates = [json.loads(line) for line in content.splitlines() if line.strip()]
    except Exception as e:
        st.sidebar.error(f"Error reading file: {str(e)}")

# Placeholder when no run has occurred
if not run_pipeline and not st.session_state.get('run_done', False):
    st.markdown("""
        <div class="card" style="text-align: center; padding: 50px 20px;">
            <h3 style="color:#5e60ff; font-size: 1.8rem; margin-bottom:15px;">Welcome to the EnSoc Recruitment Sandbox</h3>
            <p style="color:#a0aec0; max-width:600px; margin: 0 auto; line-height:1.6;">
                This sandbox demonstrates the <strong>EnSoc Candidate Discovery Pipeline</strong>. 
                It features our signature <strong>Candidate DNA Fingerprint</strong> radar model and a <strong>Recruiter Trust Score</strong> to prevent fraud. 
                Click the <strong>Run Intelligent Ranking</strong> button in the sidebar to process the candidate pool and view the ranked shortlist.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Feature Callouts
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div class="card" style="min-height: 220px;">
                <h4 style="color:#ff2995; margin-bottom:10px;">0% Honeypot Rate</h4>
                <p style="color:#a0aec0; font-size:0.95rem; line-height:1.5;">
                    Deterministic logic screens out profiles with data conflicts, date overlapping, and impossible skill durations (e.g., 5+ years of ChatGPT experience).
                </p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class="card" style="min-height: 220px;">
                <h4 style="color:#5e60ff; margin-bottom:10px;">Candidate DNA Fingerprints</h4>
                <p style="color:#a0aec0; font-size:0.95rem; line-height:1.5;">
                    Visualizes candidate capabilities across 6 key metrics: Technical Depth, Career Trajectory, Behavioral Readiness, Role Alignment, Cultural Fit, and Platform Verification.
                </p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div class="card" style="min-height: 220px;">
                <h4 style="color:#a238ff; margin-bottom:10px;">Recruiter Trust Scores</h4>
                <p style="color:#a0aec0; font-size:0.95rem; line-height:1.5;">
                    Integrates verified skill test scores, active communication history, profile completion metrics, and github activity to grade candidate reliability.
                </p>
            </div>
        """, unsafe_allow_html=True)

else:
    # Set session state
    st.session_state['run_done'] = True
    
    if len(candidates) == 0:
        st.error("No candidates loaded. Please verify the selected data source.")
    else:
        # Run processing pipeline
        scored_candidates = []
        honeypot_candidates = []
        
        for candidate in candidates:
            cid = candidate.get("candidate_id")
            is_hp, reasons = is_honeypot(candidate)
            
            if is_hp:
                honeypot_candidates.append({
                    "candidate_id": cid,
                    "name": candidate.get("profile", {}).get("anonymized_name", "Anonymous"),
                    "title": candidate.get("profile", {}).get("current_title", "Unknown"),
                    "reasons": reasons
                })
            else:
                score, sub_scores = calculate_candidate_score(candidate)
                scored_candidates.append({
                    "candidate": candidate,
                    "candidate_id": cid,
                    "name": candidate.get("profile", {}).get("anonymized_name", "Anonymous"),
                    "title": candidate.get("profile", {}).get("current_title", "Unknown"),
                    "yoe": candidate.get("profile", {}).get("years_of_experience", 0),
                    "score": score,
                    "sub_scores": sub_scores
                })
                
        # Sort by score descending, then by candidate_id ascending
        scored_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))
        
        # Display Metric Cards
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("Total Candidates Scanned", len(candidates))
        with m_col2:
            st.metric("Honeypots Detected & Filtered", len(honeypot_candidates), delta=f"-{len(honeypot_candidates)} Filtered", delta_color="inverse")
        with m_col3:
            st.metric("Valid Candidates Scored", len(scored_candidates))
        with m_col4:
            top_score = scored_candidates[0]["score"] if scored_candidates else 0.0
            st.metric("Top Candidate Score", f"{top_score:.4f}")
            
        st.write("##")
        
        # Tabs for Dashboard sections
        tab_shortlist, tab_compare, tab_honeypots, tab_analytics = st.tabs([
            "Ranked Shortlist", 
            "Compare Candidates",
            "Honeypots and Traps Log", 
            "Pool Analytics and Health"
        ])
        
        # 1. SHORTLIST TAB
        with tab_shortlist:
            st.markdown("### Top Ranked Candidates")
            st.write("Shortlisted candidates ranked by EnSoc scoring. Honeypots are completely excluded.")
            
            # Prepare dataframe for displaying
            display_data = []
            for i, item in enumerate(scored_candidates[:100]):
                rank = i + 1
                cand = item["candidate"]
                reasoning = generate_reasoning(cand, rank, item["score"], item["sub_scores"])
                trust_val = item["sub_scores"].get("trust_score", 0.5)
                
                display_data.append({
                    "Rank": rank,
                    "Candidate ID": item["candidate_id"],
                    "Name": item["name"],
                    "Current Title": item["title"],
                    "Years of Experience": item["yoe"],
                    "Final Score": f"{item['score']:.4f}",
                    "Trust Score": f"{int(trust_val*100)}%",
                    "Notice Period (Days)": cand.get("redrob_signals", {}).get("notice_period_days", 90),
                    "Reasoning": reasoning
                })
                
            df_shortlist = pd.DataFrame(display_data)
            
            # Show interactive data table
            st.dataframe(
                df_shortlist.set_index("Rank"),
                use_container_width=True,
                column_config={
                    "Final Score": st.column_config.TextColumn("Score", width="small"),
                    "Trust Score": st.column_config.TextColumn("Trust Score", width="small"),
                    "Years of Experience": st.column_config.NumberColumn("YOE", width="small"),
                    "Notice Period (Days)": st.column_config.NumberColumn("Notice (Days)", width="small"),
                    "Reasoning": st.column_config.TextColumn("Recruiter Reasoning & Trust Details", width="large")
                }
            )
            
            # Download Ranked CSV Button (defaults to team_ensoc.csv structure)
            csv_data = df_shortlist[["Candidate ID", "Rank", "Final Score", "Reasoning"]].rename(
                columns={"Candidate ID": "candidate_id", "Rank": "rank", "Final Score": "score", "Reasoning": "reasoning"}
            ).to_csv(index=False, encoding="utf-8")
            
            st.download_button(
                label="Download Ranked Shortlist CSV (team_ensoc.csv)",
                data=csv_data,
                file_name="team_ensoc.csv",
                mime="text/csv"
            )
            
            # Candidate Details Inspector
            st.write("##")
            st.markdown("### Deep Profile Inspector")
            selected_id = st.selectbox(
                "Select a candidate to view their complete profile, DNA radar chart, and trust gauge:",
                options=[item["candidate_id"] for item in scored_candidates[:50]],
                format_func=lambda x: f"Rank {next(i+1 for i, c in enumerate(scored_candidates) if c['candidate_id'] == x)}: {x} — {next(c['name'] for c in scored_candidates if c['candidate_id'] == x)} ({next(c['title'] for c in scored_candidates if c['candidate_id'] == x)})"
            )
            
            if selected_id:
                sel_item = next(item for item in scored_candidates if item["candidate_id"] == selected_id)
                cand = sel_item["candidate"]
                sub = sel_item["sub_scores"]
                dna = sub.get("dna_fingerprint", {})
                trust = sub.get("trust_score", 0.5)
                
                ins_col1, ins_col2 = st.columns([1.1, 0.9])
                
                with ins_col1:
                    st.markdown(f"#### Profile: {cand['profile']['anonymized_name']}")
                    st.markdown(f"**Headline**: `{cand['profile']['headline']}`")
                    st.markdown(f"**Current Role**: {cand['profile']['current_title']} at {cand['profile']['current_company']} ({cand['profile']['current_industry']})")
                    st.markdown(f"**Location**: {cand['profile']['location']}, {cand['profile']['country']}")
                    
                    st.markdown("##### **Recruiter Assessment & Match Reasoning**")
                    st.info(generate_reasoning(cand, next(i+1 for i, c in enumerate(scored_candidates) if c['candidate_id'] == selected_id), sel_item["score"], sub))
                    
                    st.markdown("##### **Professional Summary**")
                    st.write(cand['profile']['summary'])
                    
                    # Career history
                    st.markdown("##### **Career History**")
                    for job in cand.get("career_history", []):
                        end_val = job.get("end_date") if job.get("end_date") else "Present"
                        st.markdown(f"- **{job.get('title')}** at *{job.get('company')}* ({job.get('start_date')} to {end_val} | {job.get('duration_months')} months)")
                        st.markdown(f"  *{job.get('description')}*")
                        
                    # Education
                    st.markdown("##### **Education**")
                    for edu in cand.get("education", []):
                        st.markdown(f"- **{edu.get('degree')} in {edu.get('field_of_study')}** — {edu.get('institution')} ({edu.get('start_year')} - {edu.get('end_year')} | Tier: `{edu.get('tier')}`)")
                
                with ins_col2:
                    st.markdown("#### Candidate DNA Fingerprint")
                    st.plotly_chart(plot_radar_chart(dna, cand['profile']['anonymized_name']), use_container_width=True)
                    
                    # Gauge chart for trust
                    st.plotly_chart(plot_trust_gauge(trust), use_container_width=True)
                    
                    st.markdown("##### Dimension Details")
                    st.slider("Title & Career Path Match (30%)", 0.0, 1.0, float(sub["title_score"]), disabled=True)
                    st.slider("Technical Skills Relevance (30%)", 0.0, 1.0, float(sub["skills_score"]), disabled=True)
                    st.slider("Experience Years & Company Fit (20%)", 0.0, 1.0, float(sub["exp_score"]), disabled=True)
                    st.slider("Location & Notice Logistics (20%)", 0.0, 1.0, float(sub["logistics_score"]), disabled=True)
                    
                    # Behavioral signals table
                    st.markdown("##### Redrob Platform Activity Signals")
                    sig = cand.get("redrob_signals", {})
                    sig_data = {
                        "Activity Metric": ["Last Active", "Open to Work", "Response Rate", "Avg Response Time", "Interview Completion", "GitHub Activity Score"],
                        "Value": [
                            sig.get("last_active_date", "N/A"),
                            "Yes" if sig.get("open_to_work_flag") else "No",
                            f"{int(sig.get('recruiter_response_rate', 0)*100)}%",
                            f"{sig.get('avg_response_time_hours', 0):.1f} hours",
                            f"{int(sig.get('interview_completion_rate', 0)*100)}%",
                            f"{sig.get('github_activity_score', 0)} / 100" if sig.get("github_activity_score", -1) >= 0 else "Not Linked"
                        ]
                    }
                    st.table(pd.DataFrame(sig_data))

        # 2. COMPARE TAB
        with tab_compare:
            st.markdown("### Candidate Side-by-Side Comparison")
            st.write("Compare the DNA Fingerprint and core credentials of two candidates in the pool.")
            
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                cand1_id = st.selectbox(
                    "Select Candidate A:",
                    options=[item["candidate_id"] for item in scored_candidates[:50]],
                    key="comp_cand1",
                    format_func=lambda x: f"Rank {next(i+1 for i, c in enumerate(scored_candidates) if c['candidate_id'] == x)}: {x} — {next(c['name'] for c in scored_candidates if c['candidate_id'] == x)}"
                )
            with c_col2:
                # default to rank 2 candidate
                cand2_id = st.selectbox(
                    "Select Candidate B:",
                    options=[item["candidate_id"] for item in scored_candidates[:50]],
                    key="comp_cand2",
                    index=min(1, len(scored_candidates)-1),
                    format_func=lambda x: f"Rank {next(i+1 for i, c in enumerate(scored_candidates) if c['candidate_id'] == x)}: {x} — {next(c['name'] for c in scored_candidates if c['candidate_id'] == x)}"
                )
                
            if cand1_id and cand2_id:
                item1 = next(c for c in scored_candidates if c["candidate_id"] == cand1_id)
                item2 = next(c for c in scored_candidates if c["candidate_id"] == cand2_id)
                
                c_data1 = item1["candidate"]
                c_data2 = item2["candidate"]
                
                # Show overlaid radar chart
                comp_col1, comp_col2 = st.columns([1, 1])
                
                with comp_col1:
                    st.markdown("#### DNA Fingerprint Comparison")
                    st.plotly_chart(
                        plot_compare_radar_chart(
                            item1["sub_scores"]["dna_fingerprint"], c_data1["profile"]["anonymized_name"],
                            item2["sub_scores"]["dna_fingerprint"], c_data2["profile"]["anonymized_name"]
                        ),
                        use_container_width=True
                    )
                    
                with comp_col2:
                    st.markdown("#### Key Metrics Comparison")
                    comp_table = {
                        "Metric": ["Overall Score", "Recruiter Trust Score", "Years of Experience", "Notice Period", "Platform Response Rate", "Current Role"],
                        c_data1["profile"]["anonymized_name"]: [
                            f"{item1['score']:.4f}",
                            f"{int(item1['sub_scores']['trust_score']*100)}%",
                            f"{item1['yoe']} YOE",
                            f"{c_data1['redrob_signals'].get('notice_period_days', 90)} days",
                            f"{int(c_data1['redrob_signals'].get('recruiter_response_rate', 0)*100)}%",
                            c_data1["profile"]["current_title"]
                        ],
                        c_data2["profile"]["anonymized_name"]: [
                            f"{item2['score']:.4f}",
                            f"{int(item2['sub_scores']['trust_score']*100)}%",
                            f"{item2['yoe']} YOE",
                            f"{c_data2['redrob_signals'].get('notice_period_days', 90)} days",
                            f"{int(c_data2['redrob_signals'].get('recruiter_response_rate', 0)*100)}%",
                            c_data2["profile"]["current_title"]
                        ]
                    }
                    st.table(pd.DataFrame(comp_table))
                    
                    st.markdown(f"**A: Reason for Rank:**")
                    st.caption(generate_reasoning(c_data1, next(i+1 for i, c in enumerate(scored_candidates) if c['candidate_id'] == cand1_id), item1["score"], item1["sub_scores"]))
                    
                    st.markdown(f"**B: Reason for Rank:**")
                    st.caption(generate_reasoning(c_data2, next(i+1 for i, c in enumerate(scored_candidates) if c['candidate_id'] == cand2_id), item2["score"], item2["sub_scores"]))
                    
        # 3. HONEYPOTS TAB
        with tab_honeypots:
            st.markdown("### Filtered Honeypots & Trap Logs")
            st.write(f"The pipeline automatically screen-filtered **{len(honeypot_candidates)}** honeypot profiles from the current pool. These profiles contained logical contradictions (such as conflicting work dates or impossible skill lengths) and were assigned a score of `0.0` to exclude them entirely.")
            
            if len(honeypot_candidates) == 0:
                st.info("No honeypots detected in this pool.")
            else:
                for hp in honeypot_candidates:
                    # Cleaned red/green emojis from expanding title
                    with st.expander(f"{hp['candidate_id']} — {hp['name']} | Listed Title: {hp['title']}"):
                        st.markdown("**Found Contradictions:**")
                        for reason in hp["reasons"]:
                            st.markdown(f"- :red[{reason}]")
                            
        # 4. ANALYTICS & POOL HEALTH TAB
        with tab_analytics:
            st.markdown("### Pool Demographics & Data Health")
            st.write(
                "This section provides interactive analytical insights of the processed candidate pool. "
                "You can hover, zoom, and select legend categories in each chart to filter data dynamically."
            )
            
            # Prepare data for analytics
            pool_data = []
            from pipeline.utils import calculate_profile_completeness, calculate_verification_score
            
            for item in scored_candidates:
                cand = item["candidate"]
                sig = cand.get("redrob_signals", {})
                comp = calculate_profile_completeness(cand)
                ver = calculate_verification_score(cand)
                trust_val = item["sub_scores"].get("trust_score", 0.5)
                
                pool_data.append({
                    "score": item["score"],
                    "yoe": item["yoe"],
                    "title": item["title"],
                    "location": cand.get("profile", {}).get("location", "").split(",")[0],
                    "response_rate": sig.get("recruiter_response_rate", 0.0),
                    "open_to_work": sig.get("open_to_work_flag", False),
                    "notice": sig.get("notice_period_days", 90),
                    "github": sig.get("github_activity_score", -1),
                    "completeness": comp,
                    "verification": ver,
                    "trust_score": trust_val
                })
                
            df_pool = pd.DataFrame(pool_data)
            
            if not df_pool.empty:
                st.write("#### Dynamic Pool Filters")
                st.write("Apply filters below to slice and dice the talent pool demographics and analyze specific candidate segments in real-time.")
                
                # Interactive filters
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1:
                    filter_yoe = st.selectbox(
                        "Experience Level",
                        options=["All Experience Levels", "Senior AI Candidates (5-9 YOE)", "Highly Experienced (10+ YOE)", "Mid-level/Junior (<5 YOE)"]
                    )
                with f_col2:
                    filter_loc = st.selectbox(
                        "Location Proximity",
                        options=["All Locations", "Preferred Cities (Pune, Noida, Delhi NCR)", "Other Regions"]
                    )
                with f_col3:
                    filter_otw = st.selectbox(
                        "Availability Status",
                        options=["All Availability Statuses", "Actively Open to Work", "Passive / Not Marked"]
                    )
                
                # Apply filters
                df_filtered = df_pool.copy()
                
                if filter_yoe == "Senior AI Candidates (5-9 YOE)":
                    df_filtered = df_filtered[(df_filtered["yoe"] >= 5) & (df_filtered["yoe"] <= 9)]
                elif filter_yoe == "Highly Experienced (10+ YOE)":
                    df_filtered = df_filtered[df_filtered["yoe"] >= 10]
                elif filter_yoe == "Mid-level/Junior (<5 YOE)":
                    df_filtered = df_filtered[df_filtered["yoe"] < 5]
                    
                if filter_loc == "Preferred Cities (Pune, Noida, Delhi NCR)":
                    preferred_cities = ["pune", "noida", "delhi", "ncr"]
                    df_filtered = df_filtered[df_filtered["location"].str.lower().str.contains("|".join(preferred_cities), na=False)]
                elif filter_loc == "Other Regions":
                    preferred_cities = ["pune", "noida", "delhi", "ncr"]
                    df_filtered = df_filtered[~df_filtered["location"].str.lower().str.contains("|".join(preferred_cities), na=False)]
                    
                if filter_otw == "Actively Open to Work":
                    df_filtered = df_filtered[df_filtered["open_to_work"] == True]
                elif filter_otw == "Passive / Not Marked":
                    df_filtered = df_filtered[df_filtered["open_to_work"] == False]
                
                if df_filtered.empty:
                    st.warning("No candidates in the pool match the selected combination of filters. Please adjust your criteria.")
                else:
                    # Pool Health Summary Cards based on filtered data
                    h_col1, h_col2, h_col3 = st.columns(3)
                    with h_col1:
                        avg_comp = df_filtered["completeness"].mean()
                        st.metric("Avg Profile Completeness", f"{int(avg_comp*100)}%")
                    with h_col2:
                        avg_ver = df_filtered["verification"].mean()
                        st.metric("Avg Profile Verification", f"{int(avg_ver*100)}%")
                    with h_col3:
                        otw_count = df_filtered["open_to_work"].sum()
                        st.metric("Active Candidates (Open To Work)", f"{otw_count} / {len(df_filtered)}")
                    
                    st.write("---")
                    
                    col_chart1, col_chart2 = st.columns(2)
                    
                    with col_chart1:
                        st.markdown("#### Years of Experience Distribution")
                        fig_yoe = px.histogram(
                            df_filtered, 
                            x="yoe", 
                            nbins=12,
                            labels={"yoe": "Years of Experience", "count": "Candidates Count"},
                            color_discrete_sequence=["#5e60ff"]
                        )
                        fig_yoe.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#f1f3f9")
                        )
                        st.plotly_chart(fig_yoe, use_container_width=True)
                        st.write(
                            "This chart shows the distribution of professional tenure. Pointing out the density of profiles "
                            "helps us assess if we have a healthy volume of candidates in our targeted Senior AI Engineer experience range (5-9 YOE)."
                        )
                        
                    with col_chart2:
                        st.markdown("#### Score Correlation with Platform Response Rate")
                        fig_corr = px.scatter(
                            df_filtered, 
                            x="response_rate", 
                            y="score", 
                            color="open_to_work",
                            labels={"response_rate": "Recruiter Response Rate", "score": "Final Score", "open_to_work": "Open to Work Status"},
                            color_discrete_map={True: "#ff2995", False: "#5e60ff"}
                        )
                        fig_corr.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#f1f3f9")
                        )
                        st.plotly_chart(fig_corr, use_container_width=True)
                        st.write(
                            "This scatter plot highlights candidate responsiveness against suitability score. "
                            "Candidates in the upper-right quadrant represent high-value targets who are both highly qualified and active on the platform."
                        )
                        
                    st.write("---")
                    col_chart3, col_chart4 = st.columns(2)
                    
                    with col_chart3:
                        st.markdown("#### Top Talent Locations (Top 10)")
                        df_loc = df_filtered["location"].value_counts().head(10).reset_index()
                        df_loc.columns = ["location", "count"]
                        fig_loc = px.bar(
                            df_loc, 
                            x="location", 
                            y="count",
                            labels={"location": "City", "count": "Candidate Count"},
                            color_discrete_sequence=["#ff2995"]
                        )
                        fig_loc.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#f1f3f9")
                        )
                        st.plotly_chart(fig_loc, use_container_width=True)
                        st.write(
                            "This bar chart displays the geographic distribution of talent. A high concentration of candidates "
                            "in hybrid-friendly regions like Pune and Noida/NCR allows for office compliance without relocation overhead."
                        )
                        
                    with col_chart4:
                        st.markdown("#### Notice Period Distribution")
                        df_notice = df_filtered["notice"].value_counts().reset_index()
                        df_notice.columns = ["notice", "count"]
                        fig_notice = px.pie(
                            df_notice, 
                            names="notice", 
                            values="count",
                            color_discrete_sequence=["#5e60ff", "#ff2995", "#a238ff", "#a0aec0"]
                        )
                        fig_notice.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#f1f3f9")
                        )
                        st.plotly_chart(fig_notice, use_container_width=True)
                        st.write(
                            "This pie chart shows notice period availability. Immediate joiners (notice period <= 30 days) "
                            "are highly preferred to reduce hire-to-onboard latency, while notice periods > 90 days represent hire risk."
                        )

                    st.write("---")
                    st.markdown("#### Profile Trust Score Distribution")
                    fig_trust = px.histogram(
                        df_filtered, 
                        x="trust_score", 
                        nbins=10,
                        labels={"trust_score": "Recruiter Trust Score", "count": "Candidates Count"},
                        color_discrete_sequence=["#a238ff"]
                    )
                    fig_trust.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#f1f3f9")
                    )
                    st.plotly_chart(fig_trust, use_container_width=True)
                    st.write(
                        "This histogram displays the distribution of profile trust scores. High trust scores (>80%) indicate "
                        "profiles verified through GitHub and platform assessment scores, whereas low trust scores require extra diligence."
                    )


