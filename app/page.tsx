'use client';

import { useState } from 'react';
import { MicrophoneIcon, StopIcon } from '@heroicons/react/24/solid';

export default function Home() {
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [problems, setProblems] = useState<string[]>([]);
  const [solutions, setSolutions] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        // Here you would typically send the audio to a speech-to-text service
        // For now, we'll just set a placeholder text
        setInput('Voice recording completed. Processing...');
        processInput('Voice recording completed. Processing...');
      };

      mediaRecorder.start();
      setIsRecording(true);

      // Stop recording after 10 seconds
      setTimeout(() => {
        mediaRecorder.stop();
        setIsRecording(false);
        stream.getTracks().forEach(track => track.stop());
      }, 10000);
    } catch (err) {
      console.error('Error accessing microphone:', err);
    }
  };

  const processInput = (text: string) => {
    setIsProcessing(true);
    // Here you would typically send the text to an LLM service
    // For now, we'll use a simple example
    const exampleProblems = [
      'Need outdoor activity',
      'Looking for tennis courts',
      'Limited free time',
      'Location: Wolvercote'
    ];
    setProblems(exampleProblems);

    const exampleSolutions = [
      'Book courts at Alexandra Park (7pm, Court 1, £8)',
      'Consider joining a local tennis club',
      'Look for evening and weekend sessions',
      'Check public transport options to Alexandra Park'
    ];
    setSolutions(exampleSolutions);
    setIsProcessing(false);
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-8 text-center">
          Problem Solver
        </h1>

        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="flex gap-4 mb-4">
            <textarea
              className="flex-1 p-4 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Describe your situation..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={4}
            />
            <button
              onClick={startRecording}
              className={`p-4 rounded-lg ${
                isRecording
                  ? 'bg-red-500 hover:bg-red-600'
                  : 'bg-blue-500 hover:bg-blue-600'
              } text-white`}
            >
              {isRecording ? (
                <StopIcon className="h-6 w-6" />
              ) : (
                <MicrophoneIcon className="h-6 w-6" />
              )}
            </button>
          </div>
          <button
            onClick={() => processInput(input)}
            disabled={!input || isProcessing}
            className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-300"
          >
            {isProcessing ? 'Processing...' : 'Get Solutions'}
          </button>
        </div>

        {problems.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                Identified Problems
              </h2>
              <ul className="space-y-2">
                {problems.map((problem, index) => (
                  <li
                    key={index}
                    className="p-3 bg-gray-50 rounded-lg text-gray-700"
                  >
                    {problem}
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                Suggested Solutions
              </h2>
              <ul className="space-y-2">
                {solutions.map((solution, index) => (
                  <li
                    key={index}
                    className="p-3 bg-blue-50 rounded-lg text-gray-700"
                  >
                    {solution}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </main>
  );
} 