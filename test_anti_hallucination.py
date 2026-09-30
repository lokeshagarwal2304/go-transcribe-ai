import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from faster_whisper import WhisperModel

audio_path = r"C:\Users\Lokesh Agarwal\Downloads\transcribing_1.mp3"
model = WhisperModel("small", device="cpu", compute_type="int8")

print("--- Running with Anti-Hallucination Settings ---")
segments, info = model.transcribe(
    audio_path,
    beam_size=5,
    best_of=5,
    temperature=0.0,
    condition_on_previous_text=False, # Crucial: stops repetition loops!
    vad_filter=True,                  # Filters out background noise/silence
    vad_parameters=dict(min_silence_duration_ms=1000, speech_pad_ms=400),
    hallucination_silence_threshold=2.0,
    task="transcribe"                 # Keep original language
)

print(f"Detected Language: {info.language} (Probability: {info.language_probability:.2f})")
print(f"Audio Duration: {info.duration:.2f} seconds\n")

all_lines = []
for seg in segments:
    line = f"[{seg.start:.2f}s -> {seg.end:.2f}s] {seg.text.strip()}"
    print(line)
    all_lines.append(line)

out_file = r"C:\Users\Lokesh Agarwal\.gemini\antigravity\scratch\hinglish_transcriber\fixed_transcript.txt"
with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(all_lines))

print(f"\nTotal Segments: {len(all_lines)}")
print(f"Saved to: {out_file}")
