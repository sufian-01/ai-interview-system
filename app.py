import streamlit as st


st.set_page_config(page_title="AI Interview App", page_icon="🎤", layout="centered")

st.title("AI Interview Setup")
st.write("Configure your interview and click **Start**.")

name = st.text_input("Name", placeholder="Enter your name")

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

start_clicked = st.button("Start", type="primary")

if start_clicked:
    if not name.strip():
        st.warning("Please enter your name before starting.")
    else:
        st.success("Interview started!")
        st.markdown(
            f"""
            **Candidate:** {name.strip()}  
            **Interview Type:** {interview_type}  
            **Difficulty:** {difficulty}
            """
        )
