
import streamlit as st
import pandas as pd
from datetime import datetime
import os, re

st.set_page_config(page_title="Pause • Probe • Plan — Chat (Offline)", page_icon="🤝", layout="centered")

LOG_PATH = "chat_logs.csv"

# -------- Styles --------
BG = "#F7F7F7"
st.markdown(f"<style>body {{ background:{BG}; }}</style>", unsafe_allow_html=True)

st.title("🤝 Pause • Probe • Plan")
st.caption("No login. No API keys. Warm, validating chat that just works.")

# -------- Sidebar (teacher) --------
with st.sidebar:
    st.markdown("### Teacher settings")
    save_logs = st.toggle("Save anonymized summaries (CSV)", value=True)
    hotline = st.text_input("Safety help text", "If you need help now, tell a trusted adult or call/text 988 (US).")
    if os.path.exists(LOG_PATH):
        df = pd.read_csv(LOG_PATH)
        st.download_button("Download summaries (CSV)", data=df.to_csv(index=False).encode("utf-8"),
                           file_name="pause_probe_plan_chat_logs.csv", mime="text/csv")
    else:
        st.caption("No logs yet.")

# -------- Safety scan --------
RISK_TERMS = [
    "kill myself","want to die","suicide","hurt myself","cut myself","self-harm","self harm",
    "unsafe at home","they will hurt me","someone will hurt me","going to kill","kill them",
    "i can't go on","cant go on","no point","worthless","hopeless"
]
def risk_scan(text: str):
    low = (text or "").lower()
    hits = sorted({kw for kw in RISK_TERMS if kw in low})
    return (len(hits) > 0), hits

# -------- Age bands --------
AGE_TONES = {
    "K–2": {
        "opener": "I’m here with you. What happened?",
        "validate": "Thanks for telling me. I’m right here with you.",
        "feeling_q": "How do you feel? Mad, sad, or something else?",
        "values_q": "What matters most: kind, fair, or brave?",
        "plan_q": "What is one small thing you can try now?"
    },
    "3–5": {
        "opener": "Thanks for telling me. What went down?",
        "validate": "That makes sense. I hear you.",
        "feeling_q": "How are you feeling right now? (mad, sad, left out, worried, or something else)",
        "values_q": "What matters most here: kindness, fairness, honesty, courage, or caring?",
        "plan_q": "What’s one small step you could try next that fits that?"
    },
    "6–8": {
        "opener": "I’m listening. What happened?",
        "validate": "Yeah, that tracks. Thanks for being honest.",
        "feeling_q": "What feelings are here for you? (angry, sad, hurt, worried, frustrated, etc.)",
        "values_q": "What matters most to you in this: kindness, fairness, honesty, courage, caring, or learning?",
        "plan_q": "Thinking about the person you want to be, what’s one next step you’d be proud of?"
    }
}

# -------- State --------
if "age_band" not in st.session_state:
    st.session_state.age_band = None
if "msgs" not in st.session_state:
    st.session_state.msgs = []   # [{role, content}]
if "phase" not in st.session_state:
    st.session_state.phase = "age"  # age -> pause -> probe -> values -> plan -> card -> done
if "feelings" not in st.session_state:
    st.session_state.feelings = ""
if "value" not in st.session_state:
    st.session_state.value = ""
if "summary" not in st.session_state:
    st.session_state.summary = None
if "ended" not in st.session_state:
    st.session_state.ended = False

# -------- Helpers --------
def add(role, text):
    st.session_state.msgs.append({"role": role, "content": text})

def render():
    for m in st.session_state.msgs:
        with st.chat_message("assistant" if m["role"]=="assistant" else "user"):
            st.markdown(m["content"])

def make_plan_line(context, value, action):
    value_word = (value or "what matters to me").split(" ",1)[-1]
    context_part = f"when {context}" if context else "in tough moments"
    if not action:
        action = "take one small, kind step"
    return f"When I feel this way {context_part}, I will {action} — because {value_word.lower()} matters to me."

def save_summary(summary):
    if not save_logs: return
    row = {"timestamp": datetime.utcnow().isoformat(),
           "age_band": st.session_state.age_band or "",
           "turns": len(st.session_state.msgs),
           "summary": summary}
    try:
        if os.path.exists(LOG_PATH):
            df = pd.read_csv(LOG_PATH)
        else:
            df = pd.DataFrame(columns=row.keys())
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(LOG_PATH, index=False)
        st.toast("Saved.", icon="✅")
    except Exception as e:
        st.toast(f"Could not save: {e}", icon="⚠️")

# -------- Age picker --------
if st.session_state.phase == "age":
    st.write("Before we start, how old are you? This helps me talk in the best way for you.")
    c1, c2, c3 = st.columns(3)
    if c1.button("K–2"): st.session_state.age_band = "K–2"; st.session_state.phase = "pause"
    if c2.button("3–5"): st.session_state.age_band = "3–5"; st.session_state.phase = "pause"
    if c3.button("6–8"): st.session_state.age_band = "6–8"; st.session_state.phase = "pause"

# -------- Conversation engine (offline heuristics) --------
if st.session_state.phase == "pause" and not st.session_state.msgs:
    add("assistant", AGE_TONES[st.session_state.age_band]["opener"])

render()

user_text = st.chat_input("Type here…", disabled=st.session_state.ended)
if user_text and not st.session_state.ended:
    risky, hits = risk_scan(user_text)
    add("user", user_text)

    if risky:
        add("assistant", "That sounds really serious. I’m glad you told me. You matter and you deserve to feel safe. Let’s get you to a person who can help right now.")
        add("assistant", hotline)
        st.session_state.ended = True
        st.experimental_rerun()

    if st.session_state.phase == "pause":
        add("assistant", AGE_TONES[st.session_state.age_band]["validate"])
        add("assistant", AGE_TONES[st.session_state.age_band]["feeling_q"])
        st.session_state.context = user_text.strip()
        st.session_state.phase = "probe"

    elif st.session_state.phase == "probe":
        st.session_state.feelings = user_text.strip()
        add("assistant", "Thanks for telling me. Those feelings are real.")
        add("assistant", AGE_TONES[st.session_state.age_band]["values_q"])
        st.session_state.phase = "values"

    elif st.session_state.phase == "values":
        st.session_state.value = user_text.strip()
        add("assistant", f"Got it. {st.session_state.value.capitalize()} matters to you.")
        add("assistant", AGE_TONES[st.session_state.age_band]["plan_q"])
        st.session_state.phase = "plan"

    elif st.session_state.phase == "plan":
        st.session_state.action = user_text.strip()
        plan = make_plan_line(st.session_state.get("context",""), st.session_state.value, st.session_state.action)
        st.session_state.summary = plan
        add("assistant", "That’s a solid plan. I like how it sounds just like you.")
        add("assistant", "Tap **Make my plan card** to save it.")
        st.session_state.phase = "card"

    st.experimental_rerun()

# -------- Card & save --------
if st.session_state.phase == "card" and st.session_state.summary:
    if st.button("Make my plan card"):
        st.markdown("---")
        st.subheader("My Next Step")
        st.markdown(st.session_state.summary)
        st.caption("Proud of you for making a choice that matches your best self.")
        save_summary(st.session_state.summary)
        st.session_state.ended = True

# Reset
if st.session_state.ended:
    if st.button("Start again"):
        for k in ["age_band","msgs","phase","feelings","value","summary","ended","context","action"]:
            st.session_state.pop(k, None)
        st.experimental_rerun()
