import streamlit as st

from ai_generator import generate_questions
from face_detection import detect_face_from_webcam
from questions import get_questions
from scoring import calculate_score
from voice_input import record_voice


st.set_page_config(page_title="AI Interview App", page_icon="🎤", layout="centered")

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
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        background: #f8fafc;
        margin: 0.5rem 0 1rem 0;
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
if st.button("Start Camera", use_container_width=True):
    is_face_detected = detect_face_from_webcam()
    st.write(is_face_detected)

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
            st.markdown(
                f"<div class='question-card'><strong>Question:</strong><br>{current_question}</div>",
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

            ordered_answers = [
                st.session_state.answers.get(idx, "")
                for idx in range(len(st.session_state.selected_questions))
            ]
            final_score, feedback = calculate_score(ordered_answers)

            score_color = "#16a34a" if final_score >= 7 else "#dc2626"
            st.markdown(
                "<h3 style='text-align:center; margin-bottom:0.3rem;'>Interview Result</h3>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<h1 style='text-align:center; font-size:62px; color:{score_color}; "
                f"margin: 0.2rem 0 0.6rem 0;'>⭐ {final_score}/10</h1>",
                unsafe_allow_html=True,
            )

            if final_score >= 7:
                st.success("Strong overall performance. Keep it up!")
            else:
                st.error("You can improve with more depth and positive framing.")

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            st.markdown("### Feedback")
            feedback_items = "\n".join([f"- {message}" for message in feedback])
            st.markdown(feedback_items)

            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            st.markdown("### All Answers Summary")
            for idx, question in enumerate(st.session_state.selected_questions, start=1):
                st.markdown(f"**Q{idx}. {question}**")
                response = st.session_state.answers.get(idx - 1, "No answer provided.")
                st.write(response)
                st.markdown("---")
else:
    with st.container():
        st.info("Set up your interview from the sidebar, then click **Start Interview**.")
