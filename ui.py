import streamlit as st
import matplotlib.pyplot as plt
import base64


def display_header():
    logo_html = '<div style="font-size:50px; text-align:center;">🧑‍💼</div>'
    st.markdown(f"""
    <div class="main-header" style="margin-bottom:20px; padding:20px 0;">
        <div style="text-align:center;">
            <div class="logo-container" style="margin-bottom:10px;">
                {logo_html}
            </div>
            <div class="title-container">
                <h1 style="margin:0; color:#ffffff;">Recruitment Agent</h1>
                <p style="margin:5px 0; color:#aaaaaa; font-size:1.1rem;">Smart Resume Analysis & Interview Preparation System</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def apply_custom_css(accent_color="#380202"):
    st.markdown(f"""
    <style>
        /* Main background */
        .main {{
            background-color: #000000 !important;
            color: white !important;
        }}

        /* Header border */
        .main-header {{
            border-bottom: 4px solid {accent_color} !important;
        }}

        /* Primary buttons */
        .stButton > button {{
            background-color: {accent_color} !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.6em 1.2em !important;
            font-weight: bold !important;
            transition: all 0.3s ease;
        }}
        .stButton > button:hover {{
            background-color: #b71c1c !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(183,28,28,0.4);
        }}

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: #111111;
            border-radius: 8px;
            padding: 5px;
        }}
        .stTabs [data-baseweb="tab"] {{
            color: #aaaaaa;
            font-weight: bold;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {accent_color} !important;
            color: white !important;
            border-radius: 6px;
        }}

        /* Card container */
        .card {{
            background-color: #111111;
            padding: 24px;
            border-radius: 12px;
            margin: 20px 0;
            border: 1px solid #333333;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        /* Skill tags */
        .skill-tag {{
            background-color: #4CAF50;
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            margin: 6px 4px;
            display: inline-block;
            font-size: 0.9rem;
            font-weight: bold;
        }}
        .skill-tag.missing {{
            background-color: #d32f2f;
        }}

        /* Download button */
        .download-btn {{
            background-color: {accent_color} !important;
            color: white !important;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 8px;
            display: inline-block;
            font-weight: bold;
            margin: 10px 5px;
            transition: 0.3s;
        }}
        .download-btn:hover {{
            background-color: #b71c1c !important;
            transform: scale(1.05);
        }}

        /* Weakness & solution details */
        .weakness-detail, .solution-detail {{
            margin: 12px 0;
            padding: 14px;
            background-color: #1e1e1e;
            border-left: 5px solid #d32f2f;
            border-radius: 0 8px 8px 0;
        }}
        .solution-detail {{
            border-left-color: #4CAF50;
            background-color: #162016;
        }}

        /* Comparison boxes */
        .comparision-container {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        .comparison-box {{
            flex: 1;
            background-color: #1e1e1e;
            padding: 16px;
            border-radius: 8px;
            border: 1px solid #444;
        }}
    </style>
    """, unsafe_allow_html=True)



def role_selection_section(role_requirements):
    
    st.markdown("### Select Target Role")

    col1, col2 = st.columns([2, 1])
    with col1:
        role = st.selectbox("Predefined Role:", list(role_requirements.keys()))
    with col2:
        upload_jd = st.checkbox("Upload Custom JD")

    custom_jd = None
    if upload_jd:
        custom_jd = st.file_uploader("Upload Job Description (PDF or TXT)", type=["pdf", "txt"])
        if custom_jd:
            st.success("Custom JD uploaded successfully!")
    else:
        skills = role_requirements[role]
        st.info(f"**Required Skills:** {', '.join(skills)}")
        st.markdown("<p style='margin-top:10px;'><strong>Cutoff Score:</strong> 75/100</p>", unsafe_allow_html=True)
    return role, custom_jd


def resume_upload_section():
    st.markdown("### Upload Your Resume")
    st.markdown("<p style='color:#aaa;'>Supported: PDF only</p>", unsafe_allow_html=True)

    uploaded_resume = st.file_uploader("", type=["pdf"], label_visibility="collapsed")
    return uploaded_resume


def create_score_pie_chart(score):
    fig, ax = plt.subplots(figsize=(5, 5), facecolor='#000000')
    sizes = [score, 100 - score]
    colors = ["#d32f2f", "#333333"]
    explode = (0.08, 0)

    wedges, texts = ax.pie(
        sizes,
        colors=colors,
        explode=explode,
        startangle=90,
        wedgeprops={'width': 0.4, 'edgecolor': 'black', 'linewidth': 1.5}
    )

    centre_circle = plt.Circle((0, 0), 0.30, fc='#000000')
    ax.add_artist(centre_circle)

    ax.text(0, 0, f"{score}%", ha='center', va='center', fontsize=32, fontweight='bold', color='white')
    status = "PASS" if score >= 75 else "FAIL"
    status_color = '#4CAF50' if score >= 75 else "#d32f2f"
    ax.text(0, -0.35, status, ha='center', va='center', fontsize=16, fontweight='bold', color=status_color)

    ax.set_aspect('equal')
    fig.patch.set_facecolor('#000000')
    return fig


def display_analysis_result(analysis_result):
    if not analysis_result:
        return

    overall_score = analysis_result.get('overall_score', 0)
    selected = analysis_result.get('selected', False)
    strengths = analysis_result.get("strengths", [])
    missing_skills = analysis_result.get('missing_skills', [])
    skill_scores = analysis_result.get("skill_scores", {})
    detail_weaknesses = analysis_result.get("detailed_weaknesses", [])

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<div style='text-align:right; font-size:0.8rem; color:#888;'>Analysis Report</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Overall Score", f"{overall_score}/100")
        fig = create_score_pie_chart(overall_score)
        st.pyplot(fig, use_container_width=True)

    with col2:
        if selected:
            st.success("🎉 **Congratulations! You have been shortlisted.**")
        else:
            st.error("❌ **Unfortunately, you were not selected.**")
        st.write(analysis_result.get('reasoning', 'No reasoning provided.'))

    st.markdown("---")

    col_str, col_weak = st.columns(2)
    with col_str:
        st.subheader("✅ Strengths")
        if strengths:
            for skill in strengths:
                score = skill_scores.get(skill, "N/A")
                st.markdown(f'<div class="skill-tag">{skill} ({score}/10)</div>', unsafe_allow_html=True)
        else:
            st.info("No notable strengths identified.")

    with col_weak:
        st.subheader("⚠️ Areas for Improvement")
        if missing_skills:
            for skill in missing_skills:
                score = skill_scores.get(skill, "N/A")
                st.markdown(f'<div class="skill-tag missing">{skill} ({score}/10)</div>', unsafe_allow_html=True)
        else:
            st.info("No significant gaps found.")

    if detail_weaknesses:
        st.markdown("---")
        st.subheader("🔍 Detailed Weakness Analysis")
        for weakness in detail_weaknesses:
            skill = weakness.get('skill', 'Unknown')
            score = weakness.get('score', 0)
            with st.expander(f"{skill} (Score: {score}/10)", expanded=False):
                detail = weakness.get('detail', 'No details available.')
                if detail.startswith('```json') or '{' in detail[:50]:
                    detail = "The resume lacks clear examples demonstrating this skill."
                st.markdown(f'<div class="weakness-detail"><strong>Issue:</strong> {detail}</div>', unsafe_allow_html=True)

                if weakness.get('suggestions'):
                    st.markdown("<strong>How to Improve:</strong>", unsafe_allow_html=True)
                    for i, sugg in enumerate(weakness['suggestions']):
                        st.markdown(f'<div class="solution-detail">{i+1}. {sugg}</div>', unsafe_allow_html=True)

    # Download Report
    st.markdown("---")
    report_content = f"""# Resume Analysis Report
## Overall Score: {overall_score}/100
**Status:** {"✅ Shortlisted" if selected else "❌ Not Selected"}

## Reasoning
{analysis_result.get('reasoning', 'N/A')}

## Strengths
{', '.join(strengths) or 'None identified'}

## Areas for Improvement
{', '.join(missing_skills) or 'None identified'}

## Detailed Analysis
"""
    for w in detail_weaknesses:
        report_content += f"\n### {w.get('skill','')} ({w.get('score',0)}/10)\n"
        report_content += f"Issue: {w.get('detail','N/A')}\n"
        if w.get('suggestions'):
            report_content += "\nSuggestions:\n" + "\n".join([f"- {s}" for s in w['suggestions']]) + "\n"

    b64 = base64.b64encode(report_content.encode()).decode()
    href = f'<a class="download-btn" href="data:text/plain;base64,{b64}" download="Resume_Analysis_Report.txt">📥 Download Full Report</a>'
    st.markdown(href, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def resume_qa_selection(has_resume, ask_question_func=None):
    if not has_resume:
        st.warning("Please analyze a resume first in the 'Resume Analysis' tab.")
        return

    
    st.subheader("💬 Ask Questions About the Resume")

    question = st.text_input(
        "Your Question:",
        placeholder="e.g., What is the candidate's strongest technical skill?"
    )

    if question and ask_question_func:
        with st.spinner("Searching resume and generating answer..."):
            response = ask_question_func(question)
            st.markdown(f"**Q:** {question}")
            st.markdown(f"<div style='background-color:#1e1e1e; padding:16px; border-radius:8px; border-left:5px solid {st.get_option('theme.primaryColor') or '#380202'}'>{response}</div>", unsafe_allow_html=True)

    with st.expander("💡 Example Questions"):
        examples = [
            "What is the candidate's most recent role and key achievements?",
            "How many years of experience do they have in Python?",
            "Does the candidate have experience with cloud platforms?",
            "What projects demonstrate leadership or teamwork?",
            "Summarize the candidate's education background."
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{hash(ex)}"):
                st.text_input("Your Question:", value=ex, key=f"input_{hash(ex)}")

    st.markdown('</div>', unsafe_allow_html=True)


def interview_questions_section(has_resume, generate_questions_func=None):
    if not has_resume:
        st.warning("Please analyze a resume first.")
        return

    
    st.subheader("🎤 Generate Interview Questions")

    col1, col2 = st.columns(2)
    with col1:
        question_types = st.multiselect(
            "Question Types",
            ["Basic", "Technical", "Experience", "Behavioral", "Scenario", "Coding"],
            default=["Technical", "Behavioral"]
        )
    with col2:
        difficulty = st.select_slider("Difficulty", options=["Easy", "Medium", "Hard"], value="Medium")

    num_questions = st.slider("Number of Questions", 3, 15, 8)

    if st.button("Generate Questions", type="primary"):
        if generate_questions_func and question_types:
            with st.spinner("Creating personalized questions..."):
                questions = generate_questions_func(question_types, difficulty, num_questions)

                download_md = f"# Interview Questions\n\n**Difficulty:** {difficulty}\n**Types:** {', '.join(question_types)}\n\n"
                for i, (qtype, qtext) in enumerate(questions, 1):
                    with st.expander(f"{i}. [{qtype}] {qtext[:80]}..."):
                        st.write(qtext)
                        if qtype.lower() == "coding":
                            st.code("# Write your solution here\n", language="python")
                    download_md += f"## {i}. {qtype}\n{qtext}\n\n"

                if questions:
                    b64 = base64.b64encode(download_md.encode()).decode()
                    href = f'<a class="download-btn" href="data:text/markdown;base64,{b64}" download="Interview_Questions.md">📥 Download Questions (MD)</a>'
                    st.markdown(href, unsafe_allow_html=True)
        else:
            st.warning("Please select at least one question type.")

    st.markdown('</div>', unsafe_allow_html=True)


def resume_improvement_section(has_resume, improve_resume_func=None):
    if not has_resume:
        st.warning("Please analyze a resume first.")
        return

    
    st.subheader("✍️ Resume Improvement Suggestions")

    areas = st.multiselect(
        "Select Areas to Improve",
        ["Content", "Format", "Skills Highlighting", "Experience Description",
         "Projects", "Achievements", "Overall Structure"],
        default=["Skills Highlighting", "Experience Description"]
    )
    target_role = st.text_input("Target Role (optional)", placeholder="e.g., Senior Data Scientist")

    if st.button("Generate Suggestions", type="primary"):
        if improve_resume_func and areas:
            with st.spinner("Analyzing and generating improvements..."):
                suggestions = improve_resume_func(areas, target_role)

                download_content = f"# Resume Improvement Suggestions\n\n**Target Role:** {target_role or 'General'}\n\n"
                for area, data in suggestions.items():
                    with st.expander(f"📌 {area}", expanded=True):
                        st.markdown(f"**Description:** {data.get('description', '')}")
                        st.markdown("**Specific Suggestions:**")
                        for i, s in enumerate(data.get("specific", []), 1):
                            st.markdown(f'<div class="solution-detail">{i}. {s}</div>', unsafe_allow_html=True)

                        if data.get("before_after"):
                            st.markdown('<div class="comparision-container">', unsafe_allow_html=True)
                            st.markdown('<div class="comparison-box"><strong>Before:</strong><pre>{}</pre></div>'.format(data["before_after"]["before"]), unsafe_allow_html=True)
                            st.markdown('<div class="comparison-box"><strong>After:</strong><pre>{}</pre></div>'.format(data["before_after"]["after"]), unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)

                    download_content += f"## {area}\n\n{data.get('description','')}\n\n### Suggestions\n" + "\n".join([f"{i}. {s}" for i, s in enumerate(data.get('specific', []), 1)]) + "\n\n"

                b64 = base64.b64encode(download_content.encode()).decode()
                href = f'<a class="download-btn" href="data:text/markdown;base64,{b64}" download="Resume_Improvements.md">📥 Download All Suggestions</a>'
                st.markdown(href, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def improved_resume_section(has_resume, get_improved_resume_func=None):
    if not has_resume:
        st.warning("Please analyze a resume first.")
        return

    
    st.subheader("✨ Generate Improved Resume")

    target_role = st.text_input("Target Role", placeholder="e.g., Full Stack Engineer")
    highlight_skills = st.text_area(
        "Paste Job Description or Key Skills (comma-separated or full JD)",
        height=150,
        placeholder="e.g., React, Node.js, AWS, TypeScript\n\nOr paste full job description here..."
    )

    if st.button("Generate Improved Resume", type="primary"):
        if get_improved_resume_func:
            with st.spinner("Rewriting and optimizing your resume..."):
                improved = get_improved_resume_func(target_role, highlight_skills)
                st.markdown("### 🏆 Your Enhanced Resume")
                st.text_area("", improved, height=600)

                col1, col2 = st.columns(2)
                with col1:
                    txt_b64 = base64.b64encode(improved.encode()).decode()
                    href_txt = f'<a class="download-btn" href="data:text/plain;base64,{txt_b64}" download="Improved_Resume.txt">📄 Download as TXT</a>'
                    st.markdown(href_txt, unsafe_allow_html=True)
                with col2:
                    md_content = f"# {target_role or 'Professional'} Resume\n\n{improved}\n\n---\n*Enhanced by AI Recruitment Agent*"
                    md_b64 = base64.b64encode(md_content.encode()).decode()
                    href_md = f'<a class="download-btn" href="data:text/markdown;base64,{md_b64}" download="Improved_Resume.md">📝 Download as Markdown</a>'
                    st.markdown(href_md, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def create_tabs():
    return st.tabs([
        "Resume Analysis",
        "Resume Q&A",
        "Interview Questions",
        "Resume Improvement",
        "Improved Resume"
    ])