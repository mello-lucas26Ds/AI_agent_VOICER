🎙️ Interview Assistant — Real-Time AI Voice Coach

Multilingual voice assistant that transcribes, translates and suggests responses during live job interviews — in under <2 seconds.

![Mostrar Imagem](docs/Image1.png)
![Mostrar Imagem](docs/Image2.png)
![Mostrar Imagem](<docs/Docs and Image.png>)


🧠 What it does
During an English job interview, the assistant:

Listens to the interviewer via real-time ASR (Web Speech API / Whisper-compatible)
Transcribes the question in English
Translates it to Portuguese instantly
Generates a natural, concise suggested response (EN + PT) via Claude AI
Stores the full session in PostgreSQL for post-interview review

All of this in under 5 seconds, triggered by a single keystroke (F1).

🏗️ System Architecture
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (Browser)                  │
│                                                         │
│   Microphone → Web Speech API (ASR) → REST API call     │
└───────────────────────────┬─────────────────────────────┘
                            │ POST /api/messages/process
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                     │
│                                                         │
│   Input text → Claude Haiku (NLU + Generation)          │
│              → JSON: translation + suggested response    │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐      ┌───────────────────────┐
│   PostgreSQL DB  │      │   Response to Client   │
│  sessions +      │      │   EN + PT in < 5s      │
│  messages        │      └───────────────────────┘
└──────────────────┘
Pipeline: Audio → ASR → Text → NLU (Claude) → Translation + Response Generation → Persist → UI

✨ Key Features

🎤 Real-time ASR — browser-native speech recognition, no extra cost
🌐 Multilingual NLP — English input, Portuguese output (EN↔PT)
🤖 LLM-powered NLU — intent-aware response generation via Claude Haiku
⚡ Low latency — optimized for < 2s end-to-end response time
💾 Session persistence — full interview history stored in PostgreSQL
📊 Built-in evaluation script — measures latency (P50/P95) and response quality
⌨️ Keyboard-first UX — F1 to record / stop, designed for live use under pressure


🛠️ Tech Stack
LayerTechnology BackendPython 3.11 + FastAPIAI / NLUAnthropic Claude Haiku 4.5/Whisper OPENAI/ ASRWeb Speech API (browser-native)DatabasePostgreSQL 18 + SQLAlchemy ORM Frontend Vanilla HTML/CSS/JSEvaluationCustom Python benchmarking script

📁 Project Structure
interview-assistant/
│
├── backend/
│   ├── main.py           # FastAPI server + auto table creation
│   ├── database.py       # PostgreSQL connection via SQLAlchemy
│   ├── models.py         # ORM models: sessions + messages
│   └── routes/
│       ├── sessions.py   # Full CRUD for interview sessions
│       └── messages.py   # ASR text → Claude → persisted response
│
├── frontend/
│   └── index.html        # Complete UI — recording, history, suggestions
│
├── eval.py               # Benchmarking: latency, word count, quality score
├── .env.example          # Environment variable template
└── README.md

🚀 Getting Started
Prerequisites

Python 3.11+
PostgreSQL running locally
Google Chrome (for Web Speech API)
Anthropic API Key
OpenAI API Key


# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY and POSTGRES_PASSWORD

# 5. Create the database
psql -U postgres -c "CREATE DATABASE interview_assistant;"

# 6. Start the server
uvicorn backend.main:app --reload
Open http://localhost:8000 in Google Chrome.

📊 Evaluation
Run the built-in benchmark script to measure latency and response quality across 10 real interview questions:
bashpython eval.py
Outputs:

⏱️ Average / P95 response time
📝 Word count per response (target ≤ 45 words)
⭐ Manual quality score (1–5) per question
💾 Full results exported to eval_results.json


🗄️ Data Model
sessions — one per interview
messages — one per question, storing: original_en, translation_pt, suggested_response_en, suggested_response_pt, processing_time_ms

🔮 Roadmap

 Replace Web Speech API with Whisper for production-grade ASR
 RAG — inject company knowledge base into context (mission, products, values)
 Streaming responses — token-by-token output to reduce perceived latency to < 1s
 Speaker diarization — separate interviewer vs. candidate voice (AssemblyAI / Deepgram)
 Session analytics dashboard — response time trends, score evolution across sessions
 Cloud deployment — Railway (backend) + Supabase (PostgreSQL)


💡 Why this project
Built as a practical tool to prepare for English-language job interviews, combining:

Real-world ASR + NLU pipeline design
Production constraints (latency, reliability, UX under pressure)
Multilingual NLP (EN ↔ PT)
End-to-end AI system: from raw audio to persisted, structured insights

## 🎯 Design Decisions

| Decision | Why |
|---|---|
| F1 toggle (not hold-to-talk) | Reduces cognitive load under interview pressure |
| No auto-stop on silence | Risk of cutting long answers mid-sentence |
| Browser ASR over Whisper API | Zero latency, zero cost for MVP — Whisper planned for v2 |
| No speaker diarization | Whisper doesn't separate speakers natively — AssemblyAI on roadmap |
| Manual session control | User decides when a question ends, not the algorithm |




👤 Author
Lucas Melo — Data Scientist / AI Engineer
Linkedin
https://www.linkedin.com/in/mello-lucas26/?locale=en-US

📄 License
MIT © 2025 Lucas Melo
