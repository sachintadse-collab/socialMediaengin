# Reel Creator Agent — Software Requirements Specification (SRS) & Architecture

## 1. Executive Summary
The **Reel Creator Agent** is an interactive, multimodal AI-driven video synthesis platform designed to produce short-form vertical video reels (9:16 aspect ratio for Instagram Reels, TikTok, YouTube Shorts). The system operates strictly via an interactive conversational interface that adheres to a **Zero-Assumption Protocol**—asking clarifying questions for every parameter rather than hallucinating or guessing user intent. It ingests multimedia assets (images, videos, audio), performs multimodal "vibe" and semantic analysis, generates editable copywriting (hooks, scene descriptions, reel captions), provides background music recommendations, incorporates customizable branding overlays, facilitates synchronized in-browser voiceover recording (with automatic BGM removal upon request), supports iterative natural language revisions, and renders production-ready downloadable exports securely.

---

## 2. Recommended Technology Stack & Tools

| Component / Layer | Recommended Technology / Tool | Purpose & Justification |
| :--- | :--- | :--- |
| **Multimodal AI Engine** | **Google Gemini 2.5 / 1.5 Pro & Flash** | Native multimodal understanding across images, video keyframes, and audio tracks; high-context reasoning for aesthetic vibe detection, scene descriptions, and high-converting hooks. |
| **Video Processing Engine** | **FFmpeg (C-binary / FFmpeg CLI) + MoviePy / PyAV** | Robust, industry-standard video manipulation: 9:16 vertical crop/pad, Ken Burns animations, framerate normalization, watermark/branding overlay positioning, and GPU-accelerated encoding (NVENC / QuickSync). |
| **Audio Processing Engine** | **FFmpeg Audio Filters + Librosa / Web Audio API** | Audio waveform visualization, BPM/tempo detection, audio replacement/swapping, loudness normalization (EBU R128), and zero-latency browser recording sync. |
| **Frontend Client (PWA)** | **Mobile-First Progressive Web App (HTML5, Tailwind, ES6)** | Responsive chat UI (optimized for 9:16 mobile screens & desktop), media uploader from camera roll, synchronized audio recording HUD, and PWA installable manifest (`manifest.json` + `sw.js`). |
| **Backend API Service** | **FastAPI (Python 3.11+)** | Asynchronous REST and WebSocket endpoints for low-latency streaming chat interactions, progress tracking, and file streaming. |
| **Task Queue & Worker Pool** | **Celery / Redis / BullMQ** | Offloads resource-heavy video rendering and FFmpeg encoding to background workers to prevent blocking conversational threads. |
| **State & Session Store** | **Redis + PostgreSQL (or SQLite for local dev)** | Manages conversation state machines, step completion flags, asset metadata, and versioned reel edit histories. |
| **Security & Validation** | **Filetype / Magic Byte Checker + Pydantic + ClamAV** | Strict MIME inspection (preventing file spoofing), sanitized file storage, safe command parameterization (preventing FFmpeg argument injection), and session isolation. |

---

## 3. Functional Requirements

### FR-01: Conversational Initiation & Session Setup
* **FR-01.1**: The chatbot shall greet the user and initiate the reel creation workflow upon command or session creation.
* **FR-01.2**: The agent shall present an initial brief explaining required steps and asking the user how they would like to proceed.

### FR-02: Multimodal Media Ingestion
* **FR-02.1**: The media_read agent shall accept images (`.jpg`, `.jpeg`, `.png`, `.webp`), video clips (`.mp4`, `.mov`, `.mkv`), and audio files (`.mp3`, `.wav`, `.aac`).
* **FR-02.2**: The agent shall enforce maximum file size and upload limits per batch (e.g., up to 10 assets, max 200MB per file).
* **FR-02.3**: Uploaded media must be validated via magic bytes (not just file extension) and stored in isolated session folders.
* FR-02.4: After each file is uploaded, the agent should read the media and based on the visual content of the file, it should LLM should gnerate the discription of each image

### FR-03: Vibe & Aesthetic Tone Analysis
* **FR-03.1**: The  media_read agent must extract visual features like what is the media showing (image recognation)
* **FR-03.2**: The  media_read agent shall classify the content's vibe based on the visual content of the media (image or vedio)

### FR-04: Background Music (BGM) Recommendation
* **FR-04.1**: The music agent shall suggest curated, royalty-free audio tracks with mood descriptions and audio preview snippets.
* FR-04.2: In case there are any interferences exist in audio, the music agent should remove those in the audio 
* **FR-04.3**: The music agent shall prompt the user to choose one, upload their own custom track, or proceed without BGM.

### FR-05: Editable Scene-Level Media Descriptions
* **FR-05.1**: For each uploaded image and video clip, the  media_read agent shall generate a concise semantic description and intended narrative sequence.
* **FR-05.2**: The user must be allowed to edit, reorder, or approve the description and timeline order for each asset through the chat interface.

### FR-06: Editable Reel Caption & Description
* **FR-06.1**: The reel agent shall propose an overall caption for the reel (optimized for Instagram Reels / TikTok / YouTube Shorts algorithm with relevant hashtags and call-to-action).
* **FR-06.2**: The user must be able to accept or edit the reel description in chat before proceeding.

### FR-07: Editable High-Converting Hook
* **FR-07.1**: The reel agent shall propose 2–3 attention-grabbing visual/textual hooks for the first 3 seconds of the reel. These hook should be based on the visual content of the each media file. It should not be generic
* **FR-07.2**: The user selects or inputs their preferred hook text and overlay style (font size, banner background, text position).

### FR-08: Branding Overlays & Watermarking
* **FR-08.1**: The branding agent shall ask the user whether a branding logo, handle, or watermark should be included.
* **FR-08.2**: If the user responds affirmatively:
  * Prompt for logo file upload (PNG with transparency supported).
  * Prompt for explicit placement coordinates: *Top-Left, Top-Right, Bottom-Left, Bottom-Right, or Center*, Background
  * Prompt for scale and opacity percentage.

### FR-09: Zero-Assumption Principle
* **FR-09.1**: All the agents shall **never assume** default values for creative or structural choices (e.g., video pacing, branding placement, music selection, hook text).
* **FR-09.2**: If any required parameter is missing or ambiguous, the agent must pause execution and ask the user directly in the chat.

### FR-10: Reel Assembly & Review Generation
* **FR-10.1**: Upon receiving all user confirmations, the backend engine compiles the 9:16 vertical video with smooth transitions, Ken Burns motion on stills, hook overlays, branding, and selected BGM.
* **FR-10.2**: The rendered draft reel is displayed directly inside the chat interface video player for user review.

### FR-11: Synchronized Voiceover Recording & BGM Replacement
* **FR-11.1**: The agent shall ask the user: *"Would you like to record and add a voiceover to this reel?"*
* **FR-11.2**: If the user agrees:
  * The UI activates an interactive studio mode: the draft reel plays while the browser's microphone records audio in real time.
  * The user can re-record or preview the captured voiceover.
* **FR-11.3**: Once the voiceover is confirmed, the system shall **remove the previously added background music** and substitute it completely with the recorded voiceover track (or duck BGM if specified, defaulting strictly to complete replacement per specification).
* **FR-11.4**: A third optipon of removing background music or voiceover should be provided. If chosen by user, the backround music or recorded voice over track should be removed and only the video should be presented

### FR-12: Chatbot-Driven Conversational Revision (Review Loop)
* **FR-12.1**: After reviewing any draft, the user can provide natural language revision instructions in chat, giverned by chat agent
* **FR-12.2**: The chat agent translates the feedback into specific editing instructions using llm, and updates the reel as per the chat input, re-renders the reel, and provides an updated preview.

### FR-13: Final Approval & Secure Download
* **FR-13.1**: When the user types an approval keyword or clicks the "Approve Reel" button, the agent generates the final production-ready MP4 (1080x1920, H.264 video, AAC audio, 30/60 FPS).
* **FR-13.2**: A direct, secure download link is served to the user in chat.

### FR-14: Security, Privacy & Integrity
* **FR-14.1**: Input validation on all user text and uploaded files to prevent prompt injection and remote code execution via malicious media headers.
* **FR-14.2**: User sessions, uploaded media, and generated reels must reside in sandboxed, cryptographically random session directories with automatic expiration / cleanup after 24 hours.
* **FR-14.3**: All FFmpeg executions must be strictly parameterized (avoiding raw shell string concatenation) to prevent command injection vulnerabilities.

---

## 4. State Machine & Conversational Workflow

```
[State 0: Initialization]
       │
       ▼
[State 1: Media Upload & Validation] (Images, Videos, Audio)
       │
       ▼
[State 2: Multimodal Vibe Analysis] ──(Ask User for Vibe Confirmation)
       │
       ▼
[State 3: Music Selection] ──────────(Suggest 3 tracks, Ask User to Pick/Upload)
       │
       ▼
[State 4: Scene Descriptions] ───────(Propose descriptions per media, Ask User to Edit)
       │
       ▼
[State 5: Reel Caption & Description] (Propose post caption, Ask User to Edit)
       │
       ▼
[State 6: Hook Proposal] ────────────(Propose 3 hook variations, Ask User to Pick/Edit)
       │
       ▼
[State 7: Branding Overlay Setup] ───(Ask if logo needed -> Ask position & opacity)
       │
       ▼
[State 8: Initial Reel Rendering] ───(Assemble 9:16 video, Stream draft to Chat UI)
       │
       ▼
[State 9: Voiceover Inquiry] ────────(Ask if voiceover needed)
       ├─────────────────────────────────┐
       ▼ [If YES]                        ▼ [If NO]
[State 10: Play & Record VO]             │
       │                                 │
       ▼                                 │
[State 11: Remove BGM & Mix VO]          │
       │                                 │
       └────────────────┬────────────────┘
                        │
                        ▼
             [State 12: Review & Feedback]
                        │
       ┌────────────────┴───────────────┐
       ▼ [Revision Requested]           ▼ [Approved]
[State 13: Re-render Draft]      [State 14: Final Export & Download]
       ▲            │
       └────────────┘
```

---

## 5. Non-Functional Requirements
1. **Performance**: Initial vibe analysis and copy generation under 5 seconds. Video draft rendering under 25 seconds for a 15–30 second 1080p reel.
2. **Reliability**: Graceful fallback if video encoding fails, providing human-readable error descriptions.
3. **Accessibility**: Responsive UI with mobile and desktop support, featuring high-contrast preview controls.
4. **Data Isolation**: Multi-tenant data segregation ensuring users cannot access or view other sessions' assets.

