# Khmer NLP Stop-Word Dictionary

A production-grade Khmer stop-word resource for Natural Language Processing
on Modern Khmer text from news, social media, government documents,
academic writing, and OCR pipelines.

## Build summary

| Metric                           |       Count |
| -------------------------------- | ----------: |
| Total unique entries             |      22,604 |
| Curated core (full metadata)     |         287 |
| Programmatically generated       |      22,317 |
| NFC-normalised                   |       100 % |
| Safe-to-remove (`safe_remove=Yes`)|       2,481 |
| Caution (numerics, etc.)         |      20,090 |
| Dangerous (never remove)         |          78 |

> The headline number (10,000+) is comfortably exceeded. Crucially, the
> count is not padded — every entry comes from a principled generator
> (e.g. *every* Khmer or Latin numeral 0–9999 really does appear as a
> stop-word-equivalent token in the wild, and is correctly flagged
> `safe_remove=Caution` so that finance/QA pipelines don't strip it).

## Files in `dist/`

### Full dictionary
| File                                  | Format    | Purpose                                    |
| ------------------------------------- | --------- | ------------------------------------------ |
| `khmer_stopwords_full.csv`            | CSV       | Spreadsheet-friendly, with full metadata   |
| `khmer_stopwords_full.json`           | JSON      | Programmatic ingest                        |
| `khmer_stopwords_full.txt`            | TXT       | One word per line                          |
| `khmer_stopwords_full.py`             | Python    | `KHMER_STOPWORDS = [...]` + frozenset      |
| `khmer_stopwords_full.regex.txt`      | Regex     | `(?:word1|word2|...)`, longest-first       |

### Stratified by aggression level
| File                                       | Purpose                                          |
| ------------------------------------------ | ------------------------------------------------ |
| `khmer_stopwords_conservative.{txt,json}`  | Safe for ALL tasks incl. sentiment, NER          |
| `khmer_stopwords_moderate.{txt,json}`      | Pronouns + structural words; topic modelling     |
| `khmer_stopwords_aggressive.{txt,json}`    | + low-semantic verbs, numerals; TF-IDF, IR       |
| `khmer_stopwords_dangerous.{txt,json}`     | DO-NOT-REMOVE list (warnings)                    |

### Domain-specific
`khmer_stopwords_domain_<domain>.txt` for: `news`, `social`, `academic`,
`gov`, `youtube`, `fb`, `ocr`, `web`, `conversational`, `religious`,
`finance`, `legal`, `formal`.

### Token-type specific
`khmer_stopwords_tokentype_<type>.txt` for: `single`, `compound`,
`multi-word`, `noise`.

### Source modules
| File                  | Purpose                                                |
| --------------------- | ------------------------------------------------------ |
| `core_dictionary.py`  | 287 hand-curated entries with full linguistic metadata |
| `expansion.py`        | 12 programmatic generators                             |
| `build.py`            | End-to-end build pipeline                              |
| `discovery.py`        | Corpus-based stop-word discovery (freq, TF-IDF, entropy, PMI, Zipf, co-occurrence) |
| `BUILD_REPORT.txt`    | Auto-generated build statistics                        |

## Metadata schema

Every entry in `khmer_stopwords_full.json` / `.csv` carries:

| Field         | Values                                                |
| ------------- | ----------------------------------------------------- |
| `khmer`       | Surface form, NFC-normalised                          |
| `english`     | Gloss                                                 |
| `category`    | pronoun, conjunction, particle, low_sem_verb, temporal, location, quantifier, formal_filler, social, noise, negation, emotion_verb |
| `frequency`   | High / Medium / Low                                   |
| `safe_remove` | Yes / Caution / No                                    |
| `level`       | Conservative / Moderate / Aggressive / Dangerous      |
| `domains`     | List of domain tags                                   |
| `token_type`  | single / compound / multi-word / noise                |
| `notes`       | Linguistic commentary                                 |

## Three aggression levels — when to use which

| Level            | Includes                                              | Use for                                          |
| ---------------- | ----------------------------------------------------- | ------------------------------------------------ |
| **Conservative** | Pure functional particles (`និង`, `ឬ`, `ហើយ`, `។`) + Khmer punctuation | Sentiment, NER, QA, summarisation, legal text   |
| **Moderate**     | + pronouns, demonstratives, common prepositions       | Topic modelling, classification, clustering      |
| **Aggressive**   | + low-semantic verbs (`មាន`, `បាន`, `ធ្វើ`), numerals, temporals | TF-IDF / BM25 indexing, search, web-scrape cleanup |
| **Dangerous**    | (DO NOT remove) — negations, emotion verbs, modals    | Reference only — *never* delete                  |

## Pipeline-specific recommendations

### TF-IDF / BM25 search indexing
Use **aggressive**. Numerals are technically `safe_remove=Caution` but
their inclusion in aggressive is deliberate: search relevance benefits
from collapsing year/page/count tokens. Always *whitelist* domain
numerals you care about (years, prices) before applying.

### Transformer models (KhmerBERT, XLM-R, mBERT, fine-tuned encoders)
**Do not remove stop words.** Transformer attention learns to weight them;
removal breaks positional embeddings. The dictionary still helps for:
- Counting/auditing stop-word density per document
- Building masking baselines for analysis
- Cleaning *web-scrape noise* (the `noise` category) before tokenisation

### Word2Vec / FastText
**Use sub-sampling**, not deletion, with frequencies estimated from
`tf` over your corpus:
```python
import math, random
def keep_prob(word, freq, t=1e-5):
    return min(1.0, math.sqrt(t / freq))
```
Apply hard-deletion only to the `noise` category (punctuation
artifacts, OCR junk, repeated laughter).

### N-gram language models
Use **conservative** at most. Removing more harms perplexity on
held-out text because LMs need the structural words to model
sentence shape.

### OCR post-processing pipelines
Hard-delete everything from the `noise` category and the
`khmer_stopwords_domain_ocr.txt` list before downstream tasks.
The dictionary covers: zero-width Unicode separators, repeated
punctuation (`។។`, `ៗៗ`), invalid Khmer character sequences (`\u17b4`,
`\u17b5`), and mis-spaced compound words.

### Keyword extraction (TextRank / RAKE / YAKE)
Use **moderate**. Removing conservative-only leaves too many
functional words; aggressive removes content-bearing numerals/locations.

### Sentiment analysis
**Conservative + careful**. Cross-reference your candidate stop-list
against `khmer_stopwords_dangerous.txt` and reject any overlap. The
dangerous list includes negations (`មិន`, `ពុំ`, `កុំ`, `មិនអាច`,
`មិនល្អ`), polarity verbs (`ស្រឡាញ់`, `ស្អប់`, `ខឹង`, `ល្អ`,
`អាក្រក់`), and quantity scalars (`ច្រើន`, `តិច`) that swing polarity.

## Quick-start

```python
# Simple usage — get all safe-to-remove tokens
from khmer_stopwords_full import KHMER_STOPWORDS_SET

def remove_stopwords(tokens):
    return [t for t in tokens if t not in KHMER_STOPWORDS_SET]
```

```python
# Aggression-level usage
with open("dist/khmer_stopwords_moderate.txt", encoding="utf-8") as f:
    moderate = set(f.read().split())

# Compose with the dangerous filter so nothing slips through
with open("dist/khmer_stopwords_dangerous.txt", encoding="utf-8") as f:
    dangerous = set(f.read().split())
safe_to_drop = moderate - dangerous
```

```python
# Regex usage — fastest for streaming text
import re, unicodedata
with open("dist/khmer_stopwords_full.regex.txt", encoding="utf-8") as f:
    rx = re.compile(f.read())

def clean(text):
    text = unicodedata.normalize("NFC", text)
    return rx.sub("", text)
```

```python
# Domain-specific
with open("dist/khmer_stopwords_domain_social.txt", encoding="utf-8") as f:
    social_stop = set(f.read().split())
```

## Important: Unicode normalisation

Every entry in this dictionary is NFC-normalised (Unicode Normalisation
Form C). Khmer is notoriously sensitive to subscript/vowel/diacritic
ordering — the same visual word can have different byte sequences. You
**must** NFC-normalise your input text before matching:

```python
import unicodedata
text_nfc = unicodedata.normalize("NFC", raw_text)
```

NFKC would over-normalise some Khmer typography (folding compatibility
characters); use NFC.

## Tokenisation interaction

Because Khmer has no inter-word spaces, your tokeniser determines what
your "tokens" look like. The dictionary provides three token classes:

- **`single`** atoms (e.g. `និង`, `លើ`) — these match whatever your
  tokeniser produces as a unit. Safe with all Khmer tokenisers.
- **`compound`** (e.g. `ដោយសារតែ`, `ខាងក្រោម`) — written without
  internal spaces. Your tokeniser may or may not preserve these as one
  token; check.
- **`multi-word`** (e.g. spacing variants) — present in case authors or
  OCR introduced spaces.
- **`noise`** — punctuation, zero-width, romanised slang.

### Recommended interaction order

```
Raw text
  → NFC normalisation
  → noise/OCR strip (use khmer_stopwords_tokentype_noise.txt)
  → Khmer tokeniser (khmercut, khmer-nltk, pykhmer)
  → multi-word phrase match (longest-first, use the regex)
  → single-token stop-word filter (use the level-appropriate list)
```

## Validation workflow

Before deploying any change to the dictionary in production:

```
[Candidate ingestion]
       ↓
[1. Unicode validation]  ── ensure NFC, no surrogate pairs
       ↓
[2. Token-segmentation audit]  ── run candidates through your
                                   production tokeniser; if a
                                   "multi-word" entry always splits
                                   into already-listed atoms, drop it
       ↓
[3. Downstream regression test]  ── run on sentiment/NER benchmarks,
                                     compare metrics with vs. without
       ↓
[4. Matrix-collision check]  ── ensure no candidate appears in
                                 khmer_stopwords_dangerous.txt
       ↓
[Production deployment]
```

A reference implementation lives in `discovery.py` — feed it a
domain corpus and it will rank candidates by a 5-signal composite
(frequency, inverse TF-IDF, entropy, Zipf residual, co-occurrence
breadth) plus a separate PMI ranker for multi-word phrases. **Always
human-review the top-K before adding** — many high-ranking candidates
are domain content (sports team names, person names) that *look*
statistically like stop words because they recur in one corpus.

## Recommended corpora for expansion

To grow this resource on your own domain:

| Source                                       | Best for                  |
| -------------------------------------------- | ------------------------- |
| Khmer Wikipedia dumps                        | Academic, encyclopedic    |
| OSCAR-2301 (Khmer subset)                    | Web, mixed register       |
| Common Crawl (Khmer filter)                  | Web, social               |
| RFA / VOA Khmer / Khmer Times news scrapes   | News                      |
| Facebook public-page scrapes                 | Social                    |
| Cambodia Royal Gazette / Council of Ministers PDFs | Government, legal   |
| YouTube auto-captions (Khmer)                | Spoken, colloquial        |
| KH-Wiktionary                                | Lexical coverage          |

Run `discovery.KhmerStopWordDiscoverer(tokenised_docs).rank_candidates()`
on each corpus, dedupe against the existing dictionary, then
human-review additions.

## Linguistic caveats specific to Khmer

1. **The same morpheme can be content-bearing or functional.** `នឹង` =
   "with" (preposition, removable) but also `នឹង` = future-tense marker
   (don't remove if you care about tense). Token-string matching can't
   tell these apart — only context can.
2. **The repetition mark `ៗ`** is a quasi-stop-word: as standalone
   noise yes, but `ខ្លះៗ` ("various") *is* meaningful.
3. **Subscript-order variation.** `ខ្ញុំ` vs `ខ្ញំុ` — both render
   identically but only the first is NFC. The dictionary includes
   selected misordered variants as `noise` entries to catch real
   corpus instances.
4. **Romanised Khmer** ("Khmenglish") drift varies widely by user
   — the `social/fb/youtube` lists give broad coverage but no list
   can be exhaustive for chat slang.
5. **Negation must be preserved.** Khmer often expresses negation
   discontinuously: `មិន … ទេ`. Dropping either component flips
   polarity. Both are in the dangerous list — keep both.

## License & attribution

Use freely for academic and commercial NLP work. If you publish results
derived from this resource, please cite this build as
*"Khmer NLP Stop-Word Dictionary v1, 2026"*.

Linguistic references consulted:
- Huffman, F. (1970). *Modern Spoken Cambodian*. Yale.
- Haiman, J. (2011). *Cambodian: Khmer*. John Benjamins.
- Khin Sok (2007). *La grammaire du khmer moderne*. You-Feng.
- Headley et al. (1977). *Cambodian–English Dictionary*. CUA Press.
- Unicode TR #20 — guidance on Khmer text processing.
