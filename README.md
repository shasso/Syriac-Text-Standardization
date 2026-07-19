# Syriac Variant Classification Pipeline

Seven scripts, covering the full path from a raw NoSketchEngine `.vert`
corpus to a small, well-characterized set of word-spelling clusters that
genuinely need human linguistic review — plus both a naive baseline
standardizer and a risk-aware standardizer that consults the classification
pipeline's findings before rewriting anything.

The core problem: Sureth (Northeastern Neo-Aramaic) is written with a
heavily vocalized Syriac abjad, so the same word can surface as many
different strings depending on which vowel/stress diacritics were used.
`analyze_syriac_variants.py` finds these "duplicate" clusters by stripping
diacritics down to a bare consonantal skeleton and grouping surface forms
that share one. The obvious next step — canonicalize every cluster to its
single most frequent surface form (`standardize_syriac.py`, "Strategy 1") —
silently destroys information for a specific, identifiable, and
disproportionately high-frequency slice of the corpus: closed-class
morphology (the NENA copula/"to be" paradigm, the *piš-* passive auxiliary,
pronominal suffixes, negation, numerals) where different tense/person/gender
forms happen to share a consonantal skeleton. The four classification
scripts (`variant_insights.py` onward) find that slice, explain as much of
it as possible against known grammar and lexicon, and leave a much smaller,
well-characterized set for a human to review.
`standardize_syriac_v2.py` closes the loop: it consumes those
classification results directly and makes a per-cluster, audited merge/skip
decision instead of merging everything uniformly the way Stage B does.

If you want the reasoning and results written up in full, see
`suret_pulse_variant_classification_paper.docx` in this same output set —
this README is the operational/maintenance companion to that paper.

## Where this fits in the larger workflow

```
raw_corpus.vert  (NoSketchEngine format)
        │
        ▼
analyze_syriac_variants.py        ── Stage A: find duplicate clusters
        │  produces: <corpus>_analysis.json
        ├───────────────────────────┬────────────────────────────────────┐
        ▼                           ▼                                    │
standardize_syriac.py      variant_insights.py       ── Pass 0: dominance │
── Stage B (naive baseline):    │                        scoring + tiering│
   frequency-canonicalize        │  produces:                            │
   everything, no risk           │  flagged_for_manual_review.json       │
   awareness                     ▼  (MANUAL tier only)                  │
                          grammar_crossref.py            ── Pass 1       │
                                  │  produces:                            │
                                  │  manual_review_annotated.json         │
                                  ▼                                       │
                          lexical_subclass.py             ── Pass 2       │
                                  │  produces:                            │
                                  │  manual_review_final.json             │
                                  ▼                                       │
                          name_and_feminine_subclass.py   ── Pass 3       │
                                  │  produces:                            │
                                  │  manual_review_final2.json            │
                                  ▼                                       │
                          standardize_syriac_v2.py  ◄─────────────────────┘
                          ── Stage C (risk-aware standardizer): reads
                             BOTH the Stage A analysis JSON and the Pass 3
                             output, merges what's safe, skips what isn't,
                             and writes a full per-cluster decision log
```

`analyze_syriac_variants.py` is the shared starting point for every other
script. `standardize_syriac.py` (Stage B) and the classification pipeline
(Passes 0–3) are independent, parallel consumers of its output — Stage B
does not need the classification results, and Passes 0–3 do not need Stage
B's output. `standardize_syriac_v2.py` (Stage C) is the one script that
depends on *everything* upstream: it re-derives the same tiering as
`variant_insights.py` and reads Pass 3's category annotations to decide,
cluster by cluster, whether Stage B's "always merge" behavior is actually
appropriate.

Each script from `variant_insights.py` through `name_and_feminine_subclass.py`
is a **filter over the previous script's output**: it only touches clusters
that are still unclassified and leaves everything already tagged alone. This
means you can re-run any later script after editing its rules without
re-running the earlier ones, and you can insert new passes anywhere in the
chain by following the same pattern (read the previous JSON, skip anything
already classified, tag the rest, write a new JSON).

**Important:** `standardize_syriac.py` (Stage B) and `standardize_syriac_v2.py`
(Stage C) are two independent, complete standardizers — running one does
not require or affect the other, and neither modifies the original `.vert`
corpus (each writes its own new standardized copy). Stage C is the
risk-aware standardizer previously described in this README as future work;
it is now implemented (see Script C below) and is the recommended
standardizer to use going forward, with Stage B kept around as the naive
baseline for comparison.

---

## Prerequisites

- Python 3.6+, standard library only for all seven scripts (no `pip install`
  needed for any of them).
- `matplotlib` only if you use `variant_insights.py --chart` (`pip install
  matplotlib --break-system-packages` if missing).
- A `.vert`-format corpus is the true starting point (see Script A below for
  the format). Everything downstream of Script A works off the JSON it
  produces — no script in this pipeline needs to re-read the original
  corpus file except Script A itself (which only reads it), and Script B
  and Script C (the naive and risk-aware standardizers), which are the only
  two scripts that write out a new, rewritten corpus.

---

## A. `analyze_syriac_variants.py` — duplicate-cluster discovery

**Purpose:** scan a NoSketchEngine `.vert` corpus, extract every Syriac
token's consonantal skeleton (i.e., strip all vowel points, stress marks,
and the kashida/tatweel justification character), and group tokens that
share a skeleton into "duplicate clusters." This is the discovery step that
every other script in this set — both the naive standardizer and the
four-pass classification pipeline — is built on top of.

**Input:** a `.vert` file — one token per line, with SGML-style markup for
document/page boundaries and punctuation (`<doc ...>`, `<page no="...">`,
`<g/>`). Non-Syriac lines (tags, punctuation-glue markers, blank lines) are
skipped automatically; a line only counts as a token if `is_syriac()` finds
at least one character in the Syriac Unicode block (U+0700–U+074F).

**Output:** a JSON report (`--output`, or `<input_stem>_analysis.json` by
default) with this schema:

```json
{
  "summary": {
    "total_unique_words": 301960,
    "total_word_instances": 2975551,
    "potential_duplicate_clusters": 51858
  },
  "duplicates": [
    {
      "consonantal_base": "ܡܢ",
      "cluster_frequency": 35971,
      "num_variants": 12,
      "variants": [
        {"form": "ܡ̣ܢ", "frequency": 35937, "display": "ܡ̣ܢ"},
        {"form": "ܡ̣ـܢ", "frequency": 13, "display": "ܡ̣ـܢ"}
      ]
    }
  ]
}
```
`duplicates` only includes consonantal bases with **two or more** distinct
surface forms; a base with only one attested spelling is not "candidate
duplication" and is excluded (though it still counts toward
`total_unique_words`/`total_word_instances`). Within each cluster,
`variants` is sorted by frequency descending, so `variants[0]` is always the
most common surface form of that cluster. This is exactly the file consumed
by `variant_insights.py --input` downstream.

**How the consonantal base is computed (`get_syriac_base()`):** strips a
fixed set of ~40 Unicode combining characters — the inherited Arabic-style
vowel points and stress marks (U+064B–U+0670: fatha, damma, kasra, shadda,
sukun, maddah, hamza, superscript alef, etc.) and the Syriac-specific
combining diacritics (U+0730–U+074F: the pthaha/zqapha/rbasa/hbasa/esasa
vowel system, the feminine dot, the quššaya/rukkakha plosive/spirant
markers, and more), plus the kashida/tatweel justification character
(U+0640). **Note that it does *not* strip the seyame plural marker
(U+0308, COMBINING DIAERESIS)** — that mark is deliberately left in the base,
which is why plural and singular forms of the same noun end up in different
clusters rather than being merged together, and why `lexical_subclass.py`
downstream can use its presence as a plural-noun signal.

**Usage:**
```bash
python analyze_syriac_variants.py --input corpus.vert --output corpus_analysis.json
```
(`--output` is optional; if omitted, the script writes
`<input>_analysis.json` next to the input file.) Running with no arguments
prints a usage message and exits.

**Performance:** single-threaded, line-by-line streaming — no need to load
the whole corpus into memory beyond the accumulating frequency tables. On a
multi-million-token corpus, expect tens of seconds, not minutes.

**To extend:** the set of characters stripped in `get_syriac_base()` is a
plain Python `set` literal — if you find diacritics the script isn't
handling (e.g. a mark used in a different NENA dialect's transliteration
convention, or an OCR artifact character), add its Unicode code point there.
Remember that anything you add or remove here changes what counts as "the
same word" for every downstream script, including all four classification
passes and the naive standardizer, so re-run the whole pipeline after
editing it rather than patching outputs by hand.

---

## B. `standardize_syriac.py` — naive frequency-based standardizer ("Strategy 1")

**Purpose:** the baseline this whole project exists to improve on. For every
consonantal-base cluster with more than one surface form, pick the single
most frequent form as canonical and rewrite every other occurrence in the
corpus to match it. This is fast, simple, and — as the accompanying paper
argues — linguistically unsafe for a specific, identifiable, high-frequency
slice of clusters (closed-class morphology whose forms differ in real
grammatical content, not just spelling). It has **no awareness** of
dominance ratio, tiering, or grammatical paradigms; it treats every cluster
identically.

**Input:** a `.vert` corpus file (positional argument; typically the same
file you ran `analyze_syriac_variants.py` on — this script rebuilds its own
frequency table internally rather than reading the JSON report, so it does
not depend on Script A having been run first).

**Output:** two files (paths optional; auto-derived from the input filename
if omitted):
1. **Standardized `.vert` file** (`<input_stem>_standardized<ext>` by
   default) — same line-per-token format as the input, with every kashida
   character removed and every non-canonical variant rewritten to its
   cluster's most frequent form.
2. **Mapping JSON** (`<input_stem>_mapping.json` by default) — a flat
   `{"variant_form": "canonical_form", ...}` dictionary of every rewrite
   applied, e.g.:
   ```json
   {
     "ܗ݇ܘܵܐ": "ܗܵܘܹܐ",
     "ܠܹܐ": "ܠܵܐ"
   }
   ```
   This mapping is your audit trail — keep it alongside the standardized
   corpus. (Note: this is the naive mapping. It will contain exactly the
   linguistically risky merges the paper identifies, e.g. collapsing the
   NENA copula's past and participial forms into one "canonical" spelling —
   this file is a good place to look if you want concrete before/after
   examples of what Strategy 1 gets wrong.)

**Usage:**
```bash
python standardize_syriac.py corpus.vert corpus_standardized.vert corpus_mapping.json
# or, letting output paths default:
python standardize_syriac.py corpus.vert
```

**Processing steps (for reference/debugging):** (1) build a frequency table
by scanning the corpus once, stripping kashida from every token as it's
counted; (2) for each consonantal-base group with >1 surface form, pick
`max(forms, key=frequency)` as canonical and record every other form's
mapping; (3) stream through the corpus a second time, stripping kashida and
applying the mapping line-by-line, writing the result and printing progress
every 100,000 lines.

**Relationship to the classification pipeline:** this script and
`variant_insights.py` (Section 1 below) both start from the same
consonantal-base clustering logic but are **independent, parallel
consumers** of that idea — `standardize_syriac.py` recomputes its own
frequency table directly from the `.vert` file rather than reading
`analyze_syriac_variants.py`'s JSON, so the two can be run in either order
or in isolation. Nothing in Passes 0–3 modifies this script's output; they
exist to tell you *which* of this script's rewrites (recorded in its
mapping JSON) are trustworthy and which ones silently erase grammatical
distinctions. There is currently no "risk-aware" version of this script
that consults the tier/category annotations before deciding whether to
rewrite a cluster — building one is the natural next step and is called out
as future work in the paper.

**To extend:** if you build the risk-aware v2 mentioned above, the natural
integration point is step (2) above — instead of unconditionally picking
`max(forms, key=frequency)` for every cluster, look up the cluster's
`consonantal_base` in `manual_review_final2.json`'s tier/category
annotations first, and skip (or flag instead of silently rewriting) any
cluster that is MANUAL-tier and still has all four `*_category` fields
`null`, or that matched `copula_or_to_be_paradigm` / `passive_or_remain_piš`
/ `pronominal_suffix` specifically (the categories where "canonical form"
isn't a coherent concept at all, since the variants are different
grammatical words).

---

## 1. `variant_insights.py` — dominance scoring & merge-safety tiering

**Purpose:** quantify how much of the corpus's apparent duplication is
formatting noise vs. genuine diacritic variation, and flag which clusters
are risky to canonicalize by frequency alone.

**Input:** the `analyze_syriac_variants.py` report (`--input`).

**Output:**
- stdout: a JSON summary (kashida-only vs. genuine-variation split, Pareto
  concentration, tier sizes, base-length correlation) plus a printed list of
  the top 15 MANUAL-tier clusters.
- `--chart <path.png>` (optional): a 4-panel PNG — variants-per-cluster
  histogram, dominance-ratio distribution, cumulative concentration curve,
  base-length vs. average-variant-count.
- `--export-review <path.json>` (optional): the **full list of MANUAL-tier
  clusters**, sorted by impact. This file is the input to
  `grammar_crossref.py`. Each entry looks like:

```json
{
  "consonantal_base": "ܗܘܐ",
  "cluster_frequency": 31623,
  "dominance": 0.563,
  "variants": [["ܗ݇ܘܵܐ", 17797], ["ܗܵܘܹܐ", 5135], ["...", 0]]
}
```

**Key concept — dominance ratio:**
```
dominance(cluster) = max(variant frequencies) / cluster_frequency
```
The share of a cluster's total token frequency held by its single most
common variant. Close to 1.0 → one form overwhelmingly predominates (safe to
canonicalize). Low (spread across several forms) → no conventionalized
spelling to converge on, which for a high-frequency cluster is a strong
signal of genuine morphological alternation rather than noise.

**Tiering rule** (see `classify()` in the script):
| Tier | Condition |
|---|---|
| `SAFE_AUTO` | kashida-only cluster, OR all non-top variants have frequency ≤3, OR dominance ≥0.85 |
| `MANUAL` | cluster_frequency ≥50 AND dominance <0.75 |
| `REVIEW` | everything else |

**Usage:**
```bash
python variant_insights.py --input corpus_analysis.json \
    --chart insights_chart.png \
    --export-review flagged_for_manual_review.json
```

**To extend/tune:** the thresholds (`0.85`, `0.75`, cluster-frequency `50`,
noise-tail `3`) are the four numbers most worth revisiting first if you find
the tiers too aggressive or too conservative on a different corpus — they
live entirely inside `classify()`.

---

## 2. `grammar_crossref.py` — grammatical paradigm cross-reference (Pass 1)

**Purpose:** check whether a MANUAL-tier cluster's consonantal base matches
a known NENA closed-class morphological paradigm (copula/"to be", *piš-*
passive, pronominal suffixes, negation, numeral "one"). A match is strong
evidence the cluster's variants are different grammatical forms, not
spelling noise.

**Input:** `flagged_for_manual_review.json` (from `variant_insights.py`).

**Output:**
- stdout: a table of category → cluster count → instance count → example
  bases, plus the top 20 clusters that *still* don't match anything.
- `--export <path.json>`: every input cluster, each with two new fields:
  `grammar_category` (string or `null`) and `grammar_note` (the human-
  readable justification for the match, or `null`).

**How matching works:** `ROOT_CATEGORIES` at the top of the file is a plain
Python list of `(category_name, [roots], explanation)` tuples. A cluster's
`consonantal_base` matches a category if it **ends with** one of that
category's root strings — suffix matching (not exact-equality) because
Aramaic proclitics (`ܕ` d-, `ܘ` w-, `ܒ` b-, `ܠ` l-) attach to the *front* of
a root, so `ܕܝܗܘܐ` ("that was") still needs to match the root `ܝܗܘܐ`. Roots
are checked longest-first so e.g. `ܘܠܐ` is tried before the shorter `ܠܐ`.

**Current categories** (see the script for the full root lists):
`copula_or_to_be_paradigm`, `passive_or_remain_piš`, `pronominal_suffix`,
`negation_particle`, `numeral_one`.

**Usage:**
```bash
python grammar_crossref.py --input flagged_for_manual_review.json \
    --export manual_review_annotated.json
```

**To extend:** add a new `(category, [roots], note)` tuple to
`ROOT_CATEGORIES`. No other code changes needed — `_FLAT` and the matching
loop are generated from that list automatically. Good candidates for new
entries (see the paper's Future Work section): demonstrative gender pairs
(masc/fem "that"), additional prepositions with pronominal suffixes, and
aspectual particles.

**Caveat:** this is a heuristic built from general NENA descriptive grammar
(Khan 2008, 2011, 2016 — see the paper's References), not validated against
this specific corpus's dialect by a NENA specialist. Treat matches as a
strong prior, not ground truth.

---

## 3. `lexical_subclass.py` — lexical / phonetic sub-classification (Pass 2)

**Purpose:** for clusters `grammar_crossref.py` couldn't explain, check for
structural markers that indicate ordinary (non-paradigmatic) phonetic or
dialectal variation on a regular noun/adjective/particle — lower risk than
noise, since no tense/person/gender information is at stake, but not
presumed identical to the "safe" grammar-paradigm case either.

**Input:** `manual_review_annotated.json` (from `grammar_crossref.py`). Only
clusters where `grammar_category` is `null` are processed; everything else
is passed through unchanged.

**Output:** `--export <path.json>` — every cluster, with two more fields
added for previously-unclassified entries: `lexical_category` and
`lexical_note`.

**Signals used, in order:**
1. **Seyame** (`\u0308`, the Syriac plural-marker combining diaeresis)
   present in the base → `plural_noun_phonetic`.
2. A short closed list (`LEXICAL_ROOTS`) of specific high-frequency items:
   the "before/first" root family → `ordinal_before_root`; the
   interrogatives "what"/"how" → `interrogative_particle`; the distal
   demonstrative "that/he" → `demonstrative_pronoun`.
3. Derivational suffix `-ܝܬܐ` (-ita) or `-ܝܐ` (-aya) → `adjectival_or_ordinal_ending`.

**Usage:**
```bash
python lexical_subclass.py --input manual_review_annotated.json \
    --export manual_review_final.json
```

**To extend:** add entries to `LEXICAL_ROOTS` the same way as
`ROOT_CATEGORIES` in `grammar_crossref.py`, or add another `if
base.endswith(...)` branch in `sub_classify()` for a new derivational
pattern. Deliberately **not** included here: the plain feminine `-ܬܐ`
ending (too broad/common to mix into this tier — see script 4) and proper
nouns (need a name list, not a suffix rule — also script 4).

---

## 4. `name_and_feminine_subclass.py` — proper nouns & plain feminine nouns (Pass 3)

**Purpose:** catch two more explainable patterns among whatever Pass 1 and
Pass 2 still left ambiguous: (a) proper nouns/place names, where variation
is pure transliteration/orthography choice, not grammar or lexical
phonology; and (b) the plain Aramaic feminine `-ta` noun ending, kept as its
**own** tier rather than folded into `adjectival_or_ordinal_ending` because
it's a much broader, less specific pattern and deserves its own honesty
label rather than diluting a more precise category.

**Input:** `manual_review_final.json` (from `lexical_subclass.py`). Only
clusters where both `grammar_category` and `lexical_category` are `null`
are processed.

**Output:** `--export <path.json>` — every cluster, with
`name_or_feminine_category` and `name_or_feminine_note` added for
newly-classified entries.

**Signals used:**
1. `PROPER_NOUN_ROOTS` — a **short seed list** (13 entries as shipped:
   `ܝܘܚܢܢ` John, `ܐܘܪܡܝ` Urmia, `ܩܛܝܣܦܘܢ` Ctesiphon, `ܣܠܝܩ` Seleucia, `ܐܫܘܪ`
   Ashur/Assyria, `ܐܘܪܗܝ` Edessa, `ܢܨܝܒܝܢ` Nisibis, `ܦܪܬ` Euphrates, `ܕܩܠܬ`
   Tigris, `ܡܪܝܡ` Mary, `ܐܒܪܗܡ` Abraham, `ܡܘܫܐ` Moses, `ܕܘܝܕ` David),
   matched exactly or with a proclitic (`ܕ`/`ܘ`/`ܒ`/`ܠ`) or the "Mar"
   (`ܡܪܝ`) honorific prefix stripped.
2. Base ends with plain `ܬܐ` (not `ܝܬܐ`/`ܝܐ`, which Pass 2 already
   claimed) → `feminine_noun_ta_ending`.

**Usage:**
```bash
python name_and_feminine_subclass.py --input manual_review_final.json \
    --export manual_review_final2.json
```

**To extend — this is the highest-value place to add corpus-specific
knowledge:** `PROPER_NOUN_ROOTS` is explicitly a seed list, not a gazetteer.
If you have (or can extract, e.g. from capitalization conventions in a
transliteration, a named-entity list, or manual annotation) an actual list
of proper nouns attested in your corpus, drop them into this list — it is
the single easiest lever to pull for improving coverage of the remaining
ambiguous residual, since proper-noun variation is orthographic rather than
linguistic and therefore comparatively low-risk to canonicalize once
identified.

**Caveat:** unlike the grammar paradigms in Pass 1, neither signal here is
presumed "safe." An ordinary noun's spelling variants are plausible but not
guaranteed to be mere pronunciation differences — treat both categories as
"probably fine, worth a spot check" rather than "confirmed noise."

---

## C. `standardize_syriac_v2.py` — risk-aware standardizer

**Purpose:** the risk-aware successor to `standardize_syriac.py`. Instead of
canonicalizing every cluster to its most frequent form unconditionally, it
re-derives each cluster's merge-safety tier (the same logic as
`variant_insights.py`) and, for MANUAL-tier clusters, looks up the
grammatical/lexical/name category assigned by Passes 1–3 to decide whether
merging is appropriate — then writes out both the standardized corpus *and*
a full per-cluster decision log explaining every merge and every skip.

**Inputs:**
1. `--input` — the original `.vert` corpus (same file `analyze_syriac_variants.py`
   was run on).
2. `--analysis` — the `analyze_syriac_variants.py` output JSON (Script A).
   Required: this is what lets the script recompute dominance/tier for
   *every* cluster, not just the MANUAL-tier ones.
3. `--manual-review` — the final classification output (`manual_review_final2.json`
   from Pass 3, or any earlier pass's output if you want to stop partway
   through the classification pipeline). **Optional** — if omitted, every
   MANUAL-tier cluster is treated as if no category had been matched (see
   the policy table below), which is the conservative fallback.

**Outputs:**
1. **Standardized `.vert` file** (`--output`, default
   `<input_stem>_standardized_v2<ext>`) — same format as Script B's output,
   but only rewriting the clusters the policy decided were safe to merge.
2. **Mapping JSON** (`--mapping`, default `<input_stem>_mapping_v2.json`) —
   same flat `{"variant": "canonical", ...}` format as Script B, but only
   containing entries for clusters that were actually merged.
3. **Decision log** (`--decisions`, default `<input_stem>_decisions_v2.json`)
   — the audit trail: **every** cluster from the analysis JSON (all 51,858
   on the reference corpus, not just the merged ones), with its tier,
   dominance, matched category (if any), the merge/skip decision, and a
   human-readable reason string:
   ```json
   {
     "consonantal_base": "ܗܘܐ",
     "cluster_frequency": 31623,
     "dominance": 0.563,
     "tier": "MANUAL",
     "category": "copula_or_to_be_paradigm",
     "decision": "skip",
     "canonical_form": null,
     "reason": "MANUAL tier, high-risk category 'copula_or_to_be_paradigm': variants are different grammatical forms, not spelling variants"
   }
   ```

**Decision policy** (each stage independently overridable via CLI flag):

| Tier | Category | Default decision | CLI flag |
|---|---|---|---|
| SAFE_AUTO | — | **merge** (always) | — |
| REVIEW | — | merge | `--review-policy {merge,skip}` |
| MANUAL | `copula_or_to_be_paradigm` or `passive_or_remain_piš` (`HIGH_RISK_CATEGORIES`) | **skip** | `--manual-high-risk-policy {merge,skip}` |
| MANUAL | any other matched category | merge | `--manual-moderate-policy {merge,skip}` |
| MANUAL | no category matched (or `--manual-review` omitted) | **skip** | `--manual-unresolved-policy {merge,skip}` |

The reasoning behind the two conservative ("skip") defaults: the two
high-risk categories are cases where a single consonantal-base cluster
genuinely contains more than one grammatical word (e.g. `ܗܘܐ`'s past-tense
and participial forms of "to be") — there is no coherent "canonical form" to
collapse to, so the safest default is to leave every surface form as-is.
Unresolved MANUAL-tier clusters are, by definition, cases the heuristic
pipeline couldn't explain at all — merging them by default would silently
reintroduce exactly the risk this whole pipeline exists to avoid, so the
conservative default is also skip. The other MANUAL categories (pronominal
suffixes, negation, numerals, plural nouns, adjectival/ordinal endings,
interrogatives, demonstratives, proper nouns, plain feminine nouns) each
denote a **single** lexical item whose variants are plausible spelling
differences rather than competing grammatical readings, so merging is the
default there — but every such merge is still individually logged, since
"plausible" is not a guarantee.

Kashida (U+0640) is stripped from every token regardless of merge decision
— that cleanup is orthographically uncontroversial (Section 5.2 of the
paper: kashida-only clusters are 0.5% of clusters / 0.1% of instances, and
stripping it never touches a grammatical distinction).

**Usage:**
```bash
python standardize_syriac_v2.py \
    --input corpus.vert \
    --analysis syriac_variants_analysis.json \
    --manual-review manual_review_final2.json \
    --output corpus_standardized_v2.vert \
    --mapping corpus_mapping_v2.json \
    --decisions corpus_decisions_v2.json
```
Running it on the reference corpus produces, per the printed decision
summary:
```
=== DECISION SUMMARY (clusters) ===
  SAFE_AUTO   merged= 43165  skipped=     0
  REVIEW      merged=  6501  skipped=     0
  MANUAL      merged=   793  skipped=  1399
```
i.e. of the 2,192 MANUAL-tier clusters, 793 (the ones matched to a
non-high-risk category) get merged and 1,399 (high-risk-category matches
plus the still-unresolved residual) are left untouched in the output
corpus — exactly the set the paper argues should not be collapsed by
frequency alone.

**To experiment with looser/stricter policies**, override any of the four
flags independently, e.g. to also merge the still-unresolved residual
(accepting more risk in exchange for a cleaner corpus):
```bash
python standardize_syriac_v2.py --input corpus.vert --analysis corpus_analysis.json \
    --manual-review manual_review_final2.json \
    --manual-unresolved-policy merge
```
or to be maximally conservative and skip everything in the MANUAL tier
regardless of category:
```bash
python standardize_syriac_v2.py --input corpus.vert --analysis corpus_analysis.json \
    --manual-moderate-policy skip
```

**Relationship to `standardize_syriac.py` (Stage B):** both scripts produce
a mapping JSON and a rewritten `.vert` file in the same formats, so you can
diff Stage B's mapping against Stage C's mapping (or against Stage C's full
decision log) to see exactly which of Stage B's rewrites were judged
risky and excluded. This is the concrete way to answer "what would the naive
approach have gotten wrong on my corpus?" for a specific dataset.

**To extend:** the `HIGH_RISK_CATEGORIES` set near the top of the file is
the main lever — if you add a new grammar-paradigm category to
`grammar_crossref.py` that has the same "multiple grammatical readings
share one consonantal base" property as the copula/*piš-* paradigms, add its
name to this set too so Stage C treats it with the same caution. The
tiering constants (`SAFE_AUTO_DOMINANCE`, `MANUAL_MIN_FREQUENCY`,
`MANUAL_MAX_DOMINANCE`, `NOISE_TAIL_MAX_FREQ`) are intentionally duplicated
from `variant_insights.py` rather than imported, so this script stays
runnable on its own — if you tune the thresholds in one file, mirror the
change in the other.

---

## Cumulative data schema

After running all four scripts, each object in `manual_review_final2.json`
has this shape (fields are additive across passes; `null` means "not
matched at this pass"):

```json
{
  "consonantal_base": "ܝܘܚܢܢ",
  "cluster_frequency": 1454,
  "dominance": 0.71,
  "variants": [["ܝܘܼܚܲܢܵܢ", 1030], ["ܝܘܿܚܲܢܵܢ", 424]],
  "grammar_category": null,
  "grammar_note": null,
  "lexical_category": null,
  "lexical_note": null,
  "name_or_feminine_category": "proper_noun_heuristic",
  "name_or_feminine_note": "matches a seed proper-noun/place-name root ..."
}
```

A cluster with all four `*_category` fields `null` is in the final
unclassified residual — the actual candidate list for direct human
(ideally native-speaker or NENA-specialist) review.

---

## End-to-end example

```bash
# Stage A: discover duplicate clusters from the raw corpus
python analyze_syriac_variants.py \
    --input corpus.vert \
    --output syriac_variants_analysis.json

# Stage B (optional, independent, naive baseline): frequency-canonicalize
# everything with no risk awareness -- run this if/when you just want a
# quick-and-dirty standardized corpus and are OK with the tradeoffs the
# paper describes. Not required for, and not required by, Passes 0-3 below.
python standardize_syriac.py corpus.vert corpus_standardized.vert corpus_mapping.json

# Pass 0: score and tier every cluster, export the MANUAL tier
python variant_insights.py \
    --input syriac_variants_analysis.json \
    --chart variant_insights_chart.png \
    --export-review flagged_for_manual_review.json

# Pass 1: grammatical paradigms
python grammar_crossref.py \
    --input flagged_for_manual_review.json \
    --export manual_review_annotated.json

# Pass 2: lexical/phonetic patterns
python lexical_subclass.py \
    --input manual_review_annotated.json \
    --export manual_review_final.json

# Pass 3: proper nouns + plain feminine nouns
python name_and_feminine_subclass.py \
    --input manual_review_final.json \
    --export manual_review_final2.json

# Stage C: risk-aware standardization, using both the Stage A analysis and
# the finished Pass 3 classification to decide what's actually safe to merge
python standardize_syriac_v2.py \
    --input corpus.vert \
    --analysis syriac_variants_analysis.json \
    --manual-review manual_review_final2.json \
    --output corpus_standardized_v2.vert \
    --mapping corpus_mapping_v2.json \
    --decisions corpus_decisions_v2.json
```

On the reference corpus (2,975,551 tokens / 301,960 types / 51,858
duplicate clusters), Stage B alone collapses the type count from 301,960 to
196,541 (−34.9%) with ~12.6% of corpus lines rewritten — but with no
indication of which of those rewrites are safe. Passes 0–3 instead resolve:

| Stage | Clusters left unresolved | Instances left unresolved |
|---|---|---|
| Start (MANUAL tier) | 2,192 | 656,846 (22.1% of corpus) |
| After Pass 1 (grammar) | 2,029 | 401,450 |
| After Pass 2 (lexical) | 1,524 | 289,117 |
| After Pass 3 (name/feminine) | **1,355** | **254,484** |

i.e. 61.3% of the highest-risk tier's token instances now have an
identified explanation, and the final human-review workload (1,355
clusters) is about 38x smaller than the original 51,858-cluster candidate
list. Stage C then acts on this directly: with its default policy, of the
2,192 MANUAL-tier clusters it merges the 793 matched to a non-high-risk
category and leaves the other 1,399 (the two high-risk grammar paradigms,
plus every still-unresolved cluster) untouched in the output corpus — so
you no longer need to manually cross-reference Stage B's mapping file
against the classification results; Stage C's own decision log *is* that
cross-reference, already made and already justified per cluster.

---

## General notes for future maintainers

- **Every script is read-only with respect to its input JSON** — none of
  them overwrite the file you pass to `--input`. Always pass a new
  `--export`/`--chart`/`--export-review` path.
- **Order matters and is enforced by content, not by code**: each script
  only processes clusters whose relevant category field(s) are still
  `null`. If you re-run an earlier pass after editing it, re-run every
  later pass afterward too so the `null` filtering stays consistent.
- **All matching is on `consonantal_base`**, i.e. after diacritics have
  already been stripped by `analyze_syriac_variants.py`'s
  `get_syriac_base()`. If you change what counts as a "diacritic" upstream
  (e.g. start stripping or keeping the seyame mark differently), every
  downstream root list in these four scripts should be re-checked, since
  `lexical_subclass.py`'s seyame detection in particular depends on it
  still being present in the base.
- **None of the four scripts require corpus access** — they operate purely
  on the frequency-count JSON, not the original `.vert` file, so they're
  cheap to re-run repeatedly while tuning rules.
- **The heuristic root/suffix lists in all three cross-reference passes are
  the intended extension point.** They are plain Python lists/tuples at the
  top of each file specifically so they can be edited without touching the
  matching logic. If you build a validated gold-standard evaluation set
  (see the paper's Future Work section), the natural next step is turning
  these heuristics into something measurable (precision/recall per
  category) rather than coverage-only percentages.
