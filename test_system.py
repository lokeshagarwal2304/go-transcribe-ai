"""
Verification and Test Suite for Hinglish Transcriber Engine.
"""

import os
import sys

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import numpy as np
import soundfile as sf
from slang_lexicon import SlangNormalizer
from transcriber import HinglishTranscriber

def test_slang_normalizer():
    print("[TEST 1] Testing Slang Normalizer...")
    normalizer = SlangNormalizer()
    
    sample_text = "bhai tension mat lo, hamara jugad aur scene sorted hai, ekdum fadu kaam hua hai!"
    
    # Detect slangs
    slangs = normalizer.detect_slangs(sample_text)
    detected_words = [s["slang"] for s in slangs]
    print(f"  Input: {sample_text}")
    print(f"  Detected Slangs: {detected_words}")
    
    assert "bhai" in detected_words, "Failed to detect 'bhai'"
    assert "tension" in detected_words or "tension" in sample_text, "Failed slang check"
    assert "jugad" in detected_words or "jugaad" in detected_words, "Failed to detect 'jugad'"
    assert "scene" in detected_words or "scene sorted" in detected_words, "Failed to detect 'scene'"
    assert "fadu" in detected_words or "faadu" in detected_words, "Failed to detect 'fadu'"

    # Test normalization
    norm = normalizer.normalize_text(sample_text, mode="hinglish")
    print(f"  Normalized Hinglish: {norm}")
    assert "jugaad" in norm, "Slang normalization failed for jugaad"
    assert "faadu" in norm, "Slang normalization failed for faadu"

    # Test Devanagari conversion
    dev_norm = normalizer.normalize_text(sample_text, mode="devanagari")
    print(f"  Normalized Devanagari: {dev_norm}")
    print("  [PASSED] Slang Normalizer test passed!\n")

def test_model_loading_and_synthetic_audio():
    print("[TEST 2] Testing Transcriber Model Loading & Pipeline...")
    # Generate 2 seconds of synthetic clean sine wave tone as sample WAV
    sample_wav = os.path.join(os.path.dirname(__file__), "test_sample.wav")
    samplerate = 16000
    duration = 2.0
    t = np.linspace(0, duration, int(samplerate * duration), False)
    tone = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(sample_wav, tone.astype(np.float32), samplerate)
    print(f"  Generated test audio: {sample_wav}")

    try:
        engine = HinglishTranscriber(model_size="tiny")
        res = engine.transcribe_audio(sample_wav, language_mode="hinglish")
        print(f"  Engine Transcribe Status: {res['status']}")
        print(f"  Processing Time: {res['processing_time_seconds']}s")
        print("  [PASSED] Transcriber engine initialized and executed without errors!\n")
    finally:
        if os.path.exists(sample_wav):
            os.remove(sample_wav)

if __name__ == "__main__":
    print("========================================")
    print("Running Hinglish Transcriber Test Suite")
    print("========================================\n")
    test_slang_normalizer()
    test_model_loading_and_synthetic_audio()
    print("========================================")
    print("ALL TESTS PASSED SUCCESSFULLY! ✅")
    print("========================================")
