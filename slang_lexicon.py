"""
Hinglish, Hindi & Indian English Slang Lexicon and Contextual Normalizer.
Handles colloquial words, code-switching phrases, and phonetically ambiguous speech terms.
"""

import re
from typing import Dict, List, Tuple

# Common Slangs Dictionary (Roman Hinglish phonetic variations to standard normalized Roman Hinglish)
HINGLISH_SLANG_MAPPINGS: Dict[str, str] = {
    # Greetings & Calls
    "bhai": "bhai",
    "bhaiya": "bhaiya",
    "bro": "bro",
    "yaar": "yaar",
    "yar": "yaar",
    "dost": "dost",
    "guru": "guru",
    "boss": "boss",
    "ustad": "ustaad",
    "bawa": "bawa",
    "bhidu": "bhidu",
    
    # Action & Situation Slangs
    "jugaad": "jugaad",
    "jugad": "jugaad",
    "jugaadu": "jugaadu",
    "scene": "scene",
    "scen": "scene",
    "faadu": "faadu",
    "fadu": "faadu",
    "machao": "machao",
    "machate": "machate",
    "bawaal": "bawaal",
    "bawal": "bawaal",
    "dhamaka": "dhamaka",
    "dhamaal": "dhamaal",
    "jhakaas": "jhakaas",
    "jhakas": "jhakaas",
    "bindaas": "bindaas",
    "bindas": "bindaas",
    "chaska": "chaska",
    "chalta": "chalta",
    "chalta hai": "chalta hai",
    "totka": "totka",
    "locha": "locha",
    "panga": "panga",
    "lafda": "lafda",
    "siyapa": "siyapa",
    "raita": "raita",
    "fundoo": "fundoo",
    
    # Emotional & Casual Slangs
    "chill": "chill",
    "chill maar": "chill maar",
    "chill mar": "chill maar",
    "tension": "tension",
    "load mat le": "load mat le",
    "load mat lo": "load mat lo",
    "scene sorted": "scene sorted",
    "scene off": "scene off",
    "setting": "setting",
    "jhol": "jhol",
    "topi": "topi",
    "masti": "masti",
    "bakchodi": "bakchodi",
    "timepass": "timepass",
    "churan": "churan",
    "feku": "feku",
    "goli mat de": "goli mat de",
    "patli gali": "patli gali",
    "kat le": "kat le",
    "katli": "katli",
    "khisak": "khisak",
    "bhasad": "bhasad",
    "vibe": "vibe",
    "vibe check": "vibe check",
    "sahi hai": "sahi hai",
    "ek number": "ek number",
    "kadak": "kadak",
    "gazab": "gazab",
    "ghanta": "ghanta",
    "bevajah": "bevajah",
    "time waste": "time waste",
    "mast": "mast",
    "zabardast": "zabardast",
    "tagda": "tagda",
    "chakkar": "chakkar",
    "chai paani": "chai paani",
    "chai-pani": "chai-pani",
    "kharcha paani": "kharcha paani"
}

# Devanagari equivalents for Hindi/Hinglish transcription mode
DEVANAGARI_SLANG_MAPPINGS: Dict[str, str] = {
    "jugaad": "जुगाड़",
    "bhai": "भाई",
    "bhaiya": "भैया",
    "yaar": "यार",
    "faadu": "फाड़ू",
    "bawaal": "बवाल",
    "jhakaas": "झकास",
    "bindaas": "बिंदास",
    "locha": "लोचा",
    "panga": "पंगा",
    "lafda": "लफड़ा",
    "siyapa": "सियापा",
    "bhasad": "भसड़",
    "kadak": "कड़क",
    "mast": "मस्त",
    "zabardast": "ज़बरदस्त",
    "tagda": "तगड़ा",
    "dhamaka": "धमाका",
    "dhamaal": "धमाल",
    "masti": "मस्ती",
    "setting": "सेटिंग",
    "jhol": "झोल",
    "scene": "सीन",
    "chill": "चिल",
    "tension": "टेंशन",
    "bawa": "बावा",
    "bhidu": "भीडू",
    "gazab": "ग़ज़ब",
    "ek number": "एक नंबर"
}

# Common Hinglish context prompts to guide the Whisper / ASR decoder
HINGLISH_INITIAL_PROMPTS = (
    "Yeh ek Hindi, English aur Hinglish mixed conversation hai. "
    "Isme common Indian slangs jaise jugaad, bhai, yaar, chill maar, scene set hai, bindaas, "
    "jhakaas, bawaal, panga, locha, bhasad use hote hain."
)

class SlangNormalizer:
    """Normalizes and highlights Indian colloquial slangs in transcribed text."""
    
    def __init__(self):
        self.slangs_roman = HINGLISH_SLANG_MAPPINGS
        self.slangs_devanagari = DEVANAGARI_SLANG_MAPPINGS
    
    def detect_slangs(self, text: str) -> List[Dict[str, str]]:
        """Finds all detected slang occurrences in the transcribed text."""
        detected = []
        lower_text = text.lower()
        
        # Check multi-word slangs first, then single-word slangs
        sorted_keys = sorted(self.slangs_roman.keys(), key=lambda x: len(x), reverse=True)
        for slang in sorted_keys:
            pattern = r'\b' + re.escape(slang) + r'\b'
            matches = list(re.finditer(pattern, lower_text))
            for match in matches:
                detected.append({
                    "slang": slang,
                    "standard": self.slangs_roman[slang],
                    "devanagari": self.slangs_devanagari.get(slang, ""),
                    "start": match.start(),
                    "end": match.end()
                })
        return detected

    def normalize_text(self, text: str, mode: str = "hinglish") -> str:
        """
        Normalizes slang words and formatting based on mode:
        mode: 'hinglish' (Roman script with standardized slangs),
              'devanagari' (Hindi script with devanagari slangs),
              'verbatim' (original transcription with minor punctuation cleanups)
        """
        if not text:
            return ""
        
        cleaned = text.strip()
        
        if mode == "hinglish":
            # Normalize common misspelling variants to standard Hinglish
            sorted_keys = sorted(self.slangs_roman.keys(), key=lambda x: len(x), reverse=True)
            for slang in sorted_keys:
                pattern = re.compile(r'\b' + re.escape(slang) + r'\b', re.IGNORECASE)
                cleaned = pattern.sub(self.slangs_roman[slang], cleaned)
                
        elif mode == "devanagari":
            # Map known Roman slangs to Devanagari if present
            sorted_keys = sorted(self.slangs_devanagari.keys(), key=lambda x: len(x), reverse=True)
            for slang in sorted_keys:
                pattern = re.compile(r'\b' + re.escape(slang) + r'\b', re.IGNORECASE)
                cleaned = pattern.sub(self.slangs_devanagari[slang], cleaned)
                
        # Fix basic whitespace and punctuation
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\s([?.!,"])', r'\1', cleaned)
        
        return cleaned

    def get_initial_prompt(self, target_mode: str = "hinglish") -> str:
        """Returns the specialized Whisper prompt context for Hinglish recognition."""
        if target_mode == "hinglish":
            return HINGLISH_INITIAL_PROMPTS
        elif target_mode == "hindi":
            return "यह हिंदी और हिंग्लिश ऑडियो ट्रांसक्रिप्शन है जिसमें आम बोलचाल के शब्द शामिल हैं।"
        return "This is a transcription for conversational English and code-mixed Indian English."
