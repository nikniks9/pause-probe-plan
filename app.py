import streamlit as st
import openai
import csv
import os
from datetime import datetime

# Load API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]
MODEL = st.secrets.get("OPENAI_MODEL", "gpt-4o")

st.set_page_config(page_title="Pause • Probe • Plan", page_icon="🤝", layout="centered")

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = "intro"
if "chat" not in st.session_state:
    st.session_state.chat = []
if "age_band" not in st.session_state:
    st.session_state.age_band = None
if "log" not in st.session_state:
    st.session_state.log = []

# Age band language settings
AGE_TONES = {
    "K-2": "Use very short sentences. Simple words. Lots of reassurance. Friendly like a storytime buddy.",
    "3-5": "Friendly, concrete, warm, and encouraging. A few sentences at a time.",
    "6-8": "Respectful, warm, but speaks more like a coach. Encourages reasoning and self-reflection."
}

# Function to call OpenAI
def ask_gpt(prompt):
    messages = [
        {"role": "system", "content": f"You are a warm, validating friend helping a child resolve a conflict using Pause → Probe → Plan. {AGE_TONES[st.session_state.age_band]} Always validate their feelings before moving to the next step. If they mention wanting to hurt themselves or others, or something dangerous, stop and give them this message: 'This sounds important to share with a trusted adult right now. You matter and you are not alone. Please find your teacher, counselor, or another safe adult.'"},
        {"role": "user", "content": prompt}
    ]
    response = openai.ChatCompletion.create(model=MODEL, messages=messages)
    return response.choices[0].message["content"]

# Logging function
def save_log(age_band, conversation):
    filename = "/mnt/data/chat_log.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["timestamp", "age_band", "conversation"])
        writer.writerow([datetime.now().isoformat(), age_band, " | ".join(conversation)])

# UI Flow
st.title("🤝 Pause • Probe • Plan")

if st.session_state.step == "intro":
    st.write("Hi, I'm here to help you work through something that's bothering you.")
    st.session_state.age_band = st.selectbox("How old are you?", ["K-2", "3-5", "6-8"])
    if st.button("Start"):
        st.session_state.step = "chat"
        st.experimental_rerun()

elif st.session_state.step == "chat":
    for speaker, msg in st.session_state.chat:
        if speaker == "user":
            st.markdown(f"**You:** {msg}")
        else:
            st.markdown(f"**Friend:** {msg}")

    user_input = st.text_input("Your turn:", key=f"input_{len(st.session_state.chat)}")
    if st.button("Send"):
        if user_input.strip():
            st.session_state.chat.append(("user", user_input))
            gpt_reply = ask_gpt(user_input)
            st.session_state.chat.append(("bot", gpt_reply))
            st.session_state.log.append(f"You: {user_input}")
            st.session_state.log.append(f"Friend: {gpt_reply}")
            st.experimental_rerun()

    if st.button("Finish Plan"):
        save_log(st.session_state.age_band, st.session_state.log)
        st.success("Your plan is saved. Thanks for sharing with me today!")
        st.session_state.step = "intro"
        st.session_state.chat = []
        st.session_state.log = []
