from flask import Flask, request, jsonify
import requests

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
        return response.content
    except requests.exceptions.RequestException as e:
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

    audio_data = text_to_speech(response_text)
    if audio_data is None:
        return jsonify({"error": "Failed to generate audio"}), 500

    return jsonify({
        "response_text": response_text,
        "audio_data": audio_data.hex()  # Convert bytes to hex string for JSON serialization
    })

if __name__ == '__main__':
    app.run(debug=True)