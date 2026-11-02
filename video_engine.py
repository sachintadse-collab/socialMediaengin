"""
Video Engine: Facade connecting to VideoAssemblyAgent for assembling 9:16 vertical reels,
Ken Burns motion, transparent overlays, branding positioning, and audio synchronization.
"""
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from agents.video_assembly_agent import VideoAssemblyAgent

_video_agent = VideoAssemblyAgent()

def assemble_reel(
    session_dir: Path,
    media_files: List[Path],
    scene_descriptions: List[str],
    hook_text: Optional[str] = None,
    branding_file: Optional[Path] = None,
    branding_position: str = "Top-Right",
    branding_opacity: float = 0.90,
    bgm_file: Optional[Path] = None,
    output_filename: str = "reel_final.mp4",
    vibe: Optional[str] = None,
    scene_tags: Optional[List[str]] = None,
    mute_audio: bool = False
) -> Tuple[bool, Optional[Path], str]:
    return _video_agent.assemble_reel(
        session_dir=session_dir,
        media_files=media_files,
        scene_descriptions=scene_descriptions,
        hook_text=hook_text,
        branding_file=branding_file,
        branding_position=branding_position,
        branding_opacity=branding_opacity,
        bgm_file=bgm_file,
        output_filename=output_filename,
        vibe=vibe,
        scene_tags=scene_tags,
        mute_audio=mute_audio
    )
