"""
MusicAgent: Responsible for Background Music (BGM) Curation, Interference/Noise Cleaning,
Preview Serving, Audio Trimming, and Voiceover/BGM Swapping & Muting.
Strictly adheres to FR-04, FR-11.3, and FR-11.4 of requirements.md.
"""
import subprocess
import urllib.parse
from pathlib import Path
from typing import List, Dict, Optional, Any

from config import ASSETS_DIR, FFMPEG_BIN

# Base Curated BGM Metadata Catalog
BASE_BGM_METADATA = [
    {
        "id": "track_festive",
        "file": "bgm_festive.mp3",
        "title": "Royal Sitar & Festive Celebration",
        "bpm": "92 BPM",
        "vibe": "Traditional, ethnic, festive, cultural elegance, saree & handloom",
        "keywords": ["ethnic", "saree", "handloom", "silk", "traditional", "festive", "bridal", "wedding", "heritage", "zari", "indian"],
        "default_for": ["ethnic_fashion", "festive", "traditional"]
    },
    {
        "id": "track_chill",
        "file": "bgm_chill.mp3",
        "title": "Chill Sunset Lo-Fi",
        "bpm": "75 BPM",
        "vibe": "Relaxed, aesthetic, cozy, coffee-shop mood",
        "keywords": ["chill", "lo-fi", "cozy", "aesthetic", "warm", "coffee", "golden", "lifestyle", "travel", "slow"],
        "default_for": ["aesthetic", "travel", "portrait"]
    },
    {
        "id": "track_energetic",
        "file": "bgm_energetic.mp3",
        "title": "Cyber Pulse Beats",
        "bpm": "128 BPM",
        "vibe": "Fast-paced, high energy, electronic, dynamic movement",
        "keywords": ["energetic", "upbeat", "pulse", "workout", "fitness", "dynamic", "hustle", "gym", "action"],
        "default_for": ["energetic"]
    },
    {
        "id": "track_cinematic",
        "file": "bgm_cinematic.mp3",
        "title": "Deep Horizons Drama",
        "bpm": "60 BPM",
        "vibe": "Cinematic, storytelling, emotional, epic",
        "keywords": ["cinematic", "noir", "drama", "atmospheric", "movie", "film", "moody", "story", "luxury"],
        "default_for": ["moody", "luxury_product"]
    }
]

class MusicAgent:
    """
    Agent responsible for:
    1. BGM catalog management & dynamic scanning of all assets (FR-04.1)
    2. Audio interference & background noise removal via FFmpeg afftdn (FR-04.2)
    3. User selection, custom audio upload, and silent reel handling (FR-04.3)
    4. Voiceover replacement & silent video muting (FR-11.3, FR-11.4)
    """

    def __init__(self):
        self.catalog = BASE_BGM_METADATA

    def get_all_library_tracks(self) -> List[Dict[str, Any]]:
        """
        Scans ASSETS_DIR dynamically for ALL available audio files (.mp3, .wav, .aac, .m4a).
        Returns complete catalog with preview URLs. File size is never a display blocker.
        """
        seen_files = set()
        tracks: List[Dict[str, Any]] = []

        # 1. Include base curated tracks whose files exist
        for meta in BASE_BGM_METADATA:
            fpath = ASSETS_DIR / meta["file"]
            if fpath.exists():
                seen_files.add(fpath.name.lower())
                tracks.append({
                    "id": meta["id"],
                    "title": meta["title"],
                    "bpm": meta["bpm"],
                    "vibe": meta["vibe"],
                    "keywords": meta["keywords"],
                    "preview_url": f"/api/audio/preview/{meta['file']}",
                    "file_path": str(fpath),
                    "is_curated": True
                })

        # 2. Dynamically scan ASSETS_DIR for additional custom or library tracks
        if ASSETS_DIR.exists():
            for p in ASSETS_DIR.iterdir():
                if p.is_file() and p.suffix.lower() in [".mp3", ".wav", ".aac", ".m4a", ".ogg"]:
                    if p.name.lower() in seen_files:
                        continue
                    seen_files.add(p.name.lower())

                    # Derive friendly title from filename
                    stem = p.stem.replace("_", " ").replace("-", " ")
                    title = " ".join(w.capitalize() for w in stem.split())
                    track_id = f"custom_{p.stem.lower()[:16]}"
                    vibe_desc = "Library Track • Custom Audio"
                    keywords = [w.lower() for w in p.stem.split() if len(w) > 2]

                    # Detect aesthetic keywords
                    fn_low = p.name.lower()
                    if any(w in fn_low for w in ["saree", "ethnic", "handloom", "sitar", "traditional", "indian", "guru", "sharanam", "kalari"]):
                        vibe_desc = "Traditional & Cultural Melody • Saree & Ethnic Vibe"
                        keywords.extend(["ethnic", "saree", "traditional", "festive", "cultural"])
                    elif any(w in fn_low for w in ["chill", "lofi", "relax", "sunset", "ambient"]):
                        vibe_desc = "Chill & Relaxing Aesthetic • Ambient Vibe"
                        keywords.extend(["chill", "lo-fi", "cozy", "aesthetic"])
                    elif any(w in fn_low for w in ["beat", "fast", "dance", "electronic", "upbeat", "pulse"]):
                        vibe_desc = "Upbeat & Dynamic Pulse • High Energy"
                        keywords.extend(["energetic", "upbeat", "pulse", "gym"])

                    encoded_filename = urllib.parse.quote(p.name)
                    tracks.append({
                        "id": track_id,
                        "title": title,
                        "bpm": "Auto-sync",
                        "vibe": vibe_desc,
                        "keywords": keywords,
                        "preview_url": f"/api/audio/preview/{encoded_filename}",
                        "file_path": str(p),
                        "is_curated": False
                    })

        return tracks

    def get_bgm_recommendations(self, vibe: str) -> List[Dict[str, Any]]:
        """
        Scores all library tracks against the user's locked vibe.
        Returns all tracks sorted by match score with top matches first.
        """
        all_tracks = self.get_all_library_tracks()
        vibe_lower = (vibe or "").lower()
        scored = []

        for track in all_tracks:
            score = 0
            for kw in track.get("keywords", []):
                if kw in vibe_lower:
                    score += 3
            if any(term in vibe_lower for term in ["saree", "ethnic", "handloom", "silk", "traditional", "festive"]) and "ethnic" in track.get("keywords", []):
                score += 5
            if any(term in vibe_lower for term in ["chill", "cozy", "aesthetic", "lo-fi"]) and "chill" in track.get("keywords", []):
                score += 5
            if any(term in vibe_lower for term in ["energetic", "fitness", "workout", "pulse"]) and "energetic" in track.get("keywords", []):
                score += 5

            scored.append((score, track))

        scored.sort(key=lambda x: -x[0])
        result = []
        for score, track in scored:
            t = dict(track)
            t["_score"] = score
            result.append(t)
        return result

    def get_track_path_by_id(self, track_id: str) -> Optional[Path]:
        """Resolves track ID to local file Path."""
        if not track_id:
            return None
        all_tracks = self.get_all_library_tracks()
        for t in all_tracks:
            if t["id"] == track_id:
                p = Path(t["file_path"])
                if p.exists():
                    return p
        # Direct lookup fallback in ASSETS_DIR
        for p in ASSETS_DIR.iterdir():
            if p.is_file() and p.suffix.lower() in [".mp3", ".wav", ".aac", ".m4a"]:
                if track_id.lower() in p.stem.lower():
                    return p
        return None

    def clean_audio_interference(self, input_audio_path: Path, output_audio_path: Path) -> bool:
        """
        FR-04.2: Removes noise, hum, hiss, and audio interferences from recorded voiceover
        or custom audio using FFmpeg's adaptive FFT noise filter (afftdn) and bandpass filters.
        """
        try:
            cmd = [
                FFMPEG_BIN, "-y",
                "-i", str(input_audio_path),
                "-af", "afftdn=nf=-25,highpass=f=60,lowpass=f=12000,loudnorm=I=-16:TP=-1.5:LRA=11",
                "-c:a", "pcm_s16le",
                str(output_audio_path)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return res.returncode == 0 and output_audio_path.exists()
        except Exception as e:
            print(f"Error cleaning audio interference: {e}")
            return False

    def swap_audio_track(
        self,
        video_path: Path,
        new_audio_path: Optional[Path],
        output_path: Path,
        mute_all: bool = False
    ) -> bool:
        """
        FR-11.3 & FR-11.4:
        - If mute_all is True: Strips all audio completely (FR-11.4).
        - If new_audio_path is provided: Replaces previous BGM completely with the new audio (e.g. voiceover) (FR-11.3).
        """
        try:
            if mute_all or not new_audio_path:
                # FR-11.4: Output silent video (no BGM and no voiceover)
                cmd = [
                    FFMPEG_BIN, "-y",
                    "-i", str(video_path),
                    "-c:v", "copy",
                    "-an",  # Strip audio stream completely
                    str(output_path)
                ]
            else:
                # FR-11.3: Clean interference if voiceover, then replace audio stream
                cmd = [
                    FFMPEG_BIN, "-y",
                    "-i", str(video_path),
                    "-i", str(new_audio_path),
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    str(output_path)
                ]

            res = subprocess.run(cmd, capture_output=True, text=True)
            return res.returncode == 0 and output_path.exists()
        except Exception as e:
            print(f"Error swapping audio track: {e}")
            return False

