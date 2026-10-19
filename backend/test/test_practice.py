import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.content.curriculum import LESSONS
from app.content.practice import PRACTICE, check_answer, public_questions
from app.database.models import Lesson
from app.main import app


@pytest.fixture
def client(database):
    with patch("app.database.mongodb.Mongo.connect"), patch("app.database.mongodb.Mongo.close"), TestClient(app) as client:
        yield client


def test_every_topic_has_four_mcqs_and_two_written_questions():
    assert set(PRACTICE) == {lesson["lesson_id"] for lesson in LESSONS}
    for lesson in LESSONS:
        questions = public_questions(lesson["lesson_id"])
        assert len(questions) == 6
        assert len({question["question_id"] for question in questions}) == 6
        assert "**Knowledge check:**" not in lesson["content"]
        assert "✅" not in lesson["content"]
        assert sum(question["kind"] == "multiple_choice" for question in questions) == 4
        assert sum(question["kind"] == "short_answer" for question in questions) == 2


@pytest.mark.parametrize("lesson_id", PRACTICE)
def test_mcq_keys_and_written_samples_are_consistent(lesson_id):
    questions = public_questions(lesson_id)
    for index, (prompt, options, correct, explanation) in enumerate(PRACTICE[lesson_id]["mcq"]):
        assert prompt and explanation and len(options) == len(set(options)) == 4
        assert 0 <= correct < len(options)
        question = questions[index]
        assert len({option["option_id"] for option in question["options"]}) == 4
        for option_index, option in enumerate(question["options"]):
            result = check_answer(lesson_id, question["question_id"], option["option_id"], None)
            assert result["correct"] == (option_index == correct)
            assert result["correct_option_id"] == chr(97 + correct)
    for question in questions[4:]:
        result = check_answer(lesson_id, question["question_id"], None, "My attempt")
        assert result["sample_answer"]
        assert len(result["key_points"]) >= 3
        assert "correct" not in result  # Free text is for self-review, not automatic grading.


def test_public_lesson_list_and_detail_do_not_reveal_answer_keys(client):
    lessons = client.get("/api/lessons").json()["lessons"]
    for lesson in lessons:
        Lesson.model_validate(lesson)
        questions = lesson["practice_questions"]
        assert len(questions) == 6
        assert all(set(question) == {"question_id", "kind", "prompt", "options"} for question in questions)
        assert "correct_option_id" not in json.dumps(lesson)
        assert "sample_answer" not in json.dumps(lesson)
    detail = client.get("/api/lessons/superposition").json()
    assert detail["practice_questions"] == next(item for item in lessons if item["lesson_id"] == "superposition")["practice_questions"]


def test_legacy_answer_marked_database_content_is_hidden(client, database):
    database.lessons.update_one({"lesson_id": "superposition"}, {"$set": {
        "content": "Lesson body.\n\n**Knowledge check:** Select an option.\n\n- The answer ✅",
    }})
    detail = client.get("/api/lessons/superposition").json()
    assert detail["content"] == "Lesson body."
    assert len(detail["practice_questions"]) == 6


def test_mcq_requires_an_option_then_returns_feedback(client):
    path = "/api/lessons/superposition/practice/check"
    question_id = "superposition-mcq-1"
    assert client.post(path, json={"question_id": question_id}).status_code == 422
    assert client.post(path, json={"question_id": question_id, "option_id": "unknown"}).status_code == 422
    wrong = client.post(path, json={"question_id": question_id, "option_id": "a"}).json()
    assert wrong["correct"] is False
    assert wrong["correct_option_id"] == "c"
    assert wrong["explanation"]
    right = client.post(path, json={"question_id": question_id, "option_id": "c"}).json()
    assert right["correct"] is True


def test_written_question_requires_an_attempt_before_sample_answer(client):
    path = "/api/lessons/superposition/practice/check"
    question_id = "superposition-written-1"
    for attempt in [{}, {"answer": "   "}, {"answer": ""}, {"option_id": "a"}]:
        assert client.post(path, json={"question_id": question_id, **attempt}).status_code == 422
    response = client.post(path, json={"question_id": question_id, "answer": "H is reversible, so applying it twice gives identity."})
    assert response.status_code == 200
    assert response.json()["sample_answer"]
    assert response.json()["key_points"]
    assert "correct" not in response.json()
    assert client.post(path, json={"question_id": question_id, "answer": "x" * 2001}).status_code == 422


def test_question_cannot_be_checked_under_another_lesson(client):
    response = client.post("/api/lessons/gates/practice/check", json={"question_id": "superposition-mcq-1", "option_id": "a"})
    assert response.status_code == 404
    assert client.post("/api/lessons/unknown/practice/check", json={"question_id": "unknown-mcq-1", "option_id": "a"}).status_code == 404
