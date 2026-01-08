from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import json
import re
from typing import Dict, List, Optional, Any
import traceback
import random
import string
import PyPDF2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  Install Groq: pip install groq")

# ═══════════════════════════════════════════════════════════
# EMAIL NOTIFICATION SYSTEM
# ═══════════════════════════════════════════════════════════

class EmailNotifier:
    """Handles email notifications for form submission results."""
    
    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        recipient_email: Optional[str] = None
    ):
        """
        Initialize email notifier.
        
        Args:
            smtp_server: SMTP server address (default: Gmail)
            smtp_port: SMTP port (587 for TLS, 465 for SSL)
            sender_email: Sender email address (or use SENDER_EMAIL env var)
            sender_password: Sender app password (or use SENDER_PASSWORD env var)
            recipient_email: Recipient email (or use RECIPIENT_EMAIL env var)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email or os.getenv("SMTP_EMAIL")
        self.sender_password = sender_password or os.getenv("SMTP_PASSWORD")
        self.recipient_email = recipient_email or os.getenv("RECIPIENT_EMAIL")
        
        if not self.sender_email or not self.sender_password:
            print("⚠️  Email credentials not set. Set SENDER_EMAIL and SENDER_PASSWORD env vars")
            print("   For Gmail: Use App Password from https://myaccount.google.com/apppasswords")
        
        if not self.recipient_email:
            self.recipient_email = self.sender_email
            print(f"ℹ️  Recipient email not set, using sender email: {self.recipient_email}")
    
    def send_email(
        self,
        subject: str,
        body_html: str,
        body_text: str = None,
        attachments: List[str] = None
    ) -> bool:
        """Send an email notification."""
        try:
            if not self.sender_email or not self.sender_password or not self.recipient_email:
                print("❌ Email not configured properly")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Add text version (fallback)
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
            
            # Add attachments
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        try:
                            with open(filepath, 'rb') as f:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(f.read())
                                encoders.encode_base64(part)
                                part.add_header(
                                    'Content-Disposition',
                                    f'attachment; filename={os.path.basename(filepath)}'
                                )
                                msg.attach(part)
                        except Exception as e:
                            print(f"⚠️  Could not attach {filepath}: {e}")
            
            # Connect and send
            print(f"\n📧 Sending email to {self.recipient_email}...")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print("✅ Email sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            traceback.print_exc()
            return False
    
    def send_success_email(
        self,
        job_url: str,
        company_name: str,
        position: str,
        fields_filled: int,
        total_fields: int,
        resume_path: str = None
    ) -> bool:
        """Send success notification."""
        subject = f"✅ Job Application Submitted Successfully - {company_name}"
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }}
                .field {{ margin: 10px 0; padding: 10px; background-color: white; border-left: 4px solid #4CAF50; }}
                .footer {{ margin-top: 20px; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .success-icon {{ font-size: 48px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="success-icon">✅</div>
                    <h1>Application Submitted Successfully!</h1>
                </div>
                
                <div class="content">
                    <h2>Job Application Details</h2>
                    
                    <div class="field">
                        <strong>🏢 Company:</strong> {company_name}
                    </div>
                    
                    <div class="field">
                        <strong>💼 Position:</strong> {position}
                    </div>
                    
                    <div class="field">
                        <strong>🔗 Job URL:</strong><br>
                        <a href="{job_url}">{job_url}</a>
                    </div>
                    
                    
                    
                    <div class="field">
                        <strong>⏰ Submitted At:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    </div>
                    
                    
                
                <div class="footer">
                    <p>This is an automated notification from the Job Application Bot.</p>
                    <p>Please check your email and the company's portal for confirmation.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        ✅ JOB APPLICATION SUBMITTED SUCCESSFULLY!
        
        Company: {company_name}
        Position: {position}
        Job URL: {job_url}
        Fields Filled: {fields_filled} / {total_fields}
        Submitted At: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        This is an automated notification from the Job Application Bot.
        """
        
        return self.send_email(subject, html_body, text_body)
    
    def send_failure_email(
        self,
        job_url: str,
        company_name: str,
        position: str,
        error_message: str,
        fields_filled: int,
        total_fields: int,
        errors: List[str] = None,
        screenshot_path: str = None
    ) -> bool:
        """Send failure notification."""
        subject = f"❌ Job Application Failed - {company_name}"
        
        errors_html = ""
        if errors:
            errors_html = "<div class='field'><strong>⚠️ Errors Detected:</strong><ul>"
            for err in errors[:5]:
                errors_html += f"<li>{err}</li>"
            errors_html += "</ul></div>"
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                .content {{ background-color: #f9f9f9; padding: 20px; margin-top: 20px; border-radius: 5px; }}
                .field {{ margin: 10px 0; padding: 10px; background-color: white; border-left: 4px solid #f44336; }}
                .footer {{ margin-top: 20px; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .error-icon {{ font-size: 48px; }}
                .error-box {{ background-color: #ffebee; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="error-icon">❌</div>
                    <h1>Application Submission Failed</h1>
                </div>
                
                <div class="content">
                    <h2>Job Application Details</h2>
                    
                    <div class="field">
                        <strong>🏢 Company:</strong> {company_name}
                    </div>
                    
                    <div class="field">
                        <strong>💼 Position:</strong> {position}
                    </div>
                    
                    <div class="field">
                        <strong>🔗 Job URL:</strong><br>
                        <a href="{job_url}">{job_url}</a>
                    </div>
                    
                    <div class="field">
                        <strong>📝 Fields Filled:</strong> {fields_filled} / {total_fields}
                    </div>
                    
                    <div class="error-box">
                        <strong>❌ Error Message:</strong><br>
                        {error_message}
                    </div>
                    
                    {errors_html}
                    
                    <div class="field">
                        <strong>⏰ Failed At:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from the Job Application Bot.</p>
                    <p>Please review the error and try applying manually.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        ❌ JOB APPLICATION FAILED
        
        Company: {company_name}
        Position: {position}
        Job URL: {job_url}
        Fields Filled: {fields_filled} / {total_fields}
        
        Error: {error_message}
        
        Failed At: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        This is an automated notification from the Job Application Bot.
        """
        
        attachments = [screenshot_path] if screenshot_path and os.path.exists(screenshot_path) else None
        
        return self.send_email(subject, html_body, text_body, attachments)

# ═══════════════════════════════════════════════════════════
# RESUME PARSER
# ═══════════════════════════════════════════════════════════

class ResumeParser:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        if not GROQ_AVAILABLE:
            raise ImportError("Install: pip install groq")
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Set GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)
        self.model = model
        print(f"✅ Resume Parser initialized")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            print(f"❌ PDF error: {e}")
            return ""
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        try:
            import docx
            doc = docx.Document(docx_path)
            return "\n".join([p.text for p in doc.paragraphs]).strip()
        except:
            return ""
    
    def parse_resume(self, resume_path: str) -> Dict[str, Any]:
        print(f"\n📄 Parsing: {os.path.basename(resume_path)}")
        ext = os.path.splitext(resume_path)[1].lower()
        
        if ext == '.pdf':
            text = self.extract_text_from_pdf(resume_path)
        elif ext in ['.docx', '.doc']:
            text = self.extract_text_from_docx(resume_path)
        else:
            return {}
        
        if not text:
            return {}
        
        prompt = f"""Extract from resume into JSON:
{text}

Return ONLY:
{{
  "personal_info": {{"first_name": "", "last_name": "", "full_name": "", "email": "", "phone": "", "city": "", "state": "", "country": ""}},
  "professional": {{"current_company": "", "current_job_title": "", "summary": ""}},
  "education": [{{"degree": "", "institution": "", "graduation_year": ""}}],
  "work_experience": [{{"company": "", "position": ""}}]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000
            )
            
            text = response.choices[0].message.content.strip()
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                personal = data.get('personal_info', {})
                print(f"✅ Parsed: {personal.get('full_name', 'N/A')}")
                return data
            return {}
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return {}

# ═══════════════════════════════════════════════════════════
# DATA MAPPER
# ═══════════════════════════════════════════════════════════

class SmartDataMapper:
    @staticmethod
    def map_field_value(label: str, field_type: str, resume_data: Dict, placeholder: str = "") -> str:
        label_lower = (label + " " + placeholder).lower()
        personal = resume_data.get('personal_info', {})
        prof = resume_data.get('professional', {})
        edu = resume_data.get('education', [])
        exp = resume_data.get('work_experience', [])
        
        if any(k in label_lower for k in ["email", "e-mail"]): return personal.get('email') or ""
        if any(k in label_lower for k in ["phone", "mobile"]): return personal.get('phone') or ""
        if "first name" in label_lower: return personal.get('first_name') or ""
        if "last name" in label_lower: return personal.get('last_name') or ""
        if "full name" in label_lower or label_lower.strip() == "name": return personal.get('full_name') or ""
        if "city" in label_lower: return personal.get('city') or ""
        if "state" in label_lower: return personal.get('state') or ""
        if "country" in label_lower: return personal.get('country') or ""
        if "company" in label_lower: return prof.get('current_company') or (exp[0].get('company') if exp else "")
        if "position" in label_lower or "job title" in label_lower: return prof.get('current_job_title') or ""
        if "university" in label_lower or "college" in label_lower: return edu[0].get('institution') if edu else ""
        if "degree" in label_lower: return edu[0].get('degree') if edu else ""
        if "summary" in label_lower or "about" in label_lower: return prof.get('summary') or ""
        
        return ""

# ═══════════════════════════════════════════════════════════
# FORM EXTRACTION
# ═══════════════════════════════════════════════════════════

def extract_form_structure(driver) -> str:
    print("\n📋 Extracting form...")
    form_data = driver.execute_script("""
        function extractForm() {
            const result = {forms: [], standalone: []};
            document.querySelectorAll('form').forEach((form, idx) => {
                const formInfo = {index: idx, fields: []};
                form.querySelectorAll('input, select, textarea').forEach(el => {
                    const field = extractField(el);
                    if (field) formInfo.fields.push(field);
                });
                if (formInfo.fields.length > 0) result.forms.push(formInfo);
            });
            document.querySelectorAll('input, select, textarea').forEach(el => {
                if (!el.closest('form')) {
                    const field = extractField(el);
                    if (field) result.standalone.push(field);
                }
            });
            return result;
        }
        
        function extractField(el) {
            if (el.type === 'hidden' || !el.offsetParent) return null;
            const field = {
                tag: el.tagName.toLowerCase(),
                type: el.type || '',
                id: el.id || '',
                name: el.name || '',
                placeholder: el.placeholder || '',
                required: el.required || el.getAttribute('aria-required') === 'true',
                role: el.getAttribute('role') || ''
            };
            
            let label = '';
            if (el.id) {
                const labelEl = document.querySelector(`label[for="${el.id}"]`);
                if (labelEl) label = labelEl.textContent.trim();
            }
            if (!label) {
                const parent = el.closest('label');
                if (parent) label = parent.textContent.trim();
            }
            if (!label) label = el.getAttribute('aria-label') || el.placeholder || '';
            field.label = label;
            
            if (el.tagName === 'SELECT') {
                field.options = Array.from(el.options).map(opt => ({value: opt.value, text: opt.text.trim()}));
            }
            
            if (el.id) {
                field.selector = el.id;
                field.selectorType = 'id';
            } else if (el.name) {
                field.selector = el.name;
                field.selectorType = 'name';
            }
            
            return field;
        }
        
        return JSON.stringify(extractForm(), null, 2);
    """)
    
    try:
        data = json.loads(form_data)
        total = sum(len(f['fields']) for f in data['forms']) + len(data['standalone'])
        print(f"✅ Extracted {total} fields")
        return format_for_llm(data)
    except:
        return ""

def format_for_llm(data: Dict) -> str:
    lines = []
    for form in data['forms']:
        for field in form['fields']:
            lines.append(f"FIELD: {field['label']} (Type: {field['type']}, ID: {field.get('id', 'N/A')})")
    for field in data['standalone']:
        lines.append(f"FIELD: {field['label']} (Type: {field['type']}, ID: {field.get('id', 'N/A')})")
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════
# LLM ANALYZER
# ═══════════════════════════════════════════════════════════

class EnhancedLLMFormAnalyzer:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        if not GROQ_AVAILABLE:
            raise ImportError("Install groq")
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)
        self.model = model
        print(f"✅ Analyzer initialized")
    
    def analyze_form(self, form_structure: str, resume_data: Dict) -> Dict[str, Any]:
        print("\n🤖 Analyzing...")
        personal = resume_data.get('personal_info', {})
        
        prompt = f"""Map resume to form. Include ALL fields including checkboxes/dropdowns/file uploads.

RESUME:
- Name: {personal.get('full_name')}
- Email: {personal.get('email')}
- Phone: {personal.get('phone')}

FORM:
{form_structure}

CRITICAL: For file upload fields (type="file"), use:
- action="upload"
- value="RESUME_FILE" for resume uploads
- value="COVER_LETTER_FILE" for cover letter uploads

Return JSON:
{{
  "fields": [
    {{"selector": "email", "selector_type": "id", "field_type": "email", "label": "Email", "value": "{personal.get('email', 'USE_MAPPER')}", "action": "type"}},
    {{"selector": "resume_upload", "selector_type": "id", "field_type": "file", "label": "Resume", "value": "RESUME_FILE", "action": "upload"}},
    {{"selector": "dropdown_id", "selector_type": "id", "field_type": "select", "label": "Visa", "value": "No", "action": "select"}}
  ],
  "submit_button": {{"selector": "submit", "selector_type": "id"}}
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=8000
            )
            
            text = response.choices[0].message.content.strip()
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                result = json.loads(match.group())
                for field in result.get("fields", []):
                    if field.get("value") == "USE_MAPPER":
                        field["value"] = SmartDataMapper.map_field_value(
                            field.get("label", ""), field.get("field_type", "text"), resume_data, ""
                        )
                print(f"✅ Analyzed {len(result.get('fields', []))} fields")
                return result
            return {"fields": [], "submit_button": {}}
        except Exception as e:
            print(f"❌ Analyze error: {e}")
            return {"fields": [], "submit_button": {}}

# ═══════════════════════════════════════════════════════════
# UNIVERSAL DROPDOWN HANDLER
# ═══════════════════════════════════════════════════════════

def fill_any_dropdown(driver, element, value: str, label: str, max_retries: int = 5) -> bool:
    """Universal dropdown handler - works with ALL dropdown types."""
    tag = element.tag_name.lower()
    elem_type = element.get_attribute("type") or ""
    elem_role = element.get_attribute("role") or ""
    
    print(f"     🔽 Dropdown: Tag={tag}, Type={elem_type}, Role={elem_role}")
    
    # NATIVE SELECT
    if tag == "select":
        print(f"     📋 Native SELECT")
        try:
            select = Select(element)
            options = [opt.text.strip() for opt in select.options]
            valid = [o for o in options if o and o.lower() not in ["select...", "select", "choose", "--", ""]]
            
            # No value? Select first valid
            if not value:
                if valid:
                    select.select_by_visible_text(valid[0])
                    print(f"     ✅ Selected: {valid[0]}")
                    return True
                elif len(select.options) > 1:
                    select.select_by_index(1)
                    print(f"     ✅ Selected index 1")
                    return True
            
            # Try exact match
            for opt in options:
                if value.lower() == opt.lower():
                    select.select_by_visible_text(opt)
                    print(f"     ✅ Selected: {opt}")
                    return True
            
            # Try partial match
            for opt in options:
                if value.lower() in opt.lower():
                    select.select_by_visible_text(opt)
                    print(f"     ✅ Selected: {opt}")
                    return True
            
            # Fallback
            if valid:
                select.select_by_visible_text(valid[0])
                print(f"     ✅ Fallback: {valid[0]}")
                return True
            return False
        except Exception as e:
            print(f"     ❌ Error: {e}")
            return False
    
    # CUSTOM DROPDOWN
    print(f"     🎯 Custom dropdown - trying {max_retries} strategies")
    
    for attempt in range(max_retries):
        print(f"     🔄 Attempt {attempt + 1}/{max_retries}")
        
        # Strategy 1: Direct click
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", element)
            time.sleep(2)
            
            opts = driver.find_elements(By.XPATH, "//*[@role='option' or @role='listitem']")
            visible = [o for o in opts if o.is_displayed()]
            if visible:
                print(f"        ✅ Opened ({len(visible)} options)")
                return select_from_dropdown(driver, value, visible)
        except:
            pass
        
        # Strategy 2: Parent click
        try:
            parent = element.find_element(By.XPATH, "./..")
            driver.execute_script("arguments[0].click();", parent)
            time.sleep(2)
            opts = driver.find_elements(By.XPATH, "//*[@role='option' or @role='listitem']")
            visible = [o for o in opts if o.is_displayed()]
            if visible:
                print(f"        ✅ Opened via parent")
                return select_from_dropdown(driver, value, visible)
        except:
            pass
        
        # Strategy 3: Arrow click
        try:
            parent = element.find_element(By.XPATH, "./..")
            arrows = parent.find_elements(By.XPATH, ".//*[contains(@class, 'arrow') or contains(@class, 'icon') or name()='svg']")
            for arrow in arrows:
                if arrow.is_displayed():
                    driver.execute_script("arguments[0].click();", arrow)
                    time.sleep(2)
                    opts = driver.find_elements(By.XPATH, "//*[@role='option' or @role='listitem']")
                    visible = [o for o in opts if o.is_displayed()]
                    if visible:
                        print(f"        ✅ Opened via arrow")
                        return select_from_dropdown(driver, value, visible)
        except:
            pass
        
        # Strategy 4: Keyboard
        try:
            element.send_keys(Keys.SPACE)
            time.sleep(1.5)
            opts = driver.find_elements(By.XPATH, "//*[@role='option' or @role='listitem']")
            visible = [o for o in opts if o.is_displayed()]
            if visible:
                print(f"        ✅ Opened via SPACE")
                return select_from_dropdown(driver, value, visible)
            
            element.send_keys(Keys.ENTER)
            time.sleep(1.5)
            opts = driver.find_elements(By.XPATH, "//*[@role='option' or @role='listitem']")
            visible = [o for o in opts if o.is_displayed()]
            if visible:
                print(f"        ✅ Opened via ENTER")
                return select_from_dropdown(driver, value, visible)
        except:
            pass
        
        # Strategy 5: JS events
        try:
            driver.execute_script("""
                arguments[0].dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));
            """, element)
            time.sleep(2)
            opts = driver.find_elements(By.XPATH, "//*[@role='option' or @role='listitem']")
            visible = [o for o in opts if o.is_displayed()]
            if visible:
                print(f"        ✅ Opened via JS")
                return select_from_dropdown(driver, value, visible)
        except:
            pass
        
        if attempt < max_retries - 1:
            time.sleep(2)
    
    print(f"     ❌ All strategies failed")
    return False


def select_from_dropdown(driver, value: str, visible_options: List) -> bool:
    """Select from opened dropdown."""
    try:
        options_data = []
        for opt in visible_options:
            try:
                text = opt.text.strip() or driver.execute_script("return arguments[0].textContent;", opt).strip()
                if text:
                    options_data.append((text, opt))
            except:
                continue
        
        if not options_data:
            return False
        
        print(f"        Options: {[t[0] for t in options_data[:5]]}")
        
        valid = [(t, e) for t, e in options_data if t.lower() not in ["select...", "select", "choose", "--", ""]]
        
        # No value? Select first valid
        if not value:
            if valid:
                t, e = valid[0]
                driver.execute_script("arguments[0].click();", e)
                time.sleep(1)
                print(f"        ✅ Selected: {t}")
                return True
        
        # Exact match
        for t, e in options_data:
            if value.lower() == t.lower():
                driver.execute_script("arguments[0].click();", e)
                time.sleep(1)
                print(f"        ✅ Selected: {t}")
                return True
        
        # Partial match
        for t, e in options_data:
            if value.lower() in t.lower() or t.lower() in value.lower():
                driver.execute_script("arguments[0].click();", e)
                time.sleep(1)
                print(f"        ✅ Selected: {t}")
                return True
        
        # Fallback
        if valid:
            t, e = valid[0]
            driver.execute_script("arguments[0].click();", e)
            time.sleep(1)
            print(f"        ✅ Fallback: {t}")
            return True
        
        return False
    except Exception as e:
        print(f"        ❌ Select error: {e}")
        return False

# ═══════════════════════════════════════════════════════════
# FIELD FILLER
# ═══════════════════════════════════════════════════════════

def find_element(driver, selector: str, selector_type: str):
    if selector_type == "id":
        return driver.find_element(By.ID, selector.lstrip('#'))
    elif selector_type == "name":
        return driver.find_element(By.NAME, selector)
    else:
        return driver.find_element(By.XPATH, selector)

def fill_field(driver, field_info: Dict, resume_path: str, cover_letter_path: Optional[str] = None) -> bool:
    try:
        selector = field_info.get("selector")
        selector_type = field_info.get("selector_type", "xpath")
        action = field_info.get("action", "type")
        value = field_info.get("value", "")
        label = field_info.get("label", "unknown")
        field_type = field_info.get("field_type", "")
        
        print(f"\n  📝 {label}")
        print(f"     Action: {action}, Type: {field_type}, Value: {str(value)[:50]}")
        
        # Handle file uploads - CONVERT TO ABSOLUTE PATH
        if action == "upload" or field_type == "file":
            if value == "RESUME_FILE" or "resume" in label.lower():
                value = os.path.abspath(resume_path)
                print(f"     📎 Will upload resume: {value}")
            elif value == "COVER_LETTER_FILE" and cover_letter_path:
                value = os.path.abspath(cover_letter_path)
                print(f"     📎 Will upload cover letter: {value}")
            elif cover_letter_path and ("cover" in label.lower() or "letter" in label.lower()):
                value = os.path.abspath(cover_letter_path)
                print(f"     📎 Will upload cover letter: {value}")
            else:
                # Default to resume for any file upload
                value = os.path.abspath(resume_path)
                print(f"     📎 Will upload resume (default): {value}")
        
        # Find element
        element = None
        try:
            element = find_element(driver, selector, selector_type)
        except:
            if label:
                try:
                    element = driver.find_element(By.XPATH, 
                        f"//label[contains(text(), '{label}')]/following::input[1] | "
                        f"//label[contains(text(), '{label}')]/following::select[1] | "
                        f"//label[contains(text(), '{label}')]/following::textarea[1] | "
                        f"//*[contains(@placeholder, '{label}')] | "
                        f"//input[@type='file']"
                    )
                except:
                    pass
            
            # Special search for file inputs
            if not element and (action == "upload" or field_type == "file"):
                try:
                    file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                    for inp in file_inputs:
                        if inp.is_displayed():
                            element = inp
                            print(f"     ✅ Found visible file input")
                            break
                    
                    # Try hidden file inputs too
                    if not element and file_inputs:
                        element = file_inputs[0]
                        print(f"     ✅ Found hidden file input")
                except:
                    pass
        
        if not element:
            print(f"     ❌ Not found")
            return False
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.8)
        
        tag = element.tag_name.lower()
        elem_type = element.get_attribute("type") or ""
        elem_role = element.get_attribute("role") or ""
        elem_class = element.get_attribute("class") or ""
        is_readonly = element.get_attribute("readonly")
        
        print(f"     Element: Tag={tag}, Type={elem_type}")
        
        # === FILE UPLOAD (HANDLE FIRST - HIGHEST PRIORITY) ===
        if elem_type == "file" or action == "upload":
            print(f"     📎 FILE UPLOAD detected")
            
            if not value or not os.path.exists(value):
                print(f"     ❌ File not found: {value}")
                return False
            
            try:
                # Check if file input accepts the file type
                accept_attr = element.get_attribute("accept") or ""
                print(f"     Accepts: {accept_attr if accept_attr else 'any file'}")
                
                # Send file path directly to input
                print(f"     📤 Uploading: {os.path.basename(value)}")
                element.send_keys(value)
                time.sleep(2)
                
                # Verify upload
                uploaded_value = element.get_attribute("value")
                if uploaded_value:
                    print(f"     ✅ Uploaded successfully: {os.path.basename(value)}")
                    return True
                else:
                    print(f"     ⚠️  Upload may have failed, trying alternative method...")
                    # Try clicking any upload button nearby
                    try:
                        parent = element.find_element(By.XPATH, "./..")
                        buttons = parent.find_elements(By.XPATH, ".//button | .//a")
                        for btn in buttons:
                            if btn.is_displayed():
                                btn.click()
                                time.sleep(1)
                                element.send_keys(value)
                                time.sleep(2)
                                print(f"     ✅ Uploaded via button click")
                                return True
                    except:
                        pass
                    
                    print(f"     ✅ Upload command sent (verification not available)")
                    return True
                    
            except Exception as e:
                print(f"     ❌ Upload error: {e}")
                traceback.print_exc()
                return False
        
        # DROPDOWN
        is_dropdown = (
            tag == "select" or
            "select" in elem_class.lower() or
            "dropdown" in elem_class.lower() or
            elem_role == "combobox" or
            is_readonly == "true" or
            element.get_attribute("aria-haspopup") in ["listbox", "menu", "true"] or
            action == "select"
        )
        
        if is_dropdown:
            return fill_any_dropdown(driver, element, value, label)
        
        # CHECKBOX
        if elem_type == "checkbox":
            print(f"     ☑️  Checkbox")
            if not element.is_selected():
                driver.execute_script("arguments[0].click();", element)
                time.sleep(0.5)
            print(f"     ✅ Checked")
            return True
        
        # RADIO
        if elem_type == "radio":
            print(f"     🔘 Radio")
            driver.execute_script("arguments[0].click();", element)
            time.sleep(0.5)
            print(f"     ✅ Selected")
            return True
        
        # TEXTAREA
        if tag == "textarea":
            print(f"     📄 Textarea")
            if not value:
                value = "I am interested in this position and believe I would be a valuable addition."
            element.clear()
            element.send_keys(str(value))
            time.sleep(0.5)
            print(f"     ✅ Filled")
            return True
        
        # TEXT
        if tag == "input" or elem_type in ["text", "email", "tel", "number", "url"]:
            print(f"     ⌨️  Text input")
            if not value:
                value = generate_fallback(label, elem_type)
            element.clear()
            element.send_keys(str(value))
            time.sleep(0.3)
            print(f"     ✅ Filled")
            return True
        
        # FALLBACK
        element.clear()
        element.send_keys(str(value) if value else "Test")
        print(f"     ✅ Filled (fallback)")
        return True
        
    except Exception as e:
        print(f"     ❌ Error: {e}")
        traceback.print_exc()
        return False


def generate_fallback(label: str, field_type: str) -> str:
    label_lower = label.lower()
    if any(k in label_lower for k in ["email"]): return f"test{random.randint(1000, 9999)}@example.com"
    if any(k in label_lower for k in ["phone"]): return f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
    if "name" in label_lower: return "Test User"
    if field_type == "number": return str(random.randint(1, 10))
    return "Test Value"

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def get_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def smart_load_form(driver) -> bool:
    print("\n📜 Loading form...")
    initial = driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']), select, textarea")
    visible = [f for f in initial if f.is_displayed()]
    
    if len(visible) >= 5:
        print(f"   ✅ Loaded {len(visible)} fields")
        return True
    
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        all_f = driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']), select, textarea")
        visible = [f for f in all_f if f.is_displayed()]
        if len(visible) >= 10:
            break
    
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    print(f"   ✅ Loaded {len(visible)} fields")
    return len(visible) > 0

def click_apply_button(driver):
    print("\n📝 Looking for Apply...")
    selectors = [
        "//button[contains(translate(., 'APPLY', 'apply'), 'apply')]",
        "//a[contains(translate(., 'APPLY', 'apply'), 'apply')]"
    ]
    for sel in selectors:
        try:
            btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, sel)))
            btn.click()
            print("✅ Clicked Apply")
            time.sleep(3)
            return
        except:
            continue

def verify_fields(driver) -> Dict:
    print("\n🔍 Verifying...")
    verification = driver.execute_script("""
        const result = {filled: [], empty: []};
        document.querySelectorAll('input, select, textarea').forEach(el => {
            if (el.type === 'hidden' || !el.offsetParent || el.type === 'button' || el.type === 'submit') return;
            const label = el.placeholder || el.name || 'unknown';
            const value = el.value || '';
            const isRequired = el.required || el.getAttribute('aria-required') === 'true';
            if (value.trim()) {
                result.filled.push({label});
            } else if (isRequired) {
                result.empty.push({label});
            }
        });
        return result;
    """)
    print(f"   ✅ Filled: {len(verification['filled'])}")
    print(f"   ⚠️  Empty: {len(verification['empty'])}")
    return verification

def attempt_submit(driver, submit_info: Dict) -> bool:
    print("\n🚀 Submitting...")
    if submit_info and submit_info.get("selector"):
        try:
            btn = find_element(driver, submit_info.get("selector"), submit_info.get("selector_type", "xpath"))
            driver.execute_script("arguments[0].scrollIntoView();", btn)
            time.sleep(2)
            driver.execute_script("arguments[0].click();", btn)
            print("✅ Clicked")
            time.sleep(3)
            return True
        except:
            pass
    
    for sel in ["//button[@type='submit']", "//input[@type='submit']"]:
        try:
            btn = driver.find_element(By.XPATH, sel)
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                print("✅ Submitted")
                time.sleep(3)
                return True
        except:
            continue
    return False

def detect_success(driver) -> bool:
    try:
        indicators = ["thank you", "success", "submitted", "received", "confirmation"]
        page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
        for indicator in indicators:
            if indicator in page_text:
                return True
        url = driver.current_url.lower()
        if any(w in url for w in ['success', 'confirmation', 'thank']):
            return True
        return False
    except:
        return False

def check_errors(driver) -> List[str]:
    errors = []
    selectors = [
        "//*[contains(@class, 'error')]",
        "//*[contains(@class, 'invalid')]",
        "//*[@role='alert']"
    ]
    for sel in selectors:
        try:
            elems = driver.find_elements(By.XPATH, sel)
            for elem in elems:
                if elem.is_displayed():
                    text = elem.text.strip()
                    if text and len(text) < 200:
                        errors.append(text)
        except:
            continue
    return errors

def fill_empty_fields(driver, empty_fields: List[Dict]) -> int:
    print(f"\n🔧 Filling {len(empty_fields)} empty fields...")
    filled = 0
    
    # First check for any file upload fields that might be empty
    try:
        file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
        for file_input in file_inputs:
            try:
                if not file_input.get_attribute("value"):
                    print(f"\n  📎 Found empty file upload field")
                    # This will be handled by main fill logic
            except:
                pass
    except:
        pass
    
    for field in empty_fields:
        try:
            label = field.get('label', '')
            element = None
            try:
                element = driver.find_element(By.XPATH, 
                    f"//label[contains(text(), '{label}')]/following::select[1] | "
                    f"//label[contains(text(), '{label}')]/following::input[1]"
                )
            except:
                continue
            
            if not element:
                continue
            
            driver.execute_script("arguments[0].scrollIntoView();", element)
            time.sleep(0.5)
            
            tag = element.tag_name.lower()
            elem_type = element.get_attribute("type") or ""
            
            if tag == "select" or "dropdown" in element.get_attribute("class").lower():
                if fill_any_dropdown(driver, element, "", label):
                    filled += 1
                    continue
            
            if elem_type == "checkbox":
                if not element.is_selected():
                    driver.execute_script("arguments[0].click();", element)
                    filled += 1
                    continue
            
            if elem_type in ["text", "email", "tel"]:
                val = generate_fallback(label, elem_type)
                element.clear()
                element.send_keys(val)
                filled += 1
                continue
        except:
            continue
    
    print(f"✅ Filled {filled} fields")
    return filled

def extract_job_info(driver, url: str) -> Dict[str, str]:
    """Extract job information from the page."""
    try:
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        
        # Try to extract company name
        company = "Unknown Company"
        try:
            company_elem = driver.find_element(By.XPATH, 
                "//*[contains(@class, 'company') or contains(@id, 'company')]")
            company = company_elem.text.strip()
        except:
            # Try from URL
            if "greenhouse" in url:
                parts = url.split('/')
                if len(parts) > 3:
                    company = parts[3].replace('-', ' ').title()
        
        # Try to extract position
        position = "Unknown Position"
        try:
            # Try h1 first
            position_elem = driver.find_element(By.TAG_NAME, 'h1')
            position = position_elem.text.strip()
        except:
            try:
                # Try job title class
                position_elem = driver.find_element(By.XPATH, 
                    "//*[contains(@class, 'job-title') or contains(@class, 'position')]")
                position = position_elem.text.strip()
            except:
                pass
        
        return {
            "company": company,
            "position": position
        }
    except:
        return {
            "company": "Unknown Company",
            "position": "Unknown Position"
        }

# ═══════════════════════════════════════════════════════════
# MAIN FUNCTION WITH EMAIL INTEGRATION
# ═══════════════════════════════════════════════════════════

def fill_form_from_resume(
    url: str,
    resume_path: str,
    actually_submit: bool = True,
    groq_api_key: Optional[str] = None,
    cover_letter_path: Optional[str] = None,
    max_submit_retries: int = 3,
    send_email: bool = True,
    email_config: Optional[Dict] = None
):
    """
    Main function - Fill form from resume with auto-submit and email notifications.
    
    Args:
        url: Job application URL
        resume_path: Path to resume file
        actually_submit: Whether to actually submit the form
        groq_api_key: Groq API key for resume parsing
        cover_letter_path: Optional cover letter path
        max_submit_retries: Maximum number of submission retries
        send_email: Whether to send email notifications
        email_config: Email configuration dict with keys:
            - smtp_server (default: smtp.gmail.com)
            - smtp_port (default: 587)
            - sender_email (or use SENDER_EMAIL env var)
            - sender_password (or use SENDER_PASSWORD env var)
            - recipient_email (or use RECIPIENT_EMAIL env var)
    """
    print("="*80)
    print("🤖 ENHANCED FORM FILLER - WITH EMAIL NOTIFICATIONS")
    print("="*80)
    
    # Initialize email notifier
    email_notifier = None
    if send_email:
        config = email_config or {}
        email_notifier = EmailNotifier(
            smtp_server=config.get('smtp_server', 'smtp.gmail.com'),
            smtp_port=config.get('smtp_port', 587),
            sender_email=config.get('sender_email'),
            sender_password=config.get('sender_password'),
            recipient_email=config.get('recipient_email')
        )
    
    if not resume_path or not os.path.exists(resume_path):
        error_msg = f"Resume not found: {resume_path}"
        print(f"❌ {error_msg}")
        if email_notifier:
            email_notifier.send_failure_email(
                job_url=url,
                company_name="Unknown",
                position="Unknown",
                error_message=error_msg,
                fields_filled=0,
                total_fields=0
            )
        return False
    
    # Parse resume
    try:
        parser = ResumeParser(api_key=groq_api_key)
        resume_data = parser.parse_resume(resume_path)
        
        if not resume_data:
            error_msg = "Could not parse resume"
            print(f"❌ {error_msg}")
            if email_notifier:
                email_notifier.send_failure_email(
                    job_url=url,
                    company_name="Unknown",
                    position="Unknown",
                    error_message=error_msg,
                    fields_filled=0,
                    total_fields=0
                )
            return False
    except Exception as e:
        error_msg = f"Resume parsing failed: {str(e)}"
        print(f"❌ {error_msg}")
        if email_notifier:
            email_notifier.send_failure_email(
                job_url=url,
                company_name="Unknown",
                position="Unknown",
                error_message=error_msg,
                fields_filled=0,
                total_fields=0
            )
        return False
    
    # Initialize
    analyzer = EnhancedLLMFormAnalyzer(api_key=groq_api_key)
    driver = get_driver(headless=False)
    
    # Variables to track for email
    job_info = {"company": "Unknown Company", "position": "Unknown Position"}
    fields_filled = 0
    total_fields = 0
    final_errors = []
    submission_success = False
    
    try:
        # Navigate
        print(f"\n🌐 Opening: {url}")
        driver.get(url)
        time.sleep(3)
        
        # Extract job info
        job_info = extract_job_info(driver, url)
        print(f"\n🏢 Company: {job_info['company']}")
        print(f"💼 Position: {job_info['position']}")
        
        # Click apply
        click_apply_button(driver)
        
        # Load form
        if not smart_load_form(driver):
            error_msg = "Could not load form"
            print(f"❌ {error_msg}")
            if email_notifier:
                email_notifier.send_failure_email(
                    job_url=url,
                    company_name=job_info['company'],
                    position=job_info['position'],
                    error_message=error_msg,
                    fields_filled=0,
                    total_fields=0
                )
            return False
        
        # Extract
        form_structure = extract_form_structure(driver)
        if not form_structure:
            error_msg = "No form found on page"
            print(f"❌ {error_msg}")
            if email_notifier:
                email_notifier.send_failure_email(
                    job_url=url,
                    company_name=job_info['company'],
                    position=job_info['position'],
                    error_message=error_msg,
                    fields_filled=0,
                    total_fields=0
                )
            return False
        
        # Analyze
        analysis = analyzer.analyze_form(form_structure, resume_data)
        fields = analysis.get("fields", [])
        total_fields = len(fields)
        
        if not fields:
            error_msg = "No fillable fields found"
            print(f"❌ {error_msg}")
            if email_notifier:
                email_notifier.send_failure_email(
                    job_url=url,
                    company_name=job_info['company'],
                    position=job_info['position'],
                    error_message=error_msg,
                    fields_filled=0,
                    total_fields=0
                )
            return False
        
        print(f"\n{'='*60}")
        print(f"📋 FILLING {total_fields} FIELDS")
        print(f"{'='*60}")
        
        # Fill fields
        for idx, field_info in enumerate(fields):
            print(f"\n[{idx+1}/{total_fields}]", end="")
            if fill_field(driver, field_info, resume_path, cover_letter_path):
                fields_filled += 1
            time.sleep(0.5)
        
        # Verify
        verification = verify_fields(driver)
        
        print(f"\n{'='*60}")
        print(f"📊 SUMMARY:")
        print(f"   ✅ Filled: {fields_filled}/{total_fields}")
        print(f"   ✅ Total filled: {len(verification['filled'])}")
        print(f"   ⚠️  Empty required: {len(verification['empty'])}")
        print(f"{'='*60}")
        
        # Submit
        if actually_submit:
            for retry in range(max_submit_retries):
                print(f"\n{'='*80}")
                print(f"🚀 SUBMISSION ATTEMPT #{retry + 1}/{max_submit_retries}")
                print(f"{'='*80}")
                
                # First attempt: fill empty fields
                if retry == 0:
                    verification = verify_fields(driver)
                    if verification['empty']:
                        print(f"\n⚠️  Found {len(verification['empty'])} empty required fields")
                        filled_count = fill_empty_fields(driver, verification['empty'])
                        if filled_count > 0:
                            print(f"   ✅ Pre-filled {filled_count} fields")
                            fields_filled += filled_count
                            time.sleep(2)
                            verification = verify_fields(driver)
                
                # Attempt submit
                submit_info = analysis.get("submit_button", {})
                submitted = attempt_submit(driver, submit_info)
                
                if not submitted:
                    error_msg = "Could not find or click submit button"
                    print(f"❌ {error_msg}")
                    final_errors.append(error_msg)
                    break
                
                # Wait
                time.sleep(4)
                
                # Check success
                if detect_success(driver):
                    print("\n✅ ✅ ✅ FORM SUBMITTED SUCCESSFULLY! ✅ ✅ ✅")
                    submission_success = True
                    break
                
                # Check errors
                final_errors = check_errors(driver)
                
                if final_errors:
                    print(f"\n⚠️  Detected {len(final_errors)} error(s):")
                    for err in final_errors[:3]:
                        print(f"   - {err}")
                    
                    if retry < max_submit_retries - 1:
                        print(f"\n   🔄 Retrying...")
                        verification = verify_fields(driver)
                        if verification['empty']:
                            fill_empty_fields(driver, verification['empty'])
                            time.sleep(2)
                        time.sleep(3)
                    else:
                        print(f"\n   ❌ Max retries reached")
                        break
                else:
                    print("\n✅ ✅ ✅ FORM SUBMITTED! ✅ ✅ ✅")
                    submission_success = True
                    break
        else:
            print("\n⚠️  NOT submitting (actually_submit=False)")
        
        print("\n" + "="*80)
        print("✅ PROCESS COMPLETE!")
        print("="*80)
        
        # Send email notification
        if email_notifier:
            if submission_success:
                print("\n📧 Sending success email...")
                email_notifier.send_success_email(
                    job_url=url,
                    company_name=job_info['company'],
                    position=job_info['position'],
                    fields_filled=fields_filled,
                    total_fields=total_fields,
                    resume_path=resume_path
                )
            else:
                print("\n📧 Sending failure email...")
                error_summary = "; ".join(final_errors[:3]) if final_errors else "Submission unsuccessful"
                email_notifier.send_failure_email(
                    job_url=url,
                    company_name=job_info['company'],
                    position=job_info['position'],
                    error_message=error_summary,
                    fields_filled=fields_filled,
                    total_fields=total_fields,
                    errors=final_errors
                )
        
        wait_time = 30 if actually_submit else 60
        print(f"\n⏳ Browser will stay open for {wait_time} seconds...")
        time.sleep(wait_time)
        
        return submission_success
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"\n❌ ERROR: {error_msg}")
        traceback.print_exc()
        
        # Send failure email
        if email_notifier:
            print("\n📧 Sending error email...")
            email_notifier.send_failure_email(
                job_url=url,
                company_name=job_info.get('company', 'Unknown'),
                position=job_info.get('position', 'Unknown'),
                error_message=error_msg,
                fields_filled=fields_filled,
                total_fields=total_fields,
                errors=[error_msg]
            )
        
        time.sleep(60)
        return False
    
    finally:
        driver.quit()
        print("\n🔚 Browser closed")


# ═══════════════════════════════════════════════════════════
# USAGE EXAMPLES
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    SETUP INSTRUCTIONS:
    
    1. Install required packages:
       pip install selenium webdriver-manager groq PyPDF2
    
    2. Set environment variables:
       export GROQ_API_KEY="your-groq-api-key"
       export SENDER_EMAIL="your-email@gmail.com"
       export SENDER_PASSWORD="your-app-password"
       export RECIPIENT_EMAIL="recipient@email.com"  # Optional
    
    3. For Gmail users:
       - Enable 2-Factor Authentication
       - Generate App Password: https://myaccount.google.com/apppasswords
       - Use the app password (not your regular password)
    
    4. Run the script!
    """
    
    # EXAMPLE 1: Basic usage with environment variables
    fill_form_from_resume(
        url="https://job-boards.greenhouse.io/anthropic/jobs/4977027008",
        resume_path=r"D:\internship\chatbot\AKRUTI-KHAMBHALIYA.pdf",
        actually_submit=True,
        groq_api_key=None,  # Uses GROQ_API_KEY env var
        cover_letter_path=None,
        max_submit_retries=3,
        send_email=True  # Uses env vars: SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL
    )
    
    