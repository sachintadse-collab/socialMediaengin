"""
VideoAssemblyAgent: Responsible for Compiling 9:16 Vertical Video Reels (1080x1920),
Ken Burns Motion, Floating Transparent Hook Typography, Transparent Scene Subtitles,
Branding Overlays, and Audio Mixing with Parameterized Safe FFmpeg Execution.
Strictly adheres to FR-10, FR-11, and FR-14.3 of requirements.md.
"""
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont

from config import FFMPEG_BIN, VIDEO_WIDTH, VIDEO_HEIGHT, TARGET_FPS, HOOK_DURATION, DEFAULT_IMAGE_DURATION
from agents.branding_agent import BrandingAgent

class VideoAssemblyAgent:
    """
    Agent responsible for:
    1. Compiling 9:16 vertical video (1080x1920) with Ken Burns motion (FR-10.1)
    2. Floating transparent hook text overlay for first 3 seconds (FR-07.1, FR-10.1)
    3. Floating transparent scene description subtitles (FR-05.1, FR-10.1)
    4. Branding watermark positioning and opacity (FR-08.2)
    5. Audio synchronization (BGM, Voiceover, or Mute) (FR-11.3, FR-11.4)
    6. Safe command parameterization preventing argument injection (FR-14.3)
    """

    def __init__(self):
        self.branding_agent = BrandingAgent()

    def get_font(self, size: int = 34, bold: bool = False) -> ImageFont.ImageFont:
        """Helper to load Windows TrueType fonts with clean fallback."""
        font_files = (
            ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"]
            if bold else
            ["segoeui.ttf", "arial.ttf", "calibri.ttf"]
        )
        for font_name in font_files:
            try:
                fp = Path("C:/Windows/Fonts") / font_name
                if fp.exists():
                    return ImageFont.truetype(str(fp), size=size)
            except Exception:
                pass
        return ImageFont.load_default()

    def render_hook_banner(self, hook_text: str, output_path: Path) -> Path:
        """
        Renders 100% transparent floating text for the viral hook (FR-07, FR-10).
        No container box or borders - only crisp floating social-media reel typography
        with a soft shadow and dark outline for legibility over light scenes.
        """
        banner_w, banner_h = 1000, 240
        img = Image.new("RGBA", (banner_w, banner_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Word wrap hook text
        words = hook_text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 26:
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        font = self.get_font(42, bold=True)
        line_spacing = 52
        total_text_h = len(lines) * line_spacing
        start_y = (banner_h - total_text_h) // 2

        for i, line in enumerate(lines):
            y = start_y + (i * line_spacing) + 16
            # Soft shadow
            draw.text(
                (banner_w // 2 + 3, y + 3),
                line,
                font=font,
                fill=(0, 0, 0, 160),
                stroke_width=5,
                stroke_fill=(0, 0, 0, 160),
                anchor="mm"
            )
            # Crisp white foreground with outline
            draw.text(
                (banner_w // 2, y),
                line,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=4,
                stroke_fill=(0, 0, 0, 240),
                anchor="mm"
            )

        img.save(output_path, "PNG")
        return output_path

    def render_description_badge(self, desc_text: str, output_path: Path) -> Path:
        """
        Renders 100% transparent floating subtitle text for media descriptions (FR-05, FR-10).
        Clean subtitle typography visible at the bottom of the reel.
        """
        badge_w, badge_h = 1000, 160
        img = Image.new("RGBA", (badge_w, badge_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Word wrap description
        words = desc_text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 34:
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        font = self.get_font(32, bold=True)
        line_spacing = 42
        total_text_h = len(lines) * line_spacing
        start_y = (badge_h - total_text_h) // 2

        for i, line in enumerate(lines):
            y = start_y + (i * line_spacing) + 10
            # Soft shadow
            draw.text(
                (badge_w // 2 + 2, y + 2),
                line,
                font=font,
                fill=(0, 0, 0, 150),
                stroke_width=4,
                stroke_fill=(0, 0, 0, 150),
                anchor="mm"
            )
            # Crisp white text
            draw.text(
                (badge_w // 2, y),
                line,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=3,
                stroke_fill=(0, 0, 0, 230),
                anchor="mm"
            )

        img.save(output_path, "PNG")
        return output_path

    def get_media_duration(self, file_path: Path) -> float:
        """Extract media duration using ffprobe/ffmpeg."""
        try:
            cmd = [FFMPEG_BIN, "-i", str(file_path), "-f", "null", "-"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            for line in res.stderr.splitlines():
                if "Duration:" in line:
                    time_str = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = time_str.split(":")
                    return float(h) * 3600 + float(m) * 60 + float(s)
        except Exception:
            pass
        return DEFAULT_IMAGE_DURATION

    def assemble_reel(
        self,
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
        """
        Compiles the complete 9:16 vertical video reel (FR-10).
        Strictly parameterized to prevent command injection (FR-14.3).
        """
        if not media_files:
            return False, None, "No media files provided for assembly."

        session_dir.mkdir(parents=True, exist_ok=True)
        final_output = session_dir / output_filename
        rendered_clips = []
        total_reel_duration = 0.0

        # Render each media file into a standardized 1080x1920 9:16 clip
        for idx, media_path in enumerate(media_files):
            clip_output = session_dir / f"clip_{idx:02d}.mp4"
            desc = scene_descriptions[idx] if idx < len(scene_descriptions) else ""
            desc_badge_path = None
            if desc:
                desc_badge_path = session_dir / f"badge_{idx:02d}.png"
                self.render_description_badge(desc, desc_badge_path)

            ext = media_path.suffix.lower()
            is_video = ext in [".mp4", ".mov", ".mkv", ".m4v"]

            if is_video:
                duration = self.get_media_duration(media_path)
                cmd = [
                    FFMPEG_BIN, "-y",
                    "-i", str(media_path)
                ]
                filter_chain = (
                    f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
                    f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
                    f"fps={TARGET_FPS},format=yuv420p"
                )
                if desc_badge_path and desc_badge_path.exists():
                    cmd.extend(["-i", str(desc_badge_path)])
                    filter_complex = f"[0:v]{filter_chain}[v0];[v0][1:v]overlay=(W-w)/2:H-h-80[vout]"
                    cmd.extend(["-filter_complex", filter_complex, "-map", "[vout]"])
                else:
                    cmd.extend(["-vf", filter_chain])

                cmd.extend(["-an", "-c:v", "libx264", "-preset", "ultrafast", str(clip_output)])
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0 and clip_output.exists():
                    rendered_clips.append(clip_output)
                    total_reel_duration += duration
            else:
                # Still photo with Ken Burns pan/zoom motion
                duration = DEFAULT_IMAGE_DURATION
                total_reel_duration += duration
                total_frames = int(duration * TARGET_FPS)

                # Alternate zoom-in vs zoom-out per clip
                zoom_expr = "min(pzoom+0.0015,1.20)" if idx % 2 == 0 else "max(1.20-0.0015*on,1.0)"

                cmd = [
                    FFMPEG_BIN, "-y",
                    "-i", str(media_path)
                ]

                filter_chain = (
                    f"scale={VIDEO_WIDTH}*2:{VIDEO_HEIGHT}*2:force_original_aspect_ratio=increase,"
                    f"crop={VIDEO_WIDTH}*2:{VIDEO_HEIGHT}*2,"
                    f"zoompan=z='{zoom_expr}':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={TARGET_FPS},"
                    f"format=yuv420p"
                )

                if desc_badge_path and desc_badge_path.exists():
                    cmd.extend(["-i", str(desc_badge_path)])
                    filter_complex = f"[0:v]{filter_chain}[v0];[v0][1:v]overlay=(W-w)/2:H-h-80[vout]"
                    cmd.extend(["-filter_complex", filter_complex, "-map", "[vout]"])
                else:
                    cmd.extend(["-vf", filter_chain])

                cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", str(clip_output)])
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0 and clip_output.exists():
                    rendered_clips.append(clip_output)

        if not rendered_clips:
            return False, None, "Failed to render video clips from media."

        # Concatenate clips together
        concat_list_file = session_dir / "concat_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for clip in rendered_clips:
                clean_path = str(clip.resolve()).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        merged_video = session_dir / "merged_video.mp4"
        cmd_concat = [
            FFMPEG_BIN, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c", "copy",
            str(merged_video)
        ]
        res_c = subprocess.run(cmd_concat, capture_output=True, text=True)
        if res_c.returncode != 0 or not merged_video.exists():
            return False, None, f"Video concatenation failed: {res_c.stderr}"

        # Build Overlays: Hook banner (first 3s) & Branding watermark
        inputs = [merged_video]
        overlay_filters = []
        input_idx = 1

        # 1. Floating Hook banner overlay (first 3 seconds)
        if hook_text and hook_text.strip():
            hook_banner_path = session_dir / "hook_banner.png"
            self.render_hook_banner(hook_text, hook_banner_path)
            if hook_banner_path.exists():
                inputs.append(hook_banner_path)
                overlay_filters.append(
                    f"[{input_idx - 1}:v][{input_idx}:v]overlay=(W-w)/2:120:enable='between(t,0,{HOOK_DURATION})'[v_hook]"
                )
                input_idx += 1

        # 2. Branding Logo overlay
        if branding_file and branding_file.exists():
            processed_logo = session_dir / "branding_prepared.png"
            prep_ok = self.branding_agent.prepare_watermark_overlay(
                logo_path=branding_file,
                output_path=processed_logo,
                position=branding_position,
                opacity_pct=branding_opacity
            )
            if prep_ok and processed_logo.exists():
                inputs.append(processed_logo)
                coords = self.branding_agent.get_ffmpeg_overlay_coords(branding_position)
                prev_v = "[v_hook]" if overlay_filters else "[0:v]"
                overlay_filters.append(f"{prev_v}[{input_idx}:v]overlay={coords}[v_brand]")
                input_idx += 1

        # Audio Integration: BGM looping & trimming, or silent video (FR-04, FR-11.4)
        has_audio = (not mute_audio) and (bgm_file and bgm_file.exists())
        audio_input_idx = None
        if has_audio:
            inputs.append(bgm_file)
            audio_input_idx = input_idx
            input_idx += 1

        # Construct safe FFmpeg invocation
        cmd_final = [FFMPEG_BIN, "-y"]
        for idx, inp in enumerate(inputs):
            if idx == audio_input_idx and has_audio:
                # Loop BGM seamlessly to cover entire reel duration
                cmd_final.extend(["-stream_loop", "-1", "-i", str(inp)])
            else:
                cmd_final.extend(["-i", str(inp)])

        final_v_label = "[0:v]"
        if overlay_filters:
            final_v_label = "[v_brand]" if branding_file and branding_file.exists() else "[v_hook]"
            filter_str = ";".join(overlay_filters)
            cmd_final.extend(["-filter_complex", filter_str, "-map", final_v_label])
        else:
            cmd_final.extend(["-map", "0:v"])

        if has_audio:
            # Map and trim audio precisely to total reel duration
            cmd_final.extend([
                "-map", f"{audio_input_idx}:a",
                "-af", f"atrim=0:{total_reel_duration},loudnorm=I=-16:TP=-1.5:LRA=11",
                "-c:a", "aac",
                "-b:a", "192k"
            ])
        else:
            # Silent video per FR-11.4
            cmd_final.extend(["-an"])

        cmd_final.extend([
            "-t", str(total_reel_duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            "-crf", "22",
            str(final_output)
        ])

        res_f = subprocess.run(cmd_final, capture_output=True, text=True)
        if res_f.returncode == 0 and final_output.exists():
            return True, final_output, "Reel assembly completed successfully."
        else:
            return False, None, f"Final reel assembly failed: {res_f.stderr}"
