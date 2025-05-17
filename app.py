from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import os
from werkzeug.utils import secure_filename
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from dotenv import load_dotenv

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
    """Use Mistral AI to identify problems from the input text."""
    messages = [
        ChatMessage(role="system", content="You are a helpful assistant that identifies specific problems from user inpssut. Return only a JSON array of problem strings, nothing else."),
        ChatMessage(role="user", content=f"Identify specific problems from this text. Star them as a statement that looks like 'I have...': {text}")
    ]
    
    response = mistral_client.chat(
        model="mistral-tiny",
        messages=messages,
    )
    
    try:
        # Extract the JSON array from the response
        problems = eval(response.choices[0].message.content)
        return problems
    except:
        # Fallback to basic problem identification if JSON parsing fails
        return ["Unable to identify specific problems"]

def generate_solution(problem):
    """Use Mistral AI to generate a step-by-step solution for a specific problem."""
    messages = [
        ChatMessage(role="system", content="You are a helpful assistant that provides detailed, step-by-step solutions to problems. Format your response as a JSON object with 'steps' array."),
        ChatMessage(role="user", content=f"Provide short, step-by-step action plan as a solution for this problem. Only specific actions. If no solution available answer that you are unable to solve it: {problem}")
    ]
    
    response = mistral_client.chat(
        model="mistral-tiny",
        messages=messages,
    )
    
    try:
        # Extract the JSON object from the response
        solution = eval(response.choices[0].message.content)
        return solution
    except:
        # Fallback to basic solution if JSON parsing fails
        return {
            "steps": ["Unable to generate detailed solution"],
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
    solution = generate_solution(problem)
    return jsonify(solution)

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
    
    # Convert speech to text
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
            # Clean up the audio file
            os.remove(filepath)

if __name__ == '__main__':
    app.run(debug=True) 