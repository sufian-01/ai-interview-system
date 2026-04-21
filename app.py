import time

import streamlit as st

from ai_generator import evaluate_answer, generate_ai_questions
from face_detection import detect_face_from_webcam
from questions import get_questions
from scoring import build_interview_report, generate_pdf_report
from voice_input import record_voice
from voice_output import speak


TIMER_SECONDS = 30
ONLINE_MODE = "Online Mode (AI)"
OFFLINE_MODE = "Offline Mode (existing system)"


st.set_page_config(page_title="AI Interview App", page_icon="AI", layout="centered")

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "question_start_index" not in st.session_state:
    st.session_state.question_start_index = -1


def _build_performance_insights(answers):
    """Create answer-level scores plus strengths/weaknesses from answer text."""
    answer_metrics = []
    strengths = set()
    weaknesses = set()

    for index, answer in enumerate(answers, start=1):
        cleaned_answer = (answer or "").strip()
        word_count = len(cleaned_answer.split())
        lower_answer = cleaned_answer.lower()

        score = 0
        if cleaned_answer:
            score += 2
            strengths.add("Responded to all interview questions.")
        else:
            weaknesses.add("Some answers were empty or too short.")

        if word_count > 30:
            score += 2
            strengths.add("Provided good detail in several responses.")
        else:
            weaknesses.add("Add more depth to improve answer quality.")

        if word_count > 60:
            score += 2
            strengths.add("Explained ideas clearly with extended context.")
        else:
            weaknesses.add("Use richer examples and impact statements.")

        if any(keyword in lower_answer for keyword in ("experience", "project", "skills")):
            score += 2
            strengths.add("Connected responses to practical experience.")
        else:
            weaknesses.add("Reference concrete experience, projects, and skills.")

        positive_words = ("confident", "improved", "achieved", "led", "success")
        if any(word in lower_answer for word in positive_words):
            score += 2
            strengths.add("Used positive and outcome-focused wording.")
        else:
            weaknesses.add("Use more confident, measurable language.")

        answer_metrics.append({"Answer": f"Q{index}", "Score": score})

    if not strengths:
        strengths.add("Completed the full interview flow.")
    if not weaknesses:
        weaknesses.add("Continue practicing to keep performance consistent.")

    return answer_metrics, sorted(strengths), sorted(weaknesses)


def _build_report_text(candidate_name, interview_type, difficulty, final_score, feedback, strengths, weaknesses):
    """Return printable text report."""
    lines = [
        "FINAL INTERVIEW REPORT",
        "======================",
        f"Candidate: {candidate_name}",
        f"Interview Type: {interview_type}",
        f"Difficulty: {difficulty}",
        f"Total Score: {final_score}/10",
        "",
        "Answer-wise Feedback:",
    ]
    lines.extend([f"- {item}" for item in feedback])
    lines.extend(
        [
            "",
            "Strengths:",
            *[f"- {item}" for item in strengths],
            "",
            "Weaknesses:",
            *[f"- {item}" for item in weaknesses],
        ]
    )
    return "\n".join(lines)


def _init_session_state():
    defaults = {
        "ai_mode": ONLINE_MODE,
        "active_mode": ONLINE_MODE,
        "camera_active": False,
        "face_verified": False,
        "current_question_index": 0,
        "answers": {},
        "questions": [],
        "selected_questions": [],
        "generated_questions": [],
        "interview_completed": False,
        "report_data": None,
        "candidate_name": "",
        "interview_type": "",
        "difficulty": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _is_online_mode():
    return st.session_state.ai_mode == ONLINE_MODE


def _inject_styles():
    st.markdown(
        """
        <style>
        .main .block-container {
            max-width: 860px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .app-shell {
            padding: 0.5rem 0 1.5rem 0;
        }
        .hero-card {
            background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
            border: 1px solid #bfdbfe;
            border-radius: 24px;
            padding: 1.6rem;
            margin-bottom: 1.25rem;
            text-align: center;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
        }
        .app-title {
            font-size: 2.4rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.35rem;
        }
        .app-subtitle {
            color: #475569;
            font-size: 1rem;
            margin: 0;
        }
        .section-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 22px;
            padding: 1.35rem;
            margin-bottom: 1rem;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.06);
        }
        .question-card {
            background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
            border-radius: 20px;
            padding: 1.3rem;
            color: #f8fafc;
            margin: 0.75rem 0 1rem 0;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.18);
        }
        .question-label {
            display: inline-block;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #93c5fd;
            margin-bottom: 0.6rem;
        }
        .question-text {
            font-size: 1.08rem;
            line-height: 1.7;
        }
        .meta-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 0.8rem;
        }
        .meta-chip {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 0.9rem;
            text-align: center;
        }
        .meta-label {
            color: #64748b;
            font-size: 0.8rem;
            margin-bottom: 0.2rem;
        }
        .meta-value {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 700;
        }
        .timer-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.55rem;
        }
        .timer-title {
            color: #0f172a;
            font-size: 0.98rem;
            font-weight: 700;
        }
        .timer-countdown {
            color: #b91c1c;
            font-size: 1rem;
            font-weight: 800;
        }
        .score-card {
            border: 1px solid #dbeafe;
            border-radius: 20px;
            padding: 1.2rem;
            background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
            text-align: center;
            margin-bottom: 1rem;
        }
        .kpi-title {
            font-size: 0.9rem;
            color: #64748b;
        }
        .kpi-value {
            font-size: 2.8rem;
            font-weight: 800;
            margin-top: 0.2rem;
        }
        .mini-card {
            border: 1px solid #e2e8f0;
            background: #ffffff;
            border-radius: 18px;
            padding: 1rem;
            height: 100%;
            box-shadow: 0 12px 25px rgba(15, 23, 42, 0.05);
        }
        .report-card {
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 1rem 1.1rem;
            background: #ffffff;
            margin: 0.75rem 0;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.05);
        }
        .stButton > button {
            border-radius: 14px;
            padding: 0.72rem 1rem;
            border: 1px solid #cbd5e1;
            font-weight: 700;
            transition: all 0.2s ease;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
        }
        .stButton > button:hover {
            border-color: #3b82f6;
            color: #1d4ed8;
            transform: translateY(-1px);
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: #ffffff;
            border: none;
        }
        .stTextArea textarea {
            min-height: 220px;
            border-radius: 16px;
        }
        @media (max-width: 768px) {
            .meta-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _start_question_timer():
    st.session_state.start_time = time.time()
    st.session_state.question_start_index = st.session_state.current_question_index


def _ensure_question_timer():
    if not st.session_state.interview_started:
        return

    current_idx = st.session_state.current_question_index
    if current_idx >= len(st.session_state.selected_questions):
        return

    if (
        st.session_state.question_start_index != current_idx
    ):
        _start_question_timer()


def _get_remaining_seconds():
    _ensure_question_timer()
    if st.session_state.start_time is None:
        return TIMER_SECONDS

    elapsed = time.time() - st.session_state.start_time
    return max(0, TIMER_SECONDS - int(elapsed))


def _advance_question(answer_key):
    current_idx = st.session_state.current_question_index
    st.session_state.answers[current_idx] = st.session_state.get(answer_key, "")
    st.session_state.current_question_index += 1

    if st.session_state.current_question_index < len(st.session_state.selected_questions):
        _start_question_timer()
    else:
        st.session_state.start_time = None
        st.session_state.question_start_index = -1


def _render_header():
    st.markdown("<div class='app-shell'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero-card">
            <div class="app-title">AI Interview App</div>
            <p class="app-subtitle">Practice smarter with structured mock interviews and live feedback.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_ai_mode_control():
    selected_mode = st.radio(
        "AI Mode",
        [ONLINE_MODE, OFFLINE_MODE],
        index=0 if st.session_state.ai_mode == ONLINE_MODE else 1,
        horizontal=True,
        disabled=st.session_state.interview_started,
    )
    st.session_state.ai_mode = selected_mode

    if _is_online_mode():
        st.success("🟢 AI Mode ON")
    else:
        st.info("⚪ Offline Mode")


def _render_candidate_meta():
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.success("Interview started.")
    st.markdown(
        f"""
        <div class="meta-grid">
            <div class="meta-chip">
                <div class="meta-label">Candidate</div>
                <div class="meta-value">{st.session_state.candidate_name}</div>
            </div>
            <div class="meta-chip">
                <div class="meta-label">Interview Type</div>
                <div class="meta-value">{st.session_state.interview_type}</div>
            </div>
            <div class="meta-chip">
                <div class="meta-label">Difficulty</div>
                <div class="meta-value">{st.session_state.difficulty}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_question_progress(current_idx, total_questions, remaining_seconds):
    progress_value = (current_idx + 1) / total_questions
    timer_progress = remaining_seconds / TIMER_SECONDS

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="timer-row">
            <div class="timer-title">Question {current_idx + 1} of {total_questions}</div>
            <div class="timer-countdown">{remaining_seconds}s remaining</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(progress_value, text=f"Interview progress: {current_idx + 1}/{total_questions}")
    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
    st.progress(timer_progress, text=f"Time left for this question: {remaining_seconds}s")

    if remaining_seconds <= 10:
        st.warning("Time is almost up. Your current answer will be captured automatically.")
    else:
        st.info("You have 30 seconds for each question. Use voice or text to answer.")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_question_card(question_text):
    st.markdown(
        f"""
        <div class="question-card">
            <div class="question-label">Current Question</div>
            <div class="question-text">{question_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_completion(report_data, total_questions):
    final_score = report_data["final_score"]
    score_color = "#16a34a" if final_score >= 8 else "#d97706" if final_score >= 5 else "#dc2626"

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.progress(1.0, text=f"Interview progress: {total_questions}/{total_questions}")
    st.info("Interview completed. Your final report is ready.")
    st.markdown(
        """
        <div class="score-card">
            <div class="kpi-title">Overall Interview Score</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='kpi-value' style='color:{score_color};'>{final_score}/10</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='color:#334155; font-weight:700;'>{report_data['recommendation']}</div></div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='mini-card'><h4>Strengths</h4></div>", unsafe_allow_html=True)
        for item in report_data["strengths"]:
            st.markdown(f"- {item}")
    with col2:
        st.markdown("<div class='mini-card'><h4>Weaknesses</h4></div>", unsafe_allow_html=True)
        for item in report_data["weaknesses"]:
            st.markdown(f"- {item}")

    st.warning(f"Skipped Questions: {report_data['skipped_count']}")

    st.markdown("### Personalized Suggestions")
    for suggestion in report_data["suggestions"]:
        st.markdown(f"- {suggestion}")

    pdf_bytes = generate_pdf_report(
        report_data,
        st.session_state.interview_type,
        st.session_state.difficulty,
    )
    st.download_button(
        "Download Report (PDF)",
        data=pdf_bytes,
        file_name=f"{st.session_state.candidate_name.lower().replace(' ', '_')}_interview_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.markdown("### Answer-wise Feedback")
    answer_metrics = []
    for item in report_data["answer_reports"]:
        answer_metrics.append({"Answer": f"Q{item['index']}", "Score": item["score"]})
        st.markdown("<div class='report-card'>", unsafe_allow_html=True)
        st.markdown(f"**Q{item['index']}. {item['question']}**")
        st.markdown(f"**Answer:** {item['answer'] or 'No answer provided.'}")
        st.markdown(
            f"**Score:** {item['score']}/10 | **Status:** {item['status']} | "
            f"**Words:** {item['word_count']} | **Clarity:** {item['clarity']}"
        )
        keyword_status = ", ".join(
            [f"{key}: {'Yes' if hit else 'No'}" for key, hit in item["keyword_hits"].items()]
        )
        st.markdown(f"**Keyword Presence:** {keyword_status}")
        st.markdown(f"**Confidence Score:** {item['confidence_score']}/3")
        st.info(f"Improvement Tip: {item['feedback_tip']}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Performance Chart")
    st.bar_chart(answer_metrics, x="Answer", y="Score", color="#2563eb")
    st.markdown("</div>", unsafe_allow_html=True)


def _build_ai_interview_report(questions, answers, candidate_name):
    answer_reports = []
    strengths = set()
    weaknesses = set()

    for idx, question in enumerate(questions):
        answer = answers[idx] if idx < len(answers) else ""
        evaluation = evaluate_answer(question, answer)
        score = float(evaluation["score"])
        feedback = str(evaluation["feedback"])
        cleaned_answer = (answer or "").strip()
        word_count = len(cleaned_answer.split())

        if not cleaned_answer:
            status = "Skipped"
        elif score >= 8:
            status = "Excellent"
        elif score >= 6:
            status = "Good"
        else:
            status = "Needs Improvement"

        report = {
            "answer": cleaned_answer,
            "word_count": word_count,
            "keyword_hits": {
                "relevance": score >= 5,
                "depth": score >= 7,
                "examples": word_count >= 25,
            },
            "confidence_score": round(min(3.0, score / 10 * 3), 1),
            "clarity": "Detailed explanation" if word_count >= 40 else "Clear explanation" if word_count >= 15 else "Short explanation",
            "skipped": not cleaned_answer,
            "score": score,
            "status": status,
            "feedback_tip": feedback,
            "question": question,
            "index": idx + 1,
        }
        answer_reports.append(report)

        if status in {"Excellent", "Good"}:
            strengths.add(f"Q{idx + 1}: {feedback}")
        else:
            weaknesses.add(f"Q{idx + 1}: {feedback}")

    if not answer_reports:
        return {
            "candidate_name": candidate_name,
            "final_score": 0.0,
            "recommendation": "Needs Serious Practice",
            "skipped_count": 0,
            "strengths": [],
            "weaknesses": ["No interview answers were available for analysis."],
            "answer_reports": [],
            "suggestions": [
                "Practice concise, structured responses.",
                "Use concrete examples from projects or work.",
                "Explain trade-offs, reasoning, and impact.",
            ],
        }

    skipped_count = sum(1 for report in answer_reports if report["skipped"])
    final_score = round(
        max(0.0, min(10.0, sum(report["score"] for report in answer_reports) / len(answer_reports))),
        1,
    )

    if final_score >= 8:
        recommendation = "Strong Candidate"
    elif final_score >= 5:
        recommendation = "Average - Needs Improvement"
    else:
        recommendation = "Needs Serious Practice"

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
            "Structure answers with context, approach, result, and trade-offs.",
            "Include specific examples that prove your understanding.",
            "Use concise language while covering the key technical points.",
        ],
    }


_init_session_state()
_inject_styles()
_render_header()
_render_ai_mode_control()

if not st.session_state.interview_started:
    st.markdown("### Camera Check")
    if st.button("Start Camera", use_container_width=True):
        st.session_state.face_verified = detect_face_from_webcam()

    if st.session_state.face_verified:
        st.success("Face verified. You can start the interview.")
    else:
        st.info("Please complete camera verification before starting the interview.")

    with st.sidebar:
        st.markdown("## Interview Setup")
        name = st.text_input("Name", placeholder="Enter your name")
        topic = st.text_input(
            "Topic (for AI-generated questions)",
            placeholder="e.g. Python concurrency",
        )
        interview_type = st.selectbox(
            "Interview Type",
            ["Technical", "Behavioral", "System Design", "Case Study"],
            index=0,
        )
        difficulty = st.selectbox(
            "Difficulty",
            ["Easy", "Medium", "Hard"],
            index=1,
        )

        if st.button("Generate Questions", use_container_width=True):
            if _is_online_mode() and not topic.strip():
                st.warning("Please enter a topic before generating questions.")
            else:
                if _is_online_mode():
                    with st.spinner("Generating questions..."):
                        try:
                            st.session_state.questions = generate_ai_questions(topic)
                            st.session_state.generated_questions = st.session_state.questions
                            st.session_state.active_mode = ONLINE_MODE
                            st.success("AI questions generated successfully.")
                        except Exception as exc:
                            st.session_state.questions = get_questions(interview_type, difficulty)
                            st.session_state.generated_questions = []
                            st.session_state.ai_mode = OFFLINE_MODE
                            st.session_state.active_mode = OFFLINE_MODE
                            st.warning(
                                "AI unavailable, switching to offline mode. "
                                f"Details: {exc}"
                            )
                else:
                    st.session_state.questions = get_questions(interview_type, difficulty)
                    st.session_state.generated_questions = []
                    st.session_state.active_mode = OFFLINE_MODE
                    st.success("Offline questions loaded successfully.")

        if st.button("Start Interview", type="primary", use_container_width=True):
            if not st.session_state.face_verified:
                st.info("Please complete camera verification before starting the interview.")
            elif not name.strip():
                st.warning("Please enter your name before starting.")
            else:
                st.session_state.interview_started = True
                st.session_state.current_question_index = 0
                st.session_state.answers = {}
                st.session_state.interview_completed = False
                st.session_state.report_data = None

                if st.session_state.questions:
                    st.session_state.selected_questions = st.session_state.questions
                elif _is_online_mode() and topic.strip():
                    with st.spinner("Generating questions..."):
                        try:
                            st.session_state.questions = generate_ai_questions(topic)
                            st.session_state.selected_questions = st.session_state.questions
                            st.session_state.active_mode = ONLINE_MODE
                        except Exception as exc:
                            st.session_state.selected_questions = get_questions(interview_type, difficulty)
                            st.session_state.ai_mode = OFFLINE_MODE
                            st.session_state.active_mode = OFFLINE_MODE
                            st.warning(
                                "AI unavailable, switching to offline mode. "
                                f"Details: {exc}"
                            )
                else:
                    st.session_state.selected_questions = get_questions(interview_type, difficulty)
                    st.session_state.active_mode = OFFLINE_MODE

                st.session_state.candidate_name = name.strip()
                st.session_state.interview_type = interview_type
                st.session_state.difficulty = difficulty

                for key in list(st.session_state.keys()):
                    if key.startswith("answer_"):
                        del st.session_state[key]

                _start_question_timer()

    if not st.session_state.interview_started:
        st.info("Set up your interview from the sidebar, then click Start Interview.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()


if st.session_state.interview_started:
    _render_candidate_meta()

    total_questions = len(st.session_state.selected_questions)
    current_idx = st.session_state.current_question_index

    if current_idx < total_questions:
        answer_key = f"answer_{current_idx}"
        saved_answer = st.session_state.answers.get(current_idx, "")
        if answer_key not in st.session_state:
            st.session_state[answer_key] = saved_answer

        remaining_seconds = _get_remaining_seconds()

        if remaining_seconds <= 0:
            _advance_question(answer_key)
            st.rerun()

        if current_idx < total_questions:
            current_question = st.session_state.selected_questions[current_idx]

            _render_question_progress(current_idx, total_questions, remaining_seconds)

            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown(
                "<h3 style='text-align:center; margin-bottom:0.35rem;'>Interview Session</h3>",
                unsafe_allow_html=True,
            )
            _render_question_card(current_question)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Speak Question", use_container_width=True):
                    speak(current_question)
            with col2:
                if st.button("Speak Answer", use_container_width=True):
                    with st.spinner("Listening..."):
                        recognized_text, voice_error = record_voice()

                    if voice_error:
                        st.warning(voice_error)
                    else:
                        st.session_state[answer_key] = recognized_text
                        st.session_state.answers[current_idx] = recognized_text
                        st.success("Voice captured successfully.")
                        st.info(f"Recognized text: {recognized_text}")

            answer = st.text_area(
                "Your Answer",
                height=220,
                key=answer_key,
                placeholder="Share your answer here. Mention your approach, examples, and measurable impact.",
            )

            if st.button("Submit and Next", type="primary", use_container_width=True):
                st.session_state.answers[current_idx] = answer
                _advance_question(answer_key)
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

            time.sleep(1)
            st.rerun()
    else:
        if not st.session_state.interview_completed or st.session_state.report_data is None:
            ordered_answers = [
                st.session_state.answers.get(idx, "")
                for idx in range(len(st.session_state.selected_questions))
            ]
            if st.session_state.active_mode == ONLINE_MODE:
                with st.spinner("Evaluating answers with AI..."):
                    try:
                        st.session_state.report_data = _build_ai_interview_report(
                            st.session_state.selected_questions,
                            ordered_answers,
                            st.session_state.candidate_name,
                        )
                    except Exception as exc:
                        st.warning(
                            "AI unavailable, switching to offline mode. "
                            f"Details: {exc}"
                        )
                        st.session_state.ai_mode = OFFLINE_MODE
                        st.session_state.active_mode = OFFLINE_MODE
                        st.session_state.report_data = build_interview_report(
                            st.session_state.selected_questions,
                            ordered_answers,
                            st.session_state.candidate_name,
                        )
            else:
                st.session_state.report_data = build_interview_report(
                    st.session_state.selected_questions,
                    ordered_answers,
                    st.session_state.candidate_name,
                )
            st.session_state.interview_completed = True

        _render_completion(st.session_state.report_data, total_questions)
st.markdown("</div>", unsafe_allow_html=True)
