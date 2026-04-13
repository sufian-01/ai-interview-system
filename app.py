import streamlit as st

from ai_generator import generate_questions
from face_detection import detect_face_from_webcam
from questions import get_questions
from scoring import build_interview_report, generate_pdf_report
from voice_input import record_voice
from voice_output import speak


st.set_page_config(page_title="AI Interview App", page_icon="🎤", layout="centered")

if "camera_active" not in st.session_state:
    st.session_state.camera_active = False

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "selected_questions" not in st.session_state:
    st.session_state.selected_questions = []
if "generated_questions" not in st.session_state:
    st.session_state.generated_questions = []
if "interview_completed" not in st.session_state:
    st.session_state.interview_completed = False
if "report_data" not in st.session_state:
    st.session_state.report_data = None

if "camera_active" not in st.session_state:
    st.session_state.camera_active = False

st.markdown(
    """
    <style>
    .app-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .app-subtitle {
        text-align: center;
        color: #6b7280;
        margin-bottom: 1.2rem;
    }
    .question-card {
        max-width: 760px;
        margin: 0.5rem auto 1.2rem auto;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        background: #1e293b;
        box-shadow: 0 16px 30px rgba(15, 23, 42, 0.35);
    }
    .question-card-label {
        color: #cbd5e1;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    .question-card-text {
        color: #f8fafc;
        font-size: 1.24rem;
        line-height: 1.8;
        font-weight: 500;
        margin-top: 0.7rem;
    }
    div[data-testid="stTextArea"] {
        margin-top: 0.8rem;
        margin-bottom: 1rem;
    }
    div[data-testid="stTextArea"] label p {
        font-size: 1.03rem;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }
    div[data-testid="stTextArea"] textarea {
        border-radius: 12px;
        padding: 14px 16px;
        border: 1px solid #cbd5e1;
        background: #f8fafc;
        line-height: 1.65;
        font-size: 1.05rem;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 0.18rem rgba(37, 99, 235, 0.2);
    }

    .question-card {
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    background: #1e293b;   /* dark background */
    color: white;          /* text visible */
    margin: 0.5rem 0 1rem 0;
    font-size: 16px;
    }


    .report-card {
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        background: #0f172a;
        margin: 0.5rem 0 1rem 0;
    }
    .score-card {
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        background: #111827;
        text-align: center;
        margin-bottom: 0.8rem;
    }
    .kpi-title { font-size: 0.9rem; color: #9ca3af; }
    .kpi-value { font-size: 2.9rem; font-weight: 800; margin-top: 0.15rem; }
    .mini-card {
        border: 1px solid #374151;
        background: #1f2937;
        border-radius: 12px;
        padding: 0.9rem;
        margin-bottom: 0.6rem;
    }
 </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='app-title'>AI Interview App</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='app-subtitle'>Practice smarter with structured mock interviews.</div>",
    unsafe_allow_html=True,
)

st.markdown("### Camera Check")

# session state init
if "camera_active" not in st.session_state:
    st.session_state.camera_active = False

if st.button("Start Camera", use_container_width=True):
    is_face_detected = detect_face_from_webcam()

    if is_face_detected:
        st.success("✅ Face detected. Camera activated.")
        st.session_state.camera_active = True
    else:
        st.error("❌ Face not detected. Try again.")
        st.session_state.camera_active = False

with st.sidebar:
    st.markdown("## Interview Setup")
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

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

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    if st.button("Generate Questions", use_container_width=True):
        if not topic.strip():
            st.warning("Please enter a topic before generating questions.")
        else:
            with st.spinner("Generating interview questions with Gemini..."):
                try:
                    st.session_state.generated_questions = generate_questions(topic, difficulty)
                    st.success("AI questions generated successfully.")
                except Exception as exc:
                    st.session_state.generated_questions = []
                    st.warning(
                        "AI question generation failed. "
                        "The app will use default questions instead. "
                        f"Details: {exc}"
                    )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    start_clicked = st.button("Start Interview", type="primary", use_container_width=True)

if start_clicked:
    if not name.strip():
        st.warning("Please enter your name before starting.")
    else:
        st.session_state.interview_started = True
        st.session_state.current_question_index = 0
        st.session_state.answers = {}
        st.session_state.interview_completed = False
        st.session_state.report_data = None

        if st.session_state.generated_questions:
            st.session_state.selected_questions = st.session_state.generated_questions
        else:
            st.session_state.selected_questions = get_questions(interview_type, difficulty)

        st.session_state.candidate_name = name.strip()
        st.session_state.interview_type = interview_type
        st.session_state.difficulty = difficulty

if st.session_state.interview_started:
    with st.container():
        st.success("Interview started!")
        st.markdown(
            f"""
            **Candidate:** {st.session_state.candidate_name}  
            **Interview Type:** {st.session_state.interview_type}  
            **Difficulty:** {st.session_state.difficulty}
            """
        )
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        st.divider()

    total_questions = len(st.session_state.selected_questions)
    current_idx = st.session_state.current_question_index

    if current_idx < total_questions:
        progress = (current_idx + 1) / total_questions
        with st.container():
            st.progress(progress)
            st.markdown(
                f"<div style='text-align:center; font-weight:600; margin-top:0.35rem;'>"
                f"Question {current_idx + 1} of {total_questions}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

        with st.container():
            st.markdown(
                "<h3 style='text-align:center; margin-bottom:0.25rem;'>Interview Session</h3>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            current_question = st.session_state.selected_questions[current_idx]
            if st.button("🔊 Speak Question", use_container_width=True):
                 speak(current_question)
            st.markdown(
                f"""
                <div class='question-card'>
                    <div class='question-card-label'>Question</div>
                    <div class='question-card-text'>{current_question}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            answer_key = f"answer_{current_idx}"
            saved_answer = st.session_state.answers.get(current_idx, "")

            if answer_key not in st.session_state:
                st.session_state[answer_key] = saved_answer

            if st.button("🎤 Speak Answer", use_container_width=True):
                with st.spinner("Listening..."):
                    recognized_text, voice_error = record_voice()

                if voice_error:
                    st.warning(voice_error)
                else:
                    st.session_state[answer_key] = recognized_text
                    st.session_state.answers[current_idx] = recognized_text
                    st.success("Voice captured successfully.")
                    st.markdown(f"**Recognized text:** {recognized_text}")

            answer = st.text_area(
                "Your Answer",
                height=180,
                key=answer_key,
                placeholder="Type your answer here...",
            )

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            if st.button("Next", type="primary", use_container_width=True):
                st.session_state.answers[current_idx] = answer
                st.session_state.current_question_index += 1
                st.rerun()
    else:
        if not st.session_state.interview_completed or st.session_state.report_data is None:
            ordered_answers = [
                st.session_state.answers.get(idx, "")
                for idx in range(len(st.session_state.selected_questions))
            ]
            st.session_state.report_data = build_interview_report(
                st.session_state.selected_questions,
                ordered_answers,
                st.session_state.candidate_name,
            )
            st.session_state.interview_completed = True

        report_data = st.session_state.report_data
        final_score = report_data["final_score"]
        score_color = "#22c55e" if final_score >= 8 else "#facc15" if final_score >= 5 else "#ef4444"

        with st.container():
            st.progress(1.0)
            st.markdown(
                f"<div style='text-align:center; font-weight:600; margin-top:0.35rem;'>"
                f"Question {total_questions} of {total_questions}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

            st.markdown(
                "<h3 style='text-align:center; margin-bottom:0.25rem;'>Interview Complete</h3>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='text-align:center; color:#4b5563;'>Great work! You answered all questions.</p>",
                unsafe_allow_html=True,
            )
            st.markdown("---")

            st.markdown(
                "<h3 style='text-align:center; margin-bottom:0.3rem;'>Final Interview Report</h3>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class='score-card'>
                    <div class='kpi-title'>Overall Interview Score</div>
                    <div class='kpi-value' style='color:{score_color};'>⭐ {final_score}/10</div>
                    <div style='color:#cbd5e1; font-weight:600;'>{report_data["recommendation"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div class='mini-card'><h4>✅ Strengths</h4></div>", unsafe_allow_html=True)
                for item in report_data["strengths"]:
                    st.markdown(f"- {item}")
            with col2:
                st.markdown("<div class='mini-card'><h4>⚠️ Weaknesses</h4></div>", unsafe_allow_html=True)
                for item in report_data["weaknesses"]:
                    st.markdown(f"- {item}")

            st.markdown(
                f"<div class='report-card'><b>Skipped Questions:</b> {report_data['skipped_count']}</div>",
                unsafe_allow_html=True,
            )

            st.markdown("### Personalized Suggestions")
            for suggestion in report_data["suggestions"]:
                st.markdown(f"- {suggestion}")

            pdf_bytes = generate_pdf_report(
                report_data,
                st.session_state.interview_type,
                st.session_state.difficulty,
            )
            st.download_button(
                "📄 Download Report (PDF)",
                data=pdf_bytes,
                file_name=f"{st.session_state.candidate_name.lower().replace(' ', '_')}_interview_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
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
                    [
                        f"{key}: {'✅' if hit else '❌'}"
                        for key, hit in item["keyword_hits"].items()
                    ]
                )
                st.markdown(f"**Keyword Presence:** {keyword_status}")
                st.markdown(f"**Confidence Score:** {item['confidence_score']}/3")
                st.info(f"💡 Improvement Tip: {item['feedback_tip']}")
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("### Performance Chart")
            st.bar_chart(answer_metrics, x="Answer", y="Score", color="#38bdf8")
else:
    with st.container():
        st.info("Set up your interview from the sidebar, then click **Start Interview**.")
