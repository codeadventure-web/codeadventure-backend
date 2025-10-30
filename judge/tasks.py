from config.celery import app
from .models import Submission
from .runner_client import run_in_sandbox


@app.task(bind=True, acks_late=True)
def run_submission(self, submission_id):
    sub = Submission.objects.select_related("problem", "language", "user").get(
        id=submission_id
    )
    if sub.status != "queued":
        return
    sub.status = "running"
    sub.save(update_fields=["status"])
    result = run_in_sandbox(sub)
    sub.status = result["final_status"]
    sub.summary = result
    sub.save(update_fields=["status", "summary"])
