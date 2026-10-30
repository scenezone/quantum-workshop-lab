from fastapi import APIRouter

from app.content.practice import check_answer, public_questions
from app.database.models import PracticeAnswer
from app.database.mongodb import Mongo
from app.errors import NotFoundError

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


def with_practice(lesson: dict) -> dict:
    return {
        **lesson,
        # Existing databases may still contain the old answer-marked Markdown.
        "content": lesson["content"].split("**Knowledge check:**", 1)[0].rstrip(),
        "practice_questions": public_questions(lesson["lesson_id"]),
    }


@router.get("")
def list_lessons() -> dict:
    lessons = list(Mongo.db().lessons.find({}, {"_id": 0}).sort("order", 1))
    return {"lessons": [with_practice(lesson) for lesson in lessons]}


@router.get("/{lesson_id}")
def get_lesson(lesson_id: str) -> dict:
    lesson = Mongo.db().lessons.find_one({"lesson_id": lesson_id}, {"_id": 0})
    if not lesson:
        raise NotFoundError("Lesson not found.")
    return with_practice(lesson)


@router.post("/{lesson_id}/practice/check")
def check_practice(lesson_id: str, payload: PracticeAnswer) -> dict:
    return check_answer(lesson_id, payload.question_id, payload.option_id, payload.answer)
