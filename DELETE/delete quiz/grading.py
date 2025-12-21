def grade_attempt(attempt):
    total = 0
    correct = 0
    qmap = {q.id: q for q in attempt.quiz.questions.prefetch_related("choices").all()}
    for ans in attempt.answers.all():
        q = qmap.get(ans.question_id)
        if not q:
            continue
        total += 1
        correct_ids = {c.id for c in q.choices.all() if c.is_correct}
        if set(ans.selected_choice_ids) == correct_ids:
            correct += 1
    attempt.score = (correct / total * 100.0) if total else 0.0
    attempt.finished = True
    attempt.save(update_fields=["score", "finished"])
