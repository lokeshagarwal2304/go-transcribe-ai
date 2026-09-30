import os
import sys

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import soundfile as sf
from transcriber import HinglishTranscriber

audio_path = r"C:\Users\Lokesh Agarwal\Downloads\transcribing_1.mp3"

if not os.path.exists(audio_path):
    print("Audio file not found!")
    sys.exit(1)

print(f"File Size: {os.path.getsize(audio_path) / (1024*1024):.2f} MB")

engine = HinglishTranscriber(model_size="small")

print("\n--- Running Hindi Transcription with details ---")
result_hi = engine.transcribe_audio(audio_path, language_mode="hindi")

print(f"Total Segments: {len(result_hi['segments'])}")
print(f"Duration Processed: {result_hi['processing_time_seconds']}s")

# Save output to text file so no encoding issue happens
out_txt_hi = r"C:\Users\Lokesh Agarwal\.gemini\antigravity\scratch\hinglish_transcriber\transcription_hindi.txt"
with open(out_txt_hi, "w", encoding="utf-8") as f:
    f.write("=== FULL TRANSCRIPT (HINDI) ===\n\n")
    f.write(result_hi["normalized_transcript"] + "\n\n")
    f.write("=== SEGMENTS WITH TIMESTAMPS ===\n\n")
    for seg in result_hi["segments"]:
        f.write(f"[{seg['start']}s -> {seg['end']}s] {seg['normalized_text']}\n")

print(f"Saved Hindi transcript to: {out_txt_hi}")

# Also test English translation mode
print("\n--- Running English Mode ---")
result_en = engine.transcribe_audio(audio_path, language_mode="english")
out_txt_en = r"C:\Users\Lokesh Agarwal\.gemini\antigravity\scratch\hinglish_transcriber\transcription_english.txt"
with open(out_txt_en, "w", encoding="utf-8") as f:
    f.write("=== FULL TRANSCRIPT (ENGLISH) ===\n\n")
    f.write(result_en["normalized_transcript"] + "\n\n")
    f.write("=== SEGMENTS WITH TIMESTAMPS ===\n\n")
    for seg in result_en["segments"]:
        f.write(f"[{seg['start']}s -> {seg['end']}s] {seg['normalized_text']}\n")

print(f"Saved English transcript to: {out_txt_en}")
