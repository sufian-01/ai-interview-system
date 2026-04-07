"""Scoring helpers for interview answers."""

from textblob import TextBlob


KEYWORDS = {"experience", "project", "skills"}


def _score_single_answer(answer: str):
    """Return score and feedback for one answer."""
    score = 0
    feedback = []

    cleaned_answer = (answer or "").strip()
    words = cleaned_answer.split()
    word_count = len(words)

    if cleaned_answer:
        score += 2
    else:
        feedback.append("Answer is empty. Add at least a short response.")

    if word_count > 30:
        score += 2
    else:
        feedback.append("Try to give more detail (aim for more than 30 words).")

    if word_count > 60:
        score += 2
    else:
        feedback.append("A deeper explanation (more than 60 words) can improve clarity.")

    sentiment = TextBlob(cleaned_answer).sentiment.polarity if cleaned_answer else 0
    if sentiment > 0:
        score += 2
    else:
        feedback.append("Use more positive, confident wording.")

    lower_answer = cleaned_answer.lower()
    if any(keyword in lower_answer for keyword in KEYWORDS):
        score += 2
    else:
        feedback.append("Mention relevant keywords like experience, project, or skills.")

    return score, feedback


def calculate_score(answers):
    """Calculate interview score out of 10 and return feedback list.

    Args:
        answers: List of user answers.

    Returns:
        tuple[float, list[str]]: Average score (0-10) and feedback messages.
    """
    if not answers:
        return 0.0, ["No answers were submitted."]

    total_score = 0
    feedback_messages = []

    for index, answer in enumerate(answers, start=1):
        answer_score, answer_feedback = _score_single_answer(answer)
        total_score += answer_score

        if answer_feedback:
            feedback_messages.append(f"Answer {index}: " + " ".join(answer_feedback))
        else:
            feedback_messages.append(f"Answer {index}: Excellent response.")

    final_score = round(total_score / len(answers), 1)
    return final_score, feedback_messages
