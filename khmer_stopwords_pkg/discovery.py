"""
discovery.py
============
Statistical stop-word discovery from a Khmer corpus.

Given any tokenised Khmer corpus (list[list[str]]), this module ranks
candidate stop words using six complementary signals:

    1. raw_frequency          — Zipf-tail anchors
    2. tfidf_inverse          — words with near-zero IDF mass
    3. entropy_distribution   — uniform across documents
    4. pmi_collocations       — surface multi-word stop phrases
    5. zipf_residual          — deviation from the Zipf 1/r line
    6. cooccurrence_breadth   — appears beside almost everything

Designed to grow a hand-curated seed list from ~2,500 entries to
10,000+ corpus-specific entries when run over a domain corpus.

Typical use:
    from discovery import KhmerStopWordDiscoverer
    d = KhmerStopWordDiscoverer(tokenised_corpus)
    new_candidates = d.rank_candidates(top_k=2000)
    # ... then HUMAN-REVIEW before adding to dictionary.
"""
from __future__ import annotations
import math
import collections
from typing import Iterable, Sequence


class KhmerStopWordDiscoverer:
    def __init__(self, tokenised_corpus: Sequence[Sequence[str]]):
        """
        :param tokenised_corpus: e.g. output of khmer-nltk / pykhmer / khmercut.
                                 Must be a list of token-lists (documents).
        """
        self.corpus = [list(d) for d in tokenised_corpus]
        if not self.corpus:
            raise ValueError("Empty corpus.")
        self.N = len(self.corpus)
        self.flat = [t for d in self.corpus for t in d]
        self.total_tokens = len(self.flat)
        self.tf = collections.Counter(self.flat)
        self.vocab = list(self.tf.keys())
        self.V = len(self.vocab)

        # document frequencies
        self.df: dict[str, int] = collections.Counter()
        for d in self.corpus:
            for w in set(d):
                self.df[w] += 1

    # ─────────────────────────────────────────────────────────────
    # 1. Raw frequency
    # ─────────────────────────────────────────────────────────────
    def top_by_frequency(self, top_k: int = 1000) -> list[tuple[str, int]]:
        return self.tf.most_common(top_k)

    # ─────────────────────────────────────────────────────────────
    # 2. Inverse TF-IDF — words with the LEAST discriminative power
    # ─────────────────────────────────────────────────────────────
    def low_idf_terms(self, top_k: int = 1000) -> list[tuple[str, float]]:
        idf = {w: math.log(self.N / (1 + self.df[w])) for w in self.vocab}
        # Lowest IDF = most ubiquitous = best stop-word candidate
        return sorted(idf.items(), key=lambda x: x[1])[:top_k]

    # ─────────────────────────────────────────────────────────────
    # 3. Entropy of distribution across documents
    # ─────────────────────────────────────────────────────────────
    def entropy_per_word(self, min_count: int = 5) -> list[tuple[str, float]]:
        """
        Higher entropy ⇒ word distributed uniformly across documents
        ⇒ low topical specificity ⇒ stop-word candidate.

        Normalised by log2(N) so result ∈ [0,1].
        """
        word_doc = collections.defaultdict(lambda: collections.Counter())
        for idx, doc in enumerate(self.corpus):
            for w in doc:
                word_doc[w][idx] += 1
        max_ent = math.log2(self.N) if self.N > 1 else 1.0

        scores: dict[str, float] = {}
        for w, total in self.tf.items():
            if total < min_count:
                continue
            ent = 0.0
            for c in word_doc[w].values():
                p = c / total
                ent -= p * math.log2(p)
            scores[w] = ent / max_ent
        return sorted(scores.items(), key=lambda x: -x[1])

    # ─────────────────────────────────────────────────────────────
    # 4. PMI — surface multi-word stop phrases
    # ─────────────────────────────────────────────────────────────
    def top_bigrams_by_pmi(self, top_k: int = 1000,
                           min_count: int = 5) -> list[tuple[tuple[str, str], float]]:
        """
        Bigrams with high PMI AND high frequency are candidate
        multi-word stop expressions (e.g. ដោយ + សារ → ដោយសារ).
        """
        bg = collections.Counter()
        for d in self.corpus:
            for a, b in zip(d, d[1:]):
                bg[(a, b)] += 1
        total_bg = sum(bg.values())

        scored: list[tuple[tuple[str, str], float]] = []
        for (a, b), c in bg.items():
            if c < min_count: continue
            p_ab = c / total_bg
            p_a  = self.tf[a] / self.total_tokens
            p_b  = self.tf[b] / self.total_tokens
            if p_a == 0 or p_b == 0: continue
            pmi  = math.log2(p_ab / (p_a * p_b))
            scored.append(((a, b), pmi))
        return sorted(scored, key=lambda x: -x[1])[:top_k]

    # ─────────────────────────────────────────────────────────────
    # 5. Zipf residual — gap from ideal 1/rank line
    # ─────────────────────────────────────────────────────────────
    def zipf_residuals(self, top_k: int = 500) -> list[tuple[str, float]]:
        ranked = self.tf.most_common()
        if not ranked: return []
        f1 = ranked[0][1]
        residuals: list[tuple[str, float]] = []
        for r, (w, c) in enumerate(ranked, start=1):
            ideal = f1 / r
            residuals.append((w, c - ideal))
        # words SIGNIFICANTLY above the Zipf line are over-represented
        return sorted(residuals, key=lambda x: -x[1])[:top_k]

    # ─────────────────────────────────────────────────────────────
    # 6. Co-occurrence breadth
    # ─────────────────────────────────────────────────────────────
    def cooccurrence_breadth(self, window: int = 5,
                             top_k: int = 1000,
                             min_count: int = 10) -> list[tuple[str, int]]:
        """
        For each word, count how many DISTINCT neighbours it has within
        ±window. Stop words co-occur with almost everything.
        """
        neighbours: dict[str, set[str]] = collections.defaultdict(set)
        for d in self.corpus:
            for i, w in enumerate(d):
                lo = max(0, i - window)
                hi = min(len(d), i + window + 1)
                for j in range(lo, hi):
                    if j == i: continue
                    neighbours[w].add(d[j])
        scored = [(w, len(s)) for w, s in neighbours.items()
                  if self.tf[w] >= min_count]
        return sorted(scored, key=lambda x: -x[1])[:top_k]

    # ─────────────────────────────────────────────────────────────
    # Composite ranker
    # ─────────────────────────────────────────────────────────────
    def rank_candidates(self, top_k: int = 1000,
                        min_count: int = 5) -> list[tuple[str, float]]:
        """
        Combine the six signals with rank-based scoring.

        Each signal contributes a rank ∈ [0, V]; we sum the ranks
        (lower = more stop-wordy) and return the top_k.
        """
        signals = {
            "tf":      [w for w, _ in self.top_by_frequency(self.V)],
            "low_idf": [w for w, _ in self.low_idf_terms(self.V)],
            "ent":     [w for w, _ in self.entropy_per_word(min_count)],
            "zipf":    [w for w, _ in self.zipf_residuals(self.V)],
            "cooc":    [w for w, _ in self.cooccurrence_breadth(top_k=self.V,
                                                                min_count=min_count)],
        }
        rank_sum: dict[str, float] = collections.defaultdict(float)
        for sig_name, ranked in signals.items():
            for r, w in enumerate(ranked):
                rank_sum[w] += r
        # Lower combined rank = stronger stop-word evidence
        ordered = sorted(rank_sum.items(), key=lambda x: x[1])
        return ordered[:top_k]


# ─────────────────────────────────────────────────────────────────
# Smoke test
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    toy_corpus = [
        ["ខ្ញុំ","ទៅ","ផ្សារ","និង","ទិញ","ត្រី"],
        ["គាត់","ទៅ","សាលា","ហើយ","រៀន","ភាសា"],
        ["យើង","ស្រឡាញ់","ភូមិ","ដោយ","ព្រោះ","វា","ស្អាត"],
        ["ខ្ញុំ","មិន","ចង់","ទៅ","ឡើយ"],
        ["គាត់","និង","ខ្ញុំ","បាន","ហូបអាហារ","រួម","គ្នា"],
    ] * 50  # synthesise multiple docs
    d = KhmerStopWordDiscoverer(toy_corpus)
    print("Top frequency:", d.top_by_frequency(5))
    print("Low IDF:     ", d.low_idf_terms(5))
    print("High entropy:", d.entropy_per_word(min_count=3)[:5])
    print("Top PMI bg:  ", d.top_bigrams_by_pmi(5, min_count=3))
    print("Composite:   ", d.rank_candidates(top_k=10, min_count=3))
