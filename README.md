# Reel Creator Agent — Mobile-First PWA Studio

An AI-powered conversational agent that creates high-converting, professional 9:16 vertical reels for Instagram Reels, TikTok, and YouTube Shorts. The agent strictly adheres to the **Zero-Assumption Protocol**—asking clarifying questions at every stage rather than hallucinating default creative parameters.

---

## Features Implemented

1. **Conversational Initiation**: Interactive chatbot greets the user and initiates reel creation.
2. **Multi-Format Ingestion**: Accepts images (`.jpg`, `.png`, `.webp`), videos (`.mp4`, `.mov`, `.mkv`), and audio files (`.mp3`, `.wav`, `.aac`).
3. **Multimodal Vibe Analysis**: Analyzes visual aesthetic, lighting, palette, and mood to propose a content vibe.
4. **BGM Recommendations**: Suggests 3 curated royalty-free audio tracks with in-chat preview players matched to the vibe.
5. **Editable Scene Descriptions**: Proposes descriptions for each uploaded media file, fully editable by the user.
6. **Editable Reel Caption**: Generates high-converting post caption with hashtags, editable before rendering.
7. **Viral Hook Selection**: Generates 3 catchy hook variants for the first 3 seconds, editable by the user.
8. **Branding Overlay Positioning**: Asks for branding logo/watermark and placement (`Top-Left`, `Top-Right`, `Bottom-Left`, `Bottom-Right`, or `Center`).
9. **Zero-Assumption Guard**: Never assumes missing inputs; always prompts the user.
10. **9:16 Reel Assembly & Review**: Compiles 1080x1920 video with smooth Ken Burns motion on still images, text hook badges, branding overlay, and BGM.
11. **Synchronized Voiceover Studio & BGM Removal**: Inquires if voiceover is desired. If yes, launches synchronized in-browser recording while the reel plays. Once captured, **completely strips the background music** and replaces it with the voiceover.
12. **Chatbot Review & Revision**: Allows natural language editing instructions (e.g. *"Change hook text to XYZ"*, *"Move logo to Bottom-Right"*), re-rendering the draft reel dynamically.
13. **Final Approval & Download**: Provides one-click instant download of the production-ready MP4.
14. **Security & Sandboxing**: Parameterized FFmpeg subprocess execution (no raw shell injection), MIME validation, and isolated session workspaces.

---

## Project Structure

```
socialMediaengin/
├── app.py                     # Starlette web server (REST, media upload, video streaming)
├── agent.py                   # ReelCreatorAgent deterministic FSM & multimodal reasoning
├── video_engine.py            # FFmpeg video composition (9:16, Ken Burns, overlays, VO swap)
├── audio_engine.py            # Royalty-free BGM catalog & audio track replacement
├── config.py                  # Server configuration, paths, and FFmpeg binary locator
├── test_system.py             # End-to-end automated test suite
├── requirements.md            # Software Requirements Specification
├── architecture.md            # System Architecture Design
│
├── static/                    # Mobile-First Progressive Web App (PWA)
│   ├── index.html             # HTML5 mobile-first application shell
│   ├── style.css              # Creator studio dark theme (100dvh responsive layout)
│   ├── app.js                 # Frontend state, chat rendering, Web Audio MediaRecorder studio
│   ├── manifest.json          # PWA Manifest (standalone 9:16 portrait)
│   ├── sw.js                  # PWA Service Worker for caching
│   └── icons/                 # PWA application icons
│
├── assets/                    # Bundled royalty-free audio tracks
│   ├── track_chill.mp3
│   ├── track_energetic.mp3
│   └── track_cinematic.mp3
│
├── uploads/                   # Sandboxed session upload directories
└── outputs/                   # Rendered draft and final video outputs
```

---

## How to Run

### 1. Run the Automated Test Suite
To verify all 14 requirements end-to-end:
```bash
python test_system.py
```

### 2. Start the Mobile-First Web Studio
To start the web application server:
```bash
python app.py
```
Open your browser at:
`http://localhost:8000`

On mobile devices (iOS Safari or Android Chrome), tap **"Add to Home Screen"** to install it as a standalone full-screen app.

