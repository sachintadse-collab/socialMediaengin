# Reel Creator Multi-Agent Architecture & Tool Specification

This document details the multi-agent architecture of the **Reel Creator Agent**, specifying each dedicated Agent, its core responsibilities, and the exact tools and libraries it utilizes to fulfill the [Software Requirements Specification (requirements.md)](file:///c:/Users/2026/socialMediaengin/requirements.md).

---

## 1. System Overview & Multi-Agent Flow

The Reel Creator platform is structured as an orchestrated multi-agent network adhering to the **Zero-Assumption Protocol (FR-09)**. Each distinct creative, analytical, audio-visual, and conversational task is governed by a dedicated specialized agent.

```mermaid
graph TD
    User([User / Mobile PWA Client]) --> Coordinator[ReelCoordinatorAgent (Master Orchestrator)]
    
    Coordinator --> MediaRead[MediaReadAgent (FR-02, FR-03, FR-05)]
    Coordinator --> Music[MusicAgent (FR-04, FR-11.3, FR-11.4)]
    Coordinator --> Reel[ReelAgent (FR-06, FR-07)]
    Coordinator --> Branding[BrandingAgent (FR-08)]
    Coordinator --> VideoAssembly[VideoAssemblyAgent (FR-10, FR-11, FR-14.3)]
    Coordinator --> Chat[ChatAgent (FR-12)]
```

---

## 2. Dedicated Agents and Tools Specification

### 1. `MediaReadAgent`
* **File:** [`agents/media_read_agent.py`](file:///c:/Users/2026/socialMediaengin/agents/media_read_agent.py)
* **Functional Requirements Covered:** **FR-02** (Media Ingestion & Magic-Byte Validation), **FR-03** (Vibe & Aesthetic Tone Analysis), **FR-05** (Editable Scene-Level Descriptions).
* **Main Activities:**
  1. Inspects raw file headers using binary magic bytes (`JPEG`, `PNG`, `WebP`, `MP4`, `MKV`, `WAV`, `MP3`) to prevent file-spoofing and enforce 200MB limits.
  2. Extracts visual features from media: per-pixel dominant colors, texture variance, white/silver thread and tassel work, contrasting borders, and spatial composition.
  3. Classifies overall aesthetic vibe (e.g., `Royal Silk & Handloom Saree Collection`, `Wanderlust & Scenic Travel Vista`, `Creator Lifestyle & Confident Mood`).
  4. Generates bespoke, visually true descriptions for every individual uploaded image/video clip (no generic templates).
* **Tools & Libraries Used:**
  * **Google Gemini 1.5/2.5 Flash Multimodal Vision API:** Deep visual understanding and contextual scene description.
  * **Pillow (`PIL.Image`):** Per-pixel RGB/HSV color-space analysis, dominant chromatic hue bucketing, and regional contrast calculations.
  * **OpenCV (`cv2`):** Laplacian edge variance (`cv2.Laplacian`) for weave texture scoring and video keyframe extraction (`cv2.VideoCapture`).
  * **Magic Byte Signature Checker:** Binary header validation against RFC MIME specifications (FR-14.1).

---

### 2. `MusicAgent`
* **File:** [`agents/music_agent.py`](file:///c:/Users/2026/socialMediaengin/agents/music_agent.py)
* **Functional Requirements Covered:** **FR-04** (BGM Recommendation & Interference Removal), **FR-11.3** (Voiceover Substitution & BGM Stripping), **FR-11.4** (Silent Video Muting).
* **Main Activities:**
  1. Dynamically discovers and catalogs all audio assets in `assets/`, scoring and sorting them against the user's locked vibe.
  2. Cleans audio interference, hum, hiss, and ambient noise from recorded voiceover or custom audio (FR-04.2).
  3. Trims and loops audio to match the exact duration of the 9:16 vertical reel without truncation artifacts.
  4. Manages audio replacement: substitutes BGM with voiceover or creates silent video reels upon user request (FR-11.4).
* **Tools & Libraries Used:**
  * **FFmpeg Audio Engine (`ffmpeg`):**
    * `afftdn`: Adaptive FFT-based noise reduction filter to eliminate recording interference.
    * `highpass=f=60,lowpass=f=12000`: Bandpass filter to isolate vocal frequencies.
    * `loudnorm=I=-16:TP=-1.5:LRA=11`: EBU R128 loudness normalization.
    * `-stream_loop -1`: Seamless background music looping.
    * `atrim=0:{duration}`: Sub-millisecond audio duration trimming.
    * `-an`: Audio stream removal for silent video mode.
  * **Python URL & Path Encoders (`urllib.parse`):** Safe audio stream serving for mobile audio players.

---

### 3. `ReelAgent`
* **File:** [`agents/reel_agent.py`](file:///c:/Users/2026/socialMediaengin/agents/reel_agent.py)
* **Functional Requirements Covered:** **FR-06** (Editable Reel Caption & Description), **FR-07** (Editable High-Converting Hook).
* **Main Activities:**
  1. Drafts 4–6 diverse, high-converting caption styles (Poetic Heritage, Boutique & Shop Now, Short & Aesthetic, Viral Poll) with targeted hashtags and call-to-actions.
  2. Crafts 2–3+ attention-grabbing viral hooks for the first 3 seconds of the reel based directly on the visual elements of the uploaded assets (never generic).
  3. Provides in-place caption and hook variation cycling (`🔄 Regenerate`) without advancing state until explicit approval.
* **Tools & Libraries Used:**
  * **Google Gemini Generative AI:** Dynamic copywriting generation matching tone, genre, and social media platform algorithms.
  * **Viral Hook Pattern Matrix:** Behavioral hook templates categorized by content genre (Ethnic textiles, Travel, Culinary, Fitness, Luxury).
  * **Hashtag Taxonomy Engine:** Curated hashtag clusters optimized for Instagram Reels, TikTok, and YouTube Shorts discoverability.

---

### 4. `BrandingAgent`
* **File:** [`agents/branding_agent.py`](file:///c:/Users/2026/socialMediaengin/agents/branding_agent.py)
* **Functional Requirements Covered:** **FR-08** (Branding Overlays & Watermarking).
* **Main Activities:**
  1. Manages brand logo / watermark inquiries and validation.
  2. Calculates coordinates for 6 supported placement positions: **Top-Left, Top-Right, Bottom-Left, Bottom-Right, Center, Background**.
  3. Prepares scaled, opacity-adjusted RGBA logo overlays (preserving alpha transparency).
* **Tools & Libraries Used:**
  * **Pillow (`PIL.Image`, `PIL.ImageResampling.LANCZOS`):** High-quality bicubic/Lanczos logo downscaling with aspect ratio preservation.
  * **Alpha Channel Manipulator:** Per-pixel alpha scaling for customizable opacity (e.g., 20% for subtle background watermarks, 90% for corner badges).
  * **FFmpeg Coordinate Resolver:** Mathematical coordinate expressions (`(W-w)/2`, `H-h-pad`, etc.) for FFmpeg overlay filters.

---

### 5. `VideoAssemblyAgent`
* **File:** [`agents/video_assembly_agent.py`](file:///c:/Users/2026/socialMediaengin/agents/video_assembly_agent.py)
* **Functional Requirements Covered:** **FR-10** (Reel Assembly & Review Generation), **FR-11** (Voiceover Sync), **FR-14.3** (Safe Parameterized FFmpeg Execution).
* **Main Activities:**
  1. Standardizes all media (photos and video clips) into 1080x1920 (9:16 vertical aspect ratio, 30 FPS).
  2. Applies smooth Ken Burns motion (alternating pan and zoom) to still images.
  3. Renders 100% transparent floating typography for the viral hook banner during the first 3 seconds (no background box).
  4. Renders 100% transparent floating subtitle badges for each scene description at the bottom of the frame.
  5. Composites branding overlays and synchronized audio streams with strict argument parameterization to eliminate shell injection risks.
* **Tools & Libraries Used:**
  * **FFmpeg 7.1 C-Binary:**
    * `zoompan`: Smooth Ken Burns pan-and-zoom motion on still images.
    * `scale` & `pad`: 9:16 aspect ratio standardization.
    * `overlay`: Time-gated hook banner and watermark composition.
    * `libx264`: High-efficiency H.264 video encoding (`yuv420p`, CRF 22).
  * **Pillow (`PIL.ImageDraw`, `PIL.ImageFont`):** Transparent RGBA graphics rendering with drop shadows and dark stroke outlines for mobile contrast.

---

### 6. `ChatAgent`
* **File:** [`agents/chat_agent.py`](file:///c:/Users/2026/socialMediaengin/agents/chat_agent.py)
* **Functional Requirements Covered:** **FR-12** (Chatbot-Driven Conversational Revision Review Loop).
* **Main Activities:**
  1. Governs the conversational review loop once a draft reel is rendered.
  2. Interprets natural language user instructions (e.g., *"Change hook to XYZ"*, *"Move logo to Bottom-Right"*, *"Switch music to Royal Sitar"*, *"Mute audio"*, *"Record voiceover"*).
  3. Safely extracts parameter updates without clobbering hook or captions with casual conversational text.
  4. Triggers re-renders and delivers updated video previews in the chat stream.
* **Tools & Libraries Used:**
  * **Google Gemini Conversational AI:** Natural language intent classification and structured parameter extraction.
  * **Deterministic NLP Intent Parser:** Regex-based intent extraction fallback for offline execution.

---

### 7. `ReelCoordinatorAgent` (Master Orchestrator)
* **File:** [`agents/coordinator.py`](file:///c:/Users/2026/socialMediaengin/agents/coordinator.py)
* **Functional Requirements Covered:** **FR-01** (Initiation & Setup), **FR-09** (Zero-Assumption Protocol), **FR-13** (Final Approval & Download), **FR-14** (Security & Session Isolation).
* **Main Activities:**
  1. Tracks the dialogue state machine across all 14 states (State 0: Init through State 14: Approved).
  2. Strictly enforces the **Zero-Assumption Principle**: never assumes parameters; always presents options and requires user confirmation before proceeding.
  3. Isolates all session assets inside cryptographic sandboxes (`uploads/<session_id>` and `outputs/<session_id>`).
  4. Serves production-ready MP4 download links upon approval.
* **Tools & Libraries Used:**
  * **Starlette & Uvicorn:** Asynchronous ASGI web framework and server.
  * **Python `uuid`:** Cryptographic session generation.
  * **PWA Engine:** Mobile-first progressive web application with `manifest.json` and `sw.js`.

---

## 3. Agent vs. Tool Matrix

| Agent | Primary Activity | Core Tools & Technologies | SRS Requirements |
| :--- | :--- | :--- | :--- |
| **`MediaReadAgent`** | Ingestion, validation, visual feature recognition, vibe classification, scene descriptions | Gemini Vision API, Pillow, OpenCV, Magic-Byte Checker | FR-02, FR-03, FR-05 |
| **`MusicAgent`** | Audio curation, preview serving, interference cleaning, voiceover/BGM swapping & muting | FFmpeg (`afftdn`, `atrim`, `stream_loop`, `-an`), Dynamic Asset Scanner | FR-04, FR-11.3, FR-11.4 |
| **`ReelAgent`** | Algorithm-optimized captions, hashtag clustering, visual-content-aware viral hooks | Gemini Text Model, Viral Hook Matrix, Hashtag Taxonomy Engine | FR-06, FR-07 |
| **`BrandingAgent`** | Logo upload validation, placement coordinate calculation, opacity & scale management | Pillow RGBA Processor, Lanczos Resampler, FFmpeg Overlay Mapper | FR-08 |
| **`VideoAssemblyAgent`** | 9:16 vertical video synthesis, Ken Burns motion, transparent overlays, audio mixing | FFmpeg 7.1 (`libx264`, `zoompan`, `overlay`), Pillow ImageDraw/Font | FR-10, FR-11, FR-14.3 |
| **`ChatAgent`** | Review loop feedback interpretation, intent translation, re-render coordination | Gemini Chat Model, Deterministic NLP Matcher | FR-12 |
| **`ReelCoordinatorAgent`** | Master orchestration, 14-state dialogue graph, Zero-Assumption enforcement, secure export | Starlette ASGI, Uvicorn, Python UUID, PWA Service Worker | FR-01, FR-09, FR-13, FR-14 |

