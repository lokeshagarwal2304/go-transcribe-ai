# 🎙️ Hinglish & Multi-Dialect Audio Transcription System

An end-to-end Speech-to-Text system engineered for **Hindi, English, and Hinglish** audio with high-accuracy Indian colloquial slang identification and code-switching support.

---

## 🌟 Key Features

1. **Multi-Dialect & Code-Mixed Support**:
   - Accurately captures code-mixed spoken audio (Hindi + English).
   - Supports 3 output modes:
     - **Hinglish Mode**: Natural Roman script transcription with preserved Indian slang nuances.
     - **Hindi Mode**: Standard Devanagari script output.
     - **English Mode**: Indian English audio transcription.

2. **Indian Slang Lexicon & Context Normalizer**:
   - Automatically detects and highlights colloquial terms (e.g., `jugaad`, `scene sorted`, `bhai`, `faadu`, `chill maar`, `jhakaas`, `bawaal`, `locha`, `panga`, `bhasad`, `chai-pani`, etc.).
   - Normalizes phonetic variations to clean standard transcriptions.

3. **Fast & Resource-Efficient Engine**:
   - Built on `Faster-Whisper` (CTranslate2 transformer acceleration).
   - Up to 4x faster execution with `int8` quantization on CPU / GPU.
   - Built-in PyAV decoders for multi-format support (`.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`).

4. **Multiple Interfaces**:
   - **Modern Web Dashboard**: Zero NPM requirements, pure Python + Vanilla modern UI.
   - **Command Line CLI Tool**: One-liner transcription of any audio file.
   - **Export Formats**: One-click export to `.txt`, `.srt` (Subtitles with timestamps), and `.json`.

---

## 🚀 How to Run & Use

### Method 1: Launch Local Web Dashboard

1. Open PowerShell / Command Prompt and navigate to the project directory:
   ```powershell
   cd "C:\Users\Lokesh Agarwal\.gemini\antigravity\scratch\hinglish_transcriber"
   ```

2. Start the server:
   ```powershell
   python app.py
   ```

3. Open your browser and go to:
   ```
   http://127.0.0.1:8000
   ```

4. Drag & drop any audio file (`.mp3`, `.wav`, `.m4a`, etc.), select your preferred mode (Hinglish/Hindi/English), and click **"Start Transcription"**!

---

### Method 2: Use Instant Command-Line CLI

Transcribe any audio file directly from terminal:

```powershell
# Basic Hinglish transcription
python cli.py "path/to/your/audio.mp3"

# Hindi Devanagari output with subtitles export (.srt)
python cli.py "path/to/your/audio.wav" --mode hindi --export-srt subtitles.srt

# High-accuracy model with full JSON report
python cli.py "path/to/your/audio.m4a" --model small --export-json output.json
```

---

## 📁 Project Architecture

```
hinglish_transcriber/
├── app.py                  # FastAPI server & API endpoints
├── transcriber.py          # Faster-Whisper inference engine & timestamp parser
├── slang_lexicon.py        # Indian slang dictionary & contextual normalizer
├── cli.py                  # Direct terminal transcription command
├── requirements.txt        # Python dependency list
├── static/
│   ├── index.html          # Web dashboard interface (pure HTML)
│   ├── style.css           # Glassmorphism dark UI styling
│   └── app.js             # Client audio handling & timeline visualizer
└── README.md               # Documentation & usage guide
```
