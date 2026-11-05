"""
Karakalpak Theoretical Grammar Engine
Based on the academic textbook:
'QARAQALPAQ TILINIŃ TEORIYALÍQ GRAMMATIKASÍ'
Authors: M. Qudaybergenov, A. Qazaqbaeva, A. Kurtchaev (Nókis, 2017)
Updated with 2016 Official Karakalpak Latin Orthography and Anti-Uzbekism/Kazakhism lexical standards.
"""
import re

# Vowel classifications according to Karakalpak Phonology
BACK_VOWELS = set("aıouAIOUá")      # Juwan dawıslılar (a, ı, o, u)
FRONT_VOWELS = set("eióúeiÓÚEİ")    # Jińishke dawıslılar (e, i, ó, ú, á)

# Consonant classifications
VOICELESS_CONSONANTS = set("ptkqsşshchxíPTKQSŞSHCHX") # Qatań dawıssızlar (p, t, k, q, s, sh, ch, x, f)
VOICED_CONSONANTS = set("bdgǵvzjBDGǴVZJ")            # Uyań dawıssızlar (b, d, g, ǵ, v, z, j)
SONORANT_CONSONANTS = set("lmnńrwylmnŃRWY")          # Únli dawıssızlar (m, n, ń, l, r, w, y)

KARAKALPAK_ACADEMIC_GRAMMAR_PROMPT = """
ACADEMIC KARAKALPAK GRAMMAR & ORTHOGRAPHY GUIDE
(Source: Qaraqalpaq tiliniń teoriyalıq grammatikası, Nókis 2017 & 2016 Official Latin Orthography):

1. 2016 OFFICIAL LATIN ALPHABET & ORTHOGRAPHY RULES:
   - Letters with acute accents: Á á, Ǵ ǵ, Ń ń, Ó ó, Ú ú.
   - The dotless letter 'ı' (uppercase 'I') is a BACK vowel (juwan dawıslı): qız, uzınlıq, shıǵıs.
   - The dotted letter 'i' (uppercase 'İ') is a FRONT vowel (jińishke dawıslı): bir, tis, minnetleme.
   - NOTE: There is NO 'í' with acute for front 'i'. NEVER write 'mínnetleme' -> write 'minnetleme'.
   - The letter 'C c' is used in digraph 'Ch ch' or in scientific/foreign loanwords.
   - Proper names and toponyms: 'Savitskiy' -> 'Savickiy', 'Uzgidromet' -> 'Ózgidromet', 'Alat' -> 'Álot'.

2. VOWEL HARMONY (Singarmonizm nızamı):
   - Juwan (Back vowels: a, ı, o, u): Suffixes MUST use back vowels (-lar, -ǵa, -da, -dan, -man, -sań, -qan).
   - Jińishke (Front vowels: e, i, ó, ú, á): Suffixes MUST use front vowels (-ler, -ge, -de, -den, -men, -seń, -gen).
   - Loanwords ending in front vowel syllables take front suffixes: 'intellektpen' (NEVER 'intellektpin' or 'intellektpın'), 'prezidentke', 'universitetke'.

3. STRICT PROHIBITION OF UZBEK AND KAZAKH INTRUSIONS (False Friends):
   * ALWAYS use pure Karakalpak literary forms:
     - Russian 'искусственный' / Uzbek 'sun\\'iy' -> Karakalpak 'jasama' (NEVER Kazakh 'jasandı'!).
     - Uzbek 'tanaffus' -> Karakalpak 'tánepis'
     - Uzbek 'saroy' -> Karakalpak 'saray'
     - Uzbek 'bezorilik' -> Karakalpak 'buzaqılıq'
     - Uzbek 'kambag\\'al' -> Karakalpak 'kámbaǵal'
     - Uzbek 'tezyurar' -> Karakalpak 'tez júrer'
     - Uzbek 'jonivor' -> Karakalpak 'janzat'
     - Uzbek 'tunda' -> Karakalpak 'túnde'
     - Uzbek 'kunda' -> Karakalpak 'kúnde'
     - Uzbek 'turar joy' -> Karakalpak 'turaq jay'
     - Uzbek 'hakam / hakamlik' -> Karakalpak 'tóreshi / tóreshilik'
     - Uzbek 'nazariy' -> Karakalpak 'teoriyalıq'
     - Uzbek 'bajarmasa' -> Karakalpak 'orınlamasa'
     - Uzbek 'do\\'kon' -> Karakalpak 'dúkan'
     - Uzbek 'qoida' -> Karakalpak 'qaǵıyda'
     - Uzbek 'favqulodda' -> Karakalpak 'ayrıqsha'
     - Uzbek 'mutaxassis' -> Karakalpak 'qánige'
     - Uzbek 'uchun' -> Karakalpak 'ushın'
     - Uzbek 'chunki' -> Karakalpak 'sebebi' or 'óytkeni'
     - Uzbek 'bilan' -> Karakalpak 'menen'
     - Uzbek 'qarshi' -> Karakalpak 'qarsı'
     - Uzbek 'loyiha' / Kazakh 'joba' -> Karakalpak 'joybar'
     - Uzbek 'yo\\'nalish' / Kazakh 'baǵıt' -> Karakalpak 'baǵdar'
     - Uzbek 'imkoniyat' / Kazakh 'múmkindik' -> Karakalpak 'múmkinshilik'
     - Uzbek 'yig\\'ilish' / Kazakh 'jıynalıs' -> Karakalpak 'májilis'
     - Kazakh 'ótkezdi / ótkezildi' -> Karakalpak 'ótkerdi / ótkerildi'
     - Kazakh 'erkinen ayırıw' -> Karakalpak 'azatlıǵınan ayırıw'
     - Kazakh 'túngish márte' -> Karakalpak 'dáslepki márte'
     - Kazakh 'orın aldı' -> Karakalpak 'júz berdi'
     - Kazakh 'quwattı' -> Karakalpak 'quwatlı'
     - Kazakh 'qáwipti' -> Karakalpak 'qáwipli'
     - Kazakh 'qarap' -> Karakalpak 'qaray' (e.g., 'hawa rayına qaray')

4. PREDICATIVE / PERSONAL ENDINGS (Betlik jalǵawları):
   * 1st Person Singular (Men):
     - After vowels or sonorants (m, n, ń, l, r, w, y): -man / -men (oqıwshıman, muǵallimmen)
     - After voiceless consonants (p, t, k, q, s, sh, x, f): -pan / -pen (intellektpen, jaspan)
     - After voiced consonants (b, d, g, ǵ, z, j): -ban / -ben (jazıwshıban)
   * 1st Person Plural (Biz / Bizler): -mız / -miz (adam-bız, student-piz)
   * 2nd Person Singular (Sen): -sań / -seń
   * 2nd Person Plural / Polite (Siz / Sizler): -sız / -siz, -sızlar / -sizler
   * 3rd Person (Ol / Olar): Usually zero ending (-) or -dı / -di.

5. NOUN CASE SYSTEM (Seplik jalǵawları):
   * Ataw (Nominative): zero ending (-)
   * Iyelik (Genitive): -nıń / -niń, -dıń / -diń, -tıń / -tiń
   * Barıs (Dative): -ǵa / -ge, -qa / -ke (-na / -ne after 3rd person possessive)
   * Tabıs (Accusative): -nı / -ni, -dı / -di, -tı / -ti (-n after 3rd person possessive)
   * Orın (Locative): -da / -de, -ta / -te (-nda / -nde after 3rd person possessive)
   * Shıǵıs (Ablative): -dan / -den, -tan / -ten, -nan / -nen

6. SYNTAX (Gáp dúzilisi):
   * Strict Turkic SOV order: Baslawısh (Subject) -> Anıqlawısh/Tolıqlawısh/Pısıqlawısh (Modifiers/Objects) -> Bayanlawısh (Verb at the very end).
   * Modifiers (adjectives/numerals) precede the modified noun and NEVER take plural suffixes (e.g. 'biyik tawlar', NOT 'biyikler tawlar').
"""


def _preserve_case_replace(match: re.Match, replacement: str) -> str:
    """Helper to maintain uppercase/capitalized casing during regex replacements."""
    original = match.group(0)
    if original.isupper():
        return replacement.upper()
    elif original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


# High-precision list of regex replacement patterns for Karakalpak post-processing
COMMON_SLIPS_PATTERNS = [
    # 1. Core Kazakh false friends
    (r"\bjasand([ıi])\b", "jasama"),
    (r"\bjasandıq\b", "jasamalıq"),
    (r"\bжасанды\b", "жасама"),
    (r"\bótkez([a-zıóúáǵń]+)\b", r"ótker\1"),
    (r"\bótkezdi\b", "ótkerdi"),
    (r"\bótkezildi\b", "ótkerildi"),
    (r"\bótkeziledi\b", "ótkeriledi"),
    (r"\bótkezgen\b", "ótkergen"),
    (r"\bótkezil([a-zıóúáǵń]+)\b", r"ótkeril\1"),
    (r"\berkin(lig)?(in)?en ayırıw\b", "azatlıǵınan ayırıw"),
    (r"\btúngish márte\b", "dáslepki márte"),
    (r"\borın aldı\b", "júz berdi"),
    (r"\bjoba([a-zıóúáǵń]*)\b", r"joybar\1"),
    (r"\bbaǵıt([a-zıóúáǵń]*)\b", r"baǵdar\1"),
    (r"\bmúmkindik([a-zıóúáǵń]*)\b", r"múmkinshilik\1"),
    (r"\bjıynalıs([a-zıóúáǵń]*)\b", r"májilis\1"),
    (r"\bquwattı\b", "quwatlı"),
    (r"\bqáwipti\b", "qáwipli"),
    (r"\biskerlik([a-zıóúáǵń]*)\b", r"jumıs\1"),
    (r"(\bhawa rayına)\s+qarap\b", r"\1 qaray"),

    # 2. Uzbek false friends & leakages
    (r"\btanaffus([a-zıóúáǵń]*)\b", r"tánepis\1"),
    (r"\bsaroy([a-zıóúáǵń]*)\b", r"saray\1"),
    (r"\bbezorilik([a-zıóúáǵń]*)\b", r"buzaqılıq\1"),
    (r"\bbizarılıq([a-zıóúáǵń]*)\b", r"buzaqılıq\1"),
    (r"\bkambag['‘`]?al([a-zıóúáǵń]*)\b", r"kámbaǵal\1"),
    (r"\btezyurar\b", "tez júrer"),
    (r"\bjonivor([a-zıóúáǵń]*)\b", r"janzat\1"),
    (r"\bjanıwar([a-zıóúáǵń]*)\b", r"janzat\1"),
    (r"\btunda\b", "túnde"),
    (r"\bkunda\b", "kúnde"),
    (r"\bturar[- ]joy([a-zıóúáǵń]*)\b", r"turaq jay\1"),
    (r"\bhakamlar([a-zıóúáǵń]*)\b", r"tóreshiler\1"),
    (r"\bhakamlik([a-zıóúáǵń]*)\b", r"tóreshilik\1"),
    (r"\bhakam([a-zıóúáǵń]*)\b", r"tóreshi\1"),
    (r"\bnazariy([a-zıóúáǵń]*)\b", r"teoriyalıq\1"),
    (r"\bbajarmasa\b", "orınlamasa"),
    (r"\bbajarsa\b", "orınlasa"),
    (r"\bbajarildi\b", "orınlandı"),
    (r"\bbajaradi\b", "orınlaydı"),
    (r"\bdo['‘`]?kon([a-zıóúáǵń]*)\b", r"dúkan\1"),
    (r"\bqoida([a-zıóúáǵń]*)\b", r"qaǵıyda\1"),
    (r"\b(fóvquládda|favqulodda|favqulotda)\b", "ayrıqsha"),
    (r"\bm[úu]taxassis([a-zıóúáǵń]*)\b", r"qánige\1"),
    (r"\buchun\b", "ushın"),
    (r"\bchunki\b", "sebebi"),
    (r"\bbilan\b", "menen"),
    (r"\bqarshi\b", "qarsı"),
    (r"\byakunlandi\b", "juwmaqlandı"),
    (r"\btasdiqlandi\b", "tastıyıqlandı"),
    (r"\bshubhasiz\b", "gúmansız"),
    (r"\bbalki\b", "bálkim"),
    (r"\bxususan\b", "ásirese"),
    (r"\bshuningdek\b", "sonıń menen birge"),
    (r"\bnatijada\b", "nátiyjede"),
    (r"\bsababli\b", "sebepli"),
    (r"\bmuhim\b", "áhmiyetli"),
    (r"\btashkilot([a-zıóúáǵń]*)\b", r"shólkem\1"),
    (r"\bkorxona([a-zıóúáǵń]*)\b", r"kárxana\1"),
    (r"\bishlab chiqar([a-zıóúáǵń]+)\b", r"islep shıǵar\1"),
    (r"\bhamkorlik([a-zıóúáǵń]*)\b", r"birge islesiw\1"),
    (r"\bxizmat([a-zıóúáǵń]*)\b", r"xızmet\1"),
    (r"\brahbar([a-zıóúáǵń]*)\b", r"basshı\1"),
    (r"\bloyiha([a-zıóúáǵń]*)\b", r"joybar\1"),
    (r"\byo['‘`]?nalish([a-zıóúáǵń]*)\b", r"baǵdar\1"),
    (r"\bimkoniyat([a-zıóúáǵń]*)\b", r"múmkinshilik\1"),
    (r"\byig['‘`]?ilish([a-zıóúáǵń]*)\b", r"májilis\1"),

    # 3. Orthographic standardizations (2016 Karakalpak Latin)
    (r"\bUzgidromet\b", "Ózgidromet"),
    (r"\bSavitskiy\b", "Savickiy"),
    (r"\bYunçjou\b", "Yunchjou"),
    (r"\bmínnetleme([a-zıóúáǵń]*)\b", r"minnetleme\1"),
    (r"\btıs (pastası|shetkası|pastasi|shetkasi)\b", r"tis \1"),
    (r"\bAlat (rayonı|rayonında|rayonına)\b", r"Álot \1"),
    (r"\buzunlıq([a-zıóúáǵń]*)\b", r"uzınlıq\1"),
    (r"\bjaraqat([a-zıóúáǵń]*)\b", r"jarahat\1"),
    (r"\bseksewil([a-zıóúáǵń]*)\b", r"saqsewil\1"),
    (r"\bpuqara([a-zıóúáǵń]*)\b", r"puxara\1"),
    (r"\bjáriyalandı\b", "jariylandı"),
    (r"\bshıyrinlik([a-zıóúáǵń]*)\b", r"shiyrinlik\1"),
    (r"\bpútinley\b", "bútinley"),

    # 4. Morphophonemic predicatives (1st Person after front/back vowels and consonants)
    (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[eióúá][ptkqsxf])pin\b", r"\1pen"),
    (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[aıou][ptkqsxf])pin\b", r"\1pan"),
    (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[eióúá])mın\b", r"\1men"),
    (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[aıou])min\b", r"\1man"),
    (r"\bintellektp[ıi]n\b", "intellektpen"),
    (r"\bmashinapın\b", "mashinaman"),
    (r"\bprogrammistp[ıi]n\b", "programmistpen"),
    (r"\bstudentp[ıi]n\b", "studentpen"),
]


def fix_common_grammatical_slips(text: str) -> str:
    """
    Rule-based post-processor to correct common LLM morphophonemic slips,
    Uzbek/Kazakh intrusive borrowings, and 2016 Latin orthographic slips.
    """
    if not text:
        return text

    result = text
    for pattern, repl in COMMON_SLIPS_PATTERNS:
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
