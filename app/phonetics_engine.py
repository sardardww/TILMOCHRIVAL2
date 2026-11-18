"""
Official Karakalpak Phonetics & Syllabification Engine.
Ported and enhanced from open-source qaraqalpaq/grammatika (https://github.com/qaraqalpaq/grammatika)
Includes syllable segmentation (buwınǵa bóliw), phonetic classification of vowels and consonants,
and syllable-level vowel harmony verification.
"""
import re
from typing import List

# --- DAWÍSLÍLAR (VOWELS) ---
VOWELS_ALL = ('a', 'á', 'i', 'ı', 'e', 'o', 'ó', 'u', 'ú')
JUWAN_DAWISLILAR = ('a', 'ı', 'o', 'u')        # Back / Hard vowels
JINISHKE_DAWISLILAR = ('á', 'i', 'ó', 'ú', 'e') # Front / Soft vowels

ERINLIK_DAWISLILAR = ('o', 'u', 'ú', 'ó')       # Rounded / Labial
EZIWLIK_DAWISLILAR = ('a', 'á', 'ı', 'i', 'e')   # Unrounded

ASHIQ_DAWISLILAR = ('a', 'á', 'o', 'ó')         # Open / Low
QISIQ_DAWISLILAR = ('ı', 'i', 'u', 'ú', 'e')     # Close / High

FRONT_VOWEL_SET = set("áieóúÁİEÓÚ")
BACK_VOWEL_SET = set("aıouAIOU")

# --- DAWÍSSÍZLAR (CONSONANTS) ---
CONSONANTS_ALL = (
    'b', 'v', 'g', 'ǵ', 'd', 'j', 'z', 'y', 'k', 'q', 'l', 'm',
    'h', 'n', 'ń', 'p', 'r', 's', 't', 'w', 'f', 'x', 'c', 'sh', 'ch'
)

UNLI_DAWISSIZLAR = ('b', 'v', 'g', 'ǵ', 'd', 'j', 'z', 'l', 'm', 'n', 'ń', 'r', 'w', 'y')
UNSIZ_DAWISSIZLAR = ('p', 'f', 'k', 'q', 't', 'sh', 's', 'x', 'h', 'c', 'ch')

# Classification by Place of Articulation (Jasalıw ornı)
QOS_ERINLIK = ('b', 'p', 'm', 'w')
ERINLIK_TISLIK = ('v', 'f')
TIL_ALDI = ('t', 'd', 'n', 'l', 's', 'sh', 'z', 'j', 'r', 'c', 'ch')
TIL_ORTASI = ('y',)
TIL_ARTI = ('g', 'k')
KISHKENE_TILLIK = ('q', 'ǵ', 'ń', 'x')
KOMEKEY = ('h',)

# Classification by Manner of Articulation (Jasalıw usılı)
JABISINQI = ('p', 'b', 'm', 't', 'd', 'n', 'g', 'k', 'q', 'ń', 'c', 'ch')
JUWISINQI = ('w', 'f', 'v', 's', 'z', 'l', 'sh', 'j', 'y', 'h', 'ǵ', 'x')

# Syllabification Regex (Ported from qaraqalpaq/grammatika buwin.ts)
_SYLLABLE_REGEX = re.compile(
    r"[^aáiıeoóuú]*[aáiıeoóuú]+(?:[^aáiıeoóuú]*$|[^aáiıeoóuú](?=[^aáiıeoóuú]))?",
    re.IGNORECASE
)

def buwinga_bol(soz: str) -> List[str]:
    """
    Sózdi buwınlarǵa bóliwshi funkciya.
    Mısalı: buwinga_bol('qaraqalpaq') -> ['qa', 'ra', 'qal', 'paq']
    """
    if not soz or not soz.strip():
        return []
    return _SYLLABLE_REGEX.findall(soz.strip())

def juwan_buwinba(buwin: str) -> bool:
    """
    Buwınnıń juwan (hard/back) yaki jińishke (soft/front) ekenligin anıqlaw.
    Returns True for hard/back vowels (a, ı, o, u), False for front vowels (á, i, e, ó, ú).
    Avoids Python Unicode case-folding trap between dotless 'ı' and dotted 'i'.
    """
    for ch in buwin:
        if ch in FRONT_VOWEL_SET:
            return False
    return True

def ashiq_buwinba(buwin: str) -> bool:
    """Ashıq buwın: dawıslı ses penen tamamlanatuǵın buwın (V, CV)."""
    return bool(re.search(r"[aáiıeoóuúÁİEÓÚ]$", buwin))

def tuyiq_buwinba(buwin: str) -> bool:
    """Tuyıq buwın: dawıslıdan baslanıp, dawıssızǵa tamamlanatuǵın buwın (VC)."""
    return bool(re.search(r"^[aáiıeoóuúÁİEÓÚ]", buwin)) and not ashiq_buwinba(buwin)

def qamaw_buwinba(buwin: str) -> bool:
    """Qamaw buwın: dawıssızdan baslanıp, dawıssızǵa tamamlanatuǵın buwın (CVC)."""
    return not bool(re.search(r"^[aáiıeoóuúÁİEÓÚ]", buwin)) and not ashiq_buwinba(buwin)

def aqirgi_ses(soz: str) -> str:
    """
    Sózdiń aqırǵı sesin (háribin) qaytaradı.
    'sh' hám 'ch' qospa dawıssızların bólek ses sıpatında tutadı.
    """
    if not soz:
        return ""
    clean = soz.strip().lower()
    if clean.endswith("sh") or clean.endswith("ch"):
        return clean[-2:]
    return clean[-1]

def aqirgi_buwin_unlime(soz: str) -> bool:
    """Sózdiń aqırǵı buwını únli seske tamamlanǵanın tekseredi."""
    buwinlar = buwinga_bol(soz)
    if not buwinlar:
        return False
    last_syl = buwinlar[-1].lower()
    last_s = aqirgi_ses(last_syl)
    return last_s in UNLI_DAWISSIZLAR or last_s in VOWELS_ALL

def jalga_seplik(soz: str, seplik: str) -> str:
    """
    Attaches grammatically immaculate case suffix to any Karakalpak noun or loanword.
    seplik options: 'ilik', 'baris', 'tabis', 'orin', 'shigis', 'komekshi'
    """
    syls = buwinga_bol(soz)
    if not syls:
        return soz
    is_juwan = juwan_buwinba(syls[-1])
    last = aqirgi_ses(soz)
    is_vowel = last in VOWELS_ALL
    is_voiceless = last in UNSIZ_DAWISSIZLAR
    is_sonorant_nasal = last in ('n', 'ń', 'm')
    
    if seplik == 'ilik':
        if is_vowel:
            return soz + ('nıń' if is_juwan else 'niń')
        elif is_voiceless:
            return soz + ('tıń' if is_juwan else 'tiń')
        else:
            return soz + ('dıń' if is_juwan else 'diń')
            
    elif seplik == 'baris':
        if is_voiceless:
            return soz + ('qa' if is_juwan else 'ke')
        else:
            return soz + ('ǵa' if is_juwan else 'ge')
            
    elif seplik == 'tabis':
        if is_vowel:
            return soz + ('nı' if is_juwan else 'ni')
        elif is_voiceless:
            return soz + ('tı' if is_juwan else 'ti')
        else:
            return soz + ('dı' if is_juwan else 'di')
            
    elif seplik == 'orin':
        if is_voiceless:
            return soz + ('ta' if is_juwan else 'te')
        else:
            return soz + ('da' if is_juwan else 'de')
            
    elif seplik == 'shigis':
        if is_voiceless:
            return soz + ('tan' if is_juwan else 'ten')
        elif is_sonorant_nasal:
            return soz + ('nan' if is_juwan else 'nen')
        else:
            return soz + ('dan' if is_juwan else 'den')
            
    elif seplik == 'komekshi':
        if is_voiceless:
            return soz + 'penen'
        elif last in ('b', 'v', 'g', 'ǵ', 'd', 'z', 'j'):
            return soz + 'benen'
        else:
            return soz + 'menen'
            
    return soz
