#!/usr/bin/env python3
"""
standardize_syriac_v2.py
Risk-aware successor to standardize_syriac.py ("Strategy 1").

standardize_syriac.py canonicalizes EVERY consonantal-base cluster to its
most frequent surface form, with no awareness of whether that's safe. This
script instead consults the tier/category annotations produced by the
classification pipeline (variant_insights.py -> grammar_crossref.py ->
lexical_subclass.py -> name_and_feminine_subclass.py) and makes a per-
cluster merge/skip decision, with a full audit trail of *why*.

Decision policy (each stage independently overridable via CLI flags):

  SAFE_AUTO tier        -> always merge (kashida-only, thin noise tail, or
                           dominance >=0.85 -- frequency IS a good proxy here)
  REVIEW tier           -> merge by default (--review-policy)
  MANUAL tier, category matched a HIGH-RISK grammatical paradigm
      (copula_or_to_be_paradigm, passive_or_remain_piš)
                        -> SKIP by default (--manual-high-risk-policy):
                           these clusters conflate genuinely different
                           tense/aspect/person forms; there is no coherent
                           "canonical form" to collapse to.
  MANUAL tier, category matched anything else (pronominal_suffix,
      negation_particle, numeral_one, plural_noun_phonetic,
      adjectival_or_ordinal_ending, ordinal_before_root,
      interrogative_particle, demonstrative_pronoun, proper_noun_heuristic,
      feminine_noun_ta_ending)
                        -> merge by default (--manual-moderate-policy):
                           each of these clusters, by construction, denotes
                           ONE lexical item whose variants are plausible
                           spelling/pronunciation differences, not competing
                           grammatical readings -- but still logged, since
                           "plausible" isn't "guaranteed."
  MANUAL tier, no category matched at all (still ambiguous)
                        -> SKIP by default (--manual-unresolved-policy):
                           unknown risk, conservative default.

Kashida (U+0640) is stripped from every token regardless of merge decision --
that cleanup is orthographically uncontroversial (see the paper, Section
5.2: kashida-only clusters are only 0.5% of clusters / 0.1% of instances,
and stripping it never touches a grammatical distinction).

CAVEAT: the HIGH_RISK_CATEGORIES set and the tiering thresholds below are
duplicated from variant_insights.py's classify()/dominance() on purpose, so
this script stays runnable on its own without importing another file. If
you tune thresholds or categories in one place, update the other.

Usage:
    python standardize_syriac_v2.py \\
        --input corpus.vert \\
        --analysis syriac_variants_analysis.json \\
        --manual-review manual_review_final2.json \\
        --output corpus_standardized_v2.vert \\
        --mapping corpus_mapping_v2.json \\
        --decisions corpus_decisions_v2.json

    # --manual-review is optional. Without it, every MANUAL-tier cluster is
    # treated as "no category matched" (i.e. --manual-unresolved-policy
    # applies to ALL of them, not just the genuinely still-ambiguous ones).
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

TATWEEL = "\u0640"

# ---------------------------------------------------------------------
# Tiering logic -- kept identical to variant_insights.py's dominance()/
# classify(). If you change the thresholds there, mirror the change here.
# ---------------------------------------------------------------------
SAFE_AUTO_DOMINANCE = 0.85
MANUAL_MIN_FREQUENCY = 50
MANUAL_MAX_DOMINANCE = 0.75
NOISE_TAIL_MAX_FREQ = 3

# Categories where the cluster's variants are different grammatical
# forms of one paradigm (tense/aspect/person), not spelling variants of one
# word -- "canonical form" is not a coherent concept for these. Extend this
# set if you identify more such paradigms (e.g. after adding new root
# categories to grammar_crossref.py that have the same property).
HIGH_RISK_CATEGORIES = {
    "copula_or_to_be_paradigm",
    "passive_or_remain_piš",
}


def strip_tatweel(s):
    return s.replace(TATWEEL, "")


def dominance(variants):
    """variants: list of {"form": ..., "frequency": ...} or [form, freq] pairs."""
    freqs = [v["frequency"] if isinstance(v, dict) else v[1] for v in variants]
    total = sum(freqs)
    return (max(freqs) / total) if total else 0.0


def tier_of(cluster_frequency, dom, variants):
    stripped = {strip_tatweel(v["form"] if isinstance(v, dict) else v[0]) for v in variants}
    freqs = sorted((v["frequency"] if isinstance(v, dict) else v[1] for v in variants), reverse=True)
    non_top_max = freqs[1] if len(freqs) > 1 else 0

    if len(stripped) == 1:
        return "SAFE_AUTO"
    if non_top_max <= NOISE_TAIL_MAX_FREQ:
        return "SAFE_AUTO"
    if dom >= SAFE_AUTO_DOMINANCE:
        return "SAFE_AUTO"
    if cluster_frequency >= MANUAL_MIN_FREQUENCY and dom < MANUAL_MAX_DOMINANCE:
        return "MANUAL"
    return "REVIEW"


# ---------------------------------------------------------------------
# Corpus scanning (same token/Syriac detection as analyze_syriac_variants.py)
# ---------------------------------------------------------------------
SYRIAC_START, SYRIAC_END = 0x0700, 0x074F


def is_syriac(text):
    return any(SYRIAC_START <= ord(c) <= SYRIAC_END for c in text)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_decisions(analysis, manual_review, policies):
    """Return (mapping: dict[str,str], decisions: list[dict])."""
    ann_by_base = {}
    if manual_review:
        for c in manual_review:
            ann_by_base[c["consonantal_base"]] = c

    mapping = {}
    decisions = []

    for cluster in analysis["duplicates"]:
        base = cluster["consonantal_base"]
        variants = cluster["variants"]
        cluster_freq = cluster["cluster_frequency"]
        dom = dominance(variants)
        tier = tier_of(cluster_freq, dom, variants)

        canonical = max(variants, key=lambda v: v["frequency"])["form"]

        category = None
        if tier == "MANUAL":
            ann = ann_by_base.get(base, {})
            category = (ann.get("grammar_category") or ann.get("lexical_category")
                        or ann.get("name_or_feminine_category"))

        if tier == "SAFE_AUTO":
            decision, reason = "merge", "SAFE_AUTO tier: kashida-only, thin noise tail, or dominance >=0.85"
        elif tier == "REVIEW":
            if policies["review"] == "merge":
                decision, reason = "merge", "REVIEW tier, --review-policy=merge"
            else:
                decision, reason = "skip", "REVIEW tier, --review-policy=skip"
        else:  # MANUAL
            if category in HIGH_RISK_CATEGORIES:
                if policies["manual_high_risk"] == "merge":
                    decision, reason = "merge", f"MANUAL tier, high-risk category '{category}', --manual-high-risk-policy=merge (OVERRIDDEN DEFAULT)"
                else:
                    decision, reason = "skip", f"MANUAL tier, high-risk category '{category}': variants are different grammatical forms, not spelling variants"
            elif category is not None:
                if policies["manual_moderate"] == "merge":
                    decision, reason = "merge", f"MANUAL tier, category '{category}': single lexeme, plausible spelling variation"
                else:
                    decision, reason = "skip", f"MANUAL tier, category '{category}', --manual-moderate-policy=skip"
            else:
                if policies["manual_unresolved"] == "merge":
                    decision, reason = "merge", "MANUAL tier, no category matched, --manual-unresolved-policy=merge (OVERRIDDEN DEFAULT)"
                else:
                    decision, reason = "skip", "MANUAL tier, no category matched: unknown risk, conservative default"

        if decision == "merge":
            for v in variants:
                form = v["form"]
                if form != canonical:
                    mapping[form] = canonical

        decisions.append({
            "consonantal_base": base,
            "cluster_frequency": cluster_freq,
            "dominance": round(dom, 3),
            "tier": tier,
            "category": category,
            "decision": decision,
            "canonical_form": canonical if decision == "merge" else None,
            "reason": reason,
        })

    return mapping, decisions


def standardize_file(input_file, output_file, mapping):
    total_lines = changed_lines = 0
    with open(input_file, encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
        for line in f_in:
            original = line.rstrip("\n")
            processed = original
            if is_syriac(processed):
                after_kashida = strip_tatweel(processed)
                if after_kashida != processed:
                    processed = after_kashida
                    changed_lines += 1
            if processed in mapping:
                processed = mapping[processed]
                changed_lines += 1
            f_out.write(processed + "\n")
            total_lines += 1
    return changed_lines, total_lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, help="original .vert corpus")
    ap.add_argument("--analysis", required=True, help="analyze_syriac_variants.py output JSON")
    ap.add_argument("--manual-review", help="manual_review_final2.json (or any pass's output); optional")
    ap.add_argument("--output", help="standardized .vert path (default: <input_stem>_standardized_v2<ext>)")
    ap.add_argument("--mapping", help="mapping JSON path (default: <input_stem>_mapping_v2.json)")
    ap.add_argument("--decisions", help="full per-cluster decision log JSON (default: <input_stem>_decisions_v2.json)")
    ap.add_argument("--review-policy", choices=["merge", "skip"], default="merge")
    ap.add_argument("--manual-high-risk-policy", choices=["merge", "skip"], default="skip")
    ap.add_argument("--manual-moderate-policy", choices=["merge", "skip"], default="merge")
    ap.add_argument("--manual-unresolved-policy", choices=["merge", "skip"], default="skip")
    args = ap.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.parent / f"{input_path.stem}_standardized_v2{input_path.suffix}"
    mapping_path = Path(args.mapping) if args.mapping else input_path.parent / f"{input_path.stem}_mapping_v2.json"
    decisions_path = Path(args.decisions) if args.decisions else input_path.parent / f"{input_path.stem}_decisions_v2.json"

    analysis = load_json(args.analysis)
    manual_review = load_json(args.manual_review) if args.manual_review else None

    policies = {
        "review": args.review_policy,
        "manual_high_risk": args.manual_high_risk_policy,
        "manual_moderate": args.manual_moderate_policy,
        "manual_unresolved": args.manual_unresolved_policy,
    }

    print("Building risk-aware merge decisions...")
    mapping, decisions = build_decisions(analysis, manual_review, policies)

    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    with open(decisions_path, "w", encoding="utf-8") as f:
        json.dump(decisions, f, ensure_ascii=False, indent=2)

    print(f"Applying {len(mapping)} approved rewrites to {input_path}...")
    changed, total = standardize_file(input_path, output_path, mapping)

    tier_counts = defaultdict(lambda: defaultdict(int))
    for d in decisions:
        tier_counts[d["tier"]][d["decision"]] += 1

    print("\n=== DECISION SUMMARY (clusters) ===")
    for tier in ("SAFE_AUTO", "REVIEW", "MANUAL"):
        merged = tier_counts[tier]["merge"]
        skipped = tier_counts[tier]["skip"]
        print(f"  {tier:10s}  merged={merged:6d}  skipped={skipped:6d}")

    print("\n=== STANDARDIZATION SUMMARY ===")
    print(f"Input:        {input_path}")
    print(f"Output:       {output_path}")
    print(f"Mapping:      {mapping_path}  ({len(mapping)} rewrite rules)")
    print(f"Decision log: {decisions_path}  ({len(decisions)} clusters)")
    print(f"Total lines:  {total}")
    print(f"Changed:      {changed} ({100*changed/total:.2f}%)")


if __name__ == "__main__":
    main()
