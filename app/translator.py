import asyncio
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
from app.schemas import TargetScript, TranslationResponse, DictionaryMatch, TextCorrection

logger = logging.getLogger(__name__)

KARAKALPAK_SYSTEM_PROMPT = f"""You are a master linguist, expert Russian proofreader, and native professional translator specializing in the Karakalpak language (Qaraqalpaq tili / Қарақалпақ тили).
Your mission is to perform a mandatory 3-step translation pipeline from Russian into natural, grammatically flawless Karakalpak.

==================================================
MANDATORY 3-STEP TRANSLATION PIPELINE
==================================================

--- STEP 1: RUSSIAN SPELL-CHECK & GRAMMAR EDIT ---
- First, thoroughly inspect the Russian input text for any spelling errors, typos, missing/extra letters, or colloquial slips.
  Examples:
  * "исскуственный" -> "искусственный"
  * "здраствуйте" -> "здравствуйте"
  * "уневерситет" -> "университет"
  * "програмирование" -> "программирование"
  * "превейд" -> "привет"
- Edit and normalize the text into 100% correct literary Russian before proceeding to translation.
- Store the corrected Russian sentence in "corrected_russian".
- List each corrected word pair in "corrections": [{{"original": "...", "corrected": "..."}}]. If no errors were found, provide an empty list [].

--- STEP 2: VOCABULARY GROUNDING ---
- Check the MANDATORY GROUNDING VOCABULARY provided in the prompt.
- For all concepts in the corrected Russian sentence, strictly adhere to the Karakalpak terms provided.
- ZERO TOLERANCE FOR KAZAKH / UZBEK BORROWINGS:
  * Russian "искусственный" = Karakalpak "jasama" (NEVER Kazakh "jasandı"!).
  * Russian "естественный" = Karakalpak "tábiyiy".
  * Russian "образование" = Karakalpak "bilimlendiriw" or "tálim".

--- STEP 3: ACADEMIC KARAKALPAK TRANSLATION ---
Translate the corrected Russian text into Karakalpak adhering to:
1. Turkic SOV syntax (Subject -> Objects/Adverbs -> Verb at the end).
2. Singarmonizm / Vowel Harmony:
   - Front vowel words (containing e, i, ó, ú, á) take front suffixes (-pen, -men, -ge, -de, -ler). E.g. "intellektpen" (NEVER "intellektpin").
   - Back vowel words (containing a, ı, o, u) take back suffixes (-pan, -man, -ǵa, -da, -lar).

{KARAKALPAK_ACADEMIC_GRAMMAR_PROMPT}

OUTPUT FORMAT:
You MUST output ONLY a valid JSON object with these keys:
{{
  "corrected_russian": "Corrected Russian sentence",
  "corrections": [
    {{"original": "misspelled_word", "corrected": "correct_word"}}
  ],
  "latin": "Karakalpak translation in official 34-letter Latin script",
  "cyrillic": "Karakalpak translation in Cyrillic script"
}}
No markdown fences, no conversational prose, only pure JSON.
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
                corrected_ru = parsed_json.get("corrected_russian", text).strip()
                
                # Parse list of corrections
                raw_corrections = parsed_json.get("corrections", [])
                corrections_list = []
                if isinstance(raw_corrections, list):
                    for c in raw_corrections:
                        if isinstance(c, dict) and "original" in c and "corrected" in c:
                            corrections_list.append(TextCorrection(original=str(c["original"]), corrected=str(c["corrected"])))

                # If Russian typos were corrected, check if more dictionary matches can be discovered
                if corrected_ru and corrected_ru.lower() != text.lower():
                    extra_matches = dictionary_service.extract_matches_for_text(corrected_ru)
                    existing_lemmas = {m.dictionary_lemma for m in matches}
                    for em in extra_matches:
                        if em.dictionary_lemma not in existing_lemmas:
                            matches.append(em)
                            existing_lemmas.add(em.dictionary_lemma)

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
                    corrected_source_text=corrected_ru if corrected_ru != text else None,
                    corrections_made=corrections_list,
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
                # If 503 or 429, wait briefly and retry once
                if "503" in str(e) or "429" in str(e):
                    try:
                        logger.info(f"Retrying {model_name} after 1.5s...")
                        await asyncio.sleep(1.5)
                        retry_resp = client.models.generate_content(
                            model=model_name,
                            contents=user_prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=KARAKALPAK_SYSTEM_PROMPT,
                                temperature=0.1,
                                response_mime_type="application/json",
                            ),
                        )
                        raw_text = retry_resp.text.strip()
                        parsed_json = self._parse_gemini_json(raw_text)
                        lat_text = fix_common_grammatical_slips(parsed_json.get("latin", "").strip())
                        cyr_text = fix_common_grammatical_slips(parsed_json.get("cyrillic", "").strip())
                        final_text = cyr_text if target_script == TargetScript.cyrillic else (f"Latin:\n{lat_text}\n\nCyrillic:\n{cyr_text}" if target_script == TargetScript.both else lat_text)
                        return TranslationResponse(
                            source_text=text,
                            corrected_source_text=parsed_json.get("corrected_russian", text).strip() if parsed_json.get("corrected_russian", text).strip() != text else None,
                            translated_text=final_text,
                            translated_latin=lat_text,
                            translated_cyrillic=cyr_text,
                            target_script=target_script.value,
                            model_used=model_name,
                            matched_terms_count=len(matches),
                            matched_terms=matches if include_dictionary_matches else [],
                            used_vocabulary_note=vocab_note_str,
                        )
                    except Exception as retry_err:
                        logger.warning(f"Retry also failed for {model_name}: {retry_err}")
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
