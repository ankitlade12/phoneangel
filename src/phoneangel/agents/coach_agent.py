"""Mode 2 — Live Call Coach Agent.

Listens to real-time speech-to-text from the user's phone call and
provides on-screen coaching prompts via WebSocket. Uses Gradient AI
to interpret what the other person said and suggest responses.
"""

from __future__ import annotations

import json
import time
import structlog

from phoneangel.agents.gradient_client import gradient_agent_endpoint_json_chat
from phoneangel.config import settings
from phoneangel.models.schemas import CoachMessage, UserProfile

log = structlog.get_logger()

COACH_SYSTEM_PROMPT = """\
You are PhoneAngel Live Coach. You are watching a phone conversation
in real time via transcription. The user is autistic and needs on-screen
guidance during the call.

Your job — for EACH new transcript segment:
1. Notice what JUST happened in the call.
2. If the OTHER person asked a question or made a request, clearly explain
   what they want AND give the user a concrete sentence they can say next.
3. If the user's profile has the answer (DOB, insurance, etc.), include it
   in auto_fill_data exactly as the user could read it aloud.
4. Explain any confusing language (idioms, implied meaning, politeness).
5. Flag normal events: "You're on hold — this is normal, they'll come back."
6. Provide reassurance when there's silence or waiting.

STYLE:
- Imagine you are a calm, practical coach sitting next to the user.
- Messages should feel like natural short sentences, not system notes.
- Always include "You can say: …" in prompt messages when suggesting
  what to speak next.

RULES:
- Respond with a JSON array of coaching messages.
- Each message has: message_type, text, auto_fill_data, urgency.
- message_type: "prompt" (they asked something, suggest what to say),
  "info" (explanation of what's happening),
  "warning" (important or time-sensitive),
  "reassurance" (calm, supportive words).
- Keep text short — the user is reading while talking.
- Max 18 words per message text.
- Use literal language, no idioms.

Respond ONLY with a JSON array:
[
  {
    "message_type": "prompt|info|warning|reassurance",
    "text": "short guidance in natural language",
    "auto_fill_data": "pre-filled answer if applicable",
    "urgency": "normal|attention|important"
  }
]
If nothing needs coaching, return an empty array: []
"""


class LiveCoachSession:
    """Manages a single live-coaching session with conversation history."""

    def __init__(self, profile: UserProfile, objective: str):
        self.profile = profile
        self.objective = objective
        self.transcript_history: list[dict] = []
        self.start_time = time.time()

    def _profile_context(self) -> str:
        parts = []
        if self.profile.display_name:
            parts.append(f"Name: {self.profile.display_name}")
        if self.profile.date_of_birth:
            parts.append(f"DOB: {self.profile.date_of_birth}")
        if self.profile.insurance_id:
            parts.append(f"Insurance: {self.profile.insurance_id}")
        if self.profile.address:
            parts.append(f"Address: {self.profile.address}")
        if self.profile.phone_number:
            parts.append(f"Phone: {self.profile.phone_number}")
        return "\n".join(parts) if parts else "No profile data."

    async def process_transcript_chunk(
        self,
        speaker: str,
        text: str,
    ) -> list[CoachMessage]:
        """Process a new chunk of transcribed speech and return coaching messages."""

        self.transcript_history.append({
            "speaker": speaker,
            "text": text,
            "time": round(time.time() - self.start_time, 1),
        })

        # Build the recent conversation context (last 10 exchanges)
        recent = self.transcript_history[-10:]
        transcript_text = "\n".join(
            f"[{t['speaker']}] {t['text']}" for t in recent
        )

        user_message = f"""\
CALL OBJECTIVE: {self.objective}

USER PROFILE (auto-fill from this):
{self._profile_context()}

RECENT TRANSCRIPT:
{transcript_text}

NEW SEGMENT — {speaker}: "{text}"

What coaching does the user need RIGHT NOW?
"""

        messages = [
            {"role": "system", "content": COACH_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        data = await gradient_agent_endpoint_json_chat(
            endpoint=settings.GRADIENT_AGENT_COACH_ID,
            api_key=settings.COACH_AGENT_ACCESS_KEY,
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )

        items = data if isinstance(data, list) else data.get("messages", [])
        if not isinstance(items, list):
            log.warning("coach_agent.parse_error", raw=str(data)[:200])
            return []

        coach_messages = []
        now = time.time()
        for item in items:
            coach_messages.append(CoachMessage(
                timestamp=now,
                message_type=item.get("message_type", "info"),
                text=item.get("text", ""),
                auto_fill_data=item.get("auto_fill_data", ""),
                urgency=item.get("urgency", "normal"),
            ))

        return coach_messages
