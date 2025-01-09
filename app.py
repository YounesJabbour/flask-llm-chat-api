from flask import Flask, request, jsonify, send_file
import requests
import os
import subprocess  # To run shell commands
from io import BytesIO  # To handle binary data in memory

app = Flask(__name__)

def get_sentiment(query):
    url = "https://sentiment-analysis.eastus.cloudapp.azure.com/analyze"
    payload = {"query": query}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("sentiment")
    except requests.exceptions.RequestException as e:
        return None

def generate_response(query, sentiment):
    if sentiment is None:
        return None
    url = "https://sentiment-analysis.eastus.cloudapp.azure.com/chat/generate-response"
    payload = {"query": query, "emotion": sentiment}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("response")
    except requests.exceptions.RequestException as e:
        return None

def text_to_speech(text):
    if text is None:
        return None
    url = "https://tts.ilyaselmabrouki.com/generate"
    payload = {"text": text}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.content  # This is the binary MP3 data
    except requests.exceptions.RequestException as e:
        return None

def convert_mp3_to_wav(mp3_data):
    """
    Convert MP3 audio data to WAV format using ffmpeg.
    """
    print(f"MP3 data size: {len(mp3_data)} bytes")
    try:
        # Save the MP3 data to a temporary file
        mp3_file = "temp_audio.mp3"
        with open(mp3_file, "wb") as f:
            f.write(mp3_data)

        # Convert MP3 to WAV using ffmpeg
        wav_file = "temp_audio.wav"
        process = subprocess.run(
            ["ffmpeg", "-y", "-i", mp3_file, wav_file],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if process.returncode != 0:
          print(f"FFmpeg error: {process.stderr}")
        return None

        # Read the WAV file back into memory
        with open(wav_file, "rb") as f:
            wav_data = f.read()

        # Clean up temporary files
        os.remove(mp3_file)
        os.remove(wav_file)

        return wav_data
    except Exception as e:
        print(f"Error converting MP3 to WAV: {e}")
        return None

def generate_lip_sync(wav_data):
    """
    Generate lip-sync data using Rhubarb Lip Sync.
    """
    try:
        # Save the WAV data to a temporary file
        wav_file = "temp_audio.wav"
        with open(wav_file, "wb") as f:
            f.write(wav_data)

        # Generate lip-sync data using Rhubarb Lip Sync
        json_file = "temp_audio.json"
        subprocess.run(
            ["./bin/rhubarb", "-f", "json", "-o", json_file, wav_file, "-r", "phonetic"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Read the JSON file back into memory
        with open(json_file, "r") as f:
            lip_sync_data = f.read()

        # Clean up temporary files
        os.remove(wav_file)
        os.remove(json_file)

        return lip_sync_data
    except Exception as e:
        print(f"Error generating lip-sync data: {e}")
        return None

@app.route('/chat', methods=['POST'])
def chat():
    user_query = request.json.get('query')
    if not user_query:
        return jsonify({"error": "No query provided"}), 400

    sentiment = get_sentiment(user_query)
    if sentiment is None:
        return jsonify({"error": "Failed to analyze sentiment"}), 500

    response_text = generate_response(user_query, sentiment)
    if response_text is None:
        return jsonify({"error": "Failed to generate response"}), 500

    # Step 1: Generate MP3 audio
    mp3_data = text_to_speech(response_text)
    if mp3_data is None:
        return jsonify({"error": "Failed to generate audio"}), 500

    # Step 2: Convert MP3 to WAV
    wav_data = convert_mp3_to_wav(mp3_data)
    if wav_data is None:
        return jsonify({"error": "Failed to convert MP3 to WAV"}), 500

    # Step 3: Generate lip-sync data
    lip_sync_data = generate_lip_sync(wav_data)
    if lip_sync_data is None:
        return jsonify({"error": "Failed to generate lip-sync data"}), 500

    # Return the response text, WAV audio, and lip-sync data
    return jsonify({
        "response_text": response_text,
        "audio_data": wav_data.hex(),  # Convert WAV data to hex string for JSON serialization
        "lip_sync_data": lip_sync_data  # Lip-sync data as JSON string
    })

# if __name__ == '__main__':
#     # Bind to 0.0.0.0 and use the PORT environment variable
#     port = int(os.environ.get("PORT", 5000))  # Default to 5000 for local development
#     app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    app.run(debug=True)