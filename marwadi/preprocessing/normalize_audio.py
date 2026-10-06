#!/usr/bin/env python3
"""Normalize and standardize collected audio files for ASR fine-tuning.

This script converts any audio files into a single WAV format, resamples them to
16kHz, trims silence, and saves metadata useful for later training.
"""

import argparse
import csv
import os
from pathlib import Path

import librosa
import soundfile as sf


def normalize_audio(input_path: str, output_path: str, target_sr: int = 16000):
    audio, sr = librosa.load(input_path, sr=None, mono=False)

    if audio.ndim > 1:
        audio = librosa.to_mono(audio)

    audio = librosa.util.normalize(audio)
    audio, _ = librosa.effects.trim(audio, top_db=25)
    audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)

    sf.write(output_path, audio, target_sr)
    return output_path


def build_manifest(input_dir: str, output_csv: str):
    rows = []
    for file in sorted(Path(input_dir).rglob("*")):
        if file.suffix.lower() not in {".wav", ".mp3", ".m4a", ".ogg", ".flac"}:
            continue

        audio, sr = librosa.load(str(file), sr=None, mono=False)
        duration = librosa.get_duration(y=audio, sr=sr)
        rows.append({
            "audio_path": str(file),
            "duration": round(float(duration), 2),
            "source": file.parent.name,
            "language": "marwadi",
        })

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["audio_path", "duration", "source", "language"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[INFO] Wrote manifest with {len(rows)} entries to {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize audio for Marwadi ASR dataset")
    parser.add_argument("--input-dir", type=str, required=True, help="Directory with raw audio files")
    parser.add_argument("--output-dir", type=str, default="data/processed_audio", help="Directory for normalized audio outputs")
    parser.add_argument("--manifest", type=str, default="data/manifest.csv", help="Path to save CSV dataset manifest")
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    processed = []
    for src in sorted(in_dir.rglob("*")):
        if src.is_dir():
            continue
        if src.suffix.lower() not in {".wav", ".mp3", ".m4a", ".ogg", ".flac"}:
            continue
        target = out_dir / (src.stem + ".wav")
        normalize_audio(str(src), str(target))
        processed.append(target)

    print(f"[INFO] Normalized {len(processed)} audio files into {out_dir}")
    build_manifest(str(out_dir), args.manifest)
