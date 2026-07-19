#!/usr/bin/env python3
"""
grammar_crossref.py
Cross-references the MANUAL-tier ("real grammar, not noise") cluster list from
variant_insights.py against known Northeastern Neo-Aramaic (Sureth) closed-class
morphology: the copula / "to be" paradigm, the piš- passive-remain auxiliary,
pronominal suffixes on prepositions, the negation particle, and the "one" numeral.

IMPORTANT CAVEAT: the root/pattern list below is a heuristic built from general
NENA grammar (Khan-style descriptions of the copula and preterite/participle
system), not a verified morphological analyzer for this specific corpus's
dialect or transliteration conventions. Treat "matched" categories as a strong
prior, not ground truth -- and treat "unclassified" as "still needs a human,"
not "definitely noise." Extend ROOT_CATEGORIES as you confirm/correct entries.

Usage:
    python grammar_crossref.py --input flagged_for_manual_review.json --export annotated.json
"""
import argparse
import json
from collections import Counter, defaultdict

# (category, [roots], note) -- checked longest-root-first, matched by SUFFIX
# because Aramaic proclitics (d-, w-, b-, l-) attach to the FRONT of the root.
ROOT_CATEGORIES = [
    ("copula_or_to_be_paradigm", [
        "ܗܘܝܐ", "ܝܗܘܘ", "ܝܗܘܐ", "ܗܘܐ", "ܗܘܘ", "ܝܠܐ", "ܝܘܢ", "ܝܘܚ", "ܝܘܬ",
    ], "enclitic copula (-ile/-ila/-iwan/-iwax/-iwat) and the h-w-y 'to be' "
       "root across preterite/participle stems -- these are different tense/"
       "person/gender forms of the SAME grammatical paradigm, not spelling "
       "variants of one word."),
    ("passive_or_remain_piš", [
        "ܦܝܫܐ", "ܦܝܫ", "ܦܫܠܐ",
    ], "the piš- 'remain/become' auxiliary used to form the NENA passive; "
       "variants here often mark participle vs. preterite forms."),
    ("pronominal_suffix", [
        "ܠܗܘܢ", "ܡܢܝ", "ܥܠܝ", "ܩܬܝ", "ܥܡܝ", "ܒܝܝ", "ܕܝܝ", "ܓܢܝ", "ܐܢܐ",
    ], "preposition/pronoun + 1st-person or 3rd-plural object suffix -- "
       "different grammatical persons sharing a base, not noise."),
    ("negation_particle", [
        "ܘܠܐ", "ܠܐ",
    ], "negation particle la/le -- plausibly a real dialectal split rather "
       "than an error, but not verb morphology."),
    ("numeral_one", [
        "ܚܕܟܡܐ", "ܕܚܕ", "ܒܚܕ", "ܠܚܕ", "ܘܚܕ", "ܚܕ",
    ], "the numeral/quantifier 'one' (ḥad) and its cliticized forms."),
]

# sort all (root, category, note) longest-root-first so e.g. ܘܠܐ is tried
# before the shorter ܠܐ
_FLAT = []
for cat, roots, note in ROOT_CATEGORIES:
    for r in roots:
        _FLAT.append((r, cat, note))
_FLAT.sort(key=lambda x: -len(x[0]))


def classify_base(base):
    for root, cat, note in _FLAT:
        if base.endswith(root):
            return cat, note
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="flagged_for_manual_review.json")
    ap.add_argument("--export", help="path to save the fully annotated list")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        flagged = json.load(f)

    cat_counts = Counter()
    cat_instance_totals = Counter()
    by_category = defaultdict(list)
    unclassified = []

    for c in flagged:
        cat, note = classify_base(c["consonantal_base"])
        if cat:
            c["grammar_category"] = cat
            c["grammar_note"] = note
            cat_counts[cat] += 1
            cat_instance_totals[cat] += c["cluster_frequency"]
            by_category[cat].append(c)
        else:
            c["grammar_category"] = None
            unclassified.append(c)

    total_instances = sum(c["cluster_frequency"] for c in flagged)
    classified_instances = sum(cat_instance_totals.values())

    print("=== MANUAL-tier clusters cross-referenced against known NENA morphology ===")
    print(f"Total MANUAL-tier clusters: {len(flagged)}  ({total_instances} instances)\n")

    print(f"{'category':30s} {'clusters':>9s} {'instances':>10s}  example bases")
    for cat, _, _ in ROOT_CATEGORIES:
        n = cat_counts[cat]
        inst = cat_instance_totals[cat]
        examples = sorted(by_category[cat], key=lambda x: -x["cluster_frequency"])[:4]
        ex_str = ", ".join(e["consonantal_base"] for e in examples)
        print(f"{cat:30s} {n:9d} {inst:10d}  {ex_str}")

    n_unclass = len(unclassified)
    inst_unclass = total_instances - classified_instances
    print(f"{'UNCLASSIFIED (needs manual look)':30s} {n_unclass:9d} {inst_unclass:10d}")

    print(f"\n{classified_instances}/{total_instances} instances "
          f"({classified_instances/total_instances*100:.1f}%) matched a known "
          f"grammatical paradigm rather than being unexplained 'balanced noise'.")

    print("\n=== Top 20 still-UNCLASSIFIED clusters by impact (genuinely need a human) ===")
    for c in sorted(unclassified, key=lambda x: -x["cluster_frequency"])[:20]:
        forms = ", ".join(f"{v[0]}({v[1]})" for v in c["variants"][:4])
        print(f"  {c['consonantal_base']}  freq={c['cluster_frequency']}  "
              f"dominance={c['dominance']}  [{forms}]")

    if args.export:
        with open(args.export, "w", encoding="utf-8") as f:
            json.dump(flagged, f, ensure_ascii=False, indent=2)
        print(f"\nFull annotated list saved to {args.export}")


if __name__ == "__main__":
    main()
