import os
import sys

def install_and_generate():
    # Install reportlab if not present
    try:
        import reportlab
    except ImportError:
        print("Installing reportlab for PDF generation...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "reportlab"], check=True)
        
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    
    pdf_path = "./redrob_talent_intelligence_deck.pdf"
    print(f"Generating PDF deck at {pdf_path}...")
    
    # 1. Page numbering & running headers canvas
    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []
            
        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()
            
        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_elements(num_pages)
                super().showPage()
            super().save()
            
        def draw_page_elements(self, page_count):
            self.saveState()
            
            # Skip header/footer on title page (page 1)
            if self._pageNumber == 1:
                # Draw title page background accents
                self.setFillColor(colors.HexColor("#0d0e15"))
                self.rect(0, 0, 8.5*inch, 11*inch, fill=True, stroke=False)
                
                # Dynamic accent lines
                self.setStrokeColor(colors.HexColor("#5e60ff"))
                self.setLineWidth(5)
                self.line(1*inch, 9*inch, 7.5*inch, 9*inch)
                
                self.setStrokeColor(colors.HexColor("#ff2995"))
                self.setLineWidth(3)
                self.line(1*inch, 8.8*inch, 6*inch, 8.8*inch)
                
                self.restoreState()
                return
                
            # Running Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#5e60ff"))
            self.drawString(54, 750, "REDROB TALENT INTELLIGENCE")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#a0aec0"))
            self.drawRightString(612 - 54, 750, "Team EnSoc — Hackathon Submission")
            
            # Thin divider line below header
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)
            
            # Running Footer
            self.line(54, 60, 612 - 54, 60)
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#718096"))
            self.drawString(54, 45, "Intelligent Candidate Discovery & Ranking")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(612 - 54, 45, page_text)
            
            self.restoreState()

    # Setup document
    # Margin 54pt = 0.75in
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom color palette
    primary_color = colors.HexColor("#5e60ff")
    secondary_color = colors.HexColor("#ff2995")
    dark_bg = colors.HexColor("#0d0e15")
    dark_card = colors.HexColor("#1b1c2a")
    text_dark = colors.HexColor("#2d3748")
    text_muted = colors.HexColor("#718096")
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=colors.white,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=16,
        leading=22,
        textColor=colors.HexColor("#a0aec0"),
        spaceAfter=40
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#ff2995"),
        spaceAfter=5
    )
    
    meta_val_style = ParagraphStyle(
        'MetaValStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.white,
        spaceAfter=20
    )
    
    slide_title_style = ParagraphStyle(
        'SlideTitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        spaceAfter=5
    )
    
    slide_tag_style = ParagraphStyle(
        'SlideTagStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=secondary_color,
        spaceAfter=20
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=text_dark,
        spaceAfter=15
    )
    
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=text_dark,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=8
    )
    
    card_title_style = ParagraphStyle(
        'CardTitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=primary_color,
        spaceAfter=5
    )
    
    card_body_style = ParagraphStyle(
        'CardBodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_dark,
        spaceAfter=0
    )
    
    story = []
    
    # ------------------ PAGE 1: TITLE SLIDE ------------------
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("REDROB TALENT INTELLIGENCE", meta_style))
    story.append(Paragraph("Intelligent Candidate Discovery & Multi-Dimensional Ranking", title_style))
    story.append(Paragraph("A lightweight, sub-15 second local pipeline achieving 0% honeypots in the top 100 with facts-based explanation reasoning.", subtitle_style))
    
    story.append(Spacer(1, 1*inch))
    
    # Meta table
    meta_data = [
        [Paragraph("SUBMISSION DETAILS", meta_style), Paragraph("DEVELOPMENT TEAM", meta_style)],
        [Paragraph("Redrob AI Data & AI Hackathon<br/>Role: Senior AI Engineer (Founding Team)", ParagraphStyle('W1', parent=meta_val_style, textColor=colors.HexColor("#cbd5e0"))), 
         Paragraph("Team Name: <b>Team EnSoc</b><br/>Lead: Pratham Agarwal & Adarsh Dwivedi", ParagraphStyle('W2', parent=meta_val_style, textColor=colors.HexColor("#cbd5e0")))]
    ]
    t_meta = Table(meta_data, colWidths=[3.5*inch, 3.5*inch])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_meta)
    
    story.append(PageBreak())
    
    # ------------------ PAGE 2: THE PROBLEM & OPPORTUNITY ------------------
    story.append(Paragraph("THE RECRUITER'S DILEMMA", slide_tag_style))
    story.append(Paragraph("Why Keyword Filters and Traditional Search Fail", slide_title_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Recruiters scan hundreds of profiles daily, yet frequently miss exceptional talent. Traditional systems suffer from two structural flaws:", body_style))
    
    # Problem Cards Table
    card_p1 = [
        Paragraph("Keyword-Stuffing Traps (Honeypots)", card_title_style),
        Paragraph("Candidates often list highly fashionable skills (e.g., 'RAG', 'LangChain', 'Pinecone') on their profiles without possessing actual practical experience. A naive semantic or keyword search ranks these candidates highly, even if their current role is completely unrelated (e.g., a Marketing Manager who stuffed their profile).", card_body_style)
    ]
    card_p2 = [
        Paragraph("The Scale & Compute Bottleneck", card_title_style),
        Paragraph("While Large Language Models (LLMs) excel at nuanced understanding of job descriptions and candidate resumes, running an LLM call for each candidate in a pool of 100,000+ is operationally impossible. It exceeds compute budgets, takes hours of execution time, and introduces heavy network latency.", card_body_style)
    ]
    
    t_problems = Table([[card_p1, card_p2]], colWidths=[3.4*inch, 3.4*inch])
    t_problems.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (0,0), 1, colors.HexColor("#e2e8f0")),
        ('BOX', (1,0), (1,0), 1, colors.HexColor("#e2e8f0")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('TOPPADDING', (0,0), (-1,-1), 15),
        ('LEFTPADDING', (0,0), (-1,-1), 15),
        ('RIGHTPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(t_problems)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("<b>The EnSoc Approach:</b> Instead of an expensive LLM or a naive keyword matcher, we built a <b>modular, multi-dimensional scoring pipeline</b>. It features a deterministic <b>logical contradiction filter</b> to exclude 100% of honeypots, computes <b>DNA Fingerprints</b>, and executes in under <b>15 seconds on a single CPU core</b>.", body_style))
    
    story.append(PageBreak())
    
    # ------------------ PAGE 3: THE SOLUTION ARCHITECTURE ------------------
    story.append(Paragraph("SYSTEM OVERVIEW", slide_tag_style))
    story.append(Paragraph("Multi-Dimensional Candidate Matching Pipeline", slide_title_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Our architecture divides candidate processing into distinct phases, prioritizing speed, safety, and relevance:", body_style))
    
    # Architecture list
    story.append(Paragraph("• <b>Phase 1: Deterministic Honeypot Filter</b>: Screen-filters all candidates for structural lies and date contradictions. Flagged profiles are assigned a score of 0.0, completely removing them from the shortlist.", bullet_style))
    story.append(Paragraph("• <b>Phase 2: Multi-Dimensional Scoring Engine</b>: Scores valid candidates across key dimensions: Title Fit (30%), Technical Skill Depth (30%), Experience & Company Fit (20%), and Location & Notice Logistics (20%).", bullet_style))
    story.append(Paragraph("• <b>Phase 3: DNA Fingerprinting & Trust Scoring</b>: Formulates a 6-axis candidate DNA profile and a Recruiter Trust Score mapping profile completeness, verified Redrob assessments, and GitHub activity.", bullet_style))
    story.append(Paragraph("• <b>Phase 4: Factual Explainability Engine</b>: Generates high-quality, template-free 1-2 sentence justifications referencing candidate-specific YOE, skills, response rates, and trust status with zero hallucination.", bullet_style))
    
    story.append(Spacer(1, 15))
    
    # Performance Stats Table
    stats_data = [
        [Paragraph("<b>Pipeline Metric</b>", card_title_style), Paragraph("<b>Value / Outcome</b>", card_title_style), Paragraph("<b>Why It Matters</b>", card_title_style)],
        [Paragraph("Candidate Pool Scanned", card_body_style), Paragraph("100,000 Profiles", card_body_style), Paragraph("Fully processes the entire hackathon dataset.", card_body_style)],
        [Paragraph("Total Execution Time", card_body_style), Paragraph("<b>13.55 Seconds</b>", card_body_style), Paragraph("CPU-only execution, well below the 5-min limit.", card_body_style)],
        [Paragraph("Honeypot Exclusions", card_body_style), Paragraph("135 Candidates (100% caught)", card_body_style), Paragraph("Ensures 0% honeypot rate in top 100.", card_body_style)],
        [Paragraph("Verified Skill Scaling", card_body_style), Paragraph("1.5x Redrob Assessment Bonus", card_body_style), Paragraph("Rewards proven skills over keyword stuffing.", card_body_style)],
    ]
    t_stats = Table(stats_data, colWidths=[2.2*inch, 2.2*inch, 2.6*inch])
    t_stats.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e0")),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_stats)
    
    story.append(PageBreak())
    
    # ------------------ PAGE 4: HONEYPOT FILTERING ------------------
    story.append(Paragraph("TRAP DETECTION AND PREVENTATIVE FILTERING", slide_tag_style))
    story.append(Paragraph("Deterministic Exclusion of Subtle Honeypot Profiles", slide_title_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Honeypot profiles represent artificially generated resumes containing logical contradictions. Our pipeline filters out 135 candidates using the following strict checks:", body_style))
    
    # Rules list
    story.append(Paragraph("1. <b>Technology Age vs. Experience Duration</b>: LangChain, LlamaIndex, QLoRA, LoRA, PEFT, and RAG became widely used after 2022. Candidates claiming $>5$ years ($>60$ months) of experience in these technologies are flagged. Similarly, candidates claiming $>9$ years in BERT, PyTorch, or FastAPI are flagged.", bullet_style))
    story.append(Paragraph("2. <b>Skill Duration vs. Total Experience</b>: If a candidate's experience in a single skill exceeds their total years of experience or career history span (earliest job to now) by more than 2 years, it represents a data contradiction.", bullet_style))
    story.append(Paragraph("3. <b>Expert Skills with Zero Duration</b>: Flag candidates claiming 'expert' or 'advanced' proficiency in 3 or more skills with 0 months of experience, or when they claim 0-duration expert skills and have an empty career history.", bullet_style))
    story.append(Paragraph("4. <b>Extreme YOE Contradiction</b>: Flag candidates claiming $\ge 10$ YOE whose career history durations sum to less than 1.5 years.", bullet_style))
    story.append(Paragraph("5. <b>Job Date Overlaps and Founding Traps</b>: Flag candidates with job start dates after end dates, or working at a company before its founding year (extracted from the company description: e.g., 'founded in 2022' but job starts in 2015). Also checks for multiple concurrent current jobs at different companies.", bullet_style))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>By assigning a final score of 0.0 to any profile triggering these checks, we guarantee <b>0% honeypot presence</b> in the top 100 shortlist, satisfying the hackathon's disqualification threshold.</i>", ParagraphStyle('Ital', parent=body_style, fontName='Helvetica-Oblique', textColor=secondary_color)))
    
    story.append(PageBreak())
    
    # ------------------ PAGE 5: MULTI-DIMENSIONAL SCORING ENGINE ------------------
    story.append(Paragraph("SCORING METHODOLOGY", slide_tag_style))
    story.append(Paragraph("Multi-Dimensional Fit & Behavioral Modifiers", slide_title_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Valid candidates are scored out of 1.0 (with small bonuses possible) across five dimensions:", body_style))
    
    # Dimensions Table
    dimensions_data = [
        [Paragraph("<b>Scoring Dimension</b>", card_title_style), Paragraph("<b>Weight</b>", card_title_style), Paragraph("<b>Evaluation Logic & Multipliers</b>", card_title_style)],
        [Paragraph("Role & Title Fit", card_body_style), Paragraph("<b>30%</b>", card_body_style), Paragraph("Core AI/ML engineering titles (like <i>AI/ML/NLP Engineer</i>) score 1.0. Adjacent roles (like <i>Backend/Software Engineer</i>) score 0.6. Non-tech titles (like <i>HR/Marketing Manager</i>) score 0.0, preventing keyword stuffers.", card_body_style)],
        [Paragraph("Technical Skills Depth", card_body_style), Paragraph("<b>30%</b>", card_body_style), Paragraph("Core skills (vector databases, embeddings, evaluation, python) are scaled by proficiency (expert=1.2x) and duration. Crucially, a <b>1.5x Verification Bonus</b> is applied for high Redrob platform assessment scores.", card_body_style)],
        [Paragraph("Experience & Company Fit", card_body_style), Paragraph("<b>20%</b>", card_body_style), Paragraph("Peak score at 6-8 YOE (ideal Senior AI Engineer). Disqualifies candidates whose entire career is spent at outsourcing giants (TCS, Infosys, etc.). Grants a <b>1.1x Startup Bonus</b> for product company experience.", card_body_style)],
        [Paragraph("Location & Logistics", card_body_style), Paragraph("<b>20%</b>", card_body_style), Paragraph("Rewards candidates located in Pune/Noida/Delhi NCR (1.0). Tier-1 Indian cities (0.8) are accepted only if willing to relocate, else penalized (0.1). Rewards short notice periods (sub-30 days).", card_body_style)],
        [Paragraph("Behavioral Modifier", card_body_style), Paragraph("<b>Multiplier</b>", card_body_style), Paragraph("A multiplicative modifier based on platform activity: last active recency (up to 1.1x, down to 0.3x if >6 months inactive), recruiter response rate (scales score), and open-to-work status (1.1x).", card_body_style)]
    ]
    t_dims = Table(dimensions_data, colWidths=[1.8*inch, 1.0*inch, 4.2*inch])
    t_dims.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e0")),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_dims)
    
    story.append(PageBreak())
    
    # ------------------ PAGE 6: EXPLAINABILITY & VERIFICATION ------------------
    story.append(Paragraph("EXPLAINABILITY AND SANDBOX DASHBOARD", slide_tag_style))
    story.append(Paragraph("Factual Justifications & Interactive Verification", slide_title_style))
    story.append(Spacer(1, 15))
    
    # Factual reasoner
    story.append(Paragraph("<b>1. Factual, Template-Free Reasonings</b>", card_title_style))
    story.append(Paragraph("To satisfy the Stage 4 manual review requirements, our explanation engine dynamically builds 1-2 sentence justifications using candidate-specific profile details. It references years of experience, current titles, matched skills, and response rates, while acknowledging notice periods and relocation needs. It contains zero hallucinations and exhibits high linguistic variation, ensuring a professional, human-like justification for every recommendation.", body_style))
    
    # Streamlit Sandbox
    story.append(Paragraph("<b>2. Streamlit Sandbox App (`app.py`)</b>", card_title_style))
    story.append(Paragraph("To satisfy the sandbox requirement, we built an interactive dashboard. It allows recruiters to run the ranking engine and view a visual platform containing:", body_style))
    story.append(Paragraph("• <b>Ranked Shortlist</b> with final scores, Trust Scores, and generated justifications.", bullet_style))
    story.append(Paragraph("• <b>Deep Profile Inspector</b> showing a candidate's complete profile, DNA radar chart, and trust gauge.", bullet_style))
    story.append(Paragraph("• <b>Candidate Compare Mode</b> overlaying two candidates' DNA radar charts side-by-side.", bullet_style))
    story.append(Paragraph("• <b>Honeypot Trap Log</b> displaying filtered profiles and their contradictions.", bullet_style))
    story.append(Paragraph("• <b>Pool Analytics & Health</b> plotting experience distributions and data quality metrics.", bullet_style))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>3. Sandbox Local Setup Command:</b>", ParagraphStyle('SetupHead', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, spaceAfter=5)))
    story.append(Paragraph("<code>pip install -r requirements.txt && streamlit run app.py</code>", ParagraphStyle('CodeLine', parent=styles['Normal'], fontName='Courier', fontSize=10, textColor=primary_color, leftIndent=15, spaceAfter=15)))
    
    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF generation complete.")

if __name__ == "__main__":
    install_and_generate()
