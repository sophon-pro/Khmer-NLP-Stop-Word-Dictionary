"""
build.py
========
Assemble the full Khmer stop-word dictionary and export deliverables.

Pipeline:
  1. Load curated CORE (full metadata).
  2. Run all expansion generators.
  3. NFC-normalize every Khmer surface form.
  4. Deduplicate (keep first occurrence — CORE wins over generated).
  5. Stratify into Conservative / Moderate / Aggressive / Dangerous.
  6. Project into per-domain lists.
  7. Build tokenisation-aware splits (single / compound / multi-word / noise).
  8. Export: CSV, TXT, JSON, Python module, Regex.
  9. Print a build report.
"""
import csv
import json
import re
import unicodedata
from pathlib import Path
from collections import Counter, defaultdict

from core_dictionary import CORE
from expansion import (
    gen_khmer_digit_strings,
    gen_latin_digit_strings,
    gen_laughter_repetitions,
    gen_slang_stretches,
    gen_particle_repetitions,
    gen_compound_phrases,
    gen_romanized_khmer_slang,
    gen_ocr_artifacts,
    gen_spacing_variants,
    gen_typo_variants,
    gen_bilingual_fillers,
    gen_punctuation_artifacts,
)

OUT_DIR = Path("/home/claude/khmer_stopwords/dist")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ─── Normalisation ─────────────────────────────────────────────────
def nfc(s: str) -> str:
    """NFC normalization is the recommended form for Khmer in modern
    NLP pipelines (used by HF tokenizers, ICU, Khmer Wiki).
    NFKC would collapse some compatibility chars that matter for
    Khmer typography, so we keep NFC."""
    return unicodedata.normalize("NFC", s)


# ─── Assemble ──────────────────────────────────────────────────────
def assemble():
    print(">> Loading CORE…")
    entries = list(CORE)
    print(f"   {len(entries):,} curated entries")

    generators = [
        ("Khmer numerals 0–9999",          gen_khmer_digit_strings,    None),
        ("Latin numerals 0–9999",          gen_latin_digit_strings,    None),
        ("Laughter repetitions",           gen_laughter_repetitions,   None),
        ("Slang character stretches",      gen_slang_stretches,        None),
        ("Particle repetitions",           gen_particle_repetitions,   None),
        ("Compound particle phrases",      gen_compound_phrases,       None),
        ("Romanized Khmer slang",          gen_romanized_khmer_slang,  None),
        ("OCR confusion artifacts",        gen_ocr_artifacts,          "core"),
        ("Spacing variants of compounds",  gen_spacing_variants,       "core"),
        ("Typo / shortened spellings",     gen_typo_variants,          None),
        ("Bilingual fillers",              gen_bilingual_fillers,      None),
        ("Punctuation / emoji artifacts",  gen_punctuation_artifacts,  None),
    ]
    for label, fn, arg in generators:
        gen = fn(CORE) if arg == "core" else fn()
        print(f">> {label}: +{len(gen):,}")
        entries.extend(gen)

    # Normalise
    for e in entries:
        e["khmer"] = nfc(e["khmer"])
        if "domains" not in e or not e["domains"]:
            e["domains"] = ["all"]

    # Dedup (first-wins keeps the curated entry over generated duplicates)
    seen, unique = set(), []
    for e in entries:
        key = e["khmer"]
        if key in seen or key == "":
            continue
        seen.add(key)
        unique.append(e)

    print(f">> After NFC + dedup: {len(unique):,} unique entries")
    return unique


# ─── Stratified projections ────────────────────────────────────────
LEVEL_ORDER = {"Conservative": 0, "Moderate": 1, "Aggressive": 2, "Dangerous": 3}

def project_levels(entries):
    """
    Conservative = level=Conservative AND safe_remove=Yes
    Moderate     = Conservative ∪ (level=Moderate AND safe_remove=Yes)
    Aggressive   = Moderate ∪ (level=Aggressive AND safe_remove in {Yes,Caution})
    Dangerous    = entries where safe_remove='No' or level='Dangerous'
                   (this is the DO-NOT-REMOVE warning list)
    """
    conservative, moderate, aggressive, dangerous = [], [], [], []
    for e in entries:
        if e["level"] == "Dangerous" or e["safe_remove"] == "No":
            dangerous.append(e["khmer"])
        if e["level"] == "Conservative" and e["safe_remove"] == "Yes":
            conservative.append(e["khmer"])
        if e["level"] in ("Conservative", "Moderate") and e["safe_remove"] == "Yes":
            moderate.append(e["khmer"])
        if e["level"] in ("Conservative", "Moderate", "Aggressive") and e["safe_remove"] in ("Yes", "Caution"):
            aggressive.append(e["khmer"])
    return {
        "conservative": sorted(set(conservative)),
        "moderate":     sorted(set(moderate)),
        "aggressive":   sorted(set(aggressive)),
        "dangerous":    sorted(set(dangerous)),
    }


# ─── Domain projections ────────────────────────────────────────────
DOMAINS = ["news", "social", "academic", "gov", "youtube", "fb", "ocr", "web",
           "conversational", "religious", "finance", "legal", "formal"]

def project_domains(entries):
    out = defaultdict(list)
    for e in entries:
        if e["safe_remove"] == "No":
            continue
        for d in e["domains"]:
            if d == "all":
                for dd in DOMAINS:
                    out[dd].append(e["khmer"])
            else:
                out[d].append(e["khmer"])
    return {d: sorted(set(out[d])) for d in DOMAINS if out[d]}


# ─── Token-type projections ───────────────────────────────────────
def project_token_types(entries):
    buckets = defaultdict(list)
    for e in entries:
        if e["safe_remove"] == "No":
            continue
        buckets[e["token_type"]].append(e["khmer"])
    return {k: sorted(set(v)) for k, v in buckets.items()}


# ─── Exports ──────────────────────────────────────────────────────
def export_csv(entries):
    path = OUT_DIR / "khmer_stopwords_full.csv"
    fields = ["khmer","english","category","frequency","safe_remove",
              "level","domains","token_type","notes"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for e in entries:
            row = dict(e)
            row["domains"] = "|".join(e["domains"])
            w.writerow(row)
    return path

def export_txt(entries):
    path = OUT_DIR / "khmer_stopwords_full.txt"
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(e["khmer"] + "\n")
    return path

def export_json(entries):
    path = OUT_DIR / "khmer_stopwords_full.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    return path

def export_python(entries):
    path = OUT_DIR / "khmer_stopwords_full.py"
    words = [e["khmer"] for e in entries if e["safe_remove"] == "Yes"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated Khmer stop-word list (safe_remove == 'Yes' only).\n")
        f.write(f"# Total: {len(words)} tokens. NFC-normalized.\n\n")
        f.write("KHMER_STOPWORDS = [\n")
        for w in words:
            f.write(f"    {w!r},\n")
        f.write("]\n\n")
        f.write("KHMER_STOPWORDS_SET = frozenset(KHMER_STOPWORDS)\n")
    return path

def export_regex(entries):
    path = OUT_DIR / "khmer_stopwords_full.regex.txt"
    # Sort by length (longest-first) to ensure the alternation matches
    # multi-word compounds before their atomic pieces.
    words = sorted({e["khmer"] for e in entries if e["safe_remove"] == "Yes"},
                   key=lambda x: (-len(x), x))
    alternation = "|".join(re.escape(w) for w in words)
    pattern = f"(?:{alternation})"
    with open(path, "w", encoding="utf-8") as f:
        f.write(pattern)
    return path, len(words)

def export_levels(level_buckets):
    paths = {}
    for name, words in level_buckets.items():
        path = OUT_DIR / f"khmer_stopwords_{name}.txt"
        with open(path, "w", encoding="utf-8") as f:
            for w in words: f.write(w + "\n")
        paths[name] = path
        # JSON too
        jpath = OUT_DIR / f"khmer_stopwords_{name}.json"
        with open(jpath, "w", encoding="utf-8") as f:
            json.dump(words, f, ensure_ascii=False, indent=2)
    return paths

def export_domains(domain_buckets):
    paths = {}
    for name, words in domain_buckets.items():
        path = OUT_DIR / f"khmer_stopwords_domain_{name}.txt"
        with open(path, "w", encoding="utf-8") as f:
            for w in words: f.write(w + "\n")
        paths[name] = path
    return paths

def export_token_types(buckets):
    paths = {}
    for name, words in buckets.items():
        safe_name = name.replace(" ", "_").replace("-", "_")
        path = OUT_DIR / f"khmer_stopwords_tokentype_{safe_name}.txt"
        with open(path, "w", encoding="utf-8") as f:
            for w in words: f.write(w + "\n")
        paths[name] = path
    return paths


# ─── Build report ─────────────────────────────────────────────────
def build_report(entries, level_buckets, domain_buckets, token_buckets, regex_count):
    cats = Counter(e["category"] for e in entries)
    freqs = Counter(e["frequency"] for e in entries)
    safety = Counter(e["safe_remove"] for e in entries)
    types = Counter(e["token_type"] for e in entries)

    lines = []
    lines.append("=" * 70)
    lines.append("KHMER STOP-WORD DICTIONARY — BUILD REPORT")
    lines.append("=" * 70)
    lines.append(f"Total unique entries:               {len(entries):,}")
    lines.append("")
    lines.append("By category:")
    for k, v in sorted(cats.items(), key=lambda x: -x[1]):
        lines.append(f"  {k:18s} {v:>6,}")
    lines.append("")
    lines.append("By frequency estimate:")
    for k in ("High","Medium","Low"):
        lines.append(f"  {k:18s} {freqs.get(k,0):>6,}")
    lines.append("")
    lines.append("By safe-to-remove flag:")
    for k in ("Yes","Caution","No"):
        lines.append(f"  {k:18s} {safety.get(k,0):>6,}")
    lines.append("")
    lines.append("By token type:")
    for k, v in sorted(types.items(), key=lambda x: -x[1]):
        lines.append(f"  {k:18s} {v:>6,}")
    lines.append("")
    lines.append("Stratified level lists (safe-to-remove only):")
    for k, v in level_buckets.items():
        lines.append(f"  {k:18s} {len(v):>6,}")
    lines.append("")
    lines.append("Domain-specific lists:")
    for k, v in domain_buckets.items():
        lines.append(f"  {k:18s} {len(v):>6,}")
    lines.append("")
    lines.append(f"Regex alternation token count:      {regex_count:,}")
    lines.append("=" * 70)
    report = "\n".join(lines)
    (OUT_DIR / "BUILD_REPORT.txt").write_text(report, encoding="utf-8")
    return report


# ─── Main ──────────────────────────────────────────────────────────
def main():
    entries = assemble()

    print(">> Projecting stratified levels…")
    levels = project_levels(entries)

    print(">> Projecting per-domain lists…")
    domains = project_domains(entries)

    print(">> Projecting token-type lists…")
    types_ = project_token_types(entries)

    print(">> Exporting …")
    export_csv(entries)
    export_txt(entries)
    export_json(entries)
    export_python(entries)
    _, regex_count = export_regex(entries)
    export_levels(levels)
    export_domains(domains)
    export_token_types(types_)

    print()
    report = build_report(entries, levels, domains, types_, regex_count)
    print(report)


if __name__ == "__main__":
    main()
