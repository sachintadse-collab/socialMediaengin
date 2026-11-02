"""
Configuration settings for the Reel Creator Agent.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import imageio_ffmpeg

# Load environment variables from .env if present
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Ensure runtime directories exist
STATIC_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Locate FFmpeg binary securely from imageio_ffmpeg
try:
    FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_BIN = "ffmpeg"

# Server configuration
# Default to 0.0.0.0 so mobile devices on the same Wi-Fi can connect
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

# Gemini API configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Video Specs (Instagram Reels / TikTok / YouTube Shorts Standard)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
TARGET_FPS = 30
DEFAULT_IMAGE_DURATION = 3.5  # seconds per still photo
HOOK_DURATION = 3.0           # seconds hook text remains on screen

# Security & Limits
MAX_UPLOAD_SIZE_MB = 100
ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".webp"},
    "video": {".mp4", ".mov", ".mkv", ".webm"},
    "audio": {".mp3", ".wav", ".aac", ".m4a", ".ogg"}
}
