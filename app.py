from flask import Flask, render_template, request, jsonify
from chatbot import Chatbot
from datetime import datetime
import os
import json

app = Flask(__name__)

# Initialize the chatbot with API key
GOOGLE_API_KEY = "AIzaSyCgOKvLXucC4x8xHVGrd81-eOajXWmrxKY"
chatbot = Chatbot(GOOGLE_API_KEY)

def get_time_based_greeting():
    """Return a time-appropriate greeting"""
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 17:
        return "Good afternoon"
    elif 17 <= current_hour < 22:
        return "Good evening"
    else:
        return "Good night"

def log_chat(user_input, bot_response):
    """Log chat interactions to a JSON file"""
    try:
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_file = f'logs/chat_{datetime.now().strftime("%Y-%m-%d")}.json'
        
        # Load existing logs or create new list
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        
        # Add new log entry
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "bot_response": bot_response
        })
        
        # Save updated logs
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
    except Exception as e:
        print(f"Error logging chat: {e}")

@app.route('/')
def home():
    greeting = get_time_based_greeting()
    return render_template('index.html', greeting=greeting)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        
        if not user_input:
            return jsonify({"error": "No message provided"})
        
        # Get beautifully formatted response from chatbot
        response = chatbot.get_response(user_input)
        
        # Log the interaction
        log_chat(user_input, response)
        
        return jsonify({"response": response})
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": "An error occurred processing your request"}), 500

if __name__ == '__main__':
    app.run(debug=True) 