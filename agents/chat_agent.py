"""
ChatAgent: Governs Chatbot-Driven Conversational Revision (Review Loop)
translating natural language review comments into structured editing instructions using LLM or NLP.
Strictly adheres to FR-12 of requirements.md.
"""
import re
import os
import json
from typing import Dict, List, Optional, Any

from config import GEMINI_API_KEY
from agents.music_agent import BASE_BGM_METADATA

class ChatAgent:
    """
    Agent responsible for:
    1. Conversational review dialogue governing (FR-12.1)
    2. Translating natural language review feedback into specific editing actions using LLM (FR-12.2)
    3. Safe parameter isolation (never assigning conversational chat text as hook text)
    4. Coordination of re-render requests
    """

    def __init__(self):
        self.gemini_key = GEMINI_API_KEY

    def process_review_feedback(
        self,
        user_comment: str,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parses review comment and extracts editing instructions:
        - new_hook: Optional[str]
        - new_caption: Optional[str]
        - new_bgm_track_id: Optional[str]
        - new_branding_pos: Optional[str]
        - remove_branding: bool
        - mute_audio: bool
        - is_approval: bool
        - wants_voiceover: bool
        - reply_message: str
        """
        comment_clean = user_comment.strip()
        comment_lower = comment_clean.lower()

        # 1. Approval check (FR-13)
        approval_words = [
            "approve", "approved", "looks good", "looks great", "perfect",
            "done", "finalize", "export", "download reel", "ready to download", "ready to publish"
        ]
        if any(w in comment_lower for w in approval_words) and not any(w in comment_lower for w in ["don't", "do not", "not ready", "wait"]):
            return {
                "is_approval": True,
                "needs_rerender": False,
                "reply_message": "🎉 Reel Approved & Finalized! Click below to download your production-ready 9:16 vertical reel."
            }

        # 2. Voiceover studio activation check (FR-11)
        if any(w in comment_lower for w in ["record voiceover", "voice over", "record voice", "record mic", "add voiceover", "add voice"]):
            return {
                "wants_voiceover": True,
                "needs_rerender": False,
                "reply_message": "🎙️ Synchronized Voiceover Studio Activated. Click 'Open Voiceover Studio' below to record while the reel plays!"
            }

        # 3. Mute / Remove all audio check (FR-11.4)
        if any(w in comment_lower for w in ["remove all audio", "mute audio", "no audio", "silent reel", "silent video", "remove voiceover and bgm"]):
            return {
                "mute_audio": True,
                "new_bgm_track_id": None,
                "needs_rerender": True,
                "reply_message": "🔇 All audio (music and voiceover) removed. The reel will play as a silent video."
            }

        applied_changes = []
        gemini_reply = None
        new_hook = None
        new_caption = None
        new_bgm_id = None
        new_branding_pos = None
        remove_branding = False
        scene_edits = {}
        needs_rerender = False

        # 4. Try Google Gemini LLM reasoning if key is available
        key = self.gemini_key or os.environ.get("GEMINI_API_KEY", "")
        if key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=key)
                model = genai.GenerativeModel("gemini-1.5-flash")

                catalog_summary = [f"{t['id']}: {t['title']} ({t['vibe']})" for t in BASE_BGM_METADATA]
                prompt = (
                    "You are the Chat Review Agent inside Reel Creator Agent.\n"
                    "The user has an assembled 9:16 vertical video reel and is chatting with you in the review stage to request edits or ask questions.\n\n"
                    f"Current Reel State:\n"
                    f"- Current Hook: \"{current_state.get('hook', '')}\"\n"
                    f"- Current Caption: \"{current_state.get('caption', '')}\"\n"
                    f"- Current BGM Track: \"{current_state.get('bgm_id', '')}\"\n"
                    f"- Available Tracks: {catalog_summary}\n"
                    f"- Current Logo: has_branding={current_state.get('has_branding')}, position=\"{current_state.get('branding_position')}\"\n\n"
                    f"User Message: \"{user_comment}\"\n\n"
                    "Instructions:\n"
                    "1. Determine what the user wants to change.\n"
                    "2. Only update 'new_hook' if the user explicitly asks to change/update the hook, headline, or top text overlay. NEVER assign the user's message as the hook if they didn't ask to change the hook!\n"
                    "3. If they ask to change the caption or hashtags, put it in 'new_caption'.\n"
                    "4. If they ask to change music, pick best matching ID ('track_festive', 'track_chill', 'track_energetic', 'track_cinematic', 'none') in 'new_bgm_track_id'.\n"
                    "5. If they ask about logo/watermark, set 'new_branding_pos' or 'remove_branding'.\n"
                    "6. Return STRICTLY JSON with keys:\n"
                    "{\n"
                    "  \"reply\": \"friendly conversational explanation of what you did or answer to question\",\n"
                    "  \"new_hook\": string or null,\n"
                    "  \"new_caption\": string or null,\n"
                    "  \"new_bgm_track_id\": string or null,\n"
                    "  \"new_branding_pos\": string or null,\n"
                    "  \"remove_branding\": boolean or null,\n"
                    "  \"is_approval\": boolean\n"
                    "}"
                )

                response = model.generate_content(prompt)
                raw_text = response.text.strip()
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0].strip()

                parsed = json.loads(raw_text)
                gemini_reply = parsed.get("reply")

                if parsed.get("is_approval"):
                    return {
                        "is_approval": True,
                        "needs_rerender": False,
                        "reply_message": gemini_reply or "🎉 Reel Approved & Ready to Download!"
                    }

                if parsed.get("new_hook"):
                    new_hook = parsed["new_hook"].strip()
                    applied_changes.append(f"Updated hook text to: *\"{new_hook}\"*")
                    needs_rerender = True

                if parsed.get("new_caption"):
                    new_caption = parsed["new_caption"].strip()
                    applied_changes.append("Updated post caption & hashtags")

                if parsed.get("new_bgm_track_id"):
                    t_id = parsed["new_bgm_track_id"].strip().lower()
                    if t_id == "none":
                        new_bgm_id = None
                        applied_changes.append("Removed background music track")
                    else:
                        new_bgm_id = t_id
                        applied_changes.append(f"Switched background music to: `{t_id}`")
                    needs_rerender = True

                if parsed.get("remove_branding") is True:
                    remove_branding = True
                    applied_changes.append("Removed branding watermark")
                    needs_rerender = True
                elif parsed.get("new_branding_pos"):
                    new_branding_pos = parsed["new_branding_pos"]
                    applied_changes.append(f"Moved branding logo to: `{new_branding_pos}`")
                    needs_rerender = True

            except Exception as e:
                print(f"Gemini API edit parsing fallback: {e}")

        # 5. Deterministic NLP Fallback
        if not applied_changes:
            # Hook change
            hook_match = re.search(r'(?:change\s+)?(?:the\s+)?(?:hook|headline|title)(?:\s+text)?\s*(?:to|as|is|=|:)\s*(.+)', comment_clean, re.IGNORECASE)
            if hook_match:
                new_hook = hook_match.group(1).strip(" \"'")
                applied_changes.append(f"Updated hook text to: *\"{new_hook}\"*")
                needs_rerender = True
            elif any(w in comment_lower for w in ["remove hook", "delete hook", "no hook", "clear hook"]):
                new_hook = ""
                applied_changes.append("Removed hook text banner")
                needs_rerender = True
            elif "hook" in comment_lower and ('"' in user_comment or "'" in user_comment):
                q = '"' if '"' in user_comment else "'"
                new_hook = user_comment.split(q)[1].strip()
                applied_changes.append(f"Updated hook text to: *\"{new_hook}\"*")
                needs_rerender = True

            # Caption change
            caption_match = re.search(r'(?:change\s+)?(?:the\s+)?(?:caption|post description|hashtags?)\s*(?:to|as|is|=|:)\s*(.+)', comment_clean, re.IGNORECASE)
            if caption_match:
                new_caption = caption_match.group(1).strip()
                applied_changes.append("Updated post caption & hashtags")
            elif "caption" in comment_lower and ('"' in user_comment or "'" in user_comment):
                q = '"' if '"' in user_comment else "'"
                new_caption = user_comment.split(q)[1].strip()
                applied_changes.append("Updated post caption & hashtags")

            # Branding position or removal
            if any(w in comment_lower for w in ["remove logo", "no logo", "delete logo", "remove branding", "without branding", "no watermark"]):
                remove_branding = True
                applied_changes.append("Removed branding watermark")
                needs_rerender = True
            elif "logo" in comment_lower or "branding" in comment_lower or "watermark" in comment_lower:
                for pos in ["Top-Right", "Top-Left", "Bottom-Right", "Bottom-Left", "Center", "Background"]:
                    if pos.lower() in comment_lower or pos.lower().replace("-", " ") in comment_lower:
                        new_branding_pos = pos
                        applied_changes.append(f"Moved branding logo to: `{pos}`")
                        needs_rerender = True
                        break

            # Music change
            if any(w in comment_lower for w in ["no music", "remove music", "mute music", "without music"]):
                new_bgm_id = None
                applied_changes.append("Removed background music track")
                needs_rerender = True
            elif any(w in comment_lower for w in ["festive", "traditional", "sitar", "ethnic", "saree"]):
                new_bgm_id = "track_festive"
                applied_changes.append("Switched background music to: Royal Sitar & Festive Celebration")
                needs_rerender = True
            elif any(w in comment_lower for w in ["chill", "lo-fi", "sunset", "relax"]):
                new_bgm_id = "track_chill"
                applied_changes.append("Switched background music to: Chill Sunset Lo-Fi")
                needs_rerender = True
            elif any(w in comment_lower for w in ["energetic", "pulse", "fast", "hype", "beat"]):
                new_bgm_id = "track_energetic"
                applied_changes.append("Switched background music to: Cyber Pulse Beats")
                needs_rerender = True
            elif any(w in comment_lower for w in ["cinematic", "drama", "horizons", "epic"]):
                new_bgm_id = "track_cinematic"
                applied_changes.append("Switched background music to: Deep Horizons Drama")
                needs_rerender = True

            # Scene description change
            scene_match = re.search(r'(?:change\s+)?(?:the\s+)?(?:scene|description|slide|photo|image)\s*(\d+)\s*(?:description)?\s*(?:to|as|is|=|:)\s*(.+)', comment_clean, re.IGNORECASE)
            if scene_match:
                s_idx = int(scene_match.group(1)) - 1
                s_text = scene_match.group(2).strip()
                scene_edits[s_idx] = s_text
                applied_changes.append(f"Updated description for Scene {s_idx + 1}")
                needs_rerender = True

        if not applied_changes:
            return {
                "needs_rerender": False,
                "reply_message": (
                    f"🤖 {gemini_reply or f'I received your message: *\"{user_comment}\"*.'}\n\n"
                    "Here are the edits you can make to your reel:\n"
                    "• **Change Hook Text**: *\"Change hook to The ultimate handloom drape ✨\"*\n"
                    "• **Swap Background Music**: *\"Switch music to Royal Sitar\"* or *\"Make music chill\"* or *\"Remove music\"*\n"
                    "• **Adjust Logo/Watermark**: *\"Move logo to Bottom-Right\"* or *\"Remove logo\"*\n"
                    "• **Update Post Caption**: *\"Change caption to Pure handloom silk #sareelove\"*\n"
                    "• **Record Voiceover**: *\"Record voiceover\"*\n"
                    "• **Approve & Download**: *\"Looks good, approve & download!\"*"
                )
            }

        return {
            "needs_rerender": needs_rerender,
            "new_hook": new_hook,
            "new_caption": new_caption,
            "new_bgm_track_id": new_bgm_id,
            "new_branding_pos": new_branding_pos,
            "remove_branding": remove_branding,
            "scene_edits": scene_edits,
            "applied_changes": applied_changes,
            "reply_message": f"🔄 **Reel Updated:**\n\n• " + "\n• ".join(applied_changes)
        }

