from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import os
from werkzeug.utils import secure_filename
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Mistral client
mistral_client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def identify_problems(text):
    """Use Mistral AI to identify problems and categories from the input text."""
    messages = [
        ChatMessage(
            role="system",
            content=(
                "You are a helpful assistant that identifies specific problems from user input. "
                "Return a JSON array of objects, each with 'problem' (a statement like 'I have...') "
                "and 'category' (one word, e.g. 'Health', 'Money', 'Activity', 'Social', 'Work', 'Other'). "
                "Example: [{\"problem\": \"I have little free time\", \"category\": \"Time\"}]. "
                "Do not include any explanation."
            )
        ),
        ChatMessage(role="user", content=f"Identify specific problems and their category from this text: {text}")
    ]
    response = mistral_client.chat(
        model="mistral-tiny",
        messages=messages,
    )
    try:
        problems = json.loads(response.choices[0].message.content)
        return problems
    except Exception:
        return [{"problem": "Unable to identify specific problems", "category": "Other"}]

def generate_solution_options(problem):
    """Use Mistral AI to generate solution options for a specific problem."""
    messages = [
        ChatMessage(role="system", content="You are a helpful assistant that provides several distinct solution options for a problem. Return a JSON object with a 'options' array, each option is a short, actionable suggestion. Do not include any explanation."),
        ChatMessage(role="user", content=f"Provide several distinct solution options for this problem. Only actionable suggestions: {problem}")
    ]
    response = mistral_client.chat(
        model="mistral-tiny",
        messages=messages,
    )
    try:
        solution = json.loads(response.choices[0].message.content)
        return solution
    except Exception:
        return {
            "options": ["Unable to generate solution options"]
        }

def generate_implementation_actions(solution_option):
    """Use Mistral AI to generate implementation actions for a selected solution option."""
    messages = [
        ChatMessage(role="system", content="You are a helpful assistant that provides implementation actions for a solution. Return a JSON object with an 'actions' array, each action is a short, actionable button label (e.g., 'Schedule a call', 'Book a meeting', 'Send an email', 'Start now'). Do not include any explanation."),
        ChatMessage(role="user", content=f"Provide implementation actions for this solution option: {solution_option}")
    ]
    response = mistral_client.chat(
        model="mistral-tiny",
        messages=messages,
    )
    try:
        actions = json.loads(response.choices[0].message.content)
        return actions
    except Exception:
        return {
            "actions": ["Start now"]
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_text', methods=['POST'])
def process_text_route():
    text = request.json.get('text', '')
    problems = identify_problems(text)
    return jsonify({
        'problems': problems
    })

@app.route('/get_solution', methods=['POST'])
def get_solution():
    problem = request.json.get('problem', '')
    solution = generate_solution_options(problem)
    return jsonify(solution)

@app.route('/get_implementation', methods=['POST'])
def get_implementation():
    solution_option = request.json.get('solution_option', '')
    actions = generate_implementation_actions(solution_option)
    return jsonify(actions)

@app.route('/process_audio', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = secure_filename(audio_file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(filepath)
    recognizer = sr.Recognizer()
    with sr.AudioFile(filepath) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            problems = identify_problems(text)
            return jsonify({
                'text': text,
                'problems': problems
            })
        except sr.UnknownValueError:
            return jsonify({'error': 'Could not understand audio'}), 400
        except sr.RequestError as e:
            return jsonify({'error': f'Could not request results: {str(e)}'}), 500
        finally:
            os.remove(filepath)

if __name__ == '__main__':
    app.run(debug=True) 