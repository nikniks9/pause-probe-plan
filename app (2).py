
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Pause • Probe • Plan — Chat", page_icon="🫶", layout="centered")

APP_NAME = "Pause • Probe • Plan"
DATA_PATH = "sessions.csv"

# --- Visual palette (neutral school-friendly) ---
BG = "#F7F7F7"
INK = "#2D3748"
INK_SOFT = "#718096"
ACCENT = "#4A5568"

css = """
<style>
  .block-container {{ padding-top: 2rem; }}
  body {{ background: BGVAR; }}
  .bubble {{ background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; }}

  /* Breathing circle */
  .breath-container {{
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 12px 0 6px 0;
  }}
  .breath-circle {{
    width: 120px;
    height: 120px;
    border-radius: 60px;
    border: 2px solid #CBD5E0;
    background: radial-gradient(circle at center, #FFFFFF 60%, #EDF2F7 100%);
    animation: breathe 6s ease-in-out infinite;
  }}
  @keyframes breathe {{
    0%   {{ transform: scale(1.0); }}
    50%  {{ transform: scale(1.25); }}
    100% {{ transform: scale(1.0); }}
  }}
  .breath-instruction {{
    text-align: center; color: INKSOFTVAR; font-size: 14px; margin-top: 6px;
  }}
</style>
""".replace("BGVAR", BG).replace("INKSOFTVAR", INK_SOFT)

st.markdown(css, unsafe_allow_html=True)

# --- Data + helpers ---
@st.cache_data(show_spinner=False)
def load_data():
    try:
        df = pd.read_csv(DATA_PATH)
    except Exception:
        df = pd.DataFrame(columns=[
            "timestamp","student_id","polyvagal_state","mood","context","feelings","values",
            "what_happened","plan_action","plan_support","risk_flag","risk_terms"
        ])
    return df

def save_row(row):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)

RISK_KEYWORDS = {
    "suicide","kill myself","want to die","hurt myself","cut myself","self harm","self-harm",
    "i cant go on","no point","worthless","hopeless","im in danger","someone will hurt me",
    "they will hurt me","abuse","unsafe at home","going to kill"
}

def risk_scan(text):
    if not text: return False, []
    low = text.lower()
    hits = sorted({kw for kw in RISK_KEYWORDS if kw in low})
    return len(hits) > 0, hits

FEEL_OPTIONS = ["😡 Angry","😢 Sad","😐 Okay","🙂 Better","😄 Good"]
VALUE_OPTIONS = ["🤝 Kindness","⚖️ Fairness","💪 Courage","🗣 Honesty","❤️ Caring","🧠 Learning"]
STATE_OPTIONS = ["🏃 Fast & buzzy","🐢 Slow & heavy","🌞 Calm & steady"]

STATE_TIPS = {
    "🏃 Fast & buzzy": ("Blow out the candles",
                        "Let’s try 3 slow breaths. In through your nose… and blow out like a candle. Make the exhale a little longer."),
    "🐢 Slow & heavy": ("Big stretch",
                        "Let’s stand up and reach tall, then shake out hands and feet for 10 seconds. A little movement can wake the body."),
    "🌞 Calm & steady": ("Stay steady",
                         "Hands on heart. Notice 3 things you can see, 2 you can hear, 1 you can feel. Nice and easy.")
}

# --- Sidebar (teacher controls) ---
with st.sidebar:
    st.markdown("### Teacher settings")
    teacher_mode = st.toggle("Teacher mode (view responses)", value=False)
    allow_storage = st.toggle("Save responses locally", value=True)
    hotline = st.text_input("Safety help text", "If you need help now, tell a trusted adult or call/text 988 (US).")
    st.caption("No cloud storage by default. Export CSV from Teacher mode.")

if teacher_mode:
    st.subheader("Class snapshot")
    df = load_data()
    if df.empty:
        st.info("No entries yet.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total sessions", len(df))
        last_7 = df[pd.to_datetime(df["timestamp"]) >= (datetime.now() - timedelta(days=7))]
        c2.metric("Last 7 days", len(last_7))
        c3.metric("Safety flags", f"{100*df['risk_flag'].astype(bool).mean():.0f}%")
        st.markdown("#### Mood distribution")
        st.bar_chart(df["mood"].value_counts())
        st.markdown("#### Values chosen")
        st.bar_chart(df["values"].value_counts())
        st.download_button("Download CSV", data=df.to_csv(index=False).encode("utf-8"),
                           file_name="pause_probe_plan_sessions.csv", mime="text/csv")
    st.divider()

st.title("Pause • Probe • Plan")
st.caption("A warm, friendly chat to help you steady your body, name your feelings, and make a plan that matches your best self.")

# --- Chat state ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "step" not in st.session_state:
    st.session_state.step = "intro"
if "entry" not in st.session_state:
    st.session_state.entry = {
        "timestamp": "",
        "student_id": "",
        "polyvagal_state": "",
        "mood": "",
        "context": "",
        "feelings": "",
        "values": "",
        "what_happened": "",
        "plan_action": "",
        "plan_support": "",
        "risk_flag": False,
        "risk_terms": ""
    }
if "breath_run" not in st.session_state:
    st.session_state.breath_run = False

def say(role, text):
    st.session_state.messages.append({"role": role, "text": text})

def render_messages():
    for m in st.session_state.messages:
        with st.chat_message("assistant" if m["role"]=="bot" else "user"):
            st.markdown(m["text"])

def reset_chat():
    st.session_state.messages = []
    st.session_state.step = "intro"
    st.session_state.entry = {
        "timestamp": "",
        "student_id": "",
        "polyvagal_state": "",
        "mood": "",
        "context": "",
        "feelings": "",
        "values": "",
        "what_happened": "",
        "plan_action": "",
        "plan_support": "",
        "risk_flag": False,
        "risk_terms": ""
    }
    st.session_state.breath_run = False

def breathing_animation(seconds=30):
    # Visual circle + countdown
    st.markdown('<div class="breath-container"><div class="breath-circle"></div></div>', unsafe_allow_html=True)
    msg = st.empty()
    for t in range(seconds, 0, -1):
        # Alternate prompts roughly every 3 seconds
        phase = "Breathe in…" if (t // 3) % 2 == 0 else "Breathe out…"
        msg.markdown(f'<div class="breath-instruction">{phase} {t}s</div>', unsafe_allow_html=True)
        time.sleep(1)
    msg.markdown('<div class="breath-instruction">Nice work. Let’s keep going.</div>', unsafe_allow_html=True)

# --- Conversation flow ---
if st.session_state.step == "intro":
    say("bot", "Hey, I’m here with you. Before we talk about what happened, let’s help your body feel okay.")
    say("bot", "How does your body feel right now?\n\n• 🏃 Fast & buzzy\n• 🐢 Slow & heavy\n• 🌞 Calm & steady\n\nYou can type one of these or click a button below.")
    st.session_state.step = "ask_state"

render_messages()

# quick-pick buttons (also allow typed answers)
if st.session_state.step == "ask_state":
    cols = st.columns(3)
    if cols[0].button("🏃 Fast & buzzy"):
        user_choice = "🏃 Fast & buzzy"
    elif cols[1].button("🐢 Slow & heavy"):
        user_choice = "🐢 Slow & heavy"
    elif cols[2].button("🌞 Calm & steady"):
        user_choice = "🌞 Calm & steady"
    else:
        user_choice = None

    user_text = st.chat_input("Type your choice (🏃 / 🐢 / 🌞)")
    if user_text:
        # map simple emojis/words to options
        if "🏃" in user_text or "buzzy" in user_text.lower() or "fast" in user_text.lower():
            user_choice = "🏃 Fast & buzzy"
        elif "🐢" in user_text or "slow" in user_text.lower() or "heavy" in user_text.lower():
            user_choice = "🐢 Slow & heavy"
        elif "🌞" in user_text or "calm" in user_text.lower() or "steady" in user_text.lower():
            user_choice = "🌞 Calm & steady"

    if user_choice:
        st.session_state.messages.append({"role":"user","text":user_choice})
        st.session_state.entry["polyvagal_state"] = user_choice
        tip_title, tip = STATE_TIPS[user_choice]
        say("bot", f"Thanks for sharing. {tip_title}:\n\n{tip}")
        say("bot", "Want to try a 30-second breathing animation together? Click the button when you're ready.")
        st.session_state.step = "breathing_offer"

elif st.session_state.step == "breathing_offer":
    if st.button("Start 30-second breathing"):
        st.session_state.breath_run = True
        st.session_state.step = "breathing_run"
        st.experimental_rerun()

elif st.session_state.step == "breathing_run":
    # show animation + countdown
    breathing_animation(30)
    say("bot", "Nice job. When you’re ready, tell me what happened. Just say it like you’d tell a friend.")
    st.session_state.step = "ask_context"
    st.experimental_rerun()

elif st.session_state.step == "ask_context":
    user_text = st.chat_input("What happened?")
    if user_text:
        st.session_state.messages.append({"role":"user","text":user_text})
        # safety scan
        risk, hits = risk_scan(user_text)
        st.session_state.entry["risk_flag"] = bool(risk)
        st.session_state.entry["risk_terms"] = ", ".join(hits) if hits else ""
        if risk:
            say("bot", "That sounds really serious. I’m glad you told me.\nYou matter a lot, and you deserve to feel safe.\nLet’s get you to a person who can help right now.")
            say("bot", st.session_state.get("hotline_text", "If you need help now, tell a trusted adult or call/text 988 (US)."))
            st.session_state.step = "done"
        else:
            st.session_state.entry["context"] = user_text.strip()
            st.session_state.entry["what_happened"] = user_text.strip()
            say("bot", "Thanks for trusting me with that. What are you feeling right now? You can pick more than one:\n\n😡 Angry • 😢 Sad • 😐 Okay • 🙂 Better • 😄 Good")
            st.session_state.step = "ask_feelings"

elif st.session_state.step == "ask_feelings":
    cols = st.columns(5)
    picks = []
    if cols[0].button("😡 Angry"): picks.append("😡 Angry")
    if cols[1].button("😢 Sad"): picks.append("😢 Sad")
    if cols[2].button("😐 Okay"): picks.append("😐 Okay")
    if cols[3].button("🙂 Better"): picks.append("🙂 Better")
    if cols[4].button("😄 Good"): picks.append("😄 Good")

    user_text = st.chat_input("Type feelings (e.g., Angry, Sad)")
    if user_text:
        st.session_state.messages.append({"role":"user","text":user_text})
        lower = user_text.lower()
        for opt in FEEL_OPTIONS:
            if opt.split(" ",1)[1].lower() in lower or opt[0] in user_text:
                if opt not in picks: picks.append(opt)

    if picks:
        st.session_state.entry["mood"] = ", ".join(picks)
        st.session_state.entry["feelings"] = ", ".join(picks)
        say("bot", "Yeah, that makes sense. Those feelings are real.")
        say("bot", "What matters most to you here? Pick one:\n\n🤝 Kindness • ⚖️ Fairness • 💪 Courage • 🗣 Honesty • ❤️ Caring • 🧠 Learning")
        st.session_state.step = "ask_values"

elif st.session_state.step == "ask_values":
    cols = st.columns(6)
    val_choice = None
    if cols[0].button("🤝 Kindness"): val_choice = "🤝 Kindness"
    if cols[1].button("⚖️ Fairness"): val_choice = "⚖️ Fairness"
    if cols[2].button("💪 Courage"): val_choice = "💪 Courage"
    if cols[3].button("🗣 Honesty"): val_choice = "🗣 Honesty"
    if cols[4].button("❤️ Caring"): val_choice = "❤️ Caring"
    if cols[5].button("🧠 Learning"): val_choice = "🧠 Learning"

    user_text = st.chat_input("Type a value (e.g., kindness, fairness)")
    if user_text and not val_choice:
        st.session_state.messages.append({"role":"user","text":user_text})
        low = user_text.lower()
        for v in VALUE_OPTIONS:
            if v.split(" ",1)[1].lower() in low:
                val_choice = v
                break

    if val_choice:
        st.session_state.entry["values"] = val_choice
        say("bot", f"Got it. {val_choice.split(' ',1)[1]} matters to you — I can see why.")
        say("bot", "Think about the kind of person you want to be. What’s one small thing you could do right now that fits that?")
        st.session_state.step = "ask_plan"

elif st.session_state.step == "ask_plan":
    user_text = st.chat_input("Your one small action")
    if user_text:
        st.session_state.messages.append({"role":"user","text":user_text})
        st.session_state.entry["plan_action"] = user_text.strip()
        say("bot", "Nice. Is there someone who could help you with this? (friend, teacher, family) You can say skip if you want.")
        st.session_state.step = "ask_support"

elif st.session_state.step == "ask_support":
    user_text = st.chat_input("Who can help? (or type skip)")
    if user_text:
        st.session_state.messages.append({"role":"user","text":user_text})
        support = "" if user_text.strip().lower()=="skip" else user_text.strip()
        st.session_state.entry["plan_support"] = support

        # Build commitment line
        context = st.session_state.entry["context"]
        values = st.session_state.entry["values"]
        value_word = values.replace("🤝 ","").replace("⚖️ ","").replace("💪 ","").replace("🗣 ","").replace("❤️ ","").replace("🧠 ","")
        context_part = f"when {context}" if context else "in tough moments"
        plan = f"When I feel this way {context_part}, I will {st.session_state.entry['plan_action']} — because {value_word.lower()} matters to me."
        st.session_state.entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save
        if st.session_state.get("allow_storage", True):
            save_row({
                **st.session_state.entry,
                "risk_flag": st.session_state.entry.get("risk_flag", False),
                "risk_terms": st.session_state.entry.get("risk_terms","")
            })

        say("bot", "That’s a solid plan. I like how it sounds just like you.")
        # Show card
        st.markdown("---")
        st.subheader("My Next Step")
        st.markdown(f"**I'm feeling:** {st.session_state.entry['feelings'] or '—'}")
        st.markdown(f"**What matters to me:** {values or '—'}")
        st.markdown(f"**My plan:** {plan}")
        st.caption("Proud of you for making a choice that matches your best self.")
        st.download_button("Download my plan (.txt)",
                           data=(f"{APP_NAME} — My Next Step\nTime: {st.session_state.entry['timestamp']}\n\n"
                                 f"I'm feeling: {st.session_state.entry['feelings']}\n"
                                 f"What matters to me: {values}\n"
                                 f"My plan: {plan}\n").encode("utf-8"),
                           file_name="my-next-step.txt", mime="text/plain")
        st.session_state.step = "done"

# Connect sidebar toggles to session for save/safety text
st.session_state["allow_storage"] = allow_storage
st.session_state["hotline_text"] = hotline

# reset button (for next student)
if st.session_state.step == "done":
    if st.button("Start again (new student)"):
        reset_chat()
