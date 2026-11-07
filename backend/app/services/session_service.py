"""Workshop sessions: facilitators create a code, participants join and sync progress."""

import hashlib
import hmac
import re
import secrets
from datetime import timedelta

from pymongo.errors import DuplicateKeyError

from app.config import get_settings
from app.content.challenges import all_challenge_ids
from app.content.curriculum import LESSONS
from app.database.mongodb import Mongo, utcnow
from app.errors import ConflictError, NotFoundError, UnauthorizedError

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # No 0/O or 1/I confusion.
CODE_LENGTH = 6
LESSON_IDS = {lesson["lesson_id"] for lesson in LESSONS}


def normalize_code(code: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", code.upper())[:12]


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _clean_name(value: str) -> str:
    return " ".join(value.split())[:80]


def _public_session(document: dict) -> dict:
    return {
        "code": document["code"],
        "name": document["name"],
        "created_at": document["created_at"],
        "expires_at": document["expires_at"],
    }


class SessionService:
    @staticmethod
    def create(name: str) -> dict:
        now = utcnow()
        document = {
            "name": _clean_name(name) or "Quantum workshop",
            "created_at": now,
            "expires_at": now + timedelta(hours=get_settings().session_retention_hours),
        }
        for _ in range(8):
            document["code"] = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
            try:
                Mongo.db().workshop_sessions.insert_one(dict(document))
                return _public_session(document)
            except DuplicateKeyError:
                continue
        raise ConflictError("Unable to create a unique session code. Please try again.")

    @staticmethod
    def get(code: str) -> dict:
        document = Mongo.db().workshop_sessions.find_one(
            # TTL deletion is asynchronous, so also filter expired sessions here.
            {"code": normalize_code(code), "expires_at": {"$gt": utcnow()}},
            {"_id": 0},
        )
        if not document:
            raise NotFoundError("This workshop session code was not found or has ended.")
        return _public_session(document)

    @staticmethod
    def list_active() -> list[dict]:
        cursor = (
            Mongo.db()
            .workshop_sessions.find({"expires_at": {"$gt": utcnow()}}, {"_id": 0})
            .sort("created_at", -1)
            .limit(50)
        )
        return [_public_session(document) for document in cursor]

    @staticmethod
    def join(code: str, nickname: str) -> dict:
        session = SessionService.get(code)
        participant_id = secrets.token_hex(8)
        token = secrets.token_urlsafe(24)
        now = utcnow()
        Mongo.db().session_participants.insert_one(
            {
                "session_code": session["code"],
                "participant_id": participant_id,
                "token_hash": _hash(token),
                "nickname": " ".join(nickname.split())[:40] or "Participant",
                "completed_lessons": [],
                "completed_challenges": [],
                "practice_correct": 0,
                "practice_attempted": 0,
                "joined_at": now,
                "last_seen": now,
                "expires_at": session["expires_at"],
            }
        )
        return {
            "session": session,
            "participant_id": participant_id,
            "participant_token": token,
        }

    @staticmethod
    def update_progress(code: str, progress: dict) -> dict:
        session = SessionService.get(code)
        collection = Mongo.db().session_participants
        participant = collection.find_one(
            {"session_code": session["code"], "participant_id": progress["participant_id"]}
        )
        if not participant or not hmac.compare_digest(
            participant["token_hash"], _hash(progress["participant_token"])
        ):
            raise UnauthorizedError("This device is not registered for the session.")
        challenge_ids = all_challenge_ids()
        lessons = sorted({item for item in progress["completed_lessons"] if item in LESSON_IDS})
        challenges = sorted(
            {item for item in progress["completed_challenges"] if item in challenge_ids}
        )
        collection.update_one(
            {"_id": participant["_id"]},
            {
                "$set": {
                    "completed_lessons": lessons,
                    "completed_challenges": challenges,
                    "practice_correct": min(
                        progress["practice_correct"], progress["practice_attempted"]
                    ),
                    "practice_attempted": progress["practice_attempted"],
                    "last_seen": utcnow(),
                }
            },
        )
        return {"status": "saved", "completed_lessons": lessons, "completed_challenges": challenges}

    @staticmethod
    def dashboard(code: str) -> dict:
        session = SessionService.get(code)
        participants = list(
            Mongo.db()
            .session_participants.find(
                {"session_code": session["code"]}, {"_id": 0, "token_hash": 0}
            )
            .sort("last_seen", -1)
        )
        lesson_counts = {lesson["lesson_id"]: 0 for lesson in LESSONS}
        challenge_counts: dict[str, int] = {}
        for participant in participants:
            for lesson_id in participant.get("completed_lessons", []):
                lesson_counts[lesson_id] = lesson_counts.get(lesson_id, 0) + 1
            for challenge_id in participant.get("completed_challenges", []):
                challenge_counts[challenge_id] = challenge_counts.get(challenge_id, 0) + 1
        return {
            "session": session,
            "participant_count": len(participants),
            "participants": [
                {
                    "participant_id": item["participant_id"],
                    "nickname": item["nickname"],
                    "completed_lessons": len(item.get("completed_lessons", [])),
                    "completed_challenges": len(item.get("completed_challenges", [])),
                    "practice_correct": item.get("practice_correct", 0),
                    "practice_attempted": item.get("practice_attempted", 0),
                    "last_seen": item.get("last_seen"),
                }
                for item in participants
            ],
            "lesson_completion": [
                {
                    "lesson_id": lesson["lesson_id"],
                    "title": lesson["title"],
                    "completed": lesson_counts.get(lesson["lesson_id"], 0),
                }
                for lesson in sorted(LESSONS, key=lambda lesson: lesson["order"])
            ],
            "challenge_completion": challenge_counts,
            "feedback": feedback_summary(session["code"]),
        }


def feedback_summary(session_code: str | None = None, limit: int = 50) -> dict:
    query = {"session_code": session_code} if session_code else {}
    collection = Mongo.db().feedback
    entries = list(collection.find(query, {"_id": 0}).sort("created_at", -1))
    count = len(entries)

    def average(key: str) -> float | None:
        return round(sum(item[key] for item in entries) / count, 2) if count else None

    distribution = {str(score): 0 for score in range(1, 6)}
    for item in entries:
        distribution[str(item["rating"])] = distribution.get(str(item["rating"]), 0) + 1
    return {
        "count": count,
        "average_rating": average("rating"),
        "average_clarity": average("clarity_rating"),
        "completion_rate": round(
            sum(bool(item["completed_workshop"]) for item in entries) / count, 3
        )
        if count
        else None,
        "rating_distribution": distribution,
        "recent_comments": [
            {
                "comments": item["comments"],
                "rating": item["rating"],
                "created_at": item["created_at"],
            }
            for item in entries
            if item.get("comments")
        ][:limit],
    }


def feedback_rows(session_code: str | None = None) -> list[dict]:
    query = {"session_code": session_code} if session_code else {}
    return list(Mongo.db().feedback.find(query, {"_id": 0}).sort("created_at", 1))
