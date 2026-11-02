"""
BrandingAgent: Responsible for Logo Upload Ingestion, Transparent Watermarking,
Placement Coordinates (Top-Left, Top-Right, Bottom-Left, Bottom-Right, Center, Background),
Scale, and Opacity Configuration.
Strictly adheres to FR-08 of requirements.md.
"""
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image

class BrandingAgent:
    """
    Agent responsible for:
    1. Branding overlay inquiry (FR-08.1)
    2. Logo asset validation & processing with transparency (FR-08.2)
    3. Explicit placement coordinates calculation: Top-Left, Top-Right, Bottom-Left, Bottom-Right, Center, Background (FR-08.2)
    4. Scale and opacity percentage configuration (FR-08.2)
    """

    ALLOWED_POSITIONS = [
        "Top-Right", "Top-Left", "Bottom-Right", "Bottom-Left", "Center", "Background"
    ]

    def validate_branding_file(self, file_path: Path) -> Tuple[bool, str]:
        """Validates branding image and ensures transparency compatibility."""
        if not file_path.exists():
            return False, "Branding logo file not found."
        ext = file_path.suffix.lower()
        if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
            return False, "Unsupported logo format. PNG with transparency is recommended."
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True, "Valid logo."
        except Exception as e:
            return False, f"Corrupted logo file: {e}"

    def prepare_watermark_overlay(
        self,
        logo_path: Path,
        output_path: Path,
        position: str = "Top-Right",
        scale_pct: float = 0.18,
        opacity_pct: float = 0.90,
        target_video_w: int = 1080,
        target_video_h: int = 1920
    ) -> Optional[Path]:
        """
        Renders a pre-scaled, opacity-adjusted RGBA watermark badge
        ready for FFmpeg overlay composition.
        """
        try:
            with Image.open(logo_path) as logo:
                logo_rgba = logo.convert("RGBA")

                # If Background watermark mode: scale large to center background
                if position.lower() == "background":
                    max_w = int(target_video_w * 0.60)
                    logo_rgba.thumbnail((max_w, max_w), Image.Resampling.LANCZOS)
                    # Low opacity for subtle background watermark
                    opacity_pct = min(opacity_pct, 0.25)
                else:
                    max_dim = int(target_video_w * scale_pct)
                    logo_rgba.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

                # Adjust alpha channel for custom opacity
                r, g, b, alpha = logo_rgba.split()
                alpha = alpha.point(lambda p: int(p * (opacity_pct)))
                logo_rgba.putalpha(alpha)

                logo_rgba.save(output_path, "PNG")
                return output_path
        except Exception as e:
            print(f"Error preparing watermark overlay: {e}")
            return None

    def get_ffmpeg_overlay_coords(self, position: str, pad: int = 40) -> str:
        """
        Calculates FFmpeg overlay filter coordinates for each position (FR-08.2).
        Supports Top-Left, Top-Right, Bottom-Left, Bottom-Right, Center, Background.
        """
        pos = (position or "Top-Right").lower()
        if "top-left" in pos:
            return f"{pad}:{pad}"
        elif "bottom-left" in pos:
            return f"{pad}:H-h-{pad}"
        elif "bottom-right" in pos:
            return f"W-w-{pad}:H-h-{pad}"
        elif "center" in pos:
            return "(W-w)/2:(H-h)/2"
        elif "background" in pos:
            return "(W-w)/2:(H-h)/2"
        else:
            # Default: Top-Right
            return f"W-w-{pad}:{pad}"

