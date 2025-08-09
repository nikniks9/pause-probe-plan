
# Pause • Probe • Plan (Kid Conflict Coach)

A kid-friendly, polyvagal-informed reflection tool with a warm "friend" tone.
Includes a silent safety trigger and a teacher dashboard. Built in Streamlit.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features
- **Pause (polyvagal)**: state check + matching regulation cue
- **Probe**: what happened, feelings, values
- **Plan**: friendly “I will” commitment line
- **Safety mode**: high-risk language triggers a caring safety message + local alert via saved flag
- **Teacher view**: anonymized counts, mood/value charts, CSV export
- **Privacy**: saves to `sessions.csv` locally (toggleable). No cloud storage by default.

## Deploy on Streamlit Cloud
1. Push these files to a GitHub repo.
2. In Streamlit Cloud, create a new app pointing to `app.py`.
3. Set up your app secrets/environment if needed (none required for this MVP).
4. Share your public link 🎉
