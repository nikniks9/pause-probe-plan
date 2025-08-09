\
import streamlit as st
import pandas as pd
from datetime import datetime
import re, os

# ---------- Setup & secrets ----------
st.set_page_config(page_title="Pause • Probe • Plan — Chat", page_icon="🤝", layout="centered")

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
MODEL = st.secrets.get("OPENAI_MODEL", "gpt-4o")

try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    OPENAI_READY = client is not None
except Exception as e:
    client = None
    OPENAI_READY = False

# ---------- Styles ----------
BG = "#F7F7F7"
st.markdown(f"<style>body {{ background:{BG}; }}</style>", unsafe_allow_html=True)

st.title("🤝 Pause • Probe • Plan")
st.caption("Warm, validating chat for kids. Age-aware. Anonymous summaries for teachers.")

# ---------- Sidebar (teacher) ----------
with st.sidebar:
    st.markdown("### Teacher settings")
    save_logs = st.toggle("Save anonymized summaries (CSV)", value=True)
    hotline = st.text_input("Safety help text", "If you need help now, tell a trusted adult or call/text 988 (US).")
    st.caption("Add your OpenAI key in: Manage app → Settings → Secrets")
    if not OPENAI_READY:
        st.error("Missing or invalid OPENAI_API_KEY in Secrets.")
        st.code(r"OPENAI_API_KEY = sk-...yourkey...\nOPENAI_MODEL = gpt-4o")
    # Export
    LOG_PATH = "chat_logs.csv"
    if os.path.exists(LOG_PATH):
        df = pd.read_csv(LOG_PATH)
        st.download_button("Download summaries (CSV)", data=df.to_csv(index=False).encode("utf-8"),
                           file_name="pause_probe_plan_chat_logs.csv", mime="text/csv")
    else:
        st.caption("No logs yet.")

# ---------- Risk scan ----------
RISK_TERMS = [
    "kill myself","want to die","suicide","hurt myself","cut myself","self-harm","self harm",
    "unsafe at home","they will hurt me","someone will hurt me","going to kill","kill them",
    "i can't go on","cant go on","no point","worthless","hopeless"
]
def risk_scan(text: str):
    low = (text or "").lower()
    hits = sorted({kw for kw in RISK_TERMS if kw in low})
    return (len(hits) > 0), hits

# ---------- Age bands ----------
AGE_TONES = {
    "K–2": "Use very short sentences. Simple words. Lots of reassurance. Friendly like a storytime buddy.",
    "3–5": "Friendly, concrete, warm, and encouraging. A few short sentences at a time.",
    "6–8": "Respectful, warm, peer-like. Encourage reasoning and self-reflection, but keep it simple."
}

SYSTEM_BASE = """You are a warm, validating friend for K–8 students using a Pause → Probe → Plan flow.
Tone rules: warm, friendly, affirming, non-judgmental, short sentences. Validate before asking the next question.
Never give orders. Invite gently. Avoid the word "should". Keep cognitive load low.
If the student indicates self-harm, hurting others, abuse, or serious danger, STOP and say:
"It sounds really serious. I’m glad you told me. You matter and you deserve to feel safe. Let’s get you to a person who can help right now."
Then show the hotline text provided by the app and invite them to tell a trusted adult. End the conversation after the safety message.
Output plain text only.
"""

def system_prompt_for(age_band: str, hotline_text: str) -> str:
    return SYSTEM_BASE + f"\nAge band: {age_band}\nStyle: {AGE_TONES[age_band]}\nHotline text: {hotline_text}\n"

# ---------- State ----------
if "age_band" not in st.session_state:
    st.session_state.age_band = None
if "messages" not in st.session_state:
    st.session_state.messages = []   # [{role, content}]
if "summary" not in st.session_state:
    st.session_state.summary = None
if "ended" not in st.session_state:
    st.session_state.ended = False

# ---------- Age picker ----------
if st.session_state.age_band is None:
    st.write("Before we start, how old are you? This helps me talk in the best way for you.")
    c1, c2, c3 = st.columns(3)
    if c1.button("K–2"): st.session_state.age_band = "K–2"
    if c2.button("3–5"): st.session_state.age_band = "3–5"
    if c3.button("6–8"): st.session_state.age_band = "6–8"
    st.stop()

# ---------- Start conversation ----------
if len(st.session_state.messages) == 0:
    opener = {"K–2":"I’m here with you. What happened?",
              "3–5":"Thanks for telling me. What went down?",
              "6–8":"I’m listening. What happened?"}[st.session_state.age_band]
    st.session_state.messages = [{"role":"assistant","content":opener}]

# Render chat so far
for m in st.session_state.messages:
    with st.chat_message("assistant" if m["role"]=="assistant" else "user"):
        st.markdown(m["content"])

# Input
user_text = st.chat_input("Type here…", disabled=st.session_state.ended or not OPENAI_READY)
if user_text and not st.session_state.ended:
    # Safety first
    risky, hits = risk_scan(user_text)
    st.session_state.messages.append({"role":"user","content":user_text})

    if risky:
        st.session_state.messages.append({"role":"assistant","content":"That sounds really serious. I’m glad you told me. You matter and you deserve to feel safe. Let’s get you to a person who can help right now."})
        st.session_state.messages.append({"role":"assistant","content":hotline})
        st.session_state.ended = True
    else:
        if not OPENAI_READY:
            st.session_state.messages.append({"role":"assistant","content":"(App needs an OpenAI API key in Secrets to reply.)"})
        else:
            sys_prompt = system_prompt_for(st.session_state.age_band, hotline)
            try:
                resp = client.chat.completions.create(
                    model=MODEL,
                    temperature=0.7,
                    messages=[{"role":"system","content":sys_prompt}] + st.session_state.messages
                )
                reply = resp.choices[0].message.content
            except Exception as e:
                reply = f"[Model error: {e}]"

            st.session_state.messages.append({"role":"assistant","content":reply})

            # try to extract a plan line for summary
            import re as _re
            m = _re.search(r'(?im)^\s*(I will[^\n\.]*[\n\.]?)', reply)
            if m:
                st.session_state.summary = m.group(1).strip()

    st.experimental_rerun()

# ---------- Plan card / save ----------
if st.session_state.summary and not st.session_state.ended:
    if st.button("Make my plan card"):
        st.markdown("---")
        st.subheader("My Next Step")
        st.markdown(st.session_state.summary)
        st.caption("Proud of you for making a choice that matches your best self.")

        if save_logs:
            row = {
                "timestamp": datetime.utcnow().isoformat(),
                "age_band": st.session_state.age_band,
                "turns": len(st.session_state.messages),
                "summary": st.session_state.summary
            }
            try:
                if os.path.exists("chat_logs.csv"):
                    df = pd.read_csv("chat_logs.csv")
                else:
                    df = pd.DataFrame(columns=row.keys())
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                df.to_csv("chat_logs.csv", index=False)
                st.toast("Saved.", icon="✅")
            except Exception as e:
                st.toast(f"Could not save: {e}", icon="⚠️")

        st.session_state.ended = True

# Reset button
if st.session_state.ended:
    if st.button("Start again"):
        for k in ["messages","summary","ended","age_band"]:
            st.session_state.pop(k, None)
        st.experimental_rerun()
