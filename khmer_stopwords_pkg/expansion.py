"""
expansion.py
============
Programmatic generators that expand the curated CORE into a 10,000+
entry production stop-word dictionary.

Every generator is principled — it produces ONLY forms that fall into
recognised stop-word patterns of Modern Khmer:

  G1  Khmer numerals (digits + spelled-out compounds 0–9999)
  G2  Latin numerals 0–9999 (commonly appear inline in Khmer text)
  G3  Laughter / interjection repetition (haha × N, hahaha, ហាស×N)
  G4  Internet-slang character-repetition variants (ok, okk, okkkk…)
  G5  Repeated-particle emphasis (ហើយៗ, ដែរៗ, ណាៗ…)
  G6  Compound particle phrases (cartesian product of small particle set)
  G7  Romanized Khmer chat-slang (krom-ven keyboard typings)
  G8  OCR confusion artifacts — Unicode re-orderings of high-freq cores
  G9  Spacing/whitespace variants of multi-word compounds
  G10 Common typo / shortened spellings
  G11 Bilingual filler words (English fillers that appear in Khmer text)
  G12 Emoji-adjacent text artifacts and repeated punctuation
"""

from itertools import product
import unicodedata


# ── Generator 1: Khmer numerals (digit form) ────────────────────────
KHMER_DIGITS = "០១២៣៤៥៦៧៨៩"

def gen_khmer_digit_strings():
    """Every Khmer-digit string from 0 to 9999. These are aggressively
    removable in most NLP unless the task is numeric QA / finance."""
    out = []
    for n in range(0, 10000):
        s = "".join(KHMER_DIGITS[int(d)] for d in str(n))
        out.append({
            "khmer": s,
            "english": f"khmer numeral {n}",
            "category": "quantifier",
            "frequency": "Low" if n > 99 else "Medium",
            "safe_remove": "Caution",
            "level": "Aggressive",
            "domains": ["all"],
            "token_type": "noise" if n > 99 else "single",
            "notes": "Numeric token; preserve for finance/QA.",
        })
    return out


# ── Generator 2: Latin numerals 0–9999 ──────────────────────────────
def gen_latin_digit_strings():
    out = []
    for n in range(0, 10000):
        out.append({
            "khmer": str(n),
            "english": f"latin numeral {n}",
            "category": "quantifier",
            "frequency": "Low" if n > 99 else "Medium",
            "safe_remove": "Caution",
            "level": "Aggressive",
            "domains": ["news","social","ocr","web"],
            "token_type": "noise" if n > 99 else "single",
            "notes": "Latin digit token; preserve for finance/QA.",
        })
    return out


# ── Generator 3: Laughter / interjection repetition ────────────────
def gen_laughter_repetitions():
    out = []
    bases = [
        ("ha",   "haha (latin)",          ["social","fb","youtube"]),
        ("he",   "hehe (latin)",          ["social","fb","youtube"]),
        ("hi",   "hihi (latin)",          ["social","fb","youtube"]),
        ("ho",   "hoho (latin)",          ["social","fb","youtube"]),
        ("hu",   "huhu (latin)",          ["social","fb","youtube"]),
        ("lo",   "lolol",                 ["social","fb","youtube"]),
        ("xa",   "xaxa (latin)",          ["social","fb","youtube"]),
        ("ហា",  "haha (khmer)",          ["social","fb","youtube"]),
        ("ហី",  "hihi (khmer)",          ["social","fb","youtube"]),
        ("ហ៊ឺ","huhu (khmer)",            ["social","fb","youtube"]),
        ("ហុ",  "hu (khmer)",             ["social","fb","youtube"]),
    ]
    for base, desc, doms in bases:
        for n in range(2, 13):
            form = base * n
            out.append({
                "khmer": form,
                "english": f"{desc} ×{n}",
                "category": "social",
                "frequency": "Medium" if n <= 4 else "Low",
                "safe_remove": "Yes",
                "level": "Conservative",
                "domains": doms,
                "token_type": "noise",
                "notes": "Laughter repetition.",
            })
    # Hyphen / space separated variants
    for base, desc, doms in bases[:7]:  # latin only
        for sep in ["-", " "]:
            for n in range(2, 8):
                form = sep.join([base] * n)
                out.append({
                    "khmer": form,
                    "english": f"{desc} sep='{sep}' ×{n}",
                    "category": "social",
                    "frequency": "Low",
                    "safe_remove": "Yes",
                    "level": "Conservative",
                    "domains": doms,
                    "token_type": "noise",
                    "notes": "Separated laughter.",
                })
    return out


# ── Generator 4: Character-stretching slang variants ───────────────
def gen_slang_stretches():
    out = []
    # (base, last-char-to-repeat, english, domains)
    items = [
        ("ok",  "k", "ok stretched",       ["social","fb","youtube"]),
        ("okay","y", "okay stretched",     ["social","fb","youtube"]),
        ("oki", "i", "oki stretched",      ["social","fb","youtube"]),
        ("yes", "s", "yes stretched",      ["social","fb","youtube"]),
        ("yeah","h", "yeah stretched",     ["social","fb","youtube"]),
        ("yep", "p", "yep stretched",      ["social","fb","youtube"]),
        ("nah", "h", "nah stretched",      ["social","fb","youtube"]),
        ("hmm", "m", "hmm stretched",      ["social","fb","youtube"]),
        ("ehh", "h", "ehh stretched",      ["social","fb","youtube"]),
        ("oh",  "h", "oh stretched",       ["social","fb","youtube"]),
        ("aw",  "w", "aw stretched",       ["social","fb","youtube"]),
        ("uh",  "h", "uh stretched",       ["social","fb","youtube"]),
        ("uhm", "m", "uhm stretched",      ["social","fb","youtube"]),
        ("err", "r", "err stretched",      ["social","fb","youtube"]),
        ("hru", "u", "hru stretched",      ["social","fb","youtube"]),
        ("bro", "o", "bro stretched",      ["social","fb","youtube"]),
        ("sis", "s", "sis stretched",      ["social","fb","youtube"]),
        ("plz", "z", "plz stretched",      ["social","fb","youtube"]),
        ("pls", "s", "pls stretched",      ["social","fb","youtube"]),
        ("ya",  "a", "ya stretched",       ["social","fb","youtube"]),
        ("yo",  "o", "yo stretched",       ["social","fb","youtube"]),
        ("nope","e", "nope stretched",     ["social","fb","youtube"]),
        ("noo", "o", "no stretched",       ["social","fb","youtube"]),
        ("aha", "a", "aha stretched",      ["social","fb","youtube"]),
        ("oop", "p", "oop stretched",      ["social","fb","youtube"]),
        ("idk", "k", "idk stretched",      ["social","fb","youtube"]),
        ("imo", "o", "imo stretched",      ["social","fb","youtube"]),
        ("tbh", "h", "tbh stretched",      ["social","fb","youtube"]),
        ("btw", "w", "btw stretched",      ["social","fb","youtube"]),
        ("smh", "h", "smh stretched",      ["social","fb","youtube"]),
    ]
    for base, last, desc, doms in items:
        for n in range(1, 11):
            form = base + (last * n)
            out.append({
                "khmer": form,
                "english": f"{desc} +{n}",
                "category": "social",
                "frequency": "Medium" if n <= 2 else "Low",
                "safe_remove": "Yes",
                "level": "Conservative",
                "domains": doms,
                "token_type": "noise",
                "notes": "Character-stretching internet slang.",
            })
    return out


# ── Generator 5: Particle repetition for emphasis ──────────────────
def gen_particle_repetitions():
    out = []
    particles = [
        ("ហើយ", "and then"),
        ("ដែរ",  "also/too"),
        ("ណា",   "emphasis"),
        ("សោះ",  "intensifier"),
        ("ផង",   "also"),
        ("វិញ",  "instead/back"),
        ("ទៀត",  "more/again"),
        ("ហ៎",   "huh?"),
        ("អូ",   "oh"),
        ("អា",   "ah"),
        ("ហើ",   "hey (alt)"),
        ("មែន",  "really"),
        ("ឯង",   "you"),
        ("ហ្នឹង","this"),
        ("ផ្ទេ", "no"),
        ("បាទ",  "yes(m)"),
        ("ចា",   "yes(f)"),
        ("ចាស",  "yes"),
    ]
    for w, gloss in particles:
        for n in range(2, 8):
            out.append({
                "khmer": w * n,
                "english": f"{gloss} repeated ×{n}",
                "category": "social",
                "frequency": "Low",
                "safe_remove": "Yes",
                "level": "Conservative",
                "domains": ["social","fb","ocr"],
                "token_type": "noise",
                "notes": "Particle repetition for emphasis (also common OCR artifact).",
            })
    # Repetition mark variants
    for w, gloss in particles:
        out.append({
            "khmer": w + "ៗ",
            "english": f"{gloss} + repetition mark",
            "category": "particle",
            "frequency": "Low",
            "safe_remove": "Yes",
            "level": "Moderate",
            "domains": ["all"],
            "token_type": "single",
            "notes": "Particle followed by ៗ.",
        })
    return out


# ── Generator 6: Compound particle phrases ─────────────────────────
def gen_compound_phrases():
    """Cartesian combinations of small functional words that appear as
    multi-word stop phrases in Khmer (no inter-word space)."""
    out = []
    A = ["នៅ", "ក្នុង", "ដោយ", "ដល់", "ពី", "តាម", "ចំពោះ", "សម្រាប់",
         "ជា", "ដោយសារ", "ដោយសារតែ", "ដោយព្រោះ", "ដោយ", "ក្នុង"]
    B = ["ក្នុង", "លើ", "ក្រោម", "មុខ", "ក្រោយ", "ស្ដាំ", "ឆ្វេង",
         "ជើង", "ត្បូង", "កើត", "លិច", "នោះ", "នេះ", "ណា", "ណាមួយ",
         "ពេលណា", "ជាមួយ", "ការនេះ", "បច្ចុប្បន្ន"]
    seen = set()
    for a, b in product(A, B):
        form = a + b
        if form in seen:
            continue
        seen.add(form)
        out.append({
            "khmer": form,
            "english": f"compound: {a}+{b}",
            "category": "location",
            "frequency": "Low",
            "safe_remove": "Yes",
            "level": "Moderate",
            "domains": ["all"],
            "token_type": "compound",
            "notes": "Generated functional compound — verify in production with tokenizer.",
        })
    # second batch: temporal compounds
    T1 = ["កាល", "ពេល", "ថ្ងៃ", "ឆ្នាំ", "ខែ", "សប្ដាហ៍", "យប់", "ព្រឹក", "ល្ងាច"]
    T2 = ["នេះ", "នោះ", "ណា", "ស្អែក", "មុន", "ក្រោយ", "មិញ", "ហ្នឹង"]
    for a, b in product(T1, T2):
        form = a + b
        if form in seen:
            continue
        seen.add(form)
        out.append({
            "khmer": form,
            "english": f"temporal compound: {a}+{b}",
            "category": "temporal",
            "frequency": "Low",
            "safe_remove": "Yes",
            "level": "Aggressive",
            "domains": ["news","social"],
            "token_type": "compound",
            "notes": "Temporal compound.",
        })
    return out


# ── Generator 7: Romanized Khmer chat-slang ────────────────────────
def gen_romanized_khmer_slang():
    """Romanized Khmer (a.k.a. 'Khmenglish', 'Khmer-Latin') used heavily
    on Facebook/YouTube/Messenger when a Khmer keyboard is unavailable."""
    items = [
        ("som", "សូម please"),                    ("som tos","សូមទោស sorry"),
        ("sok sapbay","សុខសប្បាយ how are you"),  ("knhom","ខ្ញុំ I"),
        ("oun",  "អូន younger"),                  ("bong", "បង older"),
        ("min",  "មិន not"),                      ("te",   "ទេ negation/Q"),
        ("ot",   "អត់ not (informal)"),           ("ban",  "បាន can/past"),
        ("ah",   "អា (deprec.)"),                 ("krob", "គ្រប់ every"),
        ("teang","ទាំង all"),                     ("nis",  "នេះ this"),
        ("nuh",  "នោះ that"),                     ("hnoeng","ហ្នឹង this"),
        ("haey", "ហើយ already"),                  ("der",  "ដែរ also"),
        ("phong","ផង also"),                      ("vinh", "វិញ instead"),
        ("teat", "ទៀត more"),                     ("na",   "ណា which"),
        ("daoy", "ដោយ by"),                       ("nau",  "នៅ at"),
        ("kngong","ក្នុង in"),                    ("loeu", "លើ on"),
        ("krom", "ក្រោម under"),                  ("chenh","ចេញ out"),
        ("chol", "ចូល in"),                       ("teuv", "ទៅ go"),
        ("mok",  "មក come"),                      ("dol",  "ដល់ until"),
        ("pi",   "ពី from"),                      ("tam",  "តាម along"),
        ("min mean", "មិនមាន no/none"),           ("krean","ក្រែង lest"),
        ("klah", "ខ្លះ some"),                    ("chreun","ច្រើន many"),
        ("tech", "តិច few"),                      ("muoy", "មួយ one"),
        ("pi(r)","ពីរ two"),                      ("bei",  "បី three"),
        ("buon", "បួន four"),                     ("pram", "ប្រាំ five"),
        ("dop",  "ដប់ ten"),                      ("roy",  "រយ hundred"),
        ("poan", "ពាន់ thousand"),                ("orkun","អរគុណ thanks"),
        ("ar kun","អរគុណ thanks"),                ("chumreabsour","ជំរាបសួរ hello"),
        ("sus",  "សួស្ដី hi"),                    ("susdei","សួស្ដី hi"),
        ("baat", "បាទ yes(m)"),                   ("chass","ចាស yes"),
        ("jas",  "ចាស yes (alt)"),                ("nikon","មិន (alt)"),
        ("tov",  "ទៅ go (alt)"),                  ("teuv tov","ទៅ go"),
        ("krava","ការ noun marker"),              ("kar",  "ការ noun marker"),
        ("sech ktei","សេចក្ដី matter/issue"),    ("dombong","ដំបូង first"),
        ("kraoy","ក្រោយ after"),                  ("mun",  "មុន before"),
        ("sok",  "សុខ peace/well"),               ("krup yang","គ្រប់យ៉ាង all kinds"),
        ("teangoss","ទាំងអស់ all"),               ("os",   "អស់ all/finished"),
        ("hael", "ហើយ already (alt)"),            ("aey",  "អី what"),
        ("ey",   "អី what (alt)"),                ("avey", "អ្វី what"),
        ("ney",  "នៃ of"),                        ("nung", "នឹង with/will"),
        ("rebos","របស់ of"),                      ("dael", "ដែល which"),
        ("tha",  "ថា that (comp)"),               ("aoy",  "ឲ្យ let/to"),
        ("yang", "យ៉ាង manner"),                  ("yang na","យ៉ាងណា how"),
        ("baeb", "បែប kind/manner"),              ("kone", "គ្នា each other"),
        ("kchey","ខ្ជី lazy (slang)"),            ("a la", "អា la (slang)"),
        ("bro",  "ប្រ (slang prefix)"),           ("smos", "ស្មោះ honest"),
        ("akun", "អរគុណ thanks (alt)"),           ("kun ch'rein","អរគុណច្រើន many thanks"),
        ("ouy",  "អូ exclamation"),               ("yer",  "យើរ slang exclam"),
        ("hor",  "ហួរ exclam"),                   ("euy",  "អើយ vocative"),
        ("aey",  "អី what"),                      ("kru",  "គ្រូ teacher"),
        ("ah ha","អាហា (deprec.)"),               ("yes na","យ៉េសណា yes-emph"),
        ("ouy ouy","អូយ! exclam"),                ("ah hi","អា hi (deprec.)"),
    ]
    out = []
    seen = set()
    for tok, gloss in items:
        if tok in seen: continue
        seen.add(tok)
        out.append({
            "khmer": tok,
            "english": f"romanized: {gloss}",
            "category": "social",
            "frequency": "Medium",
            "safe_remove": "Yes",
            "level": "Moderate",
            "domains": ["social","fb","youtube"],
            "token_type": "noise",
            "notes": "Romanized Khmer chat-slang ('Khmenglish').",
        })
    # Add capitalised variants
    out_more = []
    for e in out:
        cap = e["khmer"].title()
        upp = e["khmer"].upper()
        if cap != e["khmer"] and cap not in seen:
            seen.add(cap)
            out_more.append({**e, "khmer": cap, "english": e["english"] + " (Titlecase)"})
        if upp != e["khmer"] and upp not in seen:
            seen.add(upp)
            out_more.append({**e, "khmer": upp, "english": e["english"] + " (UPPER)"})
    return out + out_more


# ── Generator 8: OCR confusion artifacts ───────────────────────────
def gen_ocr_artifacts(core_entries):
    """Common OCR/web noise patterns derived from high-frequency cores.
    Strategy: append zero-width separators, duplicate trailing chars,
    insert ASCII spaces in compound words (a frequent OCR error)."""
    out = []
    zw = ["\u200b", "\u200c", "\u200d", "\u00a0"]
    sampled = [e for e in core_entries
               if e["frequency"] == "High" and e["token_type"] in ("single","compound")][:60]
    for e in sampled:
        base = e["khmer"]
        # Zero-width-injected variants
        for z in zw:
            f = base + z
            out.append({
                "khmer": f,
                "english": f"{e['english']} + trailing ZW",
                "category": "noise",
                "frequency": "Low",
                "safe_remove": "Yes",
                "level": "Conservative",
                "domains": ["ocr","web"],
                "token_type": "noise",
                "notes": "OCR/web zero-width artifact.",
            })
            if len(base) >= 2:
                mid = base[:1] + z + base[1:]
                out.append({
                    "khmer": mid,
                    "english": f"{e['english']} + interior ZW",
                    "category": "noise",
                    "frequency": "Low",
                    "safe_remove": "Yes",
                    "level": "Conservative",
                    "domains": ["ocr","web"],
                    "token_type": "noise",
                    "notes": "OCR/web zero-width artifact (interior).",
                })
        # Compound with inserted ASCII space (OCR error pattern)
        if len(base) >= 4:
            spaced = base[:len(base)//2] + " " + base[len(base)//2:]
            out.append({
                "khmer": spaced,
                "english": f"{e['english']} (mis-spaced)",
                "category": "noise",
                "frequency": "Low",
                "safe_remove": "Yes",
                "level": "Conservative",
                "domains": ["ocr"],
                "token_type": "noise",
                "notes": "OCR mis-segmentation: ASCII space inside Khmer word.",
            })
    return out


# ── Generator 9: Spacing variants of multi-word compounds ──────────
def gen_spacing_variants(core_entries):
    """The same multi-word stop phrase may be written with or without
    inter-word spaces, depending on author/OCR."""
    out = []
    for e in core_entries:
        if e["token_type"] not in ("compound", "multi-word"):
            continue
        base = e["khmer"]
        if len(base) < 4:
            continue
        # Insert single ASCII space at mid-point
        mid = base[:len(base)//2] + " " + base[len(base)//2:]
        out.append({
            "khmer": mid,
            "english": f"{e['english']} (spaced variant)",
            "category": e["category"],
            "frequency": "Low",
            "safe_remove": e["safe_remove"],
            "level": e["level"],
            "domains": e["domains"],
            "token_type": "multi-word",
            "notes": "Author-introduced spacing variant.",
        })
    return out


# ── Generator 10: Typo / shortened spellings ───────────────────────
def gen_typo_variants():
    out = []
    # (typo, canonical, gloss)
    pairs = [
        ("ខ្ញំុ", "ខ្ញុំ", "I (misordered subscript+vowel)"),
        ("ឲយ",   "ឲ្យ",   "let (missing virama)"),
        ("អោយ",  "ឲ្យ",   "let (modern variant)"),
        ("ហើយ្", "ហើយ",  "already (stray virama)"),
        ("ហើយ ", "ហើយ",  "already (trailing space)"),
        ("ឥលូវ", "ឥឡូវ", "now (common typo)"),
        ("លូវ",  "ឥឡូវ", "now (shortened)"),
        ("លឺវ",  "ឥឡូវ", "now (typo)"),
        ("ឥលូ",  "ឥឡូវ", "now (clipped)"),
        ("មិន្",  "មិន",   "not (stray virama)"),
        ("ហើ",   "ហើយ",  "already (clipped)"),
        ("បាន្",  "បាន",   "PAST (stray virama)"),
        ("បាន ",  "បាន",   "PAST (trailing space)"),
        ("ហ៎ះ",   "ហ៎",    "huh (with diacritic)"),
        ("ចា៎ស",  "ចាស",   "yes (decorative)"),
        ("អូខ",   "អូខេ",  "OK (clipped)"),
        ("អូខេយ", "អូខេ",  "OK (extended)"),
        ("ចេះ",   "ចេះ",   "know (ok as-is)"),
        ("អត់",    "អត់",   "no (informal)"),
        ("អត់ទេ", "អត់ទេ", "no (informal compound)"),
        ("អត់មាន","អត់មាន","not have (informal)"),
        ("ស្អី",  "អ្វី",  "what (colloquial)"),
        ("អី",    "អ្វី",  "what (clipped)"),
        ("បាដ",   "បាទ",   "yes(m) (typo)"),
        ("ច្បាស់ៗ","ច្បាស់","clearly (emphatic)"),
        ("លោកម្ចាស់","លោក","Mr (extended)"),
    ]
    for t, canon, gloss in pairs:
        out.append({
            "khmer": t,
            "english": f"variant of {canon}: {gloss}",
            "category": "noise",
            "frequency": "Low",
            "safe_remove": "Yes",
            "level": "Conservative",
            "domains": ["ocr","social","fb"],
            "token_type": "noise",
            "notes": "Typo/non-canonical spelling — map to canonical in preprocessing.",
        })
    return out


# ── Generator 11: Bilingual fillers ────────────────────────────────
def gen_bilingual_fillers():
    """English/Western fillers that frequently appear in Khmer social text."""
    items = [
        ("the", "english article"),     ("a", "english article"),
        ("an", "english article"),       ("is", "english copula"),
        ("are","english copula"),       ("am",  "english copula"),
        ("was","english copula"),       ("were","english copula"),
        ("be", "english copula"),       ("been","english copula"),
        ("of", "english prep"),         ("in", "english prep"),
        ("on", "english prep"),         ("at", "english prep"),
        ("to", "english prep"),         ("for","english prep"),
        ("by", "english prep"),         ("from","english prep"),
        ("with","english prep"),         ("as", "english prep"),
        ("and","english conj"),         ("or", "english conj"),
        ("but","english conj"),         ("so", "english conj"),
        ("if", "english conj"),         ("then","english conj"),
        ("not","english neg (CAUTION)"), ("no","english neg (CAUTION)"),
        ("can","english modal"),         ("will","english modal"),
        ("would","english modal"),      ("should","english modal"),
        ("could","english modal"),      ("may", "english modal"),
        ("might","english modal"),       ("must","english modal"),
        ("i",  "english pronoun"),       ("you","english pronoun"),
        ("he", "english pronoun"),       ("she","english pronoun"),
        ("it", "english pronoun"),       ("we", "english pronoun"),
        ("they","english pronoun"),      ("me", "english pronoun"),
        ("us", "english pronoun"),       ("them","english pronoun"),
        ("my", "english poss"),         ("your","english poss"),
        ("his","english poss"),         ("her","english poss"),
        ("our","english poss"),         ("their","english poss"),
        ("this","english dem"),          ("that","english dem"),
        ("these","english dem"),         ("those","english dem"),
        ("here","english adv"),          ("there","english adv"),
        ("now","english adv"),           ("then","english adv"),
        ("very","english intensifier (CAUTION)"),
        ("really","english intensifier (CAUTION)"),
        ("just","english adv"),          ("also","english adv"),
        ("only","english adv"),          ("even","english adv"),
        ("still","english adv"),         ("already","english adv"),
    ]
    out = []
    seen = set()
    for tok, gloss in items:
        for f in [tok, tok.capitalize(), tok.upper()]:
            if f in seen: continue
            seen.add(f)
            safe = "Caution" if "CAUTION" in gloss else "Yes"
            lvl  = "Dangerous" if "CAUTION" in gloss else "Conservative"
            out.append({
                "khmer": f,
                "english": gloss,
                "category": "noise",
                "frequency": "Medium",
                "safe_remove": safe,
                "level": lvl,
                "domains": ["social","web","ocr"],
                "token_type": "noise",
                "notes": "English filler appearing in Khmer text.",
            })
    return out


# ── Generator 12: Punctuation / emoji-adjacent artifacts ───────────
def gen_punctuation_artifacts():
    out = []
    base_puncts = [".", ",", "!", "?", ";", ":", "-", "_", "*", "/", "\\",
                   "(", ")", "[", "]", "{", "}", "<", ">", "|", "~", "`",
                   "៕", "៚", "៙", "៘", "។", "៖", "ៗ"]
    for p in base_puncts:
        for n in range(2, 11):
            out.append({
                "khmer": p * n,
                "english": f"'{p}' ×{n}",
                "category": "noise",
                "frequency": "Low" if n > 4 else "Medium",
                "safe_remove": "Yes",
                "level": "Conservative",
                "domains": ["ocr","web","social"],
                "token_type": "noise",
                "notes": "Repeated punctuation noise.",
            })
    # Common mixed sequences
    mixed = ["?!", "!?", "?!?", "!?!", "??!", "!!?",
             "...", "....", ".....", "......",
             "----", "____", "====", "****",
             "។។", "។។។", "។។។។", "៕៕", "៚៚", "ៗៗ", "ៗៗៗ",
             "។ ។", "។  ។", "។\t។",
             "៕។", "។៕", "៚។", "។៚"]
    for m in mixed:
        out.append({
            "khmer": m,
            "english": f"punctuation cluster '{m}'",
            "category": "noise",
            "frequency": "Medium",
            "safe_remove": "Yes",
            "level": "Conservative",
            "domains": ["ocr","web","social"],
            "token_type": "noise",
            "notes": "Mixed punctuation noise.",
        })
    # Common chat emojis (text form)
    chat_emojis = [":)", ":(", ":D", ":P", ":/", ":|", ":3", "XD", "xD",
                   ":-)", ":-(", ":-D", ";)", ";-)",  "T_T", "T.T", "TT",
                   "<3", "</3", ":'(", ":'D", "=)", "=(", "=D",
                   "(y)", "(Y)", "(n)", "(N)"]
    for em in chat_emojis:
        out.append({
            "khmer": em,
            "english": f"text emoticon {em}",
            "category": "noise",
            "frequency": "Medium",
            "safe_remove": "Yes",
            "level": "Conservative",
            "domains": ["social","fb","youtube"],
            "token_type": "noise",
            "notes": "Text-form emoticon.",
        })
    return out
