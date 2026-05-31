# uv sync
# uv run streamlit run Student.py

import os
import re
import time
from datetime import datetime, timedelta

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from utils import load_json, save_result

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Kids Learning App",
    page_icon="📚",
    layout="centered"
)

# --------------------------------------------------
# GLOBAL STYLING (UNCHANGED)
# --------------------------------------------------

st.markdown(
    """
    <style>

    html, body, [class*="css"] {
        font-size: 20px !important;
    }

    label {
        font-size: 22px !important;
        font-weight: 700 !important;
    }

    input, select {
        font-size: 20px !important;
    }

    div[role="radiogroup"] label {
        font-size: 20px !important;
        padding: 8px !important;
    }

    button {
        font-size: 22px !important;
        font-weight: 800 !important;
        padding: 12px !important;
    }

    h1 { font-size: 40px !important; }
    h2 { font-size: 34px !important; }
    h3 { font-size: 28px !important; }

    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.markdown(
    """
    <h1 style='text-align:center; color:#4CAF50;'>
        🎓 Fun Learning Zone
    </h1>
    <h4 style='text-align:center; color:#888;'>
        Play • Learn • Improve 🚀
    </h4>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "started" not in st.session_state:
    st.session_state.started = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "end_time" not in st.session_state:
    st.session_state.end_time = None

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "submitted" not in st.session_state:
    st.session_state.submitted = False

# --------------------------------------------------
# INITIALIZE BUTTON STATES (Prevents NameErrors)
# --------------------------------------------------
submit_clicked = False
cancel_clicked = False
auto_submit = False

# --------------------------------------------------
# INPUTS
# --------------------------------------------------

student_name = st.text_input("👦 Student Name")

subject = st.selectbox("📘 Choose Subject", ["Math", "English"])

test_folder = f"tests/{subject.lower()}"

# --------------------------------------------------
# LOAD TEST FILES WITH DISPLAY NAME = test_name (SORTED SEQUENTIALLY)
# --------------------------------------------------

# Get raw list of test files
test_files = [f for f in os.listdir(test_folder) if f.endswith(".json")]

test_options = []

for f in test_files:
    path = os.path.join(test_folder, f)
    data = load_json(path)

    # Fallback to file name if 'test_name' key doesn't exist
    name = data.get("test_name", f.replace(".json", ""))

    test_options.append({
        "label": name,
        "file": f
    })

# Helper function to extract text chunks and integers for natural sequential sorting
# E.g., "Math Assignment - 2" comes BEFORE "Math Assignment - 13"
def natural_sort_key(option):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', option["label"])]

# Sort the test options based on the extracted Exam Name sequentially
test_options = sorted(test_options, key=natural_sort_key)

selected_label = st.selectbox(
    "📝 Choose Test",
    [t["label"] for t in test_options]
)

selected_file = next(
    t["file"] for t in test_options if t["label"] == selected_label
)

filepath = os.path.join(test_folder, selected_file)
test_data = load_json(filepath)

# --------------------------------------------------
# START TEST
# --------------------------------------------------

if not st.session_state.started:

    st.markdown("### 🚀 Ready for a Challenge?")

    if st.button("Start Test", use_container_width=True):

        if not student_name.strip():
            st.warning("Please enter your name 😊")
            st.stop()

        timer_minutes = int(test_data.get("timer_minutes", len(test_data["questions"])))

        st.session_state.started = True
        st.session_state.start_time = datetime.now()
        st.session_state.end_time = datetime.now() + timedelta(minutes=timer_minutes)
        st.session_state.answers = {}
        st.session_state.submitted = False  # Reset submission tracker

        st.rerun()

# --------------------------------------------------
# TEST SCREEN
# --------------------------------------------------

if st.session_state.started:

    # Only run refresh loop if the test hasn't been finished/submitted yet
    if not st.session_state.submitted:
        st_autorefresh(interval=1000, key="timer_refresh")

    st.markdown(f"## 📘 {test_data['test_name']}")

    remaining_seconds = int(
        (st.session_state.end_time - datetime.now()).total_seconds()
    )

    remaining_seconds = max(0, remaining_seconds)

    auto_submit = (remaining_seconds == 0 and not st.session_state.submitted)

    mins = remaining_seconds // 60
    secs = remaining_seconds % 60

    st.markdown(
        f"""
        <div style="
            background:linear-gradient(90deg,#ff4b4b,#ff7676);
            padding:14px;
            border-radius:12px;
            text-align:center;
            color:white;
            font-size:26px;
            font-weight:900;
            margin-bottom:10px;">
            ⏰ Time Left: {mins:02d}:{secs:02d}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.progress(
        remaining_seconds / (test_data.get("timer_minutes", len(test_data["questions"])) * 60)
    )

    st.markdown("---")

    # --------------------------------------------------
    # QUESTIONS (MCQ + FILL SUPPORT)
    # --------------------------------------------------

    total_questions = len(test_data["questions"])

    for idx, q in enumerate(test_data["questions"]):

        q_type = q.get("type", "mcq")

        st.markdown(
            f"""
            <div style="
                background:#e8f3ff;
                padding:16px;
                border-radius:12px;
                font-size:22px;
                font-weight:700;
                margin-bottom:6px;">
                ❓ Q{idx+1}: {q['question']}
            </div>
            """,
            unsafe_allow_html=True
        )

        if q_type == "mcq":
            st.session_state.answers[idx] = st.radio(
                "Choose answer:",
                q["options"],
                index=None,
                key=f"q_{idx}",
                disabled=st.session_state.submitted  # Freeze forms on submission
            )
        else:
            st.session_state.answers[idx] = st.text_input(
                "Your Answer:",
                key=f"q_{idx}",
                disabled=st.session_state.submitted  # Freeze fields on submission
            )

    answered_count = sum(
        1 for v in st.session_state.answers.values() if v not in [None, ""]
    )

    st.markdown(f"### 🎯 Progress: {answered_count}/{total_questions}")

    st.progress(answered_count / total_questions)

    # --------------------------------------------------
    # ACTION BUTTONS
    # --------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        submit_clicked = st.button(
            "🎯 Submit Test",
            use_container_width=True,
            disabled=st.session_state.submitted  # Disables the button dynamically
        )

    with col2:
        cancel_clicked = st.button(
            "❌ Cancel Test",
            use_container_width=True,
            disabled=st.session_state.submitted
        )

# --------------------------------------------------
# CANCEL TEST
# --------------------------------------------------

if cancel_clicked:

    st.session_state.started = False
    st.session_state.start_time = None
    st.session_state.end_time = None
    st.session_state.answers = {}
    st.session_state.submitted = False

    st.warning("❌ Test cancelled.")

    st.rerun()

# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

if (submit_clicked and not auto_submit):

    unanswered = any(
        v is None or str(v).strip() == ""
        for v in st.session_state.answers.values()
    )

    if unanswered:
        st.warning("Please answer all questions 😊")
        st.stop()

# --------------------------------------------------
# SUBMIT LOGIC
# --------------------------------------------------

if (submit_clicked or auto_submit) and not st.session_state.submitted:

    # Lock submission sequence immediately
    st.session_state.submitted = True

    score = 0
    details = []

    for idx, q in enumerate(test_data["questions"]):

        selected = st.session_state.answers.get(idx)

        if selected is None or selected == "":
            selected = "Not Answered"

        correct = q["answer"]

        is_correct = str(selected).strip().lower() == str(correct).strip().lower()

        if is_correct:
            score += 1

        details.append({
            "question": q["question"],
            "selected": selected,
            "correct": correct,
            "is_correct": is_correct
        })

    total = len(test_data["questions"])
    percentage = round(score / total * 100, 1)

    end_time = datetime.now()
    duration = (end_time - st.session_state.start_time).total_seconds()

    result = {
        "student": student_name.strip().upper(),
        "subject": subject,
        "test_name": test_data["test_name"],
        "score": score,
        "total": total,
        "percentage": percentage,
        "duration_seconds": round(duration),
        "completed_before_timeout": not auto_submit,
        "start_time": st.session_state.start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "answers": details
    }

    save_result(result)

    # Force a rerun to gray out the inputs and buttons before showing balloons
    st.rerun()

# --------------------------------------------------
# DISPLAY RESULTS AFTER DOCKING BACKEND DATA
# --------------------------------------------------
if st.session_state.submitted and st.session_state.started:
    st.balloons()
    
    # Recalculate values from inputs to display score safely
    score = 0
    for idx, q in enumerate(test_data["questions"]):
        selected = st.session_state.answers.get(idx)
        if str(selected).strip().lower() == str(q["answer"]).strip().lower():
            score += 1
    total = len(test_data["questions"])
    percentage = round(score / total * 100, 1)

    st.success(f"🎉 Score: {score}/{total} ({percentage}%)")
    
    # Hold UI visibility before wiping test loop variables completely
    time.sleep(3)

    # RESET STATE
    st.session_state.started = False
    st.session_state.start_time = None
    st.session_state.end_time = None
    st.session_state.answers = {}
    st.session_state.submitted = False
    
    st.rerun()