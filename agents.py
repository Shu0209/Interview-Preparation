import re
import json
import io
import PyPDF2
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
# from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS





class ResumeAnalysisAgent:
    def __init__(self, api_key, model_name="gpt-4o", base_url=None, cutoff_score=75):
        self.api_key = api_key.strip()
        self.model_name = model_name
        self.base_url = base_url
        self.cutoff_score = cutoff_score

        self.resume_text = None
        self.jd_text = None
        self.extracted_skills = []
        self.rag_vectorstore = None
        self.analysis_result = None
        self.resume_weaknesses = []

    def get_llm(self, temperature=0.3, response_format=None, **kwargs):
        """Centralized LLM factory for consistent configuration"""
        params = {
            "model": self.model_name,
            "api_key": self.api_key,
            "temperature": temperature,
            "max_tokens": 2048,
        }
        if self.base_url:
            params["base_url"] = self.base_url
        if response_format:
            params["response_format"] = response_format

        return ChatOpenAI(**params, **kwargs)

    def extract_text_from_pdf(self, pdf_file):
        try:
            if hasattr(pdf_file, 'getvalue'):
                pdf_data = pdf_file.getvalue()
                reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            else:
                reader = PyPDF2.PdfReader(pdf_file)

            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return ""

    def extract_text_from_txt(self, txt_file):
        try:
            if hasattr(txt_file, 'getvalue'):
                return txt_file.getvalue().decode('utf-8')
            else:
                with open(txt_file.name, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"TXT extraction error: {e}")
            return ""

    def extract_text_from_file(self, file):
        if file is None:
            return ""
        ext = file.name.split('.')[-1].lower() if hasattr(file, 'name') else ""
        if ext == 'pdf':
            return self.extract_text_from_pdf(file)
        elif ext == 'txt':
            return self.extract_text_from_txt(file)
        else:
            return ""

    def create_rag_vector_store(self, text):
        if not text.strip():
            return None
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        embeddings = OpenAIEmbeddings(api_key=self.api_key, base_url=self.base_url)
        return FAISS.from_texts(chunks, embeddings)

    def create_simple_vector_store(self, text):
        if not text.strip():
            return None
        embeddings = OpenAIEmbeddings(api_key=self.api_key, base_url=self.base_url)
        return FAISS.from_texts([text], embeddings)

    def extract_skills_from_jd(self, jd_text):
        llm = self.get_llm(temperature=0.0, response_format={"type": "json_object"})
        prompt = f"""
Extract only the required technical skills, tools, frameworks, and technologies from this job description.

Return a valid JSON array of strings. Example:
["Python", "React", "AWS", "Docker"]

Do not include soft skills, years of experience, or responsibilities.

Job Description:
{jd_text}

Return only the JSON array:
"""

        try:
            response = llm.invoke(prompt)
            content = response.content.strip()

            # Extract JSON array
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                skills = json.loads(match.group(0))
                return [s.strip() for s in skills if isinstance(s, str)]
        except Exception as e:
            print(f"Skill extraction failed: {e}")

        # Fallback: line-by-line parsing
        skills = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('-', '*', '•')):
                skill = line[1:].strip().split(',')[0].strip(' "')
                if skill:
                    skills.append(skill)
        return skills

    def analyze_skill_presence(self, resume_text, skill):
        vectorstore = self.create_simple_vector_store(resume_text)
        if not vectorstore:
            return 0, "No resume content."

        retriever = vectorstore.as_retriever()
        llm = self.get_llm(temperature=0.0)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False
        )

        query = f"""
On a scale of 0–10, how clearly and strongly does the resume demonstrate experience with "{skill}"?
Rate based on:
- Explicit mentions
- Projects or achievements using it
- Depth of usage described

Respond with ONLY a number from 0 to 10, followed by a brief reason.
Example: 8 - Multiple projects using React with Redux and TypeScript.
"""

        try:
            response = qa_chain.invoke({"query": query})["result"]
            match = re.search(r'^(\d{1,2})', response.strip())
            score = int(match.group(1)) if match else 0
            reason = response.strip()[match.end():].strip(" -:.")
            return min(score, 10), reason or "No clear evidence found."
        except:
            return 0, "Analysis failed."

    def semantic_skill_analysis(self, resume_text, skills):
        if not skills:
            return {"overall_score": 0, "selected": False, "reasoning": "No skills defined."}

        skill_scores = {}
        skill_reasoning = {}
        total_score = 0

        for skill in skills:
            score, reasoning = self.analyze_skill_presence(resume_text, skill)
            skill_scores[skill] = score
            skill_reasoning[skill] = reasoning
            total_score += score

        avg_score = total_score / len(skills) if skills else 0
        overall_score = int((avg_score / 10) * 100)
        selected = overall_score >= self.cutoff_score

        strengths = [s for s, sc in skill_scores.items() if sc >= 7]
        missing_skills = [s for s, sc in skill_scores.items() if sc <= 5]

        return {
            "overall_score": overall_score,
            "skill_scores": skill_scores,
            "skill_reasoning": skill_reasoning,
            "selected": selected,
            "reasoning": f"Scored {len(skills)} required skills. Average proficiency: {avg_score:.1f}/10.",
            "strengths": strengths,
            "missing_skills": missing_skills,
        }

    def analyze_resume_weaknesses(self):
        weaknesses = []
        for skill in self.analysis_result.get("missing_skills", []):
            llm = self.get_llm(temperature=0.3, response_format={"type": "json_object"})
            prompt = f"""
Analyze why the resume is weak in demonstrating "{skill}".

Resume excerpt:
{self.resume_text[:3000]}

Return valid JSON only:
{{
  "weakness": "One-sentence summary of the issue",
  "improvement_suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"],
  "example_addition": "One strong bullet point to add"
}}
"""

            try:
                response = llm.invoke(prompt)
                data = json.loads(response.content.strip())
                weaknesses.append({
                    "skill": skill,
                    "score": self.analysis_result["skill_scores"].get(skill, 0),
                    "detail": data.get("weakness", "Lack of clear examples."),
                    "suggestions": data.get("improvement_suggestions", []),
                    "example": data.get("example_addition", "")
                })
            except:
                weaknesses.append({
                    "skill": skill,
                    "score": self.analysis_result["skill_scores"].get(skill, 0),
                    "detail": "No strong demonstration of this skill.",
                    "suggestions": ["Add specific projects or achievements using this skill."],
                    "example": ""
                })
        self.resume_weaknesses = weaknesses
        return weaknesses

    def analyze_resume(self, resume_file, role_requirements=None, custom_jd=None):
        self.resume_text = self.extract_text_from_file(resume_file)
        if not self.resume_text.strip():
            raise ValueError("Could not extract text from resume.")

        self.rag_vectorstore = self.create_rag_vector_store(self.resume_text)

        if custom_jd:
            self.jd_text = self.extract_text_from_file(custom_jd)
            self.extracted_skills = self.extract_skills_from_jd(self.jd_text)
        elif role_requirements:
            self.extracted_skills = role_requirements
        else:
            raise ValueError("No job requirements provided.")

        self.analysis_result = self.semantic_skill_analysis(self.resume_text, self.extracted_skills)

        if self.analysis_result["missing_skills"]:
            self.analyze_resume_weaknesses()
            self.analysis_result["detailed_weaknesses"] = self.resume_weaknesses

        return self.analysis_result

    def ask_question(self, question):
        if not self.rag_vectorstore:
            return "Please analyze a resume first."

        retriever = self.rag_vectorstore.as_retriever(search_kwargs={"k": 4})
        llm = self.get_llm(temperature=0.2)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False
        )
        try:
            result = qa_chain.invoke({"query": question})
            return result["result"]
        except Exception as e:
            return f"Error answering question: {e}"

    def generate_interview_questions(self, question_types, difficulty, num_questions):
        if not self.resume_text or not self.extracted_skills:
            return []

        llm = self.get_llm(temperature=0.7)
        context = f"""
Resume Summary:
{self.resume_text[:2000]}

Key Skills: {', '.join(self.extracted_skills)}
Strengths: {', '.join(self.analysis_result.get('strengths', []))}
Weaknesses: {', '.join(self.analysis_result.get('missing_skills', []))}
"""

        prompt = f"""
Generate exactly {num_questions} {difficulty}-level interview questions of these types: {', '.join(question_types)}.

Make them personalized to the candidate's experience.

Return valid JSON only:
[
  {{"type": "Technical", "question": "Full question here"}},
  {{"type": "Behavioral", "question": "Full question here"}}
]

{context}
"""

        try:
            response = llm.invoke(prompt)
            content = response.content.strip()
            questions = json.loads(content)
            return [(q["type"], q["question"]) for q in questions[:num_questions]]
        except:
            # Fallback manual parsing
            questions = []
            lines = content.split('\n')
            current_type = None
            current_q = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                for t in question_types:
                    if t.lower() in line.lower() and ':' in line:
                        if current_type and current_q:
                            questions.append((current_type, current_q.strip()))
                        current_type = t
                        current_q = line.split(':', 1)[1].strip()
                        break
                else:
                    if current_type:
                        current_q += " " + line
            if current_type and current_q:
                questions.append((current_type, current_q.strip()))
            return questions[:num_questions]

    def improve_resume(self, improvement_areas, target_role=""):
        if not self.resume_text:
            return {}

        improvements = {}
        for area in improvement_areas:
            if area == "Skills Highlighting" and self.resume_weaknesses:
                skill_suggestions = {"description": "Better highlight missing or weak skills.", "specific": []}
                for w in self.resume_weaknesses:
                    skill = w["skill"]
                    for s in w.get("suggestions", []):
                        skill_suggestions["specific"].append(f"**{skill}**: {s}")
                improvements[area] = skill_suggestions

        # For other areas, use LLM
        remaining = [a for a in improvement_areas if a not in improvements]
        if remaining:
            llm = self.get_llm(temperature=0.4)
            prompt = f"""
Provide detailed resume improvement suggestions for: {', '.join(remaining)}

Target Role: {target_role or "General Improvement"}

Resume:
{self.resume_text[:3000]}

Return valid JSON with area names as keys.
"""
            try:
                response = llm.invoke(prompt)
                data = json.loads(response.content.strip())
                improvements.update(data)
            except:
                pass

        # Ensure all areas are covered
        for area in improvement_areas:
            if area not in improvements:
                improvements[area] = {
                    "description": f"Improve {area.lower()} for better impact.",
                    "specific": ["Review and enhance this section."]
                }
        return improvements

    def get_improved_resume(self, target_role="", highlight_skills=""):
        if not self.resume_text:
            return "No resume analyzed."

        skills_to_highlight = []
        if highlight_skills.strip():
            if len(highlight_skills) > 100:
                skills_to_highlight = self.extract_skills_from_jd(highlight_skills)
            else:
                skills_to_highlight = [s.strip() for s in highlight_skills.split(',') if s.strip()]

        if not skills_to_highlight and self.extracted_skills:
            skills_to_highlight = self.extracted_skills

        llm = self.get_llm(temperature=0.7)
        weakness_examples = "\n".join([
            f"Add: {w.get('example', '')}" for w in self.resume_weaknesses if w.get('example')
        ])

        prompt = f"""
Rewrite this resume to be highly optimized for: {target_role or "the analyzed role"}

Prioritize highlighting: {', '.join(skills_to_highlight)}

Original Resume:
{self.resume_text}

Add strong, quantifiable achievements.
Use ATS-friendly formatting.
Address weak areas with specific examples.

Examples to include:
{weakness_examples}

Return only the improved resume text in clean, professional format.
"""

        try:
            response = llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            return f"Error generating improved resume: {e}"