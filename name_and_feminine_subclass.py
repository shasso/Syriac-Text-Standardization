#!/usr/bin/env python3
"""
name_and_feminine_subclass.py
Third pass over the MANUAL-tier list (after grammar_crossref.py and
lexical_subclass.py). Targets clusters that are STILL unclassified and tags:

  1. proper_noun_heuristic -- consonantal base matches (allowing for a
     proclitic d-/w-/b-/l- or the honorific "Mar" prefix) a short seed list
     of proper names/places attested in this genre of Syriac Christian
     historiography. Proper-noun variation is pure orthography/transliteration
     choice, not grammar OR regular lexical phonology -- a third distinct
     category from the previous two passes.
  2. feminine_noun_ta_ending -- base ends in the plain "-ta" feminine noun
     suffix (Aramaic feminine absolute-state marker), a broad, extremely
     common Aramaic nominal pattern. Kept as its OWN tier rather than folded
     into "adjectival_or_ordinal_ending" (which is specifically the -aya/-ita
     derivational suffixes) because plain feminine nouns are a much larger
     and less specific class -- flagging them separately keeps the signal
     honest instead of diluting a more precise category.

CAVEAT (same as previous passes): the proper-noun seed list is short,
hand-built from general knowledge of this text genre (Assyrian Church
history: biblical/historical figures, Mesopotamian place names), and is
almost certainly incomplete for this specific corpus. Treat matches as a
lead to verify, and treat the -ta suffix tier as "probably a noun, still
worth a spot check" rather than confirmed-safe -- unlike the closed-class
grammar paradigms in pass 1, an ordinary noun's variants are not guaranteed
to be mere pronunciation differences.

Usage:
    python name_and_feminine_subclass.py --input manual_review_final.json --export final2.json
"""
import argparse
import json
from collections import Counter, defaultdict

# Seed list of proper names / places plausible in Syriac Christian
# historiography (e.g. a history of the Church of the East). Extend this
# list with names actually attested in your corpus -- this is a starting
# point, not a gazetteer.
PROPER_NOUN_ROOTS = [
    "ܝܘܚܢܢ",   # Yohannan / John
    "ܐܘܪܡܝ",   # Urmia
    "ܩܛܝܣܦܘܢ",  # Ctesiphon
    "ܣܠܝܩ",    # Seleucia
    "ܐܫܘܪ",    # Ashur / Assyria
    "ܐܘܪܗܝ",   # Edessa
    "ܢܨܝܒܝܢ",  # Nisibis
    "ܦܪܬ",     # Euphrates
    "ܕܩܠܬ",    # Tigris
    "ܡܪܝܡ",    # Maryam / Mary
    "ܐܒܪܗܡ",   # Abraham
    "ܡܘܫܐ",    # Moses
    "ܕܘܝܕ",    # David
]
# proclitics/honorific that can precede a proper name
_PREFIXES = ["ܕ", "ܘ", "ܒ", "ܠ", "ܡܪܝ"]

_PROPER_FLAT = sorted(PROPER_NOUN_ROOTS, key=lambda x: -len(x))


def is_proper_noun(base):
    for root in _PROPER_FLAT:
        if base == root:
            return True
        for pre in _PREFIXES:
            if base == pre + root:
                return True
    return False


def sub_classify(base):
    if is_proper_noun(base):
        return "proper_noun_heuristic", (
            "matches a seed proper-noun/place-name root (with or without a "
            "d-/w-/b-/l- proclitic or 'Mar' honorific) -- variation here is "
            "orthographic/transliteration choice, not grammar or regular "
            "lexical phonology.")
    if base.endswith("ܬܐ"):
        return "feminine_noun_ta_ending", (
            "plain Aramaic feminine absolute-state '-ta' noun ending -- a "
            "broad, common nominal pattern; likely dialectal/phonetic "
            "variation but NOT presumed safe the way closed-class grammar "
            "paradigms are -- spot-check before auto-merging.")
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="manual_review_final.json")
    ap.add_argument("--export", help="path to save the final annotated list")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        clusters = json.load(f)

    already, already_inst = 0, 0
    new_counts, new_inst = Counter(), Counter()
    by_cat = defaultdict(list)
    still_ambiguous = []

    for c in clusters:
        if c.get("grammar_category") or c.get("lexical_category"):
            already += 1
            already_inst += c["cluster_frequency"]
            continue
        cat, note = sub_classify(c["consonantal_base"])
        c["name_or_feminine_category"] = cat
        c["name_or_feminine_note"] = note
        if cat:
            new_counts[cat] += 1
            new_inst[cat] += c["cluster_frequency"]
            by_cat[cat].append(c)
        else:
            still_ambiguous.append(c)

    total = sum(c["cluster_frequency"] for c in clusters)

    print("=== Third pass: proper-noun heuristic + plain feminine '-ta' ending ===\n")
    print(f"{'category':30s} {'clusters':>9s} {'instances':>10s}  example bases")
    print(f"{'[already classified, pass 1+2]':30s} {already:9d} {already_inst:10d}")
    for cat in ("proper_noun_heuristic", "feminine_noun_ta_ending"):
        n, inst = new_counts[cat], new_inst[cat]
        examples = sorted(by_cat[cat], key=lambda x: -x["cluster_frequency"])[:5]
        ex_str = ", ".join(e["consonantal_base"] for e in examples)
        print(f"{cat:30s} {n:9d} {inst:10d}  {ex_str}")

    n_amb, inst_amb = len(still_ambiguous), total - already_inst - sum(new_inst.values())
    print(f"{'STILL AMBIGUOUS':30s} {n_amb:9d} {inst_amb:10d}")

    covered = already_inst + sum(new_inst.values())
    print(f"\n{covered}/{total} instances ({covered/total*100:.1f}%) now have "
          f"a grammatical, lexical, name, or feminine-noun explanation.")

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
