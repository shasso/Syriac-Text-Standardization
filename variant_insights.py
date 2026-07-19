#!/usr/bin/env python3
"""
variant_insights.py
Extended analysis of analyze_syriac_variants.py output (the *_analysis.json report).

Adds:
  1. Kashida-only vs genuine-diacritic-variation split
  2. Pareto / concentration analysis (how much of the corpus a handful of clusters explain)
  3. Dominance ratio per cluster (top variant's share of cluster mass) -> flags clusters
     where frequency-based canonicalization is linguistically risky
  4. Base-length vs variant-count correlation
  5. A tiered "merge safety" classification: SAFE_AUTO / REVIEW / MANUAL
  6. Optional chart export (matplotlib)

Usage:
    python variant_insights.py --input analysis.json [--chart out.png] [--export-review review.json]
"""
import argparse
import json
from collections import Counter

TATWEEL = "\u0640"


def strip_tatweel(s):
    return s.replace(TATWEEL, "")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dominance(cluster):
    top = max(v["frequency"] for v in cluster["variants"])
    return top / cluster["cluster_frequency"]


def classify(cluster, dom):
    """Tier each cluster by how safe frequency-based auto-merging is."""
    variants = sorted(cluster["variants"], key=lambda v: -v["frequency"])
    non_top_max = variants[1]["frequency"] if len(variants) > 1 else 0
    stripped = {strip_tatweel(v["form"]) for v in cluster["variants"]}

    if len(stripped) == 1:
        return "SAFE_AUTO"  # pure kashida/tatweel noise, no real diacritic difference
    if non_top_max <= 3:
        return "SAFE_AUTO"  # dominant form overwhelms a thin noise tail
    if dom >= 0.85:
        return "SAFE_AUTO"
    if cluster["cluster_frequency"] >= 50 and dom < 0.75:
        return "MANUAL"  # high-impact + genuinely split mass -> likely real morphological
                          # alternants (tense/person/gender), not spelling noise
    return "REVIEW"


def analyze(data):
    dups = data["duplicates"]
    summary = data["summary"]
    total_instances = summary["total_word_instances"]

    kashida_only = pure_diacritic = 0
    kashida_only_freq = pure_diacritic_freq = 0
    base_len_variants, base_len_count = Counter(), Counter()
    tiers = Counter()
    tier_freq = Counter()
    flagged_for_review = []

    for d in dups:
        dom = dominance(d)
        tier = classify(d, dom)
        tiers[tier] += 1
        tier_freq[tier] += d["cluster_frequency"]
        if tier == "MANUAL":
            flagged_for_review.append({
                "consonantal_base": d["consonantal_base"],
                "cluster_frequency": d["cluster_frequency"],
                "dominance": round(dom, 3),
                "variants": [(v["form"], v["frequency"]) for v in
                             sorted(d["variants"], key=lambda v: -v["frequency"])],
            })

        stripped = {strip_tatweel(v["form"]) for v in d["variants"]}
        if len(stripped) == 1:
            kashida_only += 1
            kashida_only_freq += d["cluster_frequency"]
        else:
            pure_diacritic += 1
            pure_diacritic_freq += d["cluster_frequency"]

        L = len(d["consonantal_base"])
        base_len_variants[L] += d["num_variants"]
        base_len_count[L] += 1

    flagged_for_review.sort(key=lambda x: -x["cluster_frequency"])

    cluster_freqs = sorted((d["cluster_frequency"] for d in dups), reverse=True)
    total_dup_instances = sum(cluster_freqs)

    def top_n_share(n):
        return sum(cluster_freqs[:n]) / total_dup_instances

    report = {
        "summary": summary,
        "kashida_only_clusters": kashida_only,
        "kashida_only_instances": kashida_only_freq,
        "genuine_variation_clusters": pure_diacritic,
        "genuine_variation_instances": pure_diacritic_freq,
        "pareto": {f"top_{n}_share_of_dup_instances": round(top_n_share(n), 4)
                   for n in (10, 100, 1000)},
        "merge_safety_tiers": dict(tiers),
        "merge_safety_tier_instance_totals": dict(tier_freq),
        "base_length_avg_variants": {
            L: round(base_len_variants[L] / base_len_count[L], 2)
            for L in sorted(base_len_count) if base_len_count[L] >= 20
        },
        "top_flagged_for_manual_review": flagged_for_review[:50],
    }
    return report, flagged_for_review


def make_chart(data, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dups = data["duplicates"]
    num_variants = [d["num_variants"] for d in dups]
    doms = [dominance(d) for d in dups]
    cluster_freqs = sorted((d["cluster_frequency"] for d in dups), reverse=True)
    cum_share = []
    running = 0
    total = sum(cluster_freqs)
    for i, f in enumerate(cluster_freqs):
        running += f
        if i < 5000:
            cum_share.append(running / total)
    base_len_variants, base_len_count = Counter(), Counter()
    for d in dups:
        L = len(d["consonantal_base"])
        base_len_variants[L] += d["num_variants"]
        base_len_count[L] += 1
    lens = sorted(L for L in base_len_count if base_len_count[L] >= 20)
    avgs = [base_len_variants[L] / base_len_count[L] for L in lens]

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    axes[0, 0].hist(num_variants, bins=range(2, 30), color="#4c72b0")
    axes[0, 0].set_title("Variants per cluster (capped at 30)")
    axes[0, 0].set_xlabel("num_variants")
    axes[0, 0].set_ylabel("cluster count")

    axes[0, 1].hist(doms, bins=30, color="#dd8452")
    axes[0, 1].set_title("Dominance ratio (top variant's share of cluster)")
    axes[0, 1].set_xlabel("dominance")
    axes[0, 1].axvline(0.75, color="red", linestyle="--", linewidth=1)

    axes[1, 0].plot(range(1, len(cum_share) + 1), cum_share, color="#55a868")
    axes[1, 0].set_title("Cumulative share of duplicate-cluster instances\n(clusters ranked by frequency)")
    axes[1, 0].set_xlabel("top N clusters")
    axes[1, 0].set_ylabel("cumulative share")

    axes[1, 1].bar(lens, avgs, color="#8172b2")
    axes[1, 1].set_title("Avg variant count by consonantal-base length")
    axes[1, 1].set_xlabel("base length (chars)")
    axes[1, 1].set_ylabel("avg num_variants")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"Chart saved to {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--chart", help="path to save a 4-panel PNG summary")
    ap.add_argument("--export-review", help="path to save the full MANUAL-tier list as JSON")
    args = ap.parse_args()

    data = load(args.input)
    report, flagged = analyze(data)

    print(json.dumps({k: v for k, v in report.items() if k != "top_flagged_for_manual_review"},
                      ensure_ascii=False, indent=2))

    print("\n=== TOP 15 CLUSTERS FLAGGED FOR MANUAL LINGUISTIC REVIEW ===")
    print("(high corpus impact + no single variant dominates -> likely real")
    print(" morphological/dialectal alternants, not spelling noise)\n")
    for c in flagged[:15]:
        print(f"{c['consonantal_base']}  freq={c['cluster_frequency']}  dominance={c['dominance']}")
        for form, freq in c["variants"][:6]:
            print(f"    {form}  (n={freq})")

    if args.chart:
        make_chart(data, args.chart)

    if args.export_review:
        with open(args.export_review, "w", encoding="utf-8") as f:
            json.dump(flagged, f, ensure_ascii=False, indent=2)
        print(f"\nFull manual-review list ({len(flagged)} clusters) saved to {args.export_review}")


if __name__ == "__main__":
    main()
