from fastapi import APIRouter

from app.database.mongodb import Mongo
from app.errors import NotFoundError

router = APIRouter(prefix='/api/lessons',tags=['lessons'])


@router.get("")
def list_lessons() -> dict:
    lessons = list(Mongo.db().lessons.find({}, {"_id": 0}).sort("order", 1))
    return {"lessons": lessons}


@router.get("/{lesson_id}")
def get_lesson(lesson_id: str) -> dict:
    lesson = Mongo.db().lessons.find_one({"lesson_id": lesson_id}, {"_id": 0})
    if not lesson:
        raise NotFoundError("Lesson not found.")
    return lesson