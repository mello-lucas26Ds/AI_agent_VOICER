🎙️ Interview Assistant — Real-Time AI Voice Coach

Multilingual voice assistant that transcribes, translates and suggests responses during live job interviews — powered by OpenAI Whisper and Anthropic Claude Opus <3 seconds.

![Mostrar Imagem](docs/Image1.png)
![Mostrar Imagem](docs/Image2.png)
![Mostrar Imagem](<docs/Docs and Image.png>)


During an English job interview, the assistant:

1. **Captures audio** from the user's microphone via the browser
2. **Transcribes** the interviewer's question using **OpenAI Whisper-1** (cloud STT)
3. **Processes** the transcript via **Anthropic Claude Opus** for NLU and contextual understanding
4. **Generates** a natural, concise suggested response (EN + PT) with translation
5. **Stores** the full session in **PostgreSQL** for post-interview review

All triggered by a single keystroke (**F1**) and optimized for live use under pressure under <3s.


🏗️ System Architecture
```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND (Browser)                                     │
│  Microphone → Audio Capture (.webm/.wav) → REST API    │
└───────────────────────────┬─────────────────────────────┘
                            │ POST /api/messages/process-audio
                            ▼
┌─────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI + Python 3.11)                        │
│                                                          │
│  Audio → OpenAI Whisper-1 (STT) → English Transcript   │
│         ↓                                                │
│  Anthropic Claude Opus (NLU + Generation)               │
│  → JSON: original + translation + suggested responses   │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐    ┌───────────────────────┐
│  PostgreSQL DB   │    │  Response to Client   │
│  sessions +      │    │  EN + PT              │
│  messages        │    └───────────────────────┘
└──────────────────┘
```

**Pipeline:** Audio → STT (Whisper) → NLU (Claude Opus) → Translation + Response Generation → Persist → UI

✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎤 **Production-grade STT** | OpenAI Whisper-1 API for accurate English speech recognition |
| 🌐 **Multilingual NLP** | English input → Portuguese translation + bilingual suggested responses |
| 🤖 **LLM-powered NLU** | Intent-aware response generation via **Anthropic Claude Opus** |
| ⚡ **Low latency** | Optimized for fast end-to-end response time |
| 💾 **Session persistence** | Full interview history stored in PostgreSQL |
| 📊 **Built-in evaluation** | `eval.py` script measures latency (P50/P95) and response quality |
| ⌨️ **Keyboard-first UX** | F1 toggle to record/stop, designed for live use under pressure |
| 🔧 **Dual input support** | `/process-audio` for voice + `/process` for direct text input |

---


🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11 + FastAPI |
| **AI / NLU** | Anthropic Claude Opus |
| **STT (Speech-to-Text)** | OpenAI Whisper-1 API |
| **Database** | PostgreSQL + SQLAlchemy ORM |
| **Frontend** | Vanilla HTML/CSS/JS |
| **Evaluation** | Custom Python benchmarking script |

---

📁 Project Structure
interview-assistant/
│
├── backend/
│   ├── main.py           # FastAPI server + auto table creation
│   ├── database.py       # PostgreSQL connection via SQLAlchemy
│   ├── models.py         # ORM models: sessions + messages
│   └── routes/
│       ├── sessions.py   # Full CRUD for interview sessions
│       └── messages.py   # Whisper STT → Claude Opus → persisted response
│
├── frontend/
│   └── index.html        # Complete UI — recording, history, suggestions
│
├── eval.py               # Benchmarking: latency, word count, quality score
├── .env.example          # Environment variable template
└── README.md

🚀 Getting Started
Prerequisites

- Python 3.11+
- PostgreSQL running locally
- **OpenAI API Key** (for Whisper STT)
- **Anthropic API Key** (for Claude Opus NLU)


# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
POSTGRES_PASSWORD=your_postgres_password
```

# 5. Create the database
psql -U postgres -c "CREATE DATABASE interview_assistant;"

# 6. Start the server
```bash
uvicorn backend.main:app --reload
```

Open `http://localhost:8000` in your browser.

---

📊 Evaluation
Run the built-in benchmark script to measure latency and response quality across 10 real interview questions:

```bash
python eval.py
```

**Outputs:**
- ⏱️ Average / P95 response time
- 📝 Word count per response (target ≤ 45 words)
- ⭐ Manual quality score (1–5) per question
- 💾 Full results exported to `eval_results.json`

---


🗄️ Data Model
- **sessions** — one per interview
- **messages** — one per question, storing:
  - `original_en` — corrected/cleaned English transcript
  - `translation_pt` — natural Brazilian Portuguese translation
  - `suggested_response_en` — professional English response suggestion
  - `suggested_response_pt` — Portuguese translation of suggested response
  - `processing_time_ms` — end-to-end latency metric

🔮 Roadmap

| Feature | Status |
|---------|--------|
| ✅ OpenAI Whisper STT | Implemented |
| ✅ Anthropic Claude Opus NLU | Implemented |
| ✅ PostgreSQL persistence | Implemented |
| ✅ RESTful API (audio + text) | Implemented |
| 🔄 Streaming responses | Token-by-token output to reduce perceived latency to < 1s |
| 🔄 RAG integration | Inject company knowledge base into context (mission, products, values) |
| 🔄 Speaker diarization | Separate interviewer vs. candidate voice (AssemblyAI / Deepgram) |
| 🔄 Session analytics dashboard | Response time trends, score evolution across sessions |
| 🔄 Cloud deployment | Railway (backend) + Supabase (PostgreSQL) |


💡 Why this project
Built as a practical tool to prepare for English-language job interviews, combining:

- **Real-world STT + NLU pipeline design** — production APIs (OpenAI + Anthropic)
- **Production constraints** — latency, reliability, UX under pressure
- **Multilingual NLP** — EN ↔ PT translation and response generation
- **End-to-end AI system** — from raw audio to persisted, structured insights

---

## 🎯 Design Decisions

| Decision | Why |
|----------|-----|
| **F1 toggle** (not hold-to-talk) | Reduces cognitive load under interview pressure |
| **No auto-stop on silence** | Risk of cutting long answers mid-sentence |
| **Backend STT via Whisper API** | Superior accuracy over browser-native ASR for professional use |
| **Claude Opus over Haiku** | Higher reasoning quality for nuanced interview context |
| **Manual session control** | User decides when a question ends, not the algorithm |
| **Dual endpoint design** | `/process-audio` for voice + `/process` for text fallback |



## 👤 Author

**Lucas Melo** — Data Scientist / AI Engineer  
[LinkedIn](https://www.linkedin.com/in/mello-lucas26/?locale=en-US)

---

## 📄 License

MIT © 2025 Lucas Melo
