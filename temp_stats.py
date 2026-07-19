import json, pathlib, collections, statistics, sys

# Path to the large JSON report (adjust if needed)
json_path = pathlib.Path(r"C:\Users\sargo\Documents\dockerDev\noSketchEngine Corpus Parsers\syriac_standardization\syriac_variants_analysis.json")

try:
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    print(f"Failed to load JSON: {e}")
    sys.exit(1)

summary = data.get("summary", {})
duplicates = data.get("duplicates", [])

# Basic stats
total_clusters = len(duplicates)
variants_per_cluster = [len(d.get("variants", [])) for d in duplicates]

avg_variants = statistics.mean(variants_per_cluster) if variants_per_cluster else 0
median_variants = statistics.median(variants_per_cluster) if variants_per_cluster else 0

# Distribution of cluster sizes
size_dist = collections.Counter(variants_per_cluster)

# Top 10 clusters (already sorted by frequency in the file)
top_clusters = duplicates[:10]

# Top 10 most frequent individual forms across all clusters
form_counter = collections.Counter()
for d in duplicates:
    for v in d.get("variants", []):
        form_counter[v.get("form", "")] = v.get("frequency", 0)
top_forms = form_counter.most_common(10)

# Output
print("=== Summary ===")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("\n=== Duplicate Cluster Stats ===")
print(f"Total duplicate clusters: {total_clusters}")
print(f"Average variants per cluster: {avg_variants:.2f}")
print(f"Median variants per cluster: {median_variants}")
print("Cluster size distribution (variants → number of clusters):")
for size, cnt in sorted(size_dist.items()):
    print(f"  {size} → {cnt}")

print("\n=== Top 10 Duplicate Clusters (by cluster frequency) ===")
for i, cl in enumerate(top_clusters, 1):
    base = cl.get("consonantal_base", "")
    freq = cl.get("cluster_frequency", 0)
    nvar = cl.get("num_variants", 0)
    print(f"{i}. Base: {base}")
    print(f"   Cluster frequency: {freq}")
    print(f"   Variants: {nvar}")
    # Show up to three most frequent variants
    for v in sorted(cl.get("variants", []), key=lambda x: x.get("frequency", 0), reverse=True)[:3]:
        print(f"     • {v.get('form', '')} (n={v.get('frequency', 0)})")
    if nvar > 3:
        print("     ...")

print("\n=== Top 10 Most Frequent Individual Forms ===")
for form, freq in top_forms:
    print(f"• {form} – {freq} occurrences")