from pathlib import Path

content = r'''# 🎓 Class Quality Assessor

An AI-assisted prototype that analyzes recorded online classes and produces an evidence-based quality assessment. It transcribes speech, calculates basic audio indicators, and uses a language model to score selected teaching-quality dimensions.

> **Important:** This is a prototype, not a definitive measure of teaching effectiveness. Review the evidence and limitations before using any assessment for decisions about teachers or students.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Assessment Dimensions](#assessment-dimensions)
- [How It Works](#how-it-works)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation and Local Setup](#installation-and-local-setup)
- [Run the Application](#run-the-application)
- [Configuration](#configuration)
- [Deploying to Streamlit Community Cloud](#deploying-to-streamlit-community-cloud)
- [Output and Reports](#output-and-reports)
- [Troubleshooting](#troubleshooting)
- [Privacy and Responsible Use](#privacy-and-responsible-use)
- [Current Limitations](#current-limitations)
- [Future Improvements](#future-improvements)
- [License](#license)

## Overview

Class Quality Assessor helps reviewers examine a recorded online class using speech transcription, basic audio measurements, and an AI-generated assessment.

Upload a supported recording to receive:
- An overall weighted score out of 5 and a quality category.
- Scores and explanations for individual assessment dimensions.
- Evidence notes, strengths, and suggested improvements.
- A transcript and basic audio indicators.
- A downloadable JSON assessment report.

The application is built with Streamlit. Speech transcription uses `faster-whisper`; assessment can use a local Ollama model or a compatible hosted language-model API.

## Features

- **Audio extraction:** Uses FFmpeg to extract audio from supported recordings.
- **Speech transcription:** Transcribes speech locally using `faster-whisper`.
- **Audio indicators:** Calculates basic measurements such as RMS loudness, peak amplitude, and clipped-sample fraction when supported by the audio format.
- **AI-assisted assessment:** Requests structured JSON output from the configured language model.
- **Evidence-aware scoring:** Instructs the model not to invent student responses, visual details, or timestamps.
- **Results dashboard:** Displays the overall score, category, dimension scores, explanations, strengths, improvements, evidence, and limitations.
- **Transcript viewer:** Lets the reviewer inspect the generated transcript.
- **JSON export:** Downloads the assessment, transcript, and audio indicators as a JSON file.
- **Flexible model backend:** Supports local Ollama or a hosted OpenAI-compatible API when configured.

## Assessment Dimensions

The rubric currently uses five dimensions:

| Dimension | Weight | What it considers |
|---|---:|---|
| Teaching clarity | 30% | Evidence of clear explanations in the transcript |
| Lesson structure | 25% | Evidence of sequencing, transitions, and organization |
| Student engagement evidence | 20% | Evidence of interaction in the available text; actual attention cannot be established from a transcript alone |
| Audio quality | 15% | Basic audio indicators; measurements alone cannot fully determine perceived quality |
| Visual presentation evidence | 10% | Visual quality cannot be verified by the current transcript-and-audio pipeline |

### Quality Categories

The overall weighted score is mapped to a category by `rubric.py`:

| Weighted score | Category |
|---:|---|
| Below 2.00 | Weak |
| 2.00 to below 3.00 | Average |
| 3.00 to below 4.00 | Good |
| 4.00 to 5.00 | Excellent |

The score is a model-generated estimate, not a validated educational measurement. Missing scores are excluded and the remaining weights are renormalized.

## How It Works

1. **Upload:** The reviewer selects an audio or video recording in the Streamlit interface.
2. **Extract audio:** FFmpeg converts the recording's audio to mono, 16 kHz PCM WAV.
3. **Measure audio:** The application calculates basic signal indicators.
4. **Transcribe:** `faster-whisper` generates timestamped transcript segments.
5. **Assess:** The evaluator sends the transcript and audio indicators to the configured language model.
6. **Validate:** The application parses and normalizes the model's JSON response and calculates a weighted score.
7. **Review and export:** Results are displayed in the interface and can be downloaded as JSON.

## Technology Stack

- **Python** — application logic
- **Streamlit** — web interface
- **faster-whisper** — speech-to-text transcription
- **FFmpeg / ffprobe** — audio extraction and media duration
- **NumPy** — numerical audio measurements
- **Requests** — hosted API and Ollama HTTP requests
- **Ollama** — optional local language-model runtime
- **OpenAI-compatible API** — optional hosted language-model backend

## Project Structure

Keep the Python modules and `requirements.txt` in the same project directory.

```text
humaniti-class-quality-assessor/
├── app.py              # Streamlit user interface
├── evaluator.py        # LLM requests, JSON parsing, and score normalization
├── processor.py        # Audio extraction, transcription, and audio indicators
├── rubric.py           # Assessment dimensions, weights, and score categories
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
└── .streamlit/
    └── secrets.toml    # Optional local secrets; do not commit this file
```

If your repository has a different name or additional files, keep the structure section aligned with the actual repository.

## Requirements

- Python 3.10 or a Python version supported by the installed dependencies.
- FFmpeg, including `ffprobe`, installed and available on `PATH`.
- Internet access to install Python dependencies and download the Whisper model on first use.
- **For local AI assessment:** Ollama installed and running, with a compatible model downloaded.
- **For hosted AI assessment:** Credentials and a compatible model name for an OpenAI-compatible API provider.
- A short test recording is recommended for the first run. Model size, media duration, and available memory affect processing time.

## Installation and Local Setup

### 1. Download the project

Clone your repository or download and extract its ZIP file.

```bash
git clone <YOUR_REPOSITORY_URL>
cd humaniti-class-quality-assessor
```

Replace `<YOUR_REPOSITORY_URL>` with your repository URL.

### 2. Create a virtual environment

**Windows (Command Prompt):**

```bat
py -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install FFmpeg

Install FFmpeg using the instructions for your operating system from the official FFmpeg website:

https://ffmpeg.org/download.html

Ensure both `ffmpeg` and `ffprobe` are available on your system `PATH`. Open a new terminal after updating `PATH`, then verify:

```bash
ffmpeg -version
ffprobe -version
```

If either command is not recognized, correct the installation or `PATH` configuration before running the app.

### 5. Set up the language model

Choose **one** of the following approaches.

#### Option A: Local Ollama (recommended for local processing)

Install Ollama from:

https://ollama.com/download

Start Ollama, then download the model used by the app's default configuration:

```bash
ollama pull qwen2.5:3b
```

Confirm the model is available:

```bash
ollama list
```

The Ollama service normally listens at `http://localhost:11434`. The application uses this local endpoint when hosted API credentials are not configured.

In the app, enter `qwen2.5:3b` as the model name, or select another model that is installed and compatible with the prompts and output requirements.

#### Option B: Hosted OpenAI-compatible API

If you use a compatible hosted provider, configure the API base URL, API key, and model name as described in [Configuration](#configuration). The selected provider must support the chat-completions format used by this application. JSON response-format support is also expected.

**Important:** With a hosted model, the transcript and audio measurements are sent to the provider for assessment. This is not local-only processing.

## Run the Application

From the project directory, with the virtual environment activated, run:

```bash
streamlit run app.py
```

Streamlit will display a local URL, usually:

```text
http://localhost:8501
```

Open that address in your browser.

1. Upload a supported recording.
2. Select a transcription model. Use `tiny` first on a lower-memory computer.
3. Enter the language-model name.
4. Select **Analyze class**.
5. Review the results, transcript, evidence, and limitations.
6. Use the download button to save the JSON report.

The first transcription run may take longer because the Whisper model may need to be downloaded.

## Configuration

### Local Ollama

By default, the app uses `qwen2.5:3b` as the model name. Make sure the model has been downloaded with Ollama before selecting it.

The app sends requests to:

```text
http://localhost:11434/api/chat
```

When `LLM_API_KEY` and `LLM_BASE_URL` are both configured, the evaluator uses the hosted API instead of local Ollama.

### Hosted API Secrets

For local development, you can create `.streamlit/secrets.toml`:

```toml
LLM_BASE_URL = "https://YOUR_PROVIDER_API_BASE_URL/v1"
LLM_API_KEY = "YOUR_API_KEY"
LLM_MODEL = "YOUR_PROVIDER_MODEL_NAME"
```

Replace the example values with the actual values from your provider. The base URL should be the provider's API base URL, generally including `/v1` when required by that provider. The evaluator appends `/chat/completions` to the configured base URL.

The Streamlit interface reads `LLM_MODEL` as its default model name. If your provider requires a different endpoint or request format, the code may need adapting.

**Security:** Never commit API keys, passwords, or populated secrets files to a public repository. Add the following to `.gitignore`:

```gitignore
.streamlit/secrets.toml
.venv/
__pycache__/
*.py[cod]
```

If a key is accidentally exposed, revoke or rotate it through your provider.

### Environment Variables

The evaluator can also read `LLM_BASE_URL` and `LLM_API_KEY` from environment variables. It reads `LLM_MODEL` from Streamlit secrets for the interface's default value; set the model in the interface if it is not configured there.

## Deploying to Streamlit Community Cloud

The current application supports hosted-model configuration, but it also depends on native media-processing and transcription components. Deployment may require additional setup and may be limited by available memory, CPU, installation time, upload limits, and the platform's ability to install FFmpeg.

1. Push the application code and `requirements.txt` to your Git repository.
2. Open [Streamlit Community Cloud](https://streamlit.io/cloud) and create an app from the repository.
3. Select `app.py` as the application entry point.
4. Open the app's **Settings / Secrets** area and add your hosted API settings:

   ```toml
   LLM_BASE_URL = "https://YOUR_PROVIDER_API_BASE_URL/v1"
   LLM_API_KEY = "YOUR_API_KEY"
   LLM_MODEL = "YOUR_PROVIDER_MODEL_NAME"
   ```

5. Deploy and check the application logs if installation or startup fails.
6. Test with a short, non-sensitive sample recording before attempting larger files.

### Important Cloud Deployment Notes

- `localhost` in a cloud app refers to the cloud container, not your personal computer. A cloud deployment cannot access Ollama running only on your laptop.
- Use a hosted API that you are authorized to use, or configure a reachable model service in a secure manner.
- The current `requirements.txt` does not install FFmpeg itself. The deployment environment must provide FFmpeg and `ffprobe`; otherwise, add an appropriate deployment setup for them.
- Do not upload children's recordings or confidential classroom material to a public app unless you have the necessary authorization, consent, and privacy safeguards.
- For local-only processing, run the app on a trusted computer with local Ollama rather than sending transcripts to a hosted API.

## Output and Reports

The interface displays:

- Overall quality category and weighted score.
- Recording duration.
- Scores, explanations, and evidence status for each dimension.
- Strengths and suggested improvements.
- Evidence notes and limitations.
- The generated transcript and audio indicators.

The **Download assessment report (JSON)** button exports a JSON object containing the original filename, recording duration, category, evaluator output, audio indicators, and transcript.

Treat exported reports and transcripts as potentially sensitive files. Store and share them only with authorized people.

## Troubleshooting

### `ModuleNotFoundError`

Activate the correct virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

Confirm that Streamlit is running from the same Python environment in which the dependencies were installed.

### `FFmpeg was not found`

Install FFmpeg and make sure both `ffmpeg` and `ffprobe` are on `PATH`. Restart the terminal or app after updating `PATH`.

### Ollama cannot be reached

1. Confirm Ollama is installed and running.
2. Run `ollama list` and confirm the model name.
3. If needed, download the model:

   ```bash
   ollama pull qwen2.5:3b
   ```

4. Make sure the model name entered in the app matches the downloaded model.
5. If deploying to the cloud, remember that cloud `localhost` is not your own computer.

### Hosted API returns HTTP 401 or 403

Check that the API key is correct, active, and authorized for the selected model. Store the key in Streamlit secrets or environment variables, not in source code.

### Hosted API returns HTTP 404 or model not found

Verify the provider's API base URL, model identifier, and supported endpoint. The current evaluator appends `/chat/completions` to `LLM_BASE_URL`.

### Invalid or incomplete JSON from the model

The application expects a JSON object with the required dimension names and fields. Try a model that follows structured-output instructions reliably, check the model identifier, and inspect the error shown by the app. Some providers or models may not support the requested JSON response format.

### Transcription is slow or memory usage is high

- Start with a short recording.
- Select the `tiny` Whisper model.
- Close other memory-intensive applications.
- Use shorter clips for initial tests.
- Remember that larger models and longer recordings require more processing resources.

### No speech was transcribed

Check that the recording contains audible speech and that FFmpeg can read the file. Try another supported format, such as WAV or MP4, and test a short sample.

## Privacy and Responsible Use

- Local Ollama mode can keep language-model assessment on the same computer, and `faster-whisper` runs locally. The application may still download models or dependencies during setup.
- Hosted API mode sends the transcript and audio measurements to the configured provider.
- The app writes a temporary copy of the uploaded recording while processing. Temporary-directory cleanup is requested when processing finishes, but this alone is not a complete data-governance guarantee.
- Use appropriate consent, access controls, retention policies, and institutional approval before processing classroom recordings, especially recordings involving children.
- Do not treat AI-generated scores as the sole basis for employment, grading, disciplinary action, or other high-impact decisions.
- Review the original recording and generated evidence before drawing conclusions.

## Current Limitations

- The current pipeline analyzes extracted audio and a transcript; it does **not** analyze the classroom video frames.
- It cannot reliably determine student attention, emotions, participation, or visual presentation quality from a transcript alone.
- RMS loudness and peak measurements are technical indicators, not a complete assessment of audio intelligibility or quality.
- Transcription errors can affect the language-model assessment.
- The model may produce incorrect or inconsistent scores despite JSON validation.
- The weighted score and category thresholds are prototype rules and have not been established as a validated educational assessment instrument.
- The application does not currently provide a full multi-user authentication, authorization, or audit-log system.

## Future Improvements

Potential next steps include:

- Add tests for rubric calculations and JSON-response validation.
- Add clearer confidence reporting and stronger validation for evidence and timestamps.
- Support optional video-frame analysis for visual-presentation evidence, with appropriate privacy controls.
- Improve error logging and cloud deployment documentation.
- Add configurable file-size and recording-duration limits.
- Evaluate the rubric against expert-reviewed sample recordings before using it operationally.

## License

No license is specified in this repository yet. Add a `LICENSE` file before distributing or reusing the project, and ensure that all dependencies and model assets are used in accordance with their respective licenses.
'''
path = Path("/mnt/data/README.md")
path.write_text(content, encoding="utf-8")
print(f"Created: {path}")
