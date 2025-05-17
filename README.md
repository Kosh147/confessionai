# Problem Solver Web App

A modern web application that helps users solve their problems by providing structured solutions. Users can input their situation either through text or voice recording, and the app will analyze their input to provide relevant solutions.

## Features

- Text input for describing your situation
- Voice recording capability with speech-to-text conversion
- Structured problem identification
- AI-powered solution suggestions
- Modern, responsive UI using Bootstrap
- Real-time processing

## Getting Started

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
```bash
python app.py
```

4. Open [http://localhost:5000](http://localhost:5000) in your browser.

## Usage

1. Enter your situation in the text area or click the microphone button to record your voice
2. Click "Get Solutions" to process your input
3. View the identified problems and suggested solutions
4. Follow the provided solutions to address your situation

## Technologies Used

- Python 3.x
- Flask
- Bootstrap 5
- SpeechRecognition
- Web Speech API (for browser-based recording)

## Development

The app is built with Python and Flask for the backend, and Bootstrap for the frontend. It uses the SpeechRecognition library for processing voice input and provides a clean, responsive interface that works well on both desktop and mobile devices.

## License

MIT 