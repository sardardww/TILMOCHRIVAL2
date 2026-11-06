"""
Karakalpak Theoretical Grammar Engine
Based on the academic textbook:
'QARAQALPAQ TILINIŃ TEORIYALÍQ GRAMMATIKASÍ'
Authors: M. Qudaybergenov, A. Qazaqbaeva, A. Kurtchaev (Nókis, 2017)
Dynamically grounded in data/KARAKALPAK_THEORETICAL_GRAMMAR.md
"""
import re
from pathlib import Path
from typing import List, Tuple

# Vowel classifications according to Karakalpak Phonology
BACK_VOWELS = set("aıouAIOUá")      # Juwan dawıslılar (a, ı, o, u)
FRONT_VOWELS = set("eióúeiÓÚEİ")    # Jińishke dawıslılar (e, i, ó, ú, á)

# Consonant classifications
VOICELESS_CONSONANTS = set("ptkqsşshchxíPTKQSŞSHCHX") # Qatań dawıssızlar (p, t, k, q, s, sh, ch, x, f)
VOICED_CONSONANTS = set("bdgǵvzjBDGǴVZJ")            # Uyań dawıssızlar (b, d, g, ǵ, v, z, j)
SONORANT_CONSONANTS = set("lmnńrwylmnŃRWY")          # Únli dawıssızlar (m, n, ń, l, r, w, y)

GRAMMAR_MD_PATH = Path(__file__).resolve().parent.parent / "data" / "KARAKALPAK_THEORETICAL_GRAMMAR.md"

def load_academic_grammar_text() -> str:
    """
    Dynamically loads the full theoretical grammar markdown file.
    Provides live synchronization so any edit in KARAKALPAK_THEORETICAL_GRAMMAR.md
    immediately shapes the prompt and grammar validation.
    """
    if GRAMMAR_MD_PATH.exists():
        try:
            return GRAMMAR_MD_PATH.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return "Official Karakalpak Academic Grammar: Follow strict Singarmonizm and SOV syntax."

# Pre-compiled static rules for phonology, loanwords, and toponyms
STATIC_SLIPS_PATTERNS: List[Tuple[str, str]] = [
    # Core Kazakh/Uzbek false friends
    (r"\bjastar([a-zıóúáǵń]*)\b", r"jaslar\1"),
    (r"\bJastar([a-zıóúáǵń]*)\b", r"Jaslar\1"),
    (r"\bjasand([ıi])\b", "jasama"),
    (r"\bjasandıq\b", "jasamalıq"),
    (r"\bjasalma\b", "jasama"),
    (r"\bжасанды\b", "жасама"),
    # Toponyms & proper names
    (r"\bUzgidromet\b", "Ózgidromet"),
    (r"\bSavitskiy\b", "Savickiy"),
    (r"\bYunçjou\b", "Yunchjou"),
    (r"\bAlat (rayonı|rayonında|rayonına)\b", r"Álot \1"),
    (r"\bmínnetleme([a-zıóúáǵń]*)\b", r"minnetleme\1"),
    (r"\btıs (pastası|shetkası|pastasi|shetkasi)\b", r"tis \1"),
    (r"\buzunlıq([a-zıóúáǵń]*)\b", r"uzınlıq\1"),
    (r"\bjaraqat([a-zıóúáǵń]*)\b", r"jarahat\1"),
    (r"\bseksewil([a-zıóúáǵń]*)\b", r"seksewil\1"),
    (r"\bpuxara([a-zıóúáǵń]*)\b", r"puqara\1"),
    (r"\bPuxara([a-zıóúáǵń]*)\b", r"Puqara\1"),
    (r"\bjáriyalad([ıi])\b", r"jariylad\1"),
    (r"\bprezidendi\b", "prezidenti"),
    (r"\bPrezidendi\b", "Prezidenti"),
    (r"\bShavqat\b", "Shavkat"),
    (r"\bbazıxana\b", "bajıxana"),
    (r"\bBazıxana\b", "Bajıxana"),
    (r"\btamoxana\b", "bajıxana"),
    (r"\bTamoxana\b", "Bajıxana"),
    (r"\bdvigatil([a-zıóúáǵń]*)\b", r"dvigatel\1"),
    (r"\bDvigatil([a-zıóúáǵń]*)\b", r"Dvigatel\1"),
    (r"\bpanelil([a-zıóúáǵń]*)\b", r"panell\1"),
    (r"\bpanelgel([a-zıóúáǵń]*)\b", r"panellerg\1"),
    (r"\bBizinsiz\b", "Biziń"),
    (r"\bbizinsiz\b", "biziń"),
    (r"\bobyektst([a-zıóúáǵń]*)\b", r"obyekt\1"),
    (r"\basteroyid([a-zıóúáǵń]*)\b", r"asteroid\1"),
    (r"\bátirindegi\b", "átirapındaǵı"),
    (r"\b(x|X)alıq aralıq\b", r"\1alıqaralıq"),
    (r"\bjumısqar sapar([a-zıóúáǵń]*)\b", r"jumıs sapar\1"),
    (r"\bÁdministraciya([a-zıóúáǵń]*)\b", r"Administraciya\1"),
    (r"\bádministraciya([a-zıóúáǵń]*)\b", r"administraciya\1"),
    (r"\bmenedjerdiler\b", "menedjerler"),
    (r"\btop-menedjerdiler\b", "top-menedjerler"),
    (r"\bnapaqá\b", "napaqa"),
    (r"\bNapaqá\b", "Napaqa"),
    (r"\btirishilik\b", "tirshilik"),
    (r"\bTirishilik\b", "Tirshilik"),
    (r"\btábiyǵiy\b", "tábiyiy"),
    (r"\bTábiyǵiy\b", "Tábiyiy"),
    (r"\bkútew([a-zıóúáǵń]*)\b", r"kútiw\1"),
    (r"\bKútew([a-zıóúáǵń]*)\b", r"Kútiw\1"),
    (r"\bkonkurenciya\b", "báseki"),
    (r"\bKonkurenciya\b", "Báseki"),
    (r"\bUsırasıw\b", "Ushırasıw"),
    (r"\busırasıw\b", "ushırasıw"),
    (r"\b(r|R)ayon turıwshı([a-zıóúáǵń]*)\b", r"\1ayon turǵın\2"),
    (r"\b(b|B)untan aldın\b", r"\1unnan aldın"),
    (r"\b(s|S)ebepti\b", r"\1ebepli"),
    (r"\bBunga\b", "Buǵan"),
    (r"\bbunga\b", "buǵan"),
    (r"\b(f|F)aktni\b", r"\1aktti"),
    (r"\b(d|D)odalawda\b", r"\1alqılamaqta"),
    (r"\b(p|P)akistanlı\b", r"\1akistanlıq"),
    (r"\b(s|S)tantsiya([a-zıóúáǵń]*)\b", r"\1tanciya\2"),
    (r"\b(a|A)ktsiya([a-zıóúáǵń]*)\b", r"\1kciya\2"),
    (r"\bhámde\b", "hám de"),
    (r"\bHámde\b", "Hám de"),
    # Audited from posts 140-141
    (r"\bdepartamendi\b", "departamenti"),
    (r"\bDepartamendi\b", "Departamenti"),
    (r"\bwáqıya([a-zıóúáǵń]*)\b", r"waqıya\1"),
    (r"\bWáqıya([a-zıóúáǵń]*)\b", r"Waqıya\1"),
    (r"\bkitniń\b", "kittiń"),
    (r"\balımlar\b", "ilimpazlar"),
    (r"\bAlımlar\b", "Ilimpazlar"),
    (r"\babıroylı\b", "abıraylı"),
    (r"\bAbıroylı\b", "Abıraylı"),
    (r"\bmoyındap\b", "moyınlap"),
    (r"\bmártebe\b", "márte"),
    (r"\bshıyrinlik([a-zıóúáǵń]*)\b", r"shiyrinlik\1"),
    (r"\bpútinley\b", "bútinley"),
    (r"\btásirsheń\b", "tásirsheń"),

    # Suffixes & Predicatives (Singarmonizm and Case Assimilation)
    (r"\bilimti\b", "ilimdi"),
    (r"\bилимти\b", "илимди"),
    (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]{2,}[mnńlrwy])ti\b", r"\1di"),
    (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]{2,}[mnńlrwy])tı\b", r"\1dı"),
    (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[eióúá][ptkqsxf])pin\b", r"\1pen"),
    (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[aıou][ptkqsxf])pin\b", r"\1pan"),
    (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[eióúá])mın\b", r"\1men"),
    (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[aıou])min\b", r"\1man"),
    (r"\bintellektp[ıi]n\b", "intellektpen"),
    (r"\bmashinapın\b", "mashinaman"),
    (r"\bprogrammistp[ıi]n\b", "programmistpen"),
    (r"\bstudentp[ıi]n\b", "studentpen"),
]

def _preserve_case_replace(match: re.Match, replacement: str) -> str:
    original = match.group(0)
    if original.isupper():
        return replacement.upper()
    elif original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement

def extract_dynamic_rules_from_markdown() -> List[Tuple[str, str]]:
    """
    Parses Markdown tables in KARAKALPAK_THEORETICAL_GRAMMAR.md:
    | *wrong_word* | **correct_word** |
    and compiles them into dynamic word-replacement rules.
    """
    text = load_academic_grammar_text()
    table_pattern = re.compile(r"\|\s*\*([^*]+)\*\s*\|\s*\*\*([^*]+)\*\*\s*\|")
    extracted_rules = []
    
    for match in table_pattern.finditer(text):
        mistakes = [m.strip() for m in match.group(1).split("/")]
        corrects = [c.strip() for c in match.group(2).split("/")]
        if not mistakes or not corrects:
            continue
        primary_correct = corrects[0]
        
        for m in mistakes:
            if not m or len(m) < 2:
                continue
            # Multi-word phrase or single word boundary
            clean_m = re.escape(m)
            pattern = rf"\b{clean_m}([a-zıóúáǵń]*)\b"
            
            # Suffix handling
            if " " in primary_correct or primary_correct.endswith(("di", "dı", "li", "lı")):
                extracted_rules.append((rf"\b{clean_m}\b", primary_correct))
            else:
                extracted_rules.append((pattern, rf"{primary_correct}\1"))

    return extracted_rules

def fix_common_grammatical_slips(text: str) -> str:
    """
    Post-processor that verifies and enforces grammar rules from both
    the static phonological engine and the dynamic KARAKALPAK_THEORETICAL_GRAMMAR.md file.
    """
    if not text:
        return text

    result = text
    
    # 1. Apply dynamic rules parsed straight from KARAKALPAK_THEORETICAL_GRAMMAR.md
    try:
        dynamic_rules = extract_dynamic_rules_from_markdown()
        for pattern, repl in dynamic_rules:
            if "\\" in repl:
                result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
            else:
                result = re.sub(
                    pattern,
                    lambda m, r=repl: _preserve_case_replace(m, r),
                    result,
                    flags=re.IGNORECASE
                )
    except Exception:
        pass

    # 2. Apply static phonology & orthography patterns
    for pattern, repl in STATIC_SLIPS_PATTERNS:
        if "\\" in repl or "(" in pattern:
            result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
        else:
            result = re.sub(
                pattern,
                lambda m, r=repl: _preserve_case_replace(m, r),
                result,
                flags=re.IGNORECASE
            )
            
    return result

# Export alias for backward compatibility
KARAKALPAK_ACADEMIC_GRAMMAR_PROMPT = load_academic_grammar_text()
