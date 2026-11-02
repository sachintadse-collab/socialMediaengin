"""
Reel Creator Agent: Top-level unified interface exposing the multi-agent system.
Adheres strictly to the Zero-Assumption Protocol and Software Requirements Specification.
"""
from agents.coordinator import (
    ReelCoordinatorAgent,
    ReelSession,
    STATE_INIT,
    STATE_AWAITING_MEDIA,
    STATE_CONFIRM_VIBE,
    STATE_SELECT_BGM,
    STATE_EDIT_SCENE_DESCRIPTIONS,
    STATE_EDIT_REEL_CAPTION,
    STATE_SELECT_HOOK,
    STATE_BRANDING_INQUIRY,
    STATE_BRANDING_POSITION,
    STATE_VOICEOVER_INQUIRY,
    STATE_VOICEOVER_RECORDING,
    STATE_REVIEW_AND_FEEDBACK,
    STATE_APPROVED
)

# ReelCreatorAgent is the multi-agent coordinator
ReelCreatorAgent = ReelCoordinatorAgent

__all__ = [
    "ReelCreatorAgent",
    "ReelCoordinatorAgent",
    "ReelSession",
    "STATE_INIT",
    "STATE_AWAITING_MEDIA",
    "STATE_CONFIRM_VIBE",
    "STATE_SELECT_BGM",
    "STATE_EDIT_SCENE_DESCRIPTIONS",
    "STATE_EDIT_REEL_CAPTION",
    "STATE_SELECT_HOOK",
    "STATE_BRANDING_INQUIRY",
    "STATE_BRANDING_POSITION",
    "STATE_VOICEOVER_INQUIRY",
    "STATE_VOICEOVER_RECORDING",
    "STATE_REVIEW_AND_FEEDBACK",
    "STATE_APPROVED"
]
