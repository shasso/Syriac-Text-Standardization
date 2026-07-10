#!/usr/bin/env python3
"""
Standardize Syriac text in NoSketchEngine vert file using Strategy 1.
- Removes Kashida/Tatweel characters
- Standardizes to most frequent variant for each consonantal base
- Generates canonical mapping
"""

import re
import json
import sys
from collections import defaultdict
from pathlib import Path

SYRIAC_START = 0x0700
SYRIAC_END = 0x074F

def is_syriac(text):
    """Check if text contains Syriac characters."""
    for char in text:
        if SYRIAC_START <= ord(char) <= SYRIAC_END:
            return True
    return False

def remove_kashida(word):
    """Remove Kashida/Tatweel character that causes variants."""
    # Kashida (U+0640) is used for text justification
    return word.replace('\u0640', '')

def get_syriac_base(word):
    """Extract consonantal skeleton (remove all diacritics/vowels)."""
    vowel_marks = {
        '\u064E', '\u064F', '\u0650', '\u064B', '\u064C', '\u064D',
        '\u0651', '\u0652', '\u0653', '\u0654', '\u0655', '\u0656',
        '\u0657', '\u0658', '\u0670', '\u0640',
        '\u0730', '\u0731', '\u0732', '\u0733', '\u0734', '\u0735',
        '\u0736', '\u0737', '\u0738', '\u0739', '\u073A', '\u073B',
        '\u073C', '\u073D', '\u073E', '\u073F', '\u0740', '\u0741',
        '\u0742', '\u0743', '\u0744', '\u0745', '\u0746', '\u0747',
        '\u0748', '\u0749', '\u074A', '\u074B', '\u074C', '\u074D',
        '\u074E', '\u074F',
    }
    return ''.join(c for c in word if c not in vowel_marks)

def build_canonical_mapping(vert_file):
    """Build mapping of consonantal base -> canonical form (most frequent)."""
    words_freq = defaultdict(int)
    base_to_forms = defaultdict(list)
    
    print(f"Building frequency table from {vert_file}...")
    with open(vert_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip non-Syriac
            if not line or line.startswith('<') or line == '<g/>':
                continue
            if not is_syriac(line):
                continue
            
            # First remove Kashida
            normalized = remove_kashida(line)
            words_freq[normalized] += 1
            
            base = get_syriac_base(normalized)
            if normalized not in base_to_forms[base]:
                base_to_forms[base].append(normalized)
    
    # For each base, select most frequent form as canonical
    canonical_mapping = {}
    for base, forms in base_to_forms.items():
        if len(forms) > 1:
            canonical = max(forms, key=lambda x: words_freq[x])
            for form in forms:
                if form != canonical:
                    canonical_mapping[form] = canonical
    
    print(f"Found {len(canonical_mapping)} variant mappings")
    return canonical_mapping

def standardize_file(input_file, output_file, mapping):
    """Apply standardization to vert file."""
    print(f"Standardizing {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        total_lines = 0
        changed_lines = 0
        
        for line in f_in:
            original = line.rstrip('\n')
            processed = original
            
            # Step 1: Remove Kashida from all Syriac text
            if is_syriac(processed):
                after_kashida = remove_kashida(processed)
                if after_kashida != processed:
                    processed = after_kashida
                    changed_lines += 1
            
            # Step 2: Apply canonical mapping
            if processed in mapping:
                processed = mapping[processed]
                changed_lines += 1
            
            f_out.write(processed + '\n')
            total_lines += 1
            
            if total_lines % 100000 == 0:
                print(f"  Processed {total_lines} lines, {changed_lines} changed...")
    
    print(f"Standardization complete: {changed_lines}/{total_lines} lines changed ({100*changed_lines/total_lines:.2f}%)")
    return changed_lines, total_lines

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python standardize_syriac.py <input_vert_file> [output_vert_file] [mapping_json_file]")
        print("\nExample:")
        print("  python standardize_syriac.py corpus.vert corpus_standardized.vert mapping.json")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Generate output filename if not provided
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    else:
        output_file = input_file.parent / f"{input_file.stem}_standardized{input_file.suffix}"
    
    if len(sys.argv) > 3:
        mapping_file = Path(sys.argv[3])
    else:
        mapping_file = input_file.parent / f"{input_file.stem}_mapping.json"
    
    # Build canonical mapping
    mapping = build_canonical_mapping(input_file)
    
    # Save mapping for reference
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"Mapping saved to: {mapping_file}")
    
    # Apply standardization
    changed, total = standardize_file(input_file, output_file, mapping)
    
    print(f"\n=== STANDARDIZATION SUMMARY ===")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Total lines: {total}")
    print(f"Changed lines: {changed} ({100*changed/total:.2f}%)")
    print(f"Mapping file: {mapping_file}")

if __name__ == "__main__":
    main()
