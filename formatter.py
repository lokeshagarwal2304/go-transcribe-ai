"""
Professional Transcription Formatter & Word Document (.docx) Generator.
Zero Stray Colons, Clean Paragraphs, and 100% GoTranscript Zero-Mistake Compliance.
"""

import os
import re
from typing import List, Dict, Any, Optional
import docx
from docx.shared import Inches, Pt, RGBColor
from gotranscript_rules import GoTranscriptPostProcessor

STOPWORDS_NOT_NAMES = {
    "for", "to", "and", "the", "you", "your", "having", "joining", "coming",
    "there", "everyone", "guys", "again", "all", "sir", "ma'am", "friend",
    "here", "speaking", "sure", "sorry", "fine", "ready", "going", "asking",
    "listening", "watching", "this", "that", "it", "so", "much", "very",
    "not", "over", "today", "yesterday", "tomorrow", "now", "well"
}

class TranscriptionFormatter:
    """Formats raw ASR segments into professional transcription documents."""

    @staticmethod
    def format_hhmmss(seconds: float) -> str:
        """Converts seconds into standard [00:00:00] format."""
        s = int(round(seconds))
        hours = s // 3600
        minutes = (s % 3600) // 60
        secs = s % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    @classmethod
    def extract_names_from_segments(cls, segments: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Scans segments to extract only genuine explicit name introductions (e.g. 'My name is John').
        """
        detected_names = {}
        
        self_intro_patterns = [
            r"\bmy name is ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
            r"\bthis is ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:speaking|here)\b",
            r"\bमेरा नाम ([A-Za-z\u0900-\u097F]+) है\b"
        ]

        address_patterns = [
            r"\b(?:mr\.|mrs\.|ms\.|dr\.)\s+([A-Z][a-z]+)\b"
        ]

        all_text = " ".join([s.get("normalized_text", "") for s in segments])

        for pattern in self_intro_patterns:
            match = re.search(pattern, all_text)
            if match:
                candidate = match.group(1).strip().title()
                if candidate.lower() not in STOPWORDS_NOT_NAMES and len(candidate) > 2:
                    detected_names["Speaker 1"] = candidate
                    break

        for pattern in address_patterns:
            matches = re.finditer(pattern, all_text)
            for m in matches:
                candidate = m.group(1).strip().title()
                if candidate.lower() not in STOPWORDS_NOT_NAMES and len(candidate) > 2:
                    if "Speaker 1" in detected_names and detected_names["Speaker 1"] != candidate:
                        detected_names["Speaker 2"] = candidate
                        break
                    elif "Speaker 1" not in detected_names:
                        detected_names["Speaker 2"] = candidate
                        break

        return detected_names

    @classmethod
    def detect_and_group_speakers(
        cls, 
        segments: List[Dict[str, Any]], 
        speaker_mode: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        Dynamically detects single-speaker monologues vs multi-speaker dialogues.
        """
        if not segments:
            return []

        if speaker_mode in ["single", "gotranscript_test"]:
            turn_text = " ".join([s["normalized_text"] for s in segments])
            return [{
                "speaker": "",
                "start": segments[0]["start"],
                "end": segments[-1]["end"],
                "segments": segments,
                "text": turn_text
            }]

        conversational_turn_triggers = [
            r"^(?:yes|yeah|no|nope|right|exactly|sure|okay|alright|definitely|absolutely|हाँ|जी|बिलकुल|सही|नहीं)\b",
            r"^(?:thank you|thanks|welcome|hello|hi|good morning|good afternoon|नमस्ते|नमस्कार|धन्यवाद)\b",
            r"\?$"
        ]

        turns = []
        current_speaker_idx = 1
        current_turn_segments = [segments[0]]
        pause_threshold = 2.5 if speaker_mode == "auto" else 1.8
        turn_switch_count = 0

        for i in range(1, len(segments)):
            prev_seg = segments[i - 1]
            curr_seg = segments[i]
            
            pause_sec = curr_seg["start"] - prev_seg["end"]
            curr_text = curr_seg.get("raw_text", "").strip()
            prev_text = prev_seg.get("raw_text", "").strip()

            is_turn = False
            has_trigger = any(re.search(pat, curr_text, re.IGNORECASE) for pat in conversational_turn_triggers)

            if pause_sec >= pause_threshold:
                is_turn = True
            elif prev_text.endswith("?") and pause_sec > 0.8:
                is_turn = True
            elif has_trigger and pause_sec > 1.0:
                is_turn = True

            if is_turn and (speaker_mode == "multiple" or turn_switch_count < 15):
                turn_switch_count += 1
                turn_text = " ".join([s["normalized_text"] for s in current_turn_segments])
                turns.append({
                    "speaker": f"Speaker {current_speaker_idx}",
                    "start": current_turn_segments[0]["start"],
                    "end": current_turn_segments[-1]["end"],
                    "segments": current_turn_segments,
                    "text": turn_text
                })
                current_speaker_idx = 2 if current_speaker_idx == 1 else 1
                current_turn_segments = [curr_seg]
            else:
                current_turn_segments.append(curr_seg)

        if current_turn_segments:
            turn_text = " ".join([s["normalized_text"] for s in current_turn_segments])
            turns.append({
                "speaker": f"Speaker {current_speaker_idx}",
                "start": current_turn_segments[0]["start"],
                "end": current_turn_segments[-1]["end"],
                "segments": current_turn_segments,
                "text": turn_text
            })

        # If auto mode detected zero conversational turn-taking, consolidate into 1 clean speaker without prefix
        if speaker_mode == "auto" and turn_switch_count == 0:
            turn_text = " ".join([s["normalized_text"] for s in segments])
            return [{
                "speaker": "",
                "start": segments[0]["start"],
                "end": segments[-1]["end"],
                "segments": segments,
                "text": turn_text
            }]

        return turns

    @classmethod
    def generate_formatted_transcript(
        cls, 
        transcription_result: Dict[str, Any],
        timestamp_rule: str = "none",
        speaker_mode: str = "auto",
        speaker_names_override: Optional[Dict[str, str]] = None,
        is_gotranscript_test: bool = True
    ) -> Dict[str, Any]:
        """
        Generates clean formatted dialogue text without stray colons.
        """
        segments = transcription_result.get("segments", [])
        if not segments:
            return {"formatted_text": "", "dialogues": [], "detected_speakers": []}

        # If GoTranscript test mode or single speaker test
        if is_gotranscript_test or speaker_mode == "gotranscript_test":
            raw_full_text = " ".join([seg.get("normalized_text", "").strip() for seg in segments])
            perfect_text = GoTranscriptPostProcessor.process_transcript(raw_full_text)
            
            paragraphs = perfect_text.split("\n\n")
            dialogue_blocks = []
            for p in paragraphs:
                if p.strip():
                    dialogue_blocks.append({
                        "speaker": "",
                        "timestamp_tag": "",
                        "start": 0.0,
                        "end": 0.0,
                        "content": p.strip(),
                        "full_line": p.strip()
                    })

            return {
                "formatted_text": perfect_text,
                "dialogues": dialogue_blocks,
                "total_turns": len(dialogue_blocks),
                "detected_speakers": ["Single Speaker"],
                "auto_detected_names": {}
            }

        # Standard Multi-Speaker Mode
        auto_detected_names = cls.extract_names_from_segments(segments)
        final_names = {}
        final_names.update(auto_detected_names)
        if speaker_names_override:
            for k, v in speaker_names_override.items():
                if v and v.strip() and not v.startswith("Speaker"):
                    final_names[k] = v.strip()

        turns = cls.detect_and_group_speakers(segments, speaker_mode=speaker_mode)
        dialogue_blocks = []
        last_timestamp_marker_sec = -120.0
        interval_sec = 120.0 if timestamp_rule == "every_2_min" else 60.0

        for turn in turns:
            spk_key = turn["speaker"]
            spk_label = final_names.get(spk_key, spk_key) if spk_key else ""
            turn_start = turn["start"]
            
            enhanced_turn_sentences = [seg.get("normalized_text", "").strip() for seg in turn["segments"]]
            turn_body = " ".join(enhanced_turn_sentences).strip()
            turn_body = GoTranscriptPostProcessor.process_transcript(turn_body)

            ts_str = ""
            if timestamp_rule == "speaker_change":
                ts_str = f"[{cls.format_hhmmss(turn_start)}] "
            elif timestamp_rule in ["every_2_min", "every_minute"]:
                if (turn_start - last_timestamp_marker_sec) >= interval_sec or last_timestamp_marker_sec < 0:
                    ts_str = f"[{cls.format_hhmmss(turn_start)}] "
                    last_timestamp_marker_sec = turn_start

            # Ensure NO leading colon if spk_label is empty!
            if spk_label and spk_label.strip():
                formatted_block = f"{spk_label}: {ts_str}{turn_body}"
            else:
                formatted_block = f"{ts_str}{turn_body}".strip()

            dialogue_blocks.append({
                "speaker": spk_label,
                "timestamp_tag": ts_str.strip(),
                "start": turn_start,
                "end": turn["end"],
                "content": turn_body,
                "full_line": formatted_block
            })

        full_formatted_text = "\n\n".join([d["full_line"] for d in dialogue_blocks])
        unique_speakers = list(set([d["speaker"] for d in dialogue_blocks if d["speaker"]]))

        return {
            "formatted_text": full_formatted_text,
            "dialogues": dialogue_blocks,
            "total_turns": len(dialogue_blocks),
            "detected_speakers": unique_speakers,
            "auto_detected_names": auto_detected_names
        }

    @classmethod
    def export_to_docx(
        cls, 
        formatted_data: Dict[str, Any], 
        output_filepath: str,
        title: str = "Audio Transcription"
    ) -> str:
        """
        Creates a clean, professional Microsoft Word (.docx) document.
        """
        doc = docx.Document()

        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)

        title_p = doc.add_paragraph()
        title_run = title_p.add_run(title)
        title_run.font.name = "Calibri"
        title_run.font.size = Pt(16)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)
        title_p.paragraph_format.space_after = Pt(14)

        for item in formatted_data.get("dialogues", []):
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(10)

            if item.get("speaker") and item["speaker"].strip():
                spk_run = p.add_run(f"{item['speaker']}: ")
                spk_run.font.name = "Calibri"
                spk_run.font.size = Pt(11)
                spk_run.font.bold = True
                spk_run.font.color.rgb = RGBColor(0x11, 0x18, 0x27)

            if item.get("timestamp_tag"):
                ts_run = p.add_run(f"{item['timestamp_tag']} ")
                ts_run.font.name = "Calibri"
                ts_run.font.size = Pt(11)
                ts_run.font.bold = True
                ts_run.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)

            content_text = item.get("content", "")
            body_run = p.add_run(content_text)
            body_run.font.name = "Calibri"
            body_run.font.size = Pt(11)
            body_run.font.color.rgb = RGBColor(0x37, 0x41, 0x51)

        doc.save(output_filepath)
        return output_filepath
