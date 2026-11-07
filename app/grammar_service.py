"""
Karakalpak Theoretical Grammar & Anti-Uzbekism Engine
Based on the academic textbook:
'QARAQALPAQ TILINIŃ TEORIYALÍQ GRAMMATIKASÍ'
Authors: M. Qudaybergenov, A. Qazaqbaeva, A. Kurtchaev (Nókis, 2017)
Enforcing strict official 34-letter 2016 Karakalpak Latin Orthography.
"""

import re

BACK_VOWELS = set("aıouAIOUá")
FRONT_VOWELS = set("eióúeiÓÚEİ")
VOICELESS_CONSONANTS = set("ptkqsşshchxíPTKQSŞSHCHX")
VOICED_CONSONANTS = set("bdgǵvzjBDGǴVZJ")
SONORANT_CONSONANTS = set("lmnńrwylmnŃRWY")

KARAKALPAK_ACADEMIC_GRAMMAR_PROMPT = """
ACADEMIC KARAKALPAK GRAMMAR & VOCABULARY STANDARDS (Nókis 2017):

1. STRICT VOWEL HARMONY & SUFFIX RULES:
   - Juwan (Back vowels: a, ı, o, u): -lar, -ǵa, -da, -dan, -man, -sań, -qan
   - Jińishke (Front vowels: e, i, ó, ú, á): -ler, -ge, -de, -den, -men, -seń, -gen
   - ALWAYS attach -pen after voiceless front consonants (e.g. "intellektpen", NOT "intellektpin"!).

2. STRICT VOCABULARY ENFORCEMENT — NO UZBEKISMS OR RUSSIAN SLIPS ALLOWED:
   * "tibbiyot" / "tibbiyotda" -> NEVER! Use "medicina", "medicinada" or "densawlıqtı saqlawda".
   * "tibbiy" -> NEVER! Use "medicinalıq".
   * "natija" -> NEVER! Use "nátiyje".
   * "muhim" -> NEVER! Use "áhmiyetli".
   * "hosil" -> NEVER! Use "ónim".
   * "yutug'i" -> NEVER! Use "tabısı".
   * "loyiha" / "loyixa" -> NEVER! Use "joybar".
   * "tadbir" -> NEVER! Use "ilaj".
   * "tadbirkor" -> NEVER! Use "isbilermen".
   * "iqtisodiyot" -> NEVER! Use "ekonomika".
   * "iqtisodiy" -> NEVER! Use "ekonomikalıq".
   * "fuqaro" / "puxara" -> NEVER! Use "puqara".
   * "tunda" -> NEVER! Use "túnde".
   * "ertaga" -> NEVER! Use "erteń".
   * "kecha" -> NEVER! Use "keshe".
   * "yordam" -> NEVER! Use "járdem".
   * "shuningdek" -> NEVER! Use "sonday-aq".
   * "masala" -> NEVER! Use "másele".
   * "qaror" -> NEVER! Use "qarar".
   * "hukumat" -> NEVER! Use "húkimet".
   * "shifokor" / "do'xtir" -> NEVER! Use "shıpaker".
   * "kasalxona" -> NEVER! Use "emlewxana".
   * "dorixona" -> NEVER! Use "dárixana".
   * "qurilish" -> NEVER! Use "qurılıs".
   * "ta'lim" -> NEVER! Use "bilimlendiriw".
   * "ish haqi" -> NEVER! Use "aylıq is haqı" or "miynet haqı".
   * "yo'l" -> NEVER! Use "jol".
   * "yo'nalish" -> NEVER! Use "jónelis".
   * "yo'lovchi" -> NEVER! Use "jolawshı".
   * "jarima" -> NEVER! Use "járiyma".
   * "boshqarma" -> NEVER! Use "basqarma".
   * "tashkilot" -> NEVER! Use "shólkem".
   * "korxona" -> NEVER! Use "kárxana".
   * "kelishuv" -> NEVER! Use "kelisim".
   * "shartnoma" -> NEVER! Use "shártnama".
   * "hamkorlik" -> NEVER! Use "birge islesiw" or "sheriklik".
   * "xavfsizlik" -> NEVER! Use "qáwipsizlik".
   * "harbiy" -> NEVER! Use "áskeriy".
   * "xodim" -> NEVER! Use "xızmetker".
   * "rahbar" -> NEVER! Use "basshı".
   * "o'rinbosar" -> NEVER! Use "orınbasar".
   * "vakil" -> NEVER! Use "wákil".
   * "aytishicha" -> NEVER! Use "aytıwınsha".
   * "so'zlariga ko'ra" -> NEVER! Use "sózlerine qaraǵanda".
   * "ma'lumot" -> NEVER! Use "maǵlıwmat".
   * "hisobot" -> NEVER! Use "esabat".
   * "ishlab chiqarish" -> NEVER! Use "islep shıǵarıw".
   * "qishloq xo'jaligi" -> NEVER! Use "awıl xojalıǵı".
   * "dehqon" -> NEVER! Use "dıyqan".
   * "ob-havo" -> NEVER! Use "hawa rayı".
   * "favqulodda vaziyat" -> NEVER! Use "ayrıqsha jaǵday".
   * "qutqaruvchi" -> NEVER! Use "qutqarıwshı".
   * "yong'in" -> NEVER! Use "órt".
   * "halokat" -> NEVER! Use "apatshılıq".
   * "jabrlanuvchi" -> NEVER! Use "jábir kórgen".
   * "jarohat" -> NEVER! Use "jaráhat".
   * "vafot etdi" -> NEVER! Use "qaytıs boldı".
   * "musobaqa" -> NEVER! Use "jarıs".
   * "g'olib" -> NEVER! Use "jeńimpaz".
   * "jasandi" -> NEVER! Use "jasama".

3. 2016 LATIN ORTHOGRAPHY (Á á, Ó ó, Ú ú, Ǵ ǵ, Ń ń, Í ı, W w, Sh sh, Ch ch):
   - Double consonants: "kesellik" (NOT "keselik"), "qánigelik", "jetiskenlik".
   - Use "w" for /w/ and diphthongs: "suw", "taw", "barıw", "keliw", "jazıw".
"""

# Exhaustive dictionary of regular expression replacements for post-processing
UZBEK_AND_GRAMMAR_FIXES = [
    # 1. High frequency Uzbekism replacements
    (r"\btibbiyot(ta|da)\b", "medicinada"),
    (r"\btibbiyot(qa|ga)\b", "medicinaǵa"),
    (r"\btibbiyot(ning|niń)\b", "medicinadan"),
    (r"\btibbiyot\b", "medicina"),
    (r"\btibbiy\b", "medicinalıq"),
    (r"\bkeselik(ler|ge|tiń|te|ke|ten|lerge|lerdi)?\b", lambda m: "kesellik" + (m.group(1) or "")),
    (r"\bjasand[ıi]\b", "jasama"),
    (r"\bjasand[ıi]q\b", "jasamalıq"),
    (r"\bжасанды\b", "жасама"),
    (r"\bnatija(da|si|lar|si|sinde)?\b", lambda m: "nátiyje" + (m.group(1) or "")),
    (r"\bmuhim\b", "áhmiyetli"),
    (r"\bhosil\b", "ónim"),
    (r"\byutug['’‘`]?i\b", "tabısı"),
    (r"\byutuq\b", "tabıs"),
    (r"\bloyih?a(si|lar|da|ǵa)?\b", lambda m: "joybar" + (m.group(1) or "")),
    (r"\btadbir(lar|da|ge)?\b", lambda m: "ilaj" + (m.group(1) or "")),
    (r"\btadbirkor(lar)?\b", lambda m: "isbilermen" + (m.group(1) or "")),
    (r"\biqtisodiyot\b", "ekonomika"),
    (r"\biqtisodiy\b", "ekonomikalıq"),
    (r"\b(fuqaro|puxara)(lar)?\b", lambda m: "puqara" + (m.group(2) or "")),
    (r"\btunda\b", "túnde"),
    (r"\bertaga\b", "erteń"),
    (r"\bkecha\b", "keshe"),
    (r"\byordam\b", "járdem"),
    (r"\bshuningdek\b", "sonday-aq"),
    (r"\bmasala(lar|da|ǵa)?\b", lambda m: "másele" + (m.group(1) or "")),
    (r"\bqaror\b", "qarar"),
    (r"\bhukumat\b", "húkimet"),
    (r"\bshifokor(lar)?\b", lambda m: "shıpaker" + (m.group(1) or "")),
    (r"\bkasalxona\b", "emlewxana"),
    (r"\bdorixona\b", "dárixana"),
    (r"\bqurilish\b", "qurılıs"),
    (r"\bta['’‘`]?lim\b", "bilimlendiriw"),
    (r"\bo['’‘`]?qituvchi(lar)?\b", lambda m: "oqıtıwshı" + (m.group(1) or "")),
    (r"\btalaba(lar)?\b", lambda m: "student" + (m.group(1) or "")),
    (r"\bmaktab(lar)?\b", lambda m: "mektep" + (m.group(1) or "")),
    (r"\bbog['’‘`]?cha\b", "balalar baqshası"),
    (r"\byo['’‘`]?l(lar)?\b", lambda m: "jol" + (m.group(1) or "")),
    (r"\byo['’‘`]?nalish\b", "jónelis"),
    (r"\byo['’‘`]?lovchi(lar)?\b", lambda m: "jolawshı" + (m.group(1) or "")),
    (r"\bjarima\b", "járiyma"),
    (r"\bboshqarma\b", "basqarma"),
    (r"\btashkilot(lar)?\b", lambda m: "shólkem" + (m.group(1) or "")),
    (r"\bkorxona(lar)?\b", lambda m: "kárxana" + (m.group(1) or "")),
    (r"\bkelishuv\b", "kelisim"),
    (r"\bshartnoma\b", "shártnama"),
    (r"\bhamkorlik\b", "birge islesiw"),
    (r"\bxavfsizlik\b", "qáwipsizlik"),
    (r"\bharbiy\b", "áskeriy"),
    (r"\bxodim(lar)?\b", lambda m: "xızmetker" + (m.group(1) or "")),
    (r"\brahbar(lar)?\b", lambda m: "basshı" + (m.group(1) or "")),
    (r"\bo['’‘`]?rinbosar(lar)?\b", lambda m: "orınbasar" + (m.group(1) or "")),
    (r"\bvakil(lar)?\b", lambda m: "wákil" + (m.group(1) or "")),
    (r"\baytishicha\b", "aytıwınsha"),
    (r"\bso['’‘`]?zlariga ko['’‘`]?ra\b", "sózlerine qaraǵanda"),
    (r"\bma['’‘`]?lumot(lar)?\b", lambda m: "maǵlıwmat" + (m.group(1) or "")),
    (r"\bhisobot(lar)?\b", lambda m: "esabat" + (m.group(1) or "")),
    (r"\bishlab chiqarish\b", "islep shıǵarıw"),
    (r"\bqishloq xo['’‘`]?jaligi\b", "awıl xojalıǵı"),
    (r"\bdehqon(lar)?\b", lambda m: "dıyqan" + (m.group(1) or "")),
    (r"\bob-havo\b", "hawa rayı"),
    (r"\bfavqulodda vaziyat(lar)?\b", lambda m: "ayrıqsha jaǵday" + (m.group(1) or "")),
    (r"\bqutqaruvchi(lar)?\b", lambda m: "qutqarıwshı" + (m.group(1) or "")),
    (r"\byong['’‘`]?in\b", "órt"),
    (r"\bhalokat\b", "apatshılıq"),
    (r"\bjabrlanuvchi(lar)?\b", lambda m: "jábir kórgen" + (m.group(1) or "")),
    (r"\bjarohat(lar)?\b", lambda m: "jaráhat" + (m.group(1) or "")),
    (r"\bvafot etdi\b", "qaytıs boldı"),
    (r"\bmusobaqa(lar)?\b", lambda m: "jarıs" + (m.group(1) or "")),
    (r"\bg['’‘`]?olib(lar)?\b", lambda m: "jeńimpaz" + (m.group(1) or "")),
    
    # Verb stems and verb suffixes
    (r"\bbajar(sa|di|iladi|ilmoqda|ayotgan)\b", "orınla\1"),
    (r"\bqollanǵan\b", "paydalanǵan"),
    (r"\bqollanıp\b", "paydalanıp"),
    (r"\bkómeklesetuǵının\b", "járdem beretuǵının"),
    (r"\bsherik-tiykarlawshısı\b", "tiykarshılarınıń biri"),
    (r"\burlaw\b", "urlıq qılıw"),

    # Predicative suffixes: intellektpin -> intellektpen
    (r"intellektpin", "intellektpen"),
    (r"intellektpın", "intellektpen"),
    (r"mashinapın", "mashinaman"),
    (r"programmistpin", "programmistpen"),
    (r"studentpın", "studentpen"),
    (r"studentpin", "studentpen"),
]

def fix_common_grammatical_slips(text: str) -> str:
    """
    Applies grammatical, orthographical, and anti-Uzbekism fixes to translated Karakalpak text.
    """
    if not text:
        return text

    result = text
    for item in UZBEK_AND_GRAMMAR_FIXES:
        pattern, repl = item
        if callable(repl):
            result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
        else:
            result = re.sub(pattern, repl, result, flags=re.IGNORECASE)

    # 2016 Latin orthography character standardizations
    # Apostrophe normalization to proper acute characters
    result = re.sub(r"a['’‘`]", "á", result)
    result = re.sub(r"A['’‘`]", "Á", result)
    result = re.sub(r"o['’‘`]", "ó", result)
    result = re.sub(r"O['’‘`]", "Ó", result)
    result = re.sub(r"u['’‘`]", "ú", result)
    result = re.sub(r"U['’‘`]", "Ú", result)
    result = re.sub(r"g['’‘`]", "ǵ", result)
    result = re.sub(r"G['’‘`]", "Ǵ", result)
    result = re.sub(r"n['’‘`]", "ń", result)
    result = re.sub(r"N['’‘`]", "Ń", result)
    result = re.sub(r"i['’‘`]", "ı", result)
    result = re.sub(r"I['’‘`]", "Í", result)

    return result
