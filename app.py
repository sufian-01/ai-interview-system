import streamlit as st

from ai_generator import generate_questions
from questions import get_questions
from scoring import calculate_score


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

st.title("AI Interview Setup")
st.write("Configure your interview and click **Start**.")

name = st.text_input("Name", placeholder="Enter your name")

topic = st.text_input(
    "Enter topic for AI-generated questions",
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

if st.button("Generate Questions"):
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

start_clicked = st.button("Start", type="primary")

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
    st.success("Interview started!")
    st.markdown(
        f"""
        **Candidate:** {st.session_state.candidate_name}  
        **Interview Type:** {st.session_state.interview_type}  
        **Difficulty:** {st.session_state.difficulty}
        """
    )

    st.divider()

    total_questions = len(st.session_state.selected_questions)
    current_idx = st.session_state.current_question_index

    if current_idx < total_questions:
        progress = (current_idx + 1) / total_questions
        st.progress(progress)

        left, center, right = st.columns([1, 3, 1])
        with center:
            st.subheader("Interview Session")
            st.caption(f"Question {current_idx + 1} of {total_questions}")
            st.markdown("---")

            current_question = st.session_state.selected_questions[current_idx]
            st.markdown(f"### {current_question}")

            answer_key = f"answer_{current_idx}"
            saved_answer = st.session_state.answers.get(current_idx, "")

            answer = st.text_area(
                "Your Answer",
                value=saved_answer,
                height=180,
                key=answer_key,
                placeholder="Type your answer here...",
            )

            st.write("")

            if st.button("Next", type="primary"):
                st.session_state.answers[current_idx] = answer
                st.session_state.current_question_index += 1
                st.rerun()
    else:
        st.progress(1.0)
        st.subheader("Interview Complete")
        st.write("Great work! You answered all questions.")
        st.markdown("---")

        ordered_answers = [
            st.session_state.answers.get(idx, "")
            for idx in range(len(st.session_state.selected_questions))
        ]
        final_score, feedback = calculate_score(ordered_answers)

        st.subheader("Interview Result")
        st.markdown(
            f"<h1 style='font-size:56px; margin-bottom:0;'>⭐ {final_score}/10</h1>",
            unsafe_allow_html=True,
        )

        if final_score >= 7:
            st.success("Strong overall performance. Keep it up!")
        else:
            st.warning("You can improve with more depth and positive framing.")

        st.markdown("### Feedback")
        for message in feedback:
            if "Excellent response" in message:
                st.success(message)
            else:
                st.warning(message)

        st.markdown("### All Answers Summary")
        for idx, question in enumerate(st.session_state.selected_questions, start=1):
            st.markdown(f"**Q{idx}. {question}**")
            response = st.session_state.answers.get(idx - 1, "No answer provided.")
            st.write(response)
            st.markdown("---")
