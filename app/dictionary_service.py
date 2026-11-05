import difflib
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from app.config import settings
from app.schemas import DictionaryMatch

logger = logging.getLogger(__name__)

# Russian inflection endings for robust lemmatization/stemming
RU_ENDINGS = [
    # Verb reflexive & compound endings
    'уются', 'ются', 'аются', 'яются', 'ется', 'ится', 'утся',
    'ующий', 'ющая', 'ющее', 'ющие', 'ющих', 'ющим', 'ущей',
    'ованный', 'ованная', 'ованное', 'ованные', 'ованных', 'ованным',
    'ование', 'евание', 'ивание', 'ывание', 'ение', 'ание',
    'овать', 'евать', 'ывать', 'ивать', 'ать', 'ять', 'еть', 'ить', 'уть', 'сти', 'зти',
    'вшись', 'вши', 'вша', 'вше',
    'вший', 'вшие', 'вших', 'вшим', 'вшего', 'вшую', 'вшем',
    'нный', 'нная', 'нное', 'нные', 'нных', 'нным', 'нными', 'нном',
    'емый', 'емая', 'емое', 'емые', 'емых', 'емым', 'емом',
    # Plural & Case endings
    'иями', 'ями', 'ами', 'ях', 'ах', 'ям', 'ам', 'ей', 'ов', 'ев',
    'ого', 'его', 'ому', 'ему', 'ыми', 'ими', 'ых', 'их', 'ую', 'юю',
    'ая', 'яя', 'ое', 'ее', 'ые', 'ие', 'ый', 'ий', 'ой',
    'ал', 'ила', 'или', 'али', 'ил', 'ит', 'ят', 'ут', 'ют', 'ет', 'ешь', 'ишь',
    'ают', 'яют', 'ите', 'ете',
    # Single suffixes
    'ом', 'ем', 'ой', 'ей', 'ью', 'а', 'е', 'и', 'о', 'у', 'ы', 'ь', 'я'
]


class KarakalpakDictionaryService:
    def __init__(self, dict_path: Optional[Path] = None):
        self.dict_path = dict_path or settings.DICTIONARY_PATH
        self.dictionary: Dict[str, Dict[str, str]] = {}
        self.stem_index: Dict[str, List[str]] = {}
        self.phrase_keys: List[str] = []
        self._is_loaded = False
        self.load()

    def load(self):
        """Loads and pre-indexes the 16,000+ Russian-Karakalpak dictionary entries."""
        if not self.dict_path.exists():
            logger.warning(f"Dictionary file not found at {self.dict_path}. Dictionary features will be inactive.")
            return

        try:
            with open(self.dict_path, "r", encoding="utf-8") as f:
                self.dictionary = json.load(f)
            
            logger.info(f"Loaded {len(self.dictionary)} dictionary entries from {self.dict_path}")
            
            # Pre-index for rapid stem-based lookup and multi-word phrase matching
            self.stem_index = {}
            self.phrase_keys = []
            
            for key in self.dictionary.keys():
                clean_key = re.sub(r'\(.*?\)', '', key).strip().lower().replace('ё', 'е')
                if not clean_key:
                    continue
                
                # If key has multiple words (e.g. "железная дорога")
                if " " in clean_key:
                    self.phrase_keys.append(clean_key)

                # Map stems to dictionary key
                for stem in self.get_stems(clean_key):
                    if stem not in self.stem_index:
                        self.stem_index[stem] = []
                    if key not in self.stem_index[stem]:
                        self.stem_index[stem].append(key)
            
            self._is_loaded = True
            logger.info(f"Pre-indexed {len(self.stem_index)} unique word stems for fast translation grounding.")
        except Exception as e:
            logger.error(f"Error loading dictionary: {e}", exc_info=True)

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def entry_count(self) -> int:
        return len(self.dictionary)

    @staticmethod
    def get_stems(word: str) -> List[str]:
        """Generate possible Russian morphological stems for a word."""
        w = word.lower().replace('ё', 'е').strip()
        stems = [w]
        for suf in RU_ENDINGS:
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                stem = w[:-len(suf)]
                stems.append(stem)
                # Handle thematic vowels for verbs/nouns
                for v in ('а', 'е', 'и', 'ы', 'я', 'о'):
                    if stem.endswith(v) and len(stem) > 3:
                        stems.append(stem[:-1])
        return list(dict.fromkeys(stems))

    def extract_matches_for_text(self, text: str, max_terms: int = 40) -> List[DictionaryMatch]:
        """
        Extracts verified dictionary matches for any Russian sentence or paragraph.
        Performs multi-word collocation search, exact word matching, and stem matching.
        """
        if not self._is_loaded:
            return []

        text_lower = text.lower().replace('ё', 'е')
        matches: Dict[str, DictionaryMatch] = {}
        seen_keys = set()

        # 1. Multi-word phrases (e.g. "детский сад", "железная дорога")
        for phrase in self.phrase_keys:
            if phrase in text_lower and phrase not in seen_keys:
                entry = self.dictionary.get(phrase)
                if entry:
                    seen_keys.add(phrase)
                    matches[phrase] = DictionaryMatch(
                        source_word=phrase,
                        dictionary_lemma=phrase,
                        qq_lat=entry.get("qq_lat"),
                        qq_cyr=entry.get("qq_cyr"),
                    )
            if len(matches) >= max_terms:
                break

        # 2. Tokenize words
        words = re.findall(r'[А-Яа-яЁёA-Za-z]+', text)
        for original_word in words:
            if len(matches) >= max_terms:
                break
            w_norm = original_word.lower().replace('ё', 'е')
            if len(w_norm) < 2 or original_word in matches:
                continue

            # Check direct exact match
            matched_key = None
            if w_norm in self.dictionary:
                matched_key = w_norm
            else:
                # Check stems
                for stem in self.get_stems(w_norm):
                    if stem in self.stem_index and self.stem_index[stem]:
                        matched_key = self.stem_index[stem][0]
                        break

            # If still not matched and word has typos, try fuzzy matching against dictionary
            if not matched_key and len(w_norm) >= 5:
                close = difflib.get_close_matches(w_norm, self.dictionary.keys(), n=1, cutoff=0.80)
                if close:
                    matched_key = close[0]

            if matched_key and matched_key not in seen_keys:
                seen_keys.add(matched_key)
                entry = self.dictionary[matched_key]
                matches[original_word] = DictionaryMatch(
                    source_word=original_word,
                    dictionary_lemma=matched_key,
                    qq_lat=entry.get("qq_lat"),
                    qq_cyr=entry.get("qq_cyr"),
                )

        return list(matches.values())

    def format_glossary_for_prompt(self, matches: List[DictionaryMatch]) -> str:
        """Formats matched entries into a compact, precise system instruction block."""
        if not matches:
            return ""

        lines = ["MANDATORY GROUNDING VOCABULARY (Russian to Karakalpak Dictionary):"]
        for m in matches:
            lat = (m.qq_lat or "").strip()
            cyr = (m.qq_cyr or "").strip()
            # Clean up excessively long example sentences from dictionary notes for prompt efficiency
            lat_clean = lat.split(";")[0].split("(")[0].strip() or lat
            cyr_clean = cyr.split(";")[0].split("(")[0].strip() or cyr
            lines.append(f'- "{m.dictionary_lemma}" (input: "{m.source_word}") => Latin: "{lat_clean}" | Cyrillic: "{cyr_clean}"')
        
        return "\n".join(lines)

    def search(self, query: str, limit: int = 10) -> List[DictionaryMatch]:
        """Search dictionary by query prefix, exact word, or stem."""
        if not self._is_loaded:
            return []

        q_norm = query.lower().replace('ё', 'е').strip()
        results: List[DictionaryMatch] = []
        seen = set()

        # 1. Exact match
        if q_norm in self.dictionary:
            seen.add(q_norm)
            e = self.dictionary[q_norm]
            results.append(DictionaryMatch(
                source_word=query,
                dictionary_lemma=q_norm,
                qq_lat=e.get("qq_lat"),
                qq_cyr=e.get("qq_cyr")
            ))

        # 2. Stem match
        for stem in self.get_stems(q_norm):
            for candidate in self.stem_index.get(stem, []):
                if candidate not in seen:
                    seen.add(candidate)
                    e = self.dictionary[candidate]
                    results.append(DictionaryMatch(
                        source_word=query,
                        dictionary_lemma=candidate,
                        qq_lat=e.get("qq_lat"),
                        qq_cyr=e.get("qq_cyr")
                    ))
                if len(results) >= limit:
                    return results

        # 3. Substring / Prefix match
        for key, entry in self.dictionary.items():
            if key.startswith(q_norm) and key not in seen:
                seen.add(key)
                results.append(DictionaryMatch(
                    source_word=query,
                    dictionary_lemma=key,
                    qq_lat=entry.get("qq_lat"),
                    qq_cyr=entry.get("qq_cyr")
                ))
            if len(results) >= limit:
                break

        return results


dictionary_service = KarakalpakDictionaryService()
