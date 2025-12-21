def grade_attempt(attempt):
    quiz = attempt.quiz
    questions = quiz.questions

    score = 0
    total = len(questions)

    for q in questions:
        qid = str(q["id"])
        correct = set(q["correct_answers"])
        user_ans = set(attempt.answers.get(qid, []))

        if user_ans == correct:
            score += 1

    attempt.score = score
    attempt.total = total
    attempt.save()
