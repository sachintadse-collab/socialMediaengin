"""
Audio Engine: Facade connecting to MusicAgent for library scans, BGM curation,
FFmpeg audio interference/noise removal, and voiceover swapping.
"""
from pathlib import Path
from typing import List, Dict, Optional, Any
from agents.music_agent import MusicAgent, BASE_BGM_METADATA

_music_agent = MusicAgent()

BGM_CATALOG = BASE_BGM_METADATA

def get_all_library_tracks() -> List[Dict[str, Any]]:
    return _music_agent.get_all_library_tracks()

def get_bgm_recommendations(vibe: str) -> List[Dict[str, Any]]:
    return _music_agent.get_bgm_recommendations(vibe)

def get_track_path_by_id(track_id: str) -> Optional[Path]:
    return _music_agent.get_track_path_by_id(track_id)

def clean_audio_interference(input_audio_path: Path, output_audio_path: Path) -> bool:
    return _music_agent.clean_audio_interference(input_audio_path, output_audio_path)

def swap_audio_track(
    video_path: Path,
    new_audio_path: Optional[Path],
    output_path: Path,
    mute_all: bool = False
) -> bool:
    return _music_agent.swap_audio_track(video_path, new_audio_path, output_path, mute_all=mute_all)
