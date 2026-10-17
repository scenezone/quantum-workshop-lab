from app.database.mongodb import Mongo
from app.quantum.circuits import get_metadata


def build_context(
    lesson_id: str | None,
    experiment_id: str | None,
    result_context: dict | None,
) -> str:

    sections: list[str]=[]

    if lesson_id:
        lesson = Mongo.db().lessons.find_one({"lesson_id":lesson_id})
        if lesson:
            sections.append(
                f"LESSON: {lesson["title"]}\n{lesson['content'][:3500]}"
            )

    if experiment_id:
        try:
            metadata = get_metadata(experiment_id)
            sections.append(
                "EXPERIMENT:\n"
                f"ID: {experiment_id}\n"
                f"Title: {metadata['title']}\n"
                f"Description: {metadata['description']}\n"
                f"Ideal probabilities: {metadata['ideal_probabilities']}"
            )
        except Exception:
            pass

    if result_context:
        safe_keys = {
            "backend",
            "backend_name",
            "shots",
            "counts",
            "observed_probabilities",
            "ideal_probabilities",
            "status",
            "provider_job_id",
        }
        filtered = {key: result_context[key] for key in safe_keys if key in result_context}
        sections.append(f"RESULT CONTEXT:\n{filtered}")

    return "\n\n".join(sections) if sections else "No additional workshop context was provided."