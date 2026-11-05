import json
import logging
import re
from typing import Optional, Tuple
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.dictionary_service import dictionary_service
from app.grammar_service import KARAKALPAK_ACADEMIC_GRAMMAR_PROMPT, fix_common_grammatical_slips
from app.schemas import TargetScript, TranslationResponse, DictionaryMatch

logger = logging.getLogger(__name__)

KARAKALPAK_SYSTEM_PROMPT = f"""You are a master linguist and native professional translator specializing in the Karakalpak language (Qaraqalpaq tili / Қарақалпақ тили).
Your mission is to translate Russian text into natural, grammatically flawless Karakalpak based on official academic norms.

{KARAKALPAK_ACADEMIC_GRAMMAR_PROMPT}

CRITICAL VOCABULARY RULES (NO KAZAKH / UZBEK BORROWINGS):
1. MANDATORY DICTIONARY GROUNDING:
   - When a word is in the MANDATORY GROUNDING VOCABULARY, you MUST use the exact Karakalpak translation provided.
   - DO NOT USE KAZAKH COGNATES!
     * Russian "искусственный" = Karakalpak "jasama" (NEVER "jasandı"!).
     * Russian "естественный" = Karakalpak "tábiyiy".
     * Russian "образование" = Karakalpak "bilimlendiriw" or "tálim".
2. Vowel Harmony & Suffix Agreement:
   - Front vowel words (containing e, i, ó, ú, á) take -pen/-men/-de/-den/-ge/-ler (e.g. "intellektpen", NOT "intellektpin").
   - Back vowel words (containing a, ı, o, u) take -pan/-man/-da/-dan/-ǵa/-lar.
3. Word Order:
   - Strict Turkic SOV order: Subject first, adverbials/objects in the middle, predicate verb at the end.
4. Output Format:
   - You MUST output ONLY a valid JSON object with exactly two keys:
     {{
       "latin": "Karakalpak translation in official Latin script",
       "cyrillic": "Karakalpak translation in Cyrillic script"
     }}
   - No explanations, no markdown comments, pure JSON only.
"""

MODEL_ALIASES = {
    "gemini-2.5-flash": "gemini-3.5-flash",
    "gemini-2.5-flash-lite": "gemini-3.5-flash-lite",
    "gemini-2.0-flash": "gemini-3.5-flash",
    "gemini-1.5-flash": "gemini-3.5-flash",
    "gemini-1.5-pro": "gemini-3.5-flash",
}

class KarakalpakTranslator:
    def __init__(self):
        pass

    def _get_client(self, api_key: Optional[str] = None) -> Optional[genai.Client]:
        key = (api_key or settings.GEMINI_API_KEY).strip()
        if not key:
            return None
        return genai.Client(api_key=key)

    async def translate(
        self,
        text: str,
        target_script: TargetScript = TargetScript.latin,
        model_override: Optional[str] = None,
        custom_api_key: Optional[str] = None,
        include_dictionary_matches: bool = True,
    ) -> TranslationResponse:
        """
        Translates Russian sentence into Karakalpak using Gemini AI Studio
        grounded with both the 16,000-entry dictionary and the 2017 Theoretical Grammar rules.
        """
        client = self._get_client(custom_api_key)
        
        # 1. Extract grounding dictionary entries
        matches = dictionary_service.extract_matches_for_text(text)
        glossary_text = dictionary_service.format_glossary_for_prompt(matches)

        # 2. Check if Gemini API Key is available
        if not client:
            return self._build_unconfigured_response(
                text=text,
                target_script=target_script,
                matches=matches if include_dictionary_matches else [],
            )

        # 3. Construct user prompt with grounding context
        user_prompt = f"""RUSSIAN SOURCE TEXT:
\"\"\"{text}\"\"\"

{glossary_text}

Translate the Russian source text above into natural, grammatically flawless Karakalpak according to the linguistic rules and provided dictionary grounding.
Return the result strictly as JSON:
{{"latin": "...", "cyrillic": "..."}}"""

        # 4. Determine models to attempt (with auto-upgrade for deprecated 2.x models)
        models_to_try = []
        if model_override:
            target_model = MODEL_ALIASES.get(model_override, model_override)
            models_to_try.append(target_model)
        
        default_model = MODEL_ALIASES.get(settings.GEMINI_MODEL, settings.GEMINI_MODEL)
        if default_model not in models_to_try:
            models_to_try.append(default_model)
            
        for fallback in settings.GEMINI_FALLBACK_MODELS:
            target_fallback = MODEL_ALIASES.get(fallback, fallback)
            if target_fallback not in models_to_try:
                models_to_try.append(target_fallback)

        last_error = None
        for model_name in models_to_try:
            try:
                logger.info(f"Attempting translation with Gemini model: {model_name}")
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=KARAKALPAK_SYSTEM_PROMPT,
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                )
                
                raw_text = response.text.strip()
                parsed_json = self._parse_gemini_json(raw_text)
                
                lat_text = parsed_json.get("latin", "").strip()
                cyr_text = parsed_json.get("cyrillic", "").strip()

                # Apply academic grammar post-processing for known morphophonemic slips
                lat_text = fix_common_grammatical_slips(lat_text)
                cyr_text = fix_common_grammatical_slips(cyr_text)

                # Build dictionary vocabulary note
                vocab_notes = []
                for m in matches:
                    lat_term = (m.qq_lat or "").split(";")[0].split("(")[0].strip()
                    vocab_notes.append(f"• {m.dictionary_lemma} ➔ {lat_term}")
                vocab_note_str = "\n".join(vocab_notes) if vocab_notes else None

                # Determine final primary translated text based on requested script
                if target_script == TargetScript.cyrillic:
                    final_text = cyr_text or lat_text
                elif target_script == TargetScript.both:
                    final_text = f"Latin:\n{lat_text}\n\nCyrillic:\n{cyr_text}"
                else: # latin default
                    final_text = lat_text or cyr_text

                return TranslationResponse(
                    source_text=text,
                    translated_text=final_text,
                    translated_latin=lat_text,
                    translated_cyrillic=cyr_text,
                    target_script=target_script.value,
                    model_used=model_name,
                    matched_terms_count=len(matches),
                    matched_terms=matches if include_dictionary_matches else [],
                    used_vocabulary_note=vocab_note_str,
                )
            except APIError as e:
                logger.warning(f"Gemini API error with {model_name}: {e}")
                last_error = e
                continue
            except Exception as e:
                logger.warning(f"Error calling {model_name}: {e}")
                last_error = e
                continue

        # If all models failed
        logger.error(f"All Gemini models failed. Last error: {last_error}")
        raise RuntimeError(f"Translation failed via AI Studio: {last_error}")

    def _parse_gemini_json(self, raw_text: str) -> dict:
        """Safely parse JSON response from Gemini, removing any accidental markdown fence."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except Exception:
            lat_match = re.search(r'"latin"\s*:\s*"(.*?)"', cleaned, re.DOTALL)
            cyr_match = re.search(r'"cyrillic"\s*:\s*"(.*?)"', cleaned, re.DOTALL)
            return {
                "latin": lat_match.group(1) if lat_match else cleaned,
                "cyrillic": cyr_match.group(1) if cyr_match else "",
            }

    def _build_unconfigured_response(
        self,
        text: str,
        target_script: TargetScript,
        matches: list[DictionaryMatch]
    ) -> TranslationResponse:
        glossary_summary = ", ".join(
            [f"{m.source_word} -> {m.qq_lat}" for m in matches[:5]]
        )
        msg_lat = (
            f"[API Key Required] GEMINI_API_KEY environment variable is not configured. "
            f"Please set your Google AI Studio API Key on Render or in .env to enable full neural translation. "
            f"Dictionary found {len(matches)} matching terms: {glossary_summary}"
        )
        return TranslationResponse(
            source_text=text,
            translated_text=msg_lat,
            translated_latin=msg_lat,
            translated_cyrillic=msg_lat,
            target_script=target_script.value,
            model_used="dictionary-offline-mode (GEMINI_API_KEY not set)",
            matched_terms_count=len(matches),
            matched_terms=matches,
        )

translator_service = KarakalpakTranslator()
