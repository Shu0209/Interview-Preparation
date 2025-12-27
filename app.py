import streamlit as st
from agents import ResumeAnalysisAgent
import ui
from dotenv import load_dotenv
import os


load_dotenv()

st.set_page_config(
    page_title="Recruitment Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# LLM model
MODEL_NAME = "openai/gpt-oss-20b:free"
BASE_URL = "https://openrouter.ai/api/v1"

# Predefined role requirements
ROLE_REQUIREMENTS = {
    "AI/ML Engineer": [
        "Python", "PyTorch", "TensorFlow", "Machine Learning", "Deep Learning", "MLOps",
        "Scikit-Learn", "NLP", "Computer Vision", "Reinforcement Learning", "Hugging Face",
        "Data Engineering", "Feature Engineering", "AutoML"
    ],
    "Frontend Engineer": [
        "HTML", "CSS", "JavaScript", "TypeScript", "React", "Next.js", "Redux", "Tailwind CSS",
        "Vue.js", "Angular", "REST APIs", "GraphQL", "Webpack", "Vite", "UI/UX Design", "Responsive Design"
    ],
    "Backend Engineer": [
        "Python", "Java", "Node.js", "Express", "Spring Boot", "Django", "Flask", "FastAPI",
        "REST API", "GraphQL", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
        "Authentication", "Microservices", "Docker", "API Design"
    ],
    "Data Engineer": [
        "Python", "SQL", "ETL", "Apache Spark", "Hadoop", "Kafka", "Airflow", "Snowflake",
        "AWS", "Azure", "GCP", "Data Warehousing", "BigQuery", "Data Modeling", "Data Pipelines",
        "Data Lakes", "Delta Lake", "dbt"
    ],
    "DevOps Engineer": [
        "Linux", "Docker", "Kubernetes", "Jenkins", "CI/CD", "Terraform", "AWS", "Azure",
        "GCP", "Ansible", "Monitoring", "Grafana", "Prometheus", "Shell Scripting", "Git",
        "Load Balancing", "Networking", "Automation"
    ],
    "Full Stack Developer": [
        "HTML", "CSS", "JavaScript", "TypeScript", "React", "Node.js", "Express", "Next.js",
        "MongoDB", "PostgreSQL", "REST API", "GraphQL", "Docker", "Git", "Redux",
        "Tailwind CSS", "Authentication", "Testing", "CI/CD"
    ],
    "Data Scientist": [
        "Python", "R", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Scikit-Learn", "TensorFlow",
        "PyTorch", "Machine Learning", "Deep Learning", "Statistics", "NLP", "Computer Vision",
        "Data Cleaning", "Feature Engineering", "Model Deployment", "MLOps"
    ],
    "Data Analyst": [
        "SQL", "Python", "Excel", "Tableau", "Power BI", "Pandas", "NumPy", "Matplotlib",
        "Seaborn", "Data Visualization", "Data Cleaning", "Statistics", "Reporting",
        "Business Intelligence", "ETL", "Dashboards"
    ]
}

# Initialize session state
if 'resume_agent' not in st.session_state:
    st.session_state.resume_agent = None
if 'resume_analyzed' not in st.session_state:
    st.session_state.resume_analyzed = False
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None


# Get API key from .env
api_key = os.getenv("OPENROUTER_API_KEY")


if not api_key:
    st.error("❌ API Key not found!")
    st.stop()

# Initialize agent once (only on first run)
if st.session_state.resume_agent is None:
    try:
        st.session_state.resume_agent = ResumeAnalysisAgent(
            api_key=api_key,
            model_name=MODEL_NAME,
            base_url=BASE_URL
        )
        st.success("Connected to model")
    except Exception as e:
        st.error(f"Failed to connect to model: {e}")
        st.stop()

agent = st.session_state.resume_agent



def analyze_resume(agent, resume_file, role, custom_jd):
    if not resume_file:
        st.error("Please upload a resume PDF.")
        return None

    try:
        with st.spinner("🔍 Analyzing resume... This may take 30–60 seconds."):
            if custom_jd:
                result = agent.analyze_resume(resume_file, custom_jd=custom_jd)
            else:
                result = agent.analyze_resume(resume_file, role_requirements=ROLE_REQUIREMENTS[role])

            st.session_state.resume_analyzed = True
            st.session_state.analysis_result = result
            st.success("✅ Resume analysis complete!")
            return result
    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")
        return None


def ask_question(agent, question):
    try:
        with st.spinner("Thinking..."):
            return agent.ask_question(question)
    except Exception as e:
        return f"Error: {e}"


def generate_interview_questions(agent, question_types, difficulty, num_questions):
    try:
        with st.spinner("Generating personalized questions..."):
            return agent.generate_interview_questions(question_types, difficulty, num_questions)
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return []


def improved_resume(agent, improvement_areas, target_role):
    try:
        with st.spinner("Generating improvement suggestions..."):
            return agent.improve_resume(improvement_areas, target_role)
    except Exception as e:
        st.error(f"Error: {e}")
        return {}


def get_improved_resume(agent, target_role, highlight_skills):
    try:
        with st.spinner("Rewriting your resume..."):
            return agent.get_improved_resume(target_role, highlight_skills)
    except Exception as e:
        st.error(f"Error: {e}")
        return "Failed to generate improved resume."




def main():
    ui.display_header()


    # Create tabs
    tabs = ui.create_tabs()

    # Tab 1: Resume Analysis
    with tabs[0]:
        role, custom_jd = ui.role_selection_section(ROLE_REQUIREMENTS)
        uploaded_resume = ui.resume_upload_section()

        if uploaded_resume:
            if uploaded_resume.type != "application/pdf":
                st.error("Please upload a valid PDF file.")
            else:
                st.success(f"📄 Uploaded: **{uploaded_resume.name}**")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Analyze Resume", type="primary", use_container_width=True):
                if uploaded_resume and uploaded_resume.type == "application/pdf":
                    analyze_resume(agent, uploaded_resume, role, custom_jd)
                else:
                    st.warning("Please upload a valid PDF resume first.")

        if st.session_state.analysis_result:
            st.markdown("---")
            ui.display_analysis_result(st.session_state.analysis_result)

    # Tab 2: Resume Q&A
    with tabs[1]:
        ui.resume_qa_selection(
            has_resume=st.session_state.resume_analyzed,
            ask_question_func=lambda q: ask_question(agent, q)
        )

    # Tab 3: Interview Questions
    with tabs[2]:
        ui.interview_questions_section(
            has_resume=st.session_state.resume_analyzed,
            generate_questions_func=lambda t, d, n: generate_interview_questions(agent, t, d, n)
        )

    # Tab 4: Resume Improvement Suggestions
    with tabs[3]:
        ui.resume_improvement_section(
            has_resume=st.session_state.resume_analyzed,
            improve_resume_func=lambda areas, role: improved_resume(agent, areas, role)
        )

    # Tab 5: Generate Improved Resume
    with tabs[4]:
        ui.improved_resume_section(
            has_resume=st.session_state.resume_analyzed,
            get_improved_resume_func=lambda role, skills: get_improved_resume(agent, role, skills)
        )

        

if __name__ == "__main__":
    main()