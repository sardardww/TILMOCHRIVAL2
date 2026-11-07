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
    # Foreign Latin letters & umlauts (Tatar, Turkmen, Turkish, German)
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
    # New audited slips from posts #381 - #399
    (r"\bengiziwdıń\b", "engiziwdiń"),
    (r"\b(t|T)echnologiya([a-zıóúáǵń]*)\b", r"\1exnologiya\2"),
    (r"\bmáselerin\b", "máselelerin"),
    (r"\bÁstanalıq\b", "Astanalıq"),
    (r"\bÁstana\b", "Astana"),
    (r"\b(p|P)rocess\b", r"\1roces"),
    (r"\bjúze keliw([a-zıóúáǵń]*)\b", r"júzege keliw\1"),
    (r"\b(q|Q)adaǵalaw ólshemler([a-zıóúáǵń]*)\b", r"\1adaǵalaw ilajlar\2"),
    (r"\bIshki isler uyımları\b", "Ishki isler organları"),
    (r"\btájiriybeli sapar([a-zıóúáǵń]*)\b", r"jumıs sapar\1"),
    (r"\bkútip barıw([a-zıóúáǵń]*)\b", r"kútip-baplaw\1"),
    (r"\b(j|J)asıl makan\b", r"\1asıl mákan"),
    (r"\b(u|U)lıwma milliy\b", r"\1lıwmamilliy"),
    (r"\b(q|Q)arıydarlardıń huqıqlar([a-zıóúáǵń]*)\b", r"\1utınıwshılardıń huqıqlar\2"),
    (r"\b(q|Q)ádemler taslamaqta\b", r"ilajlar kórmekte"),
    (r"\bqupıya orın([a-zıóúáǵń]*)\b", r"jasırın orın\1"),
    (r"\bǵalabalıq sport([a-zıóúáǵń]*)\b", r"ǵalaba sport\1"),
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
    # Highlighted mistakes audited from posts 142-143
    (r"\bbaslı qalaq\b", ""),
    (r"\bkinoqumar([a-zıóúáǵń]*)\b", r"kinosúyiwshi\1"),
    (r"\bKinoqumar([a-zıóúáǵń]*)\b", r"Kinosúyiwshi\1"),
    (r"\bdereklar\b", "derekler"),
    (r"\bDereklar\b", "Derekler"),
    (r"\boqsham([a-zıóúáǵń]*)\b", r"kesh\1"),
    (r"\bOqsham([a-zıóúáǵń]*)\b", r"Kesh\1"),
    (r"\bxizmet([a-zıóúáǵń]*)\b", r"xızmet\1"),
    (r"\bXizmet([a-zıóúáǵń]*)\b", r"Xızmet\1"),
    (r"\bBıqıńǵı\b", "Kúshli"),
    (r"\bjasawshı([a-zıóúáǵń]*)\b", r"turǵın\1"),
    (r"\bJasawshı([a-zıóúáǵń]*)\b", r"Turǵın\1"),
    # Critical audited slips from posts 146-215 (Highlighted)
    (r"\baksiy([a-zıóúáǵń]*)\b", r"akciy\1"),
    (r"\bAksiy([a-zıóúáǵń]*)\b", r"Akciy\1"),
    (r"\bádeyir\b", "ádeywir"),
    (r"\bÁdeyir\b", "Ádeywir"),
    (r"\bderek-oray([a-zıóúáǵń]*)\b", r"maǵlıwmatlar oray\1"),
    (r"\bderek oray([a-zıóúáǵń]*)\b", r"maǵlıwmatlar oray\1"),
    (r"\bshamamen\b", "shama menen"),
    (r"\bShamamen\b", "Shama menen"),
    (r"\bshıntlap\b", "shınında da"),
    (r"\bShıntlap\b", "Shınında da"),
    (r"\btopılıs([a-zıóúáǵń]*)\b", r"hújim\1"),
    (r"\bTopılıs([a-zıóúáǵń]*)\b", r"Hújim\1"),
    (r"\bjas basqan adamlard([ıi])\b", "kekselerdi"),
    (r"\bshıyrinlik([a-zıóúáǵń]*)\b", r"shiyrinlik\1"),
    (r"\bpútinley\b", "bútinley"),
    (r"\btásirsheń\b", "tásirsheń"),

    # Highlighted mistakes audited from posts 290-294
    (r"\b(t|T)ınıq toq[ıi]malar\b", r"\1iri toqımalar"),
    (r"\bJabıńqı\b", "Qaplama"),
    (r"\bjabıńqı\b", "qaplama"),
    (r"\bkletqa([a-zıóúáǵń]*)\b", r"kletka\1"),
    (r"\bKletqa([a-zıóúáǵń]*)\b", r"Kletka\1"),
    (r"\bkútik([a-zıóúáǵń]*)\b", r"kúyik\1"),
    (r"\bKútik([a-zıóúáǵń]*)\b", r"Kúyik\1"),
    (r"\bdıyqan([a-zıóúáǵń]*)\b", r"diyqan\1"),
    (r"\bDıyqan([a-zıóúáǵń]*)\b", r"Diyqan\1"),
    (r"\btaldap shıǵ([a-zıóúáǵń]*)\b", r"tallap shıǵ\1"),
    (r"\bTaldap shıǵ([a-zıóúáǵń]*)\b", r"Tallap shıǵ\1"),
    (r"\bshıń saatlar([a-zıóúáǵń]*)\b", r"eń tıǵız saatlar\1"),
    (r"\bShıń saatlar([a-zıóúáǵń]*)\b", r"Eń tıǵız saatlar\1"),
    (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]+)lerinin'\b", r"\1leriniń"),
    (r"\btarix\b", "tariyx"),
    (r"\bTarix\b", "Tariyx"),
    (r"\bashildi\b", "ashıldı"),
    (r"\bAshildi\b", "Ashıldı"),
    (r"\bzıyanlan([a-zıóúáǵń]*)\b", r"zaqımlan\1"),
    (r"\bZıyanlan([a-zıóúáǵń]*)\b", r"Zaqımlan\1"),
    (r"\bbarlıǵı tórt saat\b", "barı-joǵı tórt saat"),

    # Audited slips from latest 50 posts (#113-#294)
    (r"\bp'edestal([a-zıóúáǵń]*)\b", r"pedestal\1"),
    (r"\bP'edestal([a-zıóúáǵń]*)\b", r"Pedestal\1"),
    (r"\bjelelik arza\b", "elektronlıq arza"),
    (r"\bkadastrdi\b", "kadastrdı"),
    (r"\bKadastrdi\b", "Kadastrdı"),
    (r"\bsignaldi\b", "signaldı"),
    (r"\bSignaldi\b", "Signaldı"),
    (r"\bjırtqıshdı\b", "jırtqıshtı"),
    (r"\bıytı menen\b", "iyti menen"),
    (r"\baqsha jıliwda\b", "aqsha jıllawda"),
    (r"\bcirkumbinnıń ekzoplaneta\b", "cirkumbinar ekzoplaneta"),
    (r"\bretsenziy([a-zıóúáǵń]*)\b", r"recenziy\1"),
    (r"\bRetsenziy([a-zıóúáǵń]*)\b", r"Recenziy\1"),
    (r"\btastiyıqlaw([a-zıóúáǵń]*)\b", r"tastıyıqlaw\1"),
    (r"\bTastiyıqlaw([a-zıóúáǵń]*)\b", r"Tastıyıqlaw\1"),

    # Audited slips from posts #294-#386
    (r"\bUllı milletlik\b", "Ulıwma milliy"),
    (r"\bullı milletlik\b", "ulıwma milliy"),
    (r"\b(t|T)erek eguw\b", r"\1erek egiw"),
    (r"\b(k|K)ólem taraw boyınsha\b", r"\1óklemzarlastırıw boyınsha"),
    (r"\bmáhällä([a-zıóúáǵń]*)\b", r"máhálle\1"),
    (r"\bmáhállá([a-zıóúáǵń]*)\b", r"máhálle\1"),
    (r"\bMáhällä([a-zıóúáǵń]*)\b", r"Máhálle\1"),
    (r"\bMáhállá([a-zıóúáǵń]*)\b", r"Máhálle\1"),
    (r"\bKeniya sudi\b", "Keniya sudı"),
    (r"\bjasy tolmaǵan\b", "jası tolmaǵan"),
    (r"\bkómılgen\b", "kómilgen"),
    (r"\bKorolylıq\b", "Korolligi"),
    (r"\b(t|T)arafdar([a-zıóúáǵń]*)\b", r"\1árepdar\2"),
    (r"\bgúres sistemaları\b", "jawıngerlik sistemalar"),
    (r"\bkóp jıllardan berli\b", "kóp jıllardan beri"),
    (r"\bnarkobuzaqılıq([a-zıóúáǵń]*)\b", r"narkojınayatshılıq\1"),
    (r"\bnarkotikalıq qurallard([ıi])\b", "narkotikalıq zatlardı"),
    (r"\bbayraqdarlar\b", "sawrınlı orın iyeleri"),
    (r"\bmars tuqımı([a-zıóúáǵń]*)\b", r"mars jınısı\1"),
    (r"\b(m|M)eteorittıń\b", r"\1eteorittiń"),
    (r"\btereń erte dáwirler([a-zıóúáǵń]*)\b", r"áyyemgi dáwirler\1"),
    (r"\bshártterin\b", "shártlerin"),
    (r"\b(t|T)ibbiyot([a-zıóúáǵń]*)\b", r"\1edicina\2"),
    (r"\b(t|T)ezlestir([a-zıóúáǵń]*)\b", r"\1ezlet\2"),
    (r"\bintellekten paydalan([a-zıóúáǵń]*)\b", r"intellektten paydalan\1"),
    (r"\baqsha juwıw\b", "aqsha jıllaw"),

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
    
    # 0. Strict Character Normalization (Umlaut & Cyrillic homoglyph sanitizer)
    FOREIGN_CHARS_MAP = {
        'ä': 'á', 'Ä': 'Á',
        'ö': 'ó', 'Ö': 'Ó',
        'ü': 'ú', 'Ü': 'Ú',
        'ğ': 'ǵ', 'Ğ': 'Ǵ',
        'ş': 'sh', 'Ş': 'Sh',
        'ç': 'ch', 'Ç': 'Ch',
        'ñ': 'ń', 'Ñ': 'Ń',
        'İ': 'I',
        'ë': 'e', 'Ë': 'E',
        'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y', 'х': 'x',
        'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T'
    }
    for foreign_ch, safe_ch in FOREIGN_CHARS_MAP.items():
        result = result.replace(foreign_ch, safe_ch)

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
