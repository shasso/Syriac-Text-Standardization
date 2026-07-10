# Usage Examples for Syriac Standardization Toolkit

This file shows practical examples of how to use the standardization scripts on your corpus files.

## Your Corpus Files

You have corpus files in: `../corpora_vert_versions/`
- `abusu_02122026.vert`
- `abusu_02162026.vert` (already standardized to `abusu_02162026_standardized.vert`)
- And other vert files

## Example 1: Standardize abusu_02122026.vert

### Full Automated Workflow
```bash
cd syriac_standardization

# Run complete workflow (all 3 steps)
python quick_standardize.py ../corpora_vert_versions/abusu_02122026.vert
```

This generates:
- `../corpora_vert_versions/abusu_02122026_standardized.vert` - standardized corpus
- `../corpora_vert_versions/abusu_02122026_mapping.json` - variant mappings
- `../corpora_vert_versions/abusu_02122026_analysis.json` - before analysis
- `../corpora_vert_versions/abusu_02122026_standardized_analysis.json` - after analysis

### Manual Step-by-Step (if you want to inspect each step)

**Step 1: Analyze variants**
```bash
python analyze_syriac_variants.py \
  --input ../corpora_vert_versions/abusu_02122026.vert \
  --output ../corpora_vert_versions/abusu_02122026_analysis.json
```
Review the JSON file to see what duplicates exist.

**Step 2: Standardize**
```bash
python standardize_syriac.py \
  ../corpora_vert_versions/abusu_02122026.vert \
  ../corpora_vert_versions/abusu_02122026_standardized.vert \
  ../corpora_vert_versions/abusu_02122026_mapping.json
```

**Step 3: Verify**
```bash
python analyze_syriac_variants.py \
  --input ../corpora_vert_versions/abusu_02122026_standardized.vert \
  --output ../corpora_vert_versions/abusu_02122026_standardized_analysis.json
```
Verify that duplicate clusters are now 0.

## Example 2: Batch Process Multiple Files

### Using PowerShell (Windows)
```powershell
cd syriac_standardization

# Process all .vert files in corpora_vert_versions
Get-ChildItem ../corpora_vert_versions/*.vert | ForEach-Object {
    Write-Host "Processing: $($_.Name)"
    python quick_standardize.py $_.FullName
    Write-Host "✓ Complete`n"
}
```

### Using Bash (Linux/Mac)
```bash
cd syriac_standardization

for file in ../corpora_vert_versions/*.vert; do
    echo "Processing: $(basename $file)"
    python quick_standardize.py "$file"
    echo "✓ Complete"
done
```

## Example 3: Compare abusu_02162026 Results

You already have the results for `abusu_02162026`. Here's how to review them:

### View Before/After Comparison
```bash
cd syriac_standardization

# View summary of original duplicates
python -c "
import json
with open('syriac_variants_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f\"Before Standardization:\")
    print(f\"  Unique words: {data['summary']['total_unique_words']}\")
    print(f\"  Duplicate clusters: {data['summary']['potential_duplicate_clusters']}\")
"

# View summary after standardization
python -c "
import json
with open('syriac_variants_analysis_after.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f\"After Standardization:\")
    print(f\"  Unique words: {data['summary']['total_unique_words']}\")
    print(f\"  Duplicate clusters: {data['summary']['potential_duplicate_clusters']}\")
"
```

## Example 4: Inspect Mapping Transformations

### View top variant transformations
```bash
cd syriac_standardization

python -c "
import json
with open('syriac_standardization_mapping.json', 'r', encoding='utf-8') as f:
    mapping = json.load(f)
    
print(f'Total transformations: {len(mapping)}')
print()
print('First 20 transformations:')
for variant, canonical in list(mapping.items())[:20]:
    print(f'  {variant} → {canonical}')
"
```

### Export mappings to human-readable format
```bash
cd syriac_standardization

python -c "
import json
with open('syriac_standardization_mapping.json', 'r', encoding='utf-8') as f:
    mapping = json.load(f)

# Group by canonical form
canonical_variants = {}
for variant, canonical in mapping.items():
    if canonical not in canonical_variants:
        canonical_variants[canonical] = []
    canonical_variants[canonical].append(variant)

# Output grouped
for canonical in sorted(canonical_variants.keys(), key=lambda x: len(canonical_variants[x]), reverse=True)[:20]:
    variants = canonical_variants[canonical]
    print(f'{canonical}:')
    for variant in sorted(variants)[:5]:
        print(f'  ← {variant}')
    if len(variants) > 5:
        print(f'  ... and {len(variants)-5} more variants')
"
```

## Example 5: Verify Integrity

After standardization, verify the corpus hasn't been corrupted:

```bash
cd syriac_standardization

# Compare line counts (should be identical)
echo "Original line count:"
wc -l ../corpora_vert_versions/abusu_02122026.vert

echo "Standardized line count:"
wc -l ../corpora_vert_versions/abusu_02122026_standardized.vert

# Check for non-Syriac text preservation
# The following should match if non-Syriac lines are preserved
echo "Original punctuation marks:"
grep -o ":" ../corpora_vert_versions/abusu_02122026.vert | wc -l

echo "Standardized punctuation marks:"
grep -o ":" ../corpora_vert_versions/abusu_02122026_standardized.vert | wc -l
```

## Example 6: Selective Analysis

If you only want to analyze without standardizing:

```bash
cd syriac_standardization

# Analyze and save to custom location
python analyze_syriac_variants.py \
  --input ../corpora_vert_versions/abusu_02122026.vert \
  --output ./reports/abusu_02122026_report.json
```

Then review the report JSON in your text editor or JSON viewer to:
- Count total duplicate clusters
- Identify most problematic variants
- Manually decide which forms to use

## Workflow Recommendation

For your corpus files, I recommend:

1. **Start with one file** - e.g., `abusu_02122026.vert` (wait, this is already done!)
2. **Review the analysis** - Check `syriac_variants_analysis.json` to understand duplicates
3. **Review mappings** - Check `syriac_standardization_mapping.json` for transformations
4. **Apply to others** - Once satisfied, run on remaining files

## Tips

### Tip 1: Keep Results Organized
```bash
# Create a results directory
mkdir -p ../corpora_vert_versions/standardized_results

# Move generated files there
mv ../corpora_vert_versions/*_standardized.vert ../corpora_vert_versions/standardized_results/
mv ../corpora_vert_versions/*_mapping.json ../corpora_vert_versions/standardized_results/
```

### Tip 2: Archive Originals
```bash
# Create backup of originals before standardization
mkdir -p ../corpora_vert_versions/originals_backup
cp ../corpora_vert_versions/*.vert ../corpora_vert_versions/originals_backup/
```

### Tip 3: Generate Summary Report
```bash
# Create a CSV summary of all corpus stats
python << 'EOF'
import json
from pathlib import Path

results = []
for analysis_file in Path('../corpora_vert_versions').glob('*_analysis.json'):
    with open(analysis_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        results.append({
            'file': analysis_file.stem.replace('_analysis', ''),
            'unique_words': data['summary']['total_unique_words'],
            'duplicates': data['summary']['potential_duplicate_clusters']
        })

print("Corpus Statistics:")
print("File, Unique Words, Duplicate Clusters")
for r in sorted(results, key=lambda x: x['duplicates'], reverse=True):
    print(f"{r['file']}, {r['unique_words']}, {r['duplicates']}")
EOF
```

## Troubleshooting

### "ModuleNotFoundError: No module named..."
This shouldn't happen - the scripts only use Python standard library (no external dependencies).
Make sure you're using Python 3.6+:
```bash
python --version
```

### Very large mapping file
If `*_mapping.json` is very large (100+ MB), your corpus probably has:
- Heavy OCR errors
- Mixed language sources
- Encoding issues

Consider reviewing the analysis file first to understand the problem.

### Standardization "not working"
Check:
1. Input file is valid UTF-8 encoded
2. Input file contains Syriac text (not all non-Syriac)
3. Output location has write permissions

## Next Steps

1. ✓ Review `abusu_02162026_standardized.vert` results
2. Standardize `abusu_02122026.vert` using `quick_standardize.py`
3. Apply to other corpus files as needed
4. Archive originals and keep mapping files for reference

---

For more details, see **README.md** in this folder.
