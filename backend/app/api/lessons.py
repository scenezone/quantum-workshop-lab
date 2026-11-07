from fastapi import APIRouter, Request

from app.ai.assistant_service import AssistantService
from app.content.curriculum import LESSONS
from app.content.practice import check_answer, public_questions
from app.database.models import Lesson, LessonList, PracticeAnswer, PracticeFeedbackResponse
from app.errors import NotFoundError
from app.rate_limit import limiter

router = APIRouter(prefix="/api/lessons", tags=["lessons"])

# Lessons are served from the canonical Python content, so a simulator-only
# workshop needs no database and stale database copies cannot leak answer keys.
_ORDERED = sorted(LESSONS, key=lambda lesson: lesson["order"])


def with_practice(lesson: dict) -> dict:
    return {**lesson, "practice_questions": public_questions(lesson["lesson_id"])}


@router.get("", response_model=LessonList)
def list_lessons() -> dict:
    return {"lessons": [with_practice(lesson) for lesson in _ORDERED]}


@router.get("/{lesson_id}", response_model=Lesson)
def get_lesson(lesson_id: str) -> dict:
    lesson = next((item for item in _ORDERED if item["lesson_id"] == lesson_id), None)
    if not lesson:
        raise NotFoundError("Lesson not found.")
    return with_practice(lesson)


@router.post(
    "/{lesson_id}/practice/check",
    response_model=PracticeFeedbackResponse,
    response_model_exclude_none=True,
)
@limiter.limit("30/minute")
async def check_practice(request: Request, lesson_id: str, payload: PracticeAnswer) -> dict:
    result = check_answer(lesson_id, payload.question_id, payload.option_id, payload.answer)
    if result["kind"] == "short_answer":
        result["ai_feedback"] = await AssistantService.grade_written_answer(
            result.pop("prompt"), result["sample_answer"], result["key_points"], payload.answer
        )
    return result
