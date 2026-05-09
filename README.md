# 🤖 AI Summarization Platform

Summarize any **text**, **PDF document**, or **video** in seconds using AI.

![Tech Stack](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-1.5_Flash-4285F4?logo=google)
![Whisper](https://img.shields.io/badge/Whisper-Speech--to--Text-412991?logo=openai)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?logo=typescript)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)

---

## ✨ Features

- **📝 Text Summarization** — Paste any text and get an AI-powered summary
- **📄 PDF Summarization** — Upload PDF files with drag-and-drop support
- **🎬 Video Summarization** — Paste a YouTube URL or upload a video file
- **📏 Summary Length Control** — Choose between short, medium, or detailed summaries
- **🌍 Multi-Language Detection** — Whisper auto-detects the spoken language
- **📋 Copy & Export** — Copy summaries to clipboard or export as .txt
- **📊 Compression Stats** — See original vs. summary length and compression ratio
- **🎨 Premium Dark UI** — Glassmorphism design with smooth animations

---

## 🏗️ Architecture

```
User → Next.js Frontend → FastAPI Backend → Google Gemini 1.5 Flash
                                          → Whisper (for video)
                                          → pdfplumber (for PDF)
                                          → yt-dlp + FFmpeg (for video)
```

Three input pipelines, one output: **Text → Gemini → Summary**

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- FFmpeg (`brew install ffmpeg`)
- Google Gemini API Key ([get one here](https://aistudio.google.com/app/apikey))

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Gemini API key
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) 🎉

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/summarize/text` | Summarize raw text |
| POST | `/api/summarize/pdf` | Summarize a PDF file |
| POST | `/api/summarize/video/url` | Summarize video from URL |
| POST | `/api/summarize/video/upload` | Summarize uploaded video |
| GET | `/docs` | Interactive API documentation |
| GET | `/health` | Health check |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS | UI & UX |
| Backend | Python FastAPI + Uvicorn | API server |
| AI - Summarization | Google Gemini 1.5 Flash | Text summarization |
| AI - Transcription | OpenAI Whisper | Speech-to-text |
| PDF Processing | pdfplumber | PDF text extraction |
| Video Processing | yt-dlp + FFmpeg | Audio download & conversion |

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── routers/             # API route handlers
│   ├── services/            # Business logic (summarizer, extractor, transcriber)
│   ├── utils/               # Helpers (chunker, cleaner, logger)
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Docker config for deployment
│
└── frontend/
    ├── app/                 # Next.js pages
    ├── components/          # React components
    ├── lib/                 # API client & types
    ├── package.json         # Node dependencies
    └── tailwind.config.ts   # Tailwind configuration
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

Built with ❤️ using Google Gemini & OpenAI Whisper
