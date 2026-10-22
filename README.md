# Humaniti AI — Class Quality Assessor

A local-first prototype for assessing online class recordings. It uses local speech-to-text with faster-whisper and a local language model served by Ollama. Streamlit provides the interface.

## Features

- Upload common audio/video formats.
- Extract audio locally using FFmpeg.
- Transcribe speech locally using Whisper.
- Ask a local Ollama LLM to evaluate evidence against a fixed rubric.
- Show Poor, Average, Good, or Excellent based on a weighted score.
- Show dimension scores, strengths, improvements, evidence, limitations, and a downloadable JSON report.
- No external AI API key is required.

## Important limitations

- This prototype does not fully analyze classroom video or visual presentation.
- A transcript cannot establish that students were attentive or engaged.
- Audio signal metrics are basic technical indicators, not a definitive quality judgment.
- The rubric and thresholds are an initial design and should be refined after reviewing the organiser's sample recordings.
- Do not publish class recordings, transcripts, or reports containing sensitive data.
- The app is intended for local testing. Do not expose it publicly with sensitive recordings.

## Requirements

- Windows 10/11
- Python 3.11 or 3.12 recommended
- FFmpeg and ffprobe available on PATH
- Ollama installed and running
- Internet is needed initially to download packages and models; processing is local after setup.
- 8 GB RAM: start with Whisper `tiny` and a small Ollama model. Performance will depend on recording length and laptop hardware.

## Setup on Windows

### 1. Install Python

Install Python 3.11 or 3.12 from https://www.python.org/downloads/windows/. During setup, enable **Add Python to PATH**.

### 2. Install FFmpeg

Install FFmpeg from a trusted Windows build/distribution and add its `bin` folder to PATH. Confirm both commands work in a new Command Prompt:

```bat
ffmpeg -version
ffprobe -version
```

### 3. Install Ollama

Install from https://ollama.com/download/windows. Open Command Prompt and download a small model:

```bat
ollama pull qwen2.5:1.5b
```

Check it is available:

```bat
ollama list
```

Ollama normally runs as a background service. The app connects to `http://localhost:11434`.

### 4. Create a virtual environment

Open Command Prompt in this project folder:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `py -3.11` is not available, use the Python version you installed:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run the app

```bat
streamlit run app.py
```

A browser tab should open. Upload a short recording and click **Analyze class**. The first transcription run may download Whisper model files, so the computer needs internet access for that initial download.

## Recommended first test

1. Start with a short sample recording (1–3 minutes).
2. Select Whisper `tiny`.
3. Keep the Ollama model as `qwen2.5:3b`.
4. Verify the transcript against the recording.
5. Review the dimension scores and the evidence. Do not assume the model's judgement is ground truth.
6. Try another sample with different teaching quality and compare the reports.

## Troubleshooting

- **`ffmpeg` not found:** install FFmpeg, add its `bin` directory to PATH, and reopen Command Prompt.
- **Ollama connection error:** open Ollama, then run `ollama list`. If needed, run `ollama pull qwen2.5:3b`.
- **Out of memory / slow processing:** use Whisper `tiny`, close other applications, and test shorter recordings.
- **No transcript:** check that the file contains audible speech and try another supported format.
- **Model output invalid:** click Analyze again. If it persists, try another compatible Ollama model and inspect the error.

## Project files

- `app.py`: Streamlit interface
- `processor.py`: local audio extraction, transcription and basic audio indicators
- `evaluator.py`: local LLM call, output validation and scoring
- `rubric.py`: scoring dimensions, weights and quality thresholds

## Data handling

The app writes temporary processing files to a temporary directory and removes them when the run ends. Reports are only downloaded when the user chooses to do so. Confirm the organiser's rules before using any supplied recording. Never commit recordings, transcripts, reports, API keys, or other sensitive information to GitHub.
