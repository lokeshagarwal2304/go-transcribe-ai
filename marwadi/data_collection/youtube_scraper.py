#!/usr/bin/env python3
"""Download Marwadi speech audio from YouTube using yt-dlp.

Example:
    python marwadi/data_collection/youtube_scraper.py --query "Marwadi speech" --max-videos 10 --output-dir data/raw_audio
"""

import argparse
import os
import re
from pathlib import Path

import yt_dlp


def sanitize_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9\s-]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:120]


def download_audio(query: str, output_dir: str, max_videos: int = 20):
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "0",
        }],
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch{max_videos}:{query}", download=False)

    entries = search_results.get("entries", []) if isinstance(search_results, dict) else []
    if not entries:
        print(f"[INFO] No entries found for query: {query}")
        return []

    downloaded = []
    for idx, entry in enumerate(entries[:max_videos], start=1):
        video_url = entry.get("webpage_url") or entry.get("url")
        title = sanitize_name(entry.get("title") or f"video_{idx}")
        if not video_url:
            continue

        target_path = os.path.join(output_dir, f"{idx:02d}_{title}.wav")
        if os.path.exists(target_path):
            downloaded.append(target_path)
            continue

        opts = {
            **ydl_opts,
            "outtmpl": target_path,
        }

        print(f"[INFO] Downloading {idx}/{len(entries)}: {title}")
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([video_url])
            downloaded.append(target_path)
        except Exception as exc:
            print(f"[WARN] Failed to download {video_url}: {exc}")

    return downloaded


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download public Marwadi speech audio from YouTube")
    parser.add_argument("--query", type=str, required=True, help="Search query such as 'Marwadi speech' or 'Rajasthan folk speech'")
    parser.add_argument("--output-dir", type=str, default="data/raw_audio", help="Directory for audio storage")
    parser.add_argument("--max-videos", type=int, default=20, help="Maximum number of videos to search/download")
    args = parser.parse_args()

    files = download_audio(args.query, args.output_dir, args.max_videos)
    print(f"[INFO] Completed. Downloaded {len(files)} file(s) into {args.output_dir}")
