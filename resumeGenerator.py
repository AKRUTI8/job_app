import json
import os
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class ResumeGenerator:
    """Base class for ATS resume generation using LLM"""
    
    def __init__(self):
        """Initialize with Groq client"""
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    def load_candidate_data(self, json_file_path):
        """Load the candidate data from JSON file"""
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def extract_job_keywords(self, job_description):
        """Extract ATS keywords from job description using Groq API"""
        
        prompt = f"""Analyze this job description and extract ALL ATS-critical keywords.

JOB DESCRIPTION:
Title: {job_description.get('job_title', 'N/A')}
Company: {job_description.get('company', 'N/A')}
Description: {job_description['description']}

Extract the following in valid JSON format:

1. HARD SKILLS (Technical/Domain-Specific):
   - Exact technical skills, tools, platforms, programming languages
   - Software, systems, frameworks (with proper capitalization)
   - Certifications and licenses mentioned
   - Include both acronyms AND full forms (e.g., "AI" and "Artificial Intelligence")

2. SOFT SKILLS (Behavioral/Interpersonal):
   - Leadership, communication, teamwork, problem-solving
   - Time management, adaptability, creativity
   - Extract implicitly mentioned skills (e.g., "fast-paced" = adaptability)

3. EXPERIENCE REQUIREMENTS:
   - Years of experience required
   - Seniority level (junior/mid/senior/lead)
   - Industry experience needed

4. EDUCATION & CERTIFICATIONS:
   - Degree requirements
   - Specific certifications
   - Preferred educational background

5. KEY ACTION VERBS:
   - Power verbs used in job description (developed, managed, led, etc.)

6. EXACT PHRASES:
   - Multi-word phrases that must appear together
   - Example: "cross-functional teams", "project management", "data-driven"

7. QUANTITATIVE TERMS:
   - Metrics, KPIs, percentages mentioned
   - Numbers that indicate scale or impact

8. PRIORITY KEYWORDS (Top 20):
   - Most critical keywords for ATS scoring
   - Must-have skills and requirements

Return ONLY valid JSON (no markdown, no code blocks):

{{
  "industry": "string",
  "role_level": "string",
  "hard_skills": ["skill1", "skill2"],
  "soft_skills": ["skill1", "skill2"],
  "tools_platforms": ["tool1", "tool2"],
  "certifications": ["cert1", "cert2"],
  "education_requirements": ["requirement1"],
  "experience_required": "string",
  "key_action_verbs": ["verb1", "verb2"],
  "exact_phrases": ["phrase1", "phrase2"],
  "acronym_variations": {{"acronym": "full_form"}},
  "priority_keywords": ["keyword1", "keyword2"],
  "quantitative_terms": ["term1", "term2"]
}}"""

        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an ATS keyword extraction expert. Extract ALL relevant keywords from job descriptions. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=2000,
        )
        
        response_text = response.choices[0].message.content.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            keywords = json.loads(response_text)
            return keywords
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing keywords: {e}")
            return None

    def generate_ats_resume_and_cover_letter(self, resume_data, job_description, extracted_keywords):
        """Generate ATS-optimized resume (90%+ score) and cover letter"""
        
        prompt = f"""You are an elite ATS resume writer with a 95% interview success rate. Create a resume that:
- Scores 90%+ on ALL ATS systems
- Passes AI detection (appears 100% human-written)
- Uses natural, varied language (no repetition)

CANDIDATE DATA:
{json.dumps(resume_data, indent=2)}

TARGET JOB:
Title: {job_description['job_title']}
Company: {job_description['company']}
Location: {job_description['location']}
Description: {job_description['description']}

EXTRACTED KEYWORDS:
{json.dumps(extracted_keywords, indent=2)}

===== CRITICAL RULES =====

1. CONTACT INFORMATION (MANDATORY):
   - Full Name (exact from candidate data)
   - Email (exact from candidate data)
   - Phone (exact from candidate data, format: (XXX) XXX-XXXX or XXX-XXX-XXXX)
   - Location (City, State format)
   - LinkedIn URL (if available, must include https://)

2. PROFESSIONAL SUMMARY (3-4 sentences, 60-80 words):
   - First sentence: Role + key expertise (NO years if unclear from data)
   - Second sentence: 3-5 hard skills from priority_keywords
   - Third sentence: Notable achievement with metric (ONLY if in candidate data)
   - Fourth sentence: Value proposition for target role
   - Must include 6-8 priority keywords naturally
   - Sound conversational, not robotic

3. HARD SKILLS SECTION:
   - List 15-25 distinct technical skills
   - Use exact terminology from job description
   - Group logically: Languages, Frameworks, Tools, Platforms, Technologies
   - Include acronyms with full forms first time: "Machine Learning (ML)"
   - NO generic terms like "programming" or "coding"
   - Match capitalization exactly (React.js, Python, AWS, CI/CD)

4. SOFT SKILLS SECTION (Separate):
   - List 6-10 soft skills from extracted keywords
   - Use exact terms: "Leadership", "Team Collaboration", "Problem Solving"
   - DO NOT demonstrate here - save that for experience bullets

5. EDUCATION (Standard Format):
   - Degree Name | Institution Name
   - Graduation Date (MM/YYYY) or "Expected MM/YYYY"
   - Match education_requirements when possible

6. EXPERIENCE (Chronological, Most Recent First):
   - Format: Job Title | Company Name | Location | MM/YYYY - MM/YYYY or "Present"
   - 6-10 bullet points per role (recent roles get more bullets)
   - Each bullet MUST:
     * Start with UNIQUE action verb (never repeat verbs across resume)
     * Describe DIFFERENT accomplishment/project/responsibility
     * Include 2-4 keywords (mix of hard + soft skills demonstrated)
     * Use metrics ONLY if in candidate data
     * Be 15-25 words long
   - Bullet structure: [Action Verb] + [what you did] + [how/tools used] + [result/impact]
   - Example: "Developed RESTful API using Python and FastAPI, integrating PostgreSQL database and reducing response time by 40%"
   - Show soft skills through action: "Led team of 5" (leadership), "Collaborated with stakeholders" (teamwork)

7. PROJECTS (If applicable):
   - Project Name | Brief Description
   - 3-5 bullets per project
   - Focus on technical skills, tools, outcomes
   - Use unique action verbs (different from experience section)

8. ACHIEVEMENTS (Optional):
   - Awards, recognitions, publications
   - Relevant certifications
   - Keep brief, 1-2 lines each

9. KEYWORD OPTIMIZATION STRATEGY:
   - Priority keywords must appear 2-4 times throughout resume
   - Use variations: "led" vs "leadership", "ML" vs "Machine Learning"
   - Spread keywords across all sections: summary, skills, experience
   - Use exact phrases from job description where they fit
   - NO keyword stuffing (must read naturally)

10. WRITING STYLE (CRITICAL FOR HUMAN DETECTION):
    - Vary sentence structure: mix 10-word and 20-word bullets
    - Use 40+ unique action verbs (NEVER repeat)
    - Each bullet describes DIFFERENT work (no redundancy)
    - Mix technical depth with business impact
    - Include specific details that feel authentic
    - Avoid AI patterns: no excessive adjectives, no generic phrases

11. COVER LETTER (3-4 paragraphs):
    - Paragraph 1 (Opening): Express interest, mention position, 1-2 keywords
    - Paragraph 2 (Experience): Highlight relevant experience with story, 3-4 keywords
    - Paragraph 3 (Value): What you bring to company, align with their mission
    - Paragraph 4 (Closing): Call to action, enthusiasm
    - Total: 250-350 words
    - Use conversational tone, contractions (I'm, I've), personal pronouns
    - Show genuine company research
    - Natural language, not robotic

12. TRUTHFULNESS (ABSOLUTE REQUIREMENT):
    - ONLY use information from candidate data
    - NEVER fabricate years of experience, skills, or achievements
    - If data is missing, describe qualitatively without inventing numbers
    - Calculate experience from actual dates provided
    - Don't inflate job titles or responsibilities

===== OUTPUT FORMAT =====

Return ONLY valid JSON (no markdown, no explanations):

{{
  "ats_optimized_resume": {{
    "contact_information": {{
      "name": "Full Name",
      "email": "email@example.com",
      "phone": "(XXX) XXX-XXXX",
      "location": "City, State",
      "linkedin": "https://linkedin.com/in/profile"
    }},
    "professional_summary": "3-4 sentence summary with 6-8 priority keywords naturally integrated",
    "hard_skills": [
      "Skill 1", "Skill 2", "Skill 3"
    ],
    "soft_skills": [
      "Soft Skill 1", "Soft Skill 2"
    ],
    "experience": [
      {{
        "title": "Job Title",
        "company": "Company Name",
        "location": "City, State",
        "duration": "MM/YYYY - MM/YYYY",
        "responsibilities": [
          "Bullet point 1 with unique action verb",
          "Bullet point 2 with different action verb"
        ]
      }}
    ],
    "education": [
      {{
        "degree": "Degree Name",
        "institution": "Institution Name",
        "graduation_date": "MM/YYYY"
      }}
    ],
    "projects": [
      {{
        "name": "Project Name",
        "description": "Brief description",
        "highlights": [
          "Achievement 1",
          "Achievement 2"
        ]
      }}
    ],
    "achievements": [
      "Achievement 1",
      "Achievement 2"
    ]
  }},
  "cover_letter": {{
    "greeting": "Dear Hiring Manager,",
    "body": "3-4 paragraph cover letter text here as continuous text...",
    "closing": "Sincerely,\\n[Candidate Name]"
  }},
  "ats_analysis": {{
    "estimated_score": "90-95%",
    "keywords_used": ["keyword1", "keyword2"],
    "keyword_count": 45,
    "unique_action_verbs": 42,
    "priority_keyword_coverage": "18/20 (90%)",
    "strengths": [
      "Strength 1",
      "Strength 2"
    ],
    "humanization_score": "95% (appears human-written)"
  }}
}}

Make this resume undetectable as AI-written while scoring 90%+ on ATS."""

        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are an elite resume writer specializing in ATS optimization. Your resumes:
- Score 90-95% on ATS systems
- Pass AI detection as 100% human-written
- Use natural, varied language with zero repetition
- Include proper contact information
- Follow professional formatting standards

Always output valid JSON only. No markdown, no code blocks, no explanations."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=8000,
            top_p=0.9,
        )
        
        response_text = response.choices[0].message.content.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing resume: {e}")
            print(f"Response preview: {response_text[:300]}...")
            return None

    def save_output(self, output_data, output_file_path):
        """Save the generated resume and cover letter to a JSON file"""
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, indent=2, fp=f, ensure_ascii=False)
        print(f"\n✅ Output saved to: {output_file_path}")


def main():
    """Standalone main function for JSON-only output"""
    # Configuration
    input_file = r"D:\internship\chatbot\outputs\matched.json"
    output_file = f"ats_resume_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Check API key
    if not os.environ.get("GROQ_API_KEY"):
        print("\n❌ ERROR: GROQ_API_KEY not found in environment")
        print("\nAdd to .env file:")
        print("GROQ_API_KEY=your-api-key-here")
        return None
    
    # Initialize generator
    generator = ResumeGenerator()
    
    print("=" * 70)
    print("🚀 ATS Resume Generator (90%+ Score Guaranteed)")
    print("=" * 70)
    
    print("\n📂 Loading candidate data...")
    candidate_data = generator.load_candidate_data(input_file)
    
    resume_data = candidate_data['resume']
    first_job = candidate_data['matches'][1]
    
    print(f"\n👤 Candidate: {resume_data['candidate_name']}")
    print(f"🎯 Target Job: {first_job['job_title']}")
    print(f"🏢 Company: {first_job['company']}")
    
    # Step 1: Extract keywords
    print("\n" + "=" * 70)
    print("STEP 1: Extracting ATS Keywords...")
    print("=" * 70)
    
    extracted_keywords = generator.extract_job_keywords(first_job)
    
    if not extracted_keywords:
        print("❌ Keyword extraction failed")
        return None
    
    print(f"\n✅ Keywords extracted!")
    print(f"   📊 Priority Keywords: {len(extracted_keywords.get('priority_keywords', []))}")
    print(f"   🔧 Hard Skills: {len(extracted_keywords.get('hard_skills', []))}")
    print(f"   💡 Soft Skills: {len(extracted_keywords.get('soft_skills', []))}")
    
    # Step 2: Generate resume
    print("\n" + "=" * 70)
    print("STEP 2: Generating ATS-Optimized Resume...")
    print("=" * 70)
    print("⏳ Processing (30-60 seconds)...")
    
    result = generator.generate_ats_resume_and_cover_letter(
        resume_data, first_job, extracted_keywords
    )
    
    if not result:
        print("❌ Resume generation failed")
        return None
    
    # Prepare output
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "target_job": {
            "title": first_job['job_title'],
            "company": first_job['company'],
            "location": first_job['location']
        },
        "extracted_keywords": extracted_keywords,
        "ats_optimized_resume": result.get('ats_optimized_resume'),
        "cover_letter": result.get('cover_letter'),
        "ats_analysis": result.get('ats_analysis', {})
    }
    
    generator.save_output(output_data, output_file)
    
    # Print results
    print("\n" + "=" * 70)
    print("✅ SUCCESS! Resume Generated")
    print("=" * 70)
    
    analysis = result.get('ats_analysis', {})
    print(f"\n📊 ATS Score: {analysis.get('estimated_score', 'N/A')}")
    print(f"🔑 Keywords Used: {analysis.get('keyword_count', 0)}")
    print(f"🎯 Priority Coverage: {analysis.get('priority_keyword_coverage', 'N/A')}")
    print(f"🤖 Human Score: {analysis.get('humanization_score', 'N/A')}")
    print(f"\n📁 File: {output_file}")
    print("=" * 70)
    
    return output_data


if __name__ == "__main__":
    main()