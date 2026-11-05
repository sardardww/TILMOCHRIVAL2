from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class TargetScript(str, Enum):
    latin = "latin"
    cyrillic = "cyrillic"
    both = "both"

class DictionaryMatch(BaseModel):
    source_word: str = Field(..., description="The word as it appeared in the input text")
    dictionary_lemma: str = Field(..., description="The matched dictionary headword")
    qq_lat: Optional[str] = Field(None, description="Karakalpak Latin translation from dictionary")
    qq_cyr: Optional[str] = Field(None, description="Karakalpak Cyrillic translation from dictionary")

class TranslationRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Russian text or sentence to translate into Karakalpak",
        example="Сегодня студенты университета изучают современные технологии."
    )
    target_script: TargetScript = Field(
        default=TargetScript.latin,
        description="Target writing script: 'latin' (standard 34-letter Latin), 'cyrillic', or 'both'"
    )
    model: Optional[str] = Field(
        default=None,
        description="Optional Gemini model override (e.g., 'gemini-2.5-flash', 'gemini-2.0-flash')"
    )
    include_dictionary_matches: bool = Field(
        default=True,
        description="Whether to include dictionary lookup details in response"
    )

class TextCorrection(BaseModel):
    original: str = Field(..., description="Original misspelled Russian word")
    corrected: str = Field(..., description="Corrected Russian word")

class TranslationResponse(BaseModel):
    source_text: str = Field(..., description="Original Russian text entered by user")
    corrected_source_text: Optional[str] = Field(None, description="Step 1: Auto-corrected, normalized Russian text")
    corrections_made: List[TextCorrection] = Field(default_factory=list, description="List of spelling/grammar corrections made in Russian")
    translated_text: str = Field(..., description="Karakalpak translation in requested script")
    translated_latin: Optional[str] = Field(None, description="Karakalpak translation in official Latin script")
    translated_cyrillic: Optional[str] = Field(None, description="Karakalpak translation in Cyrillic script")
    target_script: str = Field(..., description="Requested target script")
    model_used: str = Field(..., description="AI Studio / Gemini model that performed translation")
    matched_terms_count: int = Field(..., description="Number of dictionary terms matched")
    matched_terms: List[DictionaryMatch] = Field(default_factory=list, description="Grounding dictionary matches")
    used_vocabulary_note: Optional[str] = Field(None, description="Detailed list of dictionary vocabulary applied in translation")

class BatchTranslationRequest(BaseModel):
    texts: List[str] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of Russian sentences to translate"
    )
    target_script: TargetScript = Field(
        default=TargetScript.latin,
        description="Target writing script: 'latin', 'cyrillic', or 'both'"
    )

class BatchTranslationResponse(BaseModel):
    total: int
    results: List[TranslationResponse]

class DictionaryLookupRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100, description="Russian word or phrase to look up")
    limit: int = Field(default=10, ge=1, le=50, description="Max number of matches to return")

class DictionaryLookupResponse(BaseModel):
    query: str
    total_matches: int
    results: List[DictionaryMatch]

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    dictionary_loaded: bool
    dictionary_entries: int
    gemini_configured: bool
    default_model: str
