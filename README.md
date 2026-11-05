# 🌐 Russian to Karakalpak AI Translation API

An enterprise-ready translation API connecting **GitHub ➔ Render ➔ Google AI Studio (Gemini)**, grounded with **16,059 verified Russian-to-Karakalpak dictionary entries** (`qq_dictionary.json`).

---

## 🌟 Architecture & Flow

```
[ Client / Web / App ]
          │  (POST /translate)
          ▼
┌──────────────────────────────────────────────┐
│  Render Hosted Web Service (FastAPI)         │
│                                              │
│  1. Extract Russian words & inflected stems  │
│  2. Grounding search in qq_dictionary.json   │
│  3. Build strict linguistic prompt           │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Google AI Studio (Gemini 2.5 Flash)        │
│                                              │
│  - Turkic SOV syntax & vowel harmony         │
│  - Injects verified Karakalpak vocabulary    │
│  - Outputs Latin & Cyrillic JSON             │
└──────────────────────────────────────────────┘
```

---

## 🚀 Features

- **Grounding with 16,000+ Dictionary Entries**: Eliminates AI hallucination and prevents confusion with Kazakh or Uzbek terms by injecting matched lemmas from `qq_dictionary.json`.
- **Morphological Stem Matching**: Automatically stems Russian inflected forms (nouns, verb conjugations, adjective agreements) to match base dictionary lemmas.
- **Dual Script Output**: Supports official 34-letter **Karakalpak Latin** (`qq_lat`) and **Cyrillic** (`qq_cyr`).
- **Interactive Web Interface**: Built-in test console at `/` with sample phrases and live dictionary tag inspection.
- **Auto-generated Documentation**: Interactive Swagger docs at `/docs` and ReDoc at `/redoc`.
- **Render Ready**: Includes `render.yaml` Blueprint for zero-friction continuous deployment from GitHub.

---

## 📋 Quick Start Guide

### Step 1: Get Google AI Studio API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** and generate a new key.
3. Save your key (e.g. `AIzaSy...`).

---

### Step 2: Push to GitHub

1. Create a new repository on [GitHub](https://github.com/new) (e.g. `karakalpak-translator-api`).
2. In your terminal, initialize and push:
```bash
git init
git add .
git commit -m "Initial commit: Russian-Karakalpak translation API with dictionary grounding"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/karakalpak-translator-api.git
git push -u origin main
```
*(If you do not have Git installed on your system, you can also use [GitHub Desktop](https://desktop.github.com/) or upload the folder directly to GitHub).*

---

### Step 3: Deploy on Render

#### Option A: 1-Click Blueprint (Recommended)
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** ➔ **Blueprint**.
3. Select your GitHub repository (`karakalpak-translator-api`).
4. Render will read `render.yaml` automatically.
5. In the environment variables prompt, enter your `GEMINI_API_KEY`.
6. Click **Apply**. Render will build and deploy your service!

#### Option B: Manual Web Service
1. In Render Dashboard, click **New +** ➔ **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Name**: `karakalpak-translator-api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add:
   - `GEMINI_API_KEY` = *your Google AI Studio API key*
   - `GEMINI_MODEL` = `gemini-2.5-flash`
5. Click **Create Web Service**.

---

## 📡 API Reference & Endpoints

### 1. `POST /translate`
Translates Russian text into Karakalpak using Gemini and dictionary grounding.

**Request Body:**
```json
{
  "text": "Сегодня студенты университета изучают современные технологии.",
  "target_script": "latin",
  "model": "gemini-2.5-flash",
  "include_dictionary_matches": true
}
```

**Parameters:**
- `text` (*string*, required): Russian sentence or paragraph.
- `target_script` (*string*, optional): `"latin"` (default), `"cyrillic"`, or `"both"`.
- `model` (*string*, optional): Model override (e.g., `"gemini-2.5-flash"`).
- `include_dictionary_matches` (*boolean*, optional): Returns dictionary match details.

**Response:**
```json
{
  "source_text": "Сегодня студенты университета изучают современные технологии.",
  "translated_text": "Búgin universitet studentleri házirgi zaman texnologiyaların úyrenbekte.",
  "translated_latin": "Búgin universitet studentleri házirgi zaman texnologiyaların úyrenbekte.",
  "translated_cyrillic": "Бүгин университет студентлери хәзирги заман технологияларын үйренбекте.",
  "target_script": "latin",
  "model_used": "gemini-2.5-flash",
  "matched_terms_count": 5,
  "matched_terms": [
    {
      "source_word": "Сегодня",
      "dictionary_lemma": "сегодня",
      "qq_lat": "búgin",
      "qq_cyr": "бүгин"
    },
    {
      "source_word": "студенты",
      "dictionary_lemma": "студент",
      "qq_lat": "student, talaba",
      "qq_cyr": "студент, талаба"
    },
    {
      "source_word": "изучают",
      "dictionary_lemma": "изучать",
      "qq_lat": "úyreniw, izertlew",
      "qq_cyr": "үйрениў, изертлеў"
    }
  ]
}
```

---

### 2. `POST /translate/batch`
Translates an array of Russian sentences in a single API call.

```json
{
  "texts": [
    "Здравствуйте, добро пожаловать в Нукус!",
    "Президент подписал новый указ о развитии образования."
  ],
  "target_script": "latin"
}
```

---

### 3. `POST /dictionary/lookup`
Fast, direct offline search through the 16,059 dictionary entries (does not consume Gemini API quota).

```json
{
  "query": "университет",
  "limit": 5
}
```

---

### 4. `GET /health`
Service health check and diagnostic information.

```json
{
  "status": "healthy",
  "service": "Russian to Karakalpak Translation API",
  "version": "1.0.0",
  "dictionary_loaded": true,
  "dictionary_entries": 16059,
  "gemini_configured": true,
  "default_model": "gemini-2.5-flash"
}
```

---

## 💻 Local Development

1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and set your key:
```env
GEMINI_API_KEY=your_actual_key_here
```

3. Start development server:
```bash
uvicorn app.main:app --reload --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser!

---

## 📁 Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI routes & CORS setup
│   ├── config.py             # Environment configuration
│   ├── schemas.py            # Pydantic models for requests/responses
│   ├── dictionary_service.py # Pre-indexed 16k dictionary & stem matching
│   ├── translator.py         # Google AI Studio Gemini integration
│   └── templates/
│       └── index.html        # Interactive test UI
├── data/
│   └── qq_dictionary.json    # 16,059-entry Russian-to-Karakalpak dictionary
├── tests/
│   ├── __init__.py
│   └── test_api.py           # Automated test suite
├── Dockerfile                # Multi-stage Docker container
├── render.yaml               # Render Blueprint deploy configuration
├── requirements.txt          # Production dependencies
├── .env.example              # Environment variables template
└── README.md                 # Documentation
```
