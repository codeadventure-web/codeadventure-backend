def grade_attempt(attempt):
    total = 0
    correct = 0
    qmap = {q.id: q for q in attempt.quiz.questions.prefetch_related("choices").all()}
    for ans in attempt.answers.all():
        q = qmap.get(ans.question_id)
        if not q:
            continue
        total += 1
        correct_ids = {str(c.id) for c in q.choices.all() if c.is_correct}
        if set(ans.selected_choice_ids) == correct_ids:
            correct += 1

    # Simple logic: is_passed if all are correct (or you could set a threshold)
    # Given the user wants to "simplize", let's say 100% is passed.
    attempt.is_passed = (correct == total) if total > 0 else False
    attempt.finished = True
    attempt.save(update_fields=["is_passed", "finished"])
