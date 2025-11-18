import streamlit as st
import os
import tempfile
import time
from pathlib import Path
import uuid
from utils import *
# Explicitly ensure APP_USERNAME and APP_PASSWORD are available
try:
    from utils import APP_USERNAME, APP_PASSWORD
except ImportError:
    st.error("Error: Could not import APP_USERNAME and APP_PASSWORD from utils. Please check your .env file.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="VoxOver: AI Narration Studio",
    page_icon="🎙️",
    layout="wide"
)

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 1rem;
    }
    .info-text {
        font-size: 1rem;
        color: #555;
    }
    .success-text {
        color: #0f5132;
        background-color: #d1e7dd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stProgress .st-bo {
        background-color: #4CAF50;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if 'uploaded_video_path' not in st.session_state:
    st.session_state.uploaded_video_path = None
if 'voiceover_text' not in st.session_state:
    st.session_state.voiceover_text = None
if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None
if 'merged_video_path' not in st.session_state:
    st.session_state.merged_video_path = None
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'processing_error' not in st.session_state:
    st.session_state.processing_error = None
if 'unique_id' not in st.session_state:
    st.session_state.unique_id = str(uuid.uuid4())

# Function to reset the app state
def reset_app_state():
    st.session_state.uploaded_video_path = None
    st.session_state.voiceover_text = None
    st.session_state.audio_path = None
    st.session_state.merged_video_path = None
    st.session_state.is_processing = False
    st.session_state.current_step = 1
    st.session_state.processing_complete = False
    st.session_state.processing_error = None
    st.session_state.unique_id = str(uuid.uuid4())
    
    # Clear temp directory
    if os.path.exists(st.session_state.temp_dir):
        for file in os.listdir(st.session_state.temp_dir):
            file_path = os.path.join(st.session_state.temp_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                st.error(f"Error deleting file {file_path}: {e}")

# Generate voiceover text based on video content and instructions
def process_video_for_text(video_path, instructions):
    try:
        st.session_state.current_step = 2
        with st.spinner("Analyzing video content and generating voiceover text..."):
            voiceover_text = generate_voiceover_text(video_path, instructions)
            st.session_state.voiceover_text = voiceover_text
            st.session_state.current_step = 3
        return voiceover_text
    except Exception as e:
        st.session_state.processing_error = f"Error generating voiceover text: {str(e)}"
        return None

# Generate audio from voiceover text
def generate_audio(voiceover_text, voice_name, speed):
    try:
        st.session_state.current_step = 4
        audio_path = os.path.join(st.session_state.temp_dir, f"voiceover_{st.session_state.unique_id}.mp3")
        with st.spinner("Converting text to speech..."):
            generate_voiceover_audio_elevenlabs(voiceover_text, 
            audio_path)
            st.session_state.audio_path = audio_path
            st.session_state.current_step = 5
        return audio_path
    except Exception as e:
        st.session_state.processing_error = f"Error generating audio: {str(e)}"
        return None

# Merge video with audio
def merge_video_audio(video_path, audio_path, video_volume, audio_volume):
    try:
        st.session_state.current_step = 7
        merged_path = os.path.join(st.session_state.temp_dir, f"merged_{st.session_state.unique_id}.mp4")
        with st.spinner("Merging video with voiceover audio..."):
            merge_video_with_audio(video_path, audio_path, merged_path, video_volume, audio_volume)
            st.session_state.merged_video_path = merged_path
            st.session_state.current_step = 8
            st.session_state.processing_complete = True
        return merged_path
    except Exception as e:
        st.session_state.processing_error = f"Error merging video with audio: {str(e)}"
        return None

# Authentication check
if not st.session_state.authenticated:
    # Login page
    st.markdown('<div class="main-header">🔐 Login Required</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-text">Please enter your credentials to access VoxOver: AI Narration Studio</div>', unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("### Enter Credentials")
            username_input = st.text_input("Username", key="username_input")
            password_input = st.text_input("Password", type="password", key="password_input")
            login_button = st.form_submit_button("Login", use_container_width=True)
            
            if login_button:
                # Strip whitespace from inputs and env values
                username_input_clean = username_input.strip() if username_input else ""
                password_input_clean = password_input.strip() if password_input else ""
                username_env = APP_USERNAME.strip() if APP_USERNAME else ""
                password_env = APP_PASSWORD.strip() if APP_PASSWORD else ""
                
                # Check if credentials are loaded from .env
                if not username_env or not password_env:
                    st.error("⚠️ Error: APP_USERNAME (or USERNAME) and PASSWORD must be set in .env file")
                elif username_input_clean == username_env and password_input_clean == password_env:
                    st.session_state.authenticated = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")
    
    st.stop()

# Main app header (only shown if authenticated)
col_header1, col_header2 = st.columns([4, 1])
with col_header1:
    st.markdown('<div class="main-header">🎙️ VoxOver: AI Narration Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-text">Create professional AI voiceovers for your videos with ease.</div>', unsafe_allow_html=True)
with col_header2:
    if st.button("Logout", key="logout_button"):
        st.session_state.authenticated = False
        reset_app_state()
        st.rerun()

# Create two columns for the main layout
col1, col2 = st.columns([3, 2])

with col1:
    # Step progress indicator
    steps = ["Upload Video", "Analyze Video", "Edit Script", "Generate Audio", "Preview Audio", "Set Volumes", "Merge Media", "Download"]
    current_step = st.session_state.current_step
    progress_value = current_step / len(steps)
    
    st.progress(progress_value)
    st.write(f"Step {current_step} of {len(steps)}: {steps[current_step-1]}")
    
    # File upload section
    st.markdown('<div class="sub-header">Step 1: Upload Your Video</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mov", "avi", "wmv"], key="video_uploader")
    
    if uploaded_file is not None and st.session_state.uploaded_video_path is None:
        # Save uploaded file to temporary directory
        temp_video_path = os.path.join(st.session_state.temp_dir, f"uploaded_{st.session_state.unique_id}.mp4")
        with open(temp_video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.uploaded_video_path = temp_video_path
        st.success(f"Video uploaded successfully: {uploaded_file.name}")
    
    # Instructions text area
    st.markdown('<div class="sub-header">Step 2: Provide Voiceover Instructions</div>', unsafe_allow_html=True)
    instructions = st.text_area(
        "Describe the style and content you want for your voiceover:",
        placeholder="Example: Create a professional, enthusiastic narration that explains the key points shown in the video. Use a conversational tone suitable for a marketing presentation.",
        height=100
    )
    
    # Generate voiceover text button
    if st.session_state.uploaded_video_path is not None and st.button("Generate Voiceover Text", key="generate_text_button"):
        if not instructions:
            st.warning("Please provide instructions for the voiceover style and content.")
        else:
            st.session_state.is_processing = True
            process_video_for_text(st.session_state.uploaded_video_path, instructions)
    
    # Display and edit voiceover text
    if st.session_state.voiceover_text is not None:
        st.markdown('<div class="sub-header">Step 3: Edit Voiceover Script</div>', unsafe_allow_html=True)
        edited_text = st.text_area("Edit the generated voiceover text if needed:", value=st.session_state.voiceover_text, height=200)
        
        # Generate audio button
        if st.button("Generate Voiceover Audio", key="generate_audio_button"):
            st.session_state.voiceover_text = edited_text  # Update with edited text
            generate_audio(edited_text, "nova", 1.0)  # Use default voice and speed
    
    # Display audio player if audio has been generated
    if st.session_state.audio_path is not None and os.path.exists(st.session_state.audio_path):
        st.markdown('<div class="sub-header">Step 4: Preview Voiceover Audio</div>', unsafe_allow_html=True)
        st.audio(st.session_state.audio_path, format="audio/mp3")
        st.success("✅ Voiceover audio generated successfully! You can play it above and adjust volume settings below.")
    
    # Volume adjustment sliders
    if st.session_state.audio_path is not None:
        st.markdown('<div class="sub-header">Step 6: Adjust Volume Levels</div>', unsafe_allow_html=True)
        vol_col1, vol_col2 = st.columns(2)
        
        with vol_col1:
            video_volume = st.slider("Original Video Volume:", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
        
        with vol_col2:
            audio_volume = st.slider("Voiceover Volume:", min_value=0.0, max_value=1.0, value=1.0, step=0.1)
        
        # Merge button
        if st.button("Merge Video with Voiceover", key="merge_button"):
            merge_video_audio(
                st.session_state.uploaded_video_path,
                st.session_state.audio_path,
                video_volume,
                audio_volume
            )

with col2:
    # Display error message if any
    if st.session_state.processing_error:
        st.error(st.session_state.processing_error)
    
    # Display the videos in tabs
    st.markdown('<div class="sub-header">Preview</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Original Video", "Video with Voiceover"])
    
    with tab1:
        if st.session_state.uploaded_video_path:
            st.video(st.session_state.uploaded_video_path)
        else:
            st.info("Upload a video to see preview")
    
    with tab2:
        if st.session_state.merged_video_path:
            st.video(st.session_state.merged_video_path)
            
            # Download button for final video
            st.markdown('<div class="sub-header">Step 8: Download Final Video</div>', unsafe_allow_html=True)
            
            with open(st.session_state.merged_video_path, "rb") as file:
                st.download_button(
                    label="Download Video with Voiceover",
                    data=file,
                    file_name=f"VoxOver_{Path(st.session_state.uploaded_video_path or 'video').stem}_{st.session_state.unique_id}.mp4",
                    mime="video/mp4",
                    key="download_button"
                )
            
            st.markdown('<div class="success-text">✅ Processing complete! Your video with AI voiceover is ready to download.</div>', unsafe_allow_html=True)
        else:
            if st.session_state.current_step >= 3:
                st.info("Complete all steps to generate the final video with voiceover")
            else:
                st.info("Upload a video and follow the steps on the left to create your voiceover")

# Reset button at the bottom
if st.session_state.uploaded_video_path is not None:
    if st.button("Start Over", key="reset_button"):
        reset_app_state()
        st.rerun()

# Footer
st.markdown("---")
st.markdown('<div class="info-text">VoxOver: AI Narration Studio - Create professional voiceovers for your videos with ease.</div>', unsafe_allow_html=True)