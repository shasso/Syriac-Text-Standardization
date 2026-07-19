## What's actually in the data, and the big finding

I ran the JSON through several additional analyses beyond what the report already surfaces. Short version: **the "frequency-based canonicalization" strategy your README describes is safe for most clusters but risky for exactly the highest-value ones.**

**1. Kashida isn't the real story.** Your README leads with kashida/tatweel as a cause of duplication, but clusters that are *purely* tatweel noise (same word once you strip `U+0640`) are only 248 out of 51,858 clusters — 0.1% of corpus instances. The other 99.5% of duplicate clusters differ in actual vowel/diacritic marks, not spacing artifacts.

**2. Duplicate clusters cover 86.9% of the corpus.** Almost every token instance belongs to some multi-variant cluster — but that's because short, high-frequency function words dominate token counts and also collide most (see #3), so this isn't as alarming as it sounds.

**3. Shorter consonantal skeletons → far more variants.** 1-character bases average 7.0 variants; 8+ character bases average ~2.5. Function words and grammatical particles are inherently more "collision-prone" under a skeleton-stripping approach.

**4. Concentration is steep.** The top 1,000 clusters (∼2% of all clusters) account for **59.5%** of all duplicate-cluster instances. Most of the payoff (and risk) is concentrated in a small set of very common words.

**5. The important one — dominance ratio.** For each cluster I computed what share of its total frequency the single most-common variant holds. Where that's low *and* the cluster is high-frequency, frequency-based "pick the most common form" starts looking less like denoising and more like **erasing real grammatical distinctions**:

- `ܗܘܐ` (freq 31,623, dominance 0.56): `ܗ݇ܘܵܐ` (17,797) vs `ܗܵܘܹܐ` (5,135) — these look like distinct verbal forms of "to be" (perfect vs. participle), not spelling variants of one word.
- `ܝܠܐ` (dominance 0.42), `ܝܗܘܐ` (dominance 0.41), `ܦܝܫܐ` (dominance 0.30) — copula and passive-participle paradigms, same pattern.
- `ܠܐ` (dominance 0.55): `ܠܵܐ` vs `ܠܹܐ` — plausibly a genuine dialectal/pronunciation split rather than noise.

I built a three-tier classifier (`variant_insights.py`) on top of your existing report:

| Tier | Clusters | Instances | Rule |
|---|---|---|---|
| SAFE_AUTO | 43,165 | 1,506,900 | kashida-only, or noise tail ≤3 freq, or dominance ≥0.85 |
| REVIEW | 6,501 | 422,473 | in between |
| MANUAL | 2,192 | **656,846 (22% of corpus)** | freq ≥50 and dominance <0.75 — likely real morphology, not noise |

That MANUAL tier is the headline: 22% of your corpus tokens sit in clusters where collapsing to "most frequent form" could silently destroy tense, person, or gender information for exactly your most common words.

**Files:**
- `variant_insights.py` — reusable script (`--input`, `--chart`, `--export-review`) you can run on any future `_analysis.json`
- `variant_insights_chart.png` — 4-panel chart (variant-count histogram, dominance distribution, Pareto curve, base-length correlation)
- `flagged_for_manual_review.json` — full list of the 2,192 MANUAL-tier clusters, sorted by impact, ready for a linguist/native-speaker pass

Want me to also cross-reference the MANUAL list against a Neo-Aramaic verb paradigm (e.g. flag likely "to be"/copula forms specifically) so you can separate "genuine grammar" from "still probably noise, just balanced noise"?

---
"Dominance" is the share of a cluster's total token frequency held by its single most common variant.

**Formula:**
```
dominance = max(variant frequencies) / cluster_frequency
```
where `cluster_frequency` is the sum of frequencies across all variants sharing that consonantal base.

**Range:** it's a fraction between roughly `1/num_variants` and `1.0`.

- **1.0** — every instance of that consonantal base appears as one single surface form. (Not actually possible for anything in this report, since by definition a cluster only exists if there are ≥2 distinct variants — but a cluster could still approach 1.0 if the top form has, say, 9,998 out of 10,000 instances and the rest is a thin noise tail.)
- **Close to 1.0 (e.g. 0.95+)** — one form completely dominates; the other variants are almost certainly typos, OCR noise, or rare kashida-padded copies of the same word. Safe to auto-merge onto the dominant form.
- **Around 0.5–0.7** — the mass is split fairly evenly between two (or more) forms. This is the interesting/ambiguous zone: it could mean two genuinely competing spelling conventions in the corpus, or it could mean the two forms aren't spelling variants at all but different grammatical forms that happen to share a consonantal skeleton.
- **Low (0.3–0.5)** — no single form dominates at all; frequency is spread across 3+ variants roughly evenly. This is the strongest signal that "pick the most frequent variant as canonical" is a bad idea, because there's no dominant convention to converge on — you'd be arbitrarily privileging whichever form happened to be slightly more common, potentially at the expense of a form that's grammatically distinct rather than just a misspelling.

That's why I paired dominance with `cluster_frequency` in the MANUAL tier rule: a low dominance ratio on a *rare* word isn't very consequential (worst case you merge two typos incorrectly, affecting a handful of tokens). A low dominance ratio on a *high-frequency* word like `ܗܘܐ` or `ܝܠܐ` means tens of thousands of tokens are at risk of being silently collapsed into the wrong canonical form — which is exactly the ℗`ܗ݇ܘܵܐ` (was) vs `ܗܵܘܹܐ` (becomes) situation from before.

---

Ran it against a heuristic Neo-Aramaic morphology dictionary. One important caveat up front: **this is a heuristic pattern-match built from general NENA grammar knowledge (copula/to-be system, piš- passive, pronominal suffixes), not a verified analyzer for your specific corpus's dialect or transliteration choices** — treat matches as a strong prior, and treat "unclassified" as "still needs a human," not "confirmed noise."

## Results

Of the 2,192 MANUAL-tier clusters (656,846 instances):

| Category | Clusters | Instances | What it is |
|---|---|---|---|
| `copula_or_to_be_paradigm` | 36 | **106,377** | `ܗܘܐ`, `ܝܠܐ`, `ܗܘܘ`, `ܝܗܘܐ` — enclitic copula (-ile/-ila/-iwan/-iwax) and the h-w-y "to be" root across tense/person/gender. Confirms the earlier suspicion: these variants are different grammatical forms, not spelling noise. |
| `passive_or_remain_piš` | 8 | 15,483 | `ܦܝܫܐ`, `ܦܝܫ`, `ܦܫܠܐ` — the piš- "remain/become" passive auxiliary; variants mark participle vs. preterite. |
| `pronominal_suffix` | 26 | 41,090 | `ܠܗܘܢ`, `ܐܢܐ`, `ܡܢܝ`, `ܕܐܢܐ` — preposition/pronoun + person suffix (to them / I / from me...). Different grammatical persons sharing a base. |
| `negation_particle` | 80 | 54,732 | `ܠܐ`, `ܘܠܐ` — negation, likely real dialectal la/le split. |
| `numeral_one` | 13 | 37,714 | `ܚܕ`, `ܕܚܕ`, `ܒܚܕ` — the numeral "one" and its cliticized forms. |
| **Unclassified** | 2,029 | 401,450 | Didn't match any known pattern — genuinely needs a human pass. |

**38.9% of MANUAL-tier instances (255,396) now have a linguistic explanation** for why frequency-based merging would be wrong — that's not "balanced noise," it's real grammar.

The remaining 2,029 unclassified clusters are still a mix. Eyeballing the top 20 by impact, most look like **plain dialectal/vowel variation on ordinary nouns and adverbs** rather than paradigmatic morphology — `ܐܢܫܐ` (people), `ܟܬܒܐ` (book), `ܬܪܝ` (two), `ܗܘ` (that/he), `ܡܘܕܝ` (what), `ܕܐܟܝ` (how), `ܬܚܘܬ` (under), `ܒܝܕ` (by/through), `ܩܕܡܝܐ` (first). These are lower-risk than the copula cases — there's no tense/person information at stake, just pronunciation — so frequency-based canonicalization is more defensible for this remainder, though still worth spot-checking rather than blind auto-merging given they're each 1,000+ instances.

Files:
- `grammar_crossref.py` — the classifier; `ROOT_CATEGORIES` at the top is a plain Python list you can correct or extend as you verify entries against your own knowledge of the corpus's dialect
- `manual_review_annotated.json` — the full 2,192-cluster list with `grammar_category`/`grammar_note` fields added

Want me to add a rule that separates "plain noun/adverb phonetic variation" (safe-ish to canonicalize) from "genuinely still ambiguous" among those 2,029 unclassified — e.g. by using the seyame/plural marker and common ordinal/adjective suffix patterns you already have in the data?

---

Ran a second pass over the 2,029 clusters that didn't match a paradigm. Same caveat as before applies — heuristic triage aid, not ground truth.

## Updated picture

| Layer | Clusters | Instances | Meaning |
|---|---|---|---|
| Grammar paradigm (previous pass) | 163 | 255,396 | copula/to-be, piš-, pronoun suffixes, negation, numeral "one" |
| `plural_noun_phonetic` | 291 | 52,949 | base carries the seyame (plural) mark — variation is pronunciation on an already-plural noun (`ܐܢܫ̈ܐ`, `ܝܘܡܢ̈ܐ`, `ܚܒܪ̈ܐ`) |
| `adjectival_or_ordinal_ending` | 193 | 37,398 | ends in derivational `-ܝܐ`/`-ܝܬܐ` (`ܩܪܝܐ`, `ܐܬܝܐ`, `ܚܝܐ`, `ܡܠܝܐ`) |
| `ordinal_before_root` | 9 | 11,627 | the "before/first" (qdam) word family |
| `interrogative_particle` | 9 | 7,903 | "what" / "how" |
| `demonstrative_pronoun` | 3 | 2,456 | "that/he" |
| **Still ambiguous** | **1,524** | **289,117** | genuinely needs a human |

**56.0% of MANUAL-tier instances now have some explanation** (grammatical or lexical) for why they're not simple spelling noise — up from 38.9%.

The remaining 1,524 (289k instances) are a real mixed bag when I look at the top of the list — some (`ܫܢܬܐ` "year", `ܟܬܒܐ` "book", `ܐܢܫܐ` "people") look like plain nouns with dialectal vowel variation and are probably lower-risk to canonicalize; others (`ܩܡ` — could be the perfective particle *qam-* or the verb "stood," `ܐܘ` — "or" vs. a demonstrative reading, `ܝܘܚܢܢ` — a proper name, where variation is just transliteration/orthography rather than linguistics at all) are exactly the kind of thing that needs your eyes rather than a pattern match.

Two things worth flagging honestly:
- The `-ܬܐ` feminine noun ending (without the extra `-ܝ-`) is *extremely* common in Aramaic generally — I deliberately didn't add a blanket rule for it, because it would have swept in a lot of unrelated words under a vague "probably a feminine noun" label without adding real signal. If you want, I can add it as its own separate tier rather than merging it into `adjectival_or_ordinal_ending`.
- `ܝܘܚܢܢ` (a proper name, "Yohannan/John") is a good example of a category I haven't built yet: proper nouns, where cross-variant spelling differences are pure orthography/transliteration choice, not grammar *or* even regular lexical phonology. Might be worth a `proper_noun` tag if names show up a lot in the remaining 1,524.

Files:
- `lexical_subclass.py` — the second-pass script
- `manual_review_final.json` — full list with both `grammar_category` and `lexical_category` fields

Want me to add the plain `-ܬܐ` feminine-noun tier and a proper-noun heuristic (e.g. checking against a name list, or just isolating single-token clusters with no attached prefixes) to chip further into that 1,524?

---

Added both. Results from this third pass over the still-ambiguous residual:

| Category | Clusters | Instances | Notes |
|---|---|---|---|
| `proper_noun_heuristic` | 11 | 5,421 | `ܝܘܚܢܢ` (John), `ܐܘܪܡܝ` (Urmia), `ܐܒܪܗܡ` (Abraham) — matched against a **small seed list** I built from names/places plausible in this genre (Assyrian Church history), allowing for a `d-/w-/b-/l-` proclitic or "Mar" honorific prefix |
| `feminine_noun_ta_ending` | 158 | 29,212 | `ܫܢܬܐ` (year), `ܐܬܐ` (sign/come), `ܐܚܪܬܐ` (other-fem) — the plain Aramaic feminine `-ta` noun ending |
| **Still ambiguous** | **1,355** | **254,484** | down from 1,524 / 289,117 |

**Cumulative coverage of the MANUAL tier is now 61.3%** (402,362 of 656,846 instances), up from 56.0%.

Two honesty notes, both also written into the script's docstring:

1. **The proper-noun list is a seed, not a gazetteer.** I only had 13 names/places to work with, drawn from general knowledge of the genre plus what's visible in your `sample.vert` header (Urmia, Seleucia, Ctesiphon). It will miss the vast majority of actual proper nouns in a 440-page text. If you have (or can extract) an actual name list from the corpus, swapping it in would meaningfully grow this category.

2. **The feminine `-ta` tier is deliberately *not* folded into the "safe" bucket.** Unlike the closed-class grammar paradigms (copula, negation, etc.), an ordinary feminine noun's spelling variants aren't guaranteed to be mere pronunciation differences — I kept it as its own tagged tier specifically so it doesn't quietly inherit a false sense of safety from the categories in pass 1.

Looking at the new top-of-list residual (`ܐܢܫܐ` "people," `ܗܕܟܐ` "like this," `ܒܐܡܪܐ` — likely a preposition+noun collocation, `ܬܪܝ` "two"), these look like the genuinely hardest remaining cases: common words with real dialectal pronunciation variation but no clean structural marker (no seyame, no `-ta`, no recognized paradigm root) to key off of. That's probably close to the floor of what a heuristic, no-training-data approach can resolve without either a verified name/lexicon list or actual annotated examples.

File: `name_and_feminine_subclass.py` and the updated `manual_review_final2.json` are ready — want me to present them, and/or fold this third pass into the paper (updating Section 5.5/6 and Table 4 with the new numbers)?