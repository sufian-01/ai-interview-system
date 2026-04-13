"""Scoring helpers for interview answers and report generation."""

from io import BytesIO
import re

from fpdf import FPDF


KEYWORD_GROUPS = {
    "skills": ("skill", "skills", "technology", "tech stack", "tool"),
    "experience": ("experience", "worked", "role", "responsibility"),
    "projects": ("project", "product", "built", "implemented", "delivered"),
}

CONFIDENCE_TERMS = ("led", "delivered", "improved", "achieved", "built", "owned")


def _split_sentences(text: str):
    return [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]


def _analyze_answer(answer: str):
    cleaned_answer = (answer or "").strip()
    words = cleaned_answer.split()
    word_count = len(words)
    lowered = cleaned_answer.lower()
    skipped = not cleaned_answer or word_count < 5

    keyword_hits = {
        group: any(keyword in lowered for keyword in keywords)
        for group, keywords in KEYWORD_GROUPS.items()
    }
    keyword_count = sum(keyword_hits.values())

    sentences = _split_sentences(cleaned_answer)
    sentence_count = len(sentences)
    avg_sentence_len = word_count / sentence_count if sentence_count else 0
    assertive_count = sum(1 for term in CONFIDENCE_TERMS if term in lowered)

    confidence_score = 0.0
    if sentence_count >= 2:
        confidence_score += 1
    if avg_sentence_len >= 10:
        confidence_score += 1
    if assertive_count > 0:
        confidence_score += 1
    confidence_score = min(confidence_score, 3)

    if word_count < 15:
        clarity_label = "Short explanation"
    elif word_count < 40:
        clarity_label = "Clear explanation"
    else:
        clarity_label = "Detailed explanation"

    score = 0.0
    if not skipped:
        if word_count >= 15:
            score += 3.0
        elif word_count >= 8:
            score += 2.0
        else:
            score += 1.0

        score += min(keyword_count * 1.5, 3.0)
        score += min(confidence_score, 2.0)

        if word_count >= 40:
            score += 1.5
        elif word_count >= 20:
            score += 1.0
        else:
            score += 0.5

        if word_count >= 60 and keyword_count >= 2 and sentence_count >= 3:
            score += 0.5

    score = round(min(score, 10.0), 1)

    if skipped:
        status = "Skipped"
        feedback_tip = "Provide at least 4-5 complete sentences with one real example."
    elif score >= 8:
        status = "Excellent"
        feedback_tip = "Great structure. Keep adding measurable outcomes for even stronger impact."
    elif score >= 6:
        status = "Good"
        feedback_tip = "Add one specific project/result to make the answer more convincing."
    else:
        status = "Needs Improvement"
        feedback_tip = "Increase depth, include skills used, and explain your impact clearly."

    return {
        "answer": cleaned_answer,
        "word_count": word_count,
        "keyword_hits": keyword_hits,
        "confidence_score": round(confidence_score, 1),
        "clarity": clarity_label,
        "skipped": skipped,
        "score": score,
        "status": status,
        "feedback_tip": feedback_tip,
    }


def build_interview_report(questions, answers, candidate_name):
    """Build complete interview report data for UI and PDF export."""
    safe_questions = questions or []
    safe_answers = answers or []
    answer_reports = []
    strengths = set()
    weaknesses = set()

    for idx, question in enumerate(safe_questions):
        answer = safe_answers[idx] if idx < len(safe_answers) else ""
        analysis = _analyze_answer(answer)
        analysis.update(
            {
                "question": question,
                "index": idx + 1,
            }
        )
        answer_reports.append(analysis)

        if analysis["status"] in {"Excellent", "Good"}:
            strengths.add(f"Q{idx + 1}: Demonstrated relevant knowledge and structure.")
        if analysis["status"] in {"Needs Improvement", "Skipped"}:
            weaknesses.add(f"Q{idx + 1}: {analysis['feedback_tip']}")

    if not answer_reports:
        return {
            "candidate_name": candidate_name,
            "final_score": 0.0,
            "recommendation": "Needs Serious Practice ❌",
            "skipped_count": 0,
            "strengths": [],
            "weaknesses": ["No interview answers were available for analysis."],
            "answer_reports": [],
            "suggestions": [
                "Improve communication by practicing in a structured format.",
                "Add real-world examples from projects or work.",
                "Increase answer depth with clear reasoning and outcomes.",
            ],
        }

    skipped_count = sum(1 for report in answer_reports if report["skipped"])
    raw_average = sum(report["score"] for report in answer_reports) / len(answer_reports)
    deduction = skipped_count * 0.6
    final_score = round(max(0.0, min(10.0, raw_average - deduction)), 1)

    if final_score >= 8:
        recommendation = "Strong Candidate 🚀"
    elif final_score >= 5:
        recommendation = "Average - Needs Improvement ⚠️"
    else:
        recommendation = "Needs Serious Practice ❌"

    if not strengths:
        strengths.add("Completed the interview flow and submitted responses.")
    if not weaknesses:
        weaknesses.add("Keep practicing to sustain consistent interview quality.")

    return {
        "candidate_name": candidate_name,
        "final_score": final_score,
        "recommendation": recommendation,
        "skipped_count": skipped_count,
        "strengths": sorted(strengths),
        "weaknesses": sorted(weaknesses),
        "answer_reports": answer_reports,
        "suggestions": [
            "Improve communication by using concise STAR-style responses.",
            "Add real-world examples with measurable outcomes.",
            "Increase answer depth by explaining approach, trade-offs, and impact.",
        ],
    }


def calculate_score(answers):
    """Backwards-compatible score helper used by existing app code paths."""
    report = build_interview_report(
        questions=[f"Question {idx + 1}" for idx in range(len(answers))],
        answers=answers,
        candidate_name="Candidate",
    )
    feedback_messages = [
        f"Answer {item['index']}: {item['status']} ({item['score']}/10) - {item['feedback_tip']}"
        for item in report["answer_reports"]
    ]
    return report["final_score"], feedback_messages


def generate_pdf_report(report_data, interview_type, difficulty):
    """Create a PDF bytes object for download."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "AI Interview Report", ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Candidate: {report_data['candidate_name']}", ln=True)
    pdf.cell(0, 8, f"Interview Type: {interview_type}", ln=True)
    pdf.cell(0, 8, f"Difficulty: {difficulty}", ln=True)
    pdf.cell(0, 8, f"Final Score: {report_data['final_score']}/10", ln=True)
    pdf.multi_cell(0, 8, f"Recommendation: {report_data['recommendation']}")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 8, f"Skipped Questions: {report_data['skipped_count']}")

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Strengths", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for strength in report_data["strengths"]:
        pdf.multi_cell(0, 7, f"- {strength}")

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Weaknesses", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for weakness in report_data["weaknesses"]:
        pdf.multi_cell(0, 7, f"- {weakness}")

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 9, "Answer-wise Feedback", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for item in report_data["answer_reports"]:
        pdf.multi_cell(0, 7, f"Q{item['index']}: {item['question']}")
        pdf.multi_cell(0, 7, f"Answer: {item['answer'] or 'No answer provided'}")
        pdf.multi_cell(0, 7, f"Score: {item['score']}/10 | Status: {item['status']}")
        pdf.multi_cell(0, 7, f"Tip: {item['feedback_tip']}")
        pdf.ln(2)

    buffer = BytesIO()
    buffer.write(pdf.output(dest="S").encode("latin-1", "replace"))
    buffer.seek(0)
    return buffer.getvalue()
