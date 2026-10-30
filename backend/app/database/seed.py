import logging

from pymongo.errors import DuplicateKeyError

from app.content.curriculum import EXPERIMENTS, LESSONS
from app.database.mongodb import Mongo, utcnow

logger = logging.getLogger(__name__)


def seed_database() -> None:
    db = Mongo.db()
    for collection, key, items in [
        (db.lessons, "lesson_id", LESSONS),
        (db.experiments, "experiment_id", EXPERIMENTS.values()),
    ]:
        for item in items:
            update = {"$set": item, "$setOnInsert": {"created_at": utcnow()}}
            try:
                collection.update_one({key: item[key]}, update, upsert=True)
            except DuplicateKeyError:
                collection.update_one({key: item[key]}, {"$set": item})
    logger.info("Seeded %s lessons and %s circuits", len(LESSONS), len(EXPERIMENTS))
