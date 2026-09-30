"""
CLI Utility for Professional Audio Transcriber with Word (.docx) Export.
"""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import argparse
from transcriber import HinglishTranscriber
from formatter import TranscriptionFormatter

def main():
    parser = argparse.ArgumentParser(
        description="Professional Audio Transcriber with GoTranscript Rules & Word (.docx) Export"
    )
    parser.add_argument("audio", help="Path to input audio file (.wav, .mp3, .m4a, .ogg, .flac)")
    parser.add_argument(
        "--mode", 
        choices=["auto", "hinglish", "hindi", "english"], 
        default="auto",
        help="Language mode (default: auto)"
    )
    parser.add_argument(
        "--model", 
        choices=["tiny", "base", "small", "medium", "large-v3"], 
        default="small",
        help="Whisper model size (default: small)"
    )
    parser.add_argument(
        "--timestamp-rule",
        choices=["every_2_min", "speaker_change", "none"],
        default="every_2_min",
        help="Rule for timestamp insertion (default: every_2_min)"
    )
    parser.add_argument(
        "--speaker-mode",
        choices=["auto", "single", "multiple"],
        default="auto",
        help="Speaker count mode (default: auto)"
    )
    parser.add_argument("--speaker1", default="", help="Name of Speaker 1 (leave blank for Auto Detect)")
    parser.add_argument("--speaker2", default="", help="Name of Speaker 2 (leave blank for Auto Detect)")
    parser.add_argument("--export-docx", help="Path to save Word .docx file", default=None)
    parser.add_argument("--export-txt", help="Path to save formatted .txt transcript", default=None)
    parser.add_argument("--export-srt", help="Path to save .srt subtitles", default=None)
    parser.add_argument("--export-json", help="Path to save .json report", default=None)

    args = parser.parse_args()

    audio_file = os.path.abspath(args.audio)
    if not os.path.exists(audio_file):
        print(f"[ERROR] File not found: {audio_file}")
        sys.exit(1)

    print("=" * 65)
    print("🎙️  Professional Speech-to-Text Transcriber (GoTranscript Ready)")
    print(f"📁 Audio File: {os.path.basename(audio_file)}")
    print(f"⏱️  Timestamp Rule: {args.timestamp_rule}")
    print(f"👥 Speakers: {args.speaker1} / {args.speaker2}")
    print("=" * 65)

    engine = HinglishTranscriber(model_size=args.model)
    print("\n⏳ Transcribing audio and applying formatting rules...")

    raw_result = engine.transcribe_audio(audio_path=audio_file, language_mode=args.mode)

    # Format into professional speaker dialogues
    speaker_map = {}
    if args.speaker1.strip():
        speaker_map["Speaker 1"] = args.speaker1.strip()
    if args.speaker2.strip():
        speaker_map["Speaker 2"] = args.speaker2.strip()

    formatted = TranscriptionFormatter.generate_formatted_transcript(
        raw_result,
        timestamp_rule=args.timestamp_rule,
        speaker_mode=args.speaker_mode,
        speaker_names_override=speaker_map
    )

    print("\n" + "=" * 65)
    print(f"✅ COMPLETED in {raw_result['processing_time_seconds']}s | Detected: {raw_result['detected_language'].upper()}")
    print(f"👥 Total Speaker Dialogue Turns: {formatted['total_turns']}")
    print("=" * 65)

    print("\n📄 FORMATTED TRANSCRIPT PREVIEW:\n")
    print(formatted["formatted_text"])
    print("\n" + "=" * 65)

    # DOCX Word Export
    docx_path = args.export_docx
    if not docx_path and not args.export_txt:
        # Default auto-save docx next to audio
        base_no_ext = os.path.splitext(audio_file)[0]
        docx_path = f"{base_no_ext}_transcript.docx"

    if docx_path:
        title = f"Transcript - {os.path.basename(audio_file)}"
        TranscriptionFormatter.export_to_docx(formatted, docx_path, title=title)
        print(f"📝 Word Document (.docx) Saved: {docx_path}")

    if args.export_txt:
        with open(args.export_txt, "w", encoding="utf-8") as f:
            f.write(formatted["formatted_text"])
        print(f"📄 Text Transcript Saved: {args.export_txt}")

    if args.export_srt:
        engine.export_to_srt(raw_result, args.export_srt)
        print(f"🎬 SRT Subtitles Saved: {args.export_srt}")

    if args.export_json:
        raw_result["formatted"] = formatted
        engine.export_to_json(raw_result, args.export_json)
        print(f"📦 JSON Saved: {args.export_json}")

if __name__ == "__main__":
    main()
