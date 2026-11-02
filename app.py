"""
FastAPI / Starlette Web Application:
Serves the Mobile-First PWA frontend, REST & WebSocket endpoints, media upload handling,
and video streaming.
"""
import os
import shutil
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from config import (
    BASE_DIR,
    STATIC_DIR,
    ASSETS_DIR,
    UPLOADS_DIR,
    OUTPUTS_DIR,
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_SIZE_MB
)
from agent import ReelCreatorAgent

# Initialize master agent
agent = ReelCreatorAgent()

async def index(request):
    """Serve the Mobile-First PWA single-page application."""
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)

async def get_session_state(request):
    """Retrieve or initialize session state."""
    session_id = request.query_params.get("session_id")
    session = agent.get_or_create_session(session_id)
    return JSONResponse(session.to_dict())

async def send_message(request):
    """Process a user chat message or interactive card action."""
    data = await request.json()
    session_id = data.get("session_id")
    message = data.get("message", "")
    payload = data.get("payload", {})

    session = agent.get_or_create_session(session_id)
    response = agent.process_message(session, message, payload)
    response["session"] = session.to_dict()
    return JSONResponse(response)

async def get_caption_options(request):
    """
    Returns fresh caption variations in-place for the current session without advancing state.
    """
    session_id = request.query_params.get("session_id")
    session = agent.get_or_create_session(session_id)
    category = getattr(session, "detected_category", "ethnic_fashion" if "ethnic" in (session.vibe or "").lower() or "saree" in (session.vibe or "").lower() else "aesthetic")
    session.caption_cycle = getattr(session, "caption_cycle", 0) + 1
    options = agent.get_caption_variations(category, session.vibe, cycle_offset=session.caption_cycle)
    session.caption_options = options
    return JSONResponse({"options": options, "session": session.to_dict()})

async def get_hook_options(request):
    """
    Returns fresh viral hook variations in-place for the current session without advancing state.
    """
    session_id = request.query_params.get("session_id")
    session = agent.get_or_create_session(session_id)
    category = getattr(session, "detected_category", "ethnic_fashion" if "ethnic" in (session.vibe or "").lower() or "saree" in (session.vibe or "").lower() else "aesthetic")
    session.hook_cycle = getattr(session, "hook_cycle", 0) + 1
    hooks = agent.get_hook_variations(category, session.vibe, cycle_offset=session.hook_cycle)
    session.proposed_hooks = hooks
    return JSONResponse({"hooks": hooks, "session": session.to_dict()})

async def reset_session(request):
    """Explicitly resets or starts a brand new reel session."""
    session = agent.get_or_create_session(None)
    response = agent.process_message(session, "")
    response["session"] = session.to_dict()
    return JSONResponse(response)

async def upload_media(request):
    """
    Handles media uploads (pictures, videos, audio, or branding logos).
    Performs MIME and extension validation in isolated session sandbox.
    """
    form = await request.form()
    session_id = form.get("session_id")
    upload_type = form.get("type", "media") # "media" or "branding"

    if not session_id:
        return JSONResponse({"error": "session_id required"}, status_code=400)

    session = agent.get_or_create_session(session_id)
    uploaded_files = form.getlist("files")

    if not uploaded_files:
        single_file = form.get("file")
        if single_file:
            uploaded_files = [single_file]

    saved_items = []
    for file_obj in uploaded_files:
        filename = getattr(file_obj, "filename", "upload")
        ext = Path(filename).suffix.lower()

        # Security check: validate extension
        all_allowed = ALLOWED_EXTENSIONS["image"] | ALLOWED_EXTENSIONS["video"] | ALLOWED_EXTENSIONS["audio"]
        if ext not in all_allowed:
            continue

        dest_file = session.session_dir / f"{upload_type}_{filename}"
        with open(dest_file, "wb") as f:
            content = await file_obj.read()
            f.write(content)

        # FR-02.3 & FR-14.1: Strict Magic-Byte Inspection via MediaReadAgent
        valid, reason = agent.media_read_agent.validate_file_bytes(dest_file)
        if not valid:
            try:
                dest_file.unlink(missing_ok=True)
            except Exception:
                pass
            print(f"File rejected ({filename}): {reason}")
            continue

        # Generate thumbnail for video files
        if ext in ALLOWED_EXTENSIONS["video"]:
            try:
                import cv2
                cap = cv2.VideoCapture(str(dest_file))
                ret, frame = cap.read()
                cap.release()
                if ret:
                    thumb_path = dest_file.with_name(f"{dest_file.name}.thumb.jpg")
                    cv2.imwrite(str(thumb_path), frame)
            except Exception as e:
                print(f"Error generating video thumbnail: {e}")

        if upload_type == "branding":
            session.branding_file = dest_file
            session.has_branding = True
        else:
            session.uploaded_media.append(dest_file)

        saved_items.append(filename)

    return JSONResponse({
        "status": "success",
        "uploaded_count": len(saved_items),
        "files": saved_items,
        "session": session.to_dict()
    })

async def upload_voiceover(request):
    """
    Requirement 11:
    Receives synchronized voiceover audio blob from browser MediaRecorder.
    Triggers background music removal and voiceover multiplexing.
    """
    form = await request.form()
    session_id = form.get("session_id")
    audio_file = form.get("audio")

    if not session_id or not audio_file:
        return JSONResponse({"error": "session_id and audio file required"}, status_code=400)

    session = agent.get_or_create_session(session_id)
    vo_path = session.session_dir / "user_voiceover.wav"
    
    with open(vo_path, "wb") as f:
        content = await audio_file.read()
        f.write(content)

    # Process voiceover replacement
    result = agent.handle_voiceover_upload(session, vo_path)
    result["session"] = session.to_dict()
    return JSONResponse(result)

async def serve_output_video(request):
    """
    Streams the generated reel MP4 with partial content (Range requests) support
    for smooth mobile seeking.
    """
    session_id = request.path_params["session_id"]
    filename = request.path_params["filename"]

    # Security check: prevent directory traversal
    if ".." in session_id or ".." in filename:
        return Response("Forbidden", status_code=403)

    target_file = OUTPUTS_DIR / session_id / filename
    if not target_file.exists():
        return Response("Video Not Found", status_code=404)

    return FileResponse(
        target_file,
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"}
    )

async def serve_upload_media(request):
    """Serves uploaded media files and generated thumbnails."""
    session_id = request.path_params["session_id"]
    filename = request.path_params["filename"]

    # Security check: prevent directory traversal
    if ".." in session_id or ".." in filename:
        return Response("Forbidden", status_code=403)

    target_file = UPLOADS_DIR / session_id / filename
    if not target_file.exists():
        return Response("File Not Found", status_code=404)

    ext = target_file.suffix.lower()
    media_type = "image/jpeg"
    if ext == ".png":
        media_type = "image/png"
    elif ext == ".webp":
        media_type = "image/webp"
    elif ext in [".mp4", ".mov", ".webm"]:
        media_type = "video/mp4"
    elif ext in [".mp3", ".wav", ".aac"]:
        media_type = "audio/mpeg"

    return FileResponse(target_file, media_type=media_type)

async def serve_asset_audio(request):
    """Serves royalty-free and user background music tracks from the library."""
    import urllib.parse
    raw_filename = request.path_params["filename"]
    filename = urllib.parse.unquote(raw_filename)
    if ".." in filename or ".." in raw_filename:
        return Response("Forbidden", status_code=403)

    target_file = ASSETS_DIR / filename
    if not target_file.exists():
        # Try finding case-insensitively or matching filename
        for f in ASSETS_DIR.iterdir():
            if f.name.lower() == filename.lower():
                target_file = f
                break

    if not target_file.exists():
        return Response("Audio Not Found", status_code=404)

    ext = target_file.suffix.lower()
    media_type = "audio/mpeg"
    if ext == ".wav":
        media_type = "audio/wav"
    elif ext == ".ogg":
        media_type = "audio/ogg"
    elif ext in [".m4a", ".aac"]:
        media_type = "audio/mp4"

    return FileResponse(target_file, media_type=media_type, headers={"Accept-Ranges": "bytes"})

# Routing configuration
routes = [
    Route("/", endpoint=index, methods=["GET"]),
    Route("/api/session", endpoint=get_session_state, methods=["GET"]),
    Route("/api/reset", endpoint=reset_session, methods=["GET", "POST"]),
    Route("/api/caption_options", endpoint=get_caption_options, methods=["GET"]),
    Route("/api/hook_options", endpoint=get_hook_options, methods=["GET"]),
    Route("/api/message", endpoint=send_message, methods=["POST"]),
    Route("/api/upload", endpoint=upload_media, methods=["POST"]),
    Route("/api/voiceover", endpoint=upload_voiceover, methods=["POST"]),
    Route("/outputs/{session_id}/{filename}", endpoint=serve_output_video, methods=["GET"]),
    Route("/uploads/{session_id}/{filename}", endpoint=serve_upload_media, methods=["GET"]),
    Route("/assets/{filename}", endpoint=serve_asset_audio, methods=["GET"]),
    Route("/api/audio/preview/{filename}", endpoint=serve_asset_audio, methods=["GET"]),
    Mount("/static", app=StaticFiles(directory=str(STATIC_DIR)), name="static"),
]

# Permissive CORS middleware for local PWA dev
middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

if __name__ == "__main__":
    import uvicorn
    import socket
    from config import HOST, PORT

    # Detect local Wi-Fi network IP for mobile device access
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            pass

    print("=" * 65)
    print("🚀 REEL CREATOR AGENT — MOBILE & DESKTOP STUDIO")
    print("=" * 65)
    print(f"💻 On your PC:           http://127.0.0.1:{PORT}")
    print(f"📱 On your Mobile Phone:  http://{local_ip}:{PORT}")
    print("=" * 65)
    print("💡 Tip: Make sure your phone is connected to the SAME Wi-Fi network.")
    print(f"   Share the link with 'http://' included so it becomes clickable:")
    print(f"   👉 http://{local_ip}:{PORT}")
    print("=" * 65)
    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)

