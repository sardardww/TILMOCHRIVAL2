"""
Karakalpak Theoretical Grammar Engine
Based on the academic textbook:
'QARAQALPAQ TILINIŃ TEORIYALÍQ GRAMMATIKASÍ'
Authors: M. Qudaybergenov, A. Qazaqbaeva, A. Kurtchaev (Nókis, 2017)
"""

# Vowel classifications according to Karakalpak Phonology
BACK_VOWELS = set("aıouAIOUá") # Juwan dawıslılar (a, ı, o, u)
FRONT_VOWELS = set("eióúeiÓÚEİ") # Jińishke dawıslılar (e, i, ó, ú, á)

# Consonant classifications
VOICELESS_CONSONANTS = set("ptkqsşshchxíPTKQSŞSHCHX") # Qatań dawıssızlar (p, t, k, q, s, sh, ch, x, f)
VOICED_CONSONANTS = set("bdgǵvzjBDGǴVZJ")            # Uyań dawıssızlar (b, d, g, ǵ, v, z, j)
SONORANT_CONSONANTS = set("lmnńrwylmnŃRWY")          # Únli dawıssızlar (m, n, ń, l, r, w, y)

KARAKALPAK_ACADEMIC_GRAMMAR_PROMPT = """
ACADEMIC KARAKALPAK GRAMMAR GUIDE (Source: Qaraqalpaq tiliniń teoriyalıq grammatikası, Nókis 2017):

1. VOWEL HARMONY (Singarmonizm nızamı):
   - Juwan (Back vowels: a, ı, o, u): Suffixes MUST use back vowels (-lar, -ǵa, -da, -dan, -man, -sań, -qan).
   - Jińishke (Front vowels: e, i, ó, ú, á): Suffixes MUST use front vowels (-ler, -ge, -de, -den, -men, -seń, -gen).
   - WARNING: Never mix front and back vowels in native suffixes! (e.g. NOT "intellektpin", but "intellektpen" because 'e' is a front vowel!).

2. PREDICATIVE / PERSONAL ENDINGS (Betlik jalǵawları):
   Attached to predicate nouns, adjectives, and verbs:
   * 1st Person Singular (Men):
     - After vowels or sonorants (m, n, ń, l, r, w, y): -man / -men (e.g., studentpın EMES -> studentpen / oqıwshıman, jumısshıman)
     - After voiceless consonants (p, t, k, q, s, sh, x, f): -pan / -pen (e.g., intellekt-pen, jas-pan, qazaq-pan)
     - After voiced consonants (b, d, g, ǵ, z, j): -ban / -ben (e.g., jazıwshı-ban)
   * 1st Person Plural (Biz / Bizler):
     - -mız / -miz (adam-bız, student-piz, oqıwshı-mız)
   * 2nd Person Singular (Sen): -sań / -seń
   * 2nd Person Plural / Polite (Siz / Sizler): -sız / -siz, -sızlar / -sizler
   * 3rd Person (Ol / Olar): Usually zero ending (-) or -dı / -di.

3. NOUN CASE SYSTEM (Seplik jalǵawları):
   * Ataw (Nominative): zero ending (-)
   * Iyelik (Genitive):
     - After vowels & sonorants: -nıń / -niń
     - After voiced consonants: -dıń / -diń
     - After voiceless consonants: -tıń / -tiń
   * Barıs (Dative):
     - After vowels, sonorants, voiced: -ǵa / -ge
     - After voiceless consonants: -qa / -ke
     - 3rd person possessive base: -na / -ne
   * Tabıs (Accusative):
     - After vowels: -nı / -ni
     - After voiced/sonorants: -dı / -di
     - After voiceless: -tı / -ti
     - 3rd person possessive base: -n
   * Orın (Locative):
     - After vowels, voiced, sonorants: -da / -de
     - After voiceless: -ta / -te
     - 3rd person possessive base: -nda / -nde
   * Shıǵıs (Ablative):
     - After vowels, voiced: -dan / -den
     - After voiceless: -tan / -ten
     - After sonorants (m, n, ń): -nan / -nen
     - 3rd person possessive base: -nan / -nen

4. POSSESSIVE ENDINGS (Tartım jalǵawları):
   * 1-bet (my): -ım / -im, -m (plural: -ımız / -imiz, -mız / -miz)
   * 2-bet (your): -ıń / -iń, -ń (plural: -ıńız / -ińiz, -ńız / -ńiz)
   * 3-bet (his/her/its/their): -ı / -i (after consonant), -sı / -si (after vowel)

5. TENSE & ASPECT SYSTEM (Máhál hám Feyil formalıq modelleri):
   * Anıq házirgi máhál (Present Continuous):
     - Analytical model: [Verb stem] + -p / -a / -e + otır / tur / júr / jatır / atır + personal ending.
       Examples: oqıp atır, jazıp atır, úyrenip atır, islep kiyatır.
   * Keler máhál (Future):
     - Categorical future: -jaq / -jek (e.g., barajaqpan, kórsetejek).
     - Intention: -maqshı / -mekshi (e.g., barmaqshıman).
   * Ótken máhál (Past):
     - Definite past: -dı / -di, -tı / -ti (e.g., kórdi, ayttı).
     - Narrative past: -ǵan / -gen, -qan / -ken (e.g., kelgen, jazǵan).
   * Negation (Bolımsız feyil):
     - Verb stem + -ma / -me, -ba / -be, -pa / -pe (e.g., jazba, kelme, aytpa).

6. INTENSIFIED ADJECTIVES (Kelbetliktiń arttırıw dárejesi):
   * Reduplication with 'p' in the first syllable:
     - qara -> qap-qara
     - qızıl -> qıp-qızıl
     - sarı -> sap-sarı
     - úlken -> úp-úlken
     - ashshı -> ap-ashshı
     - tik -> tip-tik
   * Analytical intensifiers: júdá, dım, oǵırı, orasan (e.g., júdá sulıw, dım qara, oǵırı qızıl).

7. COMPOUND WORDS (Qospa sózler):
   * Birikken sózler (Written together): asqazan, tasbaqa, aqquw, kókjótel, qoljazba, kúnshıǵıs, búgin, bıyıl.
   * Jup sózler (Hyphenated): áke-sheshe, ata-ana, awıl-aymaq, dos-dushpan, azlı-kópli, kún-tún.
   * Tákirar sózler (Reduplicated, hyphenated): kóre-kóre, úyme-úy, qora-qora.

8. SYNTAX (Gáp dúzilisi):
   * SOV: Baslawısh (Subject) -> Anıqlawısh/Tolıqlawısh/Pısıqlawısh (Modifiers/Objects) -> Bayanlawısh (Verb at the end).
   * Adjectives before nouns do NOT take plural suffixes: e.g., "biyik tawlar" (CORRECT), NOT "biyikler tawlar" (WRONG).
"""


def fix_common_grammatical_slips(text: str) -> str:
    """
    Rule-based post-processor to correct common LLM morphophonemic slips
    specifically documented in Qudaybergenov's Karakalpak Theoretical Grammar
    and enforce Karakalpak over Kazakh false cognates.
    """
    replacements = [
        # 1. Enforce Karakalpak 'jasama' over Kazakh 'jasandı'
        (r"\bjasandı\b", "jasama"),
        (r"\bjasandıq\b", "jasamalıq"),
        (r"\bжасанды\b", "жасама"),
        
        # 2. 1st Person predicative after front vowels (intellektpin -> intellektpen)
        (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[eióúá][ptkqsxf])pin\b", r"\1pen"),
        (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[aıou][ptkqsxf])pin\b", r"\1pan"),
        # 3. 1st person after sonorants/vowels
        (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[eióúá])mın\b", r"\1men"),
        (r"\b([A-Za-zÁáÓóÚúǴǵŃńıI]*[aıou])min\b", r"\1man"),
        # 4. Common Russian-Karakalpak loanword predicatives
        ("intellektpin", "intellektpen"),
        ("intellektpın", "intellektpen"),
        ("mashinapın", "mashinaman"),
        ("programmistpin", "programmistpen"),
        ("studentpın", "studentpen"),
        ("studentpin", "studentpen"),
    ]
    
    import re
    result = text
    for pattern, repl in replacements:
        result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
    return result
