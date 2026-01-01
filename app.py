"""
Streamlit UI for Job Search & Resume Matching System
"""

import os
import sys
import streamlit as st


# Add src to path
sys.path.append('src')

from job_embedding_pipeline import JobEmbeddingPipeline
from resume_matching_pipeline import ResumeMatchingPipeline
from elasticsearch_manager import ElasticsearchManager

# Load environment variables


# Page config
st.set_page_config(
    page_title="Job Search & Resume Matcher",
    page_icon="🎯",
    layout="wide"
)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.es_connected = False
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    ELASTICSEARCH_URL = st.secrets["ELASTICSEARCH_URL"]
    st.session_state.resume_processed = False
    st.session_state.current_resume_id = None

# Auto-connect on startup
if not st.session_state.es_connected and st.session_state.openai_api_key and st.session_state.es_url:
    try:
        es_manager = ElasticsearchManager(st.session_state.es_url)
        if es_manager.ping():
            st.session_state.es_connected = True
    except:
        pass

# Sidebar - Configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Show connection status
    if st.session_state.es_connected:
        st.success("🟢 Connected")
        
        # Index stats
        st.divider()
        st.subheader("📊 Index Statistics")
        
        es_manager = ElasticsearchManager(st.session_state.es_url)
        
        try:
            job_stats = es_manager.get_index_stats("job_embeddings")
            st.metric("Jobs Indexed", job_stats.get('document_count', 0))
        except:
            st.metric("Jobs Indexed", "N/A")
    else:
        st.error("🔴 Not Connected")
        st.info("Please check:\n- OpenAI API key in .env\n- Elasticsearch is running\n- Configuration is correct")

# Main content
st.title("🎯 Job Search & Resume Matching System")
st.markdown("### AI-Powered Job Discovery and Resume-to-Job Matching")

if not st.session_state.es_connected:
    st.warning("⚠️ Please configure your .env file with OPENAI_API_KEY and ensure Elasticsearch is running")
    st.code("""
# .env file should contain:
OPENAI_API_KEY=your-api-key-here
ELASTICSEARCH_URL=http://localhost:9200
    """)
    st.stop()

# Tabs
tab1, tab2, tab3 = st.tabs([
    "📋 Process Jobs", 
    "🎯 Find Job Matches",
    "🔍 Search Jobs"
])

# Tab 1: Process Jobs
with tab1:
    st.header("📋 Process Job Listings")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload jobs JSON file",
            type=['json'],
            help="Upload us_jobs.json or similar file"
        )
    
    with col2:
        max_jobs = st.number_input(
            "Max jobs to process",
            min_value=1,
            max_value=1000,
            value=10,
            help="Limit number of jobs for testing"
        )
        
        recreate_index = st.checkbox(
            "Recreate index",
            value=False,
            help="Delete and recreate the index"
        )
    
    if uploaded_file:
        # Save uploaded file temporarily
        temp_file = "temp_jobs.json"
        with open(temp_file, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        if st.button("🚀 Process Jobs", type="primary"):
            with st.spinner("Processing jobs..."):
                try:
                    pipeline = JobEmbeddingPipeline(
                        st.session_state.openai_api_key,
                        st.session_state.es_url
                    )
                    
                    count = pipeline.process_and_index_jobs(
                        temp_file,
                        "job_embeddings",
                        max_jobs,
                        recreate_index
                    )
                    
                    st.success(f"✅ Successfully processed and indexed {count} jobs!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        # Clean up
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass

# Tab 2: Find Job Matches (Resume Upload)
with tab2:
    st.header("🎯 Upload Resume & Find Matching Jobs")
    
    uploaded_resume = st.file_uploader(
        "Upload resume PDF",
        type=['pdf'],
        help="Upload a resume PDF to find matching jobs",
        key="resume_uploader"
    )
    
    if uploaded_resume:
        # Save temporarily
        temp_pdf = "temp_resume.pdf"
        with open(temp_pdf, 'wb') as f:
            f.write(uploaded_resume.getvalue())
        
        if st.button("🚀 Find Matching Jobs", type="primary"):
            with st.spinner("Processing resume and finding matches..."):
                try:
                    from job_portal.resume_processor import ResumeProcessor
                    from job_portal.elasticsearch_manager import ElasticsearchManager
                    
                    # Process resume without storing
                    resume_processor = ResumeProcessor(st.session_state.openai_api_key)
                    
                    # Extract and process
                    st.info("📄 Extracting text from PDF...")
                    resume_text = resume_processor.extract_text_from_pdf(temp_pdf)
                    
                    if not resume_text:
                        st.error("❌ Failed to extract text from PDF")
                    else:
                        st.success(f"✓ Extracted {len(resume_text)} characters")
                        
                        # Extract info
                        st.info("📝 Analyzing resume...")
                        resume_filename = uploaded_resume.name
                        resume_info = resume_processor.extract_resume_info(resume_text, resume_filename)
                        
                        # Show candidate info
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Candidate", resume_info.get('candidate_name', 'N/A'))
                        with col2:
                            st.metric("Experience", resume_info.get('experience_years', 'N/A'))
                        with col3:
                            st.metric("Skills Found", len(resume_info.get('skills', [])))
                        
                        # Generate embedding
                        st.info("🧠 Creating semantic embedding...")
                        resume_embedding = resume_processor.generate_embedding(resume_info['full_text'])
                        
                        if not resume_embedding:
                            st.error("❌ Failed to create embedding")
                        else:
                            st.success(f"✓ Embedding created ({len(resume_embedding)} dimensions)")
                            
                            # Search for similar jobs
                            st.divider()
                            st.subheader("🎯 Finding Matching Jobs...")
                            
                            es_manager = ElasticsearchManager(st.session_state.es_url)
                            
                            # Search using embedding
                            matches = es_manager.semantic_search(
                                resume_embedding,
                                "job_embeddings",
                                "description_embedding",
                                10
                            )
                            
                            if matches:
                                st.success(f"Found {len(matches)} matching jobs!")
                                
                                # Display matches
                                for i, job in enumerate(matches, 1):
                                    score = job.get('_score', 0)
                                    match_pct = score * 100
                                    
                                    # Color based on match percentage
                                    if match_pct >= 85:
                                        color = "🟢"
                                        label = "Excellent Match"
                                    elif match_pct >= 75:
                                        color = "🟡"
                                        label = "Good Match"
                                    elif match_pct >= 65:
                                        color = "🟠"
                                        label = "Fair Match"
                                    else:
                                        color = "🔴"
                                        label = "Low Match"
                                    
                                    with st.expander(
                                        f"{color} {i}. {job.get('job_title', 'N/A')} at {job.get('company', 'N/A')} - {label}",
                                        expanded=(i <= 3)
                                    ):
                                        col1, col2 = st.columns([3, 1])
                                        
                                        with col1:
                                            st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                                            st.markdown(f"**Salary:** {job.get('salary_range', 'Not specified')}")
                                            st.markdown(f"**Job ID:** `{job.get('job_id', 'N/A')}`")
                                        
                                        with col2:
                                            st.metric("Match", f"{match_pct:.1f}%")
                                            st.progress(match_pct / 100)
                                        
                                        st.markdown("**Role:**")
                                        st.write(job.get('role', 'N/A'))
                                        
                                        st.markdown(f"[🔗 Apply Now]({job.get('link', '#')})")
                            else:
                                st.warning("No matches found. Please process some jobs first in the 'Process Jobs' tab.")
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Clean up
        if os.path.exists(temp_pdf):
            try:
                os.remove(temp_pdf)
            except:
                pass

# Tab 3: Search Jobs
with tab3:
    st.header("🔍 Search Jobs")
    
    search_query = st.text_input(
        "Enter search query",
        placeholder="e.g., Senior Python Developer with ML experience",
        help="Enter keywords or description of the job you're looking for"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_type = st.selectbox(
            "Search Type",
            ["Semantic (AI)", "Keyword", "Hybrid"],
            help="Semantic uses AI understanding, Keyword uses text matching"
        )
    
    with col2:
        num_results = st.slider(
            "Number of results",
            min_value=5,
            max_value=50,
            value=10
        )
    
    with col3:
        if search_type == "Hybrid":
            semantic_weight = st.slider(
                "Semantic weight",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher = more AI, Lower = more keywords"
            )
    
    if st.button("🔍 Search", type="primary") and search_query:
        with st.spinner("Searching..."):
            try:
                pipeline = JobEmbeddingPipeline(
                    st.session_state.openai_api_key,
                    st.session_state.es_url
                )
                
                if search_type == "Semantic (AI)":
                    results = pipeline.search_jobs_semantic(
                        search_query,
                        "job_embeddings",
                        num_results
                    )
                elif search_type == "Keyword":
                    results = pipeline.search_jobs_keyword(
                        search_query,
                        "job_embeddings",
                        num_results
                    )
                else:  # Hybrid
                    results = pipeline.search_jobs_hybrid(
                        search_query,
                        "job_embeddings",
                        num_results,
                        semantic_weight
                    )
                
                if results:
                    st.success(f"Found {len(results)} jobs!")
                    
                    for i, job in enumerate(results, 1):
                        with st.expander(
                            f"{i}. {job.get('job_title', 'N/A')} at {job.get('company', 'N/A')}",
                            expanded=(i <= 3)
                        ):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                                st.markdown(f"**Salary:** {job.get('salary_range', 'Not specified')}")
                                st.markdown(f"**Job ID:** `{job.get('job_id', 'N/A')}`")
                            
                            with col2:
                                if 'rrf_score' in job:
                                    st.caption(f"Semantic #{job.get('semantic_rank', 'N/A')}")
                                    st.caption(f"Keyword #{job.get('keyword_rank', 'N/A')}")
                            
                            st.markdown("**Role:**")
                            st.write(job.get('role', 'N/A'))
                            
                            st.markdown(f"[🔗 View Job]({job.get('link', '#')})")
                else:
                    st.warning("No results found")
                    
            except Exception as e:
                st.error(f"❌ Error: {e}")

# Footer
st.divider()

st.caption("🎯 Job Search & Resume Matching System | Powered by OpenAI & Elasticsearch")

