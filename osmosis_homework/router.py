"""FastAPI router for homework photo analysis."""
from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Goal, GoalWord, User, _uuid, _utcnow
from app.services import goal_service, srs_service

from osmosis_homework.vision import analyze_homework_photo

router = APIRouter()


@router.post("/analyze")
async def analyze_homework(
    subject: str = Form(...),
    language: str = Form(...),
    conversation_id: str = Form(...),
    photo: UploadFile = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    photo_bytes = await photo.read()
    if not photo_bytes:
        raise HTTPException(status_code=400, detail="Empty photo upload")

    photo_b64 = base64.b64encode(photo_bytes).decode()

    try:
        analysis = await analyze_homework_photo(photo_b64, subject, language)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Vision analysis failed: {exc}") from exc

    # Create two goals
    vocab_goal = await goal_service.create_goal(
        db=db,
        user_id=user.id,
        title=f"{subject} Homework – Vocabulary",
        language=language,
        media_type="homework",
    )
    grammar_goal = await goal_service.create_goal(
        db=db,
        user_id=user.id,
        title=f"{subject} Homework – Grammar",
        language=language,
        media_type="homework",
    )

    # Create vocabulary SRS cards and link to vocab goal
    vocab_cards = []
    for item in analysis.vocabulary:
        card = await srs_service.find_or_create_card(
            db=db,
            user_id=user.id,
            word=item.word,
            language=language,
            back=item.definition,
            card_type="vocabulary",
            context_sentence=item.example or None,
            source="homework",
        )
        vocab_cards.append(card)
        existing = await db.get(GoalWord, {"goal_id": vocab_goal.id, "card_id": card.id})
        if existing is None:
            db.add(GoalWord(goal_id=vocab_goal.id, card_id=card.id, added_at=_utcnow()))

    # Create grammar SRS cards and link to grammar goal
    grammar_cards = []
    for item in analysis.grammar:
        card = await srs_service.find_or_create_card(
            db=db,
            user_id=user.id,
            word=item.pattern,
            language=language,
            back=item.rule,
            card_type="grammar",
            context_sentence=item.example or None,
            source="homework",
        )
        grammar_cards.append(card)
        existing = await db.get(GoalWord, {"goal_id": grammar_goal.id, "card_id": card.id})
        if existing is None:
            db.add(GoalWord(goal_id=grammar_goal.id, card_id=card.id, added_at=_utcnow()))

    # Set total_words on each goal
    await db.execute(
        update(Goal)
        .where(Goal.id == vocab_goal.id)
        .values(total_words=len(vocab_cards))
    )
    await db.execute(
        update(Goal)
        .where(Goal.id == grammar_goal.id)
        .values(total_words=len(grammar_cards))
    )
    await db.commit()

    return {
        "vocab_goal_id": vocab_goal.id,
        "grammar_goal_id": grammar_goal.id,
        "vocab_count": len(vocab_cards),
        "grammar_count": len(grammar_cards),
    }
