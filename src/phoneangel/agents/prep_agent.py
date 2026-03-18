"""Mode 1 — Call Prep Agent.

Generates a full conversation flowchart, opening script,
likely questions with answers, and anxiety-management notes
using DigitalOcean Gradient AI.
"""

from __future__ import annotations

import structlog

from phoneangel.agents.gradient_client import gradient_agent_endpoint_json_chat
from phoneangel.config import settings
from phoneangel.models.schemas import (
    CallCategory,
    FlowchartNode,
    PrepRequest,
    PrepResponse,
    UserProfile,
)

log = structlog.get_logger()

PREP_SYSTEM_PROMPT = """\
You are PhoneAngel Call-Prep, an AI assistant that helps autistic adults
prepare for phone calls. Your user experiences phone call anxiety and needs
to SEE the entire conversation before it happens.

Your job:
1. Predict the full conversation flow as a tree of nodes.
2. Generate a word-for-word opening script the user can read aloud.
3. List every likely question the other side will ask, with suggested answers.
4. Pre-fill answers from the user's profile data (DOB, insurance, address, etc.).
5. Add reassurance notes explaining what's normal (hold music, transfers, silence).
6. Describe the worst-case scenario and how to handle it.

RULES:
- Use simple, direct, literal language. No idioms or metaphors.
- Keep scripts short — under 15 words per sentence.
- Mark every point where the user will need to speak.
- If the user has profile data, auto-fill it into suggested answers.
- Be warm but not patronizing.

Respond ONLY with a JSON object matching this exact schema:
{
  "objective_summary": "string — one-sentence summary of the call goal",
  "estimated_duration": "string — e.g. '3-5 minutes'",
  "what_to_have_ready": ["list of items to have nearby"],
  "opening_script": "string — exact words to say when someone picks up",
  "flowchart": [
    {
      "id": "node_1",
      "speaker": "them|you",
      "text": "what they say or what you say",
      "is_question": true/false,
      "your_response": "suggested response if speaker is them",
      "notes": "coaching tip",
      "children": ["node_2", "node_3"]
    }
  ],
  "likely_questions": [
    {"question": "...", "suggested_answer": "...", "tip": "..."}
  ],
  "anxiety_notes": "string — what's normal, what to expect, reassurance",
  "worst_case": "string — if things go wrong, here's what to do"
}
"""


def _build_user_context(profile: UserProfile) -> str:
    """Assemble user profile data into a context block for the agent."""
    parts = []
    if profile.display_name:
        parts.append(f"Name: {profile.display_name}")
    if profile.date_of_birth:
        parts.append(f"Date of birth: {profile.date_of_birth}")
    if profile.phone_number:
        parts.append(f"Phone: {profile.phone_number}")
    if profile.email:
        parts.append(f"Email: {profile.email}")
    if profile.address:
        parts.append(f"Address: {profile.address}")
    if profile.insurance_provider:
        parts.append(f"Insurance provider: {profile.insurance_provider}")
    if profile.insurance_id:
        parts.append(f"Insurance ID: {profile.insurance_id}")
    if profile.primary_doctor:
        parts.append(f"Primary doctor: {profile.primary_doctor}")
    if profile.medications:
        parts.append(f"Medications: {profile.medications}")
    if profile.allergies:
        parts.append(f"Allergies: {profile.allergies}")
    if profile.emergency_contact:
        parts.append(f"Emergency contact: {profile.emergency_contact}")
    if profile.preferred_pharmacy:
        parts.append(f"Pharmacy: {profile.preferred_pharmacy}")
    if profile.notes:
        parts.append(f"Accessibility notes: {profile.notes}")
    return "\n".join(parts) if parts else "No profile data provided yet."


async def generate_prep(
    request: PrepRequest,
    profile: UserProfile,
    session_id: int,
) -> PrepResponse:
    """Call Gradient AI to generate a full call-preparation package."""

    user_context = _build_user_context(profile)

    user_message = f"""\
CALL OBJECTIVE: {request.objective}
CATEGORY: {request.category.value}
CALLING: {request.target_entity or 'Unknown'}
PHONE: {request.target_phone or 'Not provided'}
USER NOTES: {request.user_notes or 'None'}

USER PROFILE DATA (auto-fill into answers where relevant):
{user_context}
"""

    messages = [
        {"role": "system", "content": PREP_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    log.info("prep_agent.generating", session_id=session_id, objective=request.objective)
    data = await gradient_agent_endpoint_json_chat(
        endpoint=settings.GRADIENT_AGENT_PREP_ID,
        api_key=settings.PREP_AGENT_ACCESS_KEY,
        messages=messages,
    )
    log.info("prep_agent.complete", session_id=session_id)

    # Parse flowchart nodes
    flowchart_nodes = []
    for node_data in data.get("flowchart", []):
        flowchart_nodes.append(FlowchartNode(**node_data))

    return PrepResponse(
        session_id=session_id,
        objective_summary=data.get("objective_summary", request.objective),
        estimated_duration=data.get("estimated_duration", "3-5 minutes"),
        what_to_have_ready=data.get("what_to_have_ready", []),
        opening_script=data.get("opening_script", ""),
        flowchart=flowchart_nodes,
        likely_questions=data.get("likely_questions", []),
        anxiety_notes=data.get("anxiety_notes", ""),
        worst_case=data.get("worst_case", ""),
    )
