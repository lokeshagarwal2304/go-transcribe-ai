"""
Core Speech-to-Text Transcription Engine with Native Hindi Devanagari, English & Hinglish Support.
Equipped with Anti-Hallucination, Zero-Skipping VAD, and Slang Normalization.
"""

import os
import sys
import json
import time
from typing import Dict, Any, List, Optional
from slang_lexicon import SlangNormalizer

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

class HinglishTranscriber:
    def __init__(self, model_size: str = "small", device: str = "auto", compute_type: str = "int8"):
        """
        Initializes the speech-to-text model engine.
        model_size: 'small' (recommended for high Devanagari Hindi and English accuracy)
        """
        self.model_size = model_size
        self.device = "cpu" if device == "auto" else device
        self.compute_type = compute_type
        self.normalizer = SlangNormalizer()
        self.model = None
        self._load_engine()

    def _load_engine(self):
        """Loads Faster-Whisper model or standard Whisper fallback."""
        try:
            from faster_whisper import WhisperModel
            print(f"[INFO] Loading Faster-Whisper model ({self.model_size}) on {self.device}...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=6
            )
            print("[INFO] Model loaded successfully.")
        except Exception as e:
            print(f"[WARNING] Faster-Whisper load note: {e}")
            try:
                import whisper
                print(f"[INFO] Falling back to standard Whisper ({self.model_size})...")
                self.model = whisper.load_model(self.model_size)
            except Exception as e2:
                print(f"[ERROR] Could not load whisper engine: {e2}")
                self.model = None

    def transcribe_audio(
        self, 
        audio_path: str, 
        language_mode: str = "hindi", 
        beam_size: int = 5,
        word_timestamps: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribes the given audio file into pure Devanagari Hindi, English, or Hinglish.
        
        language_mode:
          - 'hindi': Pure Hindi transcription in authentic Devanagari script (देवनागरी लिपि)
          - 'auto': Automatically detects language (Hindi, English, etc.)
          - 'english': English transcription
          - 'hinglish': Roman script code-mixed Hindi-English
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found at: {audio_path}")

        start_time = time.time()
        
        # Set language code and targeted initial prompt
        lang_code = None
        if language_mode == "hindi":
            lang_code = "hi"
            initial_prompt = "यह एक स्पष्ट और सटीक हिंदी वार्तालाप है जिसमें सभी शब्द और वाक्य शुद्ध देवनागरी लिपि में बिना किसी गलती के लिखे गए हैं।"
        elif language_mode == "english":
            lang_code = "en"
            initial_prompt = "This is a clear English transcription without skipping any words, sentences, or slang phrases."
        elif language_mode == "hinglish":
            lang_code = None
            initial_prompt = "Yeh Hindi aur English mixed dialogue hai jisme normal bolchal ke shabda shamil hain."
        else:
            # Auto mode
            lang_code = None
            initial_prompt = None

        segments_data = []
        full_text_list = []
        detected_language = "unknown"
        language_probability = 0.0

        if self.model is not None:
            try:
                # Anti-Hallucination and Complete Audio Coverage Settings
                segments, info = self.model.transcribe(
                    audio_path,
                    language=lang_code,
                    initial_prompt=initial_prompt,
                    beam_size=beam_size,
                    best_of=5,
                    temperature=0.0,
                    condition_on_previous_text=False,  # Prevents repetition loops & skipped sections
                    vad_filter=True,                   # Accurately filters real silence
                    vad_parameters=dict(min_silence_duration_ms=1000, speech_pad_ms=400),
                    hallucination_silence_threshold=2.0,
                    word_timestamps=word_timestamps
                )
                
                detected_language = info.language
                language_probability = round(info.language_probability, 4)

                for seg in segments:
                    raw_seg_text = seg.text.strip()
                    if not raw_seg_text:
                        continue

                    # For Hindi mode or auto-detected Hindi, maintain pure Devanagari text
                    if language_mode == "hindi" or detected_language == "hi":
                        norm_seg_text = raw_seg_text
                    else:
                        norm_seg_text = self.normalizer.normalize_text(raw_seg_text, mode="hinglish")

                    words_list = []
                    if hasattr(seg, 'words') and seg.words:
                        for w in seg.words:
                            words_list.append({
                                "word": w.word.strip(),
                                "start": round(w.start, 2),
                                "end": round(w.end, 2),
                                "probability": round(w.probability, 3)
                            })

                    segments_data.append({
                        "id": seg.id,
                        "start": round(seg.start, 2),
                        "end": round(seg.end, 2),
                        "start_formatted": self.format_time_simple(seg.start),
                        "end_formatted": self.format_time_simple(seg.end),
                        "raw_text": raw_seg_text,
                        "normalized_text": norm_seg_text,
                        "words": words_list
                    })
                    full_text_list.append(norm_seg_text)

            except Exception as e:
                print(f"[ERROR] Inference error: {e}")
                raise e
        else:
            raise RuntimeError("Transcription model is not initialized properly.")

        full_transcript = " ".join(full_text_list)
        duration = round(time.time() - start_time, 2)

        return {
            "status": "success",
            "audio_file": os.path.basename(audio_path),
            "language_mode": language_mode,
            "detected_language": detected_language,
            "language_confidence": language_probability,
            "processing_time_seconds": duration,
            "normalized_transcript": full_transcript,
            "total_segments": len(segments_data),
            "segments": segments_data
        }

    @staticmethod
    def format_time_simple(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    @staticmethod
    def format_srt_time(seconds: float) -> str:
        millis = int(round((seconds - int(seconds)) * 1000))
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    def export_to_srt(self, result: Dict[str, Any], output_path: str) -> str:
        srt_lines = []
        for i, seg in enumerate(result.get("segments", []), 1):
            start_str = self.format_srt_time(seg["start"])
            end_str = self.format_srt_time(seg["end"])
            text = seg["normalized_text"]
            srt_lines.append(f"{i}\n{start_str} --> {end_str}\n{text}\n")
        
        content = "\n".join(srt_lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def export_to_json(self, result: Dict[str, Any], output_path: str) -> str:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        return output_path

    def export_to_txt(self, result: Dict[str, Any], output_path: str) -> str:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.get("normalized_transcript", ""))
        return output_path
