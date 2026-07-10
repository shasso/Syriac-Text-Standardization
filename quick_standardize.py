#!/usr/bin/env python3
"""
Quick reference: Applying Syriac standardization to a new corpus file.
This script demonstrates how to use the standardization tools.
"""

import subprocess
import sys
from pathlib import Path

def standardize_corpus(corpus_file):
    """
    Quick standardization workflow for a corpus file.
    
    Usage:
        python quick_standardize.py path/to/corpus.vert
    """
    
    corpus_path = Path(corpus_file)
    
    if not corpus_path.exists():
        print(f"Error: File not found: {corpus_file}")
        sys.exit(1)
    
    # Step 1: Analyze
    print("=" * 60)
    print("STEP 1: Analyzing corpus for variant duplicates...")
    print("=" * 60)
    
    analysis_file = corpus_path.parent / f"{corpus_path.stem}_analysis.json"
    cmd = [
        sys.executable,
        "analyze_syriac_variants.py",
        "--input", str(corpus_path),
        "--output", str(analysis_file)
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print("Analysis failed!")
        sys.exit(1)
    
    print(f"\n✓ Analysis complete: {analysis_file}\n")
    
    # Step 2: Standardize
    print("=" * 60)
    print("STEP 2: Standardizing corpus...")
    print("=" * 60)
    
    output_file = corpus_path.parent / f"{corpus_path.stem}_standardized.vert"
    mapping_file = corpus_path.parent / f"{corpus_path.stem}_mapping.json"
    
    cmd = [
        sys.executable,
        "standardize_syriac.py",
        str(corpus_path),
        str(output_file),
        str(mapping_file)
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print("Standardization failed!")
        sys.exit(1)
    
    print(f"\n✓ Standardization complete")
    print(f"  Output: {output_file}")
    print(f"  Mapping: {mapping_file}\n")
    
    # Step 3: Verify
    print("=" * 60)
    print("STEP 3: Verifying standardized corpus...")
    print("=" * 60)
    
    analysis_after_file = corpus_path.parent / f"{corpus_path.stem}_standardized_analysis.json"
    cmd = [
        sys.executable,
        "analyze_syriac_variants.py",
        "--input", str(output_file),
        "--output", str(analysis_after_file)
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print("Verification failed!")
        sys.exit(1)
    
    print(f"\n✓ Verification complete: {analysis_after_file}")
    print("\n" + "=" * 60)
    print("STANDARDIZATION WORKFLOW COMPLETE!")
    print("=" * 60)
    print(f"\nGenerated files:")
    print(f"  • {output_file.name}")
    print(f"  • {mapping_file.name}")
    print(f"  • {analysis_file.name}")
    print(f"  • {analysis_after_file.name}")
    print(f"\nNext steps:")
    print(f"  1. Review {analysis_file.name} to see original duplicates")
    print(f"  2. Review {analysis_after_file.name} to verify duplicates eliminated")
    print(f"  3. Replace original with standardized version if satisfied")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Syriac Corpus Standardization - Quick Workflow")
        print("\nUsage:")
        print("  python quick_standardize.py <corpus.vert>")
        print("\nExample:")
        print("  python quick_standardize.py ../corpora_vert_versions/mytext.vert")
        sys.exit(0)
    
    standardize_corpus(sys.argv[1])
