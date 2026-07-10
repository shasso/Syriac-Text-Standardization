#!/usr/bin/env python3
"""
Analyze Syriac text variants in NoSketchEngine vert file.
Identifies potential duplicate entries with different diacritics.
Uses East Syriac vowel system awareness.
"""

import re
import unicodedata
from collections import defaultdict
from pathlib import Path
import json

# Syriac Unicode ranges
SYRIAC_START = 0x0700
SYRIAC_END = 0x074F

def is_syriac(text):
    """Check if text contains Syriac characters."""
    for char in text:
        if SYRIAC_START <= ord(char) <= SYRIAC_END:
            return True
    return False

def get_syriac_base(word):
    """Extract consonantal skeleton (remove all diacritics/vowels)."""
    # East Syriac vowels and diacritical marks
    vowel_marks = {
        '\u064E',  # FATHA
        '\u064F',  # DAMMA
        '\u0650',  # KASRA
        '\u064B',  # FATHATAN
        '\u064C',  # DAMMATAN
        '\u064D',  # KASRATAN
        '\u0651',  # SHADDA
        '\u0652',  # SUKUN
        '\u0653',  # MADDAH
        '\u0654',  # HAMZA ABOVE
        '\u0655',  # HAMZA BELOW
        '\u0656',  # SUBSCRIPT ALEF
        '\u0657',  # INVERTED DAMMA
        '\u0658',  # MARK NOON GHUNNA
        '\u0670',  # SUPERSCRIPT ALEF
        '\u0640',  # TATWEEL
        # Syriac specific combining marks
        '\u0730',  # SYRIAC PTHAHA ABOVE
        '\u0731',  # SYRIAC PTHAHA BELOW
        '\u0732',  # SYRIAC PTHAHA DOTTED
        '\u0733',  # SYRIAC GATHPHA ABOVE
        '\u0734',  # SYRIAC GATHPHA BELOW
        '\u0735',  # SYRIAC GATHPHA DOTTED
        '\u0736',  # SYRIAC RBASA ABOVE
        '\u0737',  # SYRIAC RBASA BELOW
        '\u0738',  # SYRIAC HBASA ABOVE
        '\u0739',  # SYRIAC HBASA BELOW
        '\u073A',  # SYRIAC HBASA-ESASA DOTTED
        '\u073B',  # SYRIAC ESASA ABOVE
        '\u073C',  # SYRIAC ESASA BELOW
        '\u073D',  # SYRIAC RWAHA
        '\u073E',  # SYRIAC YUDH
        '\u073F',  # SYRIAC SHADDA
        '\u0740',  # SYRIAC FEMININE DOT
        '\u0741',  # SYRIAC QUSHSHAMA
        '\u0742',  # SYRIAC QUSHSHAMA DOTTED
        '\u0743',  # SYRIAC BARREKH
        '\u0744',  # SYRIAC HAHH
        '\u0745',  # SYRIAC HE
        '\u0746',  # SYRIAC SHIN
        '\u0747',  # SYRIAC SHIN DOTTED
        '\u0748',  # SYRIAC SHIN DOTTED2
        '\u0749',  # SYRIAC SHIN DOTTED3
        '\u074A',  # SYRIAC SHIN DOTTED4
        '\u074B',  # SYRIAC SHIN DOTTED5
        '\u074C',  # SYRIAC SHIN DOTTED6
        '\u074D',  # SYRIAC SHIN DOTTED7
        '\u074E',  # SYRIAC SHIN DOTTED8
        '\u074F',  # SYRIAC SHIN DOTTED9
    }
    
    return ''.join(c for c in word if c not in vowel_marks)

def analyze_file(filepath):
    """Analyze Syriac words and their variants."""
    words_freq = defaultdict(int)
    variants_by_base = defaultdict(set)
    base_to_forms = defaultdict(list)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines, XML tags, and non-Syriac entries
            if not line or line.startswith('<') or line.startswith('</') or line == '<g/>':
                continue
            
            # Only process Syriac text
            if not is_syriac(line):
                continue
            
            # Count word frequency
            words_freq[line] += 1
            
            # Get consonantal base
            base = get_syriac_base(line)
            
            # Track all variants for this base
            variants_by_base[base].add(line)
            if line not in base_to_forms[base]:
                base_to_forms[base].append(line)
    
    return words_freq, variants_by_base, base_to_forms

def generate_report(words_freq, variants_by_base, base_to_forms, output_file):
    """Generate report of potential duplicates."""
    duplicates = {base: forms for base, forms in variants_by_base.items() if len(forms) > 1}
    
    report = {
        "summary": {
            "total_unique_words": len(words_freq),
            "total_word_instances": sum(words_freq.values()),
            "potential_duplicate_clusters": len(duplicates),
        },
        "duplicates": []
    }
    
    # Sort by frequency of the cluster
    sorted_dupes = sorted(
        duplicates.items(),
        key=lambda x: sum(words_freq[form] for form in x[1]),
        reverse=True
    )
    
    for base, variants in sorted_dupes:
        variant_info = []
        for form in sorted(variants, key=lambda x: words_freq[x], reverse=True):
            variant_info.append({
                "form": form,
                "frequency": words_freq[form],
                "display": form  # For reference
            })
        
        cluster_freq = sum(v["frequency"] for v in variant_info)
        
        report["duplicates"].append({
            "consonantal_base": base,
            "cluster_frequency": cluster_freq,
            "num_variants": len(variants),
            "variants": variant_info
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report

def main():
    import sys
    
    # Allow command-line arguments
    if len(sys.argv) > 1:
        input_arg = None
        output_arg = None
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == '--input' and i < len(sys.argv)-1:
                input_arg = sys.argv[i+1]
            elif arg == '--output' and i < len(sys.argv)-1:
                output_arg = sys.argv[i+1]
        
        if input_arg:
            vert_file = Path(input_arg)
        else:
            print("Error: --input parameter required")
            sys.exit(1)
        
        if output_arg:
            output_file = Path(output_arg)
        else:
            output_file = vert_file.parent / f"{vert_file.stem}_analysis.json"
    else:
        print("Usage: python analyze_syriac_variants.py --input <vert_file> [--output <report_file>]")
        sys.exit(1)
    
    print(f"Analyzing {vert_file}...")
    words_freq, variants_by_base, base_to_forms = analyze_file(vert_file)
    
    print(f"Generating report...")
    report = generate_report(words_freq, variants_by_base, base_to_forms, output_file)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total unique words: {report['summary']['total_unique_words']}")
    print(f"Total word instances: {report['summary']['total_word_instances']}")
    print(f"Potential duplicate clusters: {report['summary']['potential_duplicate_clusters']}")
    
    if report['duplicates']:
        print(f"\nTop 10 duplicate clusters by frequency:")
        for i, dup in enumerate(report['duplicates'][:10], 1):
            print(f"\n{i}. Base: {dup['consonantal_base']}")
            print(f"   Cluster freq: {dup['cluster_frequency']}, Variants: {dup['num_variants']}")
            for var in dup['variants']:
                print(f"     • {var['form']} (n={var['frequency']})")
    
    print(f"\nFull report saved to: {output_file}")

if __name__ == "__main__":
    main()
