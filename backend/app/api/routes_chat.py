"""
FastAPI Routes: Chat with a specific complaint.
POST /api/complaints/{id}/chat
Loads the complaint from DB, retrieves prior message history,
calls chat_with_complaint, persists both messages, returns AI reply.
"""
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.db.database import SessionLocal
from app.db.models import Complaint, ChatMessage
from app.agent.nodes.chat_node import chat_with_complaint
from app.agent.prompts.chat_prompt import QUICK_REPLY_PROMPTS_TEMPLATE
from app.core.logging import logger

router = APIRouter(prefix="/complaints", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("/{complaint_id}/chat")
async def chat_complaint(complaint_id: str, body: ChatRequest):
    """
    Send a user message and receive a grounded AI response about a specific complaint.
    Persists both user message and AI reply to chat_messages table.
    """
    user_message = body.message.strip()
    if not user_message:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    db = SessionLocal()
    try:
        # Load complaint — clean 404 if missing
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise HTTPException(
                status_code=404,
                detail=f"Complaint '{complaint_id}' not found. Run extraction first."
            )

        # Load prior chat history (ordered chronologically)
        history = (
            db.query(ChatMessage)
            .filter(ChatMessage.complaint_id == complaint_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        # Get AI reply (run in executor to avoid blocking event loop)
        logger.info(f"chat: complaint={complaint_id[:8]}..., history={len(history)} msgs, question='{user_message[:60]}'")
        reply = await asyncio.get_event_loop().run_in_executor(
            None, chat_with_complaint, complaint, user_message, history
        )

        # Persist user message + AI reply
        db.add(ChatMessage(complaint_id=complaint_id, role="user",      content=user_message))
        db.add(ChatMessage(complaint_id=complaint_id, role="assistant", content=reply))
        db.commit()

        return {"reply": reply, "complaint_id": complaint_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"chat_complaint: unexpected error — {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/{complaint_id}/chat/suggestions")
async def get_chat_suggestions(complaint_id: str):
    """
    Return quick-reply chip suggestions contextualised to the complaint's severity.
    """
    db = SessionLocal()
    try:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found.")

        severity = complaint.initial_severity or "Major"
        suggestions = [t.format(severity=severity) for t in QUICK_REPLY_PROMPTS_TEMPLATE]

        # Extra suggestion for duplicates
        if complaint.is_duplicate:
            suggestions.append("How does this compare to the original complaint for this batch?")

        return {"suggestions": suggestions, "complaint_id": complaint_id}
    finally:
        db.close()
