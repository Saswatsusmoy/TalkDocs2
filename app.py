import streamlit as st
import json
import os
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse
import subprocess
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Import custom modules
from web_crawler import crawl_website
from chatbot import DocumentChatbot
from portia_web_tools import WebCrawlerTool, WebExtractorTool, WebSitemapTool, BulkWebExtractorTool
from portia import Portia, PlanBuilderV2, Config, Input

# Page configuration
st.set_page_config(
    page_title="TalkDocs2 - AI Web Crawler & Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean, minimal design
st.markdown("""
<style>
    /* Main container styling */
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
    }
    
    .user-message {
        background-color: #f0f8ff;
        border-left: 4px solid #007bff;
    }
    
    .bot-message {
        background-color: #f8f9fa;
        border-left: 4px solid #28a745;
    }
    
    .input-section {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 1rem;
        border-top: 1px solid #e0e0e0;
        z-index: 1000;
    }
    
    .main-content {
        margin-bottom: 120px;
    }
    
    /* Sidebar styling */
    .sidebar-content {
        padding: 1rem;
    }
    
    .sidebar-section {
        margin-bottom: 2rem;
        padding: 1rem;
        background: #000000;
        border-radius: 8px;
        border: 1px solid #333;
    }
    
    .sidebar-title {
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #ffffff;
    }
    
    /* Ensure all text in sidebar sections is white */
    .sidebar-section * {
        color: #ffffff !important;
    }
    
    .sidebar-section label {
        color: #ffffff !important;
    }
    
    .sidebar-section .stTextInput > div > div > input {
        background: #333333 !important;
        border: 1px solid #555555 !important;
        color: #ffffff !important;
    }
    
    .sidebar-section .stTextInput > div > div > input::placeholder {
        color: #aaaaaa !important;
    }
    
    .sidebar-section .stSelectbox > div > div > div {
        background: #333333 !important;
        border: 1px solid #555555 !important;
        color: #ffffff !important;
    }
    
    .sidebar-section .stSlider > div > div > div > div {
        background: #ffffff !important;
    }
    
    .sidebar-section .stCheckbox > div > div > div {
        color: #ffffff !important;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #007bff;
        background-color: #007bff;
        color: white;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #0056b3;
        border-color: #0056b3;
    }
    
    /* Status styling */
    .status-container {
        text-align: center;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = DocumentChatbot()
if 'crawling_in_progress' not in st.session_state:
    st.session_state.crawling_in_progress = False
if 'use_portia_workflow' not in st.session_state:
    st.session_state.use_portia_workflow = False
if 'max_pages' not in st.session_state:
    st.session_state.max_pages = 10
if 'delay' not in st.session_state:
    st.session_state.delay = 1.0
if 'create_sitemap' not in st.session_state:
    st.session_state.create_sitemap = True

# Helper Functions (defined before use)
def normalize_url(url):
    """Normalize URL for comparison"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def check_existing_data(url):
    """Check if data for the given URL already exists"""
    normalized_url = normalize_url(url)
    
    for filename in os.listdir('.'):
        if filename.startswith('crawled_data_') and filename.endswith('.json'):
    try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                    if normalize_url(data.get('base_url', '')) == normalized_url:
                        return filename, data
            except:
                continue
        return None, None

def get_data_age(timestamp_str):
    """Calculate age of data"""
    try:
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        age = datetime.now() - timestamp
        
        if age.days > 0:
            return f"{age.days} days ago"
        elif age.seconds > 3600:
            hours = age.seconds // 3600
            return f"{hours} hours ago"
        elif age.seconds > 60:
            minutes = age.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    except:
        return "Unknown"

def load_existing_data(filename):
    """Load existing crawled data"""
    try:
        if st.session_state.chatbot.load_documents_from_json(filename):
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"✅ Loaded data from {filename}. You can now ask questions about the crawled content!"
            })
            st.rerun()
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"❌ Failed to load data: {str(e)}"
        })

def test_url_matching(url):
    """Test URL matching functionality"""
    filename, data = check_existing_data(url)
    if filename:
        age = get_data_age(data.get('crawl_timestamp', ''))
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"📋 Found existing data: {filename} (crawled {age})\n\nClick 'Load Data' to use this existing data."
        })
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "🔍 No existing data found for this URL. Ready to crawl!"
        })
    st.rerun()

def crawl_website_interface(url):
    """Main crawling interface"""
    st.session_state.crawling_in_progress = True
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"🚀 Starting to crawl: {url}"
    })
    
    try:
        if st.session_state.use_portia_workflow:
            crawl_website_with_portia(url)
        else:
            crawl_website_standard(url)
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Crawling failed: {str(e)}"
        })
    finally:
        st.session_state.crawling_in_progress = False

def crawl_website_standard(url):
    """Standard web crawler"""
    filename = f"crawled_data_{int(time.time())}.json"
    
    # Start crawling
    if st.session_state.create_sitemap:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Creating sitemap..."
        })
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Starting crawl..."
        })
    
    # Perform crawling
    crawl_website(
        url, 
        max_pages=st.session_state.max_pages,
        output_file=filename,
        create_sitemap=st.session_state.create_sitemap
    )
    
    # Load data into chatbot
    if st.session_state.chatbot.load_documents_from_json(filename):
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"✅ Successfully crawled {url} and loaded {len(st.session_state.chatbot.documents)} pages. You can now ask questions!"
        })
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "❌ Failed to load crawled data into chatbot"
        })

def capture_terminal_output_and_save(func, *args, **kwargs):
    """Capture terminal output and save to file"""
    output_filename = f"portia_output_{int(time.time())}.txt"
    
    # Capture stdout and stderr
    stdout_capture = StringIO()
    stderr_capture = StringIO()
    
    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            result = None
            stderr_capture.write(f"Error: {str(e)}\n")
    
    # Get captured output
    stdout_content = stdout_capture.getvalue()
    stderr_content = stderr_capture.getvalue()
    full_output = stdout_content + stderr_content
    
    # Save to file
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(full_output)
    
    return result, output_filename, full_output

def extract_json_from_output(output_text):
    """Extract JSON data from terminal output"""
    try:
        # Look for JSON-like content in the output
        lines = output_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                return json.loads(line)
            elif line.startswith('{'):
                # Multi-line JSON
                start_idx = output_text.find('{')
                end_idx = output_text.rfind('}') + 1
                json_str = output_text[start_idx:end_idx]
                return json.loads(json_str)
    except:
        pass
    return None

def load_portia_output_to_chatbot(output_filename):
    """Load Portia AI output into chatbot"""
    try:
        with open(output_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to extract JSON from the output
        extracted_data = extract_json_from_output(content)
        if extracted_data and 'pages' in extracted_data:
            if st.session_state.chatbot.load_documents_from_data(extracted_data):
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"✅ Loaded Portia AI output from {output_filename}. You can now ask questions!"
                })
                    st.rerun()
                return
        
        # If no JSON found, save the raw output as a document
        raw_data = {
            'pages': [{
                'url': 'Portia AI Output',
                'title': f'Portia AI Output - {output_filename}',
                'content': content,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }]
        }
        
        if st.session_state.chatbot.load_documents_from_data(raw_data):
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"✅ Loaded Portia AI output from {output_filename}. You can now ask questions!"
            })
                    st.rerun()
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Failed to load Portia AI output: {str(e)}"
        })

def crawl_website_with_portia(url):
    """Crawl website using Portia AI"""
    try:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Portia AI crawling in progress..."
        })
        
        # Create custom tools
        web_crawler_tool = WebCrawlerTool()
        custom_tools = [web_crawler_tool]
        
        # Create Portia instance
        config = Config.from_default()
        portia = Portia(config=config, tools=custom_tools)
        
        # Build plan for direct tool invocation
        plan = (
            PlanBuilderV2("Crawl website and extract structured data")
            .input(name="base_url", description="The website URL to crawl")
            .invoke_tool_step(
                step_name="Crawl Website",
                tool="web_crawler_tool",
                args={
                    "base_url": Input("base_url"),
                    "max_pages": st.session_state.max_pages,
                    "delay": st.session_state.delay,
                    "create_sitemap": st.session_state.create_sitemap,
                    "output_format": "json"
                }
            )
            .build()
        )
        
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
        
        # Try to extract JSON from the captured output first
        extracted_data = extract_json_from_output(full_output)
        
        if extracted_data:
            # Successfully extracted JSON from terminal output
            filename = f"crawled_data_{int(time.time())}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)
            
            # Load into session state
            if st.session_state.chatbot.load_documents_from_data(extracted_data):
                # Also load the terminal output file into the chatbot
                load_portia_output_to_chatbot(output_filename)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"✅ Portia AI successfully crawled {url} and extracted {len(extracted_data.get('pages', []))} pages. You can now ask questions!"
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "❌ Failed to load Portia AI results into chatbot"
                })
        else:
            # Fallback to standard Portia AI result processing
            if plan_run and hasattr(plan_run, 'outputs') and plan_run.outputs:
                # Extract data from plan run outputs
                for output in plan_run.outputs:
                    if hasattr(output, 'content') and output.content:
                        try:
                            data = json.loads(output.content)
                            if 'pages' in data:
                                filename = f"crawled_data_{int(time.time())}.json"
                                with open(filename, 'w', encoding='utf-8') as f:
                                    json.dump(data, f, indent=2, ensure_ascii=False)
                                
                                if st.session_state.chatbot.load_documents_from_data(data):
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": f"✅ Portia AI successfully crawled {url} and extracted {len(data.get('pages', []))} pages. You can now ask questions!"
                                    })
                                    return
                        except:
                            continue
            
            # If we get here, no valid data was extracted
            st.session_state.messages.append({
                "role": "assistant",
                "content": "❌ No crawling results returned from Portia AI plan"
            })
            
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Portia AI crawling failed: {str(e)}"
        })

def test_portia_tools():
    """Test Portia AI tools functionality"""
    try:
        # Test the web crawler tool directly
        tool = WebCrawlerTool()
        result = tool.run(
            ctx=None,
            base_url="https://example.com",
            max_pages=1,
            delay=0.5,
            create_sitemap=False
        )
        
        # Parse the result
        data = json.loads(result)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"✅ Portia AI tools test successful! Extracted {data.get('total_pages', 0)} pages from example.com"
        })
        
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Portia AI tools test failed: {str(e)}"
        })
    
                    st.rerun()
            
# Sidebar Configuration
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
    # Main Configuration Section
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Configuration</div>', unsafe_allow_html=True)
    
    # Workflow Selection
    workflow = st.radio(
        "Select Workflow:",
        ["Standard Crawler", "Portia AI"],
        index=1 if st.session_state.use_portia_workflow else 0
    )
    st.session_state.use_portia_workflow = (workflow == "Portia AI")
    
    # Crawling Parameters
    st.session_state.max_pages = st.slider("Max Pages", 1, 50, st.session_state.max_pages)
    st.session_state.delay = st.slider("Delay (seconds)", 0.1, 3.0, st.session_state.delay, 0.1)
    st.session_state.create_sitemap = st.checkbox("Create Sitemap", st.session_state.create_sitemap)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # URL Input Section
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Crawl Website</div>', unsafe_allow_html=True)
    
    url = st.text_input("Enter Website URL:", placeholder="https://example.com")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Crawl", key="crawl_btn"):
            if url:
                crawl_website_interface(url)
            else:
                st.error("Please enter a URL")
    
    with col2:
        if st.button("Test URL Match", key="test_btn"):
            if url:
                test_url_matching(url)
        else:
                st.error("Please enter a URL")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Data Management Section
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-title">Data Management</div>', unsafe_allow_html=True)
    
    # Load existing data
    crawled_files = [f for f in os.listdir('.') if f.startswith('crawled_data_') and f.endswith('.json')]
    if crawled_files:
        selected_file = st.selectbox("Load Existing Data:", crawled_files)
        if st.button("Load Data"):
            load_existing_data(selected_file)
    else:
        st.info("No crawled data found")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main Chat Interface
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Header with sidebar toggle
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("☰", help="Toggle Sidebar"):
        st.sidebar.toggle()
with col2:
    st.markdown("""
    <div class="main-header">
        <h1>🤖 TalkDocs2</h1>
        <p>AI-Powered Web Crawler & Document Chat</p>
    </div>
    """, unsafe_allow_html=True)

# Chat Container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about the crawled documents..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Check if chatbot has documents loaded
    if not st.session_state.chatbot.documents:
        response = "Please crawl a website first or load existing data to start chatting!"
    else:
        # Generate response
        with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
                response = st.session_state.chatbot.chat(prompt)
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Status display
if st.session_state.crawling_in_progress:
    with st.spinner("🔄 Crawling in progress..."):
        st.info("Please wait while we crawl the website")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
