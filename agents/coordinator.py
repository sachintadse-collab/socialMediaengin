"""
ReelCoordinatorAgent: Master Multi-Agent Orchestrator strictly executing the
Deterministic Finite State Machine and Zero-Assumption Protocol (FR-01 through FR-14).
Delegates specialized tasks to:
- MediaReadAgent (FR-02, FR-03, FR-05)
- MusicAgent (FR-04, FR-11.3, FR-11.4)
- ReelAgent (FR-06, FR-07)
- BrandingAgent (FR-08)
- VideoAssemblyAgent (FR-10, FR-11)
- ChatAgent (FR-12)
"""
import uuid
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from config import UPLOADS_DIR, OUTPUTS_DIR, ALLOWED_EXTENSIONS
from agents.media_read_agent import MediaReadAgent
from agents.music_agent import MusicAgent
from agents.reel_agent import ReelAgent
from agents.branding_agent import BrandingAgent
from agents.video_assembly_agent import VideoAssemblyAgent
from agents.chat_agent import ChatAgent

# Dialogue State Constants (Mapping 1-to-1 to Section 4 of requirements.md)
STATE_INIT = "INIT"                                   # State 0
STATE_AWAITING_MEDIA = "AWAITING_MEDIA"               # State 1
STATE_CONFIRM_VIBE = "CONFIRM_VIBE"                   # State 2
STATE_SELECT_BGM = "SELECT_BGM"                       # State 3
STATE_EDIT_SCENE_DESCRIPTIONS = "EDIT_SCENE_DESCRIPTIONS" # State 4
STATE_EDIT_REEL_CAPTION = "EDIT_REEL_CAPTION"         # State 5
STATE_SELECT_HOOK = "SELECT_HOOK"                     # State 6
STATE_BRANDING_INQUIRY = "BRANDING_INQUIRY"           # State 7a
STATE_BRANDING_POSITION = "BRANDING_POSITION"         # State 7b
STATE_VOICEOVER_INQUIRY = "VOICEOVER_INQUIRY"         # State 8 & 9
STATE_VOICEOVER_RECORDING = "VOICEOVER_RECORDING"     # State 10
STATE_REVIEW_AND_FEEDBACK = "REVIEW_AND_FEEDBACK"     # State 11, 12, 13
STATE_APPROVED = "APPROVED"                           # State 14

class ReelSession:
    """Manages isolated cryptographic session storage and state machine tracking (FR-14.2)."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_dir = UPLOADS_DIR / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.reset()

    def reset(self):
        """Resets session to clean slate."""
        self.state = STATE_INIT
        self.uploaded_media: List[Path] = []
        self.vibe: Optional[str] = None
        self.detected_category: str = "aesthetic"
        self.bgm_track_id: Optional[str] = None
        self.custom_bgm_file: Optional[Path] = None
        self.mute_audio: bool = False
        self.scene_descriptions: List[str] = []
        self.scene_tags: List[str] = []
        self.reel_caption: Optional[str] = None
        self.caption_options: List[Dict[str, str]] = []
        self.caption_cycle: int = 0
        self.proposed_hooks: List[str] = []
        self.hook_cycle: int = 0
        self.selected_hook: Optional[str] = None
        self.has_branding: Optional[bool] = None
        self.branding_file: Optional[Path] = None
        self.branding_position: str = "Top-Right"
        self.branding_opacity: float = 0.90
        self.voiceover_file: Optional[Path] = None
        self.current_reel_path: Optional[Path] = None
        self.reel_version = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "state": self.state,
            "media_count": len(self.uploaded_media),
            "vibe": self.vibe,
            "bgm_track_id": self.bgm_track_id,
            "scene_descriptions": self.scene_descriptions,
            "reel_caption": self.reel_caption,
            "selected_hook": self.selected_hook,
            "has_branding": self.has_branding,
            "branding_position": self.branding_position,
            "reel_version": self.reel_version,
            "has_reel": self.current_reel_path is not None and self.current_reel_path.exists()
        }

class ReelCoordinatorAgent:
    """
    Main Multi-Agent Coordinator governing:
    - FR-01: Conversational Initiation & Zero-Assumption Protocol
    - Multi-agent task delegation across MediaReadAgent, MusicAgent, ReelAgent,
      BrandingAgent, VideoAssemblyAgent, and ChatAgent
    - FR-13: Production export & secure downloads
    - FR-14: Multi-tenant isolated storage & input sanitation
    """

    def __init__(self):
        self.sessions: Dict[str, ReelSession] = {}
        # Specialized Sub-Agents
        self.media_read_agent = MediaReadAgent()
        self.music_agent = MusicAgent()
        self.reel_agent = ReelAgent()
        self.branding_agent = BrandingAgent()
        self.video_assembly_agent = VideoAssemblyAgent()
        self.chat_agent = ChatAgent()

    def get_or_create_session(self, session_id: Optional[str] = None) -> ReelSession:
        if not session_id:
            new_id = str(uuid.uuid4())[:8]
            session = ReelSession(new_id)
            self.sessions[new_id] = session
            return session
        if session_id not in self.sessions:
            session = ReelSession(session_id)
            self.sessions[session_id] = session
            return session
        return self.sessions[session_id]

    def get_media_thumbnail_url(self, session_id: str, media_path: Path) -> str:
        """Returns relative URL to display media thumbnail in chat."""
        ext = media_path.suffix.lower()
        if ext in ALLOWED_EXTENSIONS["image"]:
            return f"/uploads/{session_id}/{media_path.name}"
        else:
            thumb_name = f"{media_path.name}.thumb.jpg"
            thumb_file = media_path.with_name(thumb_name)
            return f"/uploads/{session_id}/{thumb_name}"

    # Delegate helper methods for backward compatibility
    def extract_visual_profile(self, img, filename: str) -> Dict[str, Any]:
        return self.media_read_agent.extract_visual_profile(img, filename)

    def analyze_media_multimodal(self, session: ReelSession) -> Dict[str, Any]:
        return self.media_read_agent.analyze_media_batch(session.uploaded_media)

    def get_caption_variations(self, category: str, vibe: Optional[str] = None, cycle_offset: int = 0):
        return self.reel_agent.get_caption_variations(category, vibe, cycle_offset)

    def get_hook_variations(self, category: str, vibe: Optional[str] = None, cycle_offset: int = 0):
        return self.reel_agent.get_hook_variations(category, vibe, cycle_offset)

    def process_message(
        self,
        session: ReelSession,
        user_message: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes State Machine transitions adhering strictly to the Zero-Assumption Protocol (FR-09).
        Never guesses an answer; always asks the user directly.
        """
        payload = payload or {}
        msg_clean = user_message.strip()
        state = session.state
        lower_msg = msg_clean.lower()

        # GLOBAL COMMAND 1: START OVER / NEW REEL
        if any(cmd in lower_msg for cmd in ["new reel", "restart", "start over", "reset", "start fresh", "another reel", "create new"]):
            session.reset()
            return {
                "text": (
                    "🔄 **Starting a Fresh Reel Creation Session!**\n\n"
                    "All previous media and settings have been cleared.\n\n"
                    "📸 **Please upload your media files** (pictures, video clips, or audio tracks) using the box below or the 📎 attach button to begin."
                ),
                "state": session.state,
                "action_required": "upload_media",
                "interactive_type": "file_upload"
            }

        # STATE 0: INITIAL GREETING (FR-01)
        if state == STATE_INIT:
            session.state = STATE_AWAITING_MEDIA
            return {
                "text": (
                    "👋 Welcome to the **Reel Creator Agent**!\n\n"
                    "I will guide you step-by-step to craft a high-converting, professional 9:16 vertical reel. "
                    "Per our **Zero-Assumption Protocol**, I will never guess your preferences—we will review and customize every detail together.\n\n"
                    "📸 **To get started, please upload your media files** (pictures, video clips, or audio tracks)."
                ),
                "state": session.state,
                "action_required": "upload_media",
                "interactive_type": "file_upload"
            }

        # STATE 1: MEDIA UPLOAD & VALIDATION (FR-02) -> ANALYZE VIBE (FR-03)
        if state == STATE_AWAITING_MEDIA:
            if not session.uploaded_media:
                return {
                    "text": (
                        "📸 **Please upload your media files to get started!**\n\n"
                        "Tap the box below or click the 📁 attach button to select your pictures, video clips, or audio tracks."
                    ),
                    "state": session.state,
                    "action_required": "upload_media",
                    "interactive_type": "file_upload"
                }

            # Delegate to MediaReadAgent
            analysis = self.media_read_agent.analyze_media_batch(session.uploaded_media)
            session.vibe = analysis.get("vibe", "Vibrant & Aesthetic")
            session.scene_descriptions = analysis.get("scene_descriptions", [])
            session.scene_tags = analysis.get("scene_tags", [])
            session.detected_category = analysis.get("category", "aesthetic")

            session.state = STATE_CONFIRM_VIBE

            return {
                "text": (
                    f"✨ **Multimodal Content Analysis Complete!**\n\n"
                    f"Based on your {len(session.uploaded_media)} uploaded asset(s), the MediaReadAgent detected the following aesthetic vibe:\n\n"
                    f"🎭 **Detected Vibe:** `{session.vibe}`\n\n"
                    "Does this vibe match your creative vision, or would you like to customize it?"
                ),
                "state": session.state,
                "interactive_type": "confirm_vibe",
                "media_previews": [
                    {
                        "file_name": p.name,
                        "thumbnail_url": self.get_media_thumbnail_url(session.session_id, p)
                    }
                    for p in session.uploaded_media
                ],
                "options": analysis.get("options", [
                    f"✅ Yes, proceed with '{session.vibe}'",
                    "⚡ Make it Energetic & Upbeat",
                    "☕ Make it Chill & Lo-Fi",
                    "🎬 Make it Cinematic & Dramatic"
                ]),
                "vibe": session.vibe
            }

        # STATE 2: VIBE CONFIRMATION -> SUGGEST BGM (FR-04)
        if state == STATE_CONFIRM_VIBE:
            if payload.get("custom_vibe"):
                session.vibe = payload["custom_vibe"].strip()
            elif msg_clean.startswith("✅") or "yes" in lower_msg or "proceed" in lower_msg:
                pass # Keep detected vibe
            elif msg_clean:
                cleaned = msg_clean.lstrip("🥻✨🌿⚡☕🎬💎🔥🏆🌃🎞️🌧️🏢🖤 ").strip()
                session.vibe = cleaned

            # Delegate to MusicAgent
            recommendations = self.music_agent.get_bgm_recommendations(session.vibe or "")
            session.state = STATE_SELECT_BGM

            return {
                "text": (
                    f"🎵 **Background Music Selection**\n\n"
                    f"Locked vibe: **{session.vibe}**.\n\n"
                    f"The MusicAgent suggested **{len(recommendations)} available tracks** from your library matched to your rhythm and tone. "
                    "You can preview them below, select one, upload your own track, or proceed without BGM:"
                ),
                "state": session.state,
                "interactive_type": "select_bgm",
                "tracks": recommendations
            }

        # STATE 3: BGM SELECTED -> PROPOSE EDITABLE SCENE DESCRIPTIONS (FR-05)
        if state == STATE_SELECT_BGM:
            selected_track_id = payload.get("track_id")
            if payload.get("mute_audio") or "no music" in lower_msg or "without music" in lower_msg:
                session.bgm_track_id = None
                session.mute_audio = True
            else:
                all_tracks = self.music_agent.get_all_library_tracks()
                if not selected_track_id:
                    for track in all_tracks:
                        if track["id"].lower() in lower_msg or track["title"].lower() in lower_msg:
                            selected_track_id = track["id"]
                            break

                if not selected_track_id:
                    return {
                        "text": "⚠️ Please select one of the suggested background music tracks, upload your own audio file, or click 'Proceed without BGM' to continue.",
                        "state": session.state,
                        "interactive_type": "select_bgm",
                        "tracks": self.music_agent.get_bgm_recommendations(session.vibe or "")
                    }
                session.bgm_track_id = selected_track_id
                session.mute_audio = False

            session.state = STATE_EDIT_SCENE_DESCRIPTIONS

            # Propose editable descriptions per media file (FR-05.1)
            return {
                "text": (
                    f"🎶 Background music locked in!\n\n"
                    f"📝 **Proposed Media Descriptions**\n\n"
                    "The MediaReadAgent generated these bespoke descriptions based on the visual elements of each asset. "
                    "Review or edit each description directly below the media preview, or click **Approve Descriptions** to continue:"
                ),
                "state": session.state,
                "interactive_type": "edit_scene_descriptions",
                "scenes": [
                    {
                        "index": i,
                        "file_name": session.uploaded_media[i].name if i < len(session.uploaded_media) else f"Scene {i+1}",
                        "thumbnail_url": self.get_media_thumbnail_url(session.session_id, session.uploaded_media[i]) if i < len(session.uploaded_media) else "",
                        "theme_badge": session.scene_tags[i] if i < len(session.scene_tags) else "Scene Highlight",
                        "description": desc
                    }
                    for i, desc in enumerate(session.scene_descriptions)
                ]
            }

        # STATE 4: SCENE DESCRIPTIONS APPROVED -> PROPOSE REEL CAPTION (FR-06)
        if state == STATE_EDIT_SCENE_DESCRIPTIONS:
            if payload.get("scene_descriptions"):
                session.scene_descriptions = payload["scene_descriptions"]

            session.state = STATE_EDIT_REEL_CAPTION
            category = session.detected_category
            caption_options = self.reel_agent.get_caption_variations(category, session.vibe)
            session.caption_options = caption_options

            if not session.reel_caption or session.reel_caption == "None":
                session.reel_caption = caption_options[0]["caption"]

            return {
                "text": (
                    "✅ Media descriptions approved!\n\n"
                    "✍️ **Proposed Reel Caption & Hashtags**\n\n"
                    "The ReelAgent drafted high-converting captions for your post. "
                    "Select a style chip below, edit in the box, or click **🔄 Regenerate** for fresh options:"
                ),
                "state": session.state,
                "interactive_type": "edit_reel_caption",
                "caption": session.reel_caption,
                "caption_options": caption_options
            }

        # STATE 5: REEL CAPTION APPROVED -> PROPOSE VIRAL HOOKS (FR-07)
        if state == STATE_EDIT_REEL_CAPTION:
            is_approval = (
                payload.get("action") == "approve_caption"
                or any(w in lower_msg for w in ["approve", "approved", "looks good", "confirm", "proceed", "continue", "next", "finalize", "done", "use this", "keep this", "save caption"])
                or (msg_clean.startswith("✅") and "approve" in lower_msg)
            )

            is_regen = (
                payload.get("action") == "regenerate_caption"
                or any(w in lower_msg for w in ["regenerate", "different", "another", "more option", "change caption", "fresh", "variation", "roll again"])
            )

            category = session.detected_category

            if is_regen and not is_approval:
                session.caption_cycle += 1
                caption_options = self.reel_agent.get_caption_variations(category, session.vibe, cycle_offset=session.caption_cycle)
                session.caption_options = caption_options
                session.reel_caption = caption_options[0]["caption"]
                return {
                    "text": (
                        "🔄 **Fresh Caption Variations Generated!**\n\n"
                        "Select any style chip below, edit directly in the box, or click **✅ Approve Caption** when ready:"
                    ),
                    "state": session.state,
                    "interactive_type": "edit_reel_caption",
                    "caption": session.reel_caption,
                    "caption_options": caption_options
                }

            if not is_approval:
                if msg_clean and not msg_clean.startswith("✅"):
                    session.reel_caption = msg_clean
                caption_options = session.caption_options or self.reel_agent.get_caption_variations(category, session.vibe)
                return {
                    "text": (
                        "✍️ **Updated Reel Caption:**\n\n"
                        "I've updated your caption below. Click **✅ Approve Caption** to proceed to hook selection, or keep editing:"
                    ),
                    "state": session.state,
                    "interactive_type": "edit_reel_caption",
                    "caption": session.reel_caption,
                    "caption_options": caption_options
                }

            # EXPLICIT APPROVAL -> ADVANCE TO HOOK SELECTION (FR-07)
            if payload.get("reel_caption"):
                session.reel_caption = payload["reel_caption"].strip()

            session.state = STATE_SELECT_HOOK
            session.proposed_hooks = self.reel_agent.get_hook_variations(category, session.vibe, cycle_offset=session.hook_cycle)

            return {
                "text": (
                    "📌 **High-Converting Hook Selection**\n\n"
                    "The first 3 seconds determine whether viewers keep watching or scroll away. "
                    "The ReelAgent crafted these hooks specifically from your media's visual elements. "
                    "Choose one, write your own custom text, or click **🔄 Regenerate Hooks**:"
                ),
                "state": session.state,
                "interactive_type": "select_hook",
                "hooks": session.proposed_hooks
            }

        # STATE 6: HOOK SELECTED -> BRANDING INQUIRY (FR-08)
        if state == STATE_SELECT_HOOK:
            is_regen = (
                payload.get("action") == "regenerate_hooks"
                or any(w in lower_msg for w in ["regenerate", "different hook", "another hook", "new hook", "more hook", "fresh hook", "other hook", "roll again"])
            )

            if is_regen:
                category = session.detected_category
                session.hook_cycle += 1
                hooks = self.reel_agent.get_hook_variations(category, session.vibe, cycle_offset=session.hook_cycle)
                session.proposed_hooks = hooks
                return {
                    "text": (
                        "🔄 **Fresh Viral Hook Options Generated!**\n\n"
                        "Select your favorite hook below, enter a custom one, or click **🔄 Regenerate Hooks** for more options:"
                    ),
                    "state": session.state,
                    "interactive_type": "select_hook",
                    "hooks": session.proposed_hooks
                }

            chosen_hook = payload.get("hook_text") or msg_clean
            if not chosen_hook or chosen_hook.lower() in ["select", "choose"]:
                return {
                    "text": "⚠️ Please select a hook or type your preferred hook text in the chat.",
                    "state": session.state,
                    "interactive_type": "select_hook",
                    "hooks": session.proposed_hooks
                }

            session.selected_hook = chosen_hook
            session.state = STATE_BRANDING_INQUIRY

            return {
                "text": (
                    f"🎯 Selected Hook: *\"{session.selected_hook}\"*\n\n"
                    "🏷️ **Branding & Watermark Overlay**\n\n"
                    "The BrandingAgent wants to know: Would you like to include your brand logo or watermark in this reel?"
                ),
                "state": session.state,
                "interactive_type": "branding_inquiry",
                "options": [
                    "🖼️ Yes, I have a logo to upload",
                    "❌ No, proceed without branding"
                ]
            }

        # STATE 7: BRANDING DECISION -> LOGO UPLOAD & POSITION (FR-08)
        if state == STATE_BRANDING_INQUIRY:
            has_brand = payload.get("has_branding")
            if has_brand is None:
                has_brand = "yes" in lower_msg or "logo" in lower_msg

            session.has_branding = has_brand

            if has_brand:
                session.state = STATE_BRANDING_POSITION
                return {
                    "text": (
                        "🌟 Great! Please upload your logo image (PNG with transparency recommended) "
                        "and select where you would like it positioned on the screen (Top-Left, Top-Right, Bottom-Left, Bottom-Right, Center, Background):"
                    ),
                    "state": session.state,
                    "interactive_type": "branding_upload_and_position",
                    "positions": ["Top-Right", "Top-Left", "Bottom-Right", "Bottom-Left", "Center", "Background"]
                }
            else:
                return self.render_draft_reel(session)

        # STATE 8: BRANDING POSITION CONFIRMED -> RENDER INITIAL REEL (FR-10)
        if state == STATE_BRANDING_POSITION:
            if payload.get("position"):
                session.branding_position = payload["position"]
            elif any(p.lower() in lower_msg for p in ["top-right", "top-left", "bottom-right", "bottom-left", "center", "background"]):
                for p in ["Top-Right", "Top-Left", "Bottom-Right", "Bottom-Left", "Center", "Background"]:
                    if p.lower() in lower_msg:
                        session.branding_position = p
                        break

            if payload.get("opacity"):
                try:
                    session.branding_opacity = float(payload["opacity"])
                except Exception:
                    pass

            return self.render_draft_reel(session)

        # STATE 9: VOICEOVER INQUIRY (FR-11)
        if state == STATE_VOICEOVER_INQUIRY:
            wants_vo = payload.get("wants_voiceover")
            if wants_vo is None:
                wants_vo = "yes" in lower_msg or "record" in lower_msg

            if wants_vo:
                session.state = STATE_VOICEOVER_RECORDING
                return {
                    "text": (
                        "🎙️ **Synchronized Voiceover Studio Activated**\n\n"
                        "Click **'Open Voiceover Studio'** below. The reel will play in real time while you record your voice. "
                        "When finished, the MusicAgent will **completely remove the background music** and replace it with your clean voiceover!"
                    ),
                    "state": session.state,
                    "interactive_type": "record_voiceover",
                    "reel_url": f"/outputs/{session.session_id}/draft_reel_v{session.reel_version}.mp4"
                }
            else:
                session.state = STATE_REVIEW_AND_FEEDBACK
                return {
                    "text": (
                        "🎬 Your reel is ready for review!\n\n"
                        "You can inspect it above. If you'd like any edits, just tell the ChatAgent what to change "
                        "(e.g., *'Change hook text to XYZ'*, *'Move logo to Bottom-Right'*, *'Swap music'*, *'Mute audio'*). "
                        "Or, if it's ready, click **Approve & Download**!"
                    ),
                    "state": session.state,
                    "interactive_type": "review_and_feedback",
                    "reel_url": f"/outputs/{session.session_id}/draft_reel_v{session.reel_version}.mp4"
                }

        # STATE 10, 11, 12, 13: REVIEW & NATURAL LANGUAGE EDITING LOOP (FR-12)
        if state in [STATE_REVIEW_AND_FEEDBACK, STATE_APPROVED]:
            current_state_info = {
                "hook": session.selected_hook,
                "caption": session.reel_caption,
                "bgm_id": session.bgm_track_id,
                "has_branding": session.has_branding,
                "branding_position": session.branding_position
            }

            # Delegate to ChatAgent
            feedback = self.chat_agent.process_review_feedback(msg_clean, current_state_info)

            if feedback.get("is_approval"):
                session.state = STATE_APPROVED
                return {
                    "text": feedback.get("reply_message", "🎉 Reel Approved!"),
                    "state": session.state,
                    "interactive_type": "download_final",
                    "download_url": f"/outputs/{session.session_id}/draft_reel_v{session.reel_version}.mp4",
                    "caption": session.reel_caption
                }

            if feedback.get("wants_voiceover"):
                session.state = STATE_VOICEOVER_RECORDING
                return {
                    "text": feedback.get("reply_message"),
                    "state": session.state,
                    "interactive_type": "record_voiceover",
                    "reel_url": f"/outputs/{session.session_id}/draft_reel_v{session.reel_version}.mp4"
                }

            if feedback.get("needs_rerender"):
                if feedback.get("new_hook") is not None:
                    session.selected_hook = feedback["new_hook"]
                if feedback.get("new_caption") is not None:
                    session.reel_caption = feedback["new_caption"]
                if "new_bgm_track_id" in feedback:
                    session.bgm_track_id = feedback["new_bgm_track_id"]
                    session.voiceover_file = None
                if feedback.get("remove_branding"):
                    session.has_branding = False
                elif feedback.get("new_branding_pos"):
                    session.has_branding = True
                    session.branding_position = feedback["new_branding_pos"]
                if feedback.get("mute_audio"):
                    session.mute_audio = True
                    session.bgm_track_id = None
                    session.voiceover_file = None

                return self.rerender_draft_reel(session, feedback.get("reply_message", "🔄 Reel updated!"))

            return {
                "text": feedback.get("reply_message"),
                "state": session.state,
                "interactive_type": "review_and_feedback",
                "reel_url": f"/outputs/{session.session_id}/draft_reel_v{session.reel_version}.mp4"
            }

        return {
            "text": (
                f"I received: *\"{msg_clean}\"*\n\n"
                f"We are currently at step: **{session.state.replace('_', ' ').title()}**.\n"
                "Please choose one of the options above or use the 📎 button to provide the necessary input!"
            ),
            "state": session.state
        }

    def render_draft_reel(self, session: ReelSession) -> Dict[str, Any]:
        """Delegates compilation to VideoAssemblyAgent and advances to Voiceover Inquiry."""
        session_out_dir = OUTPUTS_DIR / session.session_id
        session_out_dir.mkdir(parents=True, exist_ok=True)
        
        output_name = f"draft_reel_v{session.reel_version}.mp4"
        bgm_path = self.music_agent.get_track_path_by_id(session.bgm_track_id or "")

        success, output_path, msg = self.video_assembly_agent.assemble_reel(
            session_dir=session_out_dir,
            media_files=session.uploaded_media,
            scene_descriptions=session.scene_descriptions,
            hook_text=session.selected_hook,
            branding_file=session.branding_file if session.has_branding else None,
            branding_position=session.branding_position,
            branding_opacity=session.branding_opacity,
            bgm_file=bgm_path,
            output_filename=output_name,
            vibe=session.vibe,
            scene_tags=session.scene_tags,
            mute_audio=session.mute_audio
        )

        if not success:
            return {
                "text": f"❌ Error assembling video: {msg}. Please check the media files.",
                "state": session.state
            }

        session.current_reel_path = output_path
        session.state = STATE_VOICEOVER_INQUIRY

        return {
            "text": (
                "🎉 **Your Draft Reel Has Been Generated!**\n\n"
                f"• **Vibe:** `{session.vibe}`\n"
                f"• **Hook:** *\"{session.selected_hook}\"*\n"
                f"• **Music:** `{session.bgm_track_id if not session.mute_audio else 'Muted / Silent'}`\n"
                f"• **Branding:** `{'Included (' + session.branding_position + ')' if session.has_branding else 'None'}`\n\n"
                "🎥 Take a look at the preview above.\n\n"
                "**Would you like to record a custom voiceover for this reel?**"
            ),
            "state": session.state,
            "interactive_type": "voiceover_inquiry",
            "reel_url": f"/outputs/{session.session_id}/{output_name}",
            "options": [
                "🎙️ Yes, I want to record a voiceover",
                "➡️ No, proceed with background music",
                "🔇 Proceed with Silent Reel (No Music / No Voiceover)"
            ]
        }

    def rerender_draft_reel(self, session: ReelSession, message: str) -> Dict[str, Any]:
        """Re-renders draft reel when edits are made during review loop."""
        session.reel_version += 1
        session_out_dir = OUTPUTS_DIR / session.session_id
        output_name = f"draft_reel_v{session.reel_version}.mp4"

        if session.voiceover_file and session.voiceover_file.exists():
            bgm_path = None
        elif session.mute_audio:
            bgm_path = None
        else:
            bgm_path = self.music_agent.get_track_path_by_id(session.bgm_track_id or "")

        success, output_path, msg = self.video_assembly_agent.assemble_reel(
            session_dir=session_out_dir,
            media_files=session.uploaded_media,
            scene_descriptions=session.scene_descriptions,
            hook_text=session.selected_hook,
            branding_file=session.branding_file if session.has_branding else None,
            branding_position=session.branding_position,
            branding_opacity=session.branding_opacity,
            bgm_file=bgm_path,
            output_filename=output_name,
            vibe=session.vibe,
            scene_tags=session.scene_tags,
            mute_audio=session.mute_audio
        )

        if success and session.voiceover_file and session.voiceover_file.exists():
            vo_output = session_out_dir / f"vo_{output_name}"
            self.music_agent.swap_audio_track(output_path, session.voiceover_file, vo_output)
            session.current_reel_path = vo_output
            output_name = f"vo_{output_name}"
        else:
            session.current_reel_path = output_path

        return {
            "text": f"{message}\n\nPreview the updated reel above! Tell me if you need any other changes, or click **Approve & Download** to finalize.",
            "state": session.state,
            "interactive_type": "review_and_feedback",
            "reel_url": f"/outputs/{session.session_id}/{output_name}",
            "caption": session.reel_caption
        }

    def handle_voiceover_upload(self, session: ReelSession, vo_file_path: Path) -> Dict[str, Any]:
        """
        FR-11.3: Cleans voiceover interference and substitutes BGM completely.
        """
        cleaned_vo = vo_file_path.with_name(f"cleaned_{vo_file_path.name}")
        clean_ok = self.music_agent.clean_audio_interference(vo_file_path, cleaned_vo)
        chosen_vo = cleaned_vo if clean_ok and cleaned_vo.exists() else vo_file_path

        session.voiceover_file = chosen_vo
        session.reel_version += 1
        output_name = f"draft_reel_v{session.reel_version}.mp4"
        new_output = (OUTPUTS_DIR / session.session_id) / output_name

        if not session.current_reel_path or not session.current_reel_path.exists():
            return {"error": "Original reel not found."}

        # Substitute BGM with clean voiceover track
        success = self.music_agent.swap_audio_track(
            video_path=session.current_reel_path,
            new_audio_path=chosen_vo,
            output_path=new_output
        )

        if not success:
            return {
                "text": "❌ Failed to attach voiceover track. Please try recording again.",
                "state": session.state
            }

        session.current_reel_path = new_output
        session.state = STATE_REVIEW_AND_FEEDBACK

        return {
            "text": (
                "🎙️ **Voiceover Synced & Background Music Removed!**\n\n"
                "Your recorded voiceover was cleaned of interference and has replaced the background music track. "
                "Check out the updated preview above!\n\n"
                "If you are satisfied, click **Approve & Download**. "
                "If you want any changes, let me know in the chat!"
            ),
            "state": session.state,
            "interactive_type": "review_and_feedback",
            "reel_url": f"/outputs/{session.session_id}/{output_name}"
        }
