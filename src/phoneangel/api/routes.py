"""API routes for PhoneAngel — three modes + profile management."""

from __future__ import annotations

import json
import structlog
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from twilio.rest import Client

from phoneangel.models.database import get_session
from phoneangel.models.schemas import (
    CallSession,
    CoachMessage,
    PrepRequest,
    PrepResponse,
    ProxyRequest,
    ProxyResponse,
    UserProfile,
)
from phoneangel.agents.prep_agent import generate_prep
from phoneangel.agents.coach_agent import LiveCoachSession
from phoneangel.agents.proxy_agent import generate_proxy_plan, summarize_proxy_call
from phoneangel.config import settings

log = structlog.get_logger()

router = APIRouter()


# ── Profile ───────────────────────────────────────────────────────────

@router.post("/api/profile", response_model=UserProfile)
async def create_or_update_profile(
    profile: UserProfile,
    db: AsyncSession = Depends(get_session),
):
    """Create or update user profile. Upserts by ID."""
    if profile.id:
        existing = await db.get(UserProfile, profile.id)
        if existing:
            for field in profile.model_fields:
                if field != "id":
                    setattr(existing, field, getattr(profile, field))
            db.add(existing)
            await db.commit()
            await db.refresh(existing)
            return existing

    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/api/profile/{user_id}", response_model=UserProfile)
async def get_profile(user_id: int, db: AsyncSession = Depends(get_session)):
    """Get a user profile."""
    profile = await db.get(UserProfile, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


# ── Mode 1: Call Prep ─────────────────────────────────────────────────

@router.post("/api/prep", response_model=PrepResponse)
async def prepare_call(
    request: PrepRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_session),
):
    """Mode 1 — Generate a full call preparation package with flowchart."""

    # Get or create profile
    profile = await db.get(UserProfile, user_id)
    if not profile:
        profile = UserProfile(id=user_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    # Create call session
    session = CallSession(
        user_id=user_id,
        mode="prep",
        category=request.category.value,
        objective=request.objective,
        target_entity=request.target_entity,
        target_phone=request.target_phone,
        status="preparing",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    try:
        prep = await generate_prep(request, profile, session.id)

        # Save flowchart to session
        session.prep_flowchart = json.dumps([n.model_dump() for n in prep.flowchart])
        session.status = "completed"
        db.add(session)
        await db.commit()

        return prep

    except Exception as e:
        session.status = "failed"
        db.add(session)
        await db.commit()
        log.error("prep.failed", error=str(e), session_id=session.id)
        raise HTTPException(status_code=500, detail=f"Prep generation failed: {e}")


# ── Mode 2: Live Coach (WebSocket) ───────────────────────────────────

@router.websocket("/ws/coach/{user_id}")
async def live_coach_websocket(
    websocket: WebSocket,
    user_id: int,
):
    """Mode 2 — WebSocket for real-time call coaching.

    Client sends: {"speaker": "them"|"you", "text": "transcribed words"}
    Server sends: [CoachMessage, ...]
    """
    await websocket.accept()

    # Initialize session (in production, fetch from DB)
    profile = UserProfile(id=user_id)
    objective = ""

    try:
        # First message should be the call objective
        init_data = await websocket.receive_json()
        objective = init_data.get("objective", "General phone call")
        profile.display_name = init_data.get("name", "")
        profile.date_of_birth = init_data.get("dob", "")
        profile.insurance_id = init_data.get("insurance_id", "")
        profile.address = init_data.get("address", "")
        profile.phone_number = init_data.get("phone", "")

        coach = LiveCoachSession(profile=profile, objective=objective)

        await websocket.send_json({
            "type": "ready",
            "message": "Coach is ready. Send transcript chunks as they come.",
        })

        while True:
            data = await websocket.receive_json()
            speaker = data.get("speaker", "them")
            text = data.get("text", "")

            if not text.strip():
                continue

            messages = await coach.process_transcript_chunk(speaker, text)

            await websocket.send_json({
                "type": "coaching",
                "messages": [m.model_dump() for m in messages],
            })

    except WebSocketDisconnect:
        log.info("coach.disconnected", user_id=user_id)
    except Exception as e:
        log.error("coach.error", error=str(e), user_id=user_id)
        await websocket.close(code=1011)


# ── Mode 3: Proxy Call ────────────────────────────────────────────────

@router.post("/api/proxy", response_model=dict)
async def initiate_proxy_call(
    request: ProxyRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_session),
):
    """Mode 3 — Initiate an AI proxy call.

    Step 1: Generate the call plan.
    Step 2: (In production) Trigger Twilio outbound call.
    Step 3: Return the plan for user confirmation before dialing.
    """
    profile = await db.get(UserProfile, user_id)
    if not profile:
        profile = UserProfile(id=user_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    # Create session
    session = CallSession(
        user_id=user_id,
        mode="proxy",
        category=request.category.value,
        objective=request.objective,
        target_entity=request.target_entity,
        target_phone=request.target_phone,
        status="preparing",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    try:
        plan = await generate_proxy_plan(request, profile)

        return {
            "session_id": session.id,
            "status": "ready_to_call",
            "opening_statement": plan["opening_statement"],
            "target_phone": plan["target_phone"],
            "message": "Review the plan above. Hit /api/proxy/{session_id}/confirm to start the call.",
        }

    except Exception as e:
        log.error("proxy.plan_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Proxy plan failed: {e}")


@router.post("/api/proxy/{session_id}/confirm", response_model=dict)
async def confirm_proxy_call(
    session_id: int,
    db: AsyncSession = Depends(get_session),
):
    """Confirm and start an AI proxy call via Twilio.

    For now this:
    - Looks up the call session
    - Starts an outbound Twilio call to the target number
    - Plays a short message explaining this is a PhoneAngel test call
    - Marks the session as 'active' and stores the Twilio Call SID
    """
    session = await db.get(CallSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Basic safety checks
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        raise HTTPException(
            status_code=400,
            detail="Twilio credentials are not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env.",
        )
    if not settings.TWILIO_PHONE_NUMBER:
        raise HTTPException(
            status_code=400,
            detail="Twilio phone number is not configured. Set TWILIO_PHONE_NUMBER in .env.",
        )
    if not session.target_phone:
        raise HTTPException(
            status_code=400,
            detail="Call session has no target phone number.",
        )

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        # Simple inline TwiML: announce the test call and hang up.
        twiml = (
            "<Response>"
            "<Say voice=\"alice\">"
            "Hello. This is a PhoneAngel test call from your development environment. "
            "No action is required. Goodbye."
            "</Say>"
            "</Response>"
        )

        call = client.calls.create(
            to=session.target_phone,
            from_=settings.TWILIO_PHONE_NUMBER,
            twiml=twiml,
        )

        session.status = "active"
        session.started_at = session.started_at or __import__("datetime").datetime.utcnow()
        # Store Call SID in outcome field for now
        session.outcome = json.dumps({"twilio_call_sid": call.sid})
        db.add(session)
        await db.commit()

        return {
            "session_id": session.id,
            "status": "calling",
            "twilio_call_sid": call.sid,
            "message": "Twilio call initiated. This is a test message-only call.",
        }

    except Exception as e:
        log.error("proxy.confirm_failed", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=f"Failed to start proxy call: {e}")


@router.post("/api/proxy/{session_id}/summarize", response_model=ProxyResponse)
async def summarize_call(
    session_id: int,
    transcript: str = "",
    db: AsyncSession = Depends(get_session),
):
    """Summarize a completed proxy call given its transcript."""
    session = await db.get(CallSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    summary = await summarize_proxy_call(transcript or session.transcript, session_id)

    session.transcript = transcript or session.transcript
    session.summary = summary.summary
    session.outcome = json.dumps(summary.decisions_made)
    session.status = "completed"
    db.add(session)
    await db.commit()

    return summary


# ── History ───────────────────────────────────────────────────────────

@router.get("/api/sessions/{user_id}")
async def get_sessions(
    user_id: int,
    db: AsyncSession = Depends(get_session),
):
    """Get all call sessions for a user."""
    result = await db.exec(
        select(CallSession).where(CallSession.user_id == user_id).order_by(CallSession.created_at.desc())
    )
    return result.all()


# ── Health ────────────────────────────────────────────────────────────

@router.get("/api/health")
async def health():
    return {"status": "ok", "service": "PhoneAngel"}
