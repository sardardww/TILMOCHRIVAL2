import json
from fastapi.testclient import TestClient
from app.main import app
from app.dictionary_service import dictionary_service

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["dictionary_loaded"] is True
    assert data["dictionary_entries"] > 10000

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Russian ➔ Karakalpak AI Translator" in response.text

def test_dictionary_lookup():
    response = client.post("/dictionary/lookup", json={"query": "студент", "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] > 0
    first_match = data["results"][0]
    assert first_match["dictionary_lemma"] == "студент"
    assert "student" in first_match["qq_lat"].lower()

def test_dictionary_stem_extraction():
    sentence = "Сегодня студенты университета изучают современные технологии."
    matches = dictionary_service.extract_matches_for_text(sentence)
    lemmas = [m.dictionary_lemma for m in matches]
    assert "сегодня" in lemmas
    assert "студент" in lemmas
    assert "университет" in lemmas
    assert "изучать" in lemmas

def test_translate_offline_mode():
    # When GEMINI_API_KEY is not set or custom_api_key is empty, it returns the helpful offline guidance
    response = client.post("/translate", json={
        "text": "Сегодня студенты читают книги в библиотеке.",
        "target_script": "latin"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["source_text"] == "Сегодня студенты читают книги в библиотеке."
    assert data["matched_terms_count"] > 0
    assert len(data["matched_terms"]) > 0
