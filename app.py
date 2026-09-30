"""
FastAPI Server for Professional Audio Transcription with Word (.docx) Export.
Includes Zero-Mistake GoTranscript Test Engine, Speaker Diarization, and Pure Hindi Devanagari.
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import shutil
import tempfile
from typing import Optional, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from transcriber import HinglishTranscriber
from slang_lexicon import SlangNormalizer, HINGLISH_SLANG_MAPPINGS, DEVANAGARI_SLANG_MAPPINGS
from formatter import TranscriptionFormatter

app = FastAPI(
    title="Professional Audio Transcriber & Formatter",
    description="High-Accuracy Speech-to-Text system with GoTranscript rules and Word (.docx) export."
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

print("=================================================================")
print("🚀 Initializing High-Accuracy Transcription Engine into RAM...")
DEFAULT_ENGINE = HinglishTranscriber(model_size="small")
print("✅ High-Accuracy Model Pre-loaded and Ready for Instant Inference!")
print("=================================================================")

transcribers_cache = {"small": DEFAULT_ENGINE}
normalizer = SlangNormalizer()

def get_transcriber(model_size: str = "small") -> HinglishTranscriber:
    if model_size not in transcribers_cache:
        print(f"[INFO] Loading {model_size} model into memory...")
        transcribers_cache[model_size] = HinglishTranscriber(model_size=model_size)
    return transcribers_cache[model_size]


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Professional Transcriber Backend Active</h1>"


@app.get("/api/slangs")
async def get_slang_lexicon():
    return {
        "count": len(HINGLISH_SLANG_MAPPINGS),
        "roman_slangs": HINGLISH_SLANG_MAPPINGS,
        "devanagari_slangs": DEVANAGARI_SLANG_MAPPINGS
    }


@app.post("/api/transcribe")
async def transcribe_audio_endpoint(
    audio: UploadFile = File(...),
    language_mode: str = Form("auto"),
    model_size: str = Form("small"),
    timestamp_rule: str = Form("every_2_min"),
    speaker_mode: str = Form("auto"),
    speaker1_name: str = Form(""),
    speaker2_name: str = Form(""),
    gotranscript_mode: str = Form("true")
):
    """
    Transcribes audio with high-accuracy, applies GoTranscript rules, and formats output.
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file selected.")
        
    temp_file_path = None
    try:
        file_ext = os.path.splitext(audio.filename)[1].lower() or ".wav"
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, dir=UPLOADS_DIR) as temp_file:
            shutil.copyfileobj(audio.file, temp_file)
            temp_file_path = temp_file.name

        print(f"[TRANSCRIPTION START] File: {audio.filename}, Mode: {language_mode}, Model: {model_size}")
        engine = get_transcriber(model_size=model_size)
        raw_result = engine.transcribe_audio(
            audio_path=temp_file_path,
            language_mode=language_mode
        )
        print(f"[TRANSCRIPTION DONE] Duration: {raw_result['processing_time_seconds']}s")
        
        speaker_override = {}
        if speaker1_name.strip():
            speaker_override["Speaker 1"] = speaker1_name.strip()
        if speaker2_name.strip():
            speaker_override["Speaker 2"] = speaker2_name.strip()
        
        is_gt = (gotranscript_mode.lower() == "true")
        formatted_data = TranscriptionFormatter.generate_formatted_transcript(
            raw_result,
            timestamp_rule=timestamp_rule,
            speaker_mode=speaker_mode,
            speaker_names_override=speaker_override,
            is_gotranscript_test=is_gt
        )

        raw_result["formatted"] = formatted_data
        raw_result["original_filename"] = audio.filename
        raw_result["timestamp_rule"] = timestamp_rule
        raw_result["speaker_mode"] = speaker_mode
        raw_result["speaker_override"] = speaker_override

        return JSONResponse(content=raw_result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass


@app.post("/api/export/{export_format}")
async def export_transcript(export_format: str, data: dict = Body(...)):
    """
    Exports transcription data to DOCX (Word), TXT, SRT, or JSON.
    """
    try:
        format_type = export_format.lower()
        base_name = os.path.splitext(data.get("original_filename", "transcription"))[0]
        temp_out = os.path.join(UPLOADS_DIR, f"{base_name}_export.{format_type}")
        
        if format_type == "docx":
            formatted_data = data.get("formatted", {})
            title = f"Transcript - {data.get('original_filename', 'Audio')}"
            TranscriptionFormatter.export_to_docx(formatted_data, temp_out, title=title)
            return FileResponse(
                temp_out, 
                filename=f"{base_name}_transcript.docx", 
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        elif format_type == "txt":
            formatted_text = data.get("formatted", {}).get("formatted_text") or data.get("normalized_transcript", "")
            with open(temp_out, "w", encoding="utf-8") as f:
                f.write(formatted_text)
            return FileResponse(temp_out, filename=f"{base_name}.txt", media_type="text/plain")

        elif format_type == "srt":
            engine = get_transcriber("small")
            engine.export_to_srt(data, temp_out)
            return FileResponse(temp_out, filename=f"{base_name}.srt", media_type="text/plain")

        elif format_type == "json":
            with open(temp_out, "w", encoding="utf-8") as f:
                import json
                json.dump(data, f, indent=2, ensure_ascii=False)
            return FileResponse(temp_out, filename=f"{base_name}.json", media_type="application/json")

        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'docx', 'txt', 'srt', or 'json'.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("\nStarting Professional Transcriber on http://127.0.0.1:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
