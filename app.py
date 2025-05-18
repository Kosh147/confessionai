from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import os
from werkzeug.utils import secure_filename
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from dotenv import load_dotenv
import json
import requests
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Mistral client
mistral_client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load personal solutions database
with open('test_db.json', 'r') as f:
    PERSONAL_SOLUTIONS = json.load(f)

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
    """Use Mistral AI to generate solution options for a specific problem, including personal solutions if they match."""
    system_prompt = (
        "You are a helpful assistant that provides several distinct solution options for a problem. "
        "You also have access to a user's personal solutions database as a JSON array. "
        "If any solution in the personal solutions database matches the user's problem, include it as a solution option (preferably first). "
        "Otherwise, generate new options. Make them short and personal."
        "Return a JSON object with a 'options' array, each option is a short, actionable suggestion. Do not include any explanation."
    )
    user_prompt = (
        f"Personal solutions database: {json.dumps(PERSONAL_SOLUTIONS)}\n"
        f"User problem: {problem}"
    )
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user_prompt)
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
        ChatMessage(role="user", content=f"Provide 5 best implementation actions related to local community for this solution option: {solution_option}")
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

def find_resource(action, user_input):
    """Use LLM to find a relevant resource (link + label) for the action and user input (location/comments)."""
    messages = [
        ChatMessage(
            role="system",
            content=(
                "You are a helpful assistant that finds the most relevant online resource for a given action and user location/comments. "
                "Return a JSON object with 'label' (short description) and 'url' (link). "
                "If no direct resource is available, suggest a local social event or community resource (e.g., townhall, local Facebook group, etc.) with a relevant link. "
                "If you can't find anything, return a link to a local government or community website. Do not include any explanation."
            )
        ),
        ChatMessage(role="user", content=f"Action: {action}\nLocation or comments: {user_input}")
    ]
    response = mistral_client.chat(
        model="mistral-tiny",
        messages=messages,
    )
    try:
        resource = json.loads(response.choices[0].message.content)
        return resource
    except Exception:
        return {"label": "Local community website", "url": "https://www.gov.uk/find-local-council"}

def brave_search(query, solution=None):
    api_key = os.getenv('BRAVE_API_KEY')
    if not api_key:
        return None
    url = 'https://api.search.brave.com/res/v1/web/search'
    headers = {
        'Accept': 'application/json',
        'X-Subscription-Token': api_key
    }
    if solution:
        query = f"{query} {solution}".strip()
    params = {'q': query, 'count': 1}
    #print(query)
    try:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('web', {}).get('results'):
                result = data['web']['results'][0]
                return {
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('description', '')
                }
        return None
    except Exception:
        return None
    finally:
        time.sleep(2)

def find_personal_chain(problem, solution=None, action=None):
    """Use LLM to find the best-matching Implementation and Action chain from personal solutions DB."""
    system_prompt = (
        "You are a helpful assistant. You have access to a user's personal solutions database as a JSON array. "
        "Each entry has columns: Problem, Solution, Implementation, action. "
        "Given a user's current problem, solution, and action, find the most relevant Implementation and Action chain from the database. "
        "Return a JSON array of objects, each with 'Implementation' and 'Action' fields, representing the chain of events for the user to follow. "
        "If no good match, return an empty array. Do not include any explanation."
    )
    user_prompt = (
        f"Personal solutions database: {json.dumps(PERSONAL_SOLUTIONS)}\n"
        f"User problem: {problem}\n"
        f"User solution: {solution or ''}\n"
        f"User action: {action or ''}"
    )
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user_prompt)
    ]
    response = mistral_client.chat(
        model="mistral-tiny",
        messages=messages,
    )
    try:
        chain = json.loads(response.choices[0].message.content)
        print(f"LLM chain answer{chain}")
        return chain
    except Exception:
        return []

def align_problem_solution(user_problem, user_solution):
    """Use LLM to find the single best-matching Problem/Solution in the personal database."""
    system_prompt = (
        "You are a helpful assistant. You have access to a user's personal solutions database as a JSON array. "
        "Each entry has columns: Problem, Solution, Implementation, action. "
        "Given a user's current problem and solution, select only the single best-matching Problem/Solution pair in the database. "
        "Return a JSON object with 'Problem' and 'Solution' fields from the database. If no good match, return an empty object. Do not include any explanation."
    )
    user_prompt = (
        f"Personal solutions database: {json.dumps(PERSONAL_SOLUTIONS)}\n"
        f"User problem: {user_problem}\n"
        f"User solution: {user_solution or ''}"
    )
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user_prompt)
    ]
    response = mistral_client.chat(
        model="mistral-tiny",
        messages=messages,
    )
    print(f"LLM ANSWER: {response}")
    try:
        match = json.loads(response.choices[0].message.content)
        return match if match.get('Problem') and match.get('Solution') else None
    except Exception:
        return None

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

@app.route('/elevenlabs_stt', methods=['POST'])
def elevenlabs_stt():
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        return jsonify({'error': 'No ElevenLabs API key set'}), 500
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    # Save temp file
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_audio.webm')
    audio_file.save(temp_path)
    # Convert webm to wav (ElevenLabs expects wav/mpeg/mp3/mp4/m4a)
    import subprocess
    wav_path = temp_path.replace('.webm', '.wav')
    try:
        subprocess.run([
            'ffmpeg', '-y', '-i', temp_path, '-ar', '16000', '-ac', '1', wav_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        os.remove(temp_path)
        return jsonify({'error': f'Audio conversion failed: {e}'}), 500
    # Call ElevenLabs API
    url = 'https://api.elevenlabs.io/v1/speech-to-text'
    headers = {
        'xi-api-key': api_key
    }
    files = {
        'file': open(wav_path, 'rb')
    }
    data = {
        'model_id': 'scribe_v1'  # or another supported model
    }
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        if response.status_code == 200:
            data = response.json()
            text = data.get('text', '')
            return jsonify({'text': text})
        else:
            return jsonify({'error': f'ElevenLabs error: {response.text}'}), 500
    finally:
        files['file'].close()
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

@app.route('/get_resource', methods=['POST'])
def get_resource():
    data = request.json
    action = data.get('action', '')
    user_input = data.get('user_input', '')
    solution = data.get('solution', '')
    query = f"{action} {user_input}".strip()
    result = brave_search(query, solution)
    if result:
        return jsonify(result)
    else:
        return jsonify({'title': 'No relevant resource found', 'url': '', 'snippet': ''})

@app.route('/get_personal_chain', methods=['POST'])
def get_personal_chain():
    data = request.json
    user_problem = data.get('problem', '')
    user_solution = data.get('solution', '')
    # Use LLM to align to best-matching Problem/Solution
    match = align_problem_solution(user_problem, user_solution)
    chain = []
    if match:
        # If LLM returned Implementation and/or action, use them directly
        impl = match.get('Implementation')
        act = match.get('action')
        if impl:
            chain.append({'Implementation': impl})
        if act:
            chain.append({'Action': act})
        # If not, fallback to searching the database for the matching Problem/Solution
        if not impl or not act:
            for entry in PERSONAL_SOLUTIONS:
                if entry.get('Problem') == match['Problem'] and entry.get('Solution') == match['Solution']:
                    if not impl and entry.get('Implementation'):
                        chain.append({'Implementation': entry.get('Implementation')})
                    if not act and entry.get('action'):
                        chain.append({'Action': entry.get('action')})
                    break
    return jsonify({'chain': chain})

if __name__ == '__main__':
    app.run(debug=True) 