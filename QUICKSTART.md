# Syriac Standardization Toolkit - Quick Start

Located in: `syriac_standardization/`

## Files

| File | Purpose |
|------|---------|
| `README.md` | Complete documentation (start here!) |
| `analyze_syriac_variants.py` | Identify duplicate word clusters in a corpus |
| `standardize_syriac.py` | Apply standardization to a corpus |
| `quick_standardize.py` | Automate entire workflow in one command |
| `syriac_variants_analysis.json` | Example output: variant analysis (before standardization) |
| `syriac_variants_analysis_after.json` | Example output: variant analysis (after standardization) |
| `syriac_standardization_mapping.json` | Example output: variant→canonical mappings |

## Quick Start

### Option 1: Automated Workflow (Recommended)
```bash
cd syriac_standardization
python quick_standardize.py ../corpora_vert_versions/mytext.vert
```

This runs all 3 steps:
1. Analyzes for duplicates
2. Standardizes the corpus
3. Verifies the results

### Option 2: Step-by-Step

**Step 1: Analyze corpus**
```bash
python analyze_syriac_variants.py --input corpus.vert --output analysis.json
```

**Step 2: Standardize corpus**
```bash
python standardize_syriac.py corpus.vert corpus_standardized.vert mapping.json
```

**Step 3: Verify results**
```bash
python analyze_syriac_variants.py --input corpus_standardized.vert --output analysis_after.json
```

## What These Scripts Do

### Problem
Your Syriac corpus has ~52,000 duplicate word clusters due to:
- Inconsistent diacritics (ܠܵܐ vs ܠܹܐ)
- Extra formatting characters
- OCR/encoding variations

### Solution
These scripts standardize all variants to their most-frequent form.

**Results:**
- Unique words: 301,960 → 196,541 (35% reduction)
- Duplicates: 51,858 → 0 (fully eliminated)
- Reversible: Mapping file preserved

## Example Results

**Before Standardization:**
```
Base: ܠܐ
  • ܠܵܐ (19,232 instances)
  • ܠܹܐ (15,414 instances)
  • ܠܲܐ (111 instances)
  • ܠܐ (62 instances)
  ... 20 more variants
Total cluster frequency: 34,970
```

**After Standardization:**
```
Base: ܠܐ
  • ܠܵܐ (34,970 instances)
Duplicate eliminated ✓
```

## Next Steps

1. **Read** `README.md` for comprehensive documentation
2. **Try** `quick_standardize.py` on one corpus file
3. **Review** the generated `.json` files to understand the transformations
4. **Apply** to other corpus files once satisfied with results

## Support

For issues or questions, refer to the **Troubleshooting** section in `README.md`.

---

**Version:** 1.0  
**Created:** 2026-07-07  
**Python:** 3.6+  
**Dependencies:** None (standard library only)
