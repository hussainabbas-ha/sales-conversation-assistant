# Sales Conversation Assistant

API for sales-call analysis and follow-up chat. It labels transcripts, scores conversation attributes, generates TTS, and continues the dialogue with a scripted assistant.

## Getting started

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

If the stack uses Flask locally, `python app.py` may also apply depending on how you launch it.

## Endpoints

- `POST /process-voice/` — analyze a transcript text file
- `POST /chat-with-bot/` — continue a sales conversation

Set `OPENAI_API_KEY` and `DEEPGRAM_API_KEY` in `.env`.
