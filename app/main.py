import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import settings
from app.dictionary_service import dictionary_service
from app.schemas import (
    BatchTranslationRequest,
    BatchTranslationResponse,
    DictionaryLookupRequest,
    DictionaryLookupResponse,
    HealthResponse,
    TranslationRequest,
    TranslationResponse,
)
from app.translator import translator_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
# Russian to Karakalpak AI Translation API
Grounded with 16,000+ entries from the Russian-Karakalpak Dictionary and powered by Google AI Studio (Gemini).

### Key Features:
* **Neural + Dictionary Grounding:** Injects verified Karakalpak terminology from `qq_dictionary.json` into Gemini context to eliminate hallucinations.
* **Dual Script Support:** Full support for official Karakalpak Latin (34-letter alphabet) and Cyrillic.
* **Batch Processing:** Translate multiple sentences in a single request.
* **Dictionary Lookup Endpoint:** Direct search across the 16,000+ entries without calling Gemini.
* **Ready for Render & GitHub:** Auto-deploys via Render Blueprint (`render.yaml`).
""",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for external web apps / frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home():
    """Serves the interactive web interface."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Russian to Karakalpak Translation API</h1><p>Visit <a href='/docs'>/docs</a></p>")


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint for Render and monitoring services."""
    gemini_key_present = bool(settings.GEMINI_API_KEY)
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        dictionary_loaded=dictionary_service.is_loaded,
        dictionary_entries=dictionary_service.entry_count,
        gemini_configured=gemini_key_present,
        default_model=settings.GEMINI_MODEL,
    )


@app.get("/api/models", tags=["System"])
async def list_available_models():
    """List all available models returned directly by Google AI Studio."""
    from google import genai
    key = settings.GEMINI_API_KEY.strip()
    if not key:
        return {"error": "GEMINI_API_KEY not configured"}
    try:
        client = genai.Client(api_key=key)
        models = [m.name for m in client.models.list()]
        return {"available_models": models}
    except Exception as e:
        return {"error": str(e)}


@app.post("/debug/try_model", tags=["System"])
async def debug_try_model(payload: TranslationRequest):
    """Directly test a single model without any fallback cascade to see exact behavior."""
    from google import genai
    from google.genai import types
    key = settings.GEMINI_API_KEY.strip()
    if not key:
        return {"error": "No API key"}
    try:
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model=payload.model or "gemini-2.5-flash",
            contents=f"Translate into Karakalpak JSON: {payload.text}",
        )
        return {"status": "ok", "model": payload.model, "output": resp.text}
    except Exception as e:
        return {"status": "error", "model": payload.model, "error_type": type(e).__name__, "detail": str(e)}


@app.post(
    "/translate",
    response_model=TranslationResponse,
    tags=["Translation"],
    summary="Translate Russian text to Karakalpak"
)
async def translate_text(
    payload: TranslationRequest,
    x_gemini_api_key: Optional[str] = Header(None, description="Optional Google AI Studio API key header override")
):
    """
    Translates a Russian sentence or paragraph into Karakalpak (Latin or Cyrillic).
    Automatically matches vocabulary against `qq_dictionary.json` and injects grounding context into Gemini.
    """
    try:
        result = await translator_service.translate(
            text=payload.text,
            target_script=payload.target_script,
            model_override=payload.model,
            custom_api_key=x_gemini_api_key,
            include_dictionary_matches=payload.include_dictionary_matches,
        )
        return result
    except Exception as e:
        logger.error(f"Translation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post(
    "/translate/batch",
    response_model=BatchTranslationResponse,
    tags=["Translation"],
    summary="Batch translate multiple sentences"
)
async def translate_batch(
    payload: BatchTranslationRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Translates a batch of Russian sentences in sequence.
    """
    results = []
    for text in payload.texts:
        if not text.strip():
            continue
        res = await translator_service.translate(
            text=text,
            target_script=payload.target_script,
            custom_api_key=x_gemini_api_key,
            include_dictionary_matches=True,
        )
        results.append(res)
    
    return BatchTranslationResponse(
        total=len(results),
        results=results
    )


@app.post(
    "/dictionary/lookup",
    response_model=DictionaryLookupResponse,
    tags=["Dictionary"],
    summary="Search Karakalpak dictionary directly"
)
async def dictionary_lookup(payload: DictionaryLookupRequest):
    """
    Searches the 16,000+ Karakalpak dictionary entries by Russian word or stem.
    Fast offline search that does not consume Gemini API tokens.
    """
    matches = dictionary_service.search(query=payload.query, limit=payload.limit)
    return DictionaryLookupResponse(
        query=payload.query,
        total_matches=len(matches),
        results=matches,
    )
