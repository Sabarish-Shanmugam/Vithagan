import streamlit as st
import yaml
import os
import sys
import logging
import time
from dotenv import load_dotenv

# --- PATH SETUP ---
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# --- ACTUAL IMPORTS ---
from src.ai_processor.yaml_generator import GeminiClient
from src.pipeline_controller import PipelineController

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# --- Configuration and Theme ---
st.set_page_config(
    page_title="Vithagan - AI-Powered Diagram Generator",
    layout="wide",
    initial_sidebar_state="expanded" if not os.environ.get("GOOGLE_API_KEY") else "collapsed"
)

# --- Constants ---
APP_TITLE = "Vithagan"
APP_DESCRIPTION = "Natural Language to Multi-Cloud Diagram Configuration"
API_KEY_PLACEHOLDER = "Enter your Gemini API Key..."

# --- Custom Streamlit Styling ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');
    
    .reportview-container .main {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
        color: #1e293b;
    }
    body {
        font-family: 'Inter', sans-serif;
    }
    /* Professional Button Styling */
    div.stButton > button {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        border-radius: 6px;
        padding: 0.5rem 1rem;
    }
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Helper Functions ---

def status_indicator(is_online, has_key):
    """Displays real-time system status."""
    if not is_online:
        st.error("🔴 Offline")
    elif not has_key:
        st.warning("🟡 Key Missing")
    else:
        st.success("🟢 System Ready")

def get_active_api_key():
    """Returns the active API key (user-provided takes priority, then backend)."""
    if st.session_state.user_provided_key:
        return st.session_state.user_provided_key
    return os.environ.get("GOOGLE_API_KEY", "")

# --- Session State Management ---
if 'yaml_config' not in st.session_state:
    st.session_state.yaml_config = ""
if 'is_yaml_generated' not in st.session_state:
    st.session_state.is_yaml_generated = False
if 'user_provided_key' not in st.session_state:
    st.session_state.user_provided_key = ""
if 'current_description' not in st.session_state:
    st.session_state.current_description = ""
if 'diagrams_rendered' not in st.session_state:
    st.session_state.diagrams_rendered = False
if 'selected_diagram_types' not in st.session_state:
    st.session_state.selected_diagram_types = ["Architecture"]

# --- Action Functions ---

def generate_yaml(description, diagram_types):
    """Real AI-Powered YAML Generation using Gemini."""
    active_key = get_active_api_key()
    if not active_key:
        st.error("Please provide a Gemini API Key.")
        st.session_state.is_yaml_generated = False
        return

    # Append diagram types to description to guide AI
    augmented_description = f"{description}\n\nRequired Diagram Types: {', '.join(diagram_types)}"

    try:
        # Temporarily set the active key for this generation
        os.environ["GOOGLE_API_KEY"] = active_key
        with st.spinner("Generating Configuration..."):
            client = GeminiClient()
            generated_yaml = client.generate_yaml(augmented_description)
            st.session_state.yaml_config = generated_yaml
            st.session_state.is_yaml_generated = True
            st.session_state.current_description = description
            st.session_state.diagrams_rendered = False
            st.toast("Configuration generated successfully!")
    except Exception as e:
        st.error(f"Error generating YAML: {e}")
        logger.error(f"YAML generation error: {e}")
        st.session_state.is_yaml_generated = False

def render_diagram():
    """Real diagram rendering using PipelineController."""
    try:
        with st.spinner("Rendering Diagrams..."):
            config_data = yaml.safe_load(st.session_state.yaml_config)
            controller = PipelineController(config_data=config_data)
            controller.run()
            st.session_state.diagrams_rendered = True
            st.toast("Diagrams rendered successfully!")
    except Exception as e:
        st.error(f"Error rendering diagram: {e}")
        logger.error(f"Rendering error: {e}")

# --- Sidebar (Configuration Only) ---
with st.sidebar:
    st.markdown("### Settings")
    
    # Status
    active_key = get_active_api_key()
    status_indicator(is_online=True, has_key=bool(active_key))
    st.markdown("---")

    # Secure API Key Handling
    backend_key_exists = bool(os.environ.get("GOOGLE_API_KEY"))
    
    if backend_key_exists and not st.session_state.user_provided_key:
        st.success("API Key configured")
        if st.checkbox("Override API Key"):
            custom_key = st.text_input("Custom Key", type="password")
            if custom_key:
                st.session_state.user_provided_key = custom_key
                st.rerun()
    else:
        with st.expander("API Key Setup", expanded=True):
            api_key_input = st.text_input(
                "Gemini API Key",
                type="password",
                value=st.session_state.user_provided_key,
                placeholder=API_KEY_PLACEHOLDER
            )
            if api_key_input != st.session_state.user_provided_key:
                st.session_state.user_provided_key = api_key_input
                st.rerun()
            
            if backend_key_exists and st.session_state.user_provided_key:
                if st.button("Reset to Backend Key"):
                    st.session_state.user_provided_key = ""
                    st.rerun()

# --- Main Area ---

# Header
logo_col, title_col = st.columns([1, 5])
with logo_col:
    logo_path = "assets/vithagan_logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=150)
    else:
        st.markdown(f"<h2>{APP_TITLE}</h2>", unsafe_allow_html=True)

with title_col:
    st.header(f"{APP_DESCRIPTION}")

st.markdown("---")

# --- STEP 1: Diagram Type Selection ---
st.subheader("Step 1: Select Diagram Types")
diagram_types = st.multiselect(
    "Choose the types of diagrams you want to generate:",
    ["Architecture", "Data Flow Diagram (DFD)", "Business Process (BPMN)"],
    default=["Architecture"],
    key="diagram_type_selector"
)

# --- STEP 2: Description ---
st.subheader("Step 2: Describe Your Infrastructure or Project")

# Quick Start (Moved to Main Area)
example_prompts = {
    "Select an example...": "",
    "AWS 3-Tier Web App": "Design a highly available AWS architecture with an Application Load Balancer, a web tier of 3 EC2 instances in an Auto Scaling Group, and a multi-AZ PostgreSQL RDS database.",
    "GCP E-Commerce (Arch + DFD)": "Design a complete GCP e-commerce system. 1. Create a GCP Architecture diagram with Global Load Balancer, GKE Autopilot, and Cloud Spanner. 2. Create a Data Flow Diagram (DFD) showing the user checkout process flow.",
    "Azure Serverless": "Create an Azure architecture with Front Door, Function Apps, and Cosmos DB.",
}

col_ex_label, col_ex_select = st.columns([1, 3])
with col_ex_label:
    st.markdown("**Quick Start:**")
with col_ex_select:
    selected_example = st.selectbox(
        "Load Example Prompt",
        options=list(example_prompts.keys()),
        label_visibility="collapsed"
    )

if selected_example and selected_example != "Select an example...":
    if st.session_state.current_description != example_prompts[selected_example]:
        st.session_state.current_description = example_prompts[selected_example]
        st.rerun()

input_description = st.text_area(
    "Project or Architecture description",
    value=st.session_state.current_description,
    height=150,
    placeholder="Describe your system requirements here..."
)

# Generate Button
col_btn, _ = st.columns([1, 4])
with col_btn:
    st.button(
        "Generate Configuration",
        type="primary",
        on_click=generate_yaml,
        args=(input_description, diagram_types),
        disabled=not bool(get_active_api_key()) or not bool(input_description.strip())
    )

st.markdown("---")

# --- Review & Render ---
if st.session_state.is_yaml_generated:
    st.subheader("Configuration Review")
    
    tab_config, tab_output = st.tabs(["Configuration", "Diagram Output"])
    
    with tab_config:
        col_edit, col_act = st.columns([3, 1])
        with col_edit:
            edited_yaml = st.text_area(
                "YAML Configuration",
                value=st.session_state.yaml_config,
                height=400
            )
            st.session_state.yaml_config = edited_yaml
        
        with col_act:
            st.info("Review the generated configuration.")
            if st.button("Render Diagrams", type="primary", use_container_width=True):
                render_diagram()

    with tab_output:
        if st.session_state.diagrams_rendered:
            diagrams_dir = os.path.join(os.path.dirname(__file__), "generated_diagrams")
            
            if os.path.exists(diagrams_dir):
                # Find files
                diagram_groups = {}
                for root, dirs, files in os.walk(diagrams_dir):
                    if "_archive" in root.split(os.sep):
                        continue
                    for file in files:
                        if not file.startswith('.'):
                            file_path = os.path.join(root, file)
                            filename = os.path.basename(file_path)
                            name, ext = os.path.splitext(filename)
                            if name not in diagram_groups:
                                diagram_groups[name] = {}
                            diagram_groups[name][ext] = file_path
                
                if not diagram_groups:
                    st.warning("No diagrams found.")
                
                for name, extensions in diagram_groups.items():
                    with st.expander(f"View: {name}", expanded=True):
                        if ".png" in extensions:
                            st.image(extensions[".png"], use_container_width=True)
                        
                        st.markdown("**Downloads**")
                        d_cols = st.columns(len(extensions))
                        for idx, (ext, file_path) in enumerate(extensions.items()):
                            filename = os.path.basename(file_path)
                            label = f"📥 {ext.upper().replace('.', '')}"
                            with open(file_path, "rb") as f:
                                d_cols[idx].download_button(
                                    label=label,
                                    data=f,
                                    file_name=filename,
                                    mime="image/png" if ext == ".png" else "text/plain",
                                    use_container_width=True
                                )
        else:
            st.info("Click 'Render Diagrams' to generate the visuals.")

# --- Developer Console ---
with st.expander("Developer Console", expanded=False):
    st.json({
        "status": "Active",
        "api_key_set": bool(get_active_api_key()),
        "diagram_types": diagram_types
    })
