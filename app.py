import streamlit as st
import os
import time
import shutil
from pathlib import Path
import subprocess
from utils import (
    generate_voiceover_text,
    generate_voiceover_audio,
    merge_video_with_audio
)

# Create a consistent temp directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(APP_DIR, "temp")

# Clear temp directory on app reload (only for initial load)
if 'initialized' not in st.session_state:
    if os.path.exists(TEMP_DIR):
        try:
            # Remove all files and subfolders in temp directory
            for filename in os.listdir(TEMP_DIR):
                file_path = os.path.join(TEMP_DIR, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        except Exception as e:
            print(f"Error clearing temp directory: {e}")
    
    # Mark as initialized so we don't clear temp folder on every interaction
    st.session_state.initialized = True

# Recreate the temp directory
os.makedirs(TEMP_DIR, exist_ok=True)

st.set_page_config(
    page_title="Video Voiceover Generator",
    layout="wide"
)

# Initialize session state variables
if 'voiceover_text' not in st.session_state:
    st.session_state.voiceover_text = ""
if 'instructions' not in st.session_state:
    st.session_state.instructions = ""
if 'uploaded_video_path' not in st.session_state:
    st.session_state.uploaded_video_path = None
if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None
if 'merged_video_path' not in st.session_state:
    st.session_state.merged_video_path = None
if 'audio_generated' not in st.session_state:
    st.session_state.audio_generated = False
if 'generate_clicked' not in st.session_state:
    st.session_state.generate_clicked = False
if 'merge_successful' not in st.session_state:
    st.session_state.merge_successful = False
    
# Track if the app should switch to showing the merged video tab
if 'show_merged_tab' not in st.session_state:
    st.session_state.show_merged_tab = False

# Callback functions
def set_generate_clicked():
    st.session_state.generate_clicked = True

def set_generate_audio_clicked():
    st.session_state.generate_audio_clicked = True
    
def set_merge_clicked():
    st.session_state.merge_clicked = True

def update_instructions():
    st.session_state.instructions = st.session_state.temp_instructions

def on_generate_voiceover_text():
    try:
        with st.spinner("Generating voiceover text..."):
            generated_text = generate_voiceover_text(
                st.session_state.uploaded_video_path, 
                st.session_state.instructions
            )
            st.session_state.voiceover_text = generated_text
            # Update the text area display value as well
            st.session_state.temp_voiceover_text = generated_text
            st.success("Voiceover text generated successfully!")
    except Exception as e:
        st.error(f"Error generating voiceover text: {e}")
    finally:
        st.session_state.generate_clicked = False

def on_generate_audio():
    if not st.session_state.voiceover_text:
        st.warning("Please generate or enter voiceover text first.")
        st.session_state.generate_audio_clicked = False
        return
        
    try:
        with st.spinner("Generating voiceover audio..."):
            complete = generate_voiceover_audio(
                st.session_state.voiceover_text,
                st.session_state.audio_path,
                voice_name=st.session_state.voice,
                speed=1.0
            )
            if complete:
                st.success("Voiceover audio generated successfully!")
                # Verify audio file was created
                if os.path.exists(st.session_state.audio_path) and os.path.getsize(st.session_state.audio_path) > 0:
                    st.session_state.audio_generated = True
                    # Add a short delay to ensure file is completely written
                    time.sleep(1)
                else:
                    st.error(f"Audio file was not created at {st.session_state.audio_path}")
            else:
                st.error("Failed to generate voiceover audio.")
    except Exception as e:
        st.error(f"Error generating voiceover audio: {e}")
    finally:
        st.session_state.generate_audio_clicked = False

def on_merge_audio_video():
    if not st.session_state.audio_generated:
        st.warning("Please generate voiceover audio first.")
        st.session_state.merge_clicked = False
        return
        
    audio_path = st.session_state.audio_path
    # Additional verification of audio file
    if not (os.path.exists(audio_path) and os.path.getsize(audio_path) > 0):
        st.error(f"Audio file missing or empty: {audio_path}")
        st.session_state.merge_clicked = False
        return
        
    # Debug info
    st.info(f"Audio path: {audio_path}")
    st.info(f"Audio file size: {os.path.getsize(audio_path)} bytes")
    
    # Make a safety copy of the audio file in case it gets deleted during merge
    audio_backup_path = audio_path + ".backup"
    try:
        shutil.copy2(audio_path, audio_backup_path)
    except Exception as e:
        st.warning(f"Couldn't create backup of audio file: {e}")
    
    try:
        # First try with MoviePy
        with st.spinner("Merging audio with video..."):
            try:
                merged_path = merge_video_with_audio(
                    st.session_state.uploaded_video_path,
                    audio_path,
                    st.session_state.merged_video_path,
                    st.session_state.video_volume,
                    st.session_state.audio_volume
                )
                st.success(f"Video and audio merged successfully! {st.session_state.merged_video_path}")
                
                # Set merge successful flag
                st.session_state.merge_successful = True
                
            except Exception as e:
                st.warning(f"First merge attempt failed: {e}. Trying direct FFmpeg method...")
                
                # Check if audio file was deleted during the first attempt
                if not os.path.exists(audio_path) and os.path.exists(audio_backup_path):
                    st.info("Restoring audio file from backup...")
                    shutil.copy2(audio_backup_path, audio_path)
                
                # If MoviePy fails, try direct FFmpeg
                try:
                    # Modified FFmpeg command to handle both video and added audio volumes
                    cmd = [
                        'ffmpeg',
                        '-y',  # Overwrite output if it exists
                        '-i', st.session_state.uploaded_video_path,  # Input video
                        '-i', audio_path,  # Input audio
                        '-filter_complex', 
                        f'[0:a]volume={st.session_state.video_volume}[va];[1:a]volume={st.session_state.audio_volume}[aa];[va][aa]amix=inputs=2:duration=shortest[a]',
                        '-map', '0:v',  # Map video from first input
                        '-map', '[a]',  # Map adjusted audio
                        '-c:v', 'copy',  # Copy video codec (no re-encoding)
                        '-c:a', 'aac',  # Use AAC for audio
                        '-shortest',  # End when shortest input stream ends
                        st.session_state.merged_video_path
                    ]
                    
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        st.success("Video and audio merged successfully using direct FFmpeg!")
                        # Set merge successful flag
                        st.session_state.merge_successful = True
                    else:
                        st.error(f"FFmpeg error: {result.stderr}")
                except Exception as fallback_error:
                    st.error(f"Both merge methods failed. Error in fallback method: {fallback_error}")
    finally:
        st.session_state.merge_clicked = False
        # Clean up backup file
        if os.path.exists(audio_backup_path):
            try:
                os.remove(audio_backup_path)
            except:
                pass

# Main app title
st.title("Video Voiceover Generator")

# Video upload section
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # Save the uploaded video to our consistent temp directory
    video_path = os.path.join(TEMP_DIR, uploaded_file.name)
    
    # Write the file
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Update session state
    st.session_state.uploaded_video_path = video_path
    
    # Create the audio path based on the video path
    filename = os.path.basename(video_path)
    base_name = os.path.splitext(filename)[0]
    audio_path = os.path.join(TEMP_DIR, f"{base_name}.mp3")
    st.session_state.audio_path = audio_path
    
    # Create the merged video path
    merged_path = os.path.join(TEMP_DIR, f"{base_name}_merged{os.path.splitext(filename)[1]}")
    st.session_state.merged_video_path = merged_path

    # Main interface with two columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get tab index based on merge status
        tab_index = 1 if st.session_state.merge_successful else 0
        
        # Create tabs for videos
        video_tabs = st.tabs(["Original Video", "Video with Voiceover"])
        
        # Original video tab
        with video_tabs[0]:
            # Use CSS to control the video width
            st.markdown("""
            <style>
            .stVideo {
                width: 400px !important;
            }
            </style>
            """, unsafe_allow_html=True)
            st.video(video_path)
        
        # Merged video tab
        with video_tabs[1]:
            # Check if the merge is successful before displaying the video
            if st.session_state.merge_successful and os.path.exists(st.session_state.merged_video_path) and os.path.getsize(st.session_state.merged_video_path) > 0:
                st.video(st.session_state.merged_video_path)
                # Add a refresh button to reload the video if needed
                if st.button("Refresh Video"):
                    st.rerun()
            else:
                st.info("Merged video will appear here after processing")
    
    with col2:
        # Instructions for voiceover
        st.subheader("Voiceover Instructions")
        
        # Use a key for the text area and a callback to update session state
        if 'temp_instructions' not in st.session_state:
            st.session_state.temp_instructions = st.session_state.instructions
            
        st.text_area(
            "Enter instructions for the voiceover style/content:",
            key="temp_instructions",
            on_change=update_instructions,
            height=150
        )
        
        # Generate voiceover text button with session state to track clicks
        if 'generate_clicked' not in st.session_state:
            st.session_state.generate_clicked = False
            
        st.button(
            "Generate Voiceover Text", 
            on_click=set_generate_clicked, 
            key="generate_button"
        )
        
        # Process the button click using session state
        if st.session_state.generate_clicked:
            on_generate_voiceover_text()
    
    # Editable voiceover text
    st.subheader("Voiceover Text")
    
    # Initialize temp_voiceover_text with current value if it doesn't exist
    if 'temp_voiceover_text' not in st.session_state:
        st.session_state.temp_voiceover_text = st.session_state.voiceover_text
        
    def update_voiceover_text():
        st.session_state.voiceover_text = st.session_state.temp_voiceover_text
    
    # Display the generated/edited text
    voiceover_text_area = st.text_area(
        "Edit voiceover text if needed:",
        value=st.session_state.temp_voiceover_text,  # Use the value directly
        key="temp_voiceover_text",
        on_change=update_voiceover_text,
        height=200
    )
    
    # Voice selection and audio generation
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Store voice selection in session state
        voice_options = ['nova', 'alloy', 'ash', 'ballad', 'coral', 
                 'echo', 'fable', 'onyx', 'sage', 'shimmer']
        
        # Initialize voice if not already set
        if 'voice' not in st.session_state:
            st.session_state.voice = 'nova'
            
        # Display voice selector with current value
        st.session_state.voice = st.selectbox(
            "Voice",
            options=voice_options,
            index=voice_options.index(st.session_state.voice)
        )
    
    with col2:
        # Button with session state tracking
        if 'generate_audio_clicked' not in st.session_state:
            st.session_state.generate_audio_clicked = False
            
        st.button(
            "Generate Voiceover Audio", 
            on_click=set_generate_audio_clicked,
            key="generate_audio_button"
        )
        
        # Process audio generation if button was clicked
        if st.session_state.generate_audio_clicked:
            on_generate_audio()
            
        # Display audio player if audio exists
        if st.session_state.audio_generated and os.path.exists(st.session_state.audio_path):
            st.audio(st.session_state.audio_path)
    
    # Volume sliders and merge button
    st.subheader("Merge Audio with Video")
    
    # Video volume slider
    if 'video_volume' not in st.session_state:
        st.session_state.video_volume = 1.0
        
    video_volume_percent = st.slider(
        "Original Video Volume", 
        min_value=0, 
        max_value=100, 
        value=100,
        format="%d%%"
    )
    st.session_state.video_volume = video_volume_percent / 100.0
    
    # Voiceover audio volume slider
    if 'audio_volume' not in st.session_state:
        st.session_state.audio_volume = 1.0
        
    audio_volume_percent = st.slider(
        "Voiceover Volume", 
        min_value=0, 
        max_value=100, 
        value=100,
        format="%d%%"
    )
    st.session_state.audio_volume = audio_volume_percent / 100.0
    
    # Button with session state tracking
    if 'merge_clicked' not in st.session_state:
        st.session_state.merge_clicked = False
        
    st.button(
        "Merge Voiceover with Video", 
        on_click=set_merge_clicked,
        key="merge_button"
    )
    
    # Process merge if button was clicked
    if st.session_state.merge_clicked:
        on_merge_audio_video()
        
        # If merge was successful, switch to the merged video tab
        if st.session_state.merge_successful:
            # Force a rerun to update the UI and show the merged video
            st.rerun()
else:
    st.info("Please upload a video file to begin.")

# Add a footer with instructions
st.markdown("---")
st.markdown("""
### How to use:
1. Upload your video file
2. Enter instructions for the voiceover style and content
3. Generate the voiceover text and edit if needed
4. Select a voice and generate the voiceover audio
5. Adjust the volume of both the original video and voiceover audio
6. Merge the audio with your video
7. View the final video with voiceover in the second tab

Note: Temporary files are automatically cleared when you reload the app.
""")