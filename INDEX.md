# Syriac Text Standardization Toolkit
## Complete Index & Documentation

**Location:** `c:\Users\sargo\Documents\dockerDev\noSketchEngine Corpus Parsers\syriac_standardization\`

---

## 📋 Documentation Files (Read These First)

### 1. **QUICKSTART.md** ⭐ START HERE
- Quick overview of what the toolkit does
- One-command quick start
- Expected results summary
- Next steps

### 2. **README.md** 📖 COMPREHENSIVE GUIDE
- Complete documentation
- Problem statement & solution explained
- Detailed script descriptions with parameters
- Full workflow instructions
- Technical details about algorithms
- Best practices
- Troubleshooting guide
- Performance information

### 3. **EXAMPLES.md** 💡 PRACTICAL USAGE
- Real-world usage examples
- How to apply to your specific corpus files
- Batch processing instructions
- Data inspection techniques
- Comparison examples
- Verification methods

### 4. **THIS FILE (INDEX.md)**
- Overview of all files
- What each file does
- Quick navigation guide

---

## 🔧 Script Files

### 1. **standardize_syriac.py** - Core Standardization
**What it does:** Converts all variant spellings to canonical forms

**Usage:**
```bash
python standardize_syriac.py input.vert [output.vert] [mapping.json]
```

**Inputs:**
- A NoSketchEngine `.vert` file with Syriac text

**Outputs:**
- Standardized `.vert` file (same format, normalized text)
- Mapping `.json` file (variant → canonical transformations)

**Example:**
```bash
python standardize_syriac.py corpus.vert corpus_standard.vert mapping.json
```

---

### 2. **analyze_syriac_variants.py** - Variant Analysis
**What it does:** Scans a corpus and identifies all variant word clusters

**Usage:**
```bash
python analyze_syriac_variants.py --input file.vert [--output report.json]
```

**Inputs:**
- A NoSketchEngine `.vert` file

**Outputs:**
- Analysis report `.json` with:
  - Total unique words count
  - Total word instances
  - Count of duplicate clusters
  - Top 10 duplicate clusters by frequency
  - Each cluster's consonantal base and all variants

**Example:**
```bash
python analyze_syriac_variants.py --input corpus.vert --output analysis.json
```

---

### 3. **quick_standardize.py** - Automated Workflow
**What it does:** Runs complete standardization workflow (analysis → standardize → verify)

**Usage:**
```bash
python quick_standardize.py corpus.vert
```

**Inputs:**
- A NoSketchEngine `.vert` file

**Outputs:**
- `corpus_standardized.vert` - standardized corpus
- `corpus_mapping.json` - mappings reference
- `corpus_analysis.json` - before analysis
- `corpus_standardized_analysis.json` - after analysis

**Example:**
```bash
python quick_standardize.py ../corpora_vert_versions/abusu_02122026.vert
```

---

## 📊 Data Files (From Previous Run on abusu_02162026.vert)

### 1. **syriac_variants_analysis.json**
**What:** Analysis of original corpus (before standardization)
- Total unique words: 301,960
- Total word instances: 2,975,551
- Duplicate clusters: 51,858
- Top 10 clusters detailed with variants

**Use:** Review to understand the problem

### 2. **syriac_variants_analysis_after.json**
**What:** Analysis of standardized corpus (after standardization)
- Total unique words: 196,541
- Total word instances: 2,975,551
- Duplicate clusters: 0 ✓
- Confirms standardization eliminated duplicates

**Use:** Verify standardization worked

### 3. **syriac_standardization_mapping.json**
**What:** Dictionary of variant → canonical transformations
- 103,171 variant mappings
- Shows exactly what changed
- Example: `"ܠܹܐ": "ܠܵܐ"` (variant → canonical)

**Use:** 
- Reference for reproducibility
- Audit what was transformed
- Apply to related corpus files

---

## 🚀 Quick Start Guide

### For the Impatient (5 minutes)

```bash
cd syriac_standardization

# Option 1: Run everything automatically
python quick_standardize.py ../corpora_vert_versions/your_corpus.vert

# Wait for completion, review the generated .json files
```

### For the Thorough (15 minutes)

```bash
cd syriac_standardization

# Step 1: Analyze
python analyze_syriac_variants.py --input ../corpora_vert_versions/corpus.vert --output corpus_analysis.json

# Step 2: Review corpus_analysis.json (open in text editor)
# Check: How many duplicates? Any patterns you want to understand?

# Step 3: Standardize
python standardize_syriac.py ../corpora_vert_versions/corpus.vert ../corpora_vert_versions/corpus_standardized.vert mapping.json

# Step 4: Verify
python analyze_syriac_variants.py --input ../corpora_vert_versions/corpus_standardized.vert --output corpus_analysis_after.json

# Step 5: Confirm results in corpus_analysis_after.json
# Expected: "potential_duplicate_clusters": 0
```

---

## 📈 What to Expect

### Before Standardization
```json
{
  "total_unique_words": 301960,
  "total_word_instances": 2975551,
  "potential_duplicate_clusters": 51858
}
```

### After Standardization
```json
{
  "total_unique_words": 196541,
  "total_word_instances": 2975551,
  "potential_duplicate_clusters": 0
}
```

### Improvement
- ✓ 34.9% reduction in unique word forms
- ✓ All 51,858 duplicate clusters eliminated
- ✓ Word frequency preserved (total instances unchanged)
- ✓ Non-Syriac text untouched

---

## 🎯 Recommended Workflow

### Phase 1: Learning (First Time Only)
1. Read **QUICKSTART.md** (2 min)
2. Run `quick_standardize.py` on one test corpus (5 min)
3. Review the generated JSON files (5 min)
4. Skim **README.md** sections of interest (10 min)
5. **Decision:** Continue with other files?

### Phase 2: Production Use
6. Standardize remaining corpus files:
   ```bash
   for file in ../corpora_vert_versions/*.vert; do
       python quick_standardize.py "$file"
   done
   ```
7. Archive originals and keep mapping files
8. Use standardized versions in downstream processing

### Phase 3: Maintenance
- Keep mapping files as reference
- Document any linguistic choices made
- Share mapping files with team for reproducibility

---

## 🔍 Key Concepts

### Consonantal Base
The skeleton of a word with all diacritics removed.
```
ܗ݇ܘܵܐ (with vowels) → ܗܘܐ (consonantal base)
```

### Variant Cluster
All different spellings of the same consonantal base.
```
Base: ܠܐ
Variants:
  - ܠܵܐ (canonical - most frequent)
  - ܠܹܐ → standardized to ܠܵܐ
  - ܠܲܐ → standardized to ܠܵܐ
  - ܠܐ → standardized to ܠܵܐ
```

### Kashida Character (U+0640)
A formatting character used for text justification. Standardization removes these:
```
ܡ̣ـــܢ → ܡ̣ܢ (Kashida removed)
```

---

## 📞 Support & Next Steps

### Common Questions

**Q: Will standardization break my corpus?**
A: No. All changes are:
- Based on frequency (most common variant wins)
- Recorded in mapping file (fully traceable)
- Non-Syriac text untouched
- Line count preserved

**Q: Can I undo the standardization?**
A: The mapping file shows all transformations, but true reversion requires the original file. Keep backups!

**Q: Does order matter? Which script to run first?**
A: Analysis first (optional but recommended). It shows what will change. Then standardize.

**Q: How long does it take?**
A: ~2-3 minutes per 1 million words on typical hardware.

### Next Steps

1. ✅ Review this INDEX.md (you are here)
2. 📖 Read QUICKSTART.md (5 min)
3. 🚀 Run quick_standardize.py on a test corpus (5 min)
4. 📊 Review the generated JSON files (10 min)
5. 🎯 Apply to all corpus files
6. 📁 Archive and organize results

### Need Help?

1. Check **EXAMPLES.md** for practical usage patterns
2. Read **README.md** Troubleshooting section
3. Verify your input is a valid UTF-8 `.vert` file
4. Check for write permissions in output directory

---

## 📁 File Organization

```
syriac_standardization/
├── README.md                              ← Full documentation
├── QUICKSTART.md                          ← Quick reference
├── EXAMPLES.md                            ← Usage examples
├── INDEX.md                               ← This file
│
├── analyze_syriac_variants.py             ← Script to analyze
├── standardize_syriac.py                  ← Script to standardize
├── quick_standardize.py                   ← Automated workflow
│
└── [Data Files from Example Run]
    ├── syriac_variants_analysis.json      ← Before analysis
    ├── syriac_variants_analysis_after.json ← After analysis
    └── syriac_standardization_mapping.json ← Transformation mappings
```

---

## ✅ Checklist for New Corpus Files

- [ ] Input file location verified
- [ ] Output directory has write permissions
- [ ] Backup of original created (recommended)
- [ ] Run analysis first to understand changes
- [ ] Review mapping file for unexpected transformations
- [ ] Standardize and verify
- [ ] Archive mapping file with standardized corpus
- [ ] Document any linguistic decisions made

---

## 📝 Notes

- **Python Version:** 3.6+ (any Python 3)
- **Dependencies:** None (standard library only)
- **Encoding:** UTF-8 required
- **Format:** NoSketchEngine `.vert` files (one word per line)
- **Language:** Syriac (ignores non-Syriac text)
- **Speed:** ~1 million words per minute

---

**Created:** 2026-07-07  
**Maintained by:** Sargo  
**Version:** 1.0  

**🎉 Ready to standardize your Syriac corpus?**

Start with: `python quick_standardize.py <your_corpus.vert>`
