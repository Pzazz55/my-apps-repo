import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from utils import load_results

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Parent Dashboard",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------
# UI STYLE (MATCH app.py)
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

    div[data-testid="stSidebar"] * {
        font-size: 20px !important;
        font-weight: 600 !important;
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
        📊 Parent Learning Dashboard
    </h1>
    <h4 style='text-align:center; color:#888;'>
        Track • Understand • Improve 📈
    </h4>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

results = load_results()

if not results:
    st.warning("No test attempts found yet.")
    st.stop()

df = pd.DataFrame(results)

# --------------------------------------------------
# SAFE NORMALIZATION
# --------------------------------------------------

if "answers" not in df.columns:
    df["answers"] = [[] for _ in range(len(df))]

df["end_time"] = pd.to_datetime(df.get("end_time", pd.NaT), errors="coerce")
df = df.dropna(subset=["end_time"])

# --------------------------------------------------
# DRILL STATE
# --------------------------------------------------

if "selected_attempt" not in st.session_state:
    st.session_state.selected_attempt = None

# ==================================================
# VIEW MODE (DRILL DOWN)
# ==================================================

if st.session_state.selected_attempt is not None:

    if st.button("⬅ Back"):
        st.session_state.selected_attempt = None
        st.rerun()

    attempt = st.session_state.selected_attempt

    st.subheader("📄 Assignment Review")

    completed_dt = pd.to_datetime(attempt.get("end_time")).strftime("%d/%m/%Y %H:%M")

    st.write(f"👦 Student: {attempt.get('student','')}")
    st.write(f"📘 Subject: {attempt.get('subject','')}")
    st.write(f"📝 Assignment: {attempt.get('test_name','')}")
    st.write(f"📊 Score: {attempt.get('score',0)}/{attempt.get('total',0)}")
    st.write(f"📈 Percentage: {attempt.get('percentage',0)}%")
    st.write(f"📅 Completed: {completed_dt}")

    st.markdown("---")
    st.subheader("❓ Question Feedback")

    for i, ans in enumerate(attempt.get("answers", [])):

        question = ans.get("question", "").replace("<b>", "").replace("</b>", "").replace("<br>", "")

        st.markdown(f"""
        **Q{i+1}: {question}**

        🧒 Your Answer: **{ans.get('selected','')}** ✅ Correct Answer: **{ans.get('correct','')}**

        {"🟢 Correct" if ans.get("is_correct", False) else "🔴 Wrong"}

        ---
        """)

    st.stop()

# ==================================================
# MAIN DASHBOARD FLOW
# ==================================================

students = sorted(df["student"].unique())

# Fix: Intercept and set initial index if redirected from a completed student test
default_index = 0
if "selected_student_from_test" in st.session_state:
    forwarded_student = st.session_state["selected_student_from_test"]
    if forwarded_student in students:
        default_index = students.index(forwarded_student)
    # Clear the temporary signal to avoid locking the selectbox value permanently
    del st.session_state["selected_student_from_test"]

selected_student = st.selectbox("👦 Select Student", students, index=default_index)

df = df[df["student"] == selected_student]

# Fix Attempt Ordering: Sort ascending (oldest first) to compute correct chronologically increasing attempts
df = df.sort_values("end_time", ascending=True)
df["AttemptNumber"] = df.groupby(["subject", "test_name"]).cumcount() + 1

# Sort back to descending order so parents see the newest completions at the top of the UI
df = df.sort_values("end_time", ascending=False)
df["CompletedDateTime"] = df["end_time"].dt.strftime("%d/%m/%Y %H:%M")

# --------------------------------------------------
# SCORE CALCULATION FIX (Correct / Total)
# --------------------------------------------------

total_correct = 0
total_questions = 0

for _, r in df.iterrows():
    for ans in r.get("answers", []):
        total_questions += 1
        if ans.get("is_correct"):
            total_correct += 1

avg_percentage = round((total_correct / total_questions) * 100, 1) if total_questions else 0

# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

c1, c2 = st.columns(2)
c1.metric("📚 Assignments", len(df))
c2.metric("🎯 Score", f"{total_correct}/{total_questions} ({avg_percentage}%)")

st.markdown("---")

# ==================================================
# ATTEMPT HISTORY
# ==================================================

st.subheader("📋 Attempt History")

header = st.columns([1,2,3,1,1,2,1])
header[0].markdown("**Attempt**")
header[1].markdown("**Subject**")
header[2].markdown("**Exam Name**")
header[3].markdown("**Total**")
header[4].markdown("**Correct (%)**")
header[5].markdown("**Date**")
header[6].markdown("**Action**")

for i, row in df.iterrows():

    cols = st.columns([1,2,3,1,1,2,1])

    cols[0].write(row["AttemptNumber"])
    cols[1].write(row["subject"])
    cols[2].write(row["test_name"])
    cols[3].write(row["total"])
    cols[4].write(f"{row['percentage']}%")
    cols[5].write(row["CompletedDateTime"])

    if cols[6].button("View", key=f"view_{i}"):
        st.session_state.selected_attempt = row.to_dict()
        st.rerun()

# ==================================================
# DATE FILTER
# ==================================================

st.markdown("---")
st.subheader("📅 Analysis Filters")

min_date = df["end_time"].min().date() if not df.empty else None
max_date = df["end_time"].max().date() if not df.empty else None

if min_date and max_date:

    col1, col2 = st.columns(2)

    with col1:
        from_date = st.date_input("From Date", min_date)

    with col2:
        to_date = st.date_input("To Date", max_date)

    filtered_df = df[
        (df["end_time"].dt.date >= from_date) &
        (df["end_time"].dt.date <= to_date)
    ]

else:
    filtered_df = pd.DataFrame()

if filtered_df.empty:
    st.warning("⚠️ No information available for selected date range.")
    st.stop()

# ==================================================
# SUBJECT PERFORMANCE
# ==================================================

st.subheader("📘 Subject Performance (Accuracy)")

col1, col2 = st.columns(2)

for idx, subject in enumerate(["Math", "English"]):

    sub_df = filtered_df[filtered_df["subject"] == subject]

    correct = 0
    total = 0

    for _, row in sub_df.iterrows():
        for ans in row.get("answers", []):
            total += 1
            if ans.get("is_correct"):
                correct += 1

    incorrect = total - correct if total > 0 else 0

    fig = go.Figure(data=[go.Pie(
        labels=["Correct", "Incorrect"],
        values=[correct, incorrect],
        hole=0.4
    )])

    fig.update_layout(title=f"{subject} Accuracy")

    if idx == 0:
        col1.plotly_chart(fig, use_container_width=True)
    else:
        col2.plotly_chart(fig, use_container_width=True)

# ==================================================
# WEEKLY PROGRESS TREND (FIXED DUPLICATES + TOOLTIP METRICS)
# ==================================================

st.subheader("📈 Weekly Progress Trend")

weekly_df = filtered_df.copy()

# Convert to week start date
weekly_df["week"] = weekly_df["end_time"].dt.to_period("W").apply(lambda r: r.start_time)

# --------------------------------------------------
# Build question-level accuracy data safely
# --------------------------------------------------

rows = []

for _, r in weekly_df.iterrows():
    for ans in r.get("answers", []):
        rows.append({
            "week": r["week"],
            "subject": r["subject"],
            "is_correct": 1 if ans.get("is_correct") else 0
        })

if not rows:
    st.warning("No data available for weekly trend")
    st.stop()

qdf = pd.DataFrame(rows)

# --------------------------------------------------
# Aggregate safely (NO pivot crash)
# --------------------------------------------------

agg = (
    qdf
    .groupby(["week", "subject"])
    .agg(
        correct=("is_correct", "sum"),
        total=("is_correct", "count")
    )
    .reset_index()
)

agg["percent"] = (agg["correct"] / agg["total"] * 100).round(1)

# --------------------------------------------------
# Build chart with hover details
# --------------------------------------------------

fig = go.Figure()

for subject in agg["subject"].unique():

    sub = agg[agg["subject"] == subject]

    fig.add_trace(
        go.Bar(
            x=sub["week"].dt.strftime("%d-%b-%y"),
            y=sub["percent"],
            name=subject,
            customdata=sub[["correct", "total"]],
            hovertemplate=(
                "Week: %{x}<br>"
                "Total: %{customdata[1]}<br>"
                "Correct: %{customdata[0]}<br>"
                "Pcnt: %{y}%<extra></extra>"
            )
        )
    )

fig.update_layout(
    title="Weekly Progress Trend",
    yaxis=dict(range=[0, 100], fixedrange=True),
    xaxis=dict(type="category", fixedrange=True),
    barmode="group"
)

st.plotly_chart(fig, use_container_width=True)