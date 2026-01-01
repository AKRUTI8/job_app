"""
Resume Processing Module
Handles PDF parsing, information extraction, and embedding generation
"""

import os
import json
from typing import Dict, Optional
from datetime import datetime
import hashlib

import PyPDF2
from openai import OpenAI


class ResumeProcessor:
    """Process resume PDFs: extract text, parse info, generate embeddings"""
    
    def __init__(self, openai_api_key: str):
        """Initialize with OpenAI API key"""
        self.client = OpenAI(api_key=openai_api_key)
        self.embedding_model = "text-embedding-3-small"
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                print(f"📄 Reading PDF: {num_pages} pages")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    text += page_text + "\n"
                
                print(f"✓ Extracted {len(text)} characters")
                return text.strip()
                
        except Exception as e:
            print(f"❌ Error extracting text from PDF: {e}")
            return ""
    
    def extract_resume_info(self, resume_text: str, resume_filename: str) -> Dict:
        """Extract structured information from resume text using LLM"""
        prompt = f"""Extract the following information from this resume. Return ONLY a valid JSON object:

{{
  "resume_id": "generate a unique ID from the candidate name",
  "candidate_name": "full name of the candidate",
  "email": "email address if mentioned",
  "phone": "phone number if mentioned",
  "location": "current location or preferred location",
  "summary": "professional summary or objective (2-3 sentences)",
  "skills": ["skill1", "skill2", "skill3"],
  "experience_years": "total years of experience (number or range)",
  "education": "highest education degree and institution",
  "job_titles": ["current/recent job titles"],
  "key_achievements": "top 3-5 achievements or highlights",
  "full_text": "complete resume text for embedding"
}}

Resume:
{resume_text[:10000]}

Return only the JSON object, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from resumes. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content.strip()
            
            # Remove markdown
            for marker in ["```json", "```"]:
                result = result.replace(marker, "")
            result = result.strip()
            
            resume_info = json.loads(result)
            
            # Ensure all fields exist
            defaults = {
                "resume_id": f"resume-{hashlib.md5(resume_filename.encode()).hexdigest()[:8]}",
                "candidate_name": "Not specified",
                "email": "Not specified",
                "phone": "Not specified",
                "location": "Not specified",
                "summary": "Not specified",
                "skills": [],
                "experience_years": "Not specified",
                "education": "Not specified",
                "job_titles": [],
                "key_achievements": "Not specified",
                "full_text": resume_text
            }
            
            for field, default in defaults.items():
                if field not in resume_info:
                    resume_info[field] = default
            
            resume_info['filename'] = resume_filename
            resume_info['processed_at'] = datetime.utcnow().isoformat()
            
            return resume_info
            
        except Exception as e:
            print(f"❌ Error extracting resume info: {e}")
            return {
                "resume_id": f"error-{hashlib.md5(resume_filename.encode()).hexdigest()[:8]}",
                "candidate_name": "Error",
                "email": "Not specified",
                "phone": "Not specified",
                "location": "Not specified",
                "summary": "Error extracting information",
                "skills": [],
                "experience_years": "Not specified",
                "education": "Not specified",
                "job_titles": [],
                "key_achievements": "Error extracting information",
                "full_text": resume_text,
                "filename": resume_filename,
                "processed_at": datetime.utcnow().isoformat()
            }
    
    def generate_embedding(self, text: str) -> Optional[list]:
        """Generate embedding for text"""
        try:
            max_chars = 30000
            if len(text) > max_chars:
                text = text[:max_chars]
            
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return None
    
    def process_resume_pdf(self, pdf_path: str) -> Optional[Dict]:
        """Process a resume PDF: extract, parse, embed"""
        print(f"\nProcessing: {os.path.basename(pdf_path)}")
        
        # Extract text
        resume_text = self.extract_text_from_pdf(pdf_path)
        if not resume_text:
            return None
        
        # Extract structured info
        print("📝 Extracting structured information...")
        resume_filename = os.path.basename(pdf_path)
        resume_info = self.extract_resume_info(resume_text, resume_filename)
        
        print(f"✓ Candidate: {resume_info['candidate_name']}")
        print(f"✓ Skills: {len(resume_info['skills'])} found")
        
        # Generate embedding
        print("🧠 Generating embedding...")
        embedding = self.generate_embedding(resume_info['full_text'])
        
        if not embedding:
            return None
        
        resume_info['resume_embedding'] = embedding
        resume_info['embedding_created_at'] = datetime.utcnow().isoformat()
        print(f"✓ Embedding created ({len(embedding)} dimensions)")
        
        return resume_info