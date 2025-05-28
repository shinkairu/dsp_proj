import streamlit as st
from PIL import Image
import requests
import numpy as np
from scipy.io import wavfile
import io
import os
import sys
from morse_utils import text_to_morse, morse_to_text, morse_table  # Custom utility module

# ----------- Page config -----------
st.set_page_config(page_title="Morse Code Translator 📡", layout="wide")

# ----------- Background image -----------
@st.cache_data
def get_base64_of_bin_file(image_path):
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def set_background(image_path):
    bin_str = get_base64_of_bin_file(image_path)
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}
    .css-1bzp7po {{
        justify-content: center !important;
    }}
    .nav-container {{
        display: flex;
        justify-content: center;
        gap: 40px;
        padding: 10px 0;
        background-color: rgba(0, 0, 0, 0.5);
        border-bottom: 2px solid #ffffff33;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    button[data-baseweb="tab"] {{
        background-color: rgba(255, 255, 255, 0.65);
        border: 2px solid #7b1fa2;
        color: #4A0072;
        font-weight: bold;
        padding: 10px 20px;
        border-radius: 12px;
        margin: 5px;
        transition: all 0.3s ease;
    }}
    button[data-baseweb="tab"]:hover {{
        background-color: #e1bee7;
        border-color: #4a0072;
        color: #2e003e;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        background-color: #7b1fa2;
        color: white;
        border-color: #4a0072;
    }}
    h1, h2, h3 {{
        color: #ffffff;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
        font-size: 2.5em;
    }}
    body, html, p, div {{
        color: #ffffff !important;
        font-size: 18px;
        font-family: 'Segoe UI', sans-serif;
    }}
    .stButton > button {{
        background-color: #00b4d8;
        color: #ffffff;
        border-radius: 10px;
        padding: 10px 24px;
        font-size: 18px;
        font-weight: bold;
        border: none;
        transition: background-color 0.3s ease;
    }}
    .stButton > button:hover {{
        background-color: #0077b6;
    }}
    textarea, input {{
        background-color: rgba(255,255,255,0.9) !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
    }}
    .info-box {{
        background: rgba(255, 255, 255, 0.85);
        border-left: 6px solid #00b4d8;
        padding: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        color: #000000 !important;
    }}
    .info-box h1, .info-box h2, .info-box h3, .info-box p, .info-box li {{
        color: #000000 !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

bg_path = os.path.join(os.path.dirname(__file__), "bg.jpg")
if os.path.exists(bg_path):
    set_background(bg_path)

# ----------- Tabs Setup -----------
tabs = st.tabs(["DECODER", "FACTS", "CONTACT"])

# ----------- Tab: DECODER -----------
with tabs[0]:
    st.title("Morse Code Translator")

    st.markdown("""
    <div class='info-box'>
        <h3>🔤 Translate between English and Morse Code</h3>
        <p>Choose your direction, enter your message, and click <b>Translate</b> to see the result.</p>
    </div>
    """, unsafe_allow_html=True)

    mode = st.radio("Select translation mode:", ["Text to Morse", "Morse to Text", "Image to Morse/Text", "Morse Audio to Text"])

    if mode == "Text to Morse":
        st.subheader("Text to Morse Translation")
        text_input = st.text_input("Enter English text:")
        if text_input:
            # Replace space with slash to explicitly mark word boundaries
            formatted_input = text_input.strip().replace(" ", " / ")
            morse_output = text_to_morse(formatted_input)
            st.code(morse_output, language='text')

    elif mode == "Morse to Text":
        st.subheader("Morse Input to Text Decoder")
        morse_input = st.text_input("Enter Morse code (space for letters, `/` for words):")
        st.markdown(morse_table)
        if morse_input:
            text_output = morse_to_text(morse_input)
            st.code(text_output, language='text')

    elif mode == "Image to Morse/Text":
        st.subheader("📷 Image to Morse/Text")

        uploaded_image = st.file_uploader("Upload an image with Morse or English text", type=["png", "jpg", "jpeg"])
        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
            extracted_text = ocr_image_from_url(uploaded_image)
            if extracted_text:
                st.write("🔍 Extracted Text:")
                st.code(extracted_text.strip())

                if any(c in extracted_text for c in ['.', '-', '/', ' '] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")):
                    try:
                        if any(c in extracted_text for c in ['.', '-', '/']):
                            decoded = morse_to_text(extracted_text)
                            st.write("🔤 Translated Text:")
                            st.code(decoded)
                        else:
                            morse_output = text_to_morse(extracted_text)
                            st.write("📡 Morse Code:")
                            st.code(morse_output)
                    except Exception as e:
                        st.error(f"Error during translation: {e}")
            else:
                st.error("No text detected in the image.")

    elif mode == "Morse Audio to Text":
        st.subheader("🔊 Upload a Morse Code Audio File")
        audio_file = st.file_uploader("Upload .wav file (700Hz tone, 20 WPM)", type=["wav"])

        if audio_file is not None:
            st.audio(audio_file, format="audio/wav")

        # Read and process the audio
        sample_rate, data = wavfile.read(audio_file)

        if len(data.shape) > 1:
            data = data[:, 0]  # Use mono if stereo

        # Normalize audio and apply threshold
        data = data / np.max(np.abs(data))
        threshold = 0.2  # equivalent to ~ -30 dB

        signal = np.where(np.abs(data) > threshold, 1, 0)

        # Detect durations
        diffs = np.diff(signal)
        transitions = np.where(diffs != 0)[0]
        durations = np.diff(np.concatenate(([0], transitions, [len(signal)])))

        # Determine dots/dashes based on duration (at 20 WPM, dot ~ 60ms)
        time_per_sample = 1 / sample_rate
        time_per_unit = 1.2 / 20  # 60ms
        symbols = []

        for i, dur in enumerate(durations[1:-1:2]):  # Only 'high' signals
            duration_secs = dur * time_per_sample
            if duration_secs < time_per_unit * 1.5:
                symbols.append(".")
            else:
                symbols.append("-")

            # Add spacing
            if i < len(durations[1:-1:2]) - 1:
                space_dur = durations[2 + i*2] * time_per_sample
                if space_dur > time_per_unit * 6:
                    symbols.append(" / ")
                elif space_dur > time_per_unit * 2:
                    symbols.append(" ")

        morse_string = "".join(symbols)
        st.write("📡 Detected Morse Code:")
        st.code(morse_string)

        try:
            translated_text = morse_to_text(morse_string)
            st.write("🔤 Translated Text:")
            st.code(translated_text)
        except Exception as e:
            st.error(f"Error translating Morse: {e}")

# ----------- Tab: FACTS -----------
with tabs[1]:
    st.title("📚 Fun Morse Code Facts")
    st.markdown("""
    <div class='info-box'>
        <ul>
            <li>Morse code was developed in the 1830s by Samuel Morse and Alfred Vail.</li>
            <li>It was first used for telegraph communication.</li>
            <li>Morse code is still used in aviation and amateur radio today.</li>
            <li>The distress signal SOS is "... --- ...", chosen for its simplicity.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ----------- Tab: CONTACT -----------
with tabs[2]:
    st.title("📬 Contact Us")
    st.markdown("""
    <div class='info-box'>
        <p><strong>Developed by:</strong> Group 1 - Adrian Bangalando, Keith Del Carmen, Denisse Escape, and Louie Rizo</p>
        <p><strong>GitHub</strong>: <a href='https://github.com/shinkairu' target='_blank'>github.com/shinkairu</a></p>
        <p><strong>Email</strong>: group1_BDER@gmail.com</p>
        <blockquote>This project is specifically for our DSP Course! All thanks to Dr. Jonathan Taylar for guiding us! Thank you!</blockquote>
    </div>
    """, unsafe_allow_html=True)
