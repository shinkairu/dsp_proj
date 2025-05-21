import streamlit as st
from morse_utils import text_to_morse, morse_to_text
from PIL import Image
import requests
import numpy as np
from scipy.io import wavfile
import io

st.set_page_config(page_title="Morse Code Translator + Decoder", layout="centered")
st.title("📡 Morse Code Translator + Decoder")

def ocr_image_from_url(image_bytes):
    response = requests.post(
        'https://api.ocr.space/parse/image',
        files={'filename': image_bytes},
        data={'apikey': 'helloworld', 'language': 'eng'}
    )
    result = response.json()
    return result['ParsedResults'][0]['ParsedText'] if 'ParsedResults' in result else ''

option = st.radio("Choose translation mode:", (
    "Text to Morse", "Morse to Text", 
    "Image to Morse", "Audio to Morse"
))

if option == "Text to Morse":
    text_input = st.text_input("Enter text:")
    if text_input:
        morse_output = text_to_morse(text_input)
        st.code(morse_output)

elif option == "Morse to Text":
    morse_input = st.text_input("Enter Morse code (space for letters, `/` for words):")
    if morse_input:
        text_output = morse_to_text(morse_input)
        st.code(text_output)

elif option == "Image to Morse":
    uploaded_image = st.file_uploader("Upload image with text", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
        extracted_text = ocr_image_from_url(uploaded_image)
        st.write("🔍 Extracted Text:")
        st.code(extracted_text.strip())
        morse_output = text_to_morse(extracted_text)
        st.write("📡 Morse Code:")
        st.code(morse_output)

elif option == "Audio to Morse":
    uploaded_audio = st.file_uploader("Upload Morse code audio (.wav)", type=["wav"])
    if uploaded_audio:
        rate, data = wavfile.read(io.BytesIO(uploaded_audio.read()))
        if data.ndim > 1:
            data = data[:, 0]
        signal = np.abs(data)
        threshold = 0.3 * np.max(signal)

        bits = (signal > threshold).astype(int)
        dot_length = rate // 10
        samples_per_symbol = []
        current = bits[0]
        count = 0
        for bit in bits:
            if bit == current:
                count += 1
            else:
                samples_per_symbol.append((current, count))
                current = bit
                count = 1
        samples_per_symbol.append((current, count))

        morse = ""
        for val, dur in samples_per_symbol:
            if val == 1:
                if dur < dot_length * 2:
                    morse += "."
                else:
                    morse += "-"
            else:
                if dur > dot_length * 5:
                    morse += " / "
                elif dur > dot_length * 2:
                    morse += " "

        st.write("📡 Morse Code:")
        st.code(morse)
        st.write("🔤 Translated Text:")
        st.code(morse_to_text(morse))

st.markdown("---")
st.markdown("✅ Supports A-Z, 0-9\n📍 Use `/` for space in Morse input")
