# Syriac Text Standardization & Variant Analysis

A Python-based toolkit for identifying and standardizing spelling variations in Syriac corpus files (NoSketchEngine `.vert` format). Designed to eliminate duplicate entries caused by inconsistent diacritical marking and formatting artifacts.

## Overview

### Problem
NoSketchEngine corpus files often contain variant spellings of the same word due to:
- **Non-standardized diacritics** - Different vowel marks for the same word
- **Kashida characters** - Extra spacing characters (U+0640) inserted for text justification
- **Combining mark placement** - Same marks at different positions
- **OCR inconsistencies** - Multiple representations of diacritical features

### Solution
This toolkit implements **Strategy 1: Frequency-Based Canonical Standardization**

Each word's consonantal base (skeleton without diacritics) is identified, and the most frequent variant is selected as the canonical form. All variants are then mapped to this canonical form.

**Results:**
- Unique words reduced: 301,960 → 196,541 (34.9% reduction)
- Duplicate clusters eliminated: 51,858 → 0
- Lines modified: ~12.6% (mostly non-lossy normalization)

## Scripts

### 1. `analyze_syriac_variants.py`
**Purpose:** Scan a vert file and identify duplicate word clusters

**Usage:**
```bash
python analyze_syriac_variants.py --input <corpus.vert> [--output <report.json>]
```

**Example:**
```bash
python analyze_syriac_variants.py --input ../corpora_vert_versions/mytext.vert --output mytext_analysis.json
```

**Output:**
- JSON report with:
  - Summary statistics (total unique words, instances, duplicate clusters)
  - Top duplicate clusters by frequency
  - Each cluster's consonantal base, variants, and frequencies

**Typical Output:**
```
Total unique words: 301,960
Total word instances: 2,975,551
Potential duplicate clusters: 51,858

Top 10 duplicate clusters by frequency:
1. Base: ܡ̣ܢ
   Cluster freq: 35971, Variants: 12
     • ܡ̣ܢ (n=35937)
     • ܡ̣ـܢ (n=13)
     • ܡ̣ـــܢ (n=4)
     ...
```

### 2. `standardize_syriac.py`
**Purpose:** Standardize a vert file using frequency-based canonical forms

**Usage:**
```bash
python standardize_syriac.py <input.vert> [output.vert] [mapping.json]
```

**Examples:**

Basic usage (auto-generates output filename):
```bash
python standardize_syriac.py ../corpora_vert_versions/mytext.vert
```
Creates:
- `../corpora_vert_versions/mytext_standardized.vert`
- `../corpora_vert_versions/mytext_mapping.json`

With explicit output paths:
```bash
python standardize_syriac.py corpus.vert corpus_clean.vert variant_map.json
```

**Output Files:**
1. **Standardized vert file** - Same format as input, with normalized Syriac text
2. **Mapping JSON** - Reference of all variant → canonical conversions (for reproducibility)

**Processing Steps:**
1. Removes Kashida characters (U+0640) from all Syriac text
2. For each consonantal base:
   - Identifies all variants (different diacritics)
   - Selects most frequent variant as canonical
   - Creates mapping for all other variants
3. Applies mapping to output file

## Workflow

### Quick Start (Analysis Only)
```bash
# 1. Analyze corpus to see duplicate patterns
python analyze_syriac_variants.py --input corpus.vert --output analysis.json

# 2. Review report to understand scope of duplication
# Open analysis.json in a text editor or JSON viewer

# 3. Proceed to standardization if satisfied
```

### Full Workflow (Analysis + Standardization)
```bash
# 1. Analyze original corpus
python analyze_syriac_variants.py --input corpus.vert --output before_analysis.json

# 2. Standardize corpus
python standardize_syriac.py corpus.vert corpus_standardized.vert corpus_mapping.json

# 3. Analyze standardized corpus to verify improvements
python analyze_syriac_variants.py --input corpus_standardized.vert --output after_analysis.json

# 4. Compare results
# - before_analysis.json should show many duplicate clusters
# - after_analysis.json should show 0 duplicate clusters
# - corpus_mapping.json contains the transformations applied
```

## Technical Details

### Supported Characters
Scripts handle:
- **East Syriac vowels** (Pthaha, Gathpha, Rbasa, Hbasa, Esasa, Rwaha, Yudh)
- **Combining marks** (Feminine dot, Qushshama, Barrekh, etc.)
- **Arabic-influenced marks** (Fatha, Damma, Kasra, Shadda, Sukun, Maddah, etc.)
- **Kashida/Tatweel** (text justification character)
- **Non-Syriac text** (safely skipped)

### Consonantal Base Extraction
The `get_syriac_base()` function removes:
- All vowel diacritics
- All combining marks
- Kashida characters
- Extra positioning marks

Example:
```
Input:  ܗ݇ܘܵܐ (with vowels and marks)
Base:   ܗܘܐ (consonantal skeleton)
```

### Variant Clustering
Words are grouped by consonantal base. For each group, the variant with the highest frequency in the corpus becomes the canonical form.

Example cluster:
```
Base: ܠܐ
Canonical (most frequent): ܠܵܐ (19,232 instances)
Variants:
  - ܠܹܐ (15,414) → mapped to ܠܵܐ
  - ܠܲܐ (111) → mapped to ܠܵܐ
  - ܠܐ (62) → mapped to ܠܵܐ
  ...
```

### Mapping File Format
The mapping JSON is straightforward for manual review or reapplication:

```json
{
  "ܠܹܐ": "ܠܵܐ",
  "ܠܲܐ": "ܠܵܐ",
  "ܠܸܐ": "ܠܵܐ",
  "ܗܘܵܐ": "ܗ݇ܘܵܐ",
  "ܗܵܘܹܐ": "ܗ݇ܘܵܐ",
  ...
}
```

## Performance

### Resource Requirements
- **Memory:** ~200-500 MB for typical corpus files (2-5 million words)
- **CPU:** Single-threaded Python
- **I/O:** Disk space for output files (~same size as input)

### Processing Times
- **Analysis (identify variants):** ~30-60 seconds for 4M+ word corpus
- **Standardization (apply mapping):** ~60-90 seconds for 4M+ word corpus

### Scalability
Both scripts process files line-by-line with minimal memory buffering. Safe for very large corpus files.

## Best Practices

### 1. Always Analyze First
Never standardize without understanding the variant patterns:
```bash
python analyze_syriac_variants.py --input corpus.vert --output analysis.json
```
Review the JSON report to understand what will change.

### 2. Keep Backups
Always retain the original corpus file:
```bash
# Good practice
cp corpus.vert corpus_backup.vert
python standardize_syriac.py corpus.vert corpus_standardized.vert
```

### 3. Preserve Mapping Files
The mapping JSON is essential for:
- Understanding what changed
- Recreating the standardization later
- Auditing modifications
- Applying to related corpus files

```bash
# Store mapping file with standardized corpus
python standardize_syriac.py corpus.vert corpus_standardized.vert mapping.json
```

### 4. Batch Processing Multiple Files
Create a batch script for consistency:

```bash
#!/bin/bash
# standardize_corpus.sh
for file in corpus_*.vert; do
    echo "Standardizing $file..."
    python standardize_syriac.py "$file"
done
```

### 5. Validation
After standardization, verify the output:
- Check line count matches input
- Verify non-Syriac text is unchanged
- Spot-check a few lines in the standardized file

```bash
# Compare line counts
wc -l corpus.vert corpus_standardized.vert
```

## Limitations & Notes

### What These Scripts Do
✓ Identify and cluster variant spellings
✓ Remove formatting artifacts (Kashida)
✓ Standardize to most-frequent variant per base
✓ Handle East Syriac vowel systems
✓ Preserve non-Syriac text

### What These Scripts Don't Do
✗ Manual linguistic curation (all changes based on frequency)
✗ Handle multi-language corpora specially (but skips non-Syriac)
✗ Modify XML metadata (only affects word text)
✗ Provide interactive review/approval per change

### Considerations

1. **Frequency Assumption:** Most frequent variant ≠ most correct variant
   - For finalized corpora, this is usually true
   - For noisy/OCR'd texts, may need manual review

2. **Diacritic Philosophy:** Scripts preserve East Syriac system
   - No cross-system normalization (e.g., to Western Syriac)
   - If mixing systems in one corpus, consider separate processing

3. **Non-Reversible:** While mapping is available, true reversion to original isn't guaranteed
   - Some information is lost (e.g., multiple forms → single canonical)
   - Keep originals for reference

## Troubleshooting

### No output file created
- Check input file path is absolute or relative and correct
- Verify read permissions on input file
- Verify write permissions in output directory

### "Potential duplicate clusters: 0" after standardization
- **Expected result!** This means standardization worked
- The goal is to reduce clusters to 0

### Large number of changes (>50%)
- May indicate very noisy source (heavy OCR errors, mixed sources)
- Review analysis JSON to understand patterns
- Consider manual review of top clusters before standardizing

### Out of memory
- For files >10 GB, consider splitting into smaller chunks
- Or process on a machine with more RAM

## Examples

### Example 1: Analyze and Standardize a Single Corpus
```bash
cd syriac_standardization

# Analyze
python analyze_syriac_variants.py \
  --input ../corpora_vert_versions/peshitta.vert \
  --output peshitta_analysis.json

# Review analysis (check duplicate count, top variants)

# Standardize
python standardize_syriac.py \
  ../corpora_vert_versions/peshitta.vert \
  ../corpora_vert_versions/peshitta_standardized.vert \
  peshitta_mapping.json

# Verify
python analyze_syriac_variants.py \
  --input ../corpora_vert_versions/peshitta_standardized.vert \
  --output peshitta_analysis_after.json
```

### Example 2: Batch Process Multiple Corpora
```bash
#!/bin/bash
cd syriac_standardization

for corpus in ../corpora_vert_versions/*.vert; do
  echo "Processing $corpus..."
  basename=$(basename "$corpus" .vert)
  
  # Analyze
  python analyze_syriac_variants.py --input "$corpus" --output "${basename}_analysis.json"
  
  # Standardize
  python standardize_syriac.py "$corpus"
  
  echo "Done: $basename"
done
```

## Contact & Support

For issues or feature requests related to the standardization scripts, maintain these files as reference.

---

**Last Updated:** 2026-07-07
**Version:** 1.0
**Python:** 3.6+
**Dependencies:** None (standard library only)
