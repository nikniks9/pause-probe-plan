
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(page_title="Pause • Probe • Plan (Kid Conflict Coach)", page_icon="🧠", layout="centered")

APP_NAME = "Pause • Probe • Plan"
DATA_PATH = "sessions.csv"

# Neutral, school-friendly palette
BG_COLOR = "#F7F7F7"
CARD_BG = "#FFFFFF"
ACCENT = "#4A5568"   # slate gray
ACCENT_SOFT = "#A0AEC0"
SUCCESS = "#2F855A"  # green-ish
WARN = "#C05621"     # warm orange
DANGER = "#9B2C2C"   # deep red

MOOD_OPTIONS = ["😡 Angry", "😢 Sad", "😐 Okay", "🙂 Better", "😄 Good"]
VALUE_OPTIONS = ["🤝 Kindness", "⚖️ Fairness", "💪 Courage", "🗣 Honesty", "❤️ Caring", "🧠 Learning"]

POLYVAGAL_STATES = {
    "🏃 Fast & buzzy": {
        "label": "Fast & buzzy",
        "tip_title": "Blow out the candles",
        "tip": "Take 3 slow breaths. Breathe in through your nose, then blow out like you're blowing out a birthday candle. Longer exhale.",
    },
    "🐢 Slow & heavy": {
        "label": "Slow & heavy",
        "tip_title": "Big stretch",
        "tip": "Stand tall, reach up to the sky, shake your hands and feet for 10 seconds. Get some gentle movement.",
    },
    "🌞 Calm & steady": {
        "label": "Calm & steady",
        "tip_title": "Stay steady",
        "tip": "Place your hands on your heart. Notice 3 things you can see, 2 things you can hear, and 1 thing you can feel.",
    }
}

RISK_KEYWORDS = {
    "suicide","kill myself","want to die","hurt myself","cut myself","self harm","self-harm",
    "i cant go on","no point","worthless","hopeless","im in danger","someone will hurt me",
    "they will hurt me","abuse","unsafe at home","going to kill"
}

# -----------------------------
# Helpers
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data():
    try:
        df = pd.read_csv(DATA_PATH)
        # ensure expected columns
        expected = [
            "timestamp","student_id","polyvagal_state","mood","context",
            "feelings","values","what_happened","plan_action","plan_support",
            "risk_flag","risk_terms"
        ]
        for c in expected:
            if c not in df.columns:
                df[c] = ""
        return df[expected]
    except Exception:
        return pd.DataFrame(columns=[
            "timestamp","student_id","polyvagal_state","mood","context",
            "feelings","values","what_happened","plan_action","plan_support",
            "risk_flag","risk_terms"
        ])

def save_row(row: dict):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)

def risk_scan_text(*texts):
    text = " ".join([t.lower() for t in texts if t])
    hits = sorted({kw for kw in RISK_KEYWORDS if kw in text})
    return (len(hits) > 0), hits

def make_card(plan_text, feelings, values, context):
    # Simple HTML card using neutrals
    feelings_html = st.session_state.get("feelings_display", feelings)
    values_html = st.session_state.get("values_display", values)
    html = f"""
    <div style="background:{CARD_BG}; padding: 18px 18px; border: 1px solid {ACCENT_SOFT}; border-radius: 12px; max-width: 720px;">
      <div style="color:{ACCENT}; font-weight: 700; font-size: 18px; margin-bottom: 6px;">My Next Step</div>
      <div style="color:{ACCENT_SOFT}; font-size: 13px; margin-bottom: 12px;">A quick plan for moments that feel tough.</div>
      <div style="display:flex; gap:16px; flex-wrap:wrap;">
        <div style="flex:1; min-width:220px; background:{BG_COLOR}; border-radius:10px; padding:12px;">
          <div style="color:{ACCENT}; font-weight:600; font-size:14px;">I'm feeling</div>
          <div style="margin-top:4px; font-size:15px;">{feelings_html or "—"}</div>
        </div>
        <div style="flex:1; min-width:220px; background:{BG_COLOR}; border-radius:10px; padding:12px;">
          <div style="color:{ACCENT}; font-weight:600; font-size:14px;">What matters to me</div>
          <div style="margin-top:4px; font-size:15px;">{values_html or "—"}</div>
        </div>
      </div>
      <div style="margin-top:14px; background:{BG_COLOR}; border-radius:10px; padding:12px;">
        <div style="color:{ACCENT}; font-weight:600; font-size:14px;">My plan</div>
        <div style="margin-top:4px; font-size:16px;">{plan_text or "—"}</div>
      </div>
      <div style="margin-top:14px; font-size:13px; color:{ACCENT_SOFT};">Proud of you for making a choice that matches your best self.</div>
    </div>
    """
    return html

def build_commitment(context, values, action):
    # Short friendly "I will" statement
    context_part = f"when {context}" if context else "in tough moments"
    value_word = values.replace("🤝 ","").replace("⚖️ ","").replace("💪 ","").replace("🗣 ","").replace("❤️ ","").replace("🧠 ","")
    plan = f"When I feel this way {context_part}, I will {action.strip()} — because {value_word.lower()} matters to me."
    return plan

# -----------------------------
# Styles
# -----------------------------
st.markdown(f"""
    <style>
    .block-container {{ padding-top: 2rem; }}
    body {{ background: {BG_COLOR}; }}
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar (Teacher Mode + Settings)
# -----------------------------
with st.sidebar:
    st.markdown("### Teacher view & settings")
    teacher_mode = st.toggle("Teacher mode (view responses)", value=False, help="View anonymized responses and class-level summaries.")
    allow_storage = st.toggle("Save student responses locally", value=True, help="Stores entries to sessions.csv in this app's folder.")
    st.caption("No cloud storage by default. You can export CSV if needed.")
    st.divider()
    st.markdown("**Safety text (school-specific):**")
    hotline = st.text_input("Hotline/Help text", value="If you need immediate help, tell a trusted adult now or call/text 988 (US).")

# -----------------------------
# Teacher mode dashboard
# -----------------------------
if teacher_mode:
    st.subheader("Class Snapshot")
    df = load_data()
    if df.empty:
        st.info("No sessions yet. Once students save entries, you'll see anonymized info here.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total sessions", len(df))
        last_7 = df[pd.to_datetime(df["timestamp"]) >= (datetime.now() - timedelta(days=7))]
        col2.metric("Sessions (7 days)", len(last_7))
        risk_rate = 100.0 * df["risk_flag"].astype(bool).mean() if len(df) else 0.0
        col3.metric("Safety flags", f"{risk_rate:.0f}%")
        st.markdown("#### Mood distribution")
        mood_counts = df["mood"].value_counts()
        st.bar_chart(mood_counts)
        st.markdown("#### Values chosen")
        val_counts = df["values"].value_counts()
        st.bar_chart(val_counts)
        st.download_button("Download all responses (CSV)",
                           data=df.to_csv(index=False).encode("utf-8"),
                           file_name="pause_probe_plan_sessions.csv",
                           mime="text/csv")
    st.divider()

# -----------------------------
# Title & Intro (friend tone)
# -----------------------------
st.title("Pause • Probe • Plan")
st.caption("A quick friend to help you steady your body, name your feelings, and make a plan that matches your best self.")

# -----------------------------
# Pause — Polyvagal-informed
# -----------------------------
st.header("Pause")
st.write("Before we talk about what happened, let's check how your body feels right now. Which one feels most like you?")

poly_state = st.radio("My body feels…", list(POLYVAGAL_STATES.keys()), horizontal=True, label_visibility="collapsed")

if poly_state:
    tip = POLYVAGAL_STATES[poly_state]
    with st.container():
        st.markdown(f"**{tip['tip_title']}**  \n{tip['tip']}")
        st.markdown("_When you're ready, we'll keep going._")

# -----------------------------
# Probe — What happened & feelings
# -----------------------------
st.header("Probe")
context = st.text_input("What happened? (Just say it like you'd tell a friend.)")

feelings = st.multiselect("What are you feeling right now? (You can pick more than one.)",
                          MOOD_OPTIONS, default=None)

# show chosen feelings nicely
if feelings:
    st.session_state["feelings_display"] = ", ".join(feelings)

values = st.selectbox("What matters most to you here?",
                      VALUE_OPTIONS, index=0)

if values:
    st.session_state["values_display"] = values

# -----------------------------
# Plan — Next step
# -----------------------------
st.header("Plan")
plan_action = st.text_input("Think about the kind of person you want to be. What's one small thing you could do right now that fits that?")
plan_support = st.text_input("Who could help you with this plan? (friend, teacher, family) (optional)")

# -----------------------------
# Safety Scan + Save
# -----------------------------
def safety_mode_message(hotline_text):
    st.error("That sounds really serious. I'm glad you told me.")
    st.write("You matter a lot, and you deserve to feel safe.")
    st.write("Let's get you to a person who can help right now.")
    st.info(hotline_text)

if st.button("Save my plan"):
    # risk scan
    risk_flag, hits = risk_scan_text(context, " ".join(feelings) if feelings else "", values, plan_action)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "timestamp": timestamp,
        "student_id": "",  # optional; omitted in MVP for privacy
        "polyvagal_state": poly_state or "",
        "mood": ", ".join(feelings) if feelings else "",
        "context": context.strip(),
        "feelings": ", ".join(feelings) if feelings else "",
        "values": values or "",
        "what_happened": context.strip(),
        "plan_action": plan_action.strip(),
        "plan_support": plan_support.strip(),
        "risk_flag": bool(risk_flag),
        "risk_terms": ", ".join(hits) if hits else ""
    }

    if risk_flag:
        safety_mode_message(hotline)
        # store minimal info even if safety? We'll store the row so teacher can follow up
        if allow_storage:
            save_row(row)
    else:
        # normal flow
        plan_text = build_commitment(context, values or "", plan_action or "")
        card_html = make_card(plan_text, row["feelings"], row["values"], context)
        st.success("Saved. Here's your card — nice work.")
        st.components.v1.html(card_html, height=340)
        st.download_button("Download my plan (.txt)",
                           data=(f"{APP_NAME} — My Next Step\nTime: {timestamp}\n\n"
                                 f"I'm feeling: {row['feelings']}\n"
                                 f"What matters to me: {row['values']}\n"
                                 f"My plan: {plan_text}\n").encode("utf-8"),
                           file_name="my-next-step.txt",
                           mime="text/plain")
        if allow_storage:
            save_row(row)
        st.caption("Proud of you for making a choice that matches your best self.")

st.markdown("---")
st.caption("Built for schools. No data leaves this app unless a teacher downloads it.")
