"""Gemini vision analysis for homework photos."""
from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class VocabItem:
    word: str
    definition: str
    example: str


@dataclass
class GrammarItem:
    pattern: str
    rule: str
    example: str


@dataclass
class HomeworkAnalysis:
    vocabulary: list[VocabItem] = field(default_factory=list)
    grammar: list[GrammarItem] = field(default_factory=list)


async def analyze_homework_photo(
    photo_b64: str, subject: str, language: str
) -> HomeworkAnalysis:
    """Send a base64-encoded photo to Gemini and extract vocabulary + grammar items."""
    from app import llm as app_llm

    # Always use OpenRouter + Gemini for vision — Groq has no multimodal support
    _VISION_MODEL = "openrouter/google/gemini-2.0-flash-001"

    prompt = (
        f"You are analyzing a {subject} homework assignment in {language}. "
        "Extract all vocabulary words and grammar patterns from the image. "
        "Return ONLY valid JSON with this exact structure:\n"
        '{"vocabulary": [{"word": "...", "definition": "...", "example": "..."}], '
        '"grammar": [{"pattern": "...", "rule": "...", "example": "..."}]}\n'
        "Include every distinct vocabulary word and grammar rule visible in the homework. "
        "Definitions and rules should be in English. Examples should be in the target language."
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{photo_b64}"},
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]

    raw = await app_llm.chat_completion(
        messages=messages,
        model=_VISION_MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Attempt to extract JSON from markdown fences
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group()) if match else {}

    vocab = [
        VocabItem(
            word=item.get("word", ""),
            definition=item.get("definition", ""),
            example=item.get("example", ""),
        )
        for item in data.get("vocabulary", [])
        if item.get("word")
    ]
    grammar = [
        GrammarItem(
            pattern=item.get("pattern", ""),
            rule=item.get("rule", ""),
            example=item.get("example", ""),
        )
        for item in data.get("grammar", [])
        if item.get("pattern")
    ]

    return HomeworkAnalysis(vocabulary=vocab, grammar=grammar)
