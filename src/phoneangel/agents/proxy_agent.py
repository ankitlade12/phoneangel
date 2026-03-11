"""Mode 3 — Proxy Call Agent.

Uses Twilio for outbound calling and Gradient AI for real-time
conversation management. The AI makes the call, handles the
conversation within pre-approved boundaries, and returns a
transcript + summary to the user.
"""

from __future__ import annotations

import json
import structlog

from phoneangel.agents.gradient_client import gradient_agent_endpoint_json_chat, gradient_chat
from phoneangel.config import settings
from phoneangel.models.schemas import ProxyRequest, ProxyResponse, UserProfile

log = structlog.get_logger()

PROXY_SYSTEM_PROMPT = """\
You are PhoneAngel Proxy Caller. You are about to make a phone call
ON BEHALF of an autistic user who cannot make the call themselves.
You will conduct the entire conversation.

CONTEXT:
- You are calling {target_entity} at {target_phone}.
- The user's goal: {objective}
- You may make these decisions: {boundaries}
- You must NOT exceed these boundaries. If asked something outside
  your authority, say: "I'll need to check with the person I'm
  calling for and call back."

USER DATA (use when asked):
{profile_data}

CONVERSATION RULES:
- Be polite, clear, and efficient.
- State upfront: "Hi, I'm calling on behalf of {user_name} regarding {objective}."
- Collect all relevant information (confirmation numbers, dates, costs).
- If you reach a voicemail, leave a clear message with a callback number.
- Keep the call under {max_duration} seconds.

After the call, generate a summary with:
- What was accomplished
- Any decisions you made (within boundaries)
- Anything that needs the user's confirmation
- Next steps
"""


def _build_proxy_context(
    request: ProxyRequest,
    profile: UserProfile,
) -> str:
    """Build the full system prompt for the proxy agent."""
    profile_parts = []
    if profile.display_name:
        profile_parts.append(f"Full name: {profile.display_name}")
    if profile.date_of_birth:
        profile_parts.append(f"Date of birth: {profile.date_of_birth}")
    if profile.phone_number:
        profile_parts.append(f"Callback number: {profile.phone_number}")
    if profile.insurance_id:
        profile_parts.append(f"Insurance ID: {profile.insurance_id}")
    if profile.address:
        profile_parts.append(f"Address: {profile.address}")

    return PROXY_SYSTEM_PROMPT.format(
        target_entity=request.target_entity,
        target_phone=request.target_phone,
        objective=request.objective,
        boundaries="\n".join(f"  - {b}" for b in request.decision_boundaries) or "None specified",
        profile_data="\n".join(profile_parts) or "No profile data.",
        user_name=profile.display_name or "a patient",
        max_duration=request.max_duration_seconds,
    )


SUMMARY_PROMPT = """\
Given this phone call transcript, generate a JSON summary:
{{
  "status": "completed|partial|failed",
  "summary": "2-3 sentence plain-English summary",
  "decisions_made": ["list of decisions made during the call"],
  "needs_your_confirmation": ["anything the user needs to approve"],
  "next_steps": ["what happens next"]
}}

TRANSCRIPT:
{transcript}
"""


async def generate_proxy_plan(
    request: ProxyRequest,
    profile: UserProfile,
) -> dict:
    """Generate the conversation plan the proxy agent will follow.

    Returns the system prompt and TwiML configuration for Twilio.
    """
    system_prompt = _build_proxy_context(request, profile)

    # Generate the opening statement using the dedicated proxy agent endpoint
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "Generate the exact opening statement you will say when someone "
                "answers the phone. Keep it under 30 words."
            ),
        },
    ]

    data = await gradient_agent_endpoint_json_chat(
        endpoint=settings.GRADIENT_AGENT_PROXY_ID,
        api_key=settings.PROXY_AGENT_ACCESS_KEY,
        messages=messages,
        temperature=0.3,
        max_tokens=200,
    )

    # Proxy agent may return either plain text or a small JSON object
    if isinstance(data, dict):
        opening = data.get("opening_statement") or data.get("response") or ""
    else:
        opening = str(data)

    return {
        "system_prompt": system_prompt,
        "opening_statement": opening.strip(),
        "target_phone": request.target_phone,
        "max_duration": request.max_duration_seconds,
    }


async def summarize_proxy_call(
    transcript: str,
    session_id: int,
) -> ProxyResponse:
    """After the call is complete, summarize what happened."""

    messages = [
        {"role": "system", "content": "You summarize phone calls. Respond ONLY with valid JSON."},
        {"role": "user", "content": SUMMARY_PROMPT.format(transcript=transcript)},
    ]

    # Use the proxy agent endpoint for summarization as well, so we don't depend
    # on the deprecated serverless /chat/completions URL.
    data = await gradient_agent_endpoint_json_chat(
        endpoint=settings.GRADIENT_AGENT_PROXY_ID,
        api_key=settings.PROXY_AGENT_ACCESS_KEY,
        messages=messages,
        temperature=0.2,
        max_tokens=512,
    )

    if not isinstance(data, dict):
        data = {
            "status": "completed",
            "summary": str(data)[:500],
            "decisions_made": [],
            "needs_your_confirmation": [],
            "next_steps": [],
        }

    return ProxyResponse(
        session_id=session_id,
        status=data.get("status", "completed"),
        transcript=transcript,
        summary=data.get("summary", ""),
        decisions_made=data.get("decisions_made", []),
        needs_your_confirmation=data.get("needs_your_confirmation", []),
        next_steps=data.get("next_steps", []),
    )
