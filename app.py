import streamlit as st
import json
import os
import time
import subprocess
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from web_crawler import WebCrawler
from chatbot import DocumentChatbot
import validators
from portia_web_tools import WebCrawlerTool, WebExtractorTool, WebSitemapTool, BulkWebExtractorTool

# Portia AI imports for proper integration
try:
    from portia import Portia, PlanBuilderV2, Config, Input, StepOutput
    PORTIA_AVAILABLE = True
except ImportError:
    PORTIA_AVAILABLE = False
    st.warning("⚠️ Portia AI SDK not available. Install with: pip install portia-sdk-python")

def capture_terminal_output_and_save(func, *args, **kwargs):
    """
    Capture terminal output from a function and save it to a file.
    Returns the captured output and the filename where it was saved.
    """
    # Capture stdout and stderr
    stdout_capture = StringIO()
    stderr_capture = StringIO()
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            result = func(*args, **kwargs)
    except Exception as e:
        # Capture the exception output as well
        stderr_capture.write(f"Exception: {str(e)}\n")
        result = None
    
    # Get captured output
    stdout_content = stdout_capture.getvalue()
    stderr_content = stderr_capture.getvalue()
    
    # Combine all output
    full_output = f"=== STDOUT ===\n{stdout_content}\n=== STDERR ===\n{stderr_content}"
    
    # Save to file with timestamp
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f"portia_output_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(full_output)
    
    return result, filename, full_output

def extract_json_from_output(output_text):
    """
    Try to extract JSON data from the captured output.
    Looks for JSON-like content in the output.
    """
    try:
        # Look for JSON content in the output
        lines = output_text.split('\n')
        json_start = None
        json_end = None
        
        for i, line in enumerate(lines):
            if line.strip().startswith('{') and json_start is None:
                json_start = i
            elif line.strip().endswith('}') and json_start is not None:
                json_end = i + 1
                break
        
        if json_start is not None and json_end is not None:
            json_content = '\n'.join(lines[json_start:json_end])
            return json.loads(json_content)
        
        # If no JSON found, try to parse the entire output as JSON
        return json.loads(output_text.strip())
        
    except json.JSONDecodeError:
        # If JSON parsing fails, return None
        return None

def load_portia_output_to_chatbot(output_filename):
    """
    Load the captured Portia AI output file into the chatbot as a document.
    """
    try:
        if st.session_state.chatbot:
            # Read the output file
            with open(output_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create a document structure that the chatbot can understand
            document_data = {
                'url': f'portia_output_{output_filename}',
                'title': f'Portia AI Crawling Output - {output_filename}',
                'content': content,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Load into chatbot
            success = st.session_state.chatbot.load_documents_from_data({'pages': [document_data]})
            return success
        else:
            return False
    except Exception as e:
        return False

# Page configuration
st.set_page_config(
    page_title="TalkDocs - AI Code Documentation Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ChatGPT-style Design
st.markdown("""
<style>
    /* ChatGPT-style Dark Mode Design */
    .stApp {
        background: #343541 !important;
        color: #ececf1 !important;
    }
    
    .main {
        background: #343541 !important;
        color: #ececf1 !important;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #ececf1 !important;
        font-weight: 600 !important;
        letter-spacing: -0.025em;
    }
    
    h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    h2 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.8rem;
    }
    
    h3 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.6rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: #10a37f !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
        font-size: 0.875rem !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
    }
    
    .stButton > button:hover {
        background: #0d8a6f !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(16, 163, 127, 0.3) !important;
    }
    
    /* Text Inputs */
    .stTextInput > div > div > input {
        background: #40414f !important;
        border: 1px solid #565869 !important;
        border-radius: 12px !important;
        color: #ececf1 !important;
        padding: 1rem 1.5rem !important;
        font-size: 0.875rem !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border: 1px solid #10a37f !important;
        box-shadow: 0 2px 12px rgba(16, 163, 127, 0.2) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #8e8ea0 !important;
    }
    
    /* ChatGPT-style Chat Messages */
    .chat-container {
        background: linear-gradient(135deg, #343541 0%, #40414f 100%) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        min-height: 500px !important;
        max-height: 70vh !important;
        overflow-y: auto !important;
        border: 1px solid #565869 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    
    .message {
        display: flex !important;
        margin-bottom: 1.5rem !important;
        animation: fadeIn 0.3s ease-in !important;
    }
    
    .message.user {
        justify-content: flex-end !important;
    }
    
    .message.assistant {
        justify-content: flex-start !important;
    }
    
    .message-avatar {
        width: 32px !important;
        height: 32px !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        margin: 0 0.75rem !important;
        flex-shrink: 0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    .message-avatar.user {
        background: #10a37f !important;
        color: #ffffff !important;
    }
    
    .message-avatar.assistant {
        background: #8e8ea0 !important;
        color: #ffffff !important;
    }
    
    .message-content {
        max-width: 80% !important;
        padding: 0.75rem 1rem !important;
        border-radius: 12px !important;
        font-size: 0.875rem !important;
        line-height: 1.5 !important;
        word-wrap: break-word !important;
        position: relative !important;
    }
    
    .message-content.user {
        background: #10a37f !important;
        color: #ffffff !important;
        border-bottom-right-radius: 4px !important;
    }
    
    .message-content.assistant {
        background: #40414f !important;
        color: #ececf1 !important;
        border-bottom-left-radius: 4px !important;
    }
    
    /* Markdown styling within chat messages */
    .message-content.assistant .stMarkdown {
        background: transparent !important;
        color: #ececf1 !important;
    }
    
    .message-content.assistant .stMarkdown p {
        color: #ececf1 !important;
        margin: 0.5rem 0 !important;
        line-height: 1.6 !important;
    }
    
    .message-content.assistant .stMarkdown h1,
    .message-content.assistant .stMarkdown h2,
    .message-content.assistant .stMarkdown h3,
    .message-content.assistant .stMarkdown h4,
    .message-content.assistant .stMarkdown h5,
    .message-content.assistant .stMarkdown h6 {
        color: #ececf1 !important;
        margin: 1rem 0 0.5rem 0 !important;
    }
    
    .message-content.assistant .stMarkdown code {
        background: #2d2d2d !important;
        color: #f8f8f2 !important;
        padding: 0.2rem 0.4rem !important;
        border-radius: 4px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 0.85em !important;
    }
    
    .message-content.assistant .stMarkdown pre {
        background: #2d2d2d !important;
        color: #f8f8f2 !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        overflow-x: auto !important;
        margin: 0.5rem 0 !important;
        border: 1px solid #565869 !important;
    }
    
    .message-content.assistant .stMarkdown pre code {
        background: transparent !important;
        padding: 0 !important;
        color: #f8f8f2 !important;
    }
    
    .message-content.assistant .stMarkdown ul,
    .message-content.assistant .stMarkdown ol {
        margin: 0.5rem 0 !important;
        padding-left: 1.5rem !important;
    }
    
    .message-content.assistant .stMarkdown li {
        margin: 0.25rem 0 !important;
        color: #ececf1 !important;
    }
    
    .message-content.assistant .stMarkdown blockquote {
        border-left: 4px solid #10a37f !important;
        margin: 0.5rem 0 !important;
        padding-left: 1rem !important;
        color: #b0b0b0 !important;
        font-style: italic !important;
    }
    
    .message-content.assistant .stMarkdown strong {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    .message-content.assistant .stMarkdown em {
        color: #d0d0d0 !important;
        font-style: italic !important;
    }
    
    .message-content.assistant .stMarkdown a {
        color: #10a37f !important;
        text-decoration: none !important;
    }
    
    .message-content.assistant .stMarkdown a:hover {
        text-decoration: underline !important;
    }
    
    .message-content.assistant .stMarkdown table {
        border-collapse: collapse !important;
        width: 100% !important;
        margin: 0.5rem 0 !important;
    }
    
    .message-content.assistant .stMarkdown th,
    .message-content.assistant .stMarkdown td {
        border: 1px solid #565869 !important;
        padding: 0.5rem !important;
        text-align: left !important;
    }
    
    .message-content.assistant .stMarkdown th {
        background: #2d2d2d !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Chat Input Area */
    .chat-input-container {
        background: #40414f !important;
        border: 1px solid #565869 !important;
        border-radius: 12px !important;
        padding: 0.75rem !important;
        margin-top: 1rem !important;
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    
    .chat-input-container:focus-within {
        border-color: #10a37f !important;
        box-shadow: 0 2px 12px rgba(16, 163, 127, 0.2) !important;
    }
    
    .chat-input {
        flex: 1 !important;
        background: transparent !important;
        border: none !important;
        color: #ececf1 !important;
        font-size: 0.875rem !important;
        outline: none !important;
        resize: none !important;
        min-height: 20px !important;
        max-height: 120px !important;
    }
    
    .chat-input::placeholder {
        color: #8e8ea0 !important;
    }
    
    .send-button {
        background: #10a37f !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: background 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        gap: 0.25rem !important;
    }
    
    .send-button:hover {
        background: #0d8a6f !important;
    }
    
    .send-button:disabled {
        background: #565869 !important;
        cursor: not-allowed !important;
    }
    
    /* Status Messages */
    .stSuccess {
        background: #1a2e1a !important;
        border: 1px solid #10a37f !important;
        border-radius: 8px !important;
        color: #10a37f !important;
        padding: 0.75rem !important;
    }
    
    .stError {
        background: #2e1a1a !important;
        border: 1px solid #f44336 !important;
        border-radius: 8px !important;
        color: #f44336 !important;
        padding: 0.75rem !important;
    }
    
    .stInfo {
        background: #1a1a2e !important;
        border: 1px solid #2196f3 !important;
        border-radius: 8px !important;
        color: #2196f3 !important;
        padding: 0.75rem !important;
    }
    
    .stWarning {
        background: #2e2a1a !important;
        border: 1px solid #ff9800 !important;
        border-radius: 8px !important;
        color: #ff9800 !important;
        padding: 0.75rem !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: #202123 !important;
        border-right: 1px solid #565869 !important;
    }
    
    /* Sliders */
    .stSlider > div > div > div > div {
        background: #10a37f !important;
    }
    
    .stSlider > div > div > div > div > div {
        background: #10a37f !important;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: #10a37f !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #40414f !important;
        border: 1px solid #565869 !important;
        border-radius: 8px !important;
        color: #ececf1 !important;
        font-weight: 500 !important;
    }
    
    /* JSON Display */
    .stJson {
        background: #40414f !important;
        border: 1px solid #565869 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        color: #ececf1 !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border: 2px solid #565869 !important;
        border-top: 2px solid #10a37f !important;
    }
    
    /* Status */
    .stStatus {
        background: #40414f !important;
        border: 1px solid #565869 !important;
        border-radius: 8px !important;
        color: #ececf1 !important;
    }
    
    /* General Text */
    .stMarkdown {
        color: #ececf1 !important;
    }
    
    p {
        color: #ececf1 !important;
        line-height: 1.6 !important;
    }
    
    /* Remove default Streamlit styling */
    .stMarkdown > div > div {
        background: transparent !important;
    }
    
    /* Custom container styling */
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    /* Label text */
    .stTextInput > label {
        color: #ececf1 !important;
        font-weight: 500 !important;
    }
    
    .stSlider > label {
        color: #ececf1 !important;
        font-weight: 500 !important;
    }
    
    .stButton > label {
        color: #ececf1 !important;
        font-weight: 500 !important;
    }
    
    /* Sidebar text */
    .css-1d391kg p, .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        color: #ececf1 !important;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div > div > div {
        background: #40414f !important;
        border: 1px solid #565869 !important;
        color: #ececf1 !important;
    }
    
    .stSelectbox > div > div > div > div:hover {
        border: 1px solid #10a37f !important;
    }
    
    /* Checkbox styling */
    .stCheckbox > div > div > div {
        background: #40414f !important;
        border: 1px solid #565869 !important;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes typing {
        0%, 20% { opacity: 0.3; }
        50% { opacity: 1; }
        100% { opacity: 0.3; }
    }
    
    .typing-indicator {
        display: flex !important;
        gap: 4px !important;
        padding: 0.5rem !important;
    }
    
    .typing-dot {
        width: 8px !important;
        height: 8px !important;
        border-radius: 50% !important;
        background: #8e8ea0 !important;
        animation: typing 1.4s infinite ease-in-out !important;
    }
    
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    .typing-dot:nth-child(3) { animation-delay: 0s; }
    
    /* Responsive design */
    @media (max-width: 768px) {
        h1 {
            font-size: 1.75rem !important;
        }
        
        h2 {
            font-size: 1.25rem !important;
        }
        
        .main-container {
            padding: 1rem;
        }
        
        .message-content {
            max-width: 90% !important;
        }
    }
    
    /* Scrollbar styling */
    .chat-container::-webkit-scrollbar {
        width: 6px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: #40414f;
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: #565869;
        border-radius: 3px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #8e8ea0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'crawled_data' not in st.session_state:
    st.session_state.crawled_data = None
if 'crawling_in_progress' not in st.session_state:
    st.session_state.crawling_in_progress = False
if 'current_url' not in st.session_state:
    st.session_state.current_url = None
if 'use_portia_workflow' not in st.session_state:
    st.session_state.use_portia_workflow = False

def check_existing_data(url):
    """Check if data for the given URL already exists"""
    try:
        # Normalize URL for comparison (remove trailing slash, etc.)
        normalized_url = url.rstrip('/')
        
        # Check all existing crawled data files
        for filename in os.listdir('.'):
            if filename.startswith('crawled_data_') and filename.endswith('.json'):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        stored_url = data.get('base_url', '').rstrip('/')
                        
                        # Check if the base_url matches (normalized)
                        if stored_url == normalized_url:
                            return data, filename
                except Exception as e:
                    # Skip corrupted files
                    continue
        
        return None, None
    except Exception as e:
        st.error(f"Error checking existing data: {str(e)}")
        return None, None

def load_existing_data(filename):
    """Load existing crawled data"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        st.session_state.crawled_data = data
        st.session_state.current_url = data.get('base_url')
        st.success("Loaded existing crawled data!")
        return True
    except Exception as e:
        st.error(f"Error loading existing data: {str(e)}")
        return False

def get_all_crawled_data():
    """Get list of all existing crawled data files"""
    crawled_files = []
    try:
        for filename in os.listdir('.'):
            if filename.startswith('crawled_data_') and filename.endswith('.json'):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        crawled_files.append({
                            'filename': filename,
                            'base_url': data.get('base_url', 'Unknown URL'),
                            'crawl_timestamp': data.get('crawl_timestamp', 'Unknown time'),
                            'page_count': len(data.get('pages', [])),
                            'data': data
                        })
                except Exception as e:
                    # Skip corrupted files
                    continue
        return crawled_files
    except Exception as e:
        st.error(f"Error reading crawled data files: {str(e)}")
        return []

def main():
    # Header with minimal design
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
    
    st.title("🤖 TalkDocs")
    st.markdown("**AI-powered code documentation assistant** - Crawl documentation websites and get instant help with APIs, frameworks, and technical content")
    
    # Sidebar for configuration and web crawler
    with st.sidebar:
        st.header("🔧 Configuration & Tools")
        
        # API Key input
        api_key = st.text_input(
            "Google AI API Key",
            type="password",
            help="Enter your Google AI API key for the chatbot"
        )
        
        if api_key:
            st.session_state.api_key = api_key
        
        # Web Crawler Section
        st.markdown("---")
        st.header("🕷️ Web Crawler")
        
        # URL input
        url = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            help="Enter the URL of the website you want to crawl"
        )
        
        # Crawler settings
        st.subheader("⚙️ Crawler Settings")
        
        # Document size options
        document_size = st.selectbox(
            "Document Size",
            ["Small (20 pages)", "Medium (50 pages)", "Large (100 pages)", "Max (1000 pages)"],
            help="Choose the maximum number of documents to retrieve"
        )
        
        # Map selection to actual page count
        size_mapping = {
            "Small (20 pages)": 20,
            "Medium (50 pages)": 50,
            "Large (100 pages)": 100,
            "Max (1000 pages)": 1000
        }
        
        max_pages = size_mapping[document_size]
        delay = st.slider("Delay (seconds)", 0.5, 5.0, 1.0, 0.1)
        
        # Sitemap option
        create_sitemap = st.checkbox(
            "Create Sitemap First",
            value=True,
            help="Create a detailed sitemap before crawling for better coverage"
        )
        
        st.session_state.max_pages = max_pages
        st.session_state.delay = delay
        st.session_state.create_sitemap = create_sitemap
        
        # Workflow Selection
        st.markdown("---")
        st.subheader("🔄 Workflow Selection")
        
        workflow_options = {
            "Standard Web Crawler": False,
            "Portia AI Tools": True
        }
        
        selected_workflow = st.selectbox(
            "Choose Crawling Workflow:",
            list(workflow_options.keys()),
            index=1 if st.session_state.use_portia_workflow else 0,
            help="Standard: Direct web crawler. Portia AI: Uses Portia AI tools for enhanced crawling."
        )
        
        st.session_state.use_portia_workflow = workflow_options[selected_workflow]
        
        if st.session_state.use_portia_workflow:
            if PORTIA_AVAILABLE:
                st.success("🚀 **Portia AI Tools** selected - Enhanced crawling with AI-powered tools")
                
                # Show available Portia tools
                with st.expander("🔧 Available Portia AI Tools", expanded=False):
                    st.markdown("""
                    **Available Tools:**
                    - **Web Crawler Tool**: Comprehensive website crawling with AI enhancement
                    - **Web Extractor Tool**: Single page content extraction
                    - **Web Sitemap Tool**: Generate detailed sitemaps
                    - **Bulk Web Extractor Tool**: Extract content from multiple URLs
                    
                    **Integration Method:**
                    - Uses `PlanBuilderV2` for direct tool invocation
                    - Proper Portia AI framework integration
                    - Automatic fallback to standard crawler if needed
                    """)
            else:
                st.error("❌ **Portia AI Tools** selected but SDK not available")
                st.info("📦 Install with: `pip install portia-sdk-python`")
                st.warning("🔄 Will automatically fallback to standard web crawler")
        else:
            st.info("⚡ **Standard Web Crawler** selected - Direct crawling approach")
        
        # Test buttons
        col1, col2 = st.columns(2)
        
        with col1:
            # Test URL matching button
            if st.button("🧪 Test URL", key="test_btn", help="Test if the entered URL matches existing data"):
                if url:
                    st.info(f"Testing URL matching for: {url}")
                    existing_data, filename = check_existing_data(url)
                    if existing_data:
                        st.info(f"Found existing data: {len(existing_data.get('pages', []))} pages")
                        
                        # Add a button to load this data
                        if st.button("📥 Load This Data", key="load_test_data_btn", help="Load the found existing data"):
                            st.session_state.crawled_data = existing_data
                            st.session_state.current_url = existing_data.get('base_url')
                            st.session_state.current_filename = filename  # Store the specific filename
                            
                            # Also load documents into chatbot if available
                            if st.session_state.chatbot:
                                st.session_state.chatbot.load_documents_from_data(existing_data)
                            st.rerun()
                    else:
                        st.warning("❌ No existing data found for this URL")
                else:
                    st.error("Please enter a URL first")
        
        with col2:
            # Test Portia tools button (only show when Portia workflow is selected and SDK is available)
            if st.session_state.use_portia_workflow and PORTIA_AVAILABLE:
                if st.button("🚀 Test Portia", key="test_portia_btn", help="Test individual Portia AI tools"):
                    if url:
                        st.info(f"Testing Portia AI tools for: {url}")
                        with st.spinner("Testing Portia AI tools..."):
                            test_results = test_portia_tools(url)
                        
                        if test_results:
                            # Show results in expandable sections
                            if 'extractor_result' in test_results:
                                with st.expander("📄 Web Extractor Results", expanded=False):
                                    st.json(test_results['extractor_result'])
                            
                            if 'sitemap_result' in test_results:
                                with st.expander("🗺️ Sitemap Results", expanded=False):
                                    st.json(test_results['sitemap_result'])
                    else:
                        st.error("Please enter a URL first")
            elif st.session_state.use_portia_workflow and not PORTIA_AVAILABLE:
                if st.button("⚠️ Portia SDK Missing", key="portia_missing_btn", disabled=True, help="Portia AI SDK not installed"):
                    pass  # Button is disabled
        
        # Crawl button
        if st.button("🚀 Start Crawling", key="crawl_btn"):
            if not url:
                st.error("Please enter a valid URL")
            elif not validators.url(url):
                st.error("Please enter a valid URL format")
            else:
                # Show warning for Max option
                if st.session_state.max_pages == 1000:
                    st.warning("⚠️ Max option selected (1000 pages). This will take significantly longer to complete.")
                
                # Check if data already exists for this URL
                with st.spinner("Checking for existing data..."):
                    existing_data, filename = check_existing_data(url)
                
                if existing_data:
                    st.session_state.current_url = url
                    st.session_state.existing_data = existing_data
                    st.session_state.existing_filename = filename
                    st.rerun()
                else:
                    if st.session_state.use_portia_workflow:
                        crawl_website_with_portia(url)
                    else:
                        crawl_website(url)
        
        # Show crawling status
        if st.session_state.crawling_in_progress:
            status_text = "Creating sitemap and crawling..." if st.session_state.create_sitemap else "Crawling in progress..."
            with st.status(status_text, expanded=True) as status:
                if st.session_state.create_sitemap:
                    st.write("Step 1: Creating detailed sitemap...")
                    st.write("Step 2: Crawling pages based on sitemap...")
                else:
                    st.write("Please wait while we crawl the website...")
                time.sleep(0.1)  # Small delay for UI update
        
        # Show crawled data info
        if st.session_state.crawled_data:
            st.success("✅ Crawling completed!")
            st.info(f"📄 {len(st.session_state.crawled_data['pages'])} pages crawled")
            if st.session_state.current_url:
                st.info(f"🌐 URL: {st.session_state.current_url}")
            
            # Show sitemap info if available
            if st.session_state.crawled_data.get('sitemap'):
                sitemap_count = len(st.session_state.crawled_data['sitemap'])
                st.info(f"🗺️ Sitemap created with {sitemap_count} discovered URLs")
            
            # Show sample of crawled data
            with st.expander("📄 View Crawled Data Sample"):
                if st.session_state.crawled_data['pages']:
                    sample_page = st.session_state.crawled_data['pages'][0]
                    st.json({
                        'url': sample_page['url'],
                        'title': sample_page['title'],
                        'content_preview': sample_page['content'][:200] + "..." if len(sample_page['content']) > 200 else sample_page['content']
                    })
            
            # Show sitemap data if available
            if st.session_state.crawled_data.get('sitemap'):
                with st.expander("🗺️ View Sitemap"):
                    sitemap_data = st.session_state.crawled_data['sitemap']
                    # Show first 10 URLs from sitemap
                    sample_sitemap = dict(list(sitemap_data.items())[:10])
                    st.json(sample_sitemap)
                    if len(sitemap_data) > 10:
                        st.info(f"... and {len(sitemap_data) - 10} more URLs")
        
        # Show prompt for existing data
        if hasattr(st.session_state, 'existing_data') and st.session_state.existing_data:
            st.markdown("---")
            st.markdown("### 🎯 Existing Data Found!")
            st.markdown("*We found previously crawled data for this URL. Choose what you'd like to do:*")
            
            # Display existing data info in a nice format
            existing_data = st.session_state.existing_data
            crawl_time = existing_data.get('crawl_timestamp', 'Unknown time')
            page_count = len(existing_data.get('pages', []))
            base_url = existing_data.get('base_url', 'Unknown URL')
            
            # Calculate data age
            try:
                from datetime import datetime
                if crawl_time != 'Unknown time':
                    crawl_datetime = datetime.strptime(crawl_time, '%Y-%m-%d %H:%M:%S')
                    current_time = datetime.now()
                    age_delta = current_time - crawl_datetime
                    if age_delta.days > 0:
                        age_text = f"{age_delta.days} days ago"
                    elif age_delta.seconds > 3600:
                        age_text = f"{age_delta.seconds // 3600} hours ago"
                    else:
                        age_text = f"{age_delta.seconds // 60} minutes ago"
                else:
                    age_text = "Unknown"
            except:
                age_text = "Unknown"
            
            # Create info boxes with better styling
            st.markdown("**📊 Data Summary:**")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**📅 Crawled:** {crawl_time}")
            with col2:
                st.info(f"**⏰ Age:** {age_text}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**📄 Pages:** {page_count}")
            with col2:
                st.info(f"**🌐 URL:** {base_url}")
            
            # Show sample of existing data
            with st.expander("📄 View Existing Data Sample", expanded=False):
                if existing_data.get('pages'):
                    sample_page = existing_data['pages'][0]
                    st.json({
                        'url': sample_page['url'],
                        'title': sample_page['title'],
                        'content_preview': sample_page['content'][:200] + "..." if len(sample_page['content']) > 200 else sample_page['content']
                    })
            
            st.markdown("**🤔 What would you like to do?**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Use Existing", key="use_existing_btn", type="primary", help="Load the existing data and skip crawling"):
                    load_existing_data(st.session_state.existing_filename)
                    # Clear the existing data state
                    if hasattr(st.session_state, 'existing_data'):
                        del st.session_state.existing_data
                    if hasattr(st.session_state, 'existing_filename'):
                        del st.session_state.existing_filename
                    if hasattr(st.session_state, 'current_url'):
                        del st.session_state.current_url
                    st.rerun()
            
            with col2:
                if st.button("🔄 Crawl Again", key="crawl_again_btn", help="Ignore existing data and crawl the website again"):
                    # Clear the existing data state
                    if hasattr(st.session_state, 'existing_data'):
                        del st.session_state.existing_data
                    if hasattr(st.session_state, 'existing_filename'):
                        del st.session_state.existing_filename
                    if hasattr(st.session_state, 'current_url'):
                        del st.session_state.current_url
                    # Start crawling
                    if st.session_state.use_portia_workflow:
                        crawl_website_with_portia(url)
                    else:
                        crawl_website(url)
            
            st.markdown("---")
        
        # Data Management Section
        st.markdown("---")
        st.header("📁 Data Management")
        
        # Show existing crawled data
        st.subheader("📁 Existing Data")
        
        crawled_files = get_all_crawled_data()
        if crawled_files:
            # Create a selectbox for existing data
            if crawled_files:
                file_options = [f"{file['base_url']} ({file['page_count']} pages, {file['crawl_timestamp']})" 
                              for file in crawled_files]
                selected_file = st.selectbox(
                    "Load existing data:",
                    ["Select a file..."] + file_options,
                    help="Choose existing crawled data to load"
                )
                
                if selected_file and selected_file != "Select a file...":
                    # Find the selected file
                    selected_index = file_options.index(selected_file)
                    selected_data = crawled_files[selected_index]
                    
                    if st.button("Load Selected Data", key="load_selected_btn"):
                        st.session_state.crawled_data = selected_data['data']
                        st.session_state.current_url = selected_data['base_url']
                        st.rerun()
        
        # Add option to clear all data
        if crawled_files:
            if st.button("🗑️ Clear All Data", key="clear_all_btn", help="Delete all existing crawled data files"):
                try:
                    deleted_count = 0
                    for file in crawled_files:
                        try:
                            os.remove(file['filename'])
                            deleted_count += 1
                        except Exception as e:
                            st.error(f"Failed to delete {file['filename']}: {str(e)}")
                    
                    if deleted_count > 0:
                        st.rerun()
                except Exception as e:
                    pass  # Silently ignore errors
        
        # Portia AI Output Files Section
        st.markdown("---")
        st.subheader("📄 Portia AI Output Files")
        
        # Find Portia AI output files
        portia_files = []
        try:
            for filename in os.listdir('.'):
                if filename.startswith('portia_output_') and filename.endswith('.txt'):
                    portia_files.append(filename)
        except Exception as e:
            pass  # Silently ignore errors
        
        if portia_files:
            # Create a selectbox for Portia AI output files
            selected_portia_file = st.selectbox(
                "Load Portia AI output:",
                ["Select a file..."] + portia_files,
                help="Choose a Portia AI output file to load into chatbot"
            )
            
            if selected_portia_file and selected_portia_file != "Select a file...":
                if st.button("📥 Load Portia Output", key="load_portia_btn", help="Load the selected Portia AI output file into chatbot"):
                    success = load_portia_output_to_chatbot(selected_portia_file)
                    if success:
                        st.rerun()
    
    # Main content area - Chatbot focused
    st.header("🤖 AI Document Chat")
    
    # Initialize chatbot if API key is available
    if 'api_key' in st.session_state and st.session_state.api_key:
        if st.session_state.chatbot is None:
            try:
                st.session_state.chatbot = DocumentChatbot(api_key=st.session_state.api_key)
                st.success("✅ Chatbot initialized successfully!")
            except Exception as e:
                st.error(f"Failed to initialize chatbot: {str(e)}")
                st.session_state.chatbot = None
        
        # Load documents if available
        if st.session_state.chatbot and st.session_state.crawled_data:
            if st.button("📚 Load Documents", key="load_btn"):
                with st.spinner("Loading documents..."):
                    # Try to load from session state data first
                    success = st.session_state.chatbot.load_documents_from_data(st.session_state.crawled_data)
                    
                    if not success:
                        # Use the specific filename if available, otherwise fallback
                        if hasattr(st.session_state, 'current_filename') and st.session_state.current_filename:
                            filename = st.session_state.current_filename
                            st.info(f"📁 Loading documents from: {filename}")
                        elif st.session_state.current_url:
                            normalized_url = st.session_state.current_url.rstrip('/')
                            url_hash = str(hash(normalized_url))
                            filename = f"crawled_data_{url_hash}.json"
                        else:
                            # Fallback to default filename
                            filename = 'crawled_data.json'
                        
                        success = st.session_state.chatbot.load_documents_from_json(filename)
                    
                    if success:
                        st.success("✅ Documents loaded successfully!")
                    else:
                        st.error("Failed to load documents")
        
        # ChatGPT-style Chat interface
        if st.session_state.chatbot and st.session_state.chatbot.documents:
            # Document status with better styling
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: rgba(16, 163, 127, 0.1); border: 1px solid #10a37f; border-radius: 8px; margin-bottom: 1rem;">
                    <strong>📚 {len(st.session_state.chatbot.documents)} documents loaded and ready for chat</strong>
                </div>
                """, unsafe_allow_html=True)
            
            # Chat container
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            
            # Display chat history with proper markdown formatting
            if st.session_state.chat_history and len(st.session_state.chat_history) > 0:
                for message in st.session_state.chat_history:
                    if message["role"] == "user":
                        # User message with HTML styling
                        st.markdown(f"""
                        <div class="message user">
                            <div class="message-content user">
                                {message["content"]}
                            </div>
                            <div class="message-avatar user">👤</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Assistant message with markdown rendering
                        st.markdown(f"""
                        <div class="message assistant">
                            <div class="message-avatar assistant">🤖</div>
                            <div class="message-content assistant">
                        """, unsafe_allow_html=True)
                        
                        # Render the content as markdown
                        st.markdown(message["content"])
                        
                        st.markdown("""
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                # Welcome message with markdown - only show when no chat history exists
                st.markdown(f"""
                <div class="message assistant">
                    <div class="message-avatar assistant">🤖</div>
                    <div class="message-content assistant">
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                👋 **Hello!** I'm your AI coding documentation assistant. I have access to **{len(st.session_state.chatbot.documents)} documents** from the crawled website.
                
                Ask me anything about the code documentation, APIs, frameworks, or technical content, and I'll help you understand it quickly!
                
                **I can help you with:**
                - 🔧 **Code Documentation**: Understand APIs, functions, classes, and methods
                - 💻 **Implementation**: Get code examples and usage patterns
                - ⚙️ **Configuration**: Learn about settings, parameters, and options
                - 🔗 **Integration**: Understand setup and integration instructions
                - 🐛 **Troubleshooting**: Get help with common issues and debugging
                - 📚 **Quick Reference**: Find specific information without manual searching
                
                Just ask me about any aspect of the documentation you need help with!
                """)
                
                st.markdown("""
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Single chat input with Streamlit
            user_input = st.text_input(
                "Ask a question:",
                placeholder=f"Ask me anything about your {len(st.session_state.chatbot.documents)} documents...",
                key="chat_input",
                label_visibility="collapsed"
            )
            
            # Send button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🚀 Send", key="send_btn") and user_input:
                    chat_with_bot(user_input.strip())
                    # Clear the input after sending
                    st.session_state.chat_input = ""
                    st.rerun()
            
            # Clear chat button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🗑️ Clear Chat", key="clear_chat_btn", help="Clear all chat history"):
                    st.session_state.chat_history = []
                    st.rerun()
        
        elif st.session_state.chatbot:
            st.info("📚 Please crawl a website first, then load the documents to start chatting!")
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background: rgba(16, 163, 127, 0.05); border: 1px solid #10a37f; border-radius: 12px; margin: 2rem 0;">
                <h3>🚀 Ready to get started?</h3>
                <p>Use the sidebar to crawl a website and load documents, then come back here to chat with your AI assistant!</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.warning("🔑 Please enter your Google AI API key in the sidebar to use the chatbot")
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: rgba(255, 193, 7, 0.1); border: 1px solid #ffc107; border-radius: 12px; margin: 2rem 0;">
            <h3>🔑 API Key Required</h3>
            <p>Enter your Google AI API key in the sidebar to unlock the full chatbot functionality.</p>
        </div>
        """, unsafe_allow_html=True)
        

    
    st.markdown("</div>", unsafe_allow_html=True)

def crawl_website(url):
    """Crawl the website and save data"""
    st.session_state.crawling_in_progress = True
    st.session_state.current_url = url
    
    try:
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Initialize crawler
        crawler = WebCrawler(
            base_url=url,
            max_pages=st.session_state.max_pages,
            delay=st.session_state.delay,
            create_sitemap=st.session_state.create_sitemap
        )
        
        # Start crawling
        if st.session_state.create_sitemap:
            status_text.text("Creating sitemap...")
            progress_bar.progress(10)
        else:
            status_text.text("Starting crawl...")
            progress_bar.progress(10)
        
        # Crawl the website
        pages_data = crawler.crawl()
        
        progress_bar.progress(80)
        status_text.text("Saving data...")
        
        # Create URL-specific filename using normalized URL
        normalized_url = url.rstrip('/')
        url_hash = str(hash(normalized_url))
        filename = f"crawled_data_{url_hash}.json"
        
        # Save to JSON with URL-specific filename
        saved_filename = crawler.save_to_json(filename)
        
        progress_bar.progress(100)
        status_text.text("Crawling completed!")
        
        # Load data into session state
        with open(saved_filename, 'r', encoding='utf-8') as f:
            st.session_state.crawled_data = json.load(f)
        
        time.sleep(2)  # Show completion message
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"Crawling failed: {str(e)}")
    finally:
        st.session_state.crawling_in_progress = False

def crawl_website_with_portia(url):
    """Crawl the website using Portia AI tools with proper PlanBuilderV2 integration"""
    st.session_state.crawling_in_progress = True
    st.session_state.current_url = url
    
    try:
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        if not PORTIA_AVAILABLE:
            st.error("❌ Portia AI SDK not available. Please install it first.")
            return
        
        status_text.text("Initializing Portia AI with custom web crawler tools...")
        progress_bar.progress(10)
        
        # Create our custom web tools
        web_crawler_tool = WebCrawlerTool()
        web_extractor_tool = WebExtractorTool()
        web_sitemap_tool = WebSitemapTool()
        
        # Create tools list
        custom_tools = [web_crawler_tool, web_extractor_tool, web_sitemap_tool]
        
        # Create Portia instance with custom tools
        config = Config.from_default()
        portia = Portia(config=config, tools=custom_tools)
        
        status_text.text("Building Portia AI plan for web crawling...")
        progress_bar.progress(30)
        
        # Build a plan using PlanBuilderV2 for direct tool invocation
        plan = (
            PlanBuilderV2("Crawl website and extract structured data")
            .input(name="base_url", description="The website URL to crawl", default_value=url)
            .input(name="max_pages", description="Maximum pages to crawl", default_value=st.session_state.max_pages)
            .input(name="delay", description="Delay between requests", default_value=st.session_state.delay)
            .input(name="create_sitemap", description="Whether to create sitemap", default_value=st.session_state.create_sitemap)
            .invoke_tool_step(
                step_name="Crawl Website",
                tool="web_crawler_tool",
                args={
                    "base_url": Input("base_url"),
                    "max_pages": Input("max_pages"),
                    "delay": Input("delay"),
                    "create_sitemap": Input("create_sitemap"),
                    "output_format": "json"
                }
            )
            .build()
        )
        
        status_text.text("Executing Portia AI crawling plan...")
        progress_bar.progress(50)
        
        # Execute the plan with output capture
        def run_portia_plan():
            return portia.run_plan(plan, plan_run_inputs={
                "base_url": url,
                "max_pages": st.session_state.max_pages,
                "delay": st.session_state.delay,
                "create_sitemap": st.session_state.create_sitemap
            })
        
        # Capture terminal output and save to file
        plan_run, output_filename, full_output = capture_terminal_output_and_save(run_portia_plan)
        
        progress_bar.progress(80)
        status_text.text("Processing Portia AI results...")
        
        # Try to extract JSON from the captured output first
        extracted_data = extract_json_from_output(full_output)
        
        if extracted_data:
            # Successfully extracted JSON from terminal output
            
            # Create URL-specific filename using normalized URL
            normalized_url = url.rstrip('/')
            url_hash = str(hash(normalized_url))
            filename = f"crawled_data_{url_hash}.json"
            
            # Save the result to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)
            
            # Load data into session state
            st.session_state.crawled_data = extracted_data
            
            # Also load the terminal output file into the chatbot
            load_portia_output_to_chatbot(output_filename)
            
            progress_bar.progress(100)
            status_text.text("✅ Crawling completed successfully!")
            
            time.sleep(2)  # Show completion message
            progress_bar.empty()
            status_text.empty()
        else:
            # Fallback to standard Portia AI result processing
            if plan_run and plan_run.outputs and plan_run.outputs.step_outputs:
                # Get the crawling result from the step output
                crawl_result = plan_run.outputs.step_outputs.get("Crawl Website")
                if crawl_result and crawl_result.value:
                    # Parse the JSON result if it's a string
                    if isinstance(crawl_result.value, str):
                        result_data = json.loads(crawl_result.value)
                    else:
                        result_data = crawl_result.value
                    
                    # Create URL-specific filename using normalized URL
                    normalized_url = url.rstrip('/')
                    url_hash = str(hash(normalized_url))
                    filename = f"crawled_data_{url_hash}.json"
                    
                    # Save the result to file
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(result_data, f, indent=2, ensure_ascii=False)
                    
                    # Load data into session state
                    st.session_state.crawled_data = result_data
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Crawling completed successfully!")
                    
                    time.sleep(2)  # Show completion message
                    progress_bar.empty()
                    status_text.empty()
                else:
                    raise Exception("No crawling results returned from Portia AI plan")
            else:
                raise Exception("Plan execution failed - no outputs returned")
        
    except Exception as e:
        # Fallback to standard crawler
        crawl_website(url)
    finally:
        st.session_state.crawling_in_progress = False

def test_portia_tools(url):
    """Test individual Portia AI tools using proper Portia AI integration"""
    try:
        if not PORTIA_AVAILABLE:
            st.error("❌ Portia AI SDK not available. Please install it first.")
            return None
        
        # Create our custom web tools
        web_extractor_tool = WebExtractorTool()
        web_sitemap_tool = WebSitemapTool()
        
        # Create tools list
        custom_tools = [web_extractor_tool, web_sitemap_tool]
        
        # Create Portia instance with custom tools
        config = Config.from_default()
        portia = Portia(config=config, tools=custom_tools)
        
        # Create plan for testing Web Extractor Tool
        extractor_plan = (
            PlanBuilderV2("Test Web Content Extractor")
            .input(name="target_url", description="URL to extract content from", default_value=url)
            .invoke_tool_step(
                step_name="Extract Content",
                tool="web_extractor_tool",
                args={
                    "url": Input("target_url"),
                    "extract_links": True,
                    "use_selenium": False
                }
            )
            .build()
        )
        
        # Execute extractor plan
        extractor_plan_run = portia.run_plan(extractor_plan, plan_run_inputs={"target_url": url})
        
        # Create plan for testing Web Sitemap Tool
        sitemap_plan = (
            PlanBuilderV2("Test Web Sitemap Generator")
            .input(name="base_url", description="Base URL for sitemap", default_value=url)
            .invoke_tool_step(
                step_name="Generate Sitemap", 
                tool="web_sitemap_tool",
                args={
                    "base_url": Input("base_url"),
                    "max_urls": 20,
                    "output_file": None
                }
            )
            .build()
        )
        
        # Execute sitemap plan
        sitemap_plan_run = portia.run_plan(sitemap_plan, plan_run_inputs={"base_url": url})
        
        # Extract results
        results = {}
        
        if extractor_plan_run.outputs and extractor_plan_run.outputs.step_outputs:
            extractor_result = extractor_plan_run.outputs.step_outputs.get("Extract Content")
            if extractor_result and extractor_result.value:
                if isinstance(extractor_result.value, str):
                    results['extractor_result'] = json.loads(extractor_result.value)
                else:
                    results['extractor_result'] = extractor_result.value
        
        if sitemap_plan_run.outputs and sitemap_plan_run.outputs.step_outputs:
            sitemap_result = sitemap_plan_run.outputs.step_outputs.get("Generate Sitemap")
            if sitemap_result and sitemap_result.value:
                if isinstance(sitemap_result.value, str):
                    results['sitemap_result'] = json.loads(sitemap_result.value)
                else:
                    results['sitemap_result'] = sitemap_result.value
        
        return results if results else None
        
    except Exception as e:
        st.error(f"❌ Portia AI tools test failed: {str(e)}")
        # Fallback to direct tool testing
        st.info("🔄 Falling back to direct tool testing...")
        try:
            # Direct tool execution as fallback
            from portia import ToolRunContext
            
            # Create a minimal context
            class MinimalContext:
                def __init__(self):
                    pass
            
            minimal_ctx = MinimalContext()
            
            # Test tools directly
            extractor = WebExtractorTool()
            extractor_result = extractor.run(minimal_ctx, url, True, False)
            
            sitemap_tool = WebSitemapTool()
            sitemap_result = sitemap_tool.run(minimal_ctx, url, 20, None)
            
            return {
                'extractor_result': json.loads(extractor_result),
                'sitemap_result': json.loads(sitemap_result)
            }
        except Exception as fallback_error:
            st.error(f"❌ Fallback testing also failed: {str(fallback_error)}")
            return None

def chat_with_bot(user_input):
    """Handle chat with the bot"""
    if st.session_state.chatbot and st.session_state.chatbot.documents:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Show typing indicator
        st.markdown("""
        <div class="message assistant">
            <div class="message-avatar assistant">🤖</div>
            <div class="message-content assistant">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Get bot response
        with st.spinner(""):
            response = st.session_state.chatbot.chat(user_input, use_rag=True)
        
        # Add bot response to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Rerun to update the chat display
        st.rerun()

if __name__ == "__main__":
    main()

