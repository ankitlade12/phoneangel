"""Domain models shared across the application."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField


# ── Enums ─────────────────────────────────────────────────────────────

class CallMode(str, Enum):
    PREP = "prep"       # Mode 1: Pre-call preparation & flowchart
    COACH = "coach"     # Mode 2: Live call coaching overlay
    PROXY = "proxy"     # Mode 3: AI makes the call for you


class SensoryProfile(str, Enum):
    """How the user relates to phone-call sensory aspects."""
    VOICE_SENSITIVE = "voice_sensitive"
    SILENCE_ANXIOUS = "silence_anxious"
    HOLD_MUSIC_TRIGGER = "hold_music_trigger"
    NORMAL = "normal"


class CallCategory(str, Enum):
    MEDICAL = "medical"
    INSURANCE = "insurance"
    UTILITY = "utility"
    GOVERNMENT = "government"
    REPAIR = "repair"
    WORKPLACE = "workplace"
    FINANCIAL = "financial"
    GENERAL = "general"


# ── User Profile (persisted) ─────────────────────────────────────────

class UserProfile(SQLModel, table=True):
    """Stores user preferences, personal info for auto-fill, and sensory config."""

    __tablename__ = "user_profiles"

    id: int | None = SQLField(default=None, primary_key=True)
    display_name: str = ""
    date_of_birth: str = ""
    phone_number: str = ""
    email: str = ""
    address: str = ""
    insurance_provider: str = ""    # e.g. "BlueCross BlueShield"
    insurance_id: str = ""
    primary_doctor: str = ""        # e.g. "Dr. Smith (dentist)"
    medications: str = ""           # e.g. "None" or "Ibuprofen 200mg"
    allergies: str = ""             # e.g. "None" or "Penicillin"
    emergency_contact: str = ""     # e.g. "Sai — (415) 555-0199"
    preferred_pharmacy: str = ""
    sensory_profile: str = "normal"
    max_hold_time_seconds: int = 120
    preferred_call_times: str = ""  # JSON string of preferred windows
    notes: str = ""                 # Free-text accessibility notes
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


# ── Call Session (persisted) ──────────────────────────────────────────

class CallSession(SQLModel, table=True):
    """Each call attempt—prep, coached, or proxied—is a session."""

    __tablename__ = "call_sessions"

    id: int | None = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(foreign_key="user_profiles.id")
    mode: str  # CallMode value
    category: str  # CallCategory value
    objective: str = ""             # "Reschedule dentist to Thursday 2pm"
    target_entity: str = ""         # "Dr. Smith's Office"
    target_phone: str = ""          # Phone number being called
    status: str = "created"         # created | preparing | active | completed | failed
    prep_flowchart: str = ""        # JSON flowchart from prep agent
    transcript: str = ""            # Full call transcript
    summary: str = ""               # AI-generated post-call summary
    outcome: str = ""               # What was achieved
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


# ── API Request / Response Schemas ────────────────────────────────────

class PrepRequest(BaseModel):
    """Request for Mode 1: Call Preparation."""
    objective: str = Field(..., description="What do you need to accomplish?", examples=["Reschedule my dentist appointment to next Thursday afternoon"])
    category: CallCategory = CallCategory.GENERAL
    target_entity: str = Field("", description="Who are you calling?", examples=["Dr. Smith's Dental Office"])
    target_phone: str = Field("", description="Phone number (optional)")
    user_notes: str = Field("", description="Anything specific to mention or avoid")


class FlowchartNode(BaseModel):
    """A single node in the conversation flowchart."""
    id: str
    speaker: str  # "them" or "you"
    text: str
    is_question: bool = False
    your_response: str = ""
    notes: str = ""  # Coaching tip for this moment
    children: list[str] = Field(default_factory=list)  # IDs of next nodes


class PrepResponse(BaseModel):
    """Response for Mode 1: The full call preparation package."""
    session_id: int
    objective_summary: str
    estimated_duration: str
    what_to_have_ready: list[str]
    opening_script: str
    flowchart: list[FlowchartNode]
    likely_questions: list[dict]  # {question, suggested_answer, tip}
    anxiety_notes: str  # Reassurance & what to expect
    worst_case: str     # "If X happens, here's what to do"


class CoachMessage(BaseModel):
    """Real-time coaching message sent during a live call."""
    timestamp: float
    message_type: str  # "prompt" | "info" | "warning" | "reassurance"
    text: str
    auto_fill_data: str = ""  # Pre-filled answer from profile
    urgency: str = "normal"   # "normal" | "attention" | "important"


class ProxyRequest(BaseModel):
    """Request for Mode 3: AI makes the call."""
    objective: str
    category: CallCategory = CallCategory.GENERAL
    target_entity: str
    target_phone: str
    decision_boundaries: list[str] = Field(
        default_factory=list,
        description="What the AI is allowed to decide",
        examples=[["Accept any appointment Thursday or Friday after 2pm", "Do NOT agree to a copay over $50"]],
    )
    max_duration_seconds: int = 300


class ProxyResponse(BaseModel):
    """Response after AI completes a proxy call."""
    session_id: int
    status: str
    transcript: str
    summary: str
    decisions_made: list[str]
    needs_your_confirmation: list[str]
    next_steps: list[str]
