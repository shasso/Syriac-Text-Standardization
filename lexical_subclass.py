#!/usr/bin/env python3
"""
lexical_subclass.py
Second pass over manual_review_annotated.json: for clusters that grammar_crossref.py
could NOT tie to a copula/piš-/pronoun-suffix/negation/numeral paradigm, tag the
ones that look like plain phonetic/dialectal variation on an ordinary noun or
adjective (lower risk: no tense/person/gender information at stake) versus the
remainder that still needs an actual human look.

Heuristics used (all checkable against the base string itself):
  - SEYAME (the two dots ecombining mark, U+0308, written over a letter) marks
    a plural noun in Syriac orthography. If present, the cluster is variation
    on an already-identified plural noun -- phonetic, not grammatical.
  - "-ܝܐ" / "-ܝܬܐ" endings are the adjectival/ordinal derivational suffixes
    (-aya masc / -ita fem-ordinal), e.g. qadmaya "first", qadmita "first-fem".
  - A short hand list of high-frequency closed-class items observed in this
    corpus's MANUAL tier: the "before/first" (qdam) root family, the two
    interrogatives "what" / "how", and the distal demonstrative "that/he".

CAVEAT: same as grammar_crossref.py -- this is a heuristic aid for triage,
not a verified morphological analysis. Spot-check before trusting it fully.

Usage:
    python lexical_subclass.py --input manual_review_annotated.json --export final.json
"""
import argparse
import json
from collections import Counter, defaultdict

SEYAME = "\u0308"  # combining diaeresis used as the Syriac plural marker

LEXICAL_ROOTS = [
    ("ordinal_before_root", ["ܩܕܡܝܬܐ", "ܩܕܡܝܐ", "ܩܕܡ"],
     "the 'before/first' (qdam) root and its ordinal/adjectival derivatives -- "
     "a lexical family, not an inflectional paradigm."),
    ("interrogative_particle", ["ܡܘܕܝ", "ܕܐܟܝ"],
     "interrogative particle ('what' / 'how') -- fixed function word; "
     "variation is dialectal pronunciation, not inflection."),
    ("demonstrative_pronoun", ["ܗܘ"],
     "distal demonstrative / 3rd person pronoun 'that, he' -- single form "
     "here (its feminine counterpart isn't in this cluster), so likely just "
     "phonetic variation rather than paradigm confusion."),
]
_LEX_FLAT = sorted(
    ((r, c, n) for c, roots, n in LEXICAL_ROOTS for r in roots),
    key=lambda x: -len(x[0]),
)


def sub_classify(base):
    if SEYAME in base:
        return "plural_noun_phonetic", (
            "base carries the seyame (plural) mark -- variation is vowel/"
            "pronunciation differences on an already-plural noun, not a "
            "change in grammatical category.")
    for root, cat, note in _LEX_FLAT:
        if base.endswith(root):
            return cat, note
    if base.endswith("ܝܬܐ"):
        return "adjectival_or_ordinal_ending", (
            "'-ita' feminine adjectival/ordinal derivational ending.")
    if base.endswith("ܝܐ"):
        return "adjectival_or_ordinal_ending", (
            "'-aya' adjectival/gentilic/ordinal derivational ending.")
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="manual_review_annotated.json")
    ap.add_argument("--export", help="path to save the final fully-annotated list")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        clusters = json.load(f)

    lex_counts, lex_instances = Counter(), Counter()
    by_lex = defaultdict(list)
    still_ambiguous = []

    already_classified = 0
    already_instances = 0

    for c in clusters:
        if c.get("grammar_category"):
            already_classified += 1
            already_instances += c["cluster_frequency"]
            continue
        cat, note = sub_classify(c["consonantal_base"])
        c["lexical_category"] = cat
        c["lexical_note"] = note
        if cat:
            lex_counts[cat] += 1
            lex_instances[cat] += c["cluster_frequency"]
            by_lex[cat].append(c)
        else:
            still_ambiguous.append(c)

    total = sum(c["cluster_frequency"] for c in clusters)

    print("=== Sub-classification of the remaining (non-paradigm-matched) clusters ===\n")
    print(f"{'category':30s} {'clusters':>9s} {'instances':>10s}  example bases")
    print(f"{'[already grammar-matched]':30s} {already_classified:9d} {already_instances:10d}")
    for cat, _, _ in LEXICAL_ROOTS + [("plural_noun_phonetic", None, None),
                                       ("adjectival_or_ordinal_ending", None, None)]:
        if cat not in lex_counts and cat != "plural_noun_phonetic" and cat != "adjectival_or_ordinal_ending":
            continue
        n = lex_counts[cat]
        inst = lex_instances[cat]
        examples = sorted(by_lex[cat], key=lambda x: -x["cluster_frequency"])[:4]
        ex_str = ", ".join(e["consonantal_base"] for e in examples)
        print(f"{cat:30s} {n:9d} {inst:10d}  {ex_str}")

    n_amb = len(still_ambiguous)
    inst_amb = total - already_instances - sum(lex_instances.values())
    print(f"{'STILL AMBIGUOUS (needs a human)':30s} {n_amb:9d} {inst_amb:10d}")

    covered = already_instances + sum(lex_instances.values())
    print(f"\n{covered}/{total} instances ({covered/total*100:.1f}%) now have "
          f"either a grammatical or lexical explanation.")

    print("\n=== Top 20 STILL-AMBIGUOUS clusters by impact ===")
    for c in sorted(still_ambiguous, key=lambda x: -x["cluster_frequency"])[:20]:
        forms = ", ".join(f"{v[0]}({v[1]})" for v in c["variants"][:4])
        print(f"  {c['consonantal_base']}  freq={c['cluster_frequency']}  "
              f"dominance={c['dominance']}  [{forms}]")

    if args.export:
        with open(args.export, "w", encoding="utf-8") as f:
            json.dump(clusters, f, ensure_ascii=False, indent=2)
        print(f"\nFull final annotated list saved to {args.export}")


if __name__ == "__main__":
    main()
